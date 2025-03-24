"""
项目模型模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class Project(Base):
    """
    项目模型，管理项目及其对应的代码仓库
    
    Attributes:
        id (int): 项目ID
        name (str): 项目名称
        description (str): 项目描述
        repository_url (str): 代码仓库地址
        repository_type (str): 仓库类型(git/svn)
        branch (str): 默认分支
        is_active (bool): 项目状态
        created_by (int): 创建人ID
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, comment="项目ID")
    name = Column(String(255), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    repository_url = Column(String(500), nullable=False, comment="代码仓库地址")
    repository_type = Column(String(10), default='git', comment="仓库类型")
    branch = Column(String(100), default='main', comment="默认分支")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), comment="创建人")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    __table_args__ = (
        {'comment': '项目表'}
    )

    # 关系定义
    # 创建者关系
    creator = relationship("User", back_populates="projects", foreign_keys=[created_by])
    
    # 项目用户关系 - 通过项目角色关联
    members = relationship("User", secondary="project_roles", back_populates="joined_projects",
                         secondaryjoin="and_(User.id==ProjectRole.user_id, ProjectRole.is_active==True)")
    
    # 项目角色关系
    project_roles = relationship("ProjectRole", back_populates="project", cascade="all, delete-orphan")
    
    # 代码相关关系
    code_commits = relationship("CodeCommit", back_populates="project", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="project", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        """返回项目对象的字符串表示"""
        return f"<Project(id={self.id}, name='{self.name}')>"

    def to_dict(self):
        """
        将项目对象转换为字典
        Returns:
            dict: 项目信息字典
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'repository_url': self.repository_url,
            'repository_type': self.repository_type,
            'branch': self.branch,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_stats(self):
        """
        获取项目统计信息
        Returns:
            dict: 项目统计信息
        """
        open_issues = sum(1 for issue in self.issues if issue.status == 'open')
        total_issues = len(self.issues)
        return {
            'open_issues': open_issues,
            'total_issues': total_issues,
            'total_commits': len(self.code_commits),
            'member_count': len(self.members)
        }
        
    def get_members(self):
        """
        获取项目成员列表
        Returns:
            list: 项目成员列表
        """
        return [member.to_dict() for member in self.members]
        
    def get_roles(self):
        """
        获取项目中的角色列表
        Returns:
            list: 项目角色列表
        """
        return [pr.to_dict() for pr in self.project_roles]