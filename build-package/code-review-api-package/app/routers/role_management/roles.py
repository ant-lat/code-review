"""
角色管理路由模块
@author: pgao
@date: 2024-03-13
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import time
import traceback

from app.database import get_db
from app.services.role_service import RoleService
from app.core.security import get_current_user, check_permission
from app.models.user import User
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError
from app.schemas.response import Response
from app.config.logging_config import logger
from pydantic import BaseModel

# 创建路由器
router = APIRouter(
    prefix="/api/v1/roles", 
    tags=["角色管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

class RoleCreate(BaseModel):
    """角色创建请求模型"""
    name: str
    description: Optional[str] = None
    role_type: Optional[str] = "user"
    permissions: Optional[List[str]] = None

class RoleUpdate(BaseModel):
    """角色更新请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class PermissionAssign(BaseModel):
    """权限分配请求模型"""
    permission_codes: Optional[List[str]] = None
    permission_ids: Optional[List[int]] = None
    expires_at: Optional[datetime] = None

class RoleResponse(BaseModel):
    """角色响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    role_type: str
    permissions: List[str] = []
    project_count: Optional[int] = 0
    user_count: Optional[int] = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PermissionResponse(BaseModel):
    """权限响应模型"""
    code: str
    name: str = ""
    description: Optional[str] = None
    module: Optional[str] = None

@router.get("", response_model=Response[Dict[str, Any]])
async def get_roles(
    request: Request,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的记录数"),
    name: Optional[str] = Query(None, description="按名称筛选"),
    role_type: Optional[str] = Query(None, description="按角色类型筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取角色列表
    
    Args:
        request (Request): 请求对象
        skip (int): 跳过的记录数
        limit (int): 返回的记录数
        name (str, optional): 按名称筛选
        role_type (str, optional): 按角色类型筛选
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 角色列表响应
        
    Raises:
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取角色列表，跳过: {skip}，限制: {limit}，名称筛选: {name}，角色类型: {role_type}，IP: {client_ip}")
    
    try:
        service = RoleService(db)
        
        # 构造过滤条件
        filters = {}
        if name:
            filters["name"] = name
        if role_type:
            filters["role_type"] = role_type
            
        roles, total = service.get_roles(filters, page=skip//limit + 1, page_size=limit)
        
        # 转换为响应格式
        role_list = []
        for role in roles:
            role_list.append({
                "id": role.id,
                "name": role.name,
                "description": role.description,
                "role_type": role.role_type,
                "permissions": role.permissions if role.permissions else [],
                "created_at": role.created_at.isoformat() if role.created_at else None,
                "updated_at": role.updated_at.isoformat() if role.updated_at else None
            })
        
        process_time = time.time() - start_time
        logger.info(f"获取角色列表成功，共 {len(role_list)} 条记录，处理时间: {process_time:.2f}秒")
        
        return Response(
            data={
                "items": role_list,
                "total": total
            },
            message="获取角色列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取角色列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取角色列表失败", detail=str(e))

@router.post("", response_model=Response[RoleResponse], status_code=status.HTTP_201_CREATED)
async def create_role(
    request: Request,
    role_data: RoleCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[RoleResponse]:
    """
    创建角色
    
    Args:
        request (Request): 请求对象
        role_data (RoleCreate): 角色创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[RoleResponse]: 角色创建响应
        
    Raises:
        AuthorizationError: 权限不足
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求创建角色 {role_data.name}，IP: {client_ip}")
    
    # 检查权限
    if current_user.role != "admin":
        logger.warning(f"用户 {current_user.username} 尝试创建角色，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    try:
        service = RoleService(db)
        
        role = service.create_role({
            "name": role_data.name,
            "description": role_data.description,
            "role_type": role_data.role_type,
            "permissions": role_data.permissions
        })
        
        # 转换为响应格式
        response_data = RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            role_type=role.role_type,
            permissions=role.permissions if role.permissions else [],
            created_at=role.created_at.isoformat() if role.created_at else None,
            updated_at=role.updated_at.isoformat() if role.updated_at else None
        )
        
        process_time = time.time() - start_time
        logger.info(f"创建角色成功，ID: {role.id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="角色创建成功"
        )
    except BusinessError:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"创建角色失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="创建角色失败", detail=str(e))

