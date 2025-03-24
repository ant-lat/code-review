"""
问题追踪路由模块
此模块处理项目问题的创建、更新、查询和评论等功能
@author: pgao
@date: 2024-03-13
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import time
import traceback

from app.database import get_db
from app.models.user import User
from app.services.issue_service import IssueService
from app.core.security import get_current_user, require_permission
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError
from app.schemas.response import Response, PageResponse
from app.schemas.issue import IssueCreate, IssueDetail, IssueListItem, StatusUpdate, IssueBatchUpdate
from app.schemas.comment import CommentResponse, CommentCreate
from app.config.logging_config import logger
from pydantic import BaseModel, Field
from app.routers.project_management.projects import check_project_permission
from app.routers.code_analysis.code_review import get_issue_service

router = APIRouter(
    prefix="/api/v1/issues",
    tags=["问题追踪"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

class IssueTagCreate(BaseModel):
    """问题标签创建模型"""
    name: str
    color: str = "#1890ff"
    description: Optional[str] = None
    
class IssueTagResponse(BaseModel):
    """问题标签响应模型"""
    id: int
    name: str
    color: str
    description: Optional[str] = None
    created_at: Optional[str] = None

@router.get("/", response_model=Response[PageResponse[IssueListItem]])
async def get_issues(
    request: Request,
    project_id: Optional[int] = Query(None, description="项目ID，不提供则返回所有项目的问题"),
    status: Optional[str] = Query(None, description="问题状态过滤"),
    priority: Optional[str] = Query(None, description="优先级过滤"),
    assignee_id: Optional[int] = Query(None, description="指派人ID过滤"),
    creator_id: Optional[int] = Query(None, description="创建人ID过滤"),
    tag_id: Optional[int] = Query(None, description="标签ID过滤"),
    issue_type: Optional[str] = Query(None, description="问题类型过滤"),
    created_after: Optional[str] = Query(None, description="创建时间起始（YYYY-MM-DD）"),
    created_before: Optional[str] = Query(None, description="创建时间截止（YYYY-MM-DD）"),
    keyword: Optional[str] = Query(None, description="标题或描述关键字"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[PageResponse[IssueListItem]]:
    """
    获取项目问题列表
    
    Args:
        request (Request): 请求对象
        project_id (Optional[int]): 项目ID，不提供则返回用户有权限访问的所有问题
        status (Optional[str]): 问题状态过滤
        priority (Optional[str]): 优先级过滤
        assignee_id (Optional[int]): 指派人ID过滤
        creator_id (Optional[int]): 创建人ID过滤
        tag_id (Optional[int]): 标签ID过滤
        issue_type (Optional[str]): 问题类型过滤
        created_after (Optional[str]): 创建时间起始（YYYY-MM-DD）
        created_before (Optional[str]): 创建时间截止（YYYY-MM-DD）
        keyword (Optional[str]): 标题或描述关键字
        page (int): 页码
        page_size (int): 每页数量
        sort_by (str): 排序字段
        sort_order (str): 排序方向
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[PageResponse[IssueListItem]]: 问题列表分页响应
        
    Raises:
        AuthorizationError: 权限不足
        BusinessError: 业务错误
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    
    if project_id:
        logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 的问题列表，IP: {client_ip}")
    else:
        logger.info(f"用户 {current_user.username} 请求获取所有项目的问题列表，IP: {client_ip}")
    
    try:
        # 验证项目访问权限（如果提供了项目ID）
        if project_id:
            has_project_access = check_project_permission(db, current_user.id, project_id, 'view')
            if not has_project_access:
                logger.warning(f"用户 {current_user.username} 无权访问项目 {project_id}")
                raise AuthorizationError(message="无权访问此项目")
        
        # 获取问题列表
        issue_service = IssueService(db)
        
        # 调用服务方法获取问题列表
        if project_id:
            # 如果提供了项目ID，获取指定项目的问题
            issues_dict = issue_service.get_issues(
                project_id=project_id,
                status=status,
                priority=priority,
                assignee_id=assignee_id,
                creator_id=creator_id,
                tag_id=tag_id,
                issue_type=issue_type,
                created_after=created_after,
                created_before=created_before,
                keyword=keyword,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
                current_user_id=current_user.id
            )
        else:
            # 如果没有提供项目ID，获取用户有权限访问的所有项目的问题
            # TODO: 实现跨项目问题查询逻辑
            # 临时实现：返回用户参与的项目的所有问题
            issues_dict = issue_service.get_user_issues(
                user_id=current_user.id,
                status=status,
                priority=priority,
                assignee_id=assignee_id,
                creator_id=creator_id,
                tag_id=tag_id,
                issue_type=issue_type,
                created_after=created_after,
                created_before=created_before,
                keyword=keyword,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
                current_user_id=current_user.id
            )
        
        # 构建分页响应
        paginated_response = PageResponse.create(
            items=issues_dict.get("items", []),
            total=issues_dict.get("total", 0),
            page=page,
            page_size=page_size
        )
        
        process_time = time.time() - start_time
        if project_id:
            logger.info(f"用户 {current_user.username} 获取项目 {project_id} 问题列表成功，处理时间: {process_time:.2f}秒")
        else:
            logger.info(f"用户 {current_user.username} 获取所有项目问题列表成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=paginated_response,
            message="获取问题列表成功"
        )
    except AuthorizationError:
        # 重新抛出权限错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 问题列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取问题列表失败", detail=str(e))

