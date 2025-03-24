from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from app.models.issue import Issue
from app.models.issue_comment import IssueComment
from app.models.code_commit import CodeCommit
from app.models.project import Project
from app.models.user import User
from app.services.base_service import BaseService
from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

class ReviewService(BaseService[Issue]):
    """
    代码检视服务类
    提供代码检视相关功能，包括创建代码检视问题、添加评论等
    开发用户：pgao
    开发时间：2024-05-14 10:30:00
    """
    def __init__(self, db: Session):
        """
        初始化代码检视服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)

    def create_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建代码检视问题
        
        Args:
            data (Dict[str, Any]): 问题数据
                - project_id (int): 项目ID
                - commit_id (int): 提交ID
                - file_path (str): 文件路径
                - line_start (int): 起始行号
                - line_end (int): 结束行号
                - issue_type (str): 问题类型 (style/bug/security/performance)
                - description (str): 问题描述
                - severity (str): 严重程度 (critical/high/medium/low)
                - creator_id (int): 创建者ID
                - title (str): 问题标题
                
        Returns:
            Dict[str, Any]: 标准响应，包含创建的问题信息
        """
        def _query():
            # 验证必要字段
            required_fields = ["project_id", "commit_id", "file_path", "line_start", 
                           "issue_type", "description", "severity", "creator_id", "title"]
            for field in required_fields:
                if field not in data:
                    raise BusinessError(message=f"缺少必要字段: {field}")
            
            # 验证项目是否存在
            project_id = data["project_id"]
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 验证提交是否存在
            commit_id = data["commit_id"]
            commit = self.db.query(CodeCommit).filter(CodeCommit.id == commit_id).first()
            if not commit:
                raise ResourceNotFound(message=f"提交ID {commit_id} 不存在")
            
            # 验证创建者是否存在
            creator_id = data["creator_id"]
            creator = self.db.query(User).filter(User.id == creator_id).first()
            if not creator:
                raise ResourceNotFound(message=f"创建者ID {creator_id} 不存在")
        
            # 验证行号
            line_start = data["line_start"]
            line_end = data.get("line_end", line_start)
            if line_start < 1:
                raise BusinessError(message="起始行号必须大于0")
            if line_end < line_start:
                raise BusinessError(message="结束行号必须大于或等于起始行号")
        
            # 验证问题类型
            issue_type = data["issue_type"]
            valid_types = ["style", "bug", "security", "performance", "code_review"]
            if issue_type not in valid_types:
                raise BusinessError(message=f"无效的问题类型: {issue_type}，有效值: {', '.join(valid_types)}")
        
            # 验证严重程度
            severity = data["severity"]
            valid_severities = ["critical", "high", "medium", "low"]
            if severity not in valid_severities:
                raise BusinessError(message=f"无效的严重程度: {severity}，有效值: {', '.join(valid_severities)}")
        
            # 创建问题
            now = datetime.utcnow()
            new_issue = Issue(
                project_id=project_id,
                commit_id=commit_id,
                title=data["title"],
                description=data["description"],
                status="open",
                priority="medium",
                issue_type=issue_type,
                severity=severity,
                file_path=data["file_path"],
                line_start=line_start,
                line_end=line_end,
                creator_id=creator_id,
                assignee_id=data.get("assignee_id"),
                created_at=now,
                updated_at=now
            )
            
            self.db.add(new_issue)
            self.db.commit()
            self.db.refresh(new_issue)
            
            # 返回问题信息
            issue_dict = new_issue.to_dict()
            
            # 添加创建者信息
            issue_dict["creator"] = {
                "id": creator.id,
                "username": creator.username,
                "name": getattr(creator, "name", None)
            }
            
            # 添加提交信息
            issue_dict["commit"] = {
                "id": commit.id,
                "hash": commit.commit_hash,
                "message": commit.message
            }
            
            return issue_dict
        
        result = self._safe_query(_query, "创建代码检视问题失败")
        return self.standard_response(True, result, "代码检视问题创建成功")

    def add_comment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加代码检视评论
        
        Args:
            data (Dict[str, Any]): 评论数据
                - issue_id (int): 问题ID
                - content (str): 评论内容
                - user_id (int): 用户ID
                
        Returns:
            Dict[str, Any]: 标准响应，包含创建的评论信息
        """
        def _query():
            # 验证必要字段
            required_fields = ["issue_id", "content", "user_id"]
            for field in required_fields:
                if field not in data:
                    raise BusinessError(message=f"缺少必要字段: {field}")
        
            # 验证问题是否存在
            issue_id = data["issue_id"]
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 验证用户是否存在
            user_id = data["user_id"]
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 创建评论
            now = datetime.utcnow()
            new_comment = IssueComment(
                issue_id=issue_id,
                content=data["content"],
                user_id=user_id,
                created_at=now
            )
            
            self.db.add(new_comment)
            self.db.commit()
            self.db.refresh(new_comment)
            
            # 更新问题更新时间
            issue.updated_at = now
            self.db.commit()
            
            # 返回评论信息
            comment_dict = {
                "id": new_comment.id,
                "issue_id": new_comment.issue_id,
                "content": new_comment.content,
                "user_id": new_comment.user_id,
                "username": user.username,
                "created_at": new_comment.created_at
            }
            
            return comment_dict
        
        result = self._safe_query(_query, "添加代码检视评论失败")
        return self.standard_response(True, result, "评论添加成功")

    def update_issue_status(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新代码检视问题状态
        
        Args:
            data (Dict[str, Any]): 状态更新数据
                - issue_id (int): 问题ID
                - status (str): 新状态
                - user_id (int): 操作用户ID
                
        Returns:
            Dict[str, Any]: 标准响应，包含更新后的问题信息
        """
        def _query():
            # 验证必要字段
            required_fields = ["issue_id", "status", "user_id"]
            for field in required_fields:
                if field not in data:
                    raise BusinessError(message=f"缺少必要字段: {field}")
            
            # 验证问题是否存在
            issue_id = data["issue_id"]
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 验证用户是否存在
            user_id = data["user_id"]
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
        
            # 验证状态
            new_status = data["status"]
            valid_statuses = ["open", "in_progress", "resolved", "verified", "closed", "reopened"]
            if new_status not in valid_statuses:
                raise BusinessError(message=f"无效的状态: {new_status}，有效值: {', '.join(valid_statuses)}")
            
            # 验证状态变更是否合理
            old_status = issue.status
            if old_status == new_status:
                return issue.to_dict()
            
            # 更新问题状态
            now = datetime.utcnow()
            issue.status = new_status
            issue.updated_at = now
            
            # 如果是关闭问题，设置关闭时间
            if new_status == "closed":
                issue.closed_at = now
            
            # 如果是解决问题，设置解决时间和计算解决时长
            if new_status == "resolved" and not issue.resolved_at:
                issue.resolved_at = now
                created_at = issue.created_at or now
                resolution_time = (now - created_at).total_seconds() / 3600  # 小时
                issue.resolution_time = resolution_time
            
            # 如果重新打开问题，清除关闭和解决时间
            if new_status == "reopened":
                issue.closed_at = None
                issue.resolved_at = None
                issue.resolution_time = None
            
            self.db.commit()
            self.db.refresh(issue)
            
            # 添加历史记录
            from app.models.issue_history import IssueHistory
            history = IssueHistory(
                issue_id=issue_id,
                action="update",
                field="status",
                old_value=old_status,
                new_value=new_status,
                user_id=user_id,
                created_at=now
            )
            
            self.db.add(history)
            self.db.commit()
            
            # 返回更新后的问题信息
            return issue.to_dict()
        
        result = self._safe_query(_query, "更新代码检视问题状态失败")
        return self.standard_response(True, result, "问题状态更新成功")

    def get_commit_issues(self, commit_id: int) -> Dict[str, Any]:
        """
        获取提交相关的代码检视问题
        
        Args:
            commit_id (int): 提交ID
            
        Returns:
            Dict[str, Any]: 标准响应，包含问题列表
        """
        def _query():
            # 验证提交是否存在
            commit = self.db.query(CodeCommit).filter(CodeCommit.id == commit_id).first()
            if not commit:
                raise ResourceNotFound(message=f"提交ID {commit_id} 不存在")
            
            # 获取问题列表
            issues = self.db.query(Issue).filter(Issue.commit_id == commit_id).all()
            
            # 转换为字典列表
            issue_dicts = [issue.to_dict() for issue in issues]
            
            return issue_dicts
        
        result = self._safe_query(_query, f"获取提交 {commit_id} 的代码检视问题失败")
        return self.standard_response(True, result)

    def get_issues_by_criteria(self, 
                        project_id: Optional[int] = None, 
                        creator_id: Optional[int] = None, 
                        assignee_id: Optional[int] = None,
                        code_author_id: Optional[int] = None,
                        severity: Optional[str] = None,
                        status: Optional[str] = None,
                        page: int = 1,
                        page_size: int = 10) -> Dict[str, Any]:
        """
        根据条件获取代码检视问题
        
        Args:
            project_id (Optional[int]): 项目ID
            creator_id (Optional[int]): 创建者ID
            assignee_id (Optional[int]): 指派人ID
            code_author_id (Optional[int]): 代码作者ID
            severity (Optional[str]): 严重程度
            status (Optional[str]): 状态
            page (int): 页码
            page_size (int): 每页大小
            
        Returns:
            Dict[str, Any]: 分页响应，包含问题列表和分页信息
        """
        def _query():
            # 构建基本查询
            query = self.db.query(Issue).filter(Issue.issue_type == "code_review")
            
            # 应用过滤条件
            if project_id:
                query = query.filter(Issue.project_id == project_id)
            
            if creator_id:
                query = query.filter(Issue.creator_id == creator_id)
            
            if assignee_id:
                query = query.filter(Issue.assignee_id == assignee_id)
            
            if code_author_id:
                # 通过提交查找代码作者
                query = query.join(CodeCommit, Issue.commit_id == CodeCommit.id)
                query = query.filter(CodeCommit.author_id == code_author_id)
            
            if severity:
                query = query.filter(Issue.severity == severity)
            
            if status:
                query = query.filter(Issue.status == status)
            
            # 计算总数
            total = query.count()
            
            # 应用排序和分页
            query = query.order_by(desc(Issue.created_at))
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 获取问题列表
            issues = query.all()
            
            # 转换为字典列表
            issue_dicts = []
            for issue in issues:
                issue_dict = issue.to_dict()
                
                # 添加创建者信息
                if issue.creator_id:
                    creator = self.db.query(User).filter(User.id == issue.creator_id).first()
                    if creator:
                        issue_dict["creator"] = {
                            "id": creator.id,
                            "username": creator.username,
                            "name": getattr(creator, "name", None)
                        }
                
                # 添加指派人信息
                if issue.assignee_id:
                    assignee = self.db.query(User).filter(User.id == issue.assignee_id).first()
                    if assignee:
                        issue_dict["assignee"] = {
                            "id": assignee.id,
                            "username": assignee.username,
                            "name": getattr(assignee, "name", None)
                        }
                
                # 添加提交信息
                if issue.commit_id:
                    commit = self.db.query(CodeCommit).filter(CodeCommit.id == issue.commit_id).first()
                    if commit:
                        issue_dict["commit"] = {
                            "id": commit.id,
                            "hash": commit.commit_hash,
                            "message": commit.message,
                            "author_id": commit.author_id
                        }
                
                issue_dicts.append(issue_dict)
            
            return issue_dicts, total
        
        items, total = self._safe_query(_query, "获取代码检视问题失败")
        return self.paginated_response(items, total, page, page_size)

    def get_issue_detail(self, issue_id: int) -> Dict[str, Any]:
        """
        获取代码检视问题详情
        
        Args:
            issue_id (int): 问题ID
            
        Returns:
            Dict[str, Any]: 标准响应，包含问题详情和评论
        """
        def _query():
            # 验证问题是否存在
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 获取问题详情
            issue_dict = issue.to_dict()
            
            # 添加创建者信息
            if issue.creator_id:
                creator = self.db.query(User).filter(User.id == issue.creator_id).first()
                if creator:
                    issue_dict["creator"] = {
                        "id": creator.id,
                        "username": creator.username,
                        "name": getattr(creator, "name", None)
                    }
            
            # 添加指派人信息
            if issue.assignee_id:
                assignee = self.db.query(User).filter(User.id == issue.assignee_id).first()
                if assignee:
                    issue_dict["assignee"] = {
                        "id": assignee.id,
                        "username": assignee.username,
                        "name": getattr(assignee, "name", None)
                    }
            
            # 添加提交信息
            if issue.commit_id:
                commit = self.db.query(CodeCommit).filter(CodeCommit.id == issue.commit_id).first()
                if commit:
                    issue_dict["commit"] = {
                        "id": commit.id,
                        "hash": commit.commit_hash,
                        "message": commit.message,
                        "author_id": commit.author_id
                    }
            
            # 获取评论
            comments = self.db.query(
                IssueComment, User.username
            ).join(
                User, IssueComment.user_id == User.id
            ).filter(
                IssueComment.issue_id == issue_id
            ).order_by(
                IssueComment.created_at
            ).all()
            
            # 转换评论为字典列表
            comment_dicts = []
            for comment, username in comments:
                comment_dict = {
                    "id": comment.id,
                    "content": comment.content,
                    "user_id": comment.user_id,
                    "username": username,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                }
                comment_dicts.append(comment_dict)
            
            issue_dict["comments"] = comment_dicts
            
            return issue_dict
        
        result = self._safe_query(_query, f"获取问题 {issue_id} 详情失败")
        return self.standard_response(True, result)

    def assign_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        指派代码检视问题
        
        Args:
            data (Dict[str, Any]): 指派数据
                - issue_id (int): 问题ID
                - assignee_id (int): 指派人ID
                - user_id (int): 操作用户ID
                
        Returns:
            Dict[str, Any]: 标准响应，包含更新后的问题信息
        """
        def _query():
            # 验证必要字段
            required_fields = ["issue_id", "assignee_id", "user_id"]
            for field in required_fields:
                if field not in data:
                    raise BusinessError(message=f"缺少必要字段: {field}")
            
            # 验证问题是否存在
            issue_id = data["issue_id"]
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 验证指派人是否存在
            assignee_id = data["assignee_id"]
            assignee = self.db.query(User).filter(User.id == assignee_id).first()
            if not assignee:
                raise ResourceNotFound(message=f"用户ID {assignee_id} 不存在")
            
            # 验证操作用户是否存在
            user_id = data["user_id"]
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 更新指派人
            old_assignee_id = issue.assignee_id
            issue.assignee_id = assignee_id
            issue.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(issue)
            
            # 添加历史记录
            from app.models.issue_history import IssueHistory
            history = IssueHistory(
                issue_id=issue_id,
                action="update",
                field="assignee",
                old_value=str(old_assignee_id) if old_assignee_id else None,
                new_value=str(assignee_id),
                user_id=user_id,
                created_at=datetime.utcnow()
            )
            
            self.db.add(history)
            self.db.commit()
            
            # 返回更新后的问题信息
            issue_dict = issue.to_dict()
            issue_dict["assignee"] = {
                "id": assignee.id,
                "username": assignee.username,
                "name": getattr(assignee, "name", None)
            }
            
            return issue_dict
        
        result = self._safe_query(_query, "指派代码检视问题失败")
        return self.standard_response(True, result, "问题指派成功")

    def get_issue_comments(self, issue_id: int) -> Dict[str, Any]:
        """
        获取问题评论列表
        
        Args:
            issue_id (int): 问题ID
            
        Returns:
            Dict[str, Any]: 标准响应，包含评论列表
        """
        def _query():
            # 验证问题是否存在
            issue = self.db.query(Issue).filter(Issue.id == issue_id).first()
            if not issue:
                raise ResourceNotFound(message=f"问题ID {issue_id} 不存在")
            
            # 获取评论
            comments = self.db.query(
                IssueComment, User.username, User.id.label("user_id")
            ).join(
                User, IssueComment.user_id == User.id
            ).filter(
                IssueComment.issue_id == issue_id
            ).order_by(
                IssueComment.created_at
            ).all()

            # 转换评论为字典列表
            comment_dicts = []
            for comment, username, user_id in comments:
                comment_dict = {
                    "id": comment.id,
                    "content": comment.content,
                    "user_id": user_id,
                    "username": username,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None
                }
                comment_dicts.append(comment_dict)
            
            return comment_dicts
        
        result = self._safe_query(_query, f"获取问题 {issue_id} 评论失败")
        return self.standard_response(True, result)

    def get_issue_statistics(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """
        获取代码检视问题统计信息
        
        Args:
            project_id (Optional[int]): 项目ID
            
        Returns:
            Dict[str, Any]: 标准响应，包含统计信息
        """
        def _query():
            # 构建基本查询
            query = self.db.query(Issue).filter(Issue.issue_type == "code_review")
        
            # 如果指定了项目，添加项目过滤
            if project_id:
                # 验证项目是否存在
                project = self.db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
                
                query = query.filter(Issue.project_id == project_id)
            
            # 统计总数
            total_count = query.count()
            
            # 按状态统计
            status_counts = {}
            statuses = ["open", "in_progress", "resolved", "verified", "closed", "reopened"]
            for status in statuses:
                count = query.filter(Issue.status == status).count()
                status_counts[status] = count
            
            # 按严重程度统计
            severity_counts = {}
            severities = ["critical", "high", "medium", "low"]
            for severity in severities:
                count = query.filter(Issue.severity == severity).count()
                severity_counts[severity] = count
            
            # 计算平均解决时间
            resolved_issues = query.filter(Issue.resolution_time != None).all()
            avg_resolution_time = 0
            if resolved_issues:
                total_time = sum(issue.resolution_time for issue in resolved_issues)
                avg_resolution_time = total_time / len(resolved_issues)
            
            # 返回统计结果
            return {
                "total_count": total_count,
                "status_counts": status_counts,
                "severity_counts": severity_counts,
                "avg_resolution_time": avg_resolution_time
            }
        
        result = self._safe_query(_query, "获取代码检视问题统计失败")
        return self.standard_response(True, result)

    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        统计满足条件的代码检视问题数量
        
        Args:
            filters (Dict[str, Any], optional): 过滤条件字典
                - project_id (int, optional): 项目ID
                - creator_id (int, optional): 创建者ID
                - assignee_id (int, optional): 指派人ID
                - status (str, optional): 问题状态
                - severity (str, optional): 严重程度
                - commit_id (int, optional): 提交ID
                
        Returns:
            int: 符合条件的问题数量
        """
        def _query():
            query = self.db.query(func.count(Issue.id))
            
            # 基础过滤 - 只统计代码检视问题
            query = query.filter(Issue.issue_type == "code_review")
            
            # 应用过滤条件
            if filters:
                if "project_id" in filters and filters["project_id"] is not None:
                    query = query.filter(Issue.project_id == filters["project_id"])
                    
                if "creator_id" in filters and filters["creator_id"] is not None:
                    query = query.filter(Issue.creator_id == filters["creator_id"])
                    
                if "assignee_id" in filters and filters["assignee_id"] is not None:
                    query = query.filter(Issue.assignee_id == filters["assignee_id"])
                    
                if "status" in filters and filters["status"] is not None:
                    query = query.filter(Issue.status == filters["status"])
                    
                if "severity" in filters and filters["severity"] is not None:
                    query = query.filter(Issue.severity == filters["severity"])
                    
                if "commit_id" in filters and filters["commit_id"] is not None:
                    query = query.filter(Issue.commit_id == filters["commit_id"])
            
            # 执行查询并返回结果
            count = query.scalar()
            return count or 0
        
        return self._safe_query(_query, "统计代码检视问题数量失败", 0)