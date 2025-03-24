"""
代码提交模型模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class CodeCommit(Base):
    """
    代码提交模型，存储代码提交记录
    
    Attributes:
        id (int): 提交ID
        commit_id (str): 提交哈希
        project_id (int): 关联项目ID
        repository (str): 代码仓库
        branch (str): 代码分支
        author_id (int): 提交作者ID
        commit_message (str): 提交说明
        commit_time (datetime): 提交时间
        files_changed (int): 修改文件数
        insertions (int): 新增行数
        deletions (int): 删除行数
        created_at (datetime): 记录创建时间
    """
    __tablename__ = "code_commits"

    id = Column(Integer, primary_key=True, index=True, comment="提交ID")
    commit_id = Column(String(50), unique=True, nullable=False, comment="提交哈希")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, comment="关联项目")
    repository = Column(String(255), nullable=False, comment="代码仓库")
    branch = Column(String(100), nullable=False, comment="代码分支")
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), comment="提交作者")
    commit_message = Column(Text, nullable=False, comment="提交说明")
    commit_time = Column(DateTime, nullable=False, comment="提交时间")
    files_changed = Column(Integer, default=0, comment="修改文件数")
    insertions = Column(Integer, default=0, comment="新增行数")
    deletions = Column(Integer, default=0, comment="删除行数")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="记录创建时间")

    __table_args__ = (
        {'comment': '代码提交记录表'}
    )

    # 关系定义
    project = relationship("Project", back_populates="code_commits")
    author = relationship("User", back_populates="code_commits")
    analysis_results = relationship("AnalysisResult", back_populates="commit", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="commit")

    def __repr__(self):
        """返回代码提交对象的字符串表示"""
        return f"<CodeCommit(id={self.id}, commit_id='{self.commit_id}', branch='{self.branch}')>"

    def to_dict(self):
        """
        将代码提交对象转换为字典
        Returns:
            dict: 代码提交信息字典
        """
        return {
            'id': self.id,
            'commit_id': self.commit_id,
            'project_id': self.project_id,
            'repository': self.repository,
            'branch': self.branch,
            'author_id': self.author_id,
            'commit_message': self.commit_message,
            'commit_time': self.commit_time.isoformat(),
            'files_changed': self.files_changed,
            'insertions': self.insertions,
            'deletions': self.deletions,
            'created_at': self.created_at.isoformat()
        }

    def get_stats(self):
        """
        获取提交统计信息
        Returns:
            dict: 提交统计信息
        """
        return {
            'files_changed': self.files_changed,
            'insertions': self.insertions,
            'deletions': self.deletions,
            'total_changes': self.insertions + self.deletions
        }