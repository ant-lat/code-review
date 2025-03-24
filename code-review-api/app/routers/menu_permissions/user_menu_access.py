"""
用户菜单访问路由模块
整合用户菜单与权限访问相关功能
@author: pgao
@date: 2024-03-13
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path, Request, status
from sqlalchemy.orm import Session
import time
import traceback

from app.database import get_db
from app.core.security import get_current_user, check_permission
from app.models.user import User
from app.models.menu import Menu
from app.services.menu_service import MenuService
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError
from app.schemas.response import Response
from app.config.logging_config import logger

router = APIRouter(
    prefix="/api/v1/user-access",
    tags=["用户菜单权限"]
)

@router.get("/menus", response_model=Response[List[Dict[str, Any]]])
async def get_current_user_menus(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取当前用户可访问的菜单列表
    
    Args:
        request (Request): 请求对象
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 用户菜单列表响应
        
    Raises:
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取个人菜单，IP: {client_ip}")
    
    try:
        service = MenuService(db)
        user_menus = service.get_user_menus(current_user.id)
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {current_user.username} 菜单成功，共 {len(user_menus)} 个菜单，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=user_menus,
            message="获取用户菜单成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取用户菜单失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取用户菜单失败", detail=str(e))

@router.get("/permissions", response_model=Response[List[Dict[str, Any]]])
async def get_current_user_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取当前用户所有权限列表
    
    Args:
        request (Request): 请求对象
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 用户权限列表响应
        
    Raises:
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取个人权限，IP: {client_ip}")
    
    try:
        from app.core.security import get_user_permissions
        permission_objects = get_user_permissions(db, current_user.id)
        
        # 转换为适合前端的格式
        permissions = []
        for p in permission_objects:
            permissions.append({
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "description": p.description
            })
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {current_user.username} 权限成功，共 {len(permissions)} 个权限，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=permissions,
            message="获取用户权限成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取用户权限失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取用户权限失败", detail=str(e))

@router.get("/all-permissions", response_model=Response[List[Dict[str, Any]]])
async def get_all_permissions(
    request: Request,
    type: Optional[str] = Query(None, description="权限类型，例如：project, system 等"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取系统所有权限列表，可按类型过滤
    
    Args:
        request (Request): 请求对象
        type (Optional[str]): 权限类型，用于过滤
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 权限列表响应
        
    Raises:
        AuthorizationError: 权限不足
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取系统权限列表，类型: {type}，IP: {client_ip}")
    
    try:
        # 获取权限服务
        permission_service = PermissionService(db)
        
        # 获取所有权限
        if type:
            permissions = permission_service.get_permissions_by_type(type)
        else:
            permissions = permission_service.get_all_permissions()
        
        # 转换为适合前端的格式
        formatted_permissions = []
        for p in permissions:
            formatted_permissions.append({
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "description": p.description,
                "group": p.group,
                "type": p.type
            })
        
        process_time = time.time() - start_time
        logger.info(f"获取系统权限列表成功，共 {len(formatted_permissions)} 个权限，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=formatted_permissions,
            message="获取系统权限列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取系统权限列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取系统权限列表失败", detail=str(e))

@router.get("/check-permission", response_model=Response[bool])
async def check_user_permission(
    request: Request,
    permission_code: Optional[str] = Query(None, description="权限代码"),
    permission_id: Optional[int] = Query(None, description="权限ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[bool]:
    """
    检查当前用户是否拥有指定权限
    
    Args:
        request (Request): 请求对象
        permission_code (Optional[str]): 权限代码
        permission_id (Optional[int]): 权限ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[bool]: 权限检查结果
        
    Raises:
        BusinessError: 参数错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    
    # 检查参数
    if permission_code is None and permission_id is None:
        raise BusinessError(message="必须提供permission_code或permission_id")
    
    permission_info = f"permission_code={permission_code}" if permission_code else f"permission_id={permission_id}"
    logger.info(f"用户 {current_user.username} 请求检查权限 {permission_info}，IP: {client_ip}")
    
    try:
        # 根据提供的参数进行检查
        if permission_id is not None:
            has_permission = check_permission(db, current_user.id, permission_id=permission_id)
        else:
            has_permission = check_permission(db, current_user.id, permission_code=permission_code)
        
        process_time = time.time() - start_time
        logger.info(f"检查用户 {current_user.username} 权限 {permission_info} 结果: {has_permission}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=has_permission,
            message=f"用户{'有' if has_permission else '没有'}该权限"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"检查用户权限失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="检查用户权限失败", detail=str(e)) 