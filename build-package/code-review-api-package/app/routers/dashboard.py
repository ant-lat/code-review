"""
仪表盘相关接口
@author: pgao
@date: 2024-03-13
"""
import logging
from fastapi import APIRouter, Depends, Query, Path, Request, Body
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
import traceback

from app.core.exceptions import DatabaseError, ResourceNotFound, AuthorizationError
from app.config.logging_config import logger
from app.database import get_db
from app.models import User
from app.services.dashboard import DashboardService
from app.schemas.response import Response
from app.schemas.dashboard import (
    DashboardStatsResponse,
    StatusDistribution,
    TypeDistribution,
    TeamWorkload,
    ProjectIssueDistribution,
    TrendAnalysis
)
from app.core.security import get_current_user
from app.core.decorators import handle_request

# 创建仪表盘路由
dashboard_router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["仪表盘管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "参数验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

@dashboard_router.get("/stats", response_model=Response[DashboardStatsResponse])
async def get_dashboard_stats(
    request: Request,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[DashboardStatsResponse]:
    """
    获取仪表盘统计数据
    
    Args:
        request (Request): 请求对象
        start_date (Optional[str]): 开始日期 (YYYY-MM-DD)
        end_date (Optional[str]): 结束日期 (YYYY-MM-DD)
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response[DashboardStatsResponse]: 仪表盘统计数据
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取仪表盘统计数据，IP: {client_ip}")
    
    try:
        # 处理日期范围
        date_filters = {}
        if start_date:
            try:
                date_filters["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
                
        if end_date:
            try:
                date_filters["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        # 如果没有设置日期范围，默认使用最近30天
        if not date_filters:
            date_filters = {
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now() + timedelta(days=1)  # 延长一天以确保包含当天创建的所有问题
            }
            logger.info("未提供日期范围，使用默认值：最近30天，结束日期延长一天")
        
        dashboard_service = DashboardService(db)
        # 获取所有统计数据，使用**date_filters将字典展开为关键字参数
        stats = dashboard_service.get_dashboard_stats(**date_filters)
        
        process_time = time.time() - start_time
        logger.info(f"获取仪表盘统计数据成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=DashboardStatsResponse(**stats),
            message="获取仪表盘统计数据成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取仪表盘统计数据失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取仪表盘统计数据失败", detail=str(e))

@dashboard_router.get("/team-workload", response_model=Response[List[TeamWorkload]])
async def get_team_workload(
    request: Request,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[List[TeamWorkload]]:
    """
    获取团队工作负载统计
    
    Args:
        request (Request): 请求对象
        start_date (Optional[str]): 开始日期 (YYYY-MM-DD)
        end_date (Optional[str]): 结束日期 (YYYY-MM-DD)
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response[List[TeamWorkload]]: 团队工作负载统计
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取团队工作负载，IP: {client_ip}")
    
    try:
        # 处理日期范围
        date_filters = {}
        if start_date:
            try:
                date_filters["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
                
        if end_date:
            try:
                date_filters["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        # 如果没有设置日期范围，默认使用最近30天
        if not date_filters:
            date_filters = {
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now() + timedelta(days=1)  # 延长一天以确保包含当天创建的所有问题
            }
            logger.info("未提供日期范围，使用默认值：最近30天，结束日期延长一天")
        
        dashboard_service = DashboardService(db)
        workload = dashboard_service.get_team_workload(date_filters)
        
        process_time = time.time() - start_time
        logger.info(f"获取团队工作负载统计成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=workload,
            message="获取团队工作负载统计成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取团队工作负载统计失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取团队工作负载统计失败", detail=str(e))

@dashboard_router.get("/project-stats", response_model=Response[List[ProjectIssueDistribution]])
async def get_project_stats(
    request: Request,
    limit: Optional[int] = Query(10, description="返回的项目数量", ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[List[ProjectIssueDistribution]]:
    """
    获取项目问题分布统计
    
    Args:
        request (Request): 请求对象
        limit (int): 返回的项目数量限制
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response[List[ProjectIssueDistribution]]: 项目问题分布统计
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目问题分布，限制 {limit} 个项目，IP: {client_ip}")
    
    try:
        dashboard_service = DashboardService(db)
        distribution = dashboard_service.get_project_distribution(limit=limit)
        
        process_time = time.time() - start_time
        logger.info(f"获取项目问题分布统计成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=distribution,
            message="获取项目问题分布统计成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目问题分布统计失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取项目问题分布统计失败", detail=str(e))

@dashboard_router.get("/trend", response_model=Response[TrendAnalysis])
async def get_trend_analysis(
    request: Request,
    days: Optional[int] = Query(30, description="分析的天数", ge=1, le=365),
    interval: Optional[str] = Query("day", description="统计间隔 (day/week/month)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[TrendAnalysis]:
    """
    获取问题趋势分析
    
    Args:
        request (Request): 请求对象
        days (int): 分析的天数，默认30天
        interval (str): 统计间隔 (day/week/month)
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response[TrendAnalysis]: 问题趋势分析
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取问题趋势分析，天数: {days}，间隔: {interval}，IP: {client_ip}")
    
    try:
        # 验证间隔参数
        if interval not in ["day", "week", "month"]:
            logger.warning(f"无效的统计间隔参数: {interval}，使用默认值 'day'")
            interval = "day"
            
        dashboard_service = DashboardService(db)
        trend = dashboard_service.get_trend_analysis(days, interval)
        
        process_time = time.time() - start_time
        logger.info(f"获取问题趋势分析成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=trend,
            message="获取问题趋势分析成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取问题趋势分析失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取问题趋势分析失败", detail=str(e))

@dashboard_router.get("/user-performance", response_model=Response[List[Dict[str, Any]]])
async def get_all_user_performance(
    request: Request,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[List[Dict[str, Any]]]:
    """
    获取所有用户性能统计
    
    Args:
        request (Request): 请求对象
        start_date (Optional[str]): 开始日期 (YYYY-MM-DD)
        end_date (Optional[str]): 结束日期 (YYYY-MM-DD)
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response[List[Dict[str, Any]]]: 所有用户性能统计
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取所有用户性能统计，IP: {client_ip}")
    
    try:
        # 处理日期范围
        date_filters = {}
        if start_date:
            try:
                date_filters["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
                
        if end_date:
            try:
                date_filters["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        # 如果没有设置日期范围，默认使用最近30天
        if not date_filters:
            date_filters = {
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now() + timedelta(days=1)  # 延长一天以确保包含当天创建的所有问题
            }
            logger.info("未提供日期范围，使用默认值：最近30天，结束日期延长一天")
        
        dashboard_service = DashboardService(db)

        performance_stats = dashboard_service.get_user_performance_stats(date_filters=date_filters)
        
        process_time = time.time() - start_time
        logger.info(f"获取所有用户性能统计成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=performance_stats,
            message="获取用户性能统计成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取所有用户性能统计失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取用户性能统计失败", detail=str(e))

@dashboard_router.get("/user-performance/{user_id}", response_model=Response[Dict[str, Any]])
async def get_user_performance(
    request: Request,
    user_id: int = Path(..., description="用户ID", ge=1),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[Dict[str, Any]]:
    """
    获取特定用户的性能统计
    
    Args:
        request (Request): 请求对象
        user_id (int): 用户ID
        start_date (Optional[str]): 开始日期 (YYYY-MM-DD)
        end_date (Optional[str]): 结束日期 (YYYY-MM-DD)
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response[Dict[str, Any]]: 用户性能统计
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
        ResourceNotFound: 用户不存在时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取用户 {user_id} 的性能统计，IP: {client_ip}")
    
    try:
        # 处理日期范围
        date_filters = {}
        if start_date:
            try:
                date_filters["start_date"] = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
                
        if end_date:
            try:
                date_filters["end_date"] = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        # 如果没有设置日期范围，默认使用最近30天
        if not date_filters:
            date_filters = {
                "start_date": datetime.now() - timedelta(days=30),
                "end_date": datetime.now() + timedelta(days=1)  # 延长一天以确保包含当天创建的所有问题
            }
            logger.info("未提供日期范围，使用默认值：最近30天，结束日期延长一天")
        
        dashboard_service = DashboardService(db)
        performance_stats = dashboard_service.get_user_performance_stats(user_id, date_filters)
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {user_id} 的性能统计成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=performance_stats,
            message=f"获取用户ID {user_id} 的性能统计成功"
        )
    except ResourceNotFound:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取用户 {user_id} 的性能统计失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取用户性能统计失败", detail=str(e))

@dashboard_router.get("/recent-activity", response_model=Response[List[Dict[str, Any]]])
async def get_recent_activity(
    request: Request,
    limit: Optional[int] = Query(10, description="返回结果数量限制", ge=1, le=100),
    activity_type: Optional[str] = Query(None, description="活动类型过滤"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[List[Dict[str, Any]]]:
    """
    获取最近活动

    Args:
        request (Request): 请求对象
        limit (int): 返回结果数量限制，默认10条
        activity_type (Optional[str]): 活动类型过滤
        current_user (User): 当前用户
        db (Session): 数据库会话

    Returns:
        Response[List[Dict[str, Any]]]: 最近活动列表

    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取最近活动，限制 {limit} 条，IP: {client_ip}")

    try:
        filters = {}
        if activity_type:
            filters["activity_type"] = activity_type

        dashboard_service = DashboardService(db)
        activities = dashboard_service.get_recent_activity(limit)

        process_time = time.time() - start_time
        logger.info(f"获取最近活动成功，返回 {len(activities)} 条记录，处理时间: {process_time:.2f}秒")

        return Response(
            data=activities,
            message="获取最近活动成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取最近活动失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取最近活动失败", detail=str(e))

@dashboard_router.get("/personal", response_model=Response[Dict[str, Any]])
async def get_personal_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response[Dict[str, Any]]:
    """
    获取个人仪表盘数据
    
    Args:
        request (Request): 请求对象
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response[Dict[str, Any]]: 个人仪表盘数据
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取个人仪表盘数据，IP: {client_ip}")
    
    try:
        dashboard_service = DashboardService(db)
        personal_stats = dashboard_service.get_personal_dashboard(current_user.id)
        
        process_time = time.time() - start_time
        logger.info(f"获取用户 {current_user.username} 的个人仪表盘数据成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=personal_stats,
            message="获取个人仪表盘数据成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取个人仪表盘数据失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取个人仪表盘数据失败", detail=str(e))

@dashboard_router.post("/save-config", response_model=Response)
async def save_dashboard_config(
    request: Request,
    config: Dict[str, Any] = Body(..., description="仪表盘配置"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Response:
    """
    保存用户仪表盘配置
    
    Args:
        request (Request): 请求对象
        config (Dict[str, Any]): 仪表盘配置
        current_user (User): 当前用户
        db (Session): 数据库会话
        
    Returns:
        Response: 操作结果
        
    Raises:
        DatabaseError: 数据库操作错误时抛出
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求保存仪表盘配置，IP: {client_ip}")
    
    try:
        dashboard_service = DashboardService(db)
        dashboard_service.save_user_dashboard_config(current_user.id, config)
        
        process_time = time.time() - start_time
        logger.info(f"保存用户 {current_user.username} 的仪表盘配置成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data={"success": True},
            message="保存仪表盘配置成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"保存仪表盘配置失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="保存仪表盘配置失败", detail=str(e))