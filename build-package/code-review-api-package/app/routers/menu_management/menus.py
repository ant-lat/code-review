"""
菜单管理路由模块
@author: pgao
@date: 2024-03-13
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import traceback

from app.database import get_db
from app.services.menu_service import MenuService
from app.core.security import get_current_user, check_permission
from app.models.user import User
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError
from app.schemas.response import Response
from app.config.logging_config import logger
from pydantic import BaseModel

# 创建路由器
router = APIRouter(
    prefix="/api/v1/menus", 
    tags=["菜单管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

class MenuCreate(BaseModel):
    """菜单创建请求模型"""
    title: str
    path: str
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    order_num: Optional[int] = 0
    permission_id: Optional[int] = None
    is_visible: Optional[bool] = True
    is_cache: Optional[bool] = False
    menu_type: Optional[str] = "menu"

class MenuUpdate(BaseModel):
    """菜单更新请求模型"""
    title: Optional[str] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    order_num: Optional[int] = None
    permission_id: Optional[int] = None
    is_visible: Optional[bool] = None
    is_cache: Optional[bool] = None
    menu_type: Optional[str] = None

class MenuResponse(BaseModel):
    """菜单响应模型"""
    id: int
    title: str
    path: str
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    order_num: int
    permission_id: Optional[int] = None
    permission_code: Optional[str] = None  # 保留用于前端显示
    is_visible: bool
    is_cache: bool
    menu_type: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    children: Optional[List["MenuResponse"]] = None

@router.get("", response_model=Response[Dict[str, Any]])
async def get_menus(
    request: Request,
    parent_id: Optional[int] = Query(None, description="父菜单ID"),
    title: Optional[str] = Query(None, description="菜单标题"),
    menu_type: Optional[str] = Query(None, description="菜单类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取菜单列表
    
    Args:
        request (Request): 请求对象
        parent_id (Optional[int]): 父菜单ID
        title (Optional[str]): 菜单标题
        menu_type (Optional[str]): 菜单类型
        page (int): 页码
        page_size (int): 每页数量
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 菜单列表响应
        
    Raises:
        AuthorizationError: 权限不足
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:menu:list"):
        logger.warning(f"用户 {current_user.username} 尝试获取菜单列表，但权限不足")
        raise AuthorizationError(message="权限不足，需要菜单查看权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取菜单列表，页码: {page}，每页数量: {page_size}，IP: {client_ip}")
    
    try:
        service = MenuService(db)
        
        # 构建过滤条件
        filters = {}
        if parent_id is not None:
            filters["parent_id"] = parent_id
        if title:
            filters["title"] = title
        if menu_type:
            filters["menu_type"] = menu_type
            
        menus, total = service.get_menus(filters, page=page, page_size=page_size)
        
        # 将菜单对象转换为字典
        menu_list = [menu.to_dict() for menu in menus]
        
        process_time = time.time() - start_time
        logger.info(f"获取菜单列表成功，共 {len(menu_list)} 个菜单，处理时间: {process_time:.2f}秒")
        
        return Response(
            data={
                "items": menu_list,
                "total": total,
                "page": page,
                "page_size": page_size
            },
            message="获取菜单列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取菜单列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取菜单列表失败", detail=str(e))

@router.get("/tree", response_model=Response[List[Dict[str, Any]]])
async def get_menu_tree(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取菜单树结构
    
    Args:
        request (Request): 请求对象
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 菜单树响应
        
    Raises:
        AuthorizationError: 权限不足
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:menu:list"):
        logger.warning(f"用户 {current_user.username} 尝试获取菜单树，但权限不足")
        raise AuthorizationError(message="权限不足，需要菜单查看权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求菜单树，IP: {client_ip}")
    
    try:
        service = MenuService(db)
        menu_tree = service.get_menu_tree()
        
        process_time = time.time() - start_time
        logger.info(f"菜单树查询成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=menu_tree,
            message="获取菜单树成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取菜单树失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取菜单树失败", detail=str(e))

@router.get("/user", response_model=Response[List[Dict[str, Any]]])
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

@router.post("", response_model=Response[MenuResponse], status_code=status.HTTP_201_CREATED)
async def create_menu(
    request: Request,
    menu_data: MenuCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[MenuResponse]:
    """
    创建菜单
    
    Args:
        request (Request): 请求对象
        menu_data (MenuCreate): 菜单创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[MenuResponse]: 菜单创建响应
        
    Raises:
        AuthorizationError: 权限不足
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:menu:add"):
        logger.warning(f"用户 {current_user.username} 尝试创建菜单，但权限不足")
        raise AuthorizationError(message="权限不足，需要菜单创建权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求创建菜单 {menu_data.title}，IP: {client_ip}")
    
    try:
        service = MenuService(db)
        
        menu = service.create_menu({
            "title": menu_data.title,
            "path": menu_data.path,
            "icon": menu_data.icon,
            "parent_id": menu_data.parent_id,
            "order_num": menu_data.order_num,
            "permission_id": menu_data.permission_id,
            "is_visible": menu_data.is_visible,
            "is_cache": menu_data.is_cache,
            "menu_type": menu_data.menu_type
        })
        
        # 转换为响应格式
        response_data = MenuResponse(
            id=menu.id,
            title=menu.title,
            path=menu.path,
            icon=menu.icon,
            parent_id=menu.parent_id,
            order_num=menu.order_num,
            permission_id=menu.permission_id,
            permission_code=menu.permission_code,
            is_visible=menu.is_visible if hasattr(menu, 'is_visible') else True,
            is_cache=menu.is_cache if hasattr(menu, 'is_cache') else False,
            menu_type=menu.menu_type if hasattr(menu, 'menu_type') else "menu",
            created_at=menu.created_at.isoformat() if hasattr(menu, 'created_at') and menu.created_at else None,
            updated_at=menu.updated_at.isoformat() if hasattr(menu, 'updated_at') and menu.updated_at else None,
            children=[]
        )
        
        process_time = time.time() - start_time
        logger.info(f"创建菜单成功，ID: {menu.id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="菜单创建成功"
        )
    except BusinessError:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"创建菜单失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="创建菜单失败", detail=str(e))

