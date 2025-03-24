"""
代码分析结果模型
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class AnalysisResult(Base):
    """代码分析结果模型"""
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True, comment="分析结果ID")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), comment="关联项目")
    commit_id = Column(Integer, ForeignKey("code_commits.id", ondelete="SET NULL"), nullable=True, comment="关联提交")
    analysis_type = Column(String(50), comment="分析类型")
    result_summary = Column(Text, comment="分析结果摘要")
    details = Column(JSON, comment="详细分析结果")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 分析指标
    code_quality_score = Column(Float, comment="代码质量得分")
    complexity_score = Column(Float, comment="复杂度得分")
    maintainability_score = Column(Float, comment="可维护性得分")
    security_score = Column(Float, comment="安全性得分")
    
    # 关系
    project = relationship("Project", back_populates="analysis_results")
    commit = relationship("CodeCommit", back_populates="analysis_results")
    
    def __repr__(self):
        """返回分析结果对象的字符串表示"""
        return f"<AnalysisResult(id={self.id}, type='{self.analysis_type}', project_id={self.project_id})>"
    
    def to_dict(self):
        """
        将分析结果对象转换为字典
        
        Returns:
            dict: 分析结果信息字典
        """
        return {
            'id': self.id,
            'project_id': self.project_id,
            'commit_id': self.commit_id,
            'analysis_type': self.analysis_type,
            'result_summary': self.result_summary,
            'details': self.details,
            'code_quality_score': self.code_quality_score,
            'complexity_score': self.complexity_score,
            'maintainability_score': self.maintainability_score,
            'security_score': self.security_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 