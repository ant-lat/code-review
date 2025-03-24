"""
角色菜单关联模型
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class RoleMenu(Base):
    """
    角色菜单关联模型，实现角色与菜单的多对多关系
    
    Attributes:
        role_id (int): 角色ID
        menu_id (int): 菜单ID
        assigned_at (datetime): 分配时间
    """
    __tablename__ = "role_menus"
    
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID")
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False, comment="菜单ID")
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="分配时间")
    
    __table_args__ = (
        PrimaryKeyConstraint("role_id", "menu_id"),
        {'comment': '角色菜单关联表'}
    )
    
    # 关系定义
    role = relationship("Role", back_populates="role_menus")
    menu = relationship("Menu", back_populates="role_menus")
    
    def __repr__(self):
        return f"<RoleMenu(role_id={self.role_id}, menu_id={self.menu_id})>"
    
    def to_dict(self):
        """
        将角色菜单关联对象转换为字典
        
        Returns:
            dict: 角色菜单关联信息字典
        """
        return {
            'role_id': self.role_id,
            'menu_id': self.menu_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'role_name': self.role.name if self.role else None,
            'menu_title': self.menu.title if self.menu else None
        } 