from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class UserRpythonpyesponse(BaseModel):
    id: int
    username: str
    email: str
    
class CommentResponse(BaseModel):
    id: int
    content: str
    author: UserResponse
    created_at: datetime

class IssueResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    creator: UserResponse
    created_at: datetime
    comments: List[CommentResponse] = []

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[IssueResponse]