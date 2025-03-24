"""
系统通知模型模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Notification(Base):
    """
    系统通知模型
    
    Attributes:
        id (int): 通知ID
        recipient_id (int): 接收用户ID
        issue_id (int): 关联问题ID
        type (str): 通知类型
        message (str): 通知内容
        is_read (bool): 是否已读
        read_at (datetime): 阅读时间
        created_at (datetime): 创建时间
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, comment="通知ID")
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="接收用户")
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), comment="关联问题")
    type = Column(String(50), nullable=False, comment="通知类型")
    message = Column(Text, nullable=False, comment="通知内容")
    is_read = Column(Boolean, default=False, comment="是否已读")
    read_at = Column(DateTime, comment="阅读时间")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")

    __table_args__ = (
        {'comment': '系统通知表'}
    )

    # 关系定义
    recipient = relationship("User", back_populates="notifications")
    issue = relationship("Issue")

    def __repr__(self):
        """返回通知对象的字符串表示"""
        return f"<Notification(id={self.id}, type='{self.type}', is_read={self.is_read})>"

    def to_dict(self):
        """
        将通知对象转换为字典
        Returns:
            dict: 通知信息字典
        """
        return {
            'id': self.id,
            'recipient_id': self.recipient_id,
            'issue_id': self.issue_id,
            'type': self.type,
            'message': self.message,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat(),
            'issue': {
                'id': self.issue.id,
                'title': self.issue.title
            } if self.issue else None
        }

    def mark_as_read(self):
        """标记通知为已读"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()