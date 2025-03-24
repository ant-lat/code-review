"""
菜单模型模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Menu(Base):
    """系统菜单模型"""
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True, comment="菜单ID")
    title = Column(String(255), nullable=False, comment="菜单标题")
    path = Column(String(255), comment="路由路径")
    icon = Column(String(255), comment="菜单图标")
    parent_id = Column(Integer, ForeignKey("menus.id", ondelete="SET NULL"), comment="父菜单ID")
    order_num = Column(Integer, default=0, comment="排序号")
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="SET NULL"), comment="关联权限ID")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系定义
    # 与角色的多对多关系
    roles = relationship(
        "Role",
        secondary="role_menus",
        back_populates="menus"
    )
    
    # 与权限的关系
    permission = relationship("Permission", back_populates="menus")
    
    # 子菜单关系
    children = relationship("Menu", back_populates="parent", remote_side=[parent_id])
    parent = relationship("Menu", back_populates="children", remote_side=[id])
    
    # 与菜单角色关联的关系
    role_menus = relationship("RoleMenu", back_populates="menu", cascade="all, delete-orphan")
    
    def __repr__(self):
        """返回菜单对象的字符串表示"""
        return f"<Menu(id={self.id}, title='{self.title}')>"
    
    def to_dict(self, include_children=True):
        """
        将菜单对象转换为字典
        
        Args:
            include_children (bool): 是否包含子菜单
            
        Returns:
            dict: 菜单信息字典
        """
        result = {
            'id': self.id,
            'title': self.title,
            'path': self.path,
            'icon': self.icon,
            'parent_id': self.parent_id,
            'order_num': self.order_num,
            'permission_id': self.permission_id,
            'permission_code': self.permission.code if self.permission else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_children and hasattr(self, 'children') and self.children:
            result['children'] = [child.to_dict() for child in self.children]
            
        return result