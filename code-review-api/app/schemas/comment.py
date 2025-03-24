"""
评论相关模型定义
@author: pgao
@date: 2024-03-13
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class CommentCreate(BaseModel):
    """评论创建请求模型"""
    content: str = Field(..., description="评论内容")
    file_path: Optional[str] = Field(None, description="文件路径")
    line_number: Optional[int] = Field(None, description="行号")

class CommentResponse(BaseModel):
    """评论响应模型"""
    id: int = Field(..., description="评论ID")
    issue_id: int = Field(..., description="问题ID")
    user_id: int = Field(..., description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    user_name: Optional[str] = Field(None, description="用户名(别名)")
    content: str = Field(..., description="评论内容")
    file_path: Optional[str] = Field(None, description="文件路径")
    line_number: Optional[int] = Field(None, description="行号")
    created_at: datetime = Field(..., description="创建时间")
    user: Optional[Dict[str, Any]] = Field(None, description="用户信息")
    
    class Config:
        from_attributes = True
        
    def __init__(self, **data):
        # 如果提供了user_name但没有username，则将user_name复制给username
        if 'user_name' in data and 'username' not in data:
            data['username'] = data['user_name']
        # 如果提供了user对象但没有username，则使用user.username
        elif 'user' in data and data['user'] and 'username' not in data:
            data['username'] = data['user'].get('username')
        super().__init__(**data)