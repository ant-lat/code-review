"""
问题相关模型定义
@author: pgao
@date: 2024-03-13
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class IssueCreate(BaseModel):
    """问题创建请求模型"""
    project_id: int = Field(..., description="项目ID")
    title: str = Field(..., description="问题标题")
    description: str = Field(..., description="问题描述")
    priority: str = Field(..., description="优先级", examples=["high", "medium", "low"])
    issue_type: str = Field(..., description="问题类型", examples=["bug", "feature", "improvement", "code_review"])
    assignee_id: Optional[int] = Field(None, description="指派人ID")
    # 代码检视问题特有字段
    severity: Optional[str] = Field(None, description="严重程度", examples=["low", "medium", "high", "critical"])
    file_path: Optional[str] = Field(None, description="文件路径")
    line_start: Optional[int] = Field(None, description="起始行号")
    line_end: Optional[int] = Field(None, description="结束行号")
    commit_id: Optional[int] = Field(None, description="关联提交ID")

class StatusUpdate(BaseModel):
    """状态更新请求模型"""
    status: str = Field(..., description="新状态", examples=["open", "in_progress", "resolved", "verified", "closed"])
    comment: Optional[str] = Field(None, description="状态更新说明")
    
class IssueListItem(BaseModel):
    """问题列表项模型"""
    id: int = Field(..., description="问题ID")
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    title: str = Field(..., description="问题标题")
    status: str = Field(..., description="状态")
    priority: str = Field(..., description="优先级")
    issue_type: str = Field(..., description="问题类型")
    severity: Optional[str] = Field(None, description="严重程度")
    creator_id: int = Field(..., description="创建人ID")
    creator_name: str = Field(..., description="创建人姓名")
    assignee_id: Optional[int] = Field(None, description="指派人ID")
    assignee_name: Optional[str] = Field(None, description="指派人姓名")
    file_path: Optional[str] = Field(None, description="文件路径")
    line_start: Optional[int] = Field(None, description="起始行号")
    line_end: Optional[int] = Field(None, description="结束行号")
    resolution_time: Optional[float] = Field(None, description="解决时间(小时)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    
    class Config:
        from_attributes = True

class IssueDetail(BaseModel):
    """问题详情模型"""
    id: int = Field(..., description="问题ID")
    project_id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    commit_id: Optional[int] = Field(None, description="关联提交ID")
    title: str = Field(..., description="问题标题")
    description: str = Field(..., description="问题描述")
    status: str = Field(..., description="状态")
    priority: str = Field(..., description="优先级")
    issue_type: str = Field(..., description="问题类型")
    severity: Optional[str] = Field(None, description="严重程度")
    creator_id: int = Field(..., description="创建人ID")
    creator_name: str = Field(..., description="创建人姓名")
    assignee_id: Optional[int] = Field(None, description="指派人ID")
    assignee_name: Optional[str] = Field(None, description="指派人姓名")
    file_path: Optional[str] = Field(None, description="文件路径")
    line_start: Optional[int] = Field(None, description="起始行号")
    line_end: Optional[int] = Field(None, description="结束行号")
    resolution_time: Optional[float] = Field(None, description="解决时间(小时)")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    closed_at: Optional[datetime] = Field(None, description="关闭时间")
    comment_count: int = Field(0, description="评论数量")
    
    class Config:
        from_attributes = True

class CodeReviewIssueCreate(BaseModel):
    """代码检视问题创建请求模型"""
    project_id: int = Field(..., description="项目ID")
    commit_id: int = Field(..., description="提交ID")
    file_path: str = Field(..., description="文件路径")
    line_start: int = Field(..., description="起始行号")
    line_end: int = Field(..., description="结束行号")
    title: str = Field(..., description="问题标题")
    description: str = Field(..., description="问题描述")
    issue_type: str = Field(..., description="问题类型", examples=["code_review"])
    severity: str = Field("medium", description="严重程度", examples=["low", "medium", "high", "critical"])
    priority: str = Field("medium", description="优先级", examples=["low", "medium", "high"])
    assignee_id: Optional[int] = Field(None, description="指派人ID")

class IssueBatchUpdate(BaseModel):
    """问题批量更新请求模型"""
    issue_ids: List[int] = Field(..., description="问题ID列表")
    status: Optional[str] = Field(None, description="新状态", examples=["open", "in_progress", "resolved", "closed"])
    priority: Optional[str] = Field(None, description="新优先级", examples=["high", "medium", "low"])
    assignee_id: Optional[int] = Field(None, description="新指派人ID")
    project_id: Optional[int] = Field(None, description="所属项目ID")
    tags: Optional[List[int]] = Field(None, description="标签ID列表")