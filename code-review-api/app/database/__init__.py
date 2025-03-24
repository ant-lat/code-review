"""
数据库管理模块
@author: pgao
@date: 2024-03-13

包含数据库连接配置和ORM基类，支持多种数据库类型
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import time
import traceback
from typing import Dict, Any, Generator, Optional, Callable

from app.config import config
from app.config.logging_config import logger

# 数据库连接URL
DB_TYPE = config.DB_TYPE
DB_URL = config.DB_URL

# 数据库引擎特定配置
ENGINE_CONFIGS = {
    'sqlite': {
        'connect_args': {'check_same_thread': False},
        'pool_pre_ping': True,
        'poolclass': QueuePool,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30
    },
    'mysql': {
        'pool_pre_ping': True,            # 使用连接前测试连接是否有效
        'pool_recycle': 1800,             # 30分钟回收连接，避免"MySQL server has gone away"错误
        'pool_size': 20,                  # 连接池大小
        'max_overflow': 30,               # 最大连接溢出数
        'pool_timeout': 30,               # 连接池获取连接超时
        'connect_args': {
            'connect_timeout': 10,        # 连接超时10秒
            'read_timeout': 30,           # 读取超时30秒
            'write_timeout': 30,          # 写入超时30秒
            'charset': 'utf8mb4'          # 使用UTF-8 MB4字符集支持所有Unicode字符和表情符号
        },
        'echo': True,                     # 输出执行的SQL语句，用于调试
        'echo_pool': True                 # 输出连接池操作，用于调试
    },
    'postgresql': {
        'pool_pre_ping': True,            # 使用连接前测试连接是否有效
        'pool_recycle': 1800,             # 30分钟回收连接
        'pool_size': 20,                  # 连接池大小
        'max_overflow': 30,               # 最大连接溢出数
        'pool_timeout': 30,               # 连接池获取连接超时
        'connect_args': {
            'connect_timeout': 10,        # 连接超时10秒
            'options': '-c statement_timeout=60000'  # 查询超时60秒
        }
    },
    'oracle': {
        'pool_pre_ping': True,            # 使用连接前测试连接是否有效
        'pool_recycle': 3600,             # 1小时回收连接
        'pool_size': 10,                  # 连接池大小
        'max_overflow': 10,               # 最大连接溢出数
        'pool_timeout': 30,               # 连接池获取连接超时
        'encoding': 'utf-8',              # 字符编码
        'convert_unicode': True,          # 转换Unicode
        'connect_args': {
            'encoding': 'UTF-8',          # 连接编码
            'nencoding': 'UTF-8'          # 国家字符集编码
        }
    }
}

def get_engine_config() -> Dict[str, Any]:
    """
    获取数据库引擎配置
    
    Returns:
        Dict[str, Any]: 引擎配置参数
    """
    # 获取基础配置
    db_config = ENGINE_CONFIGS.get(DB_TYPE, {}).copy()
    
    # 从配置文件中获取可能的额外配置
    if hasattr(config, 'DB_POOL_SIZE') and config.DB_POOL_SIZE is not None:
        db_config['pool_size'] = int(config.DB_POOL_SIZE)
    elif 'pool_size' not in db_config or db_config['pool_size'] is None:
        db_config['pool_size'] = 10  # 默认连接池大小
        
    if hasattr(config, 'DB_MAX_OVERFLOW') and config.DB_MAX_OVERFLOW is not None:
        db_config['max_overflow'] = int(config.DB_MAX_OVERFLOW)
    elif 'max_overflow' not in db_config or db_config['max_overflow'] is None:
        db_config['max_overflow'] = 20  # 默认最大溢出数
        
    if hasattr(config, 'DB_POOL_TIMEOUT') and config.DB_POOL_TIMEOUT is not None:
        db_config['pool_timeout'] = float(config.DB_POOL_TIMEOUT)
    elif 'pool_timeout' not in db_config or db_config['pool_timeout'] is None:
        db_config['pool_timeout'] = 30.0  # 默认池超时
    
    # 确保关键参数为有效值
    for key in ['pool_size', 'max_overflow']:
        if key in db_config and (db_config[key] is None or not isinstance(db_config[key], int)):
            logger.warning(f"{key} 配置无效，使用默认值")
            db_config[key] = 10 if key == 'pool_size' else 20
    
    return db_config

# 添加数据库类型特定的连接错误处理函数
def handle_db_connection(dbapi_connection, connection_record, db_type):
    """
    处理数据库连接问题，针对不同数据库类型采取不同策略
    
    Args:
        dbapi_connection: 数据库API连接对象
        connection_record: 连接记录
        db_type: 数据库类型
    """
    try:
        if db_type == 'mysql':
            # MySQL的ping方法
            if hasattr(dbapi_connection, 'ping') and dbapi_connection is not None:
                dbapi_connection.ping(reconnect=True)
                
        elif db_type == 'postgresql':
            # PostgreSQL的连接检查
            if hasattr(dbapi_connection, 'closed') and dbapi_connection.closed:
                # 该连接已关闭，将在连接池中自动替换
                logger.warning("检测到PostgreSQL连接已关闭")
                raise Exception("连接已关闭")
                
        elif db_type == 'oracle':
            # Oracle连接检查
            cursor = None
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
            except Exception as e:
                logger.warning(f"Oracle连接检查失败: {str(e)}")
                raise
            finally:
                if cursor:
                    cursor.close()
                    
        # SQLite通常不需要特殊处理，SQLAlchemy会自动处理
    except Exception as e:
        logger.error(f"{db_type}数据库连接检查失败: {str(e)}")
        raise

# 创建数据库引擎时添加事件监听
def create_db_engine():
    """创建数据库引擎并添加事件监听"""
    try:
        # 获取引擎配置
        engine_config = get_engine_config()
        logger.debug(f"数据库引擎配置: {engine_config}")
        
        # 创建引擎
        db_engine = create_engine(DB_URL, **engine_config)
        
        # 为不同数据库添加特殊事件监听器
        if DB_TYPE == 'mysql':
            # MySQL连接检查
            @event.listens_for(db_engine, 'connect')
            def mysql_connect(dbapi_connection, connection_record):
                handle_db_connection(dbapi_connection, connection_record, 'mysql')
            
            # MySQL连接池回收检查
            @event.listens_for(db_engine, 'checkout')
            def mysql_checkout(dbapi_connection, connection_record, connection_proxy):
                handle_db_connection(dbapi_connection, connection_record, 'mysql')
                
        elif DB_TYPE == 'postgresql':
            # PostgreSQL连接检查
            @event.listens_for(db_engine, 'connect')
            def pg_connect(dbapi_connection, connection_record):
                handle_db_connection(dbapi_connection, connection_record, 'postgresql')
                
            # PostgreSQL连接池回收检查
            @event.listens_for(db_engine, 'checkout')
            def pg_checkout(dbapi_connection, connection_record, connection_proxy):
                handle_db_connection(dbapi_connection, connection_record, 'postgresql')
                
        elif DB_TYPE == 'oracle':
            # Oracle连接检查
            @event.listens_for(db_engine, 'connect')
            def oracle_connect(dbapi_connection, connection_record):
                handle_db_connection(dbapi_connection, connection_record, 'oracle')
                
            # Oracle连接池回收检查
            @event.listens_for(db_engine, 'checkout')
            def oracle_checkout(dbapi_connection, connection_record, connection_proxy):
                handle_db_connection(dbapi_connection, connection_record, 'oracle')
        
        # 添加事件监听器记录慢查询
        @event.listens_for(db_engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            
        @event.listens_for(db_engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            # 慢查询阈值，可配置
            slow_query_threshold = getattr(config, 'DB_SLOW_QUERY_THRESHOLD', 1.0)
            if total > slow_query_threshold:
                logger.warning(f"慢查询 ({total:.2f}秒): {statement}")
        
        return db_engine
    except Exception as e:
        logger.error(f"数据库引擎初始化失败: {str(e)}")
        logger.debug(traceback.format_exc())
        # 使用SQLite作为备用数据库
        backup_url = 'sqlite:///./sql_app.db'
        logger.warning(f"切换到备用数据库: {backup_url}")
        backup_config = {
            'connect_args': {'check_same_thread': False},
            'pool_pre_ping': True
        }
        return create_engine(backup_url, **backup_config)

# 创建ORM模型基类
Base = declarative_base()

# 创建数据库引擎
logger.info(f"初始化 {DB_TYPE} 数据库引擎，连接URL: {DB_URL}")
engine = create_db_engine()

# 创建数据库会话工厂
session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SessionLocal = scoped_session(session_factory)

# 设置查询属性
Base.query = SessionLocal.query_property()

def get_db() -> Generator[session_factory, None, None]:
    """
    获取数据库会话的依赖注入函数
    
    Yields:
        Generator[session_factory, None, None]: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def db_session() -> Generator[session_factory, None, None]:
    """
    数据库会话上下文管理器
    
    Yields:
        Generator[session_factory, None, None]: 数据库会话
        
    Example:
        with db_session() as session:
            result = session.query(Model).filter(Model.id == 1).first()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库操作失败: {str(e)}")
        logger.debug(traceback.format_exc())
        raise
    finally:
        session.close()

def init_db(create_tables: bool = False) -> None:
    """
    初始化数据库
    
    Args:
        create_tables (bool, optional): 是否创建表. Defaults to False.
    """
    logger.info("初始化数据库...")
    if create_tables:
        logger.info("创建数据库表...")
        Base.metadata.create_all(bind=engine)
    logger.info("数据库初始化完成")

def check_db_connection() -> bool:
    """
    检查数据库连接
    
    Returns:
        bool: 连接是否正常
    """
    try:
        # 使用事务执行简单查询
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        logger.debug(traceback.format_exc())
        return False

class DBUtils:
    """数据库工具类，提供一些实用的数据库操作方法"""
    
    @staticmethod
    def paginate(query, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        分页查询
        
        Args:
            query: 查询对象
            page (int): 页码，从1开始
            page_size (int): 每页数量
            
        Returns:
            Dict[str, Any]: 包含分页信息和结果的字典
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
            
        items = query.limit(page_size).offset((page - 1) * page_size).all()
        total = query.order_by(None).count()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    
    @staticmethod
    def bulk_save(session, objects, batch_size: int = 100) -> None:
        """
        批量保存对象
        
        Args:
            session: 数据库会话
            objects (list): 要保存的对象列表
            batch_size (int): 批处理大小
        """
        if not objects:
            return
            
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i+batch_size]
            session.bulk_save_objects(batch)
            session.flush()

    @staticmethod
    def execute_with_retry(func: Callable, max_retries: int = 3, retry_delay: float = 0.5) -> Any:
        """
        执行函数，遇到错误时自动重试
        
        Args:
            func (Callable): 要执行的函数
            max_retries (int): 最大重试次数
            retry_delay (float): 重试延迟(秒)
            
        Returns:
            Any: 函数执行结果
            
        Raises:
            Exception: 最后一次尝试的异常
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_error = e
                logger.warning(f"数据库操作失败，尝试重试 ({attempt+1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # 指数退避
        
        logger.error(f"数据库操作失败，已达到最大重试次数: {str(last_error)}")
        raise last_error

# 导出模块内容
__all__ = [
    "engine", "Base", "get_db", "SessionLocal", 
    "db_session", "init_db", "check_db_connection", "DBUtils"
]