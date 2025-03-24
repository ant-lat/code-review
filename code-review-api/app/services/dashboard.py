"""
仪表盘服务模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import func, case, text, select, desc, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Tuple, Optional, Union, Callable
import traceback

from app.config.logging_config import logger
from app.models import Issue, User, Project, CodeCommit, IssueComment
from app.core.exceptions import DatabaseError, ResourceNotFound
from app.schemas.dashboard import (
    StatusDistribution,
    TypeDistribution,
    TeamWorkload,
    ProjectIssueDistribution,
    TrendAnalysis,
    TrendPoint
)
from app.services.base_service import BaseService

class DashboardService(BaseService):
    """
    仪表盘服务类，处理仪表盘相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化仪表盘服务
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
        self.dialect_name = self.db.bind.dialect.name if self.db.bind else "unknown"

    def _get_dialect_specific_diff_function(self, start_date, end_date):
        """
        根据数据库类型获取特定的时间差计算函数
        
        Args:
            start_date: 开始时间字段
            end_date: 结束时间字段
            
        Returns:
            时间差计算函数
        """
        if self.dialect_name == 'postgresql':
            return func.date_part('epoch', end_date - start_date)
        elif self.dialect_name == 'oracle':
            return func.extract('second', end_date - start_date)
        else:  # MySQL和其他
            return func.timestampdiff(text('SECOND'), start_date, end_date)

    def _get_date_trunc_function(self, interval, date_field):
        """
        根据数据库类型获取特定的日期截断函数
        
        Args:
            interval: 时间间隔 (day/week/month)
            date_field: 日期字段
            
        Returns:
            日期截断函数
        """
        if self.dialect_name == 'postgresql':
            return func.date_trunc(interval, date_field).label('date')
        elif self.dialect_name == 'mysql':
            if interval == 'day':
                return func.date(date_field).label('date')
            elif interval == 'week':
                return func.date(func.subdate(date_field, func.weekday(date_field))).label('date')
            elif interval == 'month':
                return func.date_format(date_field, '%Y-%m-01').label('date')
        elif self.dialect_name == 'sqlite':
            if interval == 'day':
                return func.date(date_field).label('date')
            elif interval == 'week':
                return func.date(date_field, 'weekday 0', '-' + func.strftime('%w', date_field) + ' days').label('date')
            elif interval == 'month':
                return func.date(date_field, 'start of month').label('date')
        elif self.dialect_name == 'oracle':
            if interval == 'day':
                return func.trunc(date_field, 'DD').label('date')
            elif interval == 'week':
                return func.trunc(date_field, 'IW').label('date')
            elif interval == 'month':
                return func.trunc(date_field, 'MM').label('date')
        else:
            # 默认使用日期转换为字符串然后截断
            if interval == 'day':
                return func.cast(func.date(date_field), String).label('date')
            elif interval == 'week' or interval == 'month':
                return func.cast(func.date(date_field), String).label('date')

    def get_status_distribution(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[StatusDistribution]:
        """
        获取问题状态分布
        
        Args:
            start_date (Optional[datetime]): 开始日期
            end_date (Optional[datetime]): 结束日期
            
        Returns:
            List[StatusDistribution]: 状态分布列表
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info("开始查询问题状态分布")
        
        def _query():
            query = (
                self.db.query(
                    Issue.status,
                    func.count(Issue.id).label('count')
                )
            )
            
            # 添加日期过滤条件
            if start_date:
                query = query.filter(Issue.created_at >= start_date)
            if end_date:
                query = query.filter(Issue.created_at <= end_date)
            
            # 分组并执行查询
            query = query.group_by(Issue.status)
            
            result = [
                StatusDistribution(status=row.status, count=row.count)
                for row in query.all()
            ]
            logger.info(f"状态分布查询完成，结果数量：{len(result)}")
            return result
            
        return self._safe_query(_query, "获取问题状态分布失败", [])

    def get_type_distribution(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[TypeDistribution]:
        """
        获取问题类型分布
        
        Args:
            start_date (Optional[datetime]): 开始日期
            end_date (Optional[datetime]): 结束日期
            
        Returns:
            List[TypeDistribution]: 类型分布列表
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info("开始查询问题类型分布")
        
        def _query():
            query = (
                self.db.query(
                    Issue.issue_type,
                    func.count(Issue.id).label('count')
                )
            )
            
            # 添加日期过滤条件
            if start_date:
                query = query.filter(Issue.created_at >= start_date)
            if end_date:
                query = query.filter(Issue.created_at <= end_date)
            
            # 分组并执行查询
            query = query.group_by(Issue.issue_type)
            
            result = [
                TypeDistribution(issue_type=row.issue_type, count=row.count)
                for row in query.all()
            ]
            logger.info(f"类型分布查询完成，结果类型数：{len(result)}")
            return result
            
        return self._safe_query(_query, "获取问题类型分布失败", [])

    def calculate_resolution_time(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> float:
        """
        计算平均解决时间（小时）
        
        Args:
            start_date (Optional[datetime]): 开始日期
            end_date (Optional[datetime]): 结束日期
            
        Returns:
            float: 平均解决时间
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info("开始计算平均解决时效")
        
        def _query():
            # 使用已解决的问题计算平均解决时间
            diff_function = self._get_dialect_specific_diff_function(
                Issue.created_at,
                Issue.resolved_at
            )
            
            query = (
                self.db.query(
                    func.coalesce(
                        func.avg(
                            case(
                                (Issue.status == 'closed', diff_function),  # 将条件和结果作为位置参数传递
                                else_=None
                            )
                        ),
                        0
                    ).label('avg_seconds')
                )
                .filter(Issue.resolved_at.isnot(None))
            )
            
            # 添加日期过滤条件
            if start_date:
                query = query.filter(Issue.created_at >= start_date)
            if end_date:
                query = query.filter(Issue.created_at <= end_date)
            
            resolution_time = query.scalar()
            
            # 转换为小时
            hours = round(resolution_time / 3600, 2) if resolution_time else 0
            logger.info(f"解决时效计算完成，平均时间：{hours}小时")
            return hours
            
        return self._safe_query(_query, "计算平均解决时效失败", 0.0)

    def get_team_workload(self, date_filters: Optional[dict] = None) -> List[TeamWorkload]:
        """
        获取团队工作负载
        
        Args:
            date_filters (Optional[dict]): 日期过滤条件，支持start_date和end_date参数
            
        Returns:
            List[TeamWorkload]: 团队工作负载列表
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info("开始查询团队负载")
        
        def _query():
            # 解析日期过滤条件
            start_date = None
            end_date = None
            if date_filters:
                start_date = date_filters.get('start_date')
                end_date = date_filters.get('end_date')
            
            # 构建基础查询
            query = (
                self.db.query(
                    User.username,
                    func.count(Issue.id).label('open_count')
                )
                .join(Issue, Issue.assignee_id == User.id)
                .filter(Issue.status != 'closed')
            )
            
            # 添加日期过滤条件
            if start_date:
                query = query.filter(Issue.created_at >= start_date)
            if end_date:
                query = query.filter(Issue.created_at <= end_date)
            
            # 分组并排序
            query = query.group_by(User.username).order_by(desc('open_count'))
            
            result = [
                TeamWorkload(username=row.username, open_count=row.open_count)
                for row in query.all()
            ]
            logger.info(f"团队负载查询完成，涉及用户数：{len(result)}")
            return result
            
        return self._safe_query(_query, "获取团队工作负载失败", [])

    def get_project_distribution(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[ProjectIssueDistribution]:
        """
        获取项目问题分布
        
        Args:
            start_date (Optional[date]): 开始日期
            end_date (Optional[date]): 结束日期
            
        Returns:
            List[ProjectIssueDistribution]: 项目问题分布列表
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info("开始查询项目问题分布")
        
        def _query():
            query = (
                self.db.query(
                    Project.name.label('project_name'),
                    func.coalesce(func.count(Issue.id), 0).label('total_issues')
                )
                .outerjoin(Issue, and_(Issue.project_id == Project.id, Issue.created_at >= start_date,
                                       Issue.created_at <= end_date))
                .group_by(Project.name)
                .order_by(desc('total_issues'))  # 按问题数量降序排序
            )
            result = [
                ProjectIssueDistribution(project_name=row.project_name, total_issues=row.total_issues)
                for row in query.all()
            ]
            logger.info(f"项目问题分布查询完成，涉及项目数：{len(result)}")
            return result
            
        return self._safe_query(_query, "获取项目问题分布失败", [])

    def get_trend_analysis(self, days: int = 30, interval: str = 'day', start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> TrendAnalysis:
        """
        获取问题趋势分析
        
        Args:
            days (int): 分析的天数，默认30天
            interval (str): 统计间隔 (day/week/month)
            start_date (Optional[datetime]): 开始日期，如果提供将覆盖days参数
            end_date (Optional[datetime]): 结束日期，如果提供将覆盖days参数
            
        Returns:
            TrendAnalysis: 趋势分析数据
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info(f"开始查询问题趋势，分析天数: {days}, 间隔: {interval}")
        
        def _query():
            # 确定日期范围
            if end_date is None:
                end_date_value = datetime.utcnow() + timedelta(days=1)  # 延长一天以确保包含当天创建的所有问题
            else:
                end_date_value = end_date
            
            if start_date is None:
                start_date_value = end_date_value - timedelta(days=days)
            else:
                start_date_value = start_date
            
            logger.info(f"趋势分析日期范围: {start_date_value.strftime('%Y-%m-%d')} 至 {end_date_value.strftime('%Y-%m-%d')}")
            
            # 按日期统计新增问题数
            new_issues_query = (
                self.db.query(
                    func.date(Issue.created_at).label('date'),
                    func.count(Issue.id).label('count')
                )
                .filter(Issue.created_at >= start_date_value)
                .filter(Issue.created_at <= end_date_value)
                .group_by(func.date(Issue.created_at))
            )
            
            # 按日期统计解决问题数
            resolved_issues_query = (
                self.db.query(
                    func.date(Issue.resolved_at).label('date'),
                    func.count(Issue.id).label('count')
                )
                .filter(Issue.resolved_at >= start_date_value)
                .filter(Issue.resolved_at <= end_date_value)
                .filter(Issue.resolved_at.isnot(None))
                .group_by(func.date(Issue.resolved_at))
            )
            
            # 转换为字典以便查找
            new_issues = {
                row.date: row.count
                for row in new_issues_query.all()
            }
            resolved_issues = {
                row.date: row.count
                for row in resolved_issues_query.all()
            }
            
            # 生成日期序列
            current_date = start_date_value
            trend_points = []
            while current_date <= end_date_value:
                date_str = current_date.date()
                point = TrendPoint(
                    date=date_str,
                    new_issues=new_issues.get(date_str, 0),
                    resolved_issues=resolved_issues.get(date_str, 0)
                )
                trend_points.append(point)
                current_date += timedelta(days=1)
            
            logger.info(f"问题趋势查询完成，分析天数：{len(trend_points)}")
            return TrendAnalysis(points=trend_points)
            
        return self._safe_query(_query, "获取问题趋势分析失败", TrendAnalysis(points=[]))
    
    def get_user_performance_stats(self, user_id: Optional[int] = None, date_filters: Optional[dict] = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        获取用户性能统计
        
        Args:
            user_id (Optional[int]): 用户ID，如果为None则获取所有用户
            date_filters (Optional[dict]): 日期过滤条件，支持start_date和end_date参数
            
        Returns:
            Dict[str, Any] 或 List[Dict[str, Any]]: 用户性能统计信息
            
        Raises:
            DatabaseError: 数据库操作错误
            ResourceNotFound: 用户不存在
        """
        date_info = ""
        if date_filters:
            start_date = date_filters.get('start_date')
            end_date = date_filters.get('end_date')
            if start_date and end_date:
                date_info = f", 日期范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
        
        logger.info(f"开始查询用户性能统计，用户ID: {user_id if user_id else '所有'}{date_info}")
        
        def _query():
            # 获取日期过滤条件
            start_date = None
            end_date = None
            if date_filters:
                start_date = date_filters.get('start_date')
                end_date = date_filters.get('end_date')
            
            # 检查用户是否存在
            if user_id:
                user = self.db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 构建基础查询
            base_query = self.db.query(User)
            
            if user_id:
                base_query = base_query.filter(User.id == user_id)
            
            # 获取用户基本信息
            users = base_query.all()
            
            # 收集统计数据
            result = []
            for user in users:
                # 构建基础过滤条件
                issue_filters = []
                if start_date:
                    issue_filters.append(Issue.created_at >= start_date)
                if end_date:
                    issue_filters.append(Issue.created_at <= end_date)
                
                # 已解决的问题数
                resolved_issues_query = (
                    self.db.query(func.count(Issue.id))
                    .filter(Issue.assignee_id == user.id)
                    .filter(Issue.status == 'closed')
                )
                if issue_filters:
                    for condition in issue_filters:
                        resolved_issues_query = resolved_issues_query.filter(condition)
                resolved_issues = resolved_issues_query.scalar() or 0
                
                # 待解决的问题数
                pending_issues_query = (
                    self.db.query(func.count(Issue.id))
                    .filter(Issue.assignee_id == user.id)
                    .filter(Issue.status != 'closed')
                )
                if issue_filters:
                    for condition in issue_filters:
                        pending_issues_query = pending_issues_query.filter(condition)
                pending_issues = pending_issues_query.scalar() or 0
                
                # 评论数
                comment_query = (
                    self.db.query(func.count(IssueComment.id))
                    .filter(IssueComment.user_id == user.id)
                )
                if start_date:
                    comment_query = comment_query.filter(IssueComment.created_at >= start_date)
                if end_date:
                    comment_query = comment_query.filter(IssueComment.created_at <= end_date)
                comment_count = comment_query.scalar() or 0
                
                # 提交数
                commit_query = (
                    self.db.query(func.count(CodeCommit.id))
                    .filter(CodeCommit.author_id == user.id)
                )
                if start_date:
                    commit_query = commit_query.filter(CodeCommit.commit_time >= start_date)
                if end_date:
                    commit_query = commit_query.filter(CodeCommit.commit_time <= end_date)
                commit_count = commit_query.scalar() or 0
                
                # 平均解决时间
                if resolved_issues > 0:
                    diff_function = self._get_dialect_specific_diff_function(
                        Issue.created_at,
                        Issue.resolved_at
                    )
                    
                    avg_resolution_query = (
                        self.db.query(
                            func.avg(diff_function).label('avg_seconds')
                        )
                        .filter(Issue.assignee_id == user.id)
                        .filter(Issue.status == 'closed')
                        .filter(Issue.resolved_at.isnot(None))
                    )
                    if issue_filters:
                        for condition in issue_filters:
                            avg_resolution_query = avg_resolution_query.filter(condition)
                    avg_resolution_time = avg_resolution_query.scalar() or 0
                    
                    # 转换为小时
                    avg_resolution_hours = round(avg_resolution_time / 3600, 2)
                else:
                    avg_resolution_hours = 0
                
                # 添加统计结果
                user_stats = {
                    "user_id": user.id,
                    "username": user.username,
                    "resolved_issues": resolved_issues,
                    "pending_issues": pending_issues,
                    "comment_count": comment_count,
                    "commit_count": commit_count,
                    "avg_resolution_time": avg_resolution_hours,
                    "total_issues": resolved_issues + pending_issues,
                    "resolution_rate": round(resolved_issues / (resolved_issues + pending_issues) * 100, 2) if (resolved_issues + pending_issues) > 0 else 0
                }
                
                result.append(user_stats)
            
            # 如果是单个用户查询，返回单个结果
            if user_id and result:
                logger.info(f"用户性能统计查询完成，用户ID: {user_id}")
                return result[0]
            
            # 排序结果 - 按解决问题总数降序
            result.sort(key=lambda x: x["resolved_issues"], reverse=True)
            
            logger.info(f"用户性能统计查询完成，用户数: {len(result)}")
            return result
        
        return self._safe_query(_query, f"获取用户性能统计失败: 用户ID {user_id if user_id else '所有'}", [] if not user_id else {})
        
    def get_dashboard_stats(self, **date_filters) -> Dict[str, Any]:
        """
        获取仪表盘所有统计数据
        
        Args:
            date_filters: 日期过滤条件，支持start_date和end_date参数
            
        Returns:
            Dict[str, Any]: 仪表盘统计数据
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info(f"开始获取仪表盘统计数据，日期过滤: {date_filters}")
        try:
            # 应用日期过滤
            start_date = date_filters.get('start_date')
            end_date = date_filters.get('end_date')
            
            # 获取所有统计数据并应用日期过滤
            status_distribution = self.get_status_distribution(start_date=start_date, end_date=end_date)
            type_distribution = self.get_type_distribution(start_date=start_date, end_date=end_date)
            avg_resolution_time = self.calculate_resolution_time(start_date=start_date, end_date=end_date)
            team_workload = self.get_team_workload(date_filters=date_filters)
            project_distribution = self.get_project_distribution(start_date=start_date, end_date=end_date)
            fix_rate_trend = self.get_fix_rate_trend(start_date=start_date, end_date=end_date)
            
            # 如果有日期过滤，则趋势分析也使用对应的天数范围
            days = 30  # 默认30天
            if start_date and end_date:
                # 计算日期范围天数
                delta = end_date - start_date
                days = max(delta.days, 1)  # 至少为1天
            
            trend_analysis = self.get_trend_analysis(days=days, start_date=start_date, end_date=end_date)
            
            # 获取总体统计
            total_issues = sum(item.count for item in status_distribution)
            open_issues = sum(item.count for item in status_distribution if item.status != 'closed')
            total_projects = len(project_distribution)
            total_users = len(team_workload)
            
            # 构建统计结果
            stats = {
                "status_distribution": status_distribution,
                "type_distribution": type_distribution,
                "avg_resolution_time": avg_resolution_time,
                "team_workload": team_workload,
                "project_issue_distribution": project_distribution,
                "trend_analysis": trend_analysis,
                "fix_rate_trend": fix_rate_trend,
                "summary": {
                    "total_issues": total_issues,
                    "open_issues": open_issues,
                    "closed_issues": total_issues - open_issues,
                    "total_projects": total_projects,
                    "total_active_users": total_users,
                    "completion_rate": round((total_issues - open_issues) / total_issues * 100, 2) if total_issues > 0 else 0
                }
            }
            
            logger.info("仪表盘统计数据获取完成")
            return stats
        except Exception as e:
            logger.error(f"获取仪表盘统计数据失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise DatabaseError(message="获取仪表盘统计数据失败", detail=str(e))

    def get_fix_rate_trend(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        获取问题修复率随时间的变化趋势
        
        Args:
            start_date (Optional[datetime]): 开始日期
            end_date (Optional[datetime]): 结束日期
            
        Returns:
            List[Dict[str, Any]]: 修复率趋势数据，包含日期、新增问题数、解决问题数和修复率
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info("开始查询问题修复率趋势")
        
        def _query():
            # 如果没有提供日期范围，使用过去30天
            if not start_date:
                calc_start_date = datetime.now() - timedelta(days=30)
            else:
                calc_start_date = start_date
                
            if not end_date:
                calc_end_date = datetime.now()
            else:
                calc_end_date = end_date
                
            # 计算日期范围天数
            delta = calc_end_date - calc_start_date
            period_days = max(delta.days, 1)
            
            # 根据日期范围选择合适的时间间隔
            if period_days <= 14:
                # 小于两周，按天统计
                interval = 'day'
                format_str = '%Y-%m-%d'
                delta_func = lambda date, i: date + timedelta(days=i)
            elif period_days <= 90:
                # 小于3个月，按周统计
                interval = 'week'
                format_str = '%Y-W%W'
                delta_func = lambda date, i: date + timedelta(weeks=i)
            else:
                # 大于3个月，按月统计
                interval = 'month'
                format_str = '%Y-%m'
                delta_func = lambda date, i: date.replace(month=((date.month - 1 + i) % 12) + 1,
                                                          year=date.year + ((date.month - 1 + i) // 12))
            
            # 获取适合当前数据库的日期截断函数
            sql_date_format = self._get_date_trunc_function(interval, Issue.created_at)
            sql_resolve_date_format = self._get_date_trunc_function(interval, Issue.resolved_at)
            
            try:
                # 查询每个时间间隔内的新增问题数
                created_issues_query = (
                    self.db.query(
                        sql_date_format,
                        func.count(Issue.id).label('count')
                    )
                )
                
                # 添加日期过滤
                if calc_start_date and calc_end_date:
                    created_issues_query = created_issues_query.filter(Issue.created_at >= calc_start_date, 
                                                                       Issue.created_at <= calc_end_date)
                
                created_issues = created_issues_query.group_by(sql_date_format).all()
                
                # 查询每个时间间隔内解决的问题数
                resolved_issues_query = (
                    self.db.query(
                        sql_resolve_date_format,
                        func.count(Issue.id).label('count')
                    )
                )
                
                # 添加日期过滤并确保resolved_at不为空
                if calc_start_date and calc_end_date:
                    resolved_issues_query = resolved_issues_query.filter(Issue.resolved_at >= calc_start_date, 
                                                                         Issue.resolved_at <= calc_end_date)
                
                resolved_issues_query = resolved_issues_query.filter(Issue.resolved_at.isnot(None))
                resolved_issues = resolved_issues_query.group_by(sql_resolve_date_format).all()
                
                # 将查询结果转换为字典，方便查找
                created_dict = {}
                for row in created_issues:
                    if hasattr(row, 'date') and row.date:
                        date_key = row.date.strftime(format_str) if isinstance(row.date, datetime) else str(row.date)
                        created_dict[date_key] = row.count
                
                resolved_dict = {}
                for row in resolved_issues:
                    if hasattr(row, 'date') and row.date:
                        date_key = row.date.strftime(format_str) if isinstance(row.date, datetime) else str(row.date)
                        resolved_dict[date_key] = row.count
                
                # 生成时间间隔列表
                date_periods = []
                current_date = calc_start_date
                
                if interval == 'day':
                    while current_date <= calc_end_date:
                        date_str = current_date.strftime(format_str)
                        date_periods.append(date_str)
                        current_date += timedelta(days=1)
                elif interval == 'week':
                    while current_date <= calc_end_date:
                        date_str = current_date.strftime(format_str)
                        date_periods.append(date_str)
                        current_date += timedelta(weeks=1)
                else:  # month
                    while current_date <= calc_end_date:
                        date_str = current_date.strftime(format_str)
                        date_periods.append(date_str)
                        if current_date.month == 12:
                            current_date = current_date.replace(year=current_date.year + 1, month=1)
                        else:
                            current_date = current_date.replace(month=current_date.month + 1)
                
                # 计算每个时间间隔的修复率
                result = []
                for date_str in date_periods:
                    created = created_dict.get(date_str, 0)
                    resolved = resolved_dict.get(date_str, 0)
                    fix_rate = round(resolved / created * 100, 2) if created > 0 else 0
                    
                    result.append({
                        "date": date_str,
                        "created": created,
                        "resolved": resolved,
                        "fix_rate": fix_rate,
                        "interval": interval
                    })
                
                logger.info(f"问题修复率趋势查询完成，数据点数量: {len(result)}")
                return result
            except Exception as e:
                logger.error(f"查询修复率趋势时发生错误: {e}")
                logger.debug(traceback.format_exc())
                raise DatabaseError(message="查询修复率趋势失败", detail=str(e))
            
        return self._safe_query(_query, "获取问题修复率趋势失败", [])

    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近活动

        Args:
            limit (int): 返回结果数量限制

        Returns:
            List[Dict[str, Any]]: 最近活动列表

        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info(f"开始查询最近活动，限制数量: {limit}")

        def _query():
            # 获取最近的代码提交
            recent_commits = (
                self.db.query(
                    CodeCommit.id,
                    CodeCommit.commit_message,
                    CodeCommit.commit_time,
                    User.username.label('author'),
                    Project.name.label('project_name')
                )
                .join(User, User.id == CodeCommit.author_id)
                .join(Project, Project.id == CodeCommit.project_id)
                .order_by(desc(CodeCommit.commit_time))
                .limit(limit)
                .all()
            )

            # 获取最近的问题变更
            recent_issues = (
                self.db.query(
                    Issue.id,
                    Issue.title,
                    Issue.status,
                    Issue.updated_at,
                    User.username.label('reporter'),
                    Project.name.label('project_name')
                )
                .join(Project, Project.id == Issue.project_id)
                .order_by(desc(Issue.updated_at))
                .limit(limit)
                .all()
            )

            # 获取最近的评论
            recent_comments = (
                self.db.query(
                    IssueComment.id,
                    IssueComment.issue_id,
                    IssueComment.created_at,
                    User.username.label('commenter'),
                    Issue.title.label('issue_title'),
                    Project.name.label('project_name')
                )
                .join(User, User.id == IssueComment.user_id)
                .join(Issue, Issue.id == IssueComment.issue_id)
                .join(Project, Project.id == Issue.project_id)
                .order_by(desc(IssueComment.created_at))
                .limit(limit)
                .all()
            )

            activities = []

            for commit in recent_commits:
                activities.append({
                    "id": f"commit-{commit.id}",
                    "type": "commit",
                    "title": "代码提交",
                    "message": commit.issue_title,
                    "time": commit.created_at,
                    "user": commit.commenter,
                    "project": commit.project_name
                })

            for issue in recent_issues:
                activities.append({
                    "id": f"issue-{issue.id}",
                    "type": "issue",
                    "title": "问题更新",
                    "message": f"{issue.title} ({issue.status})",
                    "time": issue.updated_at,
                    "user": issue.reporter,
                    "project": issue.project_name
                })

            for comment in recent_comments:
                activities.append({
                    "id": f"comment-{comment.id}",
                    "type": "comment",
                    "title": "评论添加",
                    "message": f"评论了问题: {comment.issue_title}",
                    "time": comment.created_at,
                    "user": comment.commenter,
                    "project": comment.project_name
                })

            # 按时间排序并限制数量
            activities.sort(key=lambda x: x["time"], reverse=True)
            result = activities[:limit]

            logger.info(f"最近活动查询完成，结果数量：{len(result)}")
            return result

        return self._safe_query(_query, "获取最近活动失败", [])

    def get_filtered_recent_activity(self, limit: int = 10, activity_type: Optional[str] = None) -> List[
        Dict[str, Any]]:
        """
        获取最近活动并进行过滤

        Args:
            limit (int): 返回结果数量限制
            activity_type (Optional[str]): 活动类型过滤

        Returns:
            List[Dict[str, Any]]: 最近活动列表

        Raises:
            DatabaseError: 数据库操作错误
        """
        logger.info(f"开始查询最近活动，限制数量: {limit}, 活动类型: {activity_type}")

        def _query():
            all_activities = self.get_recent_activity(limit)

            # 过滤活动类型
            filtered_activities = all_activities
            if activity_type:
                filtered_activities = [activity for activity in all_activities if activity['type'] == activity_type]

            logger.info(f"过滤后最近活动数量：{len(filtered_activities)}")
            return filtered_activities

        return self._safe_query(_query, "获取最近活动失败", [])
