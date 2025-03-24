"""
问题服务模块
此模块处理问题的业务逻辑，包括问题的增删改查、评论和历史记录
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc, asc, text
from typing import Dict, Any, List, Tuple, Optional, Union
from datetime import datetime
import uuid
import traceback
import sqlalchemy
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import String
import json
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError

from app.models.issue import Issue
from app.models.issue_comment import IssueComment
from app.models.issue_history import IssueHistory
from app.models.user import User
from app.models.project import Project
from app.models.code_commit import CodeCommit

from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError, AuthorizationError
from app.config.logging_config import logger
from app.services.base_service import BaseService

class IssueService(BaseService[Issue]):
    """问题服务类"""

    def __init__(self, db: Session):
        """
        初始化问题服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def _get_user_role_and_project_ids(self, user_id: int) -> Tuple[str, List[int]]:
        """
        获取用户角色和相关项目ID列表
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            Tuple[str, List[int]]: 角色类型和项目ID列表
                角色类型:
                - "admin": 管理员可查看所有数据
                - "project_admin": 项目管理员可查看其管理的项目数据
                - "member": 普通成员只能查看与自己相关的数据
        """
        from app.models.role import Role
        from app.models.user_role import UserRole
        from app.models.project_role import ProjectRole
        
        # 检查用户是否为管理员或审核员
        admin_roles = self.db.query(Role.name).join(UserRole).filter(
            UserRole.user_id == user_id,
            Role.name.in_(["admin", "review"])
        ).all()
        
        if admin_roles:
            # 用户是管理员或审核员，可查看所有数据
            return "admin", []
        
        # 检查用户是否为项目管理员
        # project_admin_ids = self.db.query(ProjectRole.project_id).filter(
        #     ProjectRole.user_id == user_id,
        #     ProjectRole.role_name == "admin"
        # ).all()
        project_admin_ids = self.db.query(Role.name).join(UserRole).filter(
            UserRole.user_id == user_id,
            Role.name.in_(["project_admin"])
        ).all()
        if project_admin_ids:
            # 用户是项目管理员，可查看其管理的项目数据
            return "project_admin", [row[0] for row in project_admin_ids]
        
        # 获取用户参与的所有项目
        member_project_ids = self.db.query(ProjectRole.project_id).filter(
            ProjectRole.user_id == user_id,
            ProjectRole.is_active == True
        ).all()
        
        # 普通成员，只能查看与自己相关的数据
        return "member", [row[0] for row in member_project_ids]

    def get_issues(
        self,
        project_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        issue_type: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        current_user_id: Optional[int] = None  # 添加当前用户ID参数
    ) -> Dict[str, Any]:
        """
        获取问题列表
        
        Args:
            project_id (int): 项目ID
            status (Optional[str]): 问题状态
            priority (Optional[str]): 问题优先级
            assignee_id (Optional[int]): 指派人ID
            creator_id (Optional[int]): 创建者ID
            tag_id (Optional[int]): 标签ID
            issue_type (Optional[str]): 问题类型
            created_after (Optional[str]): 创建时间后
            created_before (Optional[str]): 创建时间前
            keyword (Optional[str]): 关键词，用于搜索标题和描述
            page (int): 页码，默认为1
            page_size (int): 每页大小，默认为10
            sort_by (str): 排序字段，默认为created_at
            sort_order (str): 排序方向，默认为desc
            current_user_id (Optional[int]): 当前用户ID，用于基于角色过滤数据
            
        Returns:
            Dict[str, Any]: 分页响应，包含问题列表和分页信息
        """
        def _query():
            # 检查项目是否存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 项目名称用于添加到每个问题中
            project_name = project.name
            
            # 构建基本查询
            query = self.db.query(Issue).filter(Issue.project_id == project_id)
            
            # 基于用户角色应用数据过滤
            if current_user_id:
                role_type, project_ids = self._get_user_role_and_project_ids(current_user_id)
                
                if role_type == "admin":
                    # 管理员可以查看所有数据，不需要额外过滤
                    pass
                elif role_type == "project_admin":
                    # 项目管理员只能查看其管理的项目数据
                    if project_id not in project_ids:
                        # 如果当前项目不在用户管理的项目列表中，则返回空结果
                        return [], 0
                else:  # role_type == "member"
                    # 普通成员只能查看与自己相关的数据
                    query = query.filter(
                        or_(
                            Issue.creator_id == current_user_id,  # 自己创建的
                            Issue.assignee_id == current_user_id   # 指派给自己的
                        )
                    )
            
            # 应用过滤条件
            if status:
                query = query.filter(Issue.status == status)
                
            if priority:
                query = query.filter(Issue.priority == priority)
                
            if assignee_id:
                query = query.filter(Issue.assignee_id == assignee_id)
                
            if creator_id:
                query = query.filter(Issue.creator_id == creator_id)
                
            if tag_id:
                query = query.filter(Issue.tag_id == tag_id)

            if issue_type:
                query = query.filter(Issue.issue_type == issue_type)
                
            if keyword:
                search_keyword = f"%{keyword}%"
                query = query.filter(
                    or_(
                        Issue.title.ilike(search_keyword),
                        Issue.description.ilike(search_keyword)
                    )
                )
            
            if created_after:
                query = query.filter(Issue.created_at >= datetime.fromtimestamp(float(created_after)))
            
            if created_before:
                query = query.filter(Issue.created_at <= datetime.fromtimestamp(float(created_before)))
            
            # 计算总数
            total = query.count()
            
            # 应用排序
            if sort_by in ["created_at", "updated_at", "priority", "status", "title"]:
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(getattr(Issue, sort_by)))
                else:
                    query = query.order_by(asc(getattr(Issue, sort_by)))
            else:
                # 默认按创建时间降序
                query = query.order_by(desc(Issue.created_at))
            
            # 应用分页
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 获取问题列表
            issues = query.all()
            
            # 转换为字典列表
            issue_dicts = []
            for issue in issues:
                issue_dict = issue.to_dict()
                
                # 添加项目名称
                issue_dict["project_name"] = project_name
                
                # 添加创建者和指派人信息
                if issue.creator_id:
                    creator = self.db.query(User).filter(User.id == issue.creator_id).first()
                    if creator:
                        issue_dict["creator_name"] = creator.username
                        issue_dict["creator"] = {
                            "id": creator.id,
                            "username": creator.username,
                            "name": getattr(creator, "name", None)
                        }
                
                if issue.assignee_id:
                    assignee = self.db.query(User).filter(User.id == issue.assignee_id).first()
                    if assignee:
                        issue_dict["assignee_name"] = assignee.username
                        issue_dict["assignee"] = {
                            "id": assignee.id,
                            "username": assignee.username,
                            "name": getattr(assignee, "name", None)
                        }
                
                # 确保creator_name不为None
                if issue.creator:
                    issue_dict["creator_name"] = issue.creator.username
                else:
                    issue_dict["creator_name"] = "未知用户"
                
                issue_dicts.append(issue_dict)
            
            return issue_dicts, total
        
        items, total = self._safe_query(_query, f"获取项目 {project_id} 的问题列表失败")
        return self.paginated_response(items, total, page, page_size)
        
    def create_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建问题
        
        Args:
            data (Dict[str, Any]): 问题数据
                - project_id (int): 项目ID
                - title (str): 问题标题
                - description (str, optional): 问题描述
                - status (str, optional): 问题状态，默认为"open"
                - priority (str, optional): 问题优先级，默认为"medium"
                - issue_type (str, optional): 问题类型，默认为"bug"
                - creator_id (int): 创建者ID
                - assignee_id (int, optional): 指派人ID
                - commit_id (int, optional): 关联提交ID
                - file_path (str, optional): 文件路径
                - line_start (int, optional): 起始行号 
                - line_end (int, optional): 结束行号
                - severity (str, optional): 严重程度
                
        Returns:
            Dict[str, Any]: 标准响应，包含创建的问题
        """
        try:
            # 验证必要字段
            required_fields = ["project_id", "title", "creator_id"]
            for field in required_fields:
                if field not in data:
                    raise BusinessError(message=f"缺少必要字段: {field}")
            
            # 验证项目是否存在
            project_id = data["project_id"]
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
                
            # 验证创建者是否存在
            creator_id = data["creator_id"]
            creator = self.db.query(User).filter(User.id == creator_id).first()
            if not creator:
                raise ResourceNotFound(message=f"创建者ID {creator_id} 不存在")
                
            # 验证指派人是否存在
            if "assignee_id" in data and data["assignee_id"]:
                assignee_id = data["assignee_id"]
                assignee = self.db.query(User).filter(User.id == assignee_id).first()
                if not assignee:
                    raise ResourceNotFound(message=f"指派人ID {assignee_id} 不存在")
            
            # 设置默认值
            now = datetime.utcnow()
            issue_dict = None
            
            try:
                # 创建问题
                new_issue = Issue(
                    project_id=project_id,
                    title=data["title"],
                    description=data.get("description"),
                    status=data.get("status", "open"),
                    priority=data.get("priority", "medium"),
                    issue_type=data.get("issue_type", "bug"),
                    creator_id=creator_id,
                    assignee_id=data.get("assignee_id"),
                    commit_id=data.get("commit_id"),
                    file_path=data.get("file_path"),
                    line_start=data.get("line_start"),
                    line_end=data.get("line_end"),
                    severity=data.get("severity"),
                    created_at=now,
                    updated_at=now
                )
                
                self.db.add(new_issue)
                self.db.flush()  # 使用flush而不是commit，保持事务打开
                
                # 记录问题创建历史
                history = IssueHistory(
                    issue_id=new_issue.id,
                    field_name="status",
                    old_value=None,
                    new_value="open",
                    user_id=creator_id,
                    changed_at=now
                )
                
                self.db.add(history)
                self.db.flush()  # 再次flush，但仍保持事务打开
                
                # 返回问题信息
                issue_dict = new_issue.to_dict()
                
                # 添加创建者信息
                issue_dict["creator"] = {
                    "id": creator.id,
                    "username": creator.username,
                    "name": getattr(creator, "name", None)
                }
                
                # 添加项目名称
                issue_dict["project_name"] = project.name
                
                # 添加指派人信息
                if new_issue.assignee_id:
                    assignee = self.db.query(User).filter(User.id == new_issue.assignee_id).first()
                    if assignee:
                        issue_dict["assignee"] = {
                            "id": assignee.id,
                            "username": assignee.username,
                            "name": getattr(assignee, "name", None)
                        }
                
                # 仅在所有操作都成功后提交事务
                self.db.commit()
                return self.standard_response(True, issue_dict, "问题创建成功")
                
            except Exception as e:
                # 任何异常都回滚事务
                self.db.rollback()
                logger.error(f"创建问题时发生错误: {str(e)}")
                raise
                
        except (ResourceNotFound, BusinessError) as e:
            # 业务逻辑异常
            logger.warning(f"创建问题失败: {str(e)}")
            raise DatabaseError(message=f"创建问题失败: {str(e)}")
        except Exception as e:
            # 其他意外异常
            logger.error(f"创建问题时发生未预期错误: {str(e)}")
            raise DatabaseError(message=f"创建问题失败: {str(e)}")
    
    def get_issue_detail(self, issue_id: int) -> Dict[str, Any]:
        """
        获取问题详情
        
        Args:
            issue_id (int): 问题ID
            
        Returns:
            Dict[str, Any]: 问题详情字典
        """
        def _query():
            # 获取问题
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                logger.warning(f"问题ID {issue_id} 不存在")
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 获取问题详情
            issue_dict = issue.to_dict()
            
            # 确保issue_title字段存在（作为title的别名）
            issue_dict["issue_title"] = issue_dict.get("title", "")
            
            # 确保issue_type字段存在
            if "issue_type" not in issue_dict:
                issue_dict["issue_type"] = issue.type if hasattr(issue, "type") else "unknown"
                logger.warning(f"问题ID {issue_id} 缺少issue_type字段，设置为: {issue_dict['issue_type']}")
            
            # 获取项目信息
            project = self.db.query(Project).filter(Project.id == issue.project_id).first()
            if project:
                issue_dict["project"] = {
                    "id": project.id,
                    "name": project.name
                }
                # 添加项目名称到顶层结构
                issue_dict["project_name"] = project.name
            
            # 获取创建者信息
            creator_id = issue.creator_id
            creator = self.db.query(User).filter(User.id == creator_id).first()
            if creator:
                issue_dict["creator"] = {
                    "id": creator.id,
                    "username": creator.username,
                    "name": getattr(creator, "name", None)
                }
                # 添加创建者名称到顶层
                issue_dict["creator_name"] = creator.username
            else:
                issue_dict["creator_name"] = "未知用户"
            
            # 获取指派人信息
            assignee_id = issue.assignee_id
            if assignee_id:
                assignee = self.db.query(User).filter(User.id == assignee_id).first()
                if assignee:
                    issue_dict["assignee"] = {
                        "id": assignee.id,
                        "username": assignee.username,
                        "name": getattr(assignee, "name", None)
                    }
                    # 添加指派人名称到顶层
                    issue_dict["assignee_name"] = assignee.username
                else:
                    issue_dict["assignee_name"] = "未知用户"
            else:
                issue_dict["assignee_name"] = "未指派"
            
            # 获取评论数量
            # 修复自相关问题：显式指定correlate
            comment_count_query = self.db.query(func.count(IssueComment.id)).filter(IssueComment.issue_id == issue_id).correlate(None)
            issue_dict["comment_count"] = comment_count_query.scalar() or 0
            
            return issue_dict
        
        return self._safe_query(_query, f"获取问题 {issue_id} 详情失败")
    
    def update_issue_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新问题状态
        
        Args:
            data (Dict[str, Any]): 更新数据
                - issue_id (int): 问题ID
                - status (str): 新状态
                - user_id (int): 用户ID
                - comment (Optional[str]): 状态更新说明
            
        Returns:
            Dict[str, Any]: 更新后的问题详情
            
        Raises:
            ResourceNotFound: 问题不存在
            BusinessError: 业务错误
            DatabaseError: 数据库错误
        """
        # 验证必要字段
        required_fields = ["issue_id", "status", "user_id"]
        for field in required_fields:
            if field not in data:
                raise BusinessError(message=f"缺少必要字段: {field}")
        
        issue_id = data["issue_id"]
        status = data["status"]
        user_id = data["user_id"]
        
        # 验证状态值
        valid_statuses = {"open", "in_progress", "resolved", "verified", "closed", "reopened","rejected"}
        if status not in valid_statuses:
            raise BusinessError(message=f"无效的状态值: {status}，有效值: {', '.join(valid_statuses)}")
        
        try:
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 获取问题
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 如果状态相同，不做更改
            if issue.status == status:
                return self.get_issue_detail(issue_id)
            
            # 在单个事务中完成所有数据库操作
            try:
                # 记录旧状态
                old_status = issue.status
                
                # 使用模型的update_status方法更新状态并获取历史记录
                history = issue.update_status(status, user_id)
                
                # 将历史记录添加到会话
                self.db.add(history)
                
                # 更新问题的更新时间
                issue.updated_at = datetime.now()
                
                # 先flush以确保issue的更改已应用，但事务仍保持打开
                self.db.flush()
                
                # 如果提供了评论，添加评论
                if "comment" in data and data["comment"]:
                    comment = IssueComment(
                        issue_id=issue_id,
                        user_id=user_id,
                        content=data["comment"],
                        created_at=datetime.now()
                    )
                    self.db.add(comment)
                
                # 提交所有更改
                self.db.commit()
                
                logger.info(f"更新问题状态成功: ID {issue_id}, 从 {old_status} 变更为 {status}")
                
                # 返回更新后的问题详情
                return self.get_issue_detail(issue_id)
                
            except Exception as e:
                # 如果任何操作失败，回滚整个事务
                self.db.rollback()
                logger.error(f"更新问题状态事务失败: {str(e)}")
                raise DatabaseError(message="更新问题状态失败", detail=str(e))
                
        except (ResourceNotFound, BusinessError) as e:
            logger.warning(f"更新问题状态参数错误: {str(e)}")
            raise
        except DatabaseError:
            # 已在内部处理过的数据库错误，直接重新抛出
            raise
        except Exception as e:
            logger.error(f"更新问题状态失败: {str(e)}")
            raise DatabaseError(message="更新问题状态失败", detail=str(e))
    
    def add_comment(self, data: Dict[str, Any]) -> IssueComment:
        """
        添加问题评论
        
        Args:
            data (Dict[str, Any]): 评论数据
                - issue_id (int): 问题ID
                - user_id (int): 用户ID
                - content (str): 评论内容
                - file_path (Optional[str]): 相关文件路径
                - line_number (Optional[int]): 相关行号
                
        Returns:
            IssueComment: 创建的评论
            
        Raises:
            ResourceNotFound: 问题或用户不存在
            BusinessError: 业务错误
            DatabaseError: 数据库错误
        """
        try:
            # 验证必要字段
            required_fields = ["issue_id", "user_id", "content"]
            for field in required_fields:
                if field not in data:
                    raise BusinessError(message=f"缺少必要字段: {field}")
            
            issue_id = data["issue_id"]
            user_id = data["user_id"]
            content = data["content"]
            
            # 验证内容不为空
            if not content.strip():
                raise BusinessError(message="评论内容不能为空")
            
            # 验证问题是否存在
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
                
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 创建评论
            comment = IssueComment(
                issue_id=issue_id,
                user_id=user_id,
                content=content,
                file_path=data.get("file_path"),
                line_number=data.get("line_number"),
                created_at=datetime.now()
            )
            
            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)
            
            # 更新问题的更新时间
            issue.updated_at = datetime.now()
            self.db.commit()
            
            # 处理用户对象，将User对象转换为字典
            # 这样后续序列化时不会出错
            if hasattr(comment, 'user') and comment.user:
                comment.user_dict = {
                    'id': comment.user.id,
                    'user_id': comment.user.user_id,
                    'username': comment.user.username
                }
                # 暂时移除user属性，避免序列化错误
                comment.user = None
            
            logger.info(f"添加评论成功: 问题ID {issue_id}, 用户ID {user_id}")
            return comment
        
        except (ResourceNotFound, BusinessError):
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"添加评论失败: {str(e)}")
            raise DatabaseError(message="添加评论失败", detail=str(e))
    
    def get_comments(
        self,
        issue_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取问题评论列表
        
        Args:
            issue_id (int): 问题ID
            page (int): 页码，默认为1
            page_size (int): 每页大小，默认为10
            
        Returns:
            List[Dict[str, Any]]: 评论列表
            
        Raises:
            ResourceNotFound: 问题不存在
            DatabaseError: 数据库错误
        """
        def _query():
            # 检查问题是否存在
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 构建评论查询
            query = self.db.query(IssueComment).filter(IssueComment.issue_id == issue_id)
            
            # 计算总数
            total = query.count()
            
            # 按创建时间降序排序
            query = query.order_by(IssueComment.created_at.desc())
            
            # 应用分页
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 获取评论列表
            comments = query.all()
            
            # 转换为字典列表
            comment_dicts = []
            for comment in comments:
                comment_dict = comment.to_dict()
                
                # 添加用户信息
                if comment.user_id:
                    user = self.db.query(User).filter(User.id == comment.user_id).first()
                    if user:
                        comment_dict["user"] = {
                            "id": user.id,
                            "username": user.username,
                            "name": getattr(user, "name", None),
                            "avatar": getattr(user, "avatar", None)
                        }
                        # 添加username字段
                        comment_dict["username"] = user.username
                        # 添加user_name字段(兼容旧接口)
                        comment_dict["user_name"] = user.username
                
                comment_dicts.append(comment_dict)
            
            return comment_dicts
        
        return self._safe_query(_query, f"获取问题 {issue_id} 评论列表失败", [])
    
    def get_issue_history(
        self,
        issue_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取问题历史记录
        
        Args:
            issue_id (int): 问题ID
            page (int): 页码，默认为1
            page_size (int): 每页大小，默认为10
            
        Returns:
            List[Dict[str, Any]]: 历史记录列表
            
        Raises:
            ResourceNotFound: 问题不存在
            DatabaseError: 数据库错误
        """
        def _query():
            # 检查问题是否存在
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 获取历史记录
            from app.models.issue_history import IssueHistory
            
            # 构建查询
            query = self.db.query(IssueHistory).filter(IssueHistory.issue_id == issue_id)
            
            # 计算总数
            total = query.count()
            
            # 按时间降序排序
            query = query.order_by(IssueHistory.changed_at.desc())
            
            # 应用分页
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 获取历史记录列表
            histories = query.all()
            
            # 转换为字典列表
            history_dicts = []
            for history in histories:
                history_dict = history.to_dict()
                
                # 添加用户信息
                if history.user_id:
                    user = self.db.query(User).filter(User.id == history.user_id).first()
                    if user:
                        history_dict["user"] = {
                            "id": user.id,
                            "username": user.username,
                            "name": getattr(user, "name", None),
                            "avatar": getattr(user, "avatar", None)
                        }
                
                history_dicts.append(history_dict)
            
            return history_dicts
        
        return self._safe_query(_query, f"获取问题 {issue_id} 历史记录失败", [])
    
    def _add_history(
        self,
        issue_id: int,
        action: str,
        field: str,
        old_value: Optional[str],
        new_value: Optional[str],
        user_id: int
    ) -> IssueHistory:
        """
        添加问题历史记录
        
        Args:
            issue_id (int): 问题ID
            action (str): 动作
            field (str): 字段
            old_value (Optional[str]): 旧值
            new_value (Optional[str]): 新值
            user_id (int): 用户ID
            
        Returns:
            IssueHistory: 创建的历史记录
        """
        from app.models.issue_history import IssueHistory
        
        history = IssueHistory(
            issue_id=issue_id,
            user_id=user_id,
            field_name=field,
            old_value=old_value,
            new_value=new_value,
            changed_at=datetime.now()
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history

    # 以下为代码检视问题特有方法
    def create_code_review_issue(self, data: Dict[str, Any]) -> Issue:
        """
        创建代码检视问题
        
        Args:
            data (Dict[str, Any]): 问题数据
                - project_id (int): 项目ID
                - commit_id (int): 提交ID
                - file_path (str): 文件路径
                - line_start (int): 起始行号
                - line_end (int): 结束行号
                - title (str): 问题标题
                - description (str): 问题描述
                - severity (str): 严重程度
                - priority (str): 优先级
                - creator_id (int): 创建人ID
                - assignee_id (Optional[int]): 指派人ID，默认为创建人
                
        Returns:
            Issue: 创建的代码检视问题
            
        Raises:
            BusinessError: 业务错误
            DatabaseError: 数据库错误
        """
        try:
            # 验证必要字段
            required_fields = ["project_id", "commit_id", "file_path", "line_start", 
                               "line_end", "title", "description", "severity", "creator_id"]
            for field in required_fields:
                if field not in data:
                    raise BusinessError(message=f"缺少必要参数: {field}")
            
            # 验证行号
            if data["line_start"] < 1 or data["line_end"] < data["line_start"]:
                raise BusinessError(message="行号无效：起始行必须大于0，结束行必须大于等于起始行")
            
            # 验证严重程度
            valid_severities = ["low", "medium", "high", "critical"]
            if data["severity"] not in valid_severities:
                raise BusinessError(message=f"无效的严重程度: {data['severity']}，有效值: {', '.join(valid_severities)}")
            
            # 设置默认指派人
            assignee_id = data.get("assignee_id", data["creator_id"])
            
            # 创建问题
            new_issue = Issue(
                project_id=data["project_id"],
                commit_id=data["commit_id"],
                title=data["title"],
                description=data["description"],
                status="open",  # 默认状态为open
                priority=data.get("priority", "medium"),
                issue_type="code_review",  # 标记为代码检视问题
                severity=data["severity"],
                creator_id=data["creator_id"],
                assignee_id=assignee_id,
                file_path=data["file_path"],
                line_start=data["line_start"],
                line_end=data["line_end"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.db.add(new_issue)
            self.db.commit()
            self.db.refresh(new_issue)
            
            logger.info(f"创建代码检视问题成功: {new_issue.id}")
            return new_issue
            
        except BusinessError:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建代码检视问题失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise DatabaseError(message="创建代码检视问题失败", detail=str(e))
    
    def get_commit_issues(self, commit_id: int) -> List[Issue]:
        """
        获取提交关联的所有问题
        
        Args:
            commit_id (int): 提交ID
            
        Returns:
            List[Issue]: 问题列表
            
        Raises:
            DatabaseError: 数据库错误
        """
        try:
            issues = self.db.query(Issue).filter(
                Issue.commit_id == commit_id,
                Issue.issue_type == "code_review"
            ).all()
            
            return issues
        except Exception as e:
            logger.error(f"获取提交问题失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise DatabaseError(message="获取提交问题失败", detail=str(e))
    
    def get_code_review_issues(
        self, 
        project_id: Optional[int] = None, 
        creator_id: Optional[int] = None, 
        assignee_id: Optional[int] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        user_id: Optional[int] = None,  # 权限过滤参数
        current_user_id: Optional[int] = None  # 角色过滤参数
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        获取代码检视问题列表
        
        Args:
            project_id (Optional[int]): 项目ID
            creator_id (Optional[int]): 创建人ID
            assignee_id (Optional[int]): 指派人ID
            severity (Optional[str]): 严重程度
            status (Optional[str]): 状态
            page (int): 页码
            page_size (int): 每页数量
            user_id (Optional[int]): 用户ID，用于权限过滤
            current_user_id (Optional[int]): 当前用户ID，用于基于角色过滤数据
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 问题列表和总数
            
        Raises:
            DatabaseError: 数据库错误
        """
        try:
            # 使用别名来区分不同的User表实例
            creator = aliased(User, name="creator")
            assignee = aliased(User, name="assignee")
            
            # 构建基础查询
            query = self.db.query(
                Issue,
                creator.username.label("creator_name"),
                func.coalesce(assignee.username, "").label("assignee_name"),
                Project.name.label("project_name")
            ).join(
                creator, Issue.creator_id == creator.id
            ).outerjoin(
                assignee, Issue.assignee_id == assignee.id
            ).join(
                Project, Issue.project_id == Project.id
            ).filter(
                Issue.issue_type == "code_review"
            )
            
            # 基于用户角色应用数据过滤
            if current_user_id:
                role_type, project_ids = self._get_user_role_and_project_ids(current_user_id)
                
                if role_type == "admin":
                    # 管理员可以查看所有数据，不需要额外过滤
                    pass
                elif role_type == "project_admin":
                    # 项目管理员只能查看其管理的项目数据
                    if project_id and project_id not in project_ids:
                        # 如果指定了项目ID但不在管理范围内，返回空结果
                        return [], 0
                    elif not project_id:
                        # 如果没有指定项目ID，则限制为管理的项目
                        query = query.filter(Issue.project_id.in_(project_ids))
                else:  # role_type == "member"
                    # 普通成员只能查看与自己相关的数据
                    query = query.filter(
                        or_(
                            Issue.creator_id == current_user_id,  # 自己创建的
                            Issue.assignee_id == current_user_id   # 指派给自己的
                        )
                    )
            
            # 根据用户权限过滤项目（这是之前实现的基于权限的过滤）
            if user_id and not current_user_id:  # 只有在没有使用基于角色过滤时才使用权限过滤
                # 导入ProjectRole模型
                from app.models.project_role import ProjectRole
                
                # 获取用户有权限访问的项目ID列表
                # 1. 用户创建的项目
                # 2. 用户通过ProjectRole关联的项目
                user_project_ids_query = (
                    self.db.query(Project.id)
                    .filter(
                        or_(
                            Project.created_by == user_id,  # 用户创建的项目
                            Project.id.in_(  # 用户有角色的项目
                                self.db.query(ProjectRole.project_id)
                                .filter(
                                    ProjectRole.user_id == user_id,
                                    ProjectRole.is_active == True
                                )
                            )
                        )
                    )
                )
                
                # 执行查询获取项目ID列表
                user_project_ids = [row[0] for row in user_project_ids_query.all()]
                
                if not user_project_ids:
                    # 用户没有任何项目权限，返回空结果
                    return [], 0
                
                # 只查询用户有权限的项目
                query = query.filter(Issue.project_id.in_(user_project_ids))
            
            # 应用过滤条件
            if project_id:
                query = query.filter(Issue.project_id == project_id)
            if creator_id:
                query = query.filter(Issue.creator_id == creator_id)
            if assignee_id:
                query = query.filter(Issue.assignee_id == assignee_id)
            if severity:
                query = query.filter(Issue.severity == severity)
            if status:
                query = query.filter(Issue.status == status)
                
            # 获取总数
            total = query.count()
            
            # 分页查询
            query = query.order_by(Issue.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 执行查询
            result = query.all()
            
            # 处理结果
            issues = []
            for row in result:
                issue = row[0].to_dict()
                issue["creator_name"] = row[1]
                issue["assignee_name"] = row[2] or "未知用户"  # 确保assignee_name不为None
                issue["project_name"] = row[3]
                
                # 获取评论数
                comment_count = self.db.query(func.count(IssueComment.id)).filter(
                    IssueComment.issue_id == row[0].id
                ).scalar()
                
                issue["comment_count"] = comment_count
                issues.append(issue)
            
            return issues, total
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"获取代码检视问题列表失败: {str(e)}")
            raise DatabaseError(message="获取代码检视问题列表失败", detail=str(e))

    def get_issue_count(
        self,
        project_id: Optional[int] = None,
        status_filter: Optional[List[str]] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        issue_type: Optional[str] = None
    ) -> int:
        """
        获取问题数量
        
        Args:
            project_id (Optional[int]): 项目ID
            status_filter (Optional[List[str]]): 状态过滤列表，例如["open", "in_progress"]
            assignee_id (Optional[int]): 负责人ID
            creator_id (Optional[int]): 创建者ID
            issue_type (Optional[str]): 问题类型
            
        Returns:
            int: 符合条件的问题数量
        """
        def _query():
            # 构建基础查询
            query = self.db.query(func.count(Issue.id))
            
            # 添加过滤条件
            if project_id is not None:
                query = query.filter(Issue.project_id == project_id)
                
            if status_filter:
                query = query.filter(Issue.status.in_(status_filter))
                
            if assignee_id is not None:
                query = query.filter(Issue.assignee_id == assignee_id)
                
            if creator_id is not None:
                query = query.filter(Issue.creator_id == creator_id)
                
            if issue_type is not None:
                query = query.filter(Issue.issue_type == issue_type)
            
            # 执行查询并返回结果
            count = query.scalar()
            
            return count or 0
        
        return self._safe_query(_query, f"获取问题数量失败")

    def get_issue_commits(self, issue_id: int) -> List[Dict[str, Any]]:
        """
        获取问题相关的代码提交记录
        
        Args:
            issue_id (int): 问题ID
            
        Returns:
            List[Dict[str, Any]]: 代码提交记录列表
            
        Raises:
            ResourceNotFound: 问题不存在
            DatabaseError: 数据库错误
        """
        def _query():
            # 检查问题是否存在
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 查询与问题相关的提交记录
            # 假设提交消息中包含问题ID的引用，例如 #123
            commits = self.db.query(CodeCommit).filter(
                or_(
                    CodeCommit.commit_message.contains(f"#{issue_id}"),
                    CodeCommit.commit_message.contains(f"issue-{issue_id}"),
                    CodeCommit.commit_message.contains(f"fix #{issue_id}")
                )
            ).order_by(CodeCommit.commit_time.desc()).all()
            
            # 转换为字典列表
            commit_dicts = []
            for commit in commits:
                commit_dict = commit.to_dict()
                
                # 获取提交者信息（如果有）
                if commit.author_id:
                    user = self.db.query(User).filter(User.id == commit.author_id).first()
                    if user:
                        commit_dict["author"] = {
                            "id": user.id,
                            "username": user.username,
                            "name": getattr(user, "name", None),
                            "avatar": getattr(user, "avatar", None)
                        }
                
                commit_dicts.append(commit_dict)
            
            return commit_dicts
        
        return self._safe_query(_query, f"获取问题 {issue_id} 相关提交记录失败", [])

    def get_user_issues(
        self,
        user_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        creator_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        issue_type: Optional[str] = None,
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        current_user_id: Optional[int] = None  # 添加当前用户ID参数
    ) -> Dict[str, Any]:
        """
        获取用户有权限访问的所有项目的问题列表
        
        Args:
            user_id (int): 用户ID（用于查询条件）
            status (Optional[str]): 问题状态
            priority (Optional[str]): 问题优先级
            assignee_id (Optional[int]): 指派人ID
            creator_id (Optional[int]): 创建者ID
            tag_id (Optional[int]): 标签ID
            issue_type (Optional[str]): 问题类型
            created_after (Optional[str]): 创建时间后
            created_before (Optional[str]): 创建时间前
            keyword (Optional[str]): 关键词，用于搜索标题和描述
            page (int): 页码，默认为1
            page_size (int): 每页大小，默认为10
            sort_by (str): 排序字段，默认为created_at
            sort_order (str): 排序方向，默认为desc
            current_user_id (Optional[int]): 当前用户ID，用于基于角色过滤数据
            
        Returns:
            Dict[str, Any]: 分页响应，包含问题列表和分页信息
        """
        def _query():
            # 导入ProjectRole模型
            from app.models.project_role import ProjectRole
            
            # 获取用户有权限访问的项目ID列表
            # 1. 用户创建的项目
            # 2. 用户通过ProjectRole关联的项目
            user_project_ids_query = (
                self.db.query(Project.id)
                .filter(
                    or_(
                        Project.created_by == user_id,  # 用户创建的项目
                        Project.id.in_(  # 用户有角色的项目
                            self.db.query(ProjectRole.project_id)
                            .filter(
                                ProjectRole.user_id == user_id,
                                ProjectRole.is_active == True
                            )
                        )
                    )
                )
            )
            
            # 执行查询获取项目ID列表
            user_project_ids = [row[0] for row in user_project_ids_query.all()]
            
            if not user_project_ids:
                # 用户没有任何项目权限
                return [], 0
            
            # 构建基本查询 - 查询用户有权限的项目中的问题
            query = (
                self.db.query(Issue)
                .join(Project, Issue.project_id == Project.id)
                .filter(Issue.project_id.in_(user_project_ids))
            )
            
            # 基于用户角色应用数据过滤
            if current_user_id:
                role_type, project_ids = self._get_user_role_and_project_ids(current_user_id)
                
                if role_type == "admin":
                    # 管理员可以查看所有数据，不需要额外过滤
                    pass
                elif role_type == "project_admin":
                    # 项目管理员只能查看其管理的项目数据
                    query = query.filter(Issue.project_id.in_(project_ids))
                else:  # role_type == "member"
                    # 普通成员只能查看与自己相关的数据
                    query = query.filter(
                        or_(
                            Issue.creator_id == current_user_id,  # 自己创建的
                            Issue.assignee_id == current_user_id   # 指派给自己的
                        )
                    )
            
            # 应用过滤条件
            if status:
                query = query.filter(Issue.status == status)
                
            if priority:
                query = query.filter(Issue.priority == priority)
                
            if assignee_id:
                query = query.filter(Issue.assignee_id == assignee_id)
                
            if creator_id:
                query = query.filter(Issue.creator_id == creator_id)
                
            if tag_id:
                query = query.filter(Issue.tag_id == tag_id)
                
            if issue_type:
                query = query.filter(Issue.issue_type == issue_type)
                
            if keyword:
                search_keyword = f"%{keyword}%"
                query = query.filter(
                    or_(
                        Issue.title.ilike(search_keyword),
                        Issue.description.ilike(search_keyword)
                    )
                )
            
            if created_after:
                query = query.filter(Issue.created_at >= datetime.fromtimestamp(float(created_after)))
            
            if created_before:
                query = query.filter(Issue.created_at <= datetime.fromtimestamp(float(created_before)))
            
            # 计算总数
            total = query.count()
            
            # 应用排序
            if sort_by in ["created_at", "updated_at", "priority", "status", "title"]:
                if sort_order.lower() == "desc":
                    query = query.order_by(desc(getattr(Issue, sort_by)))
                else:
                    query = query.order_by(asc(getattr(Issue, sort_by)))
            else:
                # 默认按创建时间降序
                query = query.order_by(desc(Issue.created_at))
            
            # 应用分页
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 获取问题列表
            issues = query.all()
            
            # 创建项目ID到项目名称的映射，减少数据库查询次数
            project_ids = set(issue.project_id for issue in issues)
            project_map = {}
            
            if project_ids:
                projects = self.db.query(Project).filter(Project.id.in_(project_ids)).all()
                project_map = {project.id: project.name for project in projects}
            
            # 获取用户ID列表，用于批量查询用户信息
            user_ids = set()
            for issue in issues:
                if issue.creator_id:
                    user_ids.add(issue.creator_id)
                if issue.assignee_id:
                    user_ids.add(issue.assignee_id)
            
            # 创建用户ID到用户名的映射
            user_map = {}
            if user_ids:
                users = self.db.query(User).filter(User.id.in_(user_ids)).all()
                user_map = {user.id: user.username for user in users}
            
            # 转换为字典列表
            issue_dicts = []
            for issue in issues:
                issue_dict = issue.to_dict()
                
                # 添加项目名称
                issue_dict["project_name"] = project_map.get(issue.project_id, "未知项目")
                
                # 添加创建者和指派人信息
                if issue.creator_id and issue.creator_id in user_map:
                    issue_dict["creator_name"] = user_map[issue.creator_id]
                else:
                    issue_dict["creator_name"] = "未知用户"
                
                if issue.assignee_id and issue.assignee_id in user_map:
                    issue_dict["assignee_name"] = user_map[issue.assignee_id]
                
                issue_dicts.append(issue_dict)
            
            return issue_dicts, total
        
        items, total = self._safe_query(_query, f"获取用户 {user_id} 的问题列表失败")
        return self.paginated_response(items, total, page, page_size)

    def update_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新问题的所有信息
        
        Args:
            data: 包含更新数据的字典
        
        Returns:
            更新后的问题详情
        """
        issue_id = data.get("issue_id")
        user_id = data.get("user_id")
        
        if not issue_id:
            raise BusinessError(message="问题ID不能为空")
        
        if not user_id:
            raise BusinessError(message="用户ID不能为空")
        
        try:
            def _update(session):
                # 查找问题
                issue = session.query(Issue).filter(Issue.id == issue_id).first()
                if not issue:
                    raise ResourceNotFound(message=f"问题 {issue_id} 不存在")
                
                # 依次更新每个字段并记录历史
                for field in ["title", "description", "priority", "issue_type", "severity", 
                            "assignee_id", "file_path", "line_start", "line_end", 
                            "project_id", "commit_id"]:
                    if field in data and data[field] is not None:
                        old_value = getattr(issue, field)
                        new_value = data[field]
                        
                        # 只有当值发生变化时才更新
                        if old_value != new_value:
                            setattr(issue, field, new_value)
                            
                            # 添加历史记录
                            history = self._add_history(
                                issue_id=issue_id,
                                action="update",
                                field=field,
                                old_value=str(old_value) if old_value is not None else None,
                                new_value=str(new_value) if new_value is not None else None,
                                user_id=user_id
                            )
                            session.add(history)
                
                # 特殊处理状态字段，使用update_status方法
                if "status" in data and data["status"] is not None and data["status"] != issue.status:
                    history = issue.update_status(data["status"], user_id)
                    session.add(history)
                
                # 更新更新时间
                issue.updated_at = datetime.utcnow()
                
                # 保存更改
                session.flush()
                
                # 返回更新后的问题详情
                return self.get_issue_detail(issue_id)
            
            # 执行事务
            return self.db_session(_update)
            
        except ResourceNotFound:
            raise
        except BusinessError:
            raise
        except Exception as e:
            logger.error(f"更新问题 {issue_id} 失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise DatabaseError(message=f"更新问题失败: {str(e)}") 