@router.post("/", response_model=Response[IssueDetail])
async def create_issue(
    request: Request,
    issue_data: IssueCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueDetail]:
    """
    创建问题
    
    Args:
        request (Request): 请求对象
        issue_data (IssueCreate): 问题创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueDetail]: 创建的问题详情
        
    Raises:
        AuthorizationError: 权限不足
        BusinessError: 业务错误
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求创建项目 {issue_data.project_id} 的问题，IP: {client_ip}")
    
    try:
        # 验证项目访问权限
        has_project_access = check_project_permission(db, current_user.id, issue_data.project_id, 'update')
        if not has_project_access:
            logger.warning(f"用户 {current_user.username} 无权访问项目 {issue_data.project_id}")
            raise AuthorizationError(message="无权访问此项目")
        
        # 创建问题
        issue_service = IssueService(db)
        result = issue_service.create_issue({
            "project_id": issue_data.project_id,
            "title": issue_data.title,
            "description": issue_data.description,
            "priority": issue_data.priority,
            "issue_type": issue_data.issue_type,
            "assignee_id": issue_data.assignee_id,
            "creator_id": current_user.id,
            "commit_id": issue_data.commit_id,
            "line_start": issue_data.line_start,
            "line_end": issue_data.line_end,
            "severity": issue_data.severity,
            "status": issue_data.status if hasattr(issue_data, "status") and issue_data.status else "open",
            "file_path": issue_data.file_path
        })
        
        # 检查返回结果是否成功
        if not result.get("success", False):
            # 如果创建失败，记录错误并抛出异常
            error_message = result.get("message", "创建问题失败")
            logger.error(f"用户 {current_user.username} 创建问题失败: {error_message}")
            raise BusinessError(message=error_message)
            
        # 获取创建的问题数据
        issue_data = result.get("data")
        if not issue_data:
            logger.error(f"用户 {current_user.username} 创建问题成功但返回数据为空")
            raise DatabaseError(message="创建问题成功但返回数据为空")
            
        issue_id = issue_data.get("id")
        if not issue_id:
            logger.error(f"用户 {current_user.username} 创建问题成功但无法获取问题ID")
            raise DatabaseError(message="创建问题成功但无法获取问题ID")
        
        process_time = time.time() - start_time
        logger.info(f"创建问题成功，问题ID: {issue_id}，处理时间: {process_time:.2f}秒")
        
        # 直接返回创建问题的接口返回结果中的数据
        return Response(
            data=issue_data,
            message="创建问题成功"
        )
        
    except BusinessError as e:
        # 处理业务逻辑异常
        raise
    except AuthorizationError:
        # 重新抛出权限错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"创建问题失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message=f"创建问题失败: {str(e)}")

@router.get("/{issue_id}", response_model=Response[IssueDetail])
async def get_issue_detail(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueDetail]:
    """
    获取问题详情
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueDetail]: 问题详情响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 资源未找到
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取问题 {issue_id} 详情，IP: {client_ip}")
    
    try:
        # 获取问题详情
        issue_service = IssueService(db)
        issue = issue_service.get_issue_detail(issue_id)
        
        if issue is None:
            logger.warning(f"问题 {issue_id} 不存在")
            raise ResourceNotFound(message="问题不存在")
        
        # 验证项目访问权限
        # 如果issue是字典，直接获取project_id键值
        project_id = issue.get("project_id") if isinstance(issue, dict) else issue.project_id
        has_project_access = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_project_access:
            logger.warning(f"用户 {current_user.username} 无权访问项目 {project_id}")
            raise AuthorizationError(message="无权访问此项目中的问题")
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 获取问题 {issue_id} 详情成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=issue,
            message="获取问题详情成功"
        )
    except (ResourceNotFound, AuthorizationError):
        # 重新抛出资源未找到和权限错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取问题 {issue_id} 详情失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取问题详情失败", detail=str(e))

