"""
角色权限关联模型
@author: pgao
@date: 2024-03-16
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class RolePermission(Base):
    """
    角色权限关联模型，实现角色与权限的多对多关系
    
    Attributes:
        role_id (int): 角色ID
        permission_id (int): 权限ID
        assigned_at (datetime): 分配时间
    """
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID")
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID")
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="分配时间")
    
    __table_args__ = (
        PrimaryKeyConstraint("role_id", "permission_id"),
        {'comment': '角色权限关联表'}
    )
    
    # 关系定义
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission")
    
    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
    
    def to_dict(self):
        """
        将角色权限关联对象转换为字典
        
        Returns:
            dict: 角色权限关联信息字典
        """
        return {
            'role_id': self.role_id,
            'permission_id': self.permission_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'role_name': self.role.name if self.role else None,
            'permission_code': self.permission.code if self.permission else None
        } 