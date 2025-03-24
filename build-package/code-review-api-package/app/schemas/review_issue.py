from enum import Enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Dict, List, Optional, Union

class SeverityLevel(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'
    critical = 'critical'

class PriorityLevel(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'

class IssueStatus(str, Enum):
    open = 'open'
    in_progress = 'in_progress'
    resolved = 'resolved'
    verified = 'verified'
    closed = 'closed'

class ReviewIssueBase(BaseModel):
    project_id: int
    commit_id: int
    title: str
    description: str
    severity: SeverityLevel
    priority: PriorityLevel
    status: IssueStatus = IssueStatus.open
    assignee_id: Optional[int] = None

class ReviewIssueCreate(ReviewIssueBase):
    pass

class ReviewIssue(ReviewIssueBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

from .StatsResponse import StatsResponse

# 删除原有模型定义