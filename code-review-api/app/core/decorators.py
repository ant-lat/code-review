"""
路由装饰器模块
@author: pgao
@date: 2024-03-13
"""
from functools import wraps
import time
import traceback
from typing import Callable, Any, Dict, List, Optional, Union
from fastapi import Request, Response, status
import logging
from datetime import datetime

from app.config.logging_config import logger
from app.core.exceptions import DatabaseError, AuthorizationError, ResourceNotFound

def handle_request(endpoint_name: str = None):
    """
    通用请求处理装饰器
    处理请求日志记录、计时和异常处理
    
    Args:
        endpoint_name (str, optional): 端点名称，如果为None则使用函数名
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 获取客户端IP
            client_ip = request.client.host if request.client else "unknown"
            
            # 获取当前用户
            current_user = kwargs.get('current_user')
            username = current_user.username if current_user else "未登录用户"
            
            # 获取端点名称
            route_name = endpoint_name or func.__name__
            
            # 记录开始时间
            start_time = time.time()
            logger.info(f"用户 {username} 请求 [{route_name}]，IP: {client_ip}")
            
            # 记录请求信息(仅在DEBUG级别)
            if logger.isEnabledFor(logging.DEBUG):
                method = request.method
                url = str(request.url)
                logger.debug(f"请求详情: {method} {url}")
                logger.debug(f"请求参数: {dict(request.query_params)}")
                
                try:
                    if request.method in ["POST", "PUT", "PATCH"]:
                        body = await request.json()
                        # 屏蔽敏感数据
                        if isinstance(body, dict):
                            safe_body = body.copy()
                            for k in ["password", "password_hash", "token", "key", "secret"]:
                                if k in safe_body:
                                    safe_body[k] = "******"
                            logger.debug(f"请求体: {safe_body}")
                except Exception:
                    # 忽略请求体解析错误
                    pass
            
            try:
                # 执行原函数
                result = await func(request, *args, **kwargs)
                
                # 计算处理时间
                process_time = time.time() - start_time
                logger.info(f"处理完成 [{route_name}]，用时: {process_time:.2f}秒")
                
                # 判断是否需要记录性能警告
                if process_time > 1.0:  # 超过1秒的请求
                    logger.warning(f"性能警告: [{route_name}] 处理时间超过 1秒，实际: {process_time:.2f}秒")
                
                return result
            except Exception as e:
                # 计算处理时间
                process_time = time.time() - start_time
                
                # 记录异常信息
                if isinstance(e, DatabaseError):
                    logger.error(f"数据库操作错误 [{route_name}]: {str(e)}, 用时: {process_time:.2f}秒")
                elif isinstance(e, AuthorizationError):
                    logger.warning(f"用户权限不足 [{route_name}]: {str(e)}, 用时: {process_time:.2f}秒")
                elif isinstance(e, ResourceNotFound):
                    logger.warning(f"资源未找到 [{route_name}]: {str(e)}, 用时: {process_time:.2f}秒")
                else:
                    logger.error(f"处理请求时发生错误 [{route_name}]: {str(e)}, 用时: {process_time:.2f}秒")
                    logger.debug(traceback.format_exc())
                
                # 重新抛出异常，让全局异常处理器处理
                raise
        
        return wrapper
    
    return decorator

def rate_limit(max_calls: int, period: int = 60):
    """
    简单的速率限制装饰器
    注意：这是基于内存的简单实现，生产环境建议使用Redis等分布式解决方案
    
    Args:
        max_calls (int): 周期内最大请求次数
        period (int): 时间周期(秒)
        
    Returns:
        Callable: 装饰器函数
    """
    # 存储 IP 访问记录 {ip: [(timestamp, count),...]}
    rate_history: Dict[str, List[tuple]] = {}
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 获取客户端IP
            client_ip = request.client.host if request.client else "unknown"
            
            # 清理过期记录
            now = time.time()
            if client_ip in rate_history:
                rate_history[client_ip] = [
                    (ts, count) for ts, count in rate_history[client_ip] 
                    if now - ts < period
                ]
            
            # 获取当前周期内请求次数
            current_count = sum(count for _, count in rate_history.get(client_ip, []))
            
            # 判断是否超过限制
            if current_count >= max_calls:
                logger.warning(f"请求频率限制: IP {client_ip} 超过限制 {max_calls}/{period}秒")
                return Response(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content="请求频率过高，请稍后重试",
                    media_type="text/plain"
                )
            
            # 更新访问记录
            if client_ip not in rate_history:
                rate_history[client_ip] = [(now, 1)]
            else:
                rate_history[client_ip].append((now, 1))
            
            # 执行原函数
            return await func(request, *args, **kwargs)
        
        return wrapper
    
    return decorator

def cache_response(expire_seconds: int = 60):
    """
    简单的响应缓存装饰器
    注意：这是基于内存的简单实现，生产环境建议使用Redis等分布式解决方案
    
    Args:
        expire_seconds (int): 缓存过期时间(秒)
        
    Returns:
        Callable: 装饰器函数
    """
    # 存储响应缓存 {cache_key: (timestamp, response)}
    cache_data: Dict[str, tuple] = {}
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # 仅缓存GET请求
            if request.method != "GET":
                return await func(request, *args, **kwargs)
            
            # 生成缓存键(基于URL和查询参数)
            cache_key = f"{str(request.url)}"
            
            # 检查缓存是否存在且未过期
            now = time.time()
            if cache_key in cache_data:
                timestamp, response = cache_data[cache_key]
                if now - timestamp < expire_seconds:
                    logger.debug(f"缓存命中: {cache_key}")
                    return response
            
            # 执行原函数
            response = await func(request, *args, **kwargs)
            
            # 缓存响应
            cache_data[cache_key] = (now, response)
            
            # 清理过期缓存
            for key in list(cache_data.keys()):
                if now - cache_data[key][0] > expire_seconds:
                    del cache_data[key]
            
            return response
        
        return wrapper
    
    return decorator 