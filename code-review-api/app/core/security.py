"""
安全模块
处理认证、授权等安全相关功能
@author: pgao
@date: 2024-03-13
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional, Dict, Any, List, Union
from sqlalchemy.orm import Session, joinedload, contains_eager
from functools import wraps
from pydantic import BaseModel, Field
import re
import secrets
import string
import time
import bcrypt
import pytz
import traceback

from app.config import config
from app.database import get_db, DBUtils
from app.models.user import User
from app.models.role import Role
from app.config.logging_config import logger
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission

# 在文件开头添加这段代码来修复bcrypt兼容性问题
if not hasattr(bcrypt, '__about__'):
    # 为bcrypt添加缺失的__about__属性
    bcrypt.__about__ = type('obj', (object,), {
        '__version__': getattr(bcrypt, '__version__', '4.1.1')
    })

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# 令牌过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES

class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    exp: Optional[datetime] = None

class UserPermission(BaseModel):
    """
    用户权限类，用于存储用户权限信息
    """
    id: int
    permission_id: int
    code: str
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    创建访问令牌
    
    Args:
        data (Dict[str, Any]): 令牌中包含的数据
        expires_delta (Optional[timedelta], optional): 过期时间增量. Defaults to None.
        
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()

    if expires_delta:
        expire = int((datetime.utcnow() + expires_delta).timestamp())
    else:
        expire = int((datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp())

    to_encode.update({"exp": expire})
    to_encode.update({"iat": int(datetime.utcnow().timestamp())})  # 添加发行时间
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码
    
    Args:
        plain_password (str): 明文密码
        hashed_password (str): 哈希密码
        
    Returns:
        bool: 是否验证通过
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        # 尝试直接使用bcrypt进行验证
        try:
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception as e2:
            logger.error(f"bcrypt直接验证也失败: {str(e2)}")
            return False

def get_password_hash(password: str) -> str:
    """
    生成密码哈希
    
    Args:
        password (str): 明文密码
        
    Returns:
        str: 哈希密码
    """
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    通过用户名获取用户
    
    Args:
        db (Session): 数据库会话
        username (str): 用户名
        
    Returns:
        Optional[User]: 用户对象，如果不存在则为None
    """
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    认证用户
    
    Args:
        db (Session): 数据库会话
        username (str): 用户名
        password (str): 密码
        
    Returns:
        Optional[User]: 认证通过的用户对象，如果认证失败则为None
    """
    user = get_user_by_username(db, username)

    if not user:
        return None

    # 注意：User模型中的密码字段是password_hash，而不是password
    if not verify_password(password, user.password_hash):
        return None

    return user

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    获取当前用户
    
    Args:
        db (Session): 数据库会话
        token (str): 访问令牌
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 认证失败
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="认证凭据无效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码令牌
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_login_id = payload.get("sub")
        user_id = payload.get("user_id")
        
        # 验证令牌
        if user_login_id is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 获取用户
    try:
        # 使用user_id字段查询用户
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or user.user_id != user_login_id:
            raise credentials_exception
        
        # 验证用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=401,
                detail="用户已被禁用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except Exception as e:
        logger.error(f"获取当前用户时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        raise credentials_exception

def get_user_permissions(db: Session, user_id: int) -> List[UserPermission]:
    """
    获取用户权限信息
    
    Args:
        db (Session): 数据库会话
        user_id (int): 用户ID
        
    Returns:
        List[UserPermission]: 用户权限信息列表
    """
    try:
        # 创建一个新的数据库会话，避免并发问题
        with next(get_db()) as new_db:
            # 获取用户的所有角色
            user_roles = new_db.query(Role).join(
                UserRole, UserRole.role_id == Role.id
            ).filter(
                UserRole.user_id == user_id,
                UserRole.is_active == True
            ).all()

            if not user_roles:
                return []

            # 获取用户的所有权限
            permissions = []
            role_ids = [role.id for role in user_roles]

            # 通过角色ID获取所有关联的权限
            permission_records = new_db.query(Permission).join(
                RolePermission, RolePermission.permission_id == Permission.id
            ).filter(
                RolePermission.role_id.in_(role_ids)
            ).all()

            # 将权限记录转换为UserPermission对象
            for permission in permission_records:
                perm_dict = {
                    "id": permission.id,
                    "permission_id": permission.id,
                    "code": permission.code,
                    "name": permission.name,
                    "description": permission.description
                }
                
                # 检查权限是否已经存在于结果中（避免重复）
                if not any(p.permission_id == permission.id for p in permissions):
                    permissions.append(UserPermission(**perm_dict))
                    
        return permissions
    except Exception as e:
        logger.error(f"获取用户权限时发生错误: {str(e)}")
        return []

def check_permission(db: Session, user_id: int, permission_code: str) -> bool:
    """
    检查用户是否具有指定的权限
    
    Args:
        db (Session): 数据库会话
        user_id (int): 用户ID
        permission_code (str): 权限代码
        
    Returns:
        bool: 是否具有权限
    """
    try:
        # 创建一个新的数据库会话，避免并发问题
        with next(get_db()) as new_db:
            # 获取用户所有的角色ID
            user_role_ids = new_db.query(UserRole.role_id).filter(
                UserRole.user_id == user_id,
                UserRole.is_active == True
            ).all()
            
            if not user_role_ids:
                return False
                
            role_ids = [r.role_id for r in user_role_ids]
            
            # 查询特定权限码的权限ID
            permission = new_db.query(Permission.id).filter(
                Permission.code == permission_code
            ).first()
            
            if not permission:
                return False
                
            permission_id = permission.id
            
            # 查询用户角色是否具有该权限
            role_permission = new_db.query(RolePermission).filter(
                RolePermission.role_id.in_(role_ids),
                RolePermission.permission_id == permission_id
            ).first()
            
            return role_permission is not None
    except Exception as e:
        logger.error(f"检查权限时发生错误: {str(e)}")
        return False

def check_role(db: Session, user_id: int, role_names: List[str]) -> bool:
    """
    检查用户是否拥有指定角色
    
    Args:
        db (Session): 数据库会话
        user_id (int): 用户ID
        role_names (List[str]): 角色名称列表
        
    Returns:
        bool: 是否拥有任一角色
    """
    # 获取用户角色
    user_roles = db.query(Role).join(
        UserRole, UserRole.role_id == Role.id
    ).filter(
        UserRole.user_id == user_id,
        UserRole.is_active == True
    ).all()

    user_role_names = [role.name for role in user_roles]

    # 检查是否有交集
    return any(role in user_role_names for role in role_names)

def check_project_permission(db: Session, user_id: int, project_id: int, required_role: Optional[str] = None) -> bool:
    """
    检查用户是否有项目权限
    
    Args:
        db (Session): 数据库会话
        user_id (int): 用户ID
        project_id (int): 项目ID
        required_role (Optional[str]): 所需项目角色
        
    Returns:
        bool: 是否有权限
    """
    from app.models.project_role import ProjectRole

    # 构建查询条件
    conditions = [
        ProjectRole.user_id == user_id,
        ProjectRole.project_id == project_id,
        ProjectRole.is_active == True
    ]

    # 如果指定了所需角色，添加角色条件
    if required_role:
        conditions.append(ProjectRole.role.has(name=required_role))

    # 查询用户在项目中的角色
    user_project_role = db.query(ProjectRole).filter(*conditions).first()

    return user_project_role is not None

def generate_password(length: int = 12) -> str:
    """
    生成随机密码
    
    Args:
        length (int, optional): 密码长度. Defaults to 12.
        
    Returns:
        str: 随机密码
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))

    # 确保密码同时包含字母、数字和特殊字符
    while (not re.search('[a-zA-Z]', password) or
           not re.search('[0-9]', password) or
           not re.search('[!@#$%^&*()-_=+]', password)):
        password = ''.join(secrets.choice(alphabet) for _ in range(length))

    return password

def require_permission(permission_code: str):
    """
    权限装饰器，要求特定权限
    
    Args:
        permission_code (str): 权限代码
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            current_user = None

            # 查找 request 参数
            for key, val in kwargs.items():
                if isinstance(val, Request):
                    request = val
                if isinstance(val, User):
                    current_user = val

            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                    if isinstance(arg, User):
                        current_user = arg

            if not current_user:
                for key, val in kwargs.items():
                    if key == "current_user" and isinstance(val, User):
                        current_user = val

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未认证",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 获取数据库会话
            db = next((val for key, val in kwargs.items() if key == "db" and isinstance(val, Session)), None)

            if not db:
                db = get_db()

            # 获取用户权限信息
            permissions = get_user_permissions(db, current_user.id)

            # 检查是否有所需权限
            if permission_code not in [p.code for p in permissions]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要 {permission_code} 权限"
                )

            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(f"执行 {func.__name__} 耗时 {execution_time:.2f} 秒")

            return result
        return wrapper
    return decorator