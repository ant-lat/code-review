"""
用户管理路由模块
@author: pgao
@date: 2024-03-13
"""
from fastapi import APIRouter, Query, Depends, HTTPException, Path, Body, Request, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import traceback
import time
from pydantic import BaseModel, EmailStr, Field
import secrets
import string

from app.database import get_db
from app.services.user_service import UserService
from app.core.security import get_password_hash, verify_password, get_current_user
from app.models.user import User
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, ValidationError, AuthorizationError, \
    AuthenticationError
from app.schemas.response import Response, PageResponse, PageInfo
from app.config.logging_config import logger

# 默认密码配置
DEFAULT_PASSWORD = "CodeReview@2024"

# 创建用户管理路由
router = APIRouter(
    prefix="/api/v1/users", 
    tags=["用户管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

# 用户数据模型
class UserCreate(BaseModel):
    """用户创建请求模型"""
    user_id: str  # 用户登录ID
    username: str  # 用户真实姓名
    email: Optional[str] = None  # 邮箱字段，可选
    phone: Optional[str] = None  # 手机号字段，可选
    password: Optional[str] = None
    role_id: Optional[int] = None
    role_ids: Optional[List[int]] = None

class UserUpdate(BaseModel):
    """用户更新请求模型"""
    user_id: Optional[str] = None  # 用户登录ID
    username: Optional[str] = None  # 用户真实姓名
    email: Optional[str] = None  # 邮箱字段，可选
    phone: Optional[str] = None  # 手机号字段，可选
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    user_id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    roles: List[str]
    is_active: bool
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """用户列表响应模型"""
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

@router.get("", response_model=Response[UserListResponse])
async def get_users(
    request: Request,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    username: Optional[str] = Query(None, description="用户名过滤"),
    email: Optional[str] = Query(None, description="邮箱过滤"),
    role: Optional[str] = Query(None, description="角色过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[UserListResponse]:
    """
    获取用户列表，需要管理员权限
    
    Args:
        request (Request): 请求对象
        skip (int): 跳过的记录数
        limit (int): 返回的记录数
        username (str): 用户名过滤
        email (str): 邮箱过滤
        role (str): 角色过滤
        is_active (bool): 是否激活过滤
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[UserListResponse]: 用户列表响应
        
    Raises:
        AuthorizationError: 权限不足
        DatabaseError: 数据库操作错误
    """

    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求用户列表，IP: {client_ip}, 参数: skip={skip}, limit={limit}")
    
    try:
        # 构建过滤条件
        filters = {}
        if username:
            filters["username"] = username
        if email:
            filters["email"] = email
        if role:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active
        
        # 计算页码和每页大小
        page = (skip // limit) + 1 if limit > 0 else 1
        
        # 获取用户列表
        service = UserService(db)
        users, total = service.get_users(filters=filters, page=page, page_size=limit)
        
        # 计算总页数
        pages = (total + limit - 1) // limit if limit > 0 else 0
        
        # 构造用户响应列表
        user_responses = [
            UserResponse(
                id=user.id,
                user_id=user.user_id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                roles=[role.name for role in user.roles] if hasattr(user, 'roles') and user.roles else [],
                is_active=user.is_active,
                created_at=user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
            ) for user in users
        ]
        
        # 使用PageResponse.create构造分页响应
        from app.schemas.response import PageResponse
        
        # 构造响应数据
        response_data = {
            "items": user_responses,
            "total": total,
            "page": page,
            "size": limit,
            "pages": pages
        }
        
        process_time = time.time() - start_time
        logger.info(f"获取用户列表成功，共 {len(users)} 条记录，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="获取用户列表成功"
        )
    except AuthorizationError:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取用户列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取用户列表失败", detail=str(e))

@router.post("", response_model=Response[UserResponse])
async def create_user(
    request: Request,
    user_data: UserCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[UserResponse]:
    """
    创建用户，需要管理员权限
    
    Args:
        request (Request): 请求对象
        user_data (UserCreate): 用户创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[UserResponse]: 用户创建响应
        
    Raises:
        AuthorizationError: 权限不足
        ValidationError: 验证错误
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles):
        logger.warning(f"用户 {current_user.username} 尝试创建用户，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求创建用户 {user_data.user_id}，IP: {client_ip}")
    
    try:
        # 验证必要字段
        if not user_data.email and not user_data.phone:
            raise ValidationError(message="邮箱和手机号至少有一个是必需的")
        
        if not user_data.user_id:
            raise ValidationError(message="用户登录ID是必需的")
            
        # 如果password不存在或为空，使用默认密码
        password = user_data.password
        if not password:
            # 使用配置的默认密码
            password = DEFAULT_PASSWORD
            logger.info(f"为用户 {user_data.user_id} 使用默认密码")
            
        # 验证密码强度
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            logger.warning(f"创建用户 {user_data.user_id} 失败: 密码强度不足")
            raise ValidationError(message=f"密码强度不足: {error_msg}")
        
        # 创建用户数据字典
        user_dict = {
            "user_id": user_data.user_id,
            "username": user_data.username,
            "password": password
        }
        
        # 添加邮箱和手机号
        if user_data.email:
            user_dict["email"] = user_data.email
        
        if user_data.phone:
            user_dict["phone"] = user_data.phone
        
        # 处理角色分配
        if user_data.role_ids:
            user_dict["role_ids"] = user_data.role_ids
        elif user_data.role_id:
            user_dict["role_ids"] = [user_data.role_id]
        
        # 创建用户
        service = UserService(db)
        new_user = service.create_user(user_dict)
        
        # 构造响应
        response_data = UserResponse(
            id=new_user.id,
            user_id=new_user.user_id,
            username=new_user.username,
            email=new_user.email,
            phone=new_user.phone,
            roles=[role.name for role in new_user.roles] if new_user.roles else [],
            is_active=new_user.is_active,
            created_at=new_user.created_at.isoformat() if new_user.created_at else None
        )
        
        process_time = time.time() - start_time
        logger.info(f"用户 {new_user.user_id} 创建成功，ID: {new_user.id}, 处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="用户创建成功"
        )
    except (ValidationError, BusinessError, AuthorizationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"创建用户失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="创建用户失败", detail=str(e))

@router.get("/{user_id}", response_model=Response[UserResponse])
async def get_user(
    request: Request,
    user_id: int = Path(..., ge=1, description="用户ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[UserResponse]:
    """
    获取用户详情，需要管理员权限或本人
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[UserResponse]: 用户详情响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles) and current_user.id != user_id:
        logger.warning(f"用户 {current_user.username} 尝试查看用户 {user_id} 详情，但权限不足")
        raise AuthorizationError(message="权限不足，只能查看自己或需要管理员权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取用户 {user_id} 详情，IP: {client_ip}")
    
    try:
        # 获取用户
        service = UserService(db)
        user = service.get_user_by_id(user_id)
        
        # 构造响应
        response_data = UserResponse(
            id=user.id,
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            roles=[role.name for role in user.roles] if user.roles else [],
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None
        )
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {user.username} 详情成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="获取用户详情成功"
        )
    except (ResourceNotFound, AuthorizationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取用户详情失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取用户详情失败", detail=str(e))

@router.put("/{user_id}", response_model=Response[UserResponse])
async def update_user(
    request: Request,
    user_id: int = Path(..., ge=1, description="用户ID"),
    user_data: UserUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[UserResponse]:
    """
    更新用户信息，需要管理员权限
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        user_data (UserUpdate): 用户更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[UserResponse]: 用户更新响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles):
        logger.warning(f"用户 {current_user.username} 尝试更新用户 {user_id} 信息，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求更新用户 {user_id} 信息，IP: {client_ip}")
    
    try:
        # 转换为字典并过滤None值
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        if not update_data:
            logger.warning(f"更新用户 {user_id} 失败: 未提供有效的更新字段")
            raise ValidationError(message="未提供有效的更新字段")
        
        # 更新用户
        service = UserService(db)
        updated_user = service.update_user(user_id, update_data)
        
        # 构造响应
        response_data = UserResponse(
            id=updated_user.id,
            user_id=updated_user.user_id,
            username=updated_user.username,
            email=updated_user.email,
            phone=updated_user.phone,
            roles=[role.name for role in updated_user.roles] if updated_user.roles else [],
            is_active=updated_user.is_active,
            created_at=updated_user.created_at.isoformat() if updated_user.created_at else None
        )
        
        process_time = time.time() - start_time
        logger.info(f"用户 {updated_user.user_id} 信息更新成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="用户信息更新成功"
        )
    except (ResourceNotFound, BusinessError, ValidationError, AuthorizationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"更新用户信息失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="更新用户信息失败", detail=str(e))

@router.delete("/{user_id}", response_model=Response)
async def delete_user(
    request: Request,
    user_id: int = Path(..., ge=1, description="用户ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    删除用户，需要管理员权限
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 删除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles):
        logger.warning(f"用户 {current_user.username} 尝试删除用户 {user_id}，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    # 不能删除自己
    if current_user.id == user_id:
        logger.warning(f"用户 {current_user.username} 尝试删除自己")
        raise BusinessError(message="不能删除自己的账号")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求删除用户 {user_id}，IP: {client_ip}")
    
    try:
        # 删除用户
        service = UserService(db)
        service.delete_user(user_id)
        
        process_time = time.time() - start_time
        logger.info(f"删除用户 {user_id} 成功，处理时间: {process_time:.2f}秒")
        response_data={
            "message": "用户删除成功"
        }
        return Response(
            data=response_data,
            message="用户删除成功"
        )
    except ResourceNotFound:
        # 如果用户已经不存在，也视为删除成功
        process_time = time.time() - start_time
        logger.info(f"用户 {user_id} 不存在或已被删除，处理时间: {process_time:.2f}秒")
        return Response(message="用户删除成功")
    except (BusinessError, AuthorizationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"删除用户失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="删除用户失败", detail=str(e))

@router.post("/{user_id}/roles", response_model=Response)
async def assign_roles_to_user(
    request: Request,
    user_id: int = Path(..., ge=1, description="用户ID"),
    role_ids: List[int] = Body(..., description="角色ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    为用户分配角色
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        role_ids (List[int]): 角色ID列表
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 角色分配响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles):
        logger.warning(f"用户 {current_user.username} 尝试为用户分配角色，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求为用户 {user_id} 分配角色，角色数量: {len(role_ids)}，IP: {client_ip}")
    
    try:
        service = UserService(db)
        
        service.assign_roles(user_id, role_ids)
        
        process_time = time.time() - start_time
        logger.info(f"为用户 {user_id} 分配角色成功，处理时间: {process_time:.2f}秒")
        
        return Response(message="角色分配成功")
    except (ResourceNotFound, BusinessError, AuthorizationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"为用户 {user_id} 分配角色失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="角色分配失败", detail=str(e))

@router.get("/{user_id}/roles", response_model=Response[List[Dict[str, Any]]])
async def get_user_roles(
    request: Request,
    user_id: int = Path(..., ge=1, description="用户ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取用户已分配的角色列表
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 用户角色列表响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles) and current_user.id != user_id:
        logger.warning(f"用户 {current_user.username} 尝试获取用户 {user_id} 角色列表，但权限不足")
        raise AuthorizationError(message="权限不足，只能查看自己的角色或需要管理员权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取用户 {user_id} 的角色列表，IP: {client_ip}")
    
    try:
        service = UserService(db)
        
        user_roles = service.get_user_roles(user_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {user_id} 角色列表成功，共 {len(user_roles)} 个角色，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=user_roles,
            message="获取用户角色列表成功"
        )
    except ResourceNotFound:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取用户 {user_id} 角色列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取用户角色列表失败", detail=str(e))

@router.delete("/{user_id}/roles/{role_id}", response_model=Response)
async def remove_role_from_user(
    request: Request,
    user_id: int = Path(..., ge=1, description="用户ID"),
    role_id: int = Path(..., description="角色ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    从用户中移除指定角色
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        role_id (int): 角色ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 移除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户或角色不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles):
        logger.warning(f"用户 {current_user.username} 尝试从用户移除角色，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求从用户 {user_id} 移除角色 {role_id}，IP: {client_ip}")
    
    try:
        service = UserService(db)
        
        service.remove_role(user_id, role_id)
        
        process_time = time.time() - start_time
        logger.info(f"从用户 {user_id} 移除角色 {role_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(message="移除角色成功")
    except (ResourceNotFound, BusinessError, AuthorizationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"从用户 {user_id} 移除角色 {role_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="移除角色失败", detail=str(e))

# 密码强度验证函数，在文件顶部适当位置添加
def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    验证密码强度
    
    Args:
        password (str): 要验证的密码
        
    Returns:
        tuple[bool, str]: (是否通过, 错误消息)
    """
    if len(password) < 8:
        return False, "密码长度至少为8个字符"
    
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_digit = any(char.isdigit() for char in password)
    has_special = any(not char.isalnum() for char in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "密码必须包含大写字母、小写字母和数字"
    
    if not has_special:
        return False, "密码必须包含至少一个特殊字符"
    
    return True, ""

# 密码修改相关模型
class PasswordChangeRequest(BaseModel):
    """密码修改请求模型"""
    current_password: str = Field(..., min_length=6, max_length=50, description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, description="确认密码")

class PasswordResetRequest(BaseModel):
    """密码重置请求模型（管理员使用）"""
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=50, description="确认密码")

@router.post("/change-password", response_model=Response)
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    修改当前用户密码
    
    Args:
        request (Request): 请求对象
        password_data (PasswordChangeRequest): 密码修改数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 密码修改响应
        
    Raises:
        ValidationError: 验证错误
        AuthenticationError: 认证错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求修改密码，IP: {client_ip}")
    
    try:
        # 验证新密码和确认密码是否一致
        if password_data.new_password != password_data.confirm_password:
            logger.warning(f"用户 {current_user.username} 修改密码失败: 新密码和确认密码不一致")
            raise ValidationError(message="新密码和确认密码不一致")
        
        # 验证新密码强度
        is_valid, error_msg = validate_password_strength(password_data.new_password)
        if not is_valid:
            logger.warning(f"用户 {current_user.username} 修改密码失败: 新密码强度不足")
            raise ValidationError(message=f"新密码强度不足: {error_msg}")
        
        # 修改密码
        service = UserService(db)
        success = service.change_password(
            current_user.id, 
            password_data.current_password, 
            password_data.new_password
        )
        
        if not success:
            raise DatabaseError(message="修改密码失败，请稍后重试")
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 密码修改成功，处理时间: {process_time:.2f}秒")
        
        return Response(message="密码修改成功")
    except (ValidationError, AuthenticationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"修改密码失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="修改密码失败", detail=str(e))

@router.post("/{user_id}/reset-password", response_model=Response)
async def reset_user_password(
    request: Request,
    user_id: int = Path(..., ge=1, description="用户ID"),
    password_data: PasswordResetRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    重置用户密码（管理员功能）
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        password_data (PasswordResetRequest): 密码重置数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 密码重置响应
        
    Raises:
        AuthorizationError: 权限不足
        ValidationError: 验证错误
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not any(role.name == "admin" for role in current_user.roles):
        logger.warning(f"用户 {current_user.username} 尝试重置用户 {user_id} 密码，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"管理员 {current_user.username} 请求重置用户 {user_id} 密码，IP: {client_ip}")
    
    try:
        # 验证新密码和确认密码是否一致
        if password_data.new_password != password_data.confirm_password:
            logger.warning(f"重置用户 {user_id} 密码失败: 新密码和确认密码不一致")
            raise ValidationError(message="新密码和确认密码不一致")
        
        # 验证新密码强度
        is_valid, error_msg = validate_password_strength(password_data.new_password)
        if not is_valid:
            logger.warning(f"重置用户 {user_id} 密码失败: 新密码强度不足")
            raise ValidationError(message=f"新密码强度不足: {error_msg}")
        
        # 重置密码
        service = UserService(db)
        
        # 检查用户是否存在
        user = service.get_user_by_id(user_id)
        
        # 调用服务重置密码
        success = service.reset_password(user_id, password_data.new_password)
        if not success:
            raise DatabaseError(message="重置密码失败，请稍后重试")
        
        process_time = time.time() - start_time
        logger.info(f"重置用户 {user_id} 密码成功，处理时间: {process_time:.2f}秒")
        
        return Response(message="密码重置成功")
    except (ValidationError, ResourceNotFound, AuthorizationError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"重置用户 {user_id} 密码失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="重置密码失败", detail=str(e))