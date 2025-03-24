"""
代码审查路由模块
@author: pgao
@date: 2024-03-13
"""
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Request, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import time
import traceback
import logging
from sqlalchemy import or_

from app.database import get_db
from app.services.issue_service import IssueService
from app.models.user import User
from app.models.project import Project
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError
from app.schemas.response import Response, PageResponse
from app.schemas.issue import CodeReviewIssueCreate, IssueDetail, StatusUpdate
from app.schemas.comment import CommentCreate, CommentResponse
from app.config.logging_config import logger
from app.core.security import get_current_user, require_permission

# 依赖函数：获取IssueService实例
def get_issue_service(db: Session = Depends(get_db)) -> IssueService:
    """
    获取IssueService实例的依赖函数
    
    Args:
        db (Session): 数据库会话
        
    Returns:
        IssueService: IssueService实例
    """
    return IssueService(db)

# 依赖函数：获取logger实例
def get_logger() -> logging.Logger:
    """
    获取logger实例的依赖函数
    
    Returns:
        logging.Logger: logger实例
    """
    return logger

# 创建路由器
router = APIRouter(
    prefix="/api/v1/code-reviews", 
    tags=["代码审查"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

@router.post("/issues", response_model=Response[IssueDetail], status_code=status.HTTP_201_CREATED)
async def create_review_issue(
    request: Request,
    review_data: CodeReviewIssueCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueDetail]:
    """
    创建代码检视问题
    
    Args:
        request (Request): 请求对象
        review_data (CodeReviewIssueCreate): 代码检视问题创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueDetail]: 代码检视问题创建响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求创建项目 {review_data.project_id} 的代码检视问题，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 创建代码检视问题
        review_issue = service.create_code_review_issue({
            "project_id": review_data.project_id,
            "commit_id": review_data.commit_id,
            "file_path": review_data.file_path,
            "line_start": review_data.line_start,
            "line_end": review_data.line_end,
            "title": review_data.title,
            "description": review_data.description,
            "issue_type": review_data.issue_type,
            "severity": review_data.severity,
            "priority": review_data.priority,
            "creator_id": current_user.id,
            "assignee_id": review_data.assignee_id
        })
        
        # 获取问题详情
        issue_detail = service.get_issue_detail(review_issue.id)
        
        process_time = time.time() - start_time
        logger.info(f"创建代码检视问题成功，ID: {review_issue.id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=issue_detail,
            message="代码检视问题创建成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError) as e:
        logger.warning(f"创建代码检视问题错误: {str(e)}")
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"创建代码检视问题失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="创建代码检视问题失败", detail=str(e))

@router.get("/issues", response_model=Response[PageResponse[Dict[str, Any]]])
async def get_review_issues(
    request: Request,
    project_id: Optional[int] = Query(None, description="项目ID"),
    creator_id: Optional[int] = Query(None, description="创建人ID"),
    assignee_id: Optional[int] = Query(None, description="指派人ID"),
    severity: Optional[str] = Query(None, description="严重程度"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[PageResponse[Dict[str, Any]]]:
    """
    获取代码检视问题列表
    
    Args:
        request (Request): 请求对象
        project_id (Optional[int]): 项目ID
        creator_id (Optional[int]): 创建人ID
        assignee_id (Optional[int]): 指派人ID
        severity (Optional[str]): 严重程度
        status (Optional[str]): 状态
        page (int): 页码
        page_size (int): 每页数量
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[PageResponse[Dict[str, Any]]]: 问题列表分页响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取代码检视问题列表，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 使用当前用户ID调用get_code_review_issues方法，同时传入user_id参数用于基于权限的过滤，
        # 及current_user_id参数用于基于角色的过滤
        issues, total = service.get_code_review_issues(
            project_id=project_id,
            creator_id=creator_id,
            assignee_id=assignee_id,
            severity=severity,
            status=status,
            page=page,
            page_size=page_size,
            user_id=current_user.id,           # 用于基于权限的过滤
            current_user_id=current_user.id    # 用于基于角色的过滤
        )
        
        # 构建分页响应
        paginated_response = PageResponse.create(
            items=issues,
            total=total,
            page=page,
            page_size=page_size
        )
        
        process_time = time.time() - start_time
        logger.info(f"获取代码检视问题列表成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=paginated_response,
            message="获取代码检视问题列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取代码检视问题列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取代码检视问题列表失败", detail=str(e))

@router.get("/issues/{issue_id}", response_model=Response[IssueDetail])
async def get_review_issue_detail(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueDetail]:
    """
    获取代码检视问题详情
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueDetail]: 代码检视问题详情响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取代码检视问题 {issue_id} 详情，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 获取问题详情
        issue = service.get_issue_detail(issue_id)
        
        if issue is None:
            raise ResourceNotFound(message="问题不存在")
        
        # 验证问题类型，使用更安全的字典访问方式
        issue_type = issue.get('issue_type', 'unknown')
        if issue_type != "code_review" and issue_type != "unknown":
            logger.warning(f"问题ID {issue_id} 不是代码审查问题，当前类型: {issue_type}")
            raise BusinessError(message="该问题不是代码检视问题")
        
        process_time = time.time() - start_time
        logger.info(f"获取代码检视问题 {issue_id} 详情成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=issue,
            message="获取代码检视问题详情成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError) as e:
        logger.warning(f"获取代码检视问题详情错误: {str(e)}")
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取代码检视问题 {issue_id} 详情失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取代码检视问题详情失败", detail=str(e))

@router.patch("/issues/{issue_id}/status", response_model=Response[IssueDetail])
async def update_review_issue_status(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    status_data: StatusUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[IssueDetail]:
    """
    更新代码检视问题状态
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        status_data (StatusUpdate): 状态更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[IssueDetail]: 更新后的代码检视问题详情
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求更新代码检视问题 {issue_id} 状态为 {status_data.status}，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 获取问题详情
        issue = service.get_issue_detail(issue_id)
        
        if issue is None:
            raise ResourceNotFound(message="问题不存在")
        
        # 验证问题类型，使用更安全的字典访问方式
        issue_type = issue.get('issue_type', 'unknown')
        if issue_type != "code_review":
            logger.warning(f"问题ID {issue_id} 不是代码审查问题，当前类型: {issue_type}")
            raise BusinessError(message="该问题不是代码检视问题")
        
        # 更新问题状态
        updated_issue = service.update_issue_status({
            "issue_id": issue_id,
            "status": status_data.status,
            "user_id": current_user.id
        })
        
        process_time = time.time() - start_time
        logger.info(f"更新代码检视问题 {issue_id} 状态成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=updated_issue,
            message="更新代码检视问题状态成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"更新代码检视问题 {issue_id} 状态失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="更新代码检视问题状态失败", detail=str(e))

@router.post("/issues/{issue_id}/comments", response_model=Response[CommentResponse])
async def add_review_issue_comment(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    comment_data: CommentCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[CommentResponse]:
    """
    添加代码检视问题评论
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        comment_data (CommentCreate): 评论创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[CommentResponse]: 评论创建响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求为代码检视问题 {issue_id} 添加评论，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 获取问题详情
        issue = service.get_issue_detail(issue_id)
        
        if issue is None:
            raise ResourceNotFound(message="问题不存在")
        
        # 验证问题类型，使用更安全的字典访问方式
        issue_type = issue.get('issue_type', 'unknown')
        if issue_type != "code_review":
            logger.warning(f"问题ID {issue_id} 不是代码审查问题，当前类型: {issue_type}")
            raise BusinessError(message="该问题不是代码检视问题")
        
        # 添加评论
        comment = service.add_comment({
            "issue_id": issue_id,
            "content": comment_data.content,
            "user_id": current_user.id,
            "file_path": comment_data.file_path,
            "line_number": comment_data.line_number
        })
        
        process_time = time.time() - start_time
        logger.info(f"为代码检视问题 {issue_id} 添加评论成功，评论ID: {comment['id'] if isinstance(comment, dict) else comment.id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=comment,
            message="添加评论成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"为代码检视问题 {issue_id} 添加评论失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="添加评论失败", detail=str(e))

@router.get("/issues/{issue_id}/comments", response_model=Response[List[CommentResponse]])
async def get_review_issue_comments(
    request: Request,
    issue_id: int = Path(..., description="问题ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[CommentResponse]]:
    """
    获取代码检视问题评论列表
    
    Args:
        request (Request): 请求对象
        issue_id (int): 问题ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[CommentResponse]]: 评论列表响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取代码检视问题 {issue_id} 的评论列表，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 获取问题详情，验证问题是否存在
        issue = service.get_issue_detail(issue_id)
        
        if issue is None:
            raise ResourceNotFound(message="问题不存在")
        
        # 不再验证问题类型，直接获取评论列表
        comments = service.get_comments(issue_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取代码检视问题 {issue_id} 评论列表成功，共 {len(comments)} 条评论，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=comments,
            message="获取评论列表成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError) as e:
        logger.warning(f"获取评论列表错误: {str(e)}")
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取代码检视问题 {issue_id} 评论列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取评论列表失败", detail=str(e))

@router.get("/commit/{commit_id}/issues", response_model=Response[List[Dict[str, Any]]])
async def get_commit_review_issues(
    request: Request,
    commit_id: int = Path(..., description="提交ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取提交关联的代码检视问题列表
    
    Args:
        request (Request): 请求对象
        commit_id (int): 提交ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 问题列表响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取提交 {commit_id} 的代码检视问题列表，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 导入ProjectRole模型，用于权限过滤
        from app.models.project_role import ProjectRole
        
        # 获取用户有权限访问的项目ID列表
        user_project_ids_query = (
            db.query(Project.id)
            .filter(
                or_(
                    Project.created_by == current_user.id,  # 用户创建的项目
                    Project.id.in_(  # 用户有角色的项目
                        db.query(ProjectRole.project_id)
                        .filter(
                            ProjectRole.user_id == current_user.id,
                            ProjectRole.is_active == True
                        )
                    )
                )
            )
        )
        
        # 执行查询获取项目ID列表
        user_project_ids = [row[0] for row in user_project_ids_query.all()]
        
        # 获取提交关联的问题列表，并过滤只返回用户有权限的项目中的问题
        issues = []
        commit_issues = service.get_commit_issues(commit_id)
        
        if not commit_issues:
            return Response(
                data=[],
                message="未找到提交关联的代码检视问题"
            )
        
        # 获取所有问题ID
        issue_ids = [issue.id for issue in commit_issues]
        
        # 一次性查询所有问题详情
        issue_details = []
        for issue in commit_issues:
            # 只处理用户有权限的项目中的问题
            if not user_project_ids or issue.project_id in user_project_ids:
                detail = service.get_issue_detail(issue.id)
                if detail:
                    issue_details.append(detail)
        
        process_time = time.time() - start_time
        logger.info(f"获取提交 {commit_id} 的代码检视问题列表成功，共 {len(issue_details)} 条记录，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=issue_details,
            message="获取提交关联的代码检视问题列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取提交 {commit_id} 的代码检视问题列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取提交关联的代码检视问题列表失败", detail=str(e))

@router.get("", response_model=Response[PageResponse[Dict[str, Any]]])
async def get_code_reviews(
    request: Request,
    project_id: Optional[int] = Query(None, description="项目ID"),
    creator_id: Optional[int] = Query(None, description="创建人ID"),
    assignee_id: Optional[int] = Query(None, description="指派人ID"),
    severity: Optional[str] = Query(None, description="严重程度"),
    status: Optional[str] = Query(None, description="状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[PageResponse[Dict[str, Any]]]:
    """
    获取代码审查列表
    
    Args:
        request (Request): 请求对象
        project_id (Optional[int]): 项目ID过滤
        creator_id (Optional[int]): 创建者ID过滤
        assignee_id (Optional[int]): 指派人ID过滤
        severity (Optional[str]): 严重程度过滤
        status (Optional[str]): 状态过滤
        page (int): 页码
        page_size (int): 每页数量
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[PageResponse[Dict[str, Any]]]: 代码审查列表分页响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取代码审查列表，IP: {client_ip}")
    
    try:
        service = IssueService(db)
        
        # 使用当前用户ID调用get_code_review_issues方法，同时传入user_id参数用于基于权限的过滤，
        # 及current_user_id参数用于基于角色的过滤
        issues, total = service.get_code_review_issues(
            project_id=project_id,
            creator_id=creator_id,
            assignee_id=assignee_id,
            severity=severity,
            status=status,
            page=page,
            page_size=page_size,
            user_id=current_user.id,           # 用于基于权限的过滤
            current_user_id=current_user.id    # 用于基于角色的过滤
        )
        
        # 构建分页响应
        paginated_response = PageResponse.create(
            items=issues,
            total=total,
            page=page,
            page_size=page_size
        )
        
        process_time = time.time() - start_time
        logger.info(f"获取代码审查列表成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=paginated_response,
            message="获取代码审查列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取代码审查列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取代码审查列表失败", detail=str(e))