@router.patch("/{issue_id}/status", response_model=Response[IssueDetail])
async def update_issue_status(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    status_data: StatusUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueDetail]:
    """
    更新问题状态
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        status_data (StatusUpdate): 状态更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueDetail]: 更新后的问题详情
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 资源未找到
        BusinessError: 业务错误
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求更新问题 {issue_id} 状态为 {status_data.status}，IP: {client_ip}")
    
    try:
        # 获取问题信息
        issue_service = IssueService(db)
        issue = issue_service.get_issue_detail(issue_id)
        
        if issue is None:
            logger.warning(f"问题 {issue_id} 不存在")
            raise ResourceNotFound(message="问题不存在")
        
        # 验证项目访问权限
        # 如果issue是字典，直接获取project_id键值
        project_id = issue.get("project_id") if isinstance(issue, dict) else issue.project_id
        has_project_access = check_project_permission(db, current_user.id, project_id, 'update')
        if not has_project_access:
            logger.warning(f"用户 {current_user.username} 无权访问项目 {project_id}")
            raise AuthorizationError(message="无权访问此项目中的问题")
        
        # 更新问题状态
        updated_issue = issue_service.update_issue_status({
            "issue_id": issue_id,
            "status": status_data.status,
            "user_id": current_user.id
        })
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 更新问题 {issue_id} 状态成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=updated_issue,
            message="更新问题状态成功"
        )
    except (ResourceNotFound, AuthorizationError, BusinessError):
        # 重新抛出资源未找到、权限错误和业务错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"更新问题 {issue_id} 状态失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="更新问题状态失败", detail=str(e))

@router.post("/{issue_id}/comments", response_model=Response[CommentResponse])
async def add_issue_comment(
    request: Request,
    issue_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    issue_service: IssueService = Depends(get_issue_service)
) -> Response[CommentResponse]:
    """
    添加问题评论
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        comment_data (CommentCreate): 评论数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        issue_service (IssueService): 问题服务
        
    Returns:
        Response[CommentResponse]: 评论添加响应
    """
    start_time = time.time()
    try:
        # 获取issue信息，检查权限
        issue = issue_service.get_issue_detail(issue_id)
        
        # 如果issue是字典，直接获取project_id键值
        project_id = issue.get("project_id") if isinstance(issue, dict) else issue.project_id
        has_project_access = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_project_access:
            logger.warning(f"用户 {current_user.username} 无权访问项目 {project_id}")
            raise AuthorizationError(message="无权访问此项目中的问题")
        
        # 添加评论
        comment = issue_service.add_comment({
            "issue_id": issue_id,
            "content": comment_data.content,
            "file_path": comment_data.file_path,
            "line_number": comment_data.line_number,
            "user_id": current_user.id
        })
        
        # 将评论对象转换为字典，处理嵌套的用户对象
        comment_dict = {
            "id": comment.id,
            "issue_id": comment.issue_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "file_path": comment.file_path,
            "line_number": comment.line_number,
            "created_at": comment.created_at,
            "user": {
                "id": current_user.id,
                "username": current_user.username,
                "user_id": getattr(current_user, "user_id", "")
            }
        }
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 给问题 {issue_id} 添加评论成功，评论ID: {comment.id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=comment_dict,
            message="添加评论成功"
        )
    except (ResourceNotFound, AuthorizationError):
        # 重新抛出资源未找到和权限错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"给问题 {issue_id} 添加评论失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="添加评论失败", detail=str(e))

@router.get("/{issue_id}/comments", response_model=Response[List[CommentResponse]])
async def get_issue_comments(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[CommentResponse]]:
    """
    获取问题评论列表
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[CommentResponse]]: 评论列表响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 资源未找到
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取问题 {issue_id} 的评论列表，IP: {client_ip}")
    
    try:
        # 获取问题信息
        issue_service = IssueService(db)
        issue = issue_service.get_issue_detail(issue_id)
        
        if issue is None:
            logger.warning(f"问题 {issue_id} 不存在")
            raise ResourceNotFound(message="问题不存在")
        
        # 验证项目访问权限
        # 如果issue是字典，直接获取project_id键值
        project_id = issue.get("project_id") if isinstance(issue, dict) else issue.project_id
        has_project_access = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_project_access:
            logger.warning(f"用户 {current_user.username} 无权访问项目 {project_id}")
            raise AuthorizationError(message="无权访问此项目中的问题")
        
        # 获取评论列表
        comments = issue_service.get_comments(issue_id=issue_id)
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 获取问题 {issue_id} 评论列表成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=comments,
            message="获取评论列表成功"
        )
    except (ResourceNotFound, AuthorizationError):
        # 重新抛出资源未找到和权限错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取问题 {issue_id} 评论列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取评论列表失败", detail=str(e))

