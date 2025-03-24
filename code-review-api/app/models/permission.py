"""
权限模型模块
@author: pgao
@date: 2024-03-16
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Permission(Base):
    """
    权限模型，定义系统权限
    
    Attributes:
        id (int): 权限ID
        code (str): 权限代码
        name (str): 权限名称
        description (str): 权限描述
        module (str): 所属模块
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
    """
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True, comment="权限ID")
    code = Column(String(50), unique=True, nullable=False, comment="权限代码")
    name = Column(String(100), nullable=False, comment="权限名称")
    description = Column(Text, comment="权限描述")
    module = Column(String(50), nullable=False, comment="所属模块")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系定义
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")
    menus = relationship("Menu", back_populates="permission")
    
    def __repr__(self):
        """返回权限对象的字符串表示"""
        return f"<Permission(id={self.id}, code='{self.code}', module='{self.module}')>"
    
    def to_dict(self):
        """
        将权限对象转换为字典
        
        Returns:
            dict: 权限信息字典
        """
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'module': self.module,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 