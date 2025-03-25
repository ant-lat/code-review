"""
权限服务模块
@author: 
@date: 2024-03-17
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Dict, Any, Optional
from fastapi import Depends
import logging

from app.database import get_db
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.project import Project
from app.models.project_role import ProjectRole
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.core.exceptions import ResourceNotFound, DatabaseError
from app.config.logging_config import logger
from app.services.base_service import BaseService

class PermissionService(BaseService):
    """
    权限服务类，处理权限相关的业务逻辑
    集中管理用户权限和项目权限的检查逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化权限服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def check_user_permission(self, user_id: int, permission_code: str) -> bool:
        """
        检查用户是否具有特定权限（通过角色获得）
        
        Args:
            user_id (int): 用户ID
            permission_code (str): 权限代码
            
        Returns:
            bool: 是否有权限
        """
        def _query():
            # 查询用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"用户ID {user_id} 不存在")
                return False
            
            # 使用用户模型的has_permission方法检查权限
            if user.has_permission(permission_code):
                logger.debug(f"用户 {user_id} 拥有权限 {permission_code}")
                return True
            
            logger.debug(f"用户 {user_id} 没有权限 {permission_code}")
            return False
        
        return self._safe_query(_query, f"检查用户 {user_id} 权限 {permission_code} 失败", False)
    
    def check_user_role(self, user_id: int, role_id: int) -> bool:
        """
        检查用户是否具有指定角色
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            bool: 用户是否具有指定角色
        """
        try:
            # 检查用户是否有指定角色
            user_role = self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active == True
            ).first()
            
            return user_role is not None
        except Exception as e:
            logger.error(f"检查用户角色失败: 用户ID={user_id}, 角色ID={role_id}, 错误: {str(e)}")
            return False
    
    def check_project_member(self, user_id: int, project_id: int) -> bool:
        """
        检查用户是否是项目成员
        
        Args:
            user_id (int): 用户ID
            project_id (int): 项目ID
            
        Returns:
            bool: 是否是项目成员
        """
        def _query():
            # 查询项目成员关系
            project_role = self.db.query(ProjectRole).filter(
                and_(
                    ProjectRole.project_id == project_id,
                    ProjectRole.user_id == user_id,
                    ProjectRole.is_active == True
                )
            ).first()
            
            return project_role is not None
        
        return self._safe_query(_query, f"检查用户 {user_id} 是否是项目 {project_id} 成员失败", False)
    
    def check_project_admin(self, user_id: int, project_id: int) -> bool:
        """
        检查用户是否是项目管理员
        
        Args:
            user_id (int): 用户ID
            project_id (int): 项目ID
            
        Returns:
            bool: 是否是项目管理员
        """
        def _query():
            # 查询项目管理员角色
            admin_role = self.db.query(Role).filter(
                and_(
                    Role.role_type == "project",
                    or_(Role.code == "project_admin", Role.name == "PM")
                )
            ).first()
            
            if not admin_role:
                logger.warning("未找到项目管理员角色")
                return False
            
            # 查询用户是否拥有项目管理员角色
            project_role = self.db.query(ProjectRole).filter(
                and_(
                    ProjectRole.project_id == project_id,
                    ProjectRole.user_id == user_id,
                    ProjectRole.role_id == admin_role.id,
                    ProjectRole.is_active == True
                )
            ).first()
            
            return project_role is not None
        
        return self._safe_query(_query, f"检查用户 {user_id} 是否是项目 {project_id} 管理员失败", False)
    
    def check_project_access(self, user_id: int, project_id: int, required_role_id: Optional[int] = None) -> bool:
        """
        检查用户是否有权限访问项目
        
        Args:
            user_id (int): 用户ID
            project_id (int): 项目ID
            required_role_id (Optional[int]): 所需的角色ID
            
        Returns:
            bool: 是否有访问权限
        """
        def _query():
            # 查询用户是否有全局项目访问权限
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False
            
            # 检查是否有全局查看所有项目的权限
            if user.has_permission("project:view_all"):
                return True
            
            # 构建查询条件
            query_conditions = [
                ProjectRole.project_id == project_id,
                ProjectRole.user_id == user_id,
                ProjectRole.is_active == True
            ]
            
            if required_role_id is not None:
                query_conditions.append(ProjectRole.role_id == required_role_id)
            
            # 检查用户是否是项目成员
            project_role = self.db.query(ProjectRole).filter(and_(*query_conditions)).first()
            
            return project_role is not None
        
        return self._safe_query(_query, f"检查项目访问权限失败: 项目 {project_id}, 用户 {user_id}", False)
    
    def get_user_permissions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户所有权限
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[Dict[str, Any]]: 权限列表
        """
        def _query():
            # 查询用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"用户ID {user_id} 不存在")
                return []
            
            permissions = []
            # 获取用户所有角色
            user_roles = self.db.query(Role).join(
                UserRole, UserRole.role_id == Role.id
            ).filter(
                and_(
                    UserRole.user_id == user_id,
                    UserRole.is_active == True
                )
            ).all()
            
            # 从所有角色中获取权限
            for role in user_roles:
                for perm in role.permissions:
                    # 去重添加
                    existing = next((p for p in permissions if p["code"] == perm.code), None)
                    if not existing:
                        permissions.append({
                            "id": perm.id,
                            "code": perm.code,
                            "name": perm.name,
                            "description": perm.description,
                            "role": role.name
                        })
            
            logger.debug(f"用户 {user_id} 共有 {len(permissions)} 个权限")
            return permissions
        
        return self._safe_query(_query, f"获取用户 {user_id} 权限列表失败", [])
    
    def get_user_project_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户在所有项目中的角色
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[Dict[str, Any]]: 用户项目角色列表
        """
        def _query():
            # 查询用户的项目角色
            project_roles = self.db.query(
                Project.id.label("project_id"),
                Project.name.label("project_name"),
                Role.id.label("role_id"),
                Role.name.label("role_name"),
                ProjectRole.joined_at
            ).join(
                ProjectRole, ProjectRole.project_id == Project.id
            ).join(
                Role, ProjectRole.role_id == Role.id
            ).filter(
                and_(
                    ProjectRole.user_id == user_id,
                    ProjectRole.is_active == True,
                    Project.is_active == True
                )
            ).all()
            
            result = []
            for pr in project_roles:
                result.append({
                    "project_id": pr.project_id,
                    "project_name": pr.project_name,
                    "role_id": pr.role_id,
                    "role_name": pr.role_name,
                    "joined_at": pr.joined_at.isoformat() if pr.joined_at else None
                })
            
            return result
        
        return self._safe_query(_query, f"获取用户 {user_id} 项目角色列表失败", []) 