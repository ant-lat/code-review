"""
用户模型模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class User(Base):
    """
    用户模型，存储用户信息和权限
    
    Attributes:
        id (int): 用户ID（系统内部）
        user_id (str): 用户登录ID
        username (str): 用户真实姓名
        email (str): 用户邮箱
        phone (str): 用户手机号码
        password_hash (str): 密码哈希值
        is_active (bool): 用户状态
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    user_id = Column(String(50), unique=True, nullable=False, comment="用户登录ID")
    username = Column(String(50), nullable=False, comment="用户真实姓名")
    email = Column(String(100), unique=True, nullable=True, comment="用户邮箱")
    phone = Column(String(20), unique=True, nullable=True, comment="用户手机号码")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        {'comment': '用户表'}
    )

    # 关系定义
    # 用户角色关系
    roles = relationship("Role", secondary="user_roles", back_populates="users")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    
    # 用户项目关系
    projects = relationship("Project", foreign_keys="[Project.created_by]", back_populates="creator")
    joined_projects = relationship("Project", secondary="project_roles", back_populates="members",
                        primaryjoin="and_(User.id==ProjectRole.user_id, ProjectRole.is_active==True)")
    
    # 项目角色关系
    project_roles = relationship("ProjectRole", back_populates="user", cascade="all, delete-orphan")
    
    # 其他关系
    code_commits = relationship("CodeCommit", back_populates="author")
    created_issues = relationship("Issue", foreign_keys="[Issue.creator_id]", back_populates="creator")
    assigned_issues = relationship("Issue", foreign_keys="[Issue.assignee_id]", back_populates="assignee")
    issue_comments = relationship("IssueComment", back_populates="user")
    issue_histories = relationship("IssueHistory", back_populates="user")
    notifications = relationship("Notification", back_populates="recipient", cascade="all, delete-orphan")

    def __repr__(self):
        """返回用户对象的字符串表示"""
        return f"<User(id={self.id}, user_id='{self.user_id}', username='{self.username}')>"

    def to_dict(self):
        """
        将用户对象转换为字典
        Returns:
            dict: 用户信息字典
        """
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'roles': [role.name for role in self.roles] if self.roles else []
        }
        
    def get_available_menus(self):
        """
        获取用户可访问的菜单列表，基于用户的角色
        
        Returns:
            list: 可访问的菜单列表
        """
        menu_set = set()
        for role in self.roles:
            for menu in role.get_menus():
                menu_set.add(menu)
        return list(menu_set)
    
    def has_permission(self, permission_code):
        """
        检查用户是否拥有特定权限
        
        Args:
            permission_code (str): 权限代码
            
        Returns:
            bool: 是否拥有权限
        """
        for role in self.roles:
            if role.has_permission(permission_code):
                return True
        return False