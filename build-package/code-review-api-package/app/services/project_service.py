"""
项目服务模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, literal_column
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from app.models import RolePermission
from app.models.project import Project
from app.models.user import User
from app.models.role import Role
from app.models.project_role import ProjectRole
from app.models.permission import Permission
from app.config.logging_config import logger
from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError, AuthorizationError
from app.services.base_service import BaseService
from app.models.analysis_result import AnalysisResult
from sqlalchemy.sql import func

class ProjectService(BaseService[Project]):
    """
    项目服务类，处理项目相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化项目服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def create_project(self, data: Dict[str, Any]) -> Project:
        """
        创建项目
        
        Args:
            data (Dict[str, Any]): 项目数据
                - name (str): 项目名称
                - description (str): 项目描述
                - creator_id (int): 创建者ID
                - repository_url (Optional[str]): 代码仓库地址
                - repository_type (Optional[str]): 仓库类型(git/svn)
                - branch (Optional[str]): 默认分支
                - status (Optional[str]): 项目状态(active/archived/deleted)
                
        Returns:
            Project: 创建的项目对象
            
        Raises:
            ResourceNotFound: 创建者不存在
            BusinessError: 项目名称已存在或参数无效
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证创建者是否存在
            creator = self.db.query(User).filter(User.id == data["creator_id"]).first()
            if not creator:
                raise ResourceNotFound(message=f"用户ID {data['creator_id']} 不存在")
            
            # 验证项目名称是否已存在
            existing_project = self.db.query(Project).filter(Project.name == data["name"]).first()
            if existing_project:
                raise BusinessError(message=f"项目名称 '{data['name']}' 已存在")
            
            # 验证仓库类型
            repository_type = data.get("repository_type", "git")
            if repository_type not in ["git", "svn"]:
                raise BusinessError(message="仓库类型必须是 'git' 或 'svn'")
            
            # 验证项目状态
            status = data.get("status", "active")
            if status not in ["active", "archived", "deleted"]:
                raise BusinessError(message="项目状态必须是 'active'、'archived' 或 'deleted'")
            
            # 验证仓库URL格式（如果提供）
            repository_url = data.get("repository_url", "")
            if repository_url:
                if repository_type == "git":
                    if not self._validate_git_url(repository_url):
                        raise BusinessError(message="Git仓库地址格式无效")
                else:  # svn
                    if not self._validate_svn_url(repository_url):
                        raise BusinessError(message="SVN仓库地址格式无效")
            
            now = datetime.utcnow()
            # 创建项目
            new_project = Project(
                name=data["name"],
                description=data.get("description", ""),
                repository_url=repository_url,
                repository_type=repository_type,
                branch=data.get("branch", "main"),
                status=status,
                created_by=data["creator_id"],
                created_at=now,
                updated_at=now
            )
            
            self.db.add(new_project)
            self.db.commit()
            self.db.refresh(new_project)
            
            # 查找管理员角色
            admin_role = self.db.query(Role).filter(and_(
                Role.name == "PM", 
                Role.role_type == "project"
            )).first()
            
            if not admin_role:
                admin_role = self.db.query(Role).filter(
                    Role.role_type == "project"
                ).first()
            
            if admin_role:
                # 将创建者添加为项目管理员
                project_role = ProjectRole(
                    project_id=new_project.id,
                    user_id=data["creator_id"],
                    role_id=admin_role.id,
                    joined_at=now,
                    is_active=True
                )
                
                self.db.add(project_role)
                self.db.commit()
            
            logger.info(f"项目创建成功: '{data['name']}' (ID: {new_project.id})")
            return new_project
        
        return self._safe_query(_query, f"创建项目失败: {data.get('name')}")
    
    def _validate_git_url(self, url: str) -> bool:
        """
        验证Git仓库地址格式
        
        Args:
            url (str): 仓库地址
            
        Returns:
            bool: 是否有效
        """
        # 支持HTTP(S)和SSH格式
        patterns = [
            r'^https?://[^\s/$.?#].[^\s]*$',  # HTTP(S)
            r'^git@[^\s:]+:[^\s/]+/[^\s/]+\.git$'  # SSH
        ]
        return any(bool(re.match(pattern, url)) for pattern in patterns)
    
    def _validate_svn_url(self, url: str) -> bool:
        """
        验证SVN仓库地址格式
        
        Args:
            url (str): 仓库地址
            
        Returns:
            bool: 是否有效
        """
        # 支持HTTP(S)和SVN协议
        patterns = [
            r'^https?://[^\s/$.?#].[^\s]*$',  # HTTP(S)
            r'^svn://[^\s/$.?#].[^\s]*$'  # SVN
        ]
        return any(bool(re.match(pattern, url)) for pattern in patterns)
    
    def get_project_by_id(self, project_id: int) -> Project:
        """
        根据ID获取项目
        
        Args:
            project_id (int): 项目ID
            
        Returns:
            Project: 项目对象
            
        Raises:
            ResourceNotFound: 项目不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"ID为{project_id}的项目不存在")
            return project
        
        return self._safe_query(_query, f"获取项目 {project_id} 失败")
    
    def get_projects(self, filters: Dict[str, Any], page: int = 1, page_size: int = 20) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取项目列表
        
        Args:
            filters (Dict[str, Any]): 过滤条件
                - name (Optional[str]): 项目名称（模糊匹配）
                - status (Optional[str]): 项目状态(active/archived/deleted)
                - repository_type (Optional[str]): 仓库类型(git/svn)
                - creator_id (Optional[int]): 创建者ID
                - member_id (Optional[int]): 成员ID
                - role_id (Optional[int]): 角色ID
                - created_after (Optional[datetime]): 创建时间起始
                - created_before (Optional[datetime]): 创建时间截止
            page (int): 页码（从1开始）
            page_size (int): 每页数量
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 项目列表和总数
            
        Raises:
            BusinessError: 参数无效
            DatabaseError: 数据库操作错误
        """
        def _query():
            query = self.db.query(Project)
            
            # 名称模糊查询
            if "name" in filters:
                query = query.filter(Project.name.ilike(f"%{filters['name']}%"))
            
            # 状态过滤
            if "status" in filters:
                if filters["status"] not in ["active", "archived", "deleted"]:
                    raise BusinessError(message="项目状态必须是 'active'、'archived' 或 'deleted'")
                query = query.filter(Project.status == filters["status"])
            
            # 仓库类型过滤
            if "repository_type" in filters:
                if filters["repository_type"] not in ["git", "svn"]:
                    raise BusinessError(message="仓库类型必须是 'git' 或 'svn'")
                query = query.filter(Project.repository_type == filters["repository_type"])
            
            # 创建者过滤
            if "creator_id" in filters:
                query = query.filter(Project.created_by == filters["creator_id"])
            
            # 成员过滤
            if "member_id" in filters:
                query = query.join(ProjectRole).filter(ProjectRole.user_id == filters["member_id"])
            
            # 角色过滤
            if "role_id" in filters:
                query = query.join(ProjectRole).filter(ProjectRole.role_id == filters["role_id"])
            
            # 创建时间范围过滤
            if "created_after" in filters:
                query = query.filter(Project.created_at >= filters["created_after"])
            if "created_before" in filters:
                query = query.filter(Project.created_at <= filters["created_before"])
            
            # 计算总数
            total = query.count()
            
            # 分页
            query = query.order_by(Project.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 获取项目列表
            projects = query.all()
            
            # 格式化返回结果
            result = []
            for project in projects:
                # 获取项目成员数量
                member_count = self.db.query(ProjectRole).filter(
                    ProjectRole.project_id == project.id,
                    ProjectRole.is_active == True
                ).count()
                
                # 获取项目创建者信息
                creator = self.db.query(User).filter(User.id == project.created_by).first()
                
                # 获取最近一次代码分析结果
                latest_analysis = self.db.query(AnalysisResult).filter(
                    AnalysisResult.project_id == project.id
                ).order_by(AnalysisResult.created_at.desc()).first()
                
                project_dict = {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "repository_url": project.repository_url,
                    "repository_type": project.repository_type,
                    "branch": project.branch,
                    "is_active": project.is_active,
                    "member_count": member_count,
                    "creator": {
                        "id": creator.id if creator else None,
                        "username": creator.username if creator else None,
                        "email": creator.email if creator else None
                    } if creator else None,
                    "latest_analysis": {
                        "id": latest_analysis.id,
                        "score": latest_analysis.result_summary,
                        "created_at": latest_analysis.created_at.isoformat()
                    } if latest_analysis else None,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat()
                }
                result.append(project_dict)
            
            return result, total
        
        return self._safe_query(_query, "获取项目列表失败")
    
    def update_project(self, project_id: int, data: Dict[str, Any]) -> Project:
        """
        更新项目信息
        
        Args:
            project_id (int): 项目ID
            data (Dict[str, Any]): 更新数据
                - name (Optional[str]): 项目名称
                - description (Optional[str]): 项目描述
                - repository_url (Optional[str]): 代码仓库地址
                - repository_type (Optional[str]): 仓库类型(git/svn)
                - branch (Optional[str]): 默认分支
                - status (Optional[str]): 项目状态(active/archived/deleted)
                
        Returns:
            Project: 更新后的项目对象
            
        Raises:
            ResourceNotFound: 项目不存在
            BusinessError: 参数无效
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 查找项目
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 验证项目名称是否已存在（如果要更新）
            if "name" in data and data["name"] != project.name:
                existing_project = self.db.query(Project).filter(
                    and_(Project.name == data["name"], Project.id != project_id)
                ).first()
                if existing_project:
                    raise BusinessError(message=f"项目名称 '{data['name']}' 已存在")
                project.name = data["name"]
            
            # 更新描述
            if "description" in data:
                project.description = data["description"]
            
            # 更新仓库信息
            if "repository_type" in data:
                if data["repository_type"] not in ["git", "svn"]:
                    raise BusinessError(message="仓库类型必须是 'git' 或 'svn'")
                project.repository_type = data["repository_type"]
            
            if "repository_url" in data:
                repository_url = data["repository_url"]
                if repository_url:
                    if project.repository_type == "git":
                        if not self._validate_git_url(repository_url):
                            raise BusinessError(message="Git仓库地址格式无效")
                    else:  # svn
                        if not self._validate_svn_url(repository_url):
                            raise BusinessError(message="SVN仓库地址格式无效")
                project.repository_url = repository_url
            
            # 更新分支
            if "branch" in data:
                project.branch = data["branch"]
            
            # 更新状态
            if "status" in data:
                if data["status"] not in ["active", "archived", "deleted"]:
                    raise BusinessError(message="项目状态必须是 'active'、'archived' 或 'deleted'")
                project.status = data["status"]
            
            project.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(project)
            
            logger.info(f"项目更新成功: '{project.name}' (ID: {project.id})")
            return project
        
        return self._safe_query(_query, f"更新项目失败: ID {project_id}")
    
    def delete_project(self, project_id: int) -> bool:
        """
        删除项目
        
        Args:
            project_id (int): 项目ID
            
        Returns:
            bool: 是否成功
            
        Raises:
            ResourceNotFound: 项目不存在
            DatabaseError: 数据库操作错误
        """
        try:
            # 获取项目
            project = self.db.query(Project).filter(Project.id == project_id).first()
            
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 删除项目成员
            self.db.query(ProjectRole).filter(ProjectRole.project_id == project_id).delete()
            
            # 删除项目
            self.db.delete(project)
            self.db.commit()
            
            return True
        except ResourceNotFound:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"删除项目失败: {str(e)}")
            raise DatabaseError(message="删除项目失败", detail=str(e))
    
    def add_project_member(self, project_id: int, user_id: int, role_id: int) -> Dict[str, Any]:
        """
        向项目添加成员

        Args:
            project_id (int): 项目ID
            user_id (int): 用户ID
            role_id (int): 角色ID

        Returns:
            Dict[str, Any]: 新增成员信息

        Raises:
            ResourceNotFound: 项目、用户或角色不存在
            BusinessError: 用户已经是项目成员
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")

            # 检查用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")

            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")

            # 检查角色是否为项目角色
            if role.role_type != "project":
                raise BusinessError(message=f"角色ID {role_id} 不是项目角色")

            # 检查用户是否已经是项目成员
            existing_role = self.db.query(ProjectRole).filter(
                    ProjectRole.project_id == project_id,
                    ProjectRole.user_id == user_id,
                    ProjectRole.role_id == role_id,
            ProjectRole.is_active == True
            ).first()

            if existing_role:
                raise BusinessError(message=f"用户ID {user_id} 已经是项目ID {project_id} 的成员")

        # 添加项目成员
            new_role = ProjectRole(
                project_id=project_id,
                user_id=user_id,
                role_id=role_id,
                is_active=True,
                joined_at=datetime.utcnow()
            )

            self.db.add(new_role)
            self.db.commit()

            # 确保 user 和 role 对象存在
            if not user or not role or not new_role:
                raise DatabaseError(message="数据库操作失败，用户或角色信息获取失败")

            # 返回新增成员信息
            return {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "role_id": role.id,
                "role_name": role.name,
                "joined_at": new_role.joined_at.isoformat()
            }

        return self._safe_query(_query, f"向项目 {project_id} 添加成员 {user_id} 失败")

    def remove_project_member(self, project_id: int, user_id: int, role_id: Optional[int] = None) -> bool:
        """
        移除项目成员
        
        Args:
            project_id (int): 项目ID
            user_id (int): 用户ID
            role_id (Optional[int]): 角色ID，如果提供则只移除指定角色
            
        Returns:
            bool: 移除是否成功
            
        Raises:
            ResourceNotFound: 项目、用户或关系不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 构建查询条件
            query_conditions = [
                ProjectRole.project_id == project_id,
                ProjectRole.user_id == user_id
            ]
            
            if role_id is not None:
                query_conditions.append(ProjectRole.role_id == role_id)
            
            # 查找项目成员关系
            project_roles = self.db.query(ProjectRole).filter(and_(*query_conditions)).all()
            
            if not project_roles:
                raise ResourceNotFound(message=f"用户 {user_id} 不是项目 {project_id} 的成员")
            
            for project_role in project_roles:
                # 设置为非活动状态
                project_role.is_active = False
                project_role.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"已将用户 {user_id} 从项目 {project_id} 中移除")
            return True
        
        return self._safe_query(_query, f"移除项目成员失败: 项目 {project_id}, 用户 {user_id}", False)
    
    def get_project_members(self, project_id: int) -> List[Dict[str, Any]]:
        """
        获取项目成员列表
        
        Args:
            project_id (int): 项目ID
            
        Returns:
            List[Dict[str, Any]]: 项目成员列表
            
        Raises:
            ResourceNotFound: 项目不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 查询项目成员
            query = (self.db.query(
                User.id.label("user_id"),
                User.username,
                User.email,
                User.is_active,
                Role.id.label("role_id"),
                Role.name.label("role_name"),
                ProjectRole.joined_at
            ).join(
                ProjectRole, ProjectRole.user_id == User.id
            ).join(
                Role, ProjectRole.role_id == Role.id
            ).filter(
                    ProjectRole.project_id == project_id,
                ProjectRole.is_active == True,
                Role.role_type == "project"
            ))
            
            # 获取项目成员列表
            members = query.all()
            
            # 格式化返回结果
            result = []
            for member in members:
                result.append({
                    "user_id": member.user_id,
                    "username": member.username,
                    "email": member.email,
                    "is_active": member.is_active,
                    "role_id": member.role_id,
                    "role_name": member.role_name,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None
                })
            
            return result
        
        return self._safe_query(_query, f"获取项目 {project_id} 成员列表失败")
    
    def check_project_access(self, project_id: int, user_id: int, required_role_id: Optional[int] = None) -> bool:
        """
        检查用户是否有权限访问项目
        
        Args:
            project_id (int): 项目ID
            user_id (int): 用户ID
            required_role_id (Optional[int]): 所需的角色ID
            
        Returns:
            bool: 是否有访问权限
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
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
    
    def check_project_member(self, user_id: int, project_id: int) -> bool:
        """
        检查用户是否是项目成员
        
        Args:
            user_id (int): 用户ID
            project_id (int): 项目ID
            
        Returns:
            bool: 是否是项目成员
        """
        try:
            project_role = self.db.query(ProjectRole).filter(
                ProjectRole.project_id == project_id,
                ProjectRole.user_id == user_id,
                ProjectRole.is_active == True
            ).first()
            return project_role is not None
        except Exception as e:
            logger.error(f"检查用户 {user_id} 是否是项目 {project_id} 成员失败: {str(e)}")
            return False
            
    def check_project_admin(self, user_id: int, project_id: int) -> bool:
        """
        检查用户是否是项目管理员
        
        Args:
            user_id (int): 用户ID
            project_id (int): 项目ID
            
        Returns:
            bool: 是否是项目管理员
        """
        try:
            # 获取管理员角色
            admin_role = self.db.query(Role).filter(
                Role.code == "project_admin", 
                Role.role_type == "project"
            ).first()
            
            if not admin_role:
                return False
                
            # 检查用户是否有管理员角色
            project_role = self.db.query(ProjectRole).filter(
                ProjectRole.project_id == project_id,
                ProjectRole.user_id == user_id,
                ProjectRole.role_id == admin_role.id,
                ProjectRole.is_active == True
            ).first()
            
            return project_role is not None
        except Exception as e:
            logger.error(f"检查用户 {user_id} 是否是项目 {project_id} 管理员失败: {str(e)}")
            return False
    
    def assign_project_role(self, project_id: int, user_id: int, role_id: int) -> Dict[str, Any]:
        """
        为项目成员分配角色
        
        Args:
            project_id (int): 项目ID
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            Dict[str, Any]: 角色分配结果
            
        Raises:
            ResourceNotFound: 项目、用户或角色不存在
            BusinessError: 用户已有此角色
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 检查用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 检查是否为项目角色
            if role.role_type != "project":
                raise BusinessError(message=f"角色ID {role_id} 不是项目角色")
            
            # 检查用户是否已有此角色
            existing_role = self.db.query(ProjectRole).filter(
                ProjectRole.project_id == project_id,
                ProjectRole.user_id == user_id,
                ProjectRole.role_id == role_id
            ).first()
            
            # 如果已有此角色但未激活，则重新激活
            if existing_role:
                if not existing_role.is_active:
                    existing_role.is_active = True
                    existing_role.updated_at = datetime.utcnow()
                    self.db.commit()
                    return {
                        "user_id": user.id,
                        "username": user.username,
                        "role_id": role.id,
                        "role_name": role.name,
                        "project_id": project.id,
                        "project_name": project.name,
                        "is_active": existing_role.is_active,
                        "joined_at": existing_role.joined_at.isoformat() if existing_role.joined_at else None,
                        "updated_at": existing_role.updated_at.isoformat()
                    }
                else:
                    raise BusinessError(message=f"用户 {user.username} 已拥有项目 '{project.name}' 的角色 '{role.name}'")

            # 添加新角色
            new_role = ProjectRole(
                project_id=project_id,
                user_id=user_id,
                role_id=role_id,
                is_active=True,
                joined_at=datetime.utcnow()
            )
            
            self.db.add(new_role)
            self.db.commit()
            
            return {
                "user_id": user.id,
                "username": user.username,
                "role_id": role.id,
                "role_name": role.name,
                "project_id": project.id,
                "project_name": project.name,
                "is_active": new_role.is_active,
                "joined_at": new_role.joined_at.isoformat()
            }
        
        return self._safe_query(_query, f"为项目 {project_id} 用户 {user_id} 分配角色 {role_id} 失败")
    
    def remove_project_role(self, project_id: int, user_id: int, role_id: int) -> Dict[str, Any]:
        """
        移除项目成员的角色
        
        Args:
            project_id (int): 项目ID
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            Dict[str, Any]: 移除结果
            
        Raises:
            ResourceNotFound: 项目、用户或角色不存在
            BusinessError: 用户没有此角色或是最后一个角色
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 检查用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 检查用户是否有此角色
            project_role = self.db.query(ProjectRole).filter(
                ProjectRole.project_id == project_id,
                ProjectRole.user_id == user_id,
                ProjectRole.role_id == role_id,
                ProjectRole.is_active == True
            ).first()
            
            if not project_role:
                raise BusinessError(message=f"用户 {user.username} 没有项目 '{project.name}' 的角色 '{role.name}'")
            
            # 检查是否是用户在该项目中的最后一个角色
            other_roles = self.db.query(ProjectRole).filter(
                ProjectRole.project_id == project_id,
                ProjectRole.user_id == user_id,
                ProjectRole.role_id != role_id,
                ProjectRole.is_active == True
            ).count()
                
            if other_roles == 0:
                raise BusinessError(message=f"不能移除用户 {user.username} 在项目 '{project.name}' 中的最后一个角色")
                
            # 移除角色（设置为非活跃状态）
            project_role.is_active = False
            project_role.updated_at = datetime.utcnow()
            self.db.commit()
                
            return {
                "user_id": user.id,
                "username": user.username,
                "role_id": role.id,
                "role_name": role.name,
                "project_id": project.id,
                "project_name": project.name,
                "is_active": project_role.is_active,
                "updated_at": project_role.updated_at.isoformat()
            }
        
        return self._safe_query(_query, f"移除项目 {project_id} 用户 {user_id} 的角色 {role_id} 失败")
    
    def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """
        获取项目统计信息
        
        Args:
            project_id (int): 项目ID
            
        Returns:
            Dict[str, Any]: 项目统计信息
            
        Raises:
            ResourceNotFound: 项目不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 获取项目成员数
            member_count = self.db.query(ProjectRole).filter(
                ProjectRole.project_id == project_id,
                ProjectRole.is_active == True
            ).count()
            
            # 获取项目最新的分析结果
            latest_analysis = self.db.query(AnalysisResult).filter(
                AnalysisResult.project_id == project_id
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            # 构建统计信息
            stats = {
                "project_id": project.id,
                "name": project.name,
                "member_count": member_count,
                "created_at": project.created_at.isoformat(),
                "days_active": (datetime.utcnow() - project.created_at).days,
                "latest_analysis": None
            }
            
            # 添加分析结果
            if latest_analysis:
                stats["latest_analysis"] = {
                    "id": latest_analysis.id,
                    "analysis_type": latest_analysis.analysis_type,
                    "result_summary": latest_analysis.result_summary,
                    "code_quality_score": latest_analysis.code_quality_score,
                    "complexity_score": latest_analysis.complexity_score,
                    "maintainability_score": latest_analysis.maintainability_score,
                    "security_score": latest_analysis.security_score,
                    "created_at": latest_analysis.created_at.isoformat()
                }
            
            return stats
        
        return self._safe_query(_query, f"获取项目 {project_id} 统计信息失败")
    
    def get_member_count(self, project_id: int) -> int:
        """
        获取项目成员数量
        
        Args:
            project_id (int): 项目ID
            
        Returns:
            int: 项目成员数量
        """
        def _query():
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(resource_type="项目", resource_id=project_id)
            
            # 获取成员数量
            count = self.db.query(func.count(ProjectRole.id)).filter(
                and_(
                    ProjectRole.project_id == project_id,
                    ProjectRole.is_active == True
                )
            ).scalar()
            
            return count or 0
        
        return self._safe_query(_query, f"获取项目 {project_id} 成员数量失败", 0)
    
    def get_project_activities(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        获取项目活动列表
        
        Args:
            filters (Dict[str, Any]): 过滤条件
                - project_id (int): 项目ID
                - start_date (Optional[datetime]): 开始日期
                - end_date (Optional[datetime]): 结束日期
            page (int): 页码
            page_size (int): 每页数量
            
        Returns:
            Dict[str, Any]: 分页的项目活动列表
                - total (int): 总数
                - page (int): 当前页码
                - page_size (int): 每页数量
                - items (List[Dict[str, Any]]): 活动列表
        """
        def _query():
            # 获取过滤条件
            project_id = filters.get("project_id")
            start_date = filters.get("start_date")
            end_date = filters.get("end_date")
            
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(resource_type="项目", resource_id=project_id)
            
            # 活动查询 - 这里我们查询多种活动类型
            # 1. 代码提交
            # 2. 问题创建和更新
            # 3. 代码分析
            
            from app.models.code_commit import CodeCommit
            from app.models.issue import Issue
            from app.models.analysis_result import AnalysisResult
            
            # 合并所有活动类型查询
            activities = []
            
            # 1. 代码提交
            commit_query = self.db.query(
                CodeCommit.id,
                CodeCommit.commit_id,
                CodeCommit.commit_message,
                CodeCommit.author_id,
                CodeCommit.commit_time.label("activity_time"),
                User.username,
                literal_column("'commit'").label("activity_type")
            ).join(
                User, CodeCommit.author_id == User.id, isouter=True
            ).filter(
                CodeCommit.project_id == project_id
            )
            
            if start_date:
                commit_query = commit_query.filter(CodeCommit.commit_time >= start_date)
            if end_date:
                commit_query = commit_query.filter(CodeCommit.commit_time <= end_date)
            
            # 2. 问题创建
            issue_query = self.db.query(
                Issue.id,
                literal_column("''").label("commit_id"),
                Issue.title.label("commit_message"),
                User.username.label("author_id"),
                Issue.created_at.label("activity_time"),
                User.username,
                literal_column("'issue'").label("activity_type")
            ).join(
                User, Issue.creator_id == User.id, isouter=True
            ).filter(
                Issue.project_id == project_id
            )
            
            if start_date:
                issue_query = issue_query.filter(Issue.created_at >= start_date)
            if end_date:
                issue_query = issue_query.filter(Issue.created_at <= end_date)
            
            # 3. 代码分析
            analysis_query = self.db.query(
                AnalysisResult.id,
                literal_column("''").label("commit_id"),
                literal_column("'代码分析'").label("commit_message"),
                User.username.label("author_id"),
                AnalysisResult.created_at.label("activity_time"),
                User.username,
                literal_column("'analysis'").label("activity_type")
            ).join(
                User, AnalysisResult.commit_id == User.id, isouter=True
            ).filter(
                AnalysisResult.project_id == project_id
            )
            
            if start_date:
                analysis_query = analysis_query.filter(AnalysisResult.created_at >= start_date)
            if end_date:
                analysis_query = analysis_query.filter(AnalysisResult.created_at <= end_date)
            
            # 合并所有查询
            from sqlalchemy.sql import union_all
            combined_query = union_all(commit_query, issue_query, analysis_query).alias("combined")
            
            # 计算总数
            from sqlalchemy import select, func
            count_query = select(func.count()).select_from(combined_query)
            total = self.db.execute(count_query).scalar() or 0
            
            # 分页查询
            offset = (page - 1) * page_size
            
            # 获取活动列表
            activities_query = select(combined_query).order_by(
                combined_query.c.activity_time.desc()
            ).offset(offset).limit(page_size)
            
            activities_result = self.db.execute(activities_query).fetchall()
            
            # 格式化活动列表
            activities = []
            for row in activities_result:
                activities.append({
                    "id": row.id,
                    "activity_type": row.activity_type,
                    "activity_time": row.activity_time.isoformat() if row.activity_time else None,
                    "username": row.username,
                    "author_id": row.author_id,
                    "commit_id": row.commit_id if row.activity_type == "commit" else None,
                    "message": row.commit_message
                })
                
                return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "items": activities
            }
        
        return self._safe_query(_query, f"获取项目活动列表失败", {"total": 0, "page": page, "page_size": page_size, "items": []}) 