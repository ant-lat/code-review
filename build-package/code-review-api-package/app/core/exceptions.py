"""
异常定义模块
@author: pgao
@date: 2024-03-13
"""
from typing import Any, Dict, Optional, List, Union
from fastapi import HTTPException, status

class AntAuthException(HTTPException):
    """
    应用基础异常类
    所有业务异常都应继承自此类
    """
    def __init__(
        self,
        status_code: int,
        message: str,
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = None,
    ):
        """
        初始化异常

        Args:
            status_code (int): HTTP状态码
            message (str): 错误消息
            detail (Optional[Union[str, Dict[str, Any]]]): 详细错误信息
            error_code (Optional[str]): 业务错误代码
        """
        self.status_code = status_code
        self.message = message
        self.detail = detail or message
        self.error_code = error_code

        # 调用父类初始化
        super().__init__(status_code=status_code, detail=detail or message)

    def __str__(self) -> str:
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class AuthenticationError(AntAuthException):
    """
    身份验证错误
    用于登录失败，Token无效等情况
    """
    def __init__(
        self,
        message: str = "身份验证失败",
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "AUTH_001"
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            detail=detail,
            error_code=error_code
        )


class AuthorizationError(AntAuthException):
    """
    授权错误
    用于权限不足等情况
    """
    def __init__(
        self,
        message: str = "权限不足",
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "AUTH_002"
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            detail=detail,
            error_code=error_code
        )


class ResourceNotFound(AntAuthException):
    """
    资源未找到错误
    """
    def __init__(
        self,
        resource_type: str = "资源",
        resource_id: Optional[Union[str, int]] = None,
        message: Optional[str] = None,
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "RES_001"
    ):
        message = message or f"{resource_type}未找到"
        if resource_id is not None:
            message = f"{resource_type} [{resource_id}] 未找到"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            detail=detail,
            error_code=error_code
        )


class ValidationError(AntAuthException):
    """
    数据验证错误
    用于输入数据不符合要求的情况
    """
    def __init__(
        self,
        message: str = "数据验证失败",
        detail: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]]]] = None,
        error_code: Optional[str] = "VAL_001"
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            detail=detail,
            error_code=error_code
        )


class BusinessError(AntAuthException):
    """
    业务逻辑错误
    用于表示各种业务规则验证失败的情况
    """
    def __init__(
        self,
        message: str,
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "BIZ_001",
        status_code: int = status.HTTP_400_BAD_REQUEST
    ):
        super().__init__(
            status_code=status_code,
            message=message,
            detail=detail,
            error_code=error_code
        )


class DatabaseError(AntAuthException):
    """
    数据库操作错误
    用于数据库操作失败的情况
    """
    def __init__(
        self,
        message: str = "数据库操作失败",
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "DB_001"
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
            error_code=error_code
        )


class ConfigError(AntAuthException):
    """
    配置错误
    用于配置参数无效或缺失的情况
    """
    def __init__(
        self,
        message: str = "配置错误",
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "CFG_001"
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=detail,
            error_code=error_code
        )


class ServiceUnavailable(AntAuthException):
    """
    服务不可用错误
    用于外部服务调用失败或系统维护的情况
    """
    def __init__(
        self,
        message: str = "服务暂时不可用",
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "SVC_001"
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            detail=detail,
            error_code=error_code
        )


class RateLimitExceeded(AntAuthException):
    """
    请求频率超限错误
    用于API调用频率过高的情况
    """
    def __init__(
        self,
        message: str = "请求频率超过限制",
        detail: Optional[Union[str, Dict[str, Any]]] = None,
        error_code: Optional[str] = "RATE_001",
        retry_after: Optional[int] = None
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            detail=detail,
            error_code=error_code
        )
        self.headers = {"Retry-After": str(retry_after)} if retry_after else {}