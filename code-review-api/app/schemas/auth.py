"""
认证相关的数据模型模块
@author: pgao
@date: 2024-03-13
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

class TokenResponse(BaseModel):
    """
    令牌响应模型
    
    Attributes:
        access_token (str): 访问令牌
        refresh_token (str): 刷新令牌
        token_type (str): 令牌类型，默认为bearer
        expires_in (int): 令牌过期时间（秒）
    """
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="令牌过期时间（秒）")

class RefreshTokenRequest(BaseModel):
    """
    刷新令牌请求模型
    
    Attributes:
        refresh_token (str): 刷新令牌
    """
    refresh_token: str = Field(description="刷新令牌")

class UserResponse(BaseModel):
    """
    用户信息响应模型
    
    Attributes:
        id (int): 用户ID
        username (str): 用户名
        email (str): 邮箱
        roles (list): 角色列表
        is_active (bool): 是否激活
        last_login (datetime): 最后登录时间
    """
    id: int = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: EmailStr = Field(description="邮箱")
    roles: list = Field(default=[], description="角色列表")
    is_active: bool = Field(description="是否激活")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    """
    登录请求模型
    
    Attributes:
        user_id (str): 用户登录ID
        password (str): 密码
    """
    user_id: str = Field(min_length=3, max_length=50, description="用户登录ID")
    password: str = Field(min_length=6, max_length=50, description="密码")
    remember_me: bool = Field(default=False, description="记住我")

class ChangePasswordRequest(BaseModel):
    """
    修改密码请求模型
    
    Attributes:
        old_password (str): 旧密码
        new_password (str): 新密码
        confirm_password (str): 确认密码
    """
    old_password: str = Field(min_length=6, max_length=50, description="旧密码")
    new_password: str = Field(min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(min_length=6, max_length=50, description="确认密码")

class ForgotPasswordRequest(BaseModel):
    """
    忘记密码请求模型
    
    Attributes:
        email (str): 邮箱
    """
    email: EmailStr = Field(description="邮箱")

class VerifyCodeRequest(BaseModel):
    """
    验证码验证请求模型
    
    Attributes:
        email (str): 邮箱
        code (str): 验证码
    """
    email: EmailStr = Field(description="邮箱")
    code: str = Field(min_length=4, max_length=8, description="验证码")

class ResetPasswordWithCodeRequest(BaseModel):
    """
    通过验证码重置密码请求模型
    
    Attributes:
        email (str): 邮箱
        code (str): 验证码
        new_password (str): 新密码
        confirm_password (str): 确认密码
    """
    email: EmailStr = Field(description="邮箱")
    code: str = Field(min_length=4, max_length=8, description="验证码")
    new_password: str = Field(min_length=6, max_length=50, description="新密码")
    confirm_password: str = Field(min_length=6, max_length=50, description="确认密码") 