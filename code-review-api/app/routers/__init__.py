from .base import base_router
from .auth.auth import router as auth_router
from .dashboard import dashboard_router
from .user_management.users import router as users_router
from .project_management.projects import router as projects_router
from .role_management.roles import router as roles_router
from .code_analysis.code_analysis import router as code_analysis_router
from .code_analysis.code_review import router as code_review_router
from .issue_tracking.issues import router as issues_router
from .notification.notifications import router as notification_router
from .menu_management.menus import router as menus_router
from .menu_permissions.user_menu_access import router as user_menu_access_router

__all__ = [
    "base_router",
    "auth_router",
    "users_router",
    "projects_router",
    "roles_router",
    "code_analysis_router",
    "code_review_router",
    "issues_router",
    "dashboard_router",
    "notification_router",
    "menus_router",
    "user_menu_access_router",
]