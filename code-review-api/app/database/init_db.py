"""
数据库初始化模块
主要功能：根据配置执行数据库初始化脚本
@author: pgao
@date: 2024-03-13
"""
import os
import re
import sys
import pathlib
from sqlalchemy import create_engine, text

# 确保项目根目录在Python路径中
ROOT_DIR = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.config.logging_config import logger
from app.config import config

def init_db():
    """
    初始化数据库
    
    根据配置的数据库类型，执行对应的SQL初始化脚本
    支持的数据库: SQLite, MySQL, PostgreSQL, Oracle
    
    Raises:
        ValueError: 当数据库URL格式无效、不支持的数据库类型或找不到SQL脚本文件时抛出
    """
    print("init_db")
    # 获取数据库URL，默认使用SQLite
    db_url = config.DB_URL
    logger.info(f"数据库URL: {db_url}")
    print(db_url)
    # 解析数据库类型
    db_type_match = re.match(r'^([a-zA-Z]+)', db_url.split('://')[0].lower())
    if not db_type_match:
        raise ValueError(f'无效的数据库URL格式: {db_url}')
    
    db_type = db_type_match.group(1)
    
    # 数据库类型映射到对应的SQL脚本文件
    db_script_mapping = {
        'sqlite': 'SQLite.sql',
        'mysql': 'MySQL.sql',
        'postgresql': 'PostgreSQL.sql',
        'oracle': 'Oracle.sql'
    }
    print(db_type)
    # 获取对应的SQL脚本文件名
    if db_type not in db_script_mapping:
        raise ValueError(f'不支持的数据库类型: {db_type}。支持的类型有: {list(db_script_mapping.keys())}')
    
    script_filename = db_script_mapping[db_type]
    logger.info(f"使用脚本文件: {script_filename}")
    print(script_filename)
    # 构建SQL脚本文件的完整路径
    script_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db')
    script_path = os.path.join(script_dir, script_filename)
    print(script_path)
    # 如果找不到脚本文件，可能是因为路径问题，尝试绝对路径
    if not os.path.exists(script_path):
        # 尝试从项目根目录开始查找
        alt_script_path = os.path.join(ROOT_DIR, 'app', 'db', script_filename)
        print(alt_script_path)
        if os.path.exists(alt_script_path):
            script_path = alt_script_path
            logger.info(f"使用替代路径找到脚本文件: {script_path}")
        else:
            raise ValueError(f'未找到SQL脚本文件，尝试了以下路径: \n1. {script_path}\n2. {alt_script_path}')
    
    logger.info(f'使用 {script_filename} 初始化数据库')
    
    engine = create_engine(
        db_url,
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_timeout=config.DB_POOL_TIMEOUT
    )

    # 开始执行初始化脚本
    with engine.connect() as connection:
        with open(script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 使用事务执行初始化脚本
        trans = connection.begin()
        try:
            # 按分号分割SQL语句并执行
            for statement in sql_script.split(';'):
                stripped_stmt = statement.strip()
                if stripped_stmt:
                    logger.debug(f'执行SQL语句: {stripped_stmt}')
                    connection.execute(text(stripped_stmt))
            trans.commit()
            logger.info('所有SQL语句执行并提交成功')
        except Exception as e:
            trans.rollback()
            logger.error(f"初始化失败: {str(e)}")
            raise
    
    logger.info('数据库初始化完成')

if __name__ == '__main__':
    init_db()
    logger.info('数据库初始化成功')