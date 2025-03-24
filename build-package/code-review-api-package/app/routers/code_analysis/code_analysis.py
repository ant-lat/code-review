"""
代码分析路由模块
@author: pgao
@date: 2024-03-13
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from typing import Optional
import time
import traceback

from app.database import get_db
from app.services.analysis_service import CodeAnalysisService
from app.core.security import get_current_user
from app.models.user import User
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError
from app.schemas.response import Response
from app.config.logging_config import logger
from pydantic import BaseModel

# 创建路由器
router = APIRouter(
    prefix="/api/v1/code", 
    tags=["代码分析"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

class CodeCheckRequest(BaseModel):
    """代码检查请求模型"""
    project_id: int
    branch: str = "main"
    commit_id: Optional[int] = None
    code_path: Optional[str] = None

class CodeAnalysisResponse(BaseModel):
    """代码分析响应模型"""
    complexity: float
    issues: list
    statistics: dict
    analyzed_at: str

@router.get("/structure", response_model=Response)
async def get_code_structure(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    获取代码结构
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 代码结构响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 的代码结构，IP: {client_ip}")
    
    try:
        service = CodeAnalysisService(db)
        
        # 检查项目访问权限
        if not service.check_project_access(project_id, current_user.id):
            logger.warning(f"用户 {current_user.username} 尝试访问项目 {project_id} 的代码结构，但权限不足")
            raise AuthorizationError(message="无项目访问权限")
        
        structure = service.get_code_structure(project_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 代码结构成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=structure,
            message="获取代码结构成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 代码结构失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取代码结构失败", detail=str(e))

@router.get("/quality", response_model=Response)
async def get_code_quality(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    获取代码质量报告
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 代码质量报告响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 的代码质量报告，IP: {client_ip}")
    
    try:
        service = CodeAnalysisService(db)
        
        # 检查项目访问权限
        if not service.check_project_access(project_id, current_user.id):
            logger.warning(f"用户 {current_user.username} 尝试访问项目 {project_id} 的代码质量报告，但权限不足")
            raise AuthorizationError(message="无项目访问权限")
        
        quality_report = service.get_code_quality_report(project_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 代码质量报告成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=quality_report,
            message="获取代码质量报告成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 代码质量报告失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取代码质量报告失败", detail=str(e))

@router.get("/hotspots", response_model=Response)
async def get_code_hotspots(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    获取代码热点
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 代码热点响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 的代码热点，IP: {client_ip}")
    
    try:
        service = CodeAnalysisService(db)
        
        # 检查项目访问权限
        if not service.check_project_access(project_id, current_user.id):
            logger.warning(f"用户 {current_user.username} 尝试访问项目 {project_id} 的代码热点，但权限不足")
            raise AuthorizationError(message="无项目访问权限")
        
        hotspots = service.get_code_hotspots(project_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 代码热点成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=hotspots,
            message="获取代码热点成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 代码热点失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取代码热点失败", detail=str(e))

@router.post("/analyze", response_model=Response[CodeAnalysisResponse])
async def run_code_analysis(
    request: Request,
    check_data: CodeCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[CodeAnalysisResponse]:
    """
    运行代码分析
    
    Args:
        request (Request): 请求对象
        check_data (CodeCheckRequest): 代码检查请求数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[CodeAnalysisResponse]: 代码分析响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求分析项目 {check_data.project_id} 的代码，分支: {check_data.branch}，IP: {client_ip}")
    
    try:
        service = CodeAnalysisService(db)
        
        # 检查项目访问权限
        if not service.check_project_access(check_data.project_id, current_user.id):
            logger.warning(f"用户 {current_user.username} 尝试分析项目 {check_data.project_id} 的代码，但权限不足")
            raise AuthorizationError(message="无项目访问权限")
        
        analysis_result = service.analyze_code(
            project_id=check_data.project_id,
            commit_id=check_data.commit_id,
            code_path=check_data.code_path
        )
        
        process_time = time.time() - start_time
        logger.info(f"分析项目 {check_data.project_id} 代码成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=analysis_result,
            message="代码分析成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"分析项目 {check_data.project_id} 代码失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="代码分析失败", detail=str(e))

@router.get("/history", response_model=Response)
async def get_analysis_history(
    request: Request,
    project_id: int = Query(..., description="项目ID"),
    limit: int = Query(10, ge=1, le=100, description="返回记录数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    获取代码分析历史
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        limit (int): 返回记录数
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 代码分析历史响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 的分析历史，IP: {client_ip}")
    
    try:
        service = CodeAnalysisService(db)
        
        # 检查项目访问权限
        if not service.check_project_access(project_id, current_user.id):
            logger.warning(f"用户 {current_user.username} 尝试访问项目 {project_id} 的分析历史，但权限不足")
            raise AuthorizationError(message="无项目访问权限")
        
        history = service.get_analysis_history(project_id, limit)
        
        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 分析历史成功，记录数: {len(history)}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=history,
            message="获取分析历史成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 分析历史失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取分析历史失败", detail=str(e))