"""
通知管理路由模块
@author: pgao
@date: 2024-03-13
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Union
import time
import traceback
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.notification_service import NotificationService, NotificationType
from app.core.security import get_current_user
from app.models.user import User
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError
from app.schemas.response import Response, PageResponse, PageInfo
from app.config.logging_config import logger

# 创建路由器
router = APIRouter(
    prefix="/api/v1/notifications", 
    tags=["通知管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

class NotificationUpdateRequest(BaseModel):
    """通知更新请求模型"""
    notification_ids: List[int] = Field(..., description="通知ID列表")

class NotificationDeleteRequest(BaseModel):
    """通知删除请求模型"""
    notification_ids: List[int] = Field(..., description="通知ID列表")

class NotificationResponse(BaseModel):
    """通知响应模型"""
    id: int = Field(..., description="通知ID")
    message: str = Field(..., description="通知内容")
    type: str = Field(default="system", description="通知类型")
    is_read: bool = Field(..., description="是否已读")
    created_at: Optional[str] = Field(None, description="创建时间")
    read_at: Optional[str] = Field(None, description="阅读时间")
    issue_id: Optional[int] = Field(None, description="关联问题ID")
    issue_title: Optional[str] = Field(None, description="关联问题标题")
    issue_status: Optional[str] = Field(None, description="关联问题状态")

@router.get("", response_model=PageResponse[NotificationResponse])
async def get_user_notifications(
    request: Request,
    unread_only: bool = Query(False, description="是否只获取未读通知"),
    notification_type: Optional[str] = Query(None, description="通知类型过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    from_date: Optional[date] = Query(None, description="开始日期过滤"),
    to_date: Optional[date] = Query(None, description="结束日期过滤"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PageResponse[NotificationResponse]:
    """
    获取当前用户的通知列表
    
    Args:
        request (Request): 请求对象
        unread_only (bool): 是否只获取未读通知
        notification_type (str): 按通知类型过滤
        search (str): 搜索关键词
        from_date (date): 开始日期过滤
        to_date (date): 结束日期过滤
        page (int): 页码
        page_size (int): 每页数量
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        PageResponse[NotificationResponse]: 通知列表分页响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取通知列表，只看未读: {unread_only}，类型: {notification_type}，IP: {client_ip}")
    
    try:
        service = NotificationService(db)
        
        # 处理日期过滤条件
        from_datetime = datetime.combine(from_date, datetime.min.time()) if from_date else None
        to_datetime = datetime.combine(to_date, datetime.max.time()) if to_date else None
        
        # 计算分页参数
        skip = (page - 1) * page_size
        
        # 获取通知列表和总数
        notifications, total = service.get_user_notifications(
            user_id=current_user.id, 
            unread_only=unread_only,
            notification_type=notification_type,
            search_text=search,
            from_date=from_datetime,
            to_date=to_datetime,
            skip=skip,
            limit=page_size
        )
        
        # 格式化响应
        notification_items = []
        for notification in notifications:
            notification_items.append(NotificationResponse(
                id=notification["id"],
                message=notification["message"],
                type=notification["type"],
                is_read=notification["is_read"],
                created_at=notification["created_at"],
                read_at=notification.get("read_at"),
                issue_id=notification["issue_id"],
                issue_title=notification["issue_title"],
                issue_status=notification["issue_status"]
            ))
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {current_user.id} 通知列表成功，共 {len(notification_items)} 条通知，总量 {total}，处理时间: {process_time:.2f}秒")
        
        # 使用分页响应
        return PageResponse.create(
            items=notification_items,
            total=total,
            page=page,
            page_size=page_size,
            message="获取通知列表成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取用户 {current_user.id} 通知列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取通知列表失败", detail=str(e))

