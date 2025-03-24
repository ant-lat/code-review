"""
日志配置模块
@author: pgao
@date: 2024-03-13
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import datetime
import sys
from pathlib import Path
import json

# 获取日志级别，默认为INFO
DEFAULT_LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}
LOG_LEVEL = LOG_LEVELS.get(DEFAULT_LOG_LEVEL, logging.INFO)

# 日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(process)d:%(thread)d] %(name)s - %(filename)s:%(lineno)d - %(message)s"

# JSON格式日志
def json_formatter(record):
    log_record = {
        "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
        "level": record.levelname,
        "logger": record.name,
        "message": record.getMessage(),
        "module": record.module,
        "function": record.funcName,
        "line": record.lineno,
    }
    if hasattr(record, "request_id"):
        log_record["request_id"] = record.request_id
    if record.exc_info:
        log_record["exception"] = {
            "type": record.exc_info[0].__name__,
            "message": str(record.exc_info[1]),
        }
    return json.dumps(log_record)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json_formatter(record)

# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

def configure_logging(enable_json=False):
    """
    配置日志系统
    
    Args:
        enable_json (bool): 是否启用JSON格式的日志
    """
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    if enable_json:
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMAT))
    console_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)
    
    # 应用日志文件处理器 (按时间轮转，每天一个文件)
    app_log_path = log_dir / "app.log"
    app_handler = TimedRotatingFileHandler(
        app_log_path,
        when="midnight",
        interval=1,
        backupCount=30  # 保留30天的日志
    )
    if enable_json:
        app_handler.setFormatter(JsonFormatter())
    else:
        app_handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
    app_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(app_handler)
    
    # 错误日志文件处理器 (按大小轮转，只记录ERROR及以上级别)
    error_log_path = log_dir / "error.log"
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10
    )
    if enable_json:
        error_handler.setFormatter(JsonFormatter())
    else:
        error_handler.setFormatter(logging.Formatter(DETAILED_LOG_FORMAT))
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # 禁用对根日志记录器的传播
    for logger_name in ["uvicorn", "fastapi", "sqlalchemy"]:
        logger = logging.getLogger(logger_name)
        logger.propagate = False

# 初始化日志系统
configure_logging()

# 获取应用日志记录器
logger = logging.getLogger("app")

def get_logger(name):
    """
    获取一个指定名称的日志记录器
    
    Args:
        name (str): 日志记录器名称
        
    Returns:
        Logger: 日志记录器对象
    """
    return logging.getLogger(f"app.{name}")

class LoggerAdapter(logging.LoggerAdapter):
    """
    自定义日志适配器，允许添加上下文信息
    
    用法:
        logger_adapter = LoggerAdapter(logger, {"request_id": "123"})
        logger_adapter.info("这是一条带有请求ID的日志")
    """
    def process(self, msg, kwargs):
        # 将上下文信息添加到日志记录中
        kwargs.setdefault("extra", {}).update(self.extra)
        return msg, kwargs