"""
仪表盘相关的数据模型
@author: pgao
@date: 2024-03-13
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import field_validator

class StatusDistribution(BaseModel):
    """
    问题状态分布模型
    """
    status: str
    count: int

class TypeDistribution(BaseModel):
    """
    问题类型分布模型
    """
    issue_type: str
    count: int

class TeamWorkload(BaseModel):
    """
    团队工作负载模型
    """
    username: str
    open_count: int
    in_progress_count: Optional[int] = None

class ProjectIssueDistribution(BaseModel):
    """
    项目问题分布模型
    """
    project_name: str
    total_issues: int

class TrendPoint(BaseModel):
    """
    趋势点模型
    """
    date: str
    new_issues: int
    resolved_issues: int

class TrendAnalysis(BaseModel):
    """
    趋势分析模型
    """
    points: List[TrendPoint]

class FixRatePoint(BaseModel):
    """修复率趋势点"""
    date: str
    created: int
    resolved: int
    fix_rate: float
    interval: str
    
class FixRateTrend(BaseModel):
    """修复率趋势分析"""
    points: List[FixRatePoint]

class DashboardStats(BaseModel):
    """
    仪表盘统计数据模型
    """
    status_distribution: List[StatusDistribution] = Field(default_factory=list())
    type_distribution: List[TypeDistribution] = Field(default_factory=list())
    average_resolution_time: float = Field(default=0.0)
    team_workload: List[TeamWorkload] = Field(default_factory=list())
    project_distribution: List[ProjectIssueDistribution] = Field(default_factory=list())
    trend_analysis: Optional[TrendAnalysis] = None

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class DashboardStatsResponse(BaseModel):
    """
    仪表盘统计响应模型
    """
    status_distribution: Optional[List[StatusDistribution]] = None
    type_distribution: Optional[List[TypeDistribution]] = None
    avg_resolution_time: Optional[float] = None
    team_workload: Optional[List[TeamWorkload]] = None
    project_issue_distribution: Optional[List[ProjectIssueDistribution]] = None
    trend_analysis: Optional[TrendAnalysis] = None
    fix_rate_trend: Optional[List[FixRatePoint]] = None
    summary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }
