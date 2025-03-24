"""
问题评论模型模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class IssueComment(Base):
    """
    问题评论模型 - 合并了一般问题评论和代码检视评论功能
    
    Attributes:
        id (int): 评论ID
        issue_id (int): 关联问题ID
        user_id (int): 评论用户ID
        content (str): 评论内容
        file_path (str): 相关文件路径
        line_number (int): 相关行号
        is_resolution (bool): 是否为解决方案
        parent_id (int): 父评论ID，用于嵌套回复
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
    """
    __tablename__ = "issue_comments"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="评论ID")
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, comment="关联问题ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="评论用户ID")
    content = Column(Text, nullable=False, comment="评论内容")
    file_path = Column(String(255), nullable=True, comment="相关文件路径")
    line_number = Column(Integer, nullable=True, comment="相关行号")
    is_resolution = Column(Boolean, default=False, comment="是否为解决方案")
    parent_id = Column(Integer, ForeignKey("issue_comments.id", ondelete="SET NULL"), nullable=True, comment="父评论ID，用于嵌套回复")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    issue = relationship("Issue", back_populates="comments")
    user = relationship("User", back_populates="issue_comments")
    replies = relationship("IssueComment", backref="parent", remote_side=[id])
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            dict: 字典表示
        """
        return {
            "id": self.id,
            "issue_id": self.issue_id,
            "user_id": self.user_id,
            "user_name": self.user.username if self.user else None,
            "content": self.content,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "is_resolution": self.is_resolution,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 字符串表示
        """
        return f"<IssueComment(id={self.id}, issue_id={self.issue_id})>" 