@router.get("/{issue_id}/history", response_model=Response[List[Dict[str, Any]]])
async def get_issue_history(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取问题历史记录
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 历史记录列表响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 资源未找到
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取问题 {issue_id} 的历史记录，IP: {client_ip}")
    
    try:
        # 获取问题信息
        issue_service = IssueService(db)
        issue = issue_service.get_issue_detail(issue_id)
        
        if issue is None:
            logger.warning(f"问题 {issue_id} 不存在")
            raise ResourceNotFound(message="问题不存在")
        
        # 验证项目访问权限
        # 如果issue是字典，直接获取project_id键值
        project_id = issue.get("project_id") if isinstance(issue, dict) else issue.project_id
        has_project_access = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_project_access:
            logger.warning(f"用户 {current_user.username} 无权访问项目 {project_id}")
            raise AuthorizationError(message="无权访问此项目中的问题")
        
        # 获取历史记录
        history = issue_service.get_issue_history(issue_id=issue_id)
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 获取问题 {issue_id} 历史记录成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=history,
            message="获取历史记录成功"
        )
    except (ResourceNotFound, AuthorizationError):
        # 重新抛出资源未找到和权限错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取问题 {issue_id} 历史记录失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取历史记录失败", detail=str(e))

@router.post("/batch-update", response_model=Response[Dict[str, Any]])
async def batch_update_issues(
    request: Request,
    update_data: IssueBatchUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    批量更新问题
    
    Args:
        request (Request): 请求对象
        update_data (IssueBatchUpdate): 批量更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 更新结果
        
    Raises:
        AuthorizationError: 权限不足
        BusinessError: 业务错误
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求批量更新问题，问题IDs: {update_data.issue_ids}，IP: {client_ip}")
    
    try:
        # 验证项目访问权限
        if update_data.project_id:
            has_project_access = check_project_permission(db, current_user.id, update_data.project_id, 'update')
            if not has_project_access:
                logger.warning(f"用户 {current_user.username} 无权访问项目 {update_data.project_id}")
                raise AuthorizationError(message="无权访问此项目")
        
        # 批量更新问题
        issue_service = IssueService(db)
        result = issue_service.batch_update_issues({
            "issue_ids": update_data.issue_ids,
            "status": update_data.status,
            "priority": update_data.priority,
            "assignee_id": update_data.assignee_id,
            "tags": update_data.tags,
            "user_id": current_user.id
        })
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 批量更新问题成功，更新 {result.get('updated_count', 0)} 个问题，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=result,
            message="批量更新问题成功"
        )
    except AuthorizationError:
        # 重新抛出权限错误
        raise
    except BusinessError as e:
        logger.warning(f"批量更新问题业务错误: {str(e)}")
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"批量更新问题失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="批量更新问题失败", detail=str(e))

@router.post("/tags", response_model=Response[IssueTagResponse], status_code=status.HTTP_201_CREATED)
async def create_issue_tag(
    request: Request,
    tag_data: IssueTagCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueTagResponse]:
    """
    创建问题标签
    
    Args:
        request (Request): 请求对象
        tag_data (IssueTagCreate): 标签创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueTagResponse]: 创建的标签响应
        
    Raises:
        BusinessError: 业务错误
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求创建问题标签 '{tag_data.name}'，IP: {client_ip}")
    
    try:
        issue_service = IssueService(db)
        tag = issue_service.create_tag({
            "name": tag_data.name,
            "color": tag_data.color,
            "description": tag_data.description,
            "creator_id": current_user.id
        })
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 创建问题标签 '{tag_data.name}' 成功，标签ID: {tag.id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=tag,
            message="创建问题标签成功"
        )
    except BusinessError as e:
        logger.warning(f"创建问题标签业务错误: {str(e)}")
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"创建问题标签失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="创建问题标签失败", detail=str(e))

@router.get("/tags", response_model=Response[List[IssueTagResponse]])
async def get_issue_tags(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[IssueTagResponse]]:
    """
    获取问题标签列表
    
    Args:
        request (Request): 请求对象
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[IssueTagResponse]]: 标签列表响应
        
    Raises:
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取问题标签列表，IP: {client_ip}")
    
    try:
        issue_service = IssueService(db)
        tags = issue_service.get_tags()
        
        process_time = time.time() - start_time
        logger.info(f"获取问题标签列表成功，共 {len(tags)} 个标签，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=tags,
            message="获取问题标签列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取问题标签列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取问题标签列表失败", detail=str(e))

