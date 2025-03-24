"""
响应模型定义
@author: pgao
@date: 2024-03-13
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator

# 用于泛型支持的类型变量
T = TypeVar('T')
DataT = TypeVar('DataT')
ItemT = TypeVar('ItemT')

class ResponseBase(BaseModel):
    """
    基础响应模型
    所有响应都应该继承此类
    """
    code: int = Field(200, description="状态码")
    message: str = Field("操作成功", description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda dt: dt.isoformat()
        }
    )

class Response(ResponseBase, Generic[DataT]):
    """
    通用响应模型，支持泛型
    示例：
        Response[User] - 用户数据响应
        Response[List[Item]] - 列表数据响应
        Response[Dict[str, Any]] - 字典数据响应
    """
    data: Optional[DataT] = Field(None, description="响应数据")
    
    @model_validator(mode='before')
    @classmethod
    def handle_none_data(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('data') is None and 'code' not in values:
            values['code'] = 404
            values['message'] = "未找到数据"
        return values

class PageInfo(BaseModel):
    """分页信息"""
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页条数")
    total: int = Field(0, description="总记录数")
    total_pages: int = Field(0, description="总页数")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )
    
    @model_validator(mode='after')
    def calculate_total_pages(self) -> "PageInfo":
        """计算总页数"""
        if self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size
        else:
            self.total_pages = 0
        return self

class PageResponse(ResponseBase, Generic[ItemT]):
    """
    分页响应模型
    示例：
        PageResponse[User] - 用户分页数据
    """
    data: List[ItemT] = Field(None, description="分页数据列表")
    page_info: PageInfo = Field(..., description="分页信息")
    @classmethod
    def create(
        cls, 
        items: List[ItemT], 
        total: int, 
        page: int = 1, 
        page_size: int = 10, 
        message: str = "查询成功"
    ) -> "PageResponse[ItemT]":
        """
        创建分页响应
        
        Args:
            items: 分页数据列表
            total: 总记录数
            page: 当前页码
            page_size: 每页条数
            message: 响应消息
            
        Returns:
            PageResponse[ItemT]: 分页响应对象
        """
        page_info = PageInfo(
            page=page,
            page_size=page_size,
            total=total
        )
        # 计算总页数
        page_info.calculate_total_pages()
        
        return cls(
            data=items,
            page_info=page_info,
            message=message
        )

class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class ErrorResponse(ResponseBase):
    """
    错误响应模型
    用于返回各种错误响应
    """
    code: int = Field(500, description="错误状态码")
    message: str = Field("服务器内部错误", description="错误消息")
    detail: Optional[Union[str, Dict[str, Any]]] = Field(None, description="错误详情")
    path: Optional[str] = Field(None, description="请求路径")
    
    @classmethod
    def create(
        cls, 
        code: int, 
        message: str, 
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        path: Optional[str] = None
    ) -> "ErrorResponse":
        """
        创建错误响应
        
        Args:
            code: 错误状态码
            message: 错误消息
            detail: 错误详情
            path: 请求路径
            
        Returns:
            ErrorResponse: 错误响应对象
        """
        return cls(
            code=code,
            message=message,
            detail=detail,
            path=path
        )

class ValidationErrorDetail(BaseModel):
    """验证错误详情"""
    loc: str = Field(..., description="错误位置")
    msg: str = Field(..., description="错误消息")
    type: str = Field(..., description="错误类型")
    
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

class ValidationErrorResponse(ErrorResponse):
    """
    验证错误响应模型
    用于返回请求参数验证错误
    """
    code: int = Field(400, description="错误状态码")
    message: str = Field("输入数据验证失败", description="错误消息")
    errors: List[Union[ValidationErrorDetail, Dict[str, Any]]] = Field(None, description="错误列表")
