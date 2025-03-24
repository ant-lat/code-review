"""
统计响应相关的数据模型
@author: pgao
@date: 2024-03-13
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class StatusDistribution(BaseModel):
    """状态分布模型"""
    status: str
    count: int

class TypeDistribution(BaseModel):
    """类型分布模型"""
    issue_type: str
    count: int

class TeamWorkload(BaseModel):
    """团队工作负载模型"""
    username: str
    open_count: int

class ProjectIssueDistribution(BaseModel):
    """项目问题分布模型"""
    project_name: str
    total_issues: int

class RecentCommits(BaseModel):
    """最近提交模型"""
    commit_hash: str
    committed_at: str

class CiCdStatus(BaseModel):
    """CI/CD状态模型"""
    commit_id: str
    status: str
    executed_at: str

class StatsResponse(BaseModel):
    """统计响应模型"""
    status_distribution: List[StatusDistribution] = Field(default_factory=list)
    type_distribution: List[TypeDistribution] = Field(default_factory=list)
    avg_resolution_time: float = Field(default=0.0)
    team_workload: List[TeamWorkload] = Field(default_factory=list)
    project_issue_distribution: List[ProjectIssueDistribution] = Field(default_factory=list)