@router.put("/{menu_id}", response_model=Response[MenuResponse])
async def update_menu(
    request: Request,
    menu_id: int = Path(..., description="菜单ID"),
    menu_data: MenuUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[MenuResponse]:
    """
    更新菜单
    
    Args:
        request (Request): 请求对象
        menu_id (int): 菜单ID
        menu_data (MenuUpdate): 菜单更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[MenuResponse]: 菜单更新响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 菜单不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:menu:edit"):
        logger.warning(f"用户 {current_user.username} 尝试更新菜单，但权限不足")
        raise AuthorizationError(message="权限不足，需要菜单编辑权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求更新菜单 {menu_id}，IP: {client_ip}")
    
    try:
        service = MenuService(db)
        
        updated_menu = service.update_menu(menu_id, {
            "title": menu_data.title,
            "path": menu_data.path,
            "icon": menu_data.icon,
            "parent_id": menu_data.parent_id,
            "order_num": menu_data.order_num,
            "permission_id": menu_data.permission_id,
            "is_visible": menu_data.is_visible,
            "is_cache": menu_data.is_cache,
            "menu_type": menu_data.menu_type
        })
        
        # 转换为响应格式
        response_data = MenuResponse(
            id=updated_menu.id,
            title=updated_menu.title,
            path=updated_menu.path,
            icon=updated_menu.icon,
            parent_id=updated_menu.parent_id,
            order_num=updated_menu.order_num,
            permission_id=updated_menu.permission_id,
            permission_code=updated_menu.permission_code,
            is_visible=updated_menu.is_visible if hasattr(updated_menu, 'is_visible') else True,
            is_cache=updated_menu.is_cache if hasattr(updated_menu, 'is_cache') else False,
            menu_type=updated_menu.menu_type if hasattr(updated_menu, 'menu_type') else "menu",
            created_at=updated_menu.created_at.isoformat() if hasattr(updated_menu, 'created_at') and updated_menu.created_at else None,
            updated_at=updated_menu.updated_at.isoformat() if hasattr(updated_menu, 'updated_at') and updated_menu.updated_at else None,
            children=[]
        )
        
        process_time = time.time() - start_time
        logger.info(f"更新菜单 {menu_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="菜单更新成功"
        )
    except (ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"更新菜单 {menu_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="更新菜单失败", detail=str(e))

@router.delete("/{menu_id}", response_model=Response)
async def delete_menu(
    request: Request,
    menu_id: int = Path(..., description="菜单ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    删除菜单
    
    Args:
        request (Request): 请求对象
        menu_id (int): 菜单ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 删除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 菜单不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    # 检查权限
    if not check_permission(db, current_user.id, "system:menu:delete"):
        logger.warning(f"用户 {current_user.username} 尝试删除菜单，但权限不足")
        raise AuthorizationError(message="权限不足，需要菜单删除权限")
    
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求删除菜单 {menu_id}，IP: {client_ip}")
    
    try:
        service = MenuService(db)
        
        service.delete_menu(menu_id)
        
        process_time = time.time() - start_time
        logger.info(f"删除菜单 {menu_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="菜单删除成功"
        )
    except (ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"删除菜单 {menu_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="删除菜单失败", detail=str(e))