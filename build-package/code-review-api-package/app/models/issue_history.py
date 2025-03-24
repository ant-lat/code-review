from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class IssueHistory(Base):
    """问题修改历史模型"""
    __tablename__ = "issue_history"

    id = Column(Integer, primary_key=True, index=True, comment="历史记录ID")
    issue_id = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, comment="关联问题")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="操作用户")
    field_name = Column(String(50), nullable=False, comment="变更字段")
    old_value = Column(Text, nullable=True, comment="旧值")
    new_value = Column(Text, nullable=True, comment="新值")
    changed_at = Column(DateTime, default=datetime.utcnow, comment="变更时间")

    # 关系定义
    issue = relationship("Issue", back_populates="history")
    user = relationship("User", back_populates="issue_histories")
    
    def __repr__(self):
        """返回历史记录对象的字符串表示"""
        return f"<IssueHistory(id={self.id}, issue_id={self.issue_id}, field='{self.field_name}')>"
        
    def to_dict(self):
        """
        将历史记录对象转换为字典
        
        Returns:
            dict: 历史记录信息字典
        """
        return {
            'id': self.id,
            'issue_id': self.issue_id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else None,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None
        }