@router.get("/{role_id}", response_model=Response[RoleResponse])
async def get_role(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[RoleResponse]:
    """
    获取角色详情
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[RoleResponse]: 角色详情响应
        
    Raises:
        ResourceNotFound: 角色不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取角色 {role_id} 详情，IP: {client_ip}")
    
    try:
        service = RoleService(db)
        
        role = service.get_role(role_id)
        
        # 获取关联数量
        user_count = service.get_role_user_count(role_id)
        project_count = service.get_role_project_count(role_id) if role.role_type == "project" else 0
        
        # 格式化响应
        response_data = RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            role_type=role.role_type,
            permissions=role.permissions if role.permissions else [],
            user_count=user_count,
            project_count=project_count,
            created_at=role.created_at.isoformat() if role.created_at else None,
            updated_at=role.updated_at.isoformat() if role.updated_at else None
        )
        
        process_time = time.time() - start_time
        logger.info(f"获取角色 {role_id} 详情成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="获取角色详情成功"
        )
    except ResourceNotFound:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取角色 {role_id} 详情失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取角色详情失败", detail=str(e))

@router.put("/{role_id}", response_model=Response[RoleResponse])
async def update_role(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    role_data: RoleUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[RoleResponse]:
    """
    更新角色
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        role_data (RoleUpdate): 角色更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[RoleResponse]: 角色更新响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 角色不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求更新角色 {role_id}，IP: {client_ip}")
    
    # 检查权限
    if current_user.role != "admin":
        logger.warning(f"用户 {current_user.username} 尝试更新角色，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    try:
        service = RoleService(db)
        
        updated_role = service.update_role(role_id, {
            "name": role_data.name,
            "description": role_data.description,
            "permissions": role_data.permissions
        })
        
        # 转换为响应格式
        response_data = RoleResponse(
            id=updated_role.id,
            name=updated_role.name,
            description=updated_role.description,
            role_type=updated_role.role_type,
            permissions=updated_role.permissions if updated_role.permissions else [],
            created_at=updated_role.created_at.isoformat() if updated_role.created_at else None,
            updated_at=updated_role.updated_at.isoformat() if updated_role.updated_at else None
        )
        
        process_time = time.time() - start_time
        logger.info(f"更新角色 {role_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="角色更新成功"
        )
    except (ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"更新角色 {role_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="更新角色失败", detail=str(e))

@router.delete("/{role_id}", response_model=Response)
async def delete_role(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    删除角色
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 删除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 角色不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求删除角色 {role_id}，IP: {client_ip}")
    
    # 检查权限
    if current_user.role != "admin":
        logger.warning(f"用户 {current_user.username} 尝试删除角色，但权限不足")
        raise AuthorizationError(message="权限不足，需要管理员权限")
    
    try:
        service = RoleService(db)
        
        service.delete_role(role_id)
        
        process_time = time.time() - start_time
        logger.info(f"删除角色 {role_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="角色删除成功"
        )
    except (ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"删除角色 {role_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="删除角色失败", detail=str(e))

@router.get("/{role_id}/permissions", response_model=Response[List[PermissionResponse]])
async def get_role_permissions(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[PermissionResponse]]:
    """
    获取角色权限列表
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[PermissionResponse]]: 角色权限列表响应
        
    Raises:
        ResourceNotFound: 角色不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取角色 {role_id} 权限列表，IP: {client_ip}")
    
    try:
        service = RoleService(db)
        
        permissions = service.get_role_permissions(role_id)
        
        # 格式化响应 - 权限现在是字符串代码列表
        response_data = [PermissionResponse(code=code) for code in permissions]
        
        process_time = time.time() - start_time
        logger.info(f"获取角色 {role_id} 权限列表成功，共 {len(response_data)} 个权限，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="获取角色权限列表成功"
        )
    except ResourceNotFound:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取角色 {role_id} 权限列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取角色权限列表失败", detail=str(e))

@router.post("/{role_id}/permissions", response_model=Response)
async def assign_permissions(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    perm_data: PermissionAssign = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    分配权限给角色
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        perm_data (PermissionAssign): 权限分配数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 权限分配响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 角色不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    codes_str = ", ".join(perm_data.permission_codes[:5]) + (
        f"...等共{len(perm_data.permission_codes)}个" if len(perm_data.permission_codes) > 5 else ""
    )
    logger.info(f"用户 {current_user.username} 请求为角色 {role_id} 分配权限 {codes_str}，IP: {client_ip}")
    
    # 检查权限
    if not check_permission(db, current_user.id, "system:role:edit"):
        logger.warning(f"用户 {current_user.username} 尝试分配权限，但权限不足")
        raise AuthorizationError(message="权限不足，需要角色管理权限")
    
    try:
        service = RoleService(db)
        
        service.assign_permissions(
            role_id=role_id,
            permission_codes=perm_data.permission_codes,
            permission_ids=perm_data.permission_ids,
            expires_at=perm_data.expires_at
        )
        
        process_time = time.time() - start_time
        logger.info(f"为角色 {role_id} 分配权限成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="权限分配成功"
        )
    except (ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"为角色 {role_id} 分配权限失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="权限分配失败", detail=str(e))

@router.post("/{role_id}/menus", response_model=Response)
async def assign_menus_to_role(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    menu_ids: List[int] = Body(..., description="菜单ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    为角色分配菜单权限
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        menu_ids (List[int]): 菜单ID列表
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 菜单分配响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 角色不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:role:edit"):
        logger.warning(f"用户 {current_user.username} 尝试为角色分配菜单，但权限不足")
        raise AuthorizationError(message="权限不足，需要角色编辑权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求为角色 {role_id} 分配菜单，菜单数量: {len(menu_ids)}，IP: {client_ip}")
    
    try:
        service = RoleService(db)
        
        service.assign_menus_to_role(role_id, menu_ids)
        
        process_time = time.time() - start_time
        logger.info(f"为角色 {role_id} 分配菜单成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="菜单分配成功"
        )
    except (ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"为角色 {role_id} 分配菜单失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="菜单分配失败", detail=str(e))

@router.get("/{role_id}/menus", response_model=Response[List[Dict[str, Any]]])
async def get_role_menus(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取角色已分配的菜单列表
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 角色菜单列表响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 角色不存在
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:role:view"):
        logger.warning(f"用户 {current_user.username} 尝试获取角色菜单，但权限不足")
        raise AuthorizationError(message="权限不足，需要角色查看权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取角色 {role_id} 的菜单列表，IP: {client_ip}")
    
    try:
        service = RoleService(db)
        
        role_menus = service.get_role_menus(role_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取角色 {role_id} 菜单列表成功，共 {len(role_menus)} 个菜单，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=role_menus,
            message="获取角色菜单列表成功"
        )
    except ResourceNotFound:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取角色 {role_id} 菜单列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取角色菜单列表失败", detail=str(e))

@router.delete("/{role_id}/menus/{menu_id}", response_model=Response)
async def remove_menu_from_role(
    request: Request,
    role_id: int = Path(..., description="角色ID"),
    menu_id: int = Path(..., description="菜单ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    从角色中移除指定菜单
    
    Args:
        request (Request): 请求对象
        role_id (int): 角色ID
        menu_id (int): 菜单ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 移除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 角色或菜单不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:role:edit"):
        logger.warning(f"用户 {current_user.username} 尝试从角色移除菜单，但权限不足")
        raise AuthorizationError(message="权限不足，需要角色编辑权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求从角色 {role_id} 移除菜单 {menu_id}，IP: {client_ip}")
    
    try:
        service = RoleService(db)
        
        service.remove_menu_from_role(role_id, menu_id)
        
        process_time = time.time() - start_time
        logger.info(f"从角色 {role_id} 移除菜单 {menu_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="移除菜单成功"
        )
    except (ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"从角色 {role_id} 移除菜单 {menu_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="移除菜单失败", detail=str(e))

@router.get("/permissions/all", response_model=Response[List[PermissionResponse]])
async def get_all_permissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[PermissionResponse]]:
    """
    获取所有权限列表
    
    Args:
        request (Request): 请求对象
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[PermissionResponse]]: 权限列表响应
        
    Raises:
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取所有权限列表，IP: {client_ip}")
    
    try:
        service = RoleService(db)
        permissions = service.get_all_permissions()
        
        process_time = time.time() - start_time
        logger.info(f"获取所有权限列表成功，共 {len(permissions)} 个权限，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=permissions,
            message="获取权限列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取所有权限列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取权限列表失败", detail=str(e))