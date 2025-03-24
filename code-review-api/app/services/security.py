"""
安全服务模块
@author: pgao
@date: 2024-03-13
"""
from passlib.context import CryptContext
import secrets
import string
import re
from typing import Tuple

from app.config.logging_config import logger

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password (str): 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password (str): 明文密码
        hashed_password (str): 哈希后的密码
        
    Returns:
        bool: 验证是否通过
    """
    return pwd_context.verify(plain_password, hashed_password)

def generate_password(length: int = 12) -> str:
    """
    生成强密码
    
    Args:
        length (int): 密码长度，默认12位
        
    Returns:
        str: 生成的强密码
    """
    # 确保密码包含数字、大写字母、小写字母和特殊字符
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_-+=<>?"
    
    # 确保包含至少一个数字、大写字母、小写字母和特殊字符
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in password) and
            any(c.isupper() for c in password) and
            any(c.isdigit() for c in password) and
            any(c in "!@#$%^&*()_-+=<>?" for c in password)):
            break
    
    return password

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password (str): 密码
        
    Returns:
        Tuple[bool, str]: (是否通过, 错误消息)
    """
    # 检查长度
    if len(password) < 8:
        return False, "密码长度必须大于或等于8位"
    
    # 检查是否包含数字
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含至少一个数字"
    
    # 检查是否包含大写字母
    if not any(c.isupper() for c in password):
        return False, "密码必须包含至少一个大写字母"
    
    # 检查是否包含小写字母
    if not any(c.islower() for c in password):
        return False, "密码必须包含至少一个小写字母"
    
    # 检查是否包含特殊字符
    if not any(c in "!@#$%^&*()_-+=<>?" for c in password):
        return False, "密码必须包含至少一个特殊字符"
    
    return True, ""

def sanitize_input(input_str: str) -> str:
    """
    清理输入字符串，防止XSS攻击
    
    Args:
        input_str (str): 输入字符串
        
    Returns:
        str: 清理后的字符串
    """
    if not input_str:
        return ""
        
    # 替换特殊字符
    input_str = input_str.replace("&", "&amp;")
    input_str = input_str.replace("<", "&lt;")
    input_str = input_str.replace(">", "&gt;")
    input_str = input_str.replace("\"", "&quot;")
    input_str = input_str.replace("'", "&#x27;")
    input_str = input_str.replace("/", "&#x2F;")
    
    return input_str