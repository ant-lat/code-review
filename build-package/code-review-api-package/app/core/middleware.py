"""
中间件模块
@author: pgao
@date: 2024-03-13
"""
import time
import traceback
import uuid
from typing import Callable, Dict, Optional, Any
import json
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.config.logging_config import logger
from app.core.exceptions import AntAuthException
from app.schemas.response import ErrorResponse, ValidationErrorResponse

def setup_middlewares(app: FastAPI) -> None:
    """配置应用的中间件"""
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境中应限制为特定域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 添加请求处理中间件
    app.add_middleware(RequestProcessingMiddleware)

class RequestProcessingMiddleware(BaseHTTPMiddleware):
    """请求处理中间件，处理全局异常、性能监控和请求跟踪"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求
        
        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理函数
            
        Returns:
            Response: 响应对象
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录开始时间
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        
        # 记录请求信息
        logger.info(f"请求开始: [{request_id}] {method} {path} - IP: {client_ip}{' Query: ' + query if query else ''}")
        
        try:
            # 调用下一个处理函数
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            status_code = response.status_code
            
            # 添加处理时间和请求ID到响应头
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            response.headers["X-Request-ID"] = request_id
            
            # 记录响应结果
            logger.info(f"请求完成: [{request_id}] {method} {path} - 状态码: {status_code} - 用时: {process_time:.4f}秒")
            
            # 性能监控
            if process_time > 1.0:
                logger.warning(f"性能警告: [{request_id}] {method} {path} - 处理时间超过1秒: {process_time:.4f}秒")
            
            return response
            
        except RequestValidationError as exc:
            # 处理请求验证错误
            return await self._handle_validation_error(exc, request_id, start_time)
            
        except AntAuthException as exc:
            # 处理应用自定义异常
            return await self._handle_auth_exception(exc, request_id, start_time)
            
        except SQLAlchemyError as exc:
            # 处理数据库异常
            return await self._handle_database_error(exc, request_id, start_time)
            
        except Exception as exc:
            # 处理其他未捕获异常
            return await self._handle_unexpected_error(exc, request_id, start_time)
    
    async def _handle_validation_error(self, exc: RequestValidationError, 
                                      request_id: str, start_time: float) -> JSONResponse:
        """处理验证错误"""
        process_time = time.time() - start_time
        
        # 获取所有错误
        errors = []
        for error in exc.errors():
            error_loc = " -> ".join([str(loc) for loc in error["loc"]])
            errors.append({
                "loc": error_loc,
                "msg": error["msg"],
                "type": error["type"]
            })
        
        # 记录错误
        logger.warning(
            f"请求验证错误 [{request_id}]: {len(errors)}个验证错误 - 用时: {process_time:.4f}秒"
        )
        
        # 构建错误响应
        response = ValidationErrorResponse(
            code=400,
            message="输入数据验证失败",
            errors=errors
        )
        
        return JSONResponse(
            status_code=400,
            content=response.dict(),
            headers={"X-Process-Time": f"{process_time:.4f}", "X-Request-ID": request_id}
        )
    
    async def _handle_auth_exception(self, exc: AntAuthException, 
                                    request_id: str, start_time: float) -> JSONResponse:
        """处理应用自定义异常"""
        process_time = time.time() - start_time
        
        # 记录错误
        logger.warning(
            f"应用异常 [{request_id}]: [{exc.__class__.__name__}] {exc.message} - 用时: {process_time:.4f}秒"
        )
        
        # 构建错误响应
        response = ErrorResponse(
            code=exc.status_code,
            message=exc.message,
            detail=exc.detail
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response.dict(),
            headers={"X-Process-Time": f"{process_time:.4f}", "X-Request-ID": request_id}
        )
    
    async def _handle_database_error(self, exc: SQLAlchemyError, 
                                    request_id: str, start_time: float) -> JSONResponse:
        """处理数据库错误"""
        process_time = time.time() - start_time
        
        # 记录错误
        error_msg = str(exc)
        logger.error(
            f"数据库错误 [{request_id}]: {error_msg} - 用时: {process_time:.4f}秒"
        )
        logger.debug(traceback.format_exc())
        
        # 构建错误响应
        response = ErrorResponse(
            code=500,
            message="数据库操作错误",
            detail="数据库操作过程中出现异常，请稍后再试或联系管理员"
        )
        
        return JSONResponse(
            status_code=500,
            content=response.dict(),
            headers={"X-Process-Time": f"{process_time:.4f}", "X-Request-ID": request_id}
        )
    
    async def _handle_unexpected_error(self, exc: Exception, 
                                      request_id: str, start_time: float) -> JSONResponse:
        """处理未预期的错误"""
        process_time = time.time() - start_time
        
        # 记录错误
        error_msg = str(exc)
        error_type = exc.__class__.__name__
        logger.error(
            f"未处理异常 [{request_id}]: [{error_type}] {error_msg} - 用时: {process_time:.4f}秒"
        )
        logger.debug(traceback.format_exc())
        
        # 构建错误响应
        response = ErrorResponse(
            code=500,
            message="服务器内部错误",
            detail="服务器发生未预期的错误，请稍后再试或联系管理员"
        )
        
        return JSONResponse(
            status_code=500,
            content=response.dict(),
            headers={"X-Process-Time": f"{process_time:.4f}", "X-Request-ID": request_id}
        )

async def exception_handler_middleware(request: Request, call_next):
    """
    异常处理中间件（兼容性保留，推荐使用RequestProcessingMiddleware）
    """
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        logger.debug(traceback.format_exc())
        
        status_code = 500
        message = "服务器内部错误"
        
        if isinstance(e, AntAuthException):
            status_code = e.status_code
            message = e.message
            return JSONResponse(
                status_code=status_code,
                content={"code": status_code, "message": message, "data": None}
            )
        
        if isinstance(e, SQLAlchemyError):
            message = "数据库操作错误"
        elif isinstance(e, ValueError):
            status_code = 400
            message = str(e)
        
        return JSONResponse(
            status_code=status_code,
            content={"code": status_code, "message": message, "data": None}
        ) 