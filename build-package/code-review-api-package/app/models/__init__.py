"""
模型包初始化
@author: pgao
@date: 2024-03-13
"""

from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.user_role import UserRole
from app.models.role_permission import RolePermission
from app.models.project import Project
from app.models.project_role import ProjectRole
from app.models.menu import Menu
from app.models.role_menu import RoleMenu
from app.models.code_commit import CodeCommit
from app.models.issue import Issue
from app.models.issue_comment import IssueComment
from app.models.issue_history import IssueHistory
from app.models.notification import Notification
from app.models.analysis_result import AnalysisResult

# 便于外部导入
__all__ = [
    'User', 
    'Role', 
    'Permission',
    'UserRole',
    'RolePermission', 
    'Project', 
    'ProjectRole', 
    'Menu', 
    'RoleMenu',
    'CodeCommit', 
    'Issue', 
    'IssueComment', 
    'IssueHistory',
    'Notification', 
    'AnalysisResult'
]
