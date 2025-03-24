"""
通知服务模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum

from app.models.notification import Notification
from app.models.issue import Issue
from app.models.user import User
from app.database import get_db
from app.config.logging_config import logger
from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError
from app.services.base_service import BaseService

class NotificationType(str, Enum):
    """通知类型枚举"""
    ISSUE_CREATED = "issue_created"         # 问题创建
    ISSUE_ASSIGNED = "issue_assigned"       # 问题已分配
    ISSUE_UPDATED = "issue_updated"         # 问题更新
    ISSUE_CLOSED = "issue_closed"           # 问题关闭
    ISSUE_REOPENED = "issue_reopened"       # 问题重新打开
    COMMENT_ADDED = "comment_added"         # 添加评论
    MENTIONED = "mentioned"                 # 提及用户
    SYSTEM = "system"                       # 系统通知
    TASK_DEADLINE = "task_deadline"         # 任务截止时间提醒

class NotificationService(BaseService[Notification]):
    """
    通知服务类，处理用户通知相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化通知服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def create_notification(self, 
                           recipient_id: int, 
                           message: str, 
                           issue_id: Optional[int] = None,
                           notification_type: Union[NotificationType, str] = NotificationType.SYSTEM) -> Notification:
        """
        创建通知
        
        Args:
            recipient_id (int): 接收者ID
            message (str): 通知消息
            issue_id (Optional[int]): 问题ID，可选
            notification_type (Union[NotificationType, str]): 通知类型
            
        Returns:
            Notification: 创建的通知对象
            
        Raises:
            ResourceNotFound: 接收者或问题不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证接收者存在
            recipient = self.db.query(User).filter(User.id == recipient_id).first()
            if not recipient:
                raise ResourceNotFound(resource_type="用户", resource_id=recipient_id, message=f"用户ID {recipient_id} 不存在")
            
            # 如果提供了问题ID，验证问题存在
            if issue_id:
                issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
                if not issue:
                    raise ResourceNotFound(resource_type="问题", resource_id=issue_id, message=f"问题ID {issue_id} 不存在")
            
            # 将字符串类型的通知类型转换为枚举
            if isinstance(notification_type, str):
                try:
                    notification_type_enum = NotificationType(notification_type)
                except ValueError:
                    notification_type_enum = NotificationType.SYSTEM
            else:
                notification_type_enum = notification_type
            
            # 创建通知
            now = datetime.utcnow()
            new_notification = Notification(
                recipient_id=recipient_id,
                issue_id=issue_id,
                type=notification_type_enum.value,
                message=message,
                is_read=False,
                created_at=now
            )
            
            self.db.add(new_notification)
            self.db.commit()
            self.db.refresh(new_notification)
            
            logger.info(f"为用户 {recipient_id} 创建{notification_type_enum.value}类型通知: {message}")
            return new_notification
        
        return self._safe_query(_query, f"创建通知失败: 接收者 {recipient_id}, 问题 {issue_id if issue_id else 'N/A'}")
    
    def create_bulk_notifications(self, 
                                recipient_ids: List[int], 
                                message: str, 
                                issue_id: Optional[int] = None,
                                notification_type: Union[NotificationType, str] = NotificationType.SYSTEM) -> int:
        """
        批量创建通知
        
        Args:
            recipient_ids (List[int]): 接收者ID列表
            message (str): 通知消息
            issue_id (Optional[int]): 问题ID，可选
            notification_type (Union[NotificationType, str]): 通知类型
            
        Returns:
            int: 成功创建的通知数量
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查接收者是否存在
            existing_users = self.db.query(User.id).filter(User.id.in_(recipient_ids)).all()
            existing_user_ids = [user.id for user in existing_users]
            
            # 过滤掉不存在的用户
            valid_recipient_ids = [uid for uid in recipient_ids if uid in existing_user_ids]
            
            # 如果提供了问题ID，验证问题存在
            if issue_id:
                issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
                if not issue:
                    raise ResourceNotFound(resource_type="问题", resource_id=issue_id, message=f"问题ID {issue_id} 不存在")
            
            # 将字符串类型的通知类型转换为枚举
            if isinstance(notification_type, str):
                try:
                    notification_type_enum = NotificationType(notification_type)
                except ValueError:
                    notification_type_enum = NotificationType.SYSTEM
            else:
                notification_type_enum = notification_type
            
            # 批量创建通知对象
            now = datetime.utcnow()
            notifications = []
            for rid in valid_recipient_ids:
                notifications.append(Notification(
                    recipient_id=rid,
                    issue_id=issue_id,
                    type=notification_type_enum.value,
                    message=message,
                    is_read=False,
                    created_at=now
                ))
            
            if notifications:
                self.db.bulk_save_objects(notifications)
                self.db.commit()
            
            logger.info(f"批量创建{notification_type_enum.value}类型通知，接收者数量: {len(valid_recipient_ids)}")
            return len(valid_recipient_ids)
        
        return self._safe_query(_query, f"批量创建通知失败: 接收者数量 {len(recipient_ids)}", 0)
    
    def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        """
        将通知标记为已读
        
        Args:
            notification_id (int): 通知ID
            user_id (int): 用户ID，用于验证权限
            
        Returns:
            Notification: 更新后的通知对象
            
        Raises:
            ResourceNotFound: 通知不存在
            BusinessError: 用户无权限
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 获取通知
            notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                raise ResourceNotFound(resource_type="通知", resource_id=notification_id, message=f"通知ID {notification_id} 不存在")
            
            # 验证用户权限
            if notification.recipient_id != user_id:
                raise BusinessError(message="无权操作此通知")
            
            # 如果已经是已读状态，直接返回
            if notification.is_read:
                return notification
            
            # 更新通知
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(notification)
            
            logger.info(f"通知 {notification_id} 已被用户 {user_id} 标记为已读")
            return notification
        
        return self._safe_query(_query, f"将通知标记为已读失败: 通知ID {notification_id}")
    
    def mark_multiple_as_read(self, notification_ids: List[int], user_id: int) -> Tuple[int, int]:
        """
        将多个通知标记为已读
        
        Args:
            notification_ids (List[int]): 通知ID列表
            user_id (int): 用户ID，用于验证权限
            
        Returns:
            Tuple[int, int]: (成功标记数量, 失败标记数量)
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 查询属于此用户且未读的通知
            notifications = self.db.query(Notification).filter(
                Notification.id.in_(notification_ids),
                Notification.recipient_id == user_id,
                Notification.is_read == False
            ).all()
            
            # 批量更新通知
            now = datetime.utcnow()
            for notification in notifications:
                notification.is_read = True
                notification.read_at = now
            
            # 提交更改
            try:
                self.db.commit()
                logger.info(f"用户 {user_id} 将 {len(notifications)} 条通知标记为已读")
                # 计算成功和失败数量
                success_count = len(notifications)
                fail_count = len(notification_ids) - success_count
                return success_count, fail_count
            except Exception as e:
                self.db.rollback()
                logger.error(f"批量标记通知为已读失败: {str(e)}")
                raise DatabaseError(message="批量标记通知为已读失败")
        
        return self._safe_query(_query, f"批量标记通知为已读失败: 通知数量 {len(notification_ids)}", (0, len(notification_ids)))
    
    def mark_all_as_read(self, user_id: int, notification_type: Optional[str] = None) -> int:
        """
        将用户所有未读通知标记为已读
        
        Args:
            user_id (int): 用户ID
            notification_type (Optional[str]): 可选指定通知类型
            
        Returns:
            int: 标记为已读的通知数量
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 构建查询条件
            query = self.db.query(Notification).filter(
                Notification.recipient_id == user_id,
                Notification.is_read == False
            )
            
            # 如果指定了通知类型，添加过滤条件
            if notification_type:
                query = query.filter(Notification.type == notification_type)
            
            # 获取所有未读通知
            notifications = query.all()
            
            # 如果没有未读通知，直接返回
            if not notifications:
                return 0
            
            # 批量更新为已读
            now = datetime.utcnow()
            for notification in notifications:
                notification.is_read = True
                notification.read_at = now
            
            # 提交更改
            try:
                self.db.commit()
                read_count = len(notifications)
                type_info = f"类型为{notification_type}的" if notification_type else "所有"
                logger.info(f"用户 {user_id} 将{type_info}未读通知({read_count}条)标记为已读")
                return read_count
            except Exception as e:
                self.db.rollback()
                logger.error(f"标记所有通知为已读失败: {str(e)}")
                raise DatabaseError(message="标记所有通知为已读失败")
        
        return self._safe_query(_query, f"标记所有通知为已读失败: 用户 {user_id}", 0)

    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """
        删除通知
        
        Args:
            notification_id (int): 通知ID
            user_id (int): 用户ID，用于验证权限
            
        Returns:
            bool: 是否成功删除
            
        Raises:
            ResourceNotFound: 通知不存在
            BusinessError: 用户无权限
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 获取通知
            notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                raise ResourceNotFound(resource_type="通知", resource_id=notification_id, message=f"通知ID {notification_id} 不存在")
            
            # 验证用户权限
            if notification.recipient_id != user_id:
                raise BusinessError(message="无权操作此通知")
            
            # 删除通知
            self.db.delete(notification)
            self.db.commit()
            
            logger.info(f"通知 {notification_id} 已被用户 {user_id} 删除")
            return True
        
        return self._safe_query(_query, f"删除通知失败: 通知ID {notification_id}", False)
    
    def delete_multiple_notifications(self, notification_ids: List[int], user_id: int) -> Tuple[int, int]:
        """
        批量删除通知
        
        Args:
            notification_ids (List[int]): 通知ID列表
            user_id (int): 用户ID，用于验证权限
            
        Returns:
            Tuple[int, int]: (成功删除数量, 失败删除数量)
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 查询属于此用户的通知
            notifications = self.db.query(Notification).filter(
                Notification.id.in_(notification_ids),
                Notification.recipient_id == user_id
            ).all()
            
            # 批量删除通知
            for notification in notifications:
                self.db.delete(notification)
            
            # 提交更改
            try:
                self.db.commit()
                logger.info(f"用户 {user_id} 删除了 {len(notifications)} 条通知")
                # 计算成功和失败数量
                success_count = len(notifications)
                fail_count = len(notification_ids) - success_count
                return success_count, fail_count
            except Exception as e:
                self.db.rollback()
                logger.error(f"批量删除通知失败: {str(e)}")
                raise DatabaseError(message="批量删除通知失败")
        
        return self._safe_query(_query, f"批量删除通知失败: 通知数量 {len(notification_ids)}", (0, len(notification_ids)))
    
    def get_user_notifications(
        self, 
        user_id: int, 
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        search_text: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None, 
        skip: int = 0, 
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取用户通知列表
        
        Args:
            user_id (int): 用户ID
            unread_only (bool): 是否只返回未读通知
            notification_type (Optional[str]): 按通知类型过滤
            search_text (Optional[str]): 搜索关键词
            from_date (Optional[datetime]): 开始日期过滤
            to_date (Optional[datetime]): 结束日期过滤
            skip (int): 分页偏移量
            limit (int): 分页大小
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: (通知列表, 总记录数)
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            try:
                # 构建基础查询
                base_query = self.db.query(Notification).filter(Notification.recipient_id == user_id)
                count_query = self.db.query(func.count(Notification.id)).filter(Notification.recipient_id == user_id)
                
                # 应用各种过滤条件
                if unread_only:
                    base_query = base_query.filter(Notification.is_read == False)
                    count_query = count_query.filter(Notification.is_read == False)
                
                if notification_type:
                    base_query = base_query.filter(Notification.type == notification_type)
                    count_query = count_query.filter(Notification.type == notification_type)
                
                if search_text:
                    search_pattern = f"%{search_text}%"
                    base_query = base_query.filter(or_(
                        Notification.message.ilike(search_pattern),
                        Notification.type.ilike(search_pattern)
                    ))
                    count_query = count_query.filter(or_(
                        Notification.message.ilike(search_pattern),
                        Notification.type.ilike(search_pattern)
                    ))
                
                if from_date:
                    base_query = base_query.filter(Notification.created_at >= from_date)
                    count_query = count_query.filter(Notification.created_at >= from_date)
                
                if to_date:
                    base_query = base_query.filter(Notification.created_at <= to_date)
                    count_query = count_query.filter(Notification.created_at <= to_date)
                
                # 获取总数
                total_count = count_query.scalar()
                
                # 添加排序和分页
                notifications = base_query.order_by(desc(Notification.created_at)).offset(skip).limit(limit).all()
                
                # 转换为字典列表
                result = []
                for notification in notifications:
                    # 获取关联的问题信息（如果有）
                    issue_info = {}
                    if notification.issue_id:
                        issue = self.db.query(Issue).filter(Issue.id == notification.issue_id).first()
                        if issue:
                            issue_info = {
                                "issue_id": issue.id,
                                "issue_title": issue.title,
                                "issue_status": issue.status
                            }
                    
                    # 构建通知字典
                    notification_dict = {
                        "id": notification.id,
                        "message": notification.message,
                        "type": notification.type,
                        "is_read": notification.is_read,
                        "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M:%S") if notification.created_at else None,
                        "read_at": notification.read_at.strftime("%Y-%m-%d %H:%M:%S") if notification.read_at else None,
                        **issue_info
                    }
                    result.append(notification_dict)
                
                return result, total_count
            except Exception as e:
                logger.error(f"获取用户通知列表失败: {str(e)}")
                raise DatabaseError(message="获取用户通知列表失败")
        
        return self._safe_query(_query, f"获取用户通知列表失败: 用户 {user_id}", ([], 0))
    
    def get_unread_count(self, user_id: int, notification_type: Optional[str] = None) -> int:
        """
        获取用户未读通知数量
        
        Args:
            user_id (int): 用户ID
            notification_type (Optional[str]): 可选指定通知类型
            
        Returns:
            int: 未读通知数量
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            try:
                # 构建查询
                query = self.db.query(func.count(Notification.id)).filter(
                    Notification.recipient_id == user_id,
                    Notification.is_read == False
                )
                
                # 如果指定了通知类型，添加过滤条件
                if notification_type:
                    query = query.filter(Notification.type == notification_type)
                
                # 执行查询并返回结果
                count = query.scalar() or 0
                return count
            except Exception as e:
                logger.error(f"获取未读通知数量失败: {str(e)}")
                raise DatabaseError(message="获取未读通知数量失败")
        
        return self._safe_query(_query, f"获取未读通知数量失败: 用户 {user_id}", 0)