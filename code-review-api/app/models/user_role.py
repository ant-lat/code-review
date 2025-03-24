"""
用户角色关联模型
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class UserRole(Base):
    """
    用户角色关联模型，实现用户与角色的多对多关系
    
    Attributes:
        id (int): 主键ID
        user_id (int): 用户ID
        role_id (int): 角色ID
        created_at (datetime): 创建时间
        expires_at (datetime): 过期时间
        is_active (bool): 是否激活
    """
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True, comment="关联ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'role_id', name='user_role_unique'),
        {'comment': '用户角色关联表'}
    )
    
    # 关系
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
    
    def to_dict(self):
        """
        将用户角色关联对象转换为字典
        Returns:
            dict: 用户角色关联信息字典
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'user_name': self.user.username if self.user else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active
        } 