@router.put("/mark-read", response_model=Response)
async def mark_notifications_read(
    request: Request,
    update_data: NotificationUpdateRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    将多条通知标记为已读
    
    Args:
        request (Request): 请求对象
        update_data (NotificationUpdateRequest): 通知更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 更新响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 通知不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    ids_str = ", ".join(map(str, update_data.notification_ids[:5])) + (
        f"...等共{len(update_data.notification_ids)}条" if len(update_data.notification_ids) > 5 else ""
    )
    logger.info(f"用户 {current_user.username} 请求标记通知为已读，通知ID: {ids_str}，IP: {client_ip}")
    
    try:
        service = NotificationService(db)
        
        # 如果通知ID列表为空，则标记所有通知为已读
        if not update_data.notification_ids:
            count = service.mark_all_as_read(current_user.id)
            
            process_time = time.time() - start_time
            logger.info(f"用户 {current_user.id} 标记所有通知为已读成功，共 {count} 条通知，处理时间: {process_time:.2f}秒")
            
            return Response(
                message=f"已将所有通知标记为已读，共 {count} 条通知"
            )
        
        # 批量标记多个通知为已读
        success_count, fail_count = service.mark_multiple_as_read(
            update_data.notification_ids, 
            current_user.id
        )
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.id} 标记通知为已读完成，成功: {success_count}，失败: {fail_count}，处理时间: {process_time:.2f}秒")
        
        return Response(
            message=f"通知标记为已读：成功 {success_count} 条，失败 {fail_count} 条"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"标记通知为已读失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="标记通知为已读失败", detail=str(e))

@router.put("/read/all", response_model=Response)
async def mark_all_notifications_read(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    将当前用户的所有通知标记为已读
    
    Args:
        request (Request): 请求对象
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 操作结果响应
        
    Raises:
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求标记所有通知为已读，IP: {client_ip}")
    
    try:
        service = NotificationService(db)
        count = service.mark_all_as_read(current_user.id)
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.id} 标记所有通知为已读成功，共 {count} 条通知，处理时间: {process_time:.2f}秒")
        
        return Response(
            message=f"成功将所有通知标记为已读，共 {count} 条"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"标记所有通知为已读失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="标记所有通知为已读失败", detail=str(e))

@router.delete("/{notification_id}", response_model=Response)
async def delete_notification(
    request: Request,
    notification_id: int = Path(..., ge=1, description="通知ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    删除单个通知
    
    Args:
        request (Request): 请求对象
        notification_id (int): 通知ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 删除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 通知不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求删除通知 {notification_id}，IP: {client_ip}")
    
    try:
        service = NotificationService(db)
        
        success = service.delete_notification(notification_id, current_user.id)
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.id} 删除通知 {notification_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="删除通知成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"删除通知 {notification_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="删除通知失败", detail=str(e))

@router.delete("", response_model=Response)
async def delete_multiple_notifications(
    request: Request,
    delete_data: NotificationDeleteRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    批量删除通知
    
    Args:
        request (Request): 请求对象
        delete_data (NotificationDeleteRequest): 通知删除数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 删除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 通知不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    ids_str = ", ".join(map(str, delete_data.notification_ids[:5])) + (
        f"...等共{len(delete_data.notification_ids)}条" if len(delete_data.notification_ids) > 5 else ""
    )
    logger.info(f"用户 {current_user.username} 请求批量删除通知，通知ID: {ids_str}，IP: {client_ip}")
    
    try:
        service = NotificationService(db)
        
        # 批量删除通知
        success_count, fail_count = service.delete_multiple_notifications(
            delete_data.notification_ids, 
            current_user.id
        )
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.id} 批量删除通知完成，成功: {success_count}，失败: {fail_count}，处理时间: {process_time:.2f}秒")
        
        return Response(
            message=f"通知删除：成功 {success_count} 条，失败 {fail_count} 条"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"批量删除通知失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="批量删除通知失败", detail=str(e))

@router.get("/unread-count", response_model=Response)
async def get_unread_notification_count(
    request: Request,
    notification_type: Optional[str] = Query(None, description="按通知类型过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    获取当前用户未读通知数量
    
    Args:
        request (Request): 请求对象
        notification_type (str): 按通知类型过滤
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 未读通知数量响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
        """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    type_info = f"类型: {notification_type}" if notification_type else "所有类型"
    logger.info(f"用户 {current_user.username} 请求获取{type_info}未读通知数量，IP: {client_ip}")
    
    try:
        service = NotificationService(db)
        
        count = service.get_unread_count(current_user.id, notification_type)
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {current_user.id} 未读通知数量成功: {count}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data={"count": count},
            message="获取未读通知数量成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取未读通知数量失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取未读通知数量失败", detail=str(e))

@router.get("/types", response_model=Response)
async def get_notification_types(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    获取通知类型列表
    
    Args:
        request (Request): 请求对象
        current_user (User): 当前用户
        
    Returns:
        Response: 通知类型列表响应
    """
    type_list = []
    for notification_type in NotificationType:
        type_list.append({
            "value": notification_type.value,
            "label": notification_type.name,
            "description": get_notification_type_description(notification_type)
        })
    
    return Response(
        data=type_list,
        message="获取通知类型成功"
    )

def get_notification_type_description(notification_type: NotificationType) -> str:
    """获取通知类型的中文描述"""
    descriptions = {
        NotificationType.ISSUE_CREATED: "问题创建",
        NotificationType.ISSUE_ASSIGNED: "问题分配",
        NotificationType.ISSUE_UPDATED: "问题更新",
        NotificationType.ISSUE_CLOSED: "问题关闭",
        NotificationType.ISSUE_REOPENED: "问题重新打开",
        NotificationType.COMMENT_ADDED: "新增评论",
        NotificationType.MENTIONED: "提到我",
        NotificationType.SYSTEM: "系统通知",
        NotificationType.TASK_DEADLINE: "任务截止时间提醒"
    }
    return descriptions.get(notification_type, "未知类型")