"""
服务层模块初始化
@author: pgao
@date: 2024-03-13
"""

# 导出所有服务，方便导入
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.project_service import ProjectService
from app.services.role_service import RoleService
from app.services.analysis_service import CodeAnalysisService as AnalysisService
from app.services.notification_service import NotificationService
from app.services.review_service import ReviewService
from app.services.menu_service import MenuService
# 导入仪表盘服务
from app.services.dashboard import DashboardService
# 导入子目录服务
from app.services.issue_service import IssueService 
from app.services.permission_service import PermissionService