@router.delete("/tags/{tag_id}", response_model=Response)
async def delete_issue_tag(
    request: Request,
    tag_id: int = Path(..., description="标签ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    删除问题标签
    
    Args:
        request (Request): 请求对象
        tag_id (int): 标签ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 操作结果响应
        
    Raises:
        ResourceNotFound: 标签不存在
        BusinessError: 标签正在使用中
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求删除问题标签 {tag_id}，IP: {client_ip}")
    
    try:
        issue_service = IssueService(db)
        result = issue_service.delete_tag(tag_id)
        
        process_time = time.time() - start_time
        logger.info(f"删除问题标签 {tag_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=result,
            message="删除问题标签成功"
        )
    except ResourceNotFound as e:
        process_time = time.time() - start_time
        logger.warning(f"删除问题标签失败，资源不存在: {str(e)}, 处理时间: {process_time:.2f}秒")
        raise
    except BusinessError as e:
        process_time = time.time() - start_time
        logger.warning(f"删除问题标签失败，业务错误: {str(e)}, 处理时间: {process_time:.2f}秒")
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"删除问题标签失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="删除问题标签失败", detail=str(e))

@router.get("/{issue_id}/commits", response_model=Response[List[Dict[str, Any]]])
@require_permission("issue:view")
async def get_issue_commits(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取问题相关的代码提交记录
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 代码提交记录列表
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 资源未找到
        DatabaseError: 数据库错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取问题 {issue_id} 的提交记录，IP: {client_ip}")
    
    try:
        # 首先获取问题并验证问题存在
        issue_service = IssueService(db)
        issue_detail = issue_service.get_issue_detail(issue_id)
        
        # 获取问题相关的提交记录
        commits = issue_service.get_issue_commits(issue_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取问题 {issue_id} 提交记录成功，找到 {len(commits)} 条记录，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=commits,
            message="获取问题相关提交记录成功"
        )
    except ResourceNotFound:
        # 重新抛出资源不存在错误
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取问题 {issue_id} 提交记录失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取问题提交记录失败", detail=str(e))

@router.put("/{issue_id}", response_model=Response[IssueDetail])
async def update_issue(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    issue_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueDetail]:
    """
    更新问题所有信息
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        issue_data (dict): 问题更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueDetail]: 更新后的问题详情
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求更新问题 {issue_id}，IP: {client_ip}")
    
    try:
        # 获取问题信息
        issue_service = IssueService(db)
        issue = issue_service.get_issue_detail(issue_id)
        
        if issue is None:
            logger.warning(f"问题 {issue_id} 不存在")
            raise ResourceNotFound(message="问题不存在")
        
        # 验证项目访问权限
        project_id = issue.get("project_id") if isinstance(issue, dict) else issue.project_id
        has_project_access = check_project_permission(db, current_user.id, project_id, 'update')
        if not has_project_access:
            logger.warning(f"用户 {current_user.username} 无权更新项目 {project_id} 的问题")
            raise AuthorizationError(message="无权更新此项目中的问题")
        
        # 如果尝试更新项目ID，需要验证对新项目的访问权限
        if issue_data.get("project_id") and issue_data.get("project_id") != project_id:
            has_new_project_access = check_project_permission(db, current_user.id, issue_data.get("project_id"), 'update')
            if not has_new_project_access:
                logger.warning(f"用户 {current_user.username} 无权将问题转移到项目 {issue_data.get('project_id')}")
                raise AuthorizationError(message="无权将问题转移到目标项目")
        
        # 更新问题
        issue_data["issue_id"] = issue_id
        issue_data["user_id"] = current_user.id
        
        updated_issue = issue_service.update_issue(issue_data)
        
        process_time = time.time() - start_time
        logger.info(f"用户 {current_user.username} 更新问题 {issue_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=updated_issue,
            message="更新问题成功"
        )
    except (ResourceNotFound, AuthorizationError, BusinessError) as e:
        raise e
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"更新问题 {issue_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="更新问题失败", detail=str(e))