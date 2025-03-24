"""
代码分析服务模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import os
import re
import json
import subprocess
from datetime import datetime
from sqlalchemy import func

from app.database import get_db
from app.config.logging_config import logger
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound
from app.services.base_service import BaseService
from app.models.analysis_result import AnalysisResult
from app.models.project import Project
from app.models.code_commit import CodeCommit

class CodeAnalysisService(BaseService[AnalysisResult]):
    """
    代码分析服务类，处理代码分析相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化代码分析服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
        
    def analyze_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析代码质量
        
        Args:
            data (Dict[str, Any]): 分析参数
                - project_id (int): 项目ID
                - commit_id (Optional[int]): 提交ID，如果不提供则使用最新提交
                - code_path (Optional[str]): 代码路径，如果不提供则使用整个项目
                - analysis_type (Optional[str]): 分析类型，默认为 code_quality
            
        Returns:
            Dict[str, Any]: 分析结果
            
        Raises:
            ResourceNotFound: 项目或提交不存在
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        # 验证必要参数
        if "project_id" not in data:
            raise BusinessError(message="缺少必要参数: project_id")
        
        project_id = data["project_id"]
        commit_id = data.get("commit_id")
        code_path = data.get("code_path")
        analysis_type = data.get("analysis_type", "code_quality")
        
        # 验证分析类型
        valid_analysis_types = ["code_quality", "security", "performance", "maintainability"]
        if analysis_type not in valid_analysis_types:
            raise BusinessError(message=f"无效的分析类型: {analysis_type}，有效值: {', '.join(valid_analysis_types)}")
        
        logger.info(f"开始分析代码: 项目ID {project_id}, 提交ID {commit_id}, 路径 {code_path}, 类型 {analysis_type}")
        
        def _query():
            # 获取项目信息
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 获取提交信息
            if commit_id:
                commit = self.db.query(CodeCommit).filter(CodeCommit.id == commit_id).first()
                if not commit:
                    raise ResourceNotFound(message=f"提交ID {commit_id} 不存在")
            else:
                # 获取最新提交
                commit = self.db.query(CodeCommit).filter(
                    CodeCommit.project_id == project_id
                ).order_by(CodeCommit.commit_time.desc()).first()
                
                if not commit:
                    raise BusinessError(message=f"项目ID {project_id} 没有任何提交")
            
            # 如果已经分析过，返回缓存结果
            existing_analysis = self.db.query(AnalysisResult).filter(
                AnalysisResult.project_id == project_id,
                AnalysisResult.commit_id == commit.id,
                AnalysisResult.analysis_type == analysis_type
            ).first()
            
            if existing_analysis and code_path is None:
                logger.info(f"使用缓存的分析结果: 项目ID {project_id}, 提交ID {commit.id}")
                return existing_analysis.to_dict()
            
            # 实际进行代码分析
            analysis_result = self._perform_code_analysis(project, commit, code_path)
            
            # 只有在分析整个项目时才缓存结果
            if code_path is None:
                # 计算各项得分
                code_quality_score = self._calculate_code_quality_score(analysis_result)
                complexity_score = self._calculate_complexity_score(analysis_result)
                maintainability_score = self._calculate_maintainability_score(analysis_result)
                security_score = self._calculate_security_score(analysis_result)
                
                if existing_analysis:
                    # 更新现有结果
                    existing_analysis.result_summary = analysis_result.get("summary", "")
                    existing_analysis.details = analysis_result
                    existing_analysis.code_quality_score = code_quality_score
                    existing_analysis.complexity_score = complexity_score
                    existing_analysis.maintainability_score = maintainability_score
                    existing_analysis.security_score = security_score
                    self.db.commit()
                else:
                    # 创建新结果
                    new_analysis = AnalysisResult(
                        project_id=project_id,
                        commit_id=commit.id,
                        analysis_type=analysis_type,
                        result_summary=analysis_result.get("summary", ""),
                        details=analysis_result,
                        code_quality_score=code_quality_score,
                        complexity_score=complexity_score,
                        maintainability_score=maintainability_score,
                        security_score=security_score,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(new_analysis)
                    self.db.commit()
            
            logger.info(f"代码分析完成: 项目ID {project_id}, 提交ID {commit.id}")
            return analysis_result
        
        return self._safe_query(_query, f"分析代码失败: 项目ID {project_id}", {"complexity": 0, "issues": []})
    
    def _perform_code_analysis(self, project: Project, commit: CodeCommit, code_path: Optional[str] = None) -> Dict[str, Any]:
        """
        执行实际的代码分析
        
        Args:
            project (Project): 项目对象
            commit (CodeCommit): 提交对象
            code_path (Optional[str]): 代码路径
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        logger.info(f"执行代码分析: 项目 {project.name}, 提交 {commit.commit_id}")
        
        try:
            # 这里实现实际的代码分析逻辑
            # 可以使用工具如pylint, flake8, eslint等
            result = {
                "complexity": self._calculate_complexity(project, commit, code_path),
                "issues": self._find_code_issues(project, commit, code_path),
                "statistics": self._gather_statistics(project, commit, code_path),
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            return result
        except Exception as e:
            logger.error(f"代码分析过程中发生错误: {str(e)}")
            # 返回基本结果
            return {
                "complexity": 0,
                "issues": [],
                "statistics": {
                    "files": 0,
                    "lines": 0,
                    "functions": 0,
                    "classes": 0
                },
                "error": str(e),
                "analyzed_at": datetime.utcnow().isoformat()
            }
    
    def _calculate_complexity(self, project: Project, commit: CodeCommit, code_path: Optional[str] = None) -> float:
        """
        计算代码复杂度
        
        Args:
            project (Project): 项目对象
            commit (CodeCommit): 提交对象
            code_path (Optional[str]): 代码路径
            
        Returns:
            float: 代码复杂度
        """
        # 这里是复杂度计算的示例实现
        # 实际项目中可以使用工具如radon, metrics等
        return 5.0  # 示例复杂度
    
    def _find_code_issues(self, project: Project, commit: CodeCommit, code_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查找代码问题
        
        Args:
            project (Project): 项目对象
            commit (CodeCommit): 提交对象
            code_path (Optional[str]): 代码路径
            
        Returns:
            List[Dict[str, Any]]: 代码问题列表
        """
        # 这里是代码问题查找的示例实现
        # 实际项目中可以使用工具如pylint, flake8, eslint等
        return [
            {
                "file": "example.py",
                "line": 10,
                "message": "变量名过短",
                "severity": "warning",
                "rule": "naming-convention"
            }
        ]
    
    def _gather_statistics(self, project: Project, commit: CodeCommit, code_path: Optional[str] = None) -> Dict[str, int]:
        """
        收集代码统计数据
        
        Args:
            project (Project): 项目对象
            commit (CodeCommit): 提交对象
            code_path (Optional[str]): 代码路径
            
        Returns:
            Dict[str, int]: 统计数据
        """
        # 这里是代码统计的示例实现
        # 实际项目中可以使用工具如cloc, scc等
        return {
            "files": 10,
            "lines": 500,
            "functions": 20,
            "classes": 5
        }
    
    def get_analysis_history(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        获取项目的分析历史
        
        Args:
            data (Dict[str, Any]): 查询参数
                - project_id (int): 项目ID
                - limit (Optional[int]): 返回的记录数量，默认10
                - offset (Optional[int]): 跳过的记录数量，默认0
                - analysis_type (Optional[str]): 分析类型筛选
                - start_date (Optional[str]): 开始日期，ISO格式 (YYYY-MM-DD)
                - end_date (Optional[str]): 结束日期，ISO格式 (YYYY-MM-DD)
            
        Returns:
            List[Dict[str, Any]]: 分析历史
            
        Raises:
            ResourceNotFound: 项目不存在
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        # 验证必要参数
        if "project_id" not in data:
            raise BusinessError(message="缺少必要参数: project_id")
        
        project_id = data["project_id"]
        limit = data.get("limit", 10)
        offset = data.get("offset", 0)
        analysis_type = data.get("analysis_type")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        
        # 验证分析类型
        if analysis_type:
            valid_analysis_types = ["code_quality", "security", "performance", "maintainability"]
            if analysis_type not in valid_analysis_types:
                raise BusinessError(message=f"无效的分析类型: {analysis_type}，有效值: {', '.join(valid_analysis_types)}")
        
        # 验证日期格式
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date)
            except ValueError:
                raise BusinessError(message="无效的开始日期格式，应为ISO格式 (YYYY-MM-DD)")
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date)
            except ValueError:
                raise BusinessError(message="无效的结束日期格式，应为ISO格式 (YYYY-MM-DD)")
        
        def _query():
            # 获取项目信息
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 构建查询
            query = self.db.query(AnalysisResult).join(
                CodeCommit, AnalysisResult.commit_id == CodeCommit.id
            ).filter(
                AnalysisResult.project_id == project_id
            )
            
            # 应用分析类型筛选
            if analysis_type:
                query = query.filter(AnalysisResult.analysis_type == analysis_type)
            
            # 应用日期筛选
            if start_date:
                query = query.filter(AnalysisResult.created_at >= start_date)
            
            if end_date:
                query = query.filter(AnalysisResult.created_at <= end_date)
            
            # 获取分析历史
            analyses = query.order_by(
                CodeCommit.commit_time.desc()
            ).offset(offset).limit(limit).all()
            
            # 获取总数
            total = query.count()
            
            # 格式化结果
            history = []
            for analysis in analyses:
                commit = self.db.query(CodeCommit).filter(CodeCommit.id == analysis.commit_id).first()
                if commit:
                    history.append({
                        **analysis.to_dict(),
                        'commit': {
                            'id': commit.id,
                            'commit_id': commit.commit_id,
                            'commit_message': commit.commit_message,
                            'commit_time': commit.commit_time.isoformat(),
                            'author': commit.author.username if commit.author else None
                        }
                    })
            
            return {
                "total": total,
                "offset": offset,
                "limit": limit,
                "items": history
            }
        
        return self._safe_query(_query, f"获取分析历史失败: 项目ID {project_id}", {"total": 0, "items": []})

    def _calculate_code_quality_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算代码质量得分"""
        # 实现代码质量得分计算逻辑
        return 0.0

    def _calculate_complexity_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算复杂度得分"""
        # 实现复杂度得分计算逻辑
        return 0.0

    def _calculate_maintainability_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算可维护性得分"""
        # 实现可维护性得分计算逻辑
        return 0.0

    def _calculate_security_score(self, analysis_result: Dict[str, Any]) -> float:
        """计算安全性得分"""
        # 实现安全性得分计算逻辑
        return 0.0

    def get_analysis_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取特定的分析结果
        
        Args:
            data (Dict[str, Any]): 查询参数
                - analysis_id (int): 分析结果ID
                - include_details (Optional[bool]): 是否包含详细信息，默认True
            
        Returns:
            Dict[str, Any]: 分析结果
            
        Raises:
            ResourceNotFound: 分析结果不存在
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        # 验证必要参数
        if "analysis_id" not in data:
            raise BusinessError(message="缺少必要参数: analysis_id")
        
        analysis_id = data["analysis_id"]
        include_details = data.get("include_details", True)
        
        def _query():
            analysis = self.db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
            if not analysis:
                raise ResourceNotFound(message=f"分析结果ID {analysis_id} 不存在")
            
            # 获取提交信息
            commit = self.db.query(CodeCommit).filter(CodeCommit.id == analysis.commit_id).first()
            
            # 获取项目信息
            project = self.db.query(Project).filter(Project.id == analysis.project_id).first()
            
            result = {
                "id": analysis.id,
                "project_id": analysis.project_id,
                "project_name": project.name if project else None,
                "analysis_type": analysis.analysis_type,
                "summary": analysis.result_summary,
                "code_quality_score": float(analysis.code_quality_score or 0),
                "complexity_score": float(analysis.complexity_score or 0),
                "maintainability_score": float(analysis.maintainability_score or 0),
                "security_score": float(analysis.security_score or 0),
                "created_at": analysis.created_at.isoformat()
            }
            
            # 添加提交信息
            if commit:
                result["commit"] = {
                    "id": commit.id,
                    "commit_id": commit.commit_id,
                    "commit_message": commit.commit_message,
                    "commit_time": commit.commit_time.isoformat(),
                    "author": commit.author.username if commit.author else None
                }
            
            # 如果需要详细信息，添加详细数据
            if include_details:
                result["details"] = analysis.details
            
            return result
        
        return self._safe_query(_query, f"获取分析结果失败: ID {analysis_id}", {})

    def get_project_analysis_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取项目的分析汇总信息
        
        Args:
            data (Dict[str, Any]): 查询参数
                - project_id (int): 项目ID
                - analysis_type (Optional[str]): 分析类型，默认所有类型
                - include_details (Optional[bool]): 是否包含详细数据，默认False
            
        Returns:
            Dict[str, Any]: 分析汇总信息
            
        Raises:
            ResourceNotFound: 项目不存在
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        # 验证必要参数
        if "project_id" not in data:
            raise BusinessError(message="缺少必要参数: project_id")
        
        project_id = data["project_id"]
        analysis_type = data.get("analysis_type")
        include_details = data.get("include_details", False)
        
        # 验证分析类型
        if analysis_type:
            valid_analysis_types = ["code_quality", "security", "performance", "maintainability"]
            if analysis_type not in valid_analysis_types:
                raise BusinessError(message=f"无效的分析类型: {analysis_type}，有效值: {', '.join(valid_analysis_types)}")
        
        def _query():
            # 验证项目存在
            project = self.db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ResourceNotFound(message=f"项目ID {project_id} 不存在")
            
            # 构建查询
            query = self.db.query(AnalysisResult).filter(
                AnalysisResult.project_id == project_id
            )
            
            # 应用分析类型筛选
            if analysis_type:
                query = query.filter(AnalysisResult.analysis_type == analysis_type)
            
            # 获取最新的分析结果
            latest_analysis = query.order_by(
                AnalysisResult.created_at.desc()
            ).first()
            
            if not latest_analysis:
                return {
                    "project_id": project_id,
                    "project_name": project.name,
                    "has_analysis": False,
                    "latest_analysis": None,
                    "average_scores": {
                        "code_quality": 0.0,
                        "complexity": 0.0,
                        "maintainability": 0.0,
                        "security": 0.0
                    }
                }
            
            # 计算平均得分
            avg_scores = self.db.query(
                func.avg(AnalysisResult.code_quality_score).label('avg_code_quality'),
                func.avg(AnalysisResult.complexity_score).label('avg_complexity'),
                func.avg(AnalysisResult.maintainability_score).label('avg_maintainability'),
                func.avg(AnalysisResult.security_score).label('avg_security')
            ).filter(
                AnalysisResult.project_id == project_id
            )
            
            # 应用分析类型筛选
            if analysis_type:
                avg_scores = avg_scores.filter(AnalysisResult.analysis_type == analysis_type)
            
            avg_scores = avg_scores.first()
            
            # 获取分析趋势（最近5次分析）
            trend_query = self.db.query(
                AnalysisResult.created_at,
                AnalysisResult.code_quality_score,
                AnalysisResult.complexity_score,
                AnalysisResult.maintainability_score,
                AnalysisResult.security_score
            ).filter(
                AnalysisResult.project_id == project_id
            )
            
            # 应用分析类型筛选
            if analysis_type:
                trend_query = trend_query.filter(AnalysisResult.analysis_type == analysis_type)
            
            trends = trend_query.order_by(
                AnalysisResult.created_at.desc()
            ).limit(5).all()
            
            trend_data = [{
                "date": t.created_at.isoformat(),
                "code_quality": float(t.code_quality_score or 0),
                "complexity": float(t.complexity_score or 0),
                "maintainability": float(t.maintainability_score or 0),
                "security": float(t.security_score or 0)
            } for t in trends]
            
            result = {
                "project_id": project_id,
                "project_name": project.name,
                "has_analysis": True,
                "latest_analysis": {
                    "id": latest_analysis.id,
                    "analysis_type": latest_analysis.analysis_type,
                    "summary": latest_analysis.result_summary,
                    "code_quality_score": float(latest_analysis.code_quality_score or 0),
                    "complexity_score": float(latest_analysis.complexity_score or 0),
                    "maintainability_score": float(latest_analysis.maintainability_score or 0),
                    "security_score": float(latest_analysis.security_score or 0),
                    "created_at": latest_analysis.created_at.isoformat()
                },
                "average_scores": {
                    "code_quality": float(avg_scores.avg_code_quality or 0),
                    "complexity": float(avg_scores.avg_complexity or 0),
                    "maintainability": float(avg_scores.avg_maintainability or 0),
                    "security": float(avg_scores.avg_security or 0)
                },
                "trends": trend_data
            }
            
            # 如果需要详细数据，添加详细信息
            if include_details:
                result["latest_analysis"]["details"] = latest_analysis.details
            
            return result
        
        return self._safe_query(_query, f"获取项目分析汇总失败: 项目ID {project_id}", {
            "project_id": project_id,
            "has_analysis": False,
            "latest_analysis": None,
            "average_scores": {
                "code_quality": 0.0,
                "complexity": 0.0,
                "maintainability": 0.0,
                "security": 0.0
            },
            "trends": []
        })

    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        统计满足条件的代码分析结果数量
        
        Args:
            filters (Dict[str, Any], optional): 过滤条件字典
                - project_id (int, optional): 项目ID
                - creator_id (int, optional): 创建者ID
                - analysis_type (str, optional): 分析类型
                - commit_id (int, optional): 提交ID
                - start_date (datetime, optional): 开始日期
                - end_date (datetime, optional): 结束日期
                
        Returns:
            int: 符合条件的分析结果数量
        """
        def _query():
            query = self.db.query(func.count(AnalysisResult.id))
            
            # 应用过滤条件
            if filters:
                if "project_id" in filters and filters["project_id"] is not None:
                    query = query.filter(AnalysisResult.project_id == filters["project_id"])
                #
                # if "creator_id" in filters and filters["creator_id"] is not None:
                #     query = query.filter(AnalysisResult.creator_id == filters["creator_id"])
                    
                if "analysis_type" in filters and filters["analysis_type"] is not None:
                    query = query.filter(AnalysisResult.analysis_type == filters["analysis_type"])
                    
                if "commit_id" in filters and filters["commit_id"] is not None:
                    query = query.filter(AnalysisResult.commit_id == filters["commit_id"])
                    
                if "start_date" in filters and filters["start_date"] is not None:
                    query = query.filter(AnalysisResult.created_at >= filters["start_date"])
                    
                if "end_date" in filters and filters["end_date"] is not None:
                    query = query.filter(AnalysisResult.created_at <= filters["end_date"])
            
            # 执行查询并返回结果
            count = query.scalar()
            return count or 0
        
        return self._safe_query(_query, "统计代码分析结果数量失败", 0)