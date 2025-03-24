"""
角色模型
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.database import Base

class Role(Base):
    """
    角色模型，定义系统角色
    
    Attributes:
        id (int): 角色ID
        name (str): 角色名称
        description (str): 角色描述
        role_type (str): 角色类型(project/user)
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
    """
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True, index=True, comment="角色ID")
    name = Column(String(50), nullable=False, index=True, comment="角色名称")
    description = Column(Text, nullable=True, comment="角色描述")
    role_type = Column(String(20), nullable=False, default="user", comment="角色类型(user/project)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        {'comment': '角色表'}
    )

    # 关系定义
    # 角色与权限关系
    permissions = relationship("Permission", secondary="role_permissions", back_populates="roles")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    
    # 角色用户关系
    users = relationship("User", secondary="user_roles", back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    # 角色菜单关系
    menus = relationship("Menu", secondary="role_menus", back_populates="roles")
    role_menus = relationship("RoleMenu", back_populates="role", cascade="all, delete-orphan")
    
    # 角色项目关系
    projects = relationship("Project", secondary="project_roles", viewonly=True)
    project_roles = relationship("ProjectRole", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        """返回角色对象的字符串表示"""
        return f"<Role(id={self.id}, name={self.name}, role_type={self.role_type})>"

    def to_dict(self) -> Dict[str, Any]:
        """
        将角色对象转换为字典
        Returns:
            Dict[str, Any]: 角色信息字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "role_type": self.role_type,
            "permissions": [p.code for p in self.permissions] if self.permissions else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
    def get_menus(self):
        """
        获取角色可访问的菜单列表
        
        Returns:
            list: 可访问的菜单列表
        """
        return self.menus
        
    def get_permissions(self) -> List[str]:
        """
        获取角色拥有的权限代码列表
        
        Returns:
            List[str]: 权限代码列表
        """
        return [p.code for p in self.permissions] if self.permissions else []
        
    def has_permission(self, permission_code: str) -> bool:
        """
        检查角色是否拥有特定权限
        
        Args:
            permission_code (str): 权限代码
            
        Returns:
            bool: 是否拥有权限
        """
        return any(p.code == permission_code for p in self.permissions)