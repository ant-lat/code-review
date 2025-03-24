"""
项目角色关联模型
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class ProjectRole(Base):
    """项目用户角色关联模型，定义用户在特定项目中的角色"""
    __tablename__ = "project_roles"

    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, comment="关联项目")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="关联用户")
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="关联角色")
    joined_at = Column(DateTime, default=datetime.utcnow, comment="加入时间")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', 'role_id', name='project_user_role_unique'),
        {'comment': '项目角色关联表'}
    )

    # 关系定义
    project = relationship("Project", back_populates="project_roles")
    user = relationship("User", back_populates="project_roles")
    role = relationship("Role", back_populates="project_roles")
    
    def __repr__(self):
        """返回项目角色对象的字符串表示"""
        return f"<ProjectRole(project_id={self.project_id}, user_id={self.user_id}, role_id={self.role_id})>"
    
    def to_dict(self):
        """
        将项目角色对象转换为字典
        Returns:
            dict: 项目角色信息字典
        """
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'role_name': self.role.name if self.role else None,
            'user_name': self.user.username if self.user else None,
            'project_name': self.project.name if self.project else None,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'is_active': self.is_active,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }