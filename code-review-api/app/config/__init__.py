"""
配置管理模块
@author: pgao
@date: 2024-03-13
"""
import os
from dotenv import load_dotenv
from typing import Any, Optional, Dict, TypeVar, cast, List, Union
import ast
import logging
import argparse
import json
import yaml
from pathlib import Path
import traceback

__all__ = ['Config']

# 配置日志记录
logger = logging.getLogger(__name__)

# 定义配置类型
T = TypeVar('T')

class ConfigMeta(type):
    """配置类元类，确保单例模式"""
    _instance = None

    def __call__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance

class Config(metaclass=ConfigMeta):
    """
    配置管理类
    支持从环境变量、命令行参数、配置文件(JSON, YAML)加载配置
    遵循优先级：命令行参数 > .env文件 > 环境变量 > 默认值
    """
    
    def __init__(self, args=None, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            args: 命令行参数
            config_path: 配置文件路径
        """
        self.args = {}
        self.env_values = {}
        self._config_map: Dict[str, Any] = {}
        self._config_file_values: Dict[str, Any] = {}
        
        # 加载配置
        self._load_args(args)
        self._load_dotenv()
        if config_path:
            self._load_config_file(config_path)
        
        # 加载一些常用配置
        self._initialize_default_configs()
        
        logger.debug("配置管理器初始化完成")
    
    def _initialize_default_configs(self):
        """初始化一些默认配置"""
        # 数据库配置
        _ = self.DB_TYPE
        _ = self.DB_URL
        _ = self.DB_POOL_SIZE
        _ = self.DB_MAX_OVERFLOW
        _ = self.DB_POOL_TIMEOUT
        _ = self.DB_SLOW_QUERY_THRESHOLD
        # 认证配置
        _ = self.BCRYPT_ROUNDS
        _ = self.BCRYPT_IDENT
        _ = self.SECRET_KEY
        _ = self.REFRESH_SECRET_KEY
        _ = self.ALGORITHM
        _ = self.ACCESS_TOKEN_EXPIRE_MINUTES
        # 消息队列配置
        _ = self.CELERY_BROKER_URL
        _ = self.CELERY_RESULT_BACKEND
        # 邮件服务配置
        _ = self.SMTP_SERVER
        _ = self.SMTP_PORT
        _ = self.SMTP_USERNAME
        _ = self.SMTP_PASSWORD
        # 应用配置
        _ = self.ENVIRONMENT
        _ = self.LOG_LEVEL
        _ = self.HOST
        _ = self.PORT
        # CORS配置
        _ = self.ALLOWED_ORIGINS
    
    def _load_args(self, args):
        """加载命令行参数"""
        if args is not None:
            parsed_args = vars(args)
            self.args = {k: v for k, v in parsed_args.items() if v is not None}
            logger.debug(f"成功加载启动参数: {self.args}")
    
    def _load_dotenv(self):
        """加载.env文件中的环境变量"""
        try:
            # 尝试加载.env文件，不存在则忽略
            load_dotenv()
            logger.debug("成功加载 .env 文件")
            self.env_values = os.environ.copy()
        except Exception as e:
            logger.error(f"加载 .env 文件时出错: {e}")
            logger.debug(traceback.format_exc())
    
    def _load_config_file(self, config_path: str):
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
        """
        if not config_path:
            return
        
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"配置文件 {config_path} 不存在")
            return
        
        try:
            if path.suffix.lower() == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    self._config_file_values = json.load(f)
            elif path.suffix.lower() in ['.yml', '.yaml']:
                with open(path, 'r', encoding='utf-8') as f:
                    self._config_file_values = yaml.safe_load(f)
            else:
                logger.warning(f"不支持的配置文件格式: {path.suffix}")
                return
            
            logger.debug(f"成功加载配置文件: {config_path}")
        except Exception as e:
            logger.error(f"加载配置文件 {config_path} 时出错: {e}")
            logger.debug(traceback.format_exc())
    
    def get(self, key: str, default: Optional[Any] = None, value_type: Optional[type] = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键名
            default: 默认值
            value_type: 值类型
            
        Returns:
            配置值
        """
        # 缓存中有值直接返回
        if key in self._config_map:
            return self._config_map[key]
        
        # 准备不同格式的键名
        key_lower = key.lower().replace('_', '-')
        key_upper = key.upper()
        
        # 按优先级获取值
        # 1. 命令行参数
        value = self.args.get(key_lower)
        if value is not None:
            logger.debug(f"从启动参数获取配置项 {key}: {value}")
            result = self._auto_convert(value, value_type)
            self._config_map[key] = result
            return result
        
        # 2. .env文件
        value = self.env_values.get(key_upper)
        if value is not None:
            logger.debug(f"从 .env 文件获取配置项 {key}: {value}")
            result = self._auto_convert(value, value_type)
            self._config_map[key] = result
            return result
        
        # 3. 环境变量
        value = os.getenv(key_upper)
        if value is not None:
            logger.debug(f"从环境变量获取配置项 {key}: {value}")
            result = self._auto_convert(value, value_type)
            self._config_map[key] = result
            return result
        
        # 4. 配置文件
        if key in self._config_file_values:
            value = self._config_file_values[key]
            logger.debug(f"从配置文件获取配置项 {key}: {value}")
            result = self._auto_convert(value, value_type)
            self._config_map[key] = result
            return result
        
        # 5. 最后返回默认值
        logger.debug(f"使用默认值 {default} 作为配置项 {key}")
        self._config_map[key] = default
        return default
    
    def get_typed(self, key: str, default: T, value_type: type = None) -> T:
        """
        获取指定类型的配置值
        
        Args:
            key: 配置键名
            default: 默认值
            value_type: 值类型
            
        Returns:
            配置值
        """
        if value_type is None and default is not None:
            value_type = type(default)
        
        value = self.get(key, default, value_type)
        return cast(T, value)
    
    def _auto_convert(self, value: Any, value_type: Optional[type] = None) -> Any:
        """
        自动转换值类型
        
        Args:
            value: 要转换的值
            value_type: 目标类型
            
        Returns:
            转换后的值
        """
        if value_type is not None:
            try:
                if value_type == bool and isinstance(value, str):
                    return value.lower() in ('true', 'yes', 'on', '1')
                return value_type(value)
            except (ValueError, TypeError):
                logger.warning(f"无法将 {value} 转换为 {value_type.__name__} 类型")
        
        # 如果是字符串，尝试自动转换
        if isinstance(value, str):
            try:
                return ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # 处理特殊布尔值
                if value.lower() in ('true', 'yes', 'on'):
                    return True
                if value.lower() in ('false', 'no', 'off'):
                    return False
        
        return value
    
    def __getattr__(self, name: str) -> Any:
        """通过属性访问配置"""
        value = self.get(name)
        if value is None:
            # 当访问的配置不存在时返回None，不再抛出异常
            logger.debug(f"配置 '{name}' 不存在，返回None")
            return None
        return value
    
    @property
    def DB_TYPE(self) -> str:
        """数据库类型"""
        db_type = self.get('DB_TYPE', 'sqlite').lower()
        logger.debug(f"DB_TYPE: {db_type}")
        return db_type
    
    @property
    def DB_URL(self) -> str:
        """数据库连接URL"""
        db_url = self.get('DB_URL', 'sqlite:///./sql_app.db')
        logger.debug(f"DB_URL: {db_url}")
        return db_url
    
    @property
    def DB_POOL_SIZE(self) -> int:
        """数据库连接池大小"""
        pool_size = self.get_typed('DB_POOL_SIZE', 10, int)
        logger.debug(f"DB_POOL_SIZE: {pool_size}")
        return pool_size
    
    @property
    def DB_MAX_OVERFLOW(self) -> int:
        """数据库最大溢出连接数"""
        max_overflow = self.get_typed('DB_MAX_OVERFLOW', 20, int)
        logger.debug(f"DB_MAX_OVERFLOW: {max_overflow}")
        return max_overflow
    
    @property
    def DB_POOL_TIMEOUT(self) -> int:
        """数据库连接池超时时间"""
        pool_timeout = self.get_typed('DB_POOL_TIMEOUT', 30, int)
        logger.debug(f"DB_POOL_TIMEOUT: {pool_timeout}")
        return pool_timeout
    
    @property
    def DB_SLOW_QUERY_THRESHOLD(self) -> float:
        """慢查询阈值"""
        slow_query_threshold = self.get_typed('DB_SLOW_QUERY_THRESHOLD', 1.0, float)
        logger.debug(f"DB_SLOW_QUERY_THRESHOLD: {slow_query_threshold}")
        return slow_query_threshold
    
    @property
    def BCRYPT_ROUNDS(self) -> int:
        """bcrypt工作因子"""
        rounds = self.get_typed('BCRYPT_ROUNDS', 12, int)
        logger.debug(f"BCRYPT_ROUNDS: {rounds}")
        return rounds
    
    @property
    def BCRYPT_IDENT(self) -> str:
        """bcrypt标识符"""
        ident = self.get('BCRYPT_IDENT', '2a')
        logger.debug(f"BCRYPT_IDENT: {ident}")
        return ident
    
    @property
    def SECRET_KEY(self) -> str:
        """JWT密钥"""
        secret_key = self.get('SECRET_KEY', 'your-default-secret-key')
        return secret_key
    
    @property
    def REFRESH_SECRET_KEY(self) -> str:
        """JWT刷新密钥"""
        refresh_secret_key = self.get('REFRESH_SECRET_KEY', 'your-default-refresh-secret-key')
        return refresh_secret_key
    
    @property
    def ALGORITHM(self) -> str:
        """JWT算法"""
        algorithm = self.get('ALGORITHM', 'HS256')
        logger.debug(f"ALGORITHM: {algorithm}")
        return algorithm
    
    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """访问令牌有效期（分钟）"""
        expire_minutes = self.get_typed('ACCESS_TOKEN_EXPIRE_MINUTES', 30, int)
        logger.debug(f"ACCESS_TOKEN_EXPIRE_MINUTES: {expire_minutes}")
        return expire_minutes
    
    @property
    def CELERY_BROKER_URL(self) -> str:
        """Celery消息代理地址"""
        broker_url = self.get('CELERY_BROKER_URL', '')
        logger.debug(f"CELERY_BROKER_URL: {broker_url}")
        return broker_url
    
    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Celery任务结果存储后端"""
        result_backend = self.get('CELERY_RESULT_BACKEND', '')
        logger.debug(f"CELERY_RESULT_BACKEND: {result_backend}")
        return result_backend
    
    @property
    def SMTP_SERVER(self) -> str:
        """SMTP服务器地址"""
        smtp_server = self.get('SMTP_SERVER', '')
        logger.debug(f"SMTP_SERVER: {smtp_server}")
        return smtp_server
    
    @property
    def SMTP_PORT(self) -> int:
        """SMTP服务器端口"""
        smtp_port = self.get_typed('SMTP_PORT', 587, int)
        logger.debug(f"SMTP_PORT: {smtp_port}")
        return smtp_port
    
    @property
    def SMTP_USERNAME(self) -> str:
        """SMTP用户名"""
        smtp_username = self.get('SMTP_USERNAME', '')
        logger.debug(f"SMTP_USERNAME: {smtp_username}")
        return smtp_username
    
    @property
    def SMTP_PASSWORD(self) -> str:
        """SMTP密码"""
        smtp_password = self.get('SMTP_PASSWORD', '')
        logger.debug(f"SMTP_PASSWORD: {smtp_password}")
        return smtp_password
    
    @property
    def ENVIRONMENT(self) -> str:
        """应用环境"""
        environment = self.get('ENVIRONMENT', 'development').lower()
        logger.debug(f"ENVIRONMENT: {environment}")
        return environment
    
    @property
    def LOG_LEVEL(self) -> str:
        """日志级别"""
        log_level = self.get('LOG_LEVEL', 'INFO').upper()
        return log_level
    
    @property
    def HOST(self) -> str:
        """服务主机地址"""
        host = self.get('HOST', '127.0.0.1')
        return host
    
    @property
    def PORT(self) -> int:
        """服务端口"""
        port = self.get_typed('PORT', 8000, int)
        return port
    
    @property
    def ALLOWED_ORIGINS(self) -> Union[List[str], str]:
        """CORS允许的源"""
        default_origins = ["http://localhost", "http://localhost:5173"]
        allowed_origins = self.get('ALLOWED_ORIGINS', ",".join(default_origins))
        logger.debug(f"ALLOWED_ORIGINS: {allowed_origins}")
        return allowed_origins
    
    def reload(self):
        """强制重新加载配置"""
        self._config_map.clear()
        self._load_dotenv()
        logger.info("配置已重新加载")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典
        
        Returns:
            配置字典
        """
        result = {}
        # 加载所有已知配置
        for key in dir(self):
            if key.isupper() and not key.startswith('_'):
                result[key] = getattr(self, key)
        return result


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数
    """
    parser = argparse.ArgumentParser(description='CodeC 代码检视系统')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 初始化数据库命令
    db_parser = subparsers.add_parser('init-db', help='初始化数据库')
    
    # 通用参数
    parser.add_argument('--command', type=str, choices=['start', 'init-db'], default='start', help='Command to execute')
    parser.add_argument('--config', type=str, help='Configuration file path (JSON or YAML)')
    parser.add_argument('--db-type', type=str, help='Database type (sqlite, mysql, postgresql, oracle)')
    parser.add_argument('--db-url', type=str, help='Database URL')
    parser.add_argument('--db-pool-size', type=int, help='Database connection pool size')
    parser.add_argument('--db-max-overflow', type=int, help='Database maximum overflow connections')
    parser.add_argument('--db-pool-timeout', type=int, help='Database connection pool timeout')
    parser.add_argument('--db-slow-query-threshold', type=float, help='Slow query threshold')
    parser.add_argument('--bcrypt-rounds', type=int, help='Bcrypt work factor')
    parser.add_argument('--bcrypt-ident', type=str, help='Bcrypt identifier')
    parser.add_argument('--secret-key', type=str, help='Secret key for JWT signing')
    parser.add_argument('--refresh-secret-key', type=str, help='Refresh-secret key for JWT signing')
    parser.add_argument('--algorithm', type=str, help='JWT algorithm')
    parser.add_argument('--access-token-expire-minutes', type=int, help='Access token expiration time (minutes)')
    parser.add_argument('--celery-broker-url', type=str, help='Celery broker URL')
    parser.add_argument('--celery-result-backend', type=str, help='Celery result backend')
    parser.add_argument('--smtp-server', type=str, help='SMTP server address')
    parser.add_argument('--smtp-port', type=int, help='SMTP server port')
    parser.add_argument('--smtp-username', type=str, help='SMTP username')
    parser.add_argument('--smtp-password', type=str, help='SMTP password')
    parser.add_argument('--environment', type=str, choices=['development', 'staging', 'production'], help='Environment mode')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                       help='Logging level')
    parser.add_argument('--host', type=str, help='Host address')
    parser.add_argument('--port', type=int, help='Port number')
    parser.add_argument('--allowed-origins', type=str, help='Comma-separated list of allowed CORS origins')
    return parser.parse_args()

# 配置类实例化
config = Config()

# 明确导出config实例
__all__ = ['config']