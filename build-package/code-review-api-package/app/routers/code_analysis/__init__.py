"""
代码分析路由包
@author: pgao
@date: 2024-03-13
"""
# 包含代码结构解析、质量检查、代码审查等API路由
from app.routers.code_analysis.code_analysis import router as code_analysis_router
from app.routers.code_analysis.code_review import router as code_review_router