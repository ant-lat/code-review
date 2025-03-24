"""
问题模型模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base
from app.models.issue_history import IssueHistory

class Issue(Base):
    """
    问题模型 - 合并了普通问题和代码检视问题功能
    
    Attributes:
        id (int): 问题ID
        project_id (int): 关联项目ID
        commit_id (int): 关联提交ID
        title (str): 问题标题
        description (str): 问题描述
        status (str): 问题状态
        priority (str): 问题优先级
        issue_type (str): 问题类型
        severity (str): 严重程度，用于代码检视问题
        creator_id (int): 创建者ID
        assignee_id (int): 分配者ID
        file_path (str): 文件路径
        line_start (int): 起始行号
        line_end (int): 结束行号
        resolution_time (float): 解决时间(小时)
        created_at (datetime): 创建时间
        updated_at (datetime): 更新时间
        closed_at (datetime): 关闭时间
        resolved_at (datetime): 解决时间
    """
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="问题ID")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, comment="关联项目ID")
    commit_id = Column(Integer, ForeignKey("code_commits.id", ondelete="SET NULL"), nullable=True, comment="关联提交ID")
    title = Column(String(255), nullable=False, comment="问题标题")
    description = Column(Text, nullable=True, comment="问题描述")
    status = Column(String(50), nullable=False, default="open", comment="问题状态")
    priority = Column(String(50), nullable=False, default="medium", comment="问题优先级")
    issue_type = Column(String(50), nullable=False, default="bug", comment="问题类型")
    severity = Column(String(20), nullable=True, default="medium", comment="严重程度（代码检视问题特有）")
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="创建者ID")
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="指派人ID")
    file_path = Column(String(255), nullable=True, comment="文件路径")
    line_start = Column(Integer, nullable=True, comment="起始行号")
    line_end = Column(Integer, nullable=True, comment="结束行号")
    resolution_time = Column(Float, nullable=True, comment="解决时间(小时)")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    closed_at = Column(DateTime, nullable=True, comment="关闭时间")
    resolved_at = Column(DateTime, nullable=True, comment="解决时间")
    
    # 状态约束
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'resolved', 'verified', 'closed', 'reopened','rejected')",
            name="check_issue_status"
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'critical')",
            name="check_issue_priority"
        ),
        CheckConstraint(
            "issue_type IN ('bug', 'feature', 'improvement', 'task', 'security', 'code_review')",
            name="check_issue_type"
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="check_issue_severity"
        ),
        {'comment': '问题跟踪表，包含一般问题和代码检视问题'}
    )
    
    # 关系
    project = relationship("Project", back_populates="issues")
    commit = relationship("CodeCommit", back_populates="issues")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_issues")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_issues")
    comments = relationship("IssueComment", back_populates="issue", cascade="all, delete-orphan")
    history = relationship("IssueHistory", back_populates="issue", cascade="all, delete-orphan")
    
    def to_dict(self) -> dict:
        """
        将模型转换为字典
        
        Returns:
            dict: 字典表示
        """
        return {
            "id": self.id,
            "project_id": self.project_id,
            "commit_id": self.commit_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "creator_id": self.creator_id,
            "creator_name": self.creator.username if self.creator else None,
            "assignee_id": self.assignee_id,
            "assignee_name": self.assignee.username if self.assignee else None,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "resolution_time": self.resolution_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __repr__(self) -> str:
        """
        字符串表示
        
        Returns:
            str: 字符串表示
        """
        return f"<Issue(id={self.id}, title='{self.title}', status='{self.status}')>"
        
    def update_status(self, new_status: str, user_id: int):
        """
        更新问题状态并记录历史
        Args:
            new_status (str): 新状态
            user_id (int): 操作用户ID
        """
        from app.models.issue_history import IssueHistory
        
        old_status = self.status
        self.status = new_status
        
        if new_status == 'closed' and old_status != 'closed':
            self.closed_at = datetime.utcnow()
        
        if new_status == 'resolved' and old_status != 'resolved':
            self.resolved_at = datetime.utcnow()
            if self.created_at:
                self.resolution_time = (self.resolved_at - self.created_at).total_seconds() / 3600
            
        # 创建状态变更历史记录，但不直接添加到session中
        # 而是返回历史记录供调用者处理，避免嵌套事务问题
        history = IssueHistory(
            issue_id=self.id,
            user_id=user_id,
            field_name='status',
            old_value=old_status,
            new_value=new_status,
            changed_at=datetime.utcnow()
        )
        
        # 不再自动添加到history集合，避免可能的自动flush
        # 而是返回历史记录对象，让调用者决定如何处理
        return history 