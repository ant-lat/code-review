"""
项目管理路由模块
@author: pgao
@date: 2024-03-13
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import time
import traceback

from app.database import get_db
from app.services.project_service import ProjectService
from app.core.security import get_current_user
from app.models.user import User
from app.core.exceptions import BusinessError, DatabaseError, ResourceNotFound, AuthorizationError, ValidationError
from app.schemas.response import Response
from app.config.logging_config import logger
from pydantic import BaseModel
from app.services.role_service import RoleService
from app.services.permission_service import PermissionService
from app.services.issue_service import IssueService
from app.services.review_service import ReviewService
from app.services.analysis_service import CodeAnalysisService

def check_permission(db: Session, user_id: int, permission_code: str) -> bool:
    """
    检查用户是否具有指定权限
    
    Args:
        db (Session): 数据库会话
        user_id (int): 用户ID
        permission_code (str): 权限代码
        
    Returns:
        bool: 用户是否具有指定权限
    """
    try:
        # 使用权限服务检查用户权限
        permission_service = PermissionService(db)
        return permission_service.check_user_permission(user_id, permission_code)
    except Exception as e:
        logger.error(f"检查用户 {user_id} 权限 {permission_code} 失败: {str(e)}")
        # 出现异常时，默认为无权限
        return False

def check_project_permission(db: Session, user_id: int, project_id: int, action: str) -> bool:
    """
    检查用户是否具有项目相关权限
    
    Args:
        db (Session): 数据库会话
        user_id (int): 用户ID
        project_id (int): 项目ID
        action (str): 操作类型，可选值：'view', 'admin', 'member'
        
    Returns:
        bool: 用户是否有权限
    """
    try:
        permission_service = PermissionService(db)

        # 检查用户是否有全局权限
        if action == 'view':
            global_perm = permission_service.check_user_permission(user_id, "project:view_all")
            if global_perm:
                return True
        elif action == 'admin':
            # 检查是否是系统管理员 (角色id=1)
            if permission_service.check_user_role(user_id, 1):
                return True
                
            # 检查是否有全局项目管理权限
            global_perm = permission_service.check_user_permission(user_id, "project:manage_all")
            if global_perm:
                return True
        
        # 检查用户项目权限
        if action == 'view':
            # 只需要是项目成员
            return permission_service.check_project_member(user_id, project_id)
        elif action == 'admin':
            # 需要是项目管理员
            return permission_service.check_project_admin(user_id, project_id)
        elif action == 'member':
            # 需要是项目成员
            return permission_service.check_project_member(user_id, project_id)
        elif action == 'update':
            # 需要是项目成员
            return permission_service.check_project_member(user_id, project_id)
        else:
            logger.warning(f"未知的项目权限操作类型: {action}")
            return False
    except Exception as e:
        logger.error(f"检查项目权限失败: 用户 {user_id}, 项目 {project_id}, 操作 {action}, 错误: {str(e)}")
        return False

# 创建路由器
router = APIRouter(
    prefix="/api/v1/projects", 
    tags=["项目管理"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"}, 
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

class ProjectCreate(BaseModel):
    """项目创建请求模型"""
    name: str
    description: Optional[str] = ""
    repository_url: str
    repository_type: Optional[str] = "git"
    branch: Optional[str] = "main"

class ProjectResponse(BaseModel):
    """项目响应模型"""
    id: int
    name: str
    description: Optional[str] = None
    repository_url: str
    repository_type: str
    branch: str
    is_active: bool
    created_by: int
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ProjectMemberCreate(BaseModel):
    """项目成员创建请求模型"""
    user_id: int
    role_id: int

class ProjectMemberResponse(BaseModel):
    """项目成员响应模型"""
    user_id: int
    username: str
    role_id: int
    role_name: str
    is_active: bool
    joined_at: Optional[str] = None

class ProjectRoleAssignRequest(BaseModel):
    user_id: int
    role_id: int

class ProjectUpdate(BaseModel):
    """项目更新请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    repository_type: Optional[str] = None
    branch: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("", response_model=Response[ProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    request: Request,
    project_data: ProjectCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[ProjectResponse]:
    """
    创建项目
    
    Args:
        request (Request): 请求对象
        project_data (ProjectCreate): 项目创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns: 
        Response[ProjectResponse]: 项目创建响应
        
    Raises:
        AuthorizationError: 权限不足
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求创建项目 {project_data.name}，IP: {client_ip}")
    
    try:
        # 检查用户是否有权限创建项目
        if not check_permission(db, current_user.id, "project:create"):
            logger.warning(f"用户 {current_user.username} 尝试创建项目，但权限不足")
            raise AuthorizationError(message="无项目创建权限")
        
        service = ProjectService(db)
        new_project = service.create_project({
            "name": project_data.name,
            "description": project_data.description,
            "creator_id": current_user.id,
            "repository_url": project_data.repository_url,
            "repository_type": project_data.repository_type,
            "branch": project_data.branch,
            "is_active": True
        })
        
        # 格式化响应
        response_data = ProjectResponse(
            id=new_project.id,
            name=new_project.name,
            description=new_project.description,
            repository_url=new_project.repository_url,
            repository_type=new_project.repository_type,
            branch=new_project.branch,
            is_active=new_project.is_active,
            created_by=new_project.created_by,
            creator_name=new_project.creator.username if new_project.creator else None,
            created_at=new_project.created_at,
            updated_at=new_project.updated_at
        )
        
        process_time = time.time() - start_time
        logger.info(f"创建项目成功，ID: {new_project.id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="项目创建成功"
        )
    except AuthorizationError:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"创建项目失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="创建项目失败", detail=str(e))

@router.get("", response_model=Response[Dict[str, Any]])
async def get_projects(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(None, description="项目名称"),
    is_active: Optional[bool] = Query(None, description="项目状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取项目列表
    
    Args:
        request (Request): 请求对象
        page (int): 页码
        page_size (int): 每页数量
        name (str, optional): 按名称筛选
        is_active (bool, optional): 按项目状态筛选
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 项目列表响应
        
    Raises:
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目列表，页码: {page}，每页数量: {page_size}，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 构建过滤条件
        filters = {}
        if name:
            filters["name"] = name
        if is_active is not None:
            filters["is_active"] = is_active
            
        # 是否仅显示用户参与的项目
        only_user_projects = not check_permission(db, current_user.id, "project:view")
        if only_user_projects:
            filters["user_id"] = current_user.id
        
        projects, total = service.get_projects(filters, page=page, page_size=page_size)
        
        # 格式化响应
        project_list = []
        for project in projects:
            project_list.append({
                "id": project["id"],
                "name": project["name"],
                "description": project["description"],
                "repository_url": project["repository_url"],
                "repository_type": project["repository_type"],
                "branch": project["branch"],
                "status": project["is_active"],
                "member_count": project["member_count"],
                "creator": project["creator"],
                "latest_analysis": project["latest_analysis"],
                "created_at": project["created_at"],
                "updated_at": project["updated_at"],
            })
        
        process_time = time.time() - start_time
        logger.info(f"获取项目列表成功，总数: {total}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data={
                "items": project_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "pages": (total + page_size - 1) // page_size
            },
            message="获取项目列表成功"
        )
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取项目列表失败", detail=str(e))

@router.get("/{project_id}", response_model=Response[ProjectResponse])
async def get_project(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[ProjectResponse]:
    """
    获取项目详情
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[ProjectResponse]: 项目详情响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 详情，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 检查用户是否可以访问此项目
        has_permission = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_permission:
            logger.warning(f"用户 {current_user.username} 尝试获取项目 {project_id} 详情，但权限不足")
            raise AuthorizationError(message="无权访问此项目")
        
        project = service.get_project_by_id(project_id)
        
        # 格式化响应
        response_data = ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            repository_url=project.repository_url,
            repository_type=project.repository_type,
            branch=project.branch,
            is_active=project.is_active,
            created_by=project.created_by,
            creator_name=project.creator.username if project.creator else None,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        
        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 详情成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="获取项目详情成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 详情失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取项目详情失败", detail=str(e))

@router.get("/{project_id}/members", response_model=Response[List[ProjectMemberResponse]])
async def get_project_members(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[ProjectMemberResponse]]:
    """
    获取项目成员列表
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[ProjectMemberResponse]]: 项目成员列表响应
        
    Raises:
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 成员列表，IP: {client_ip}")
    
    try:
        # 确保project_id是整数
        try:
            project_id_int = int(project_id)
        except (ValueError, TypeError):
            raise ValidationError(message=f"无效的项目ID: {project_id}，必须是整数")
            
        service = ProjectService(db)
        
        # 获取项目成员列表
        members = service.get_project_members(project_id_int)
        
        # 将成员数据转换为响应模型格式
        response_data = []
        for member in members:
            response_data.append(ProjectMemberResponse(
                user_id=member["user_id"],
                username=member["username"],
                role_id=member["role_id"],
                role_name=member["role_name"],
                is_active=member["is_active"],
                joined_at=member["joined_at"]
            ))

        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 成员列表成功，共 {len(response_data)} 个成员，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="获取项目成员列表成功"
        )
    except ResourceNotFound:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 成员列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取项目成员列表失败", detail=str(e))

@router.post("/{project_id}/members", response_model=Response[ProjectMemberResponse])
async def add_project_member(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    member_data: ProjectMemberCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[ProjectMemberResponse]:
    """
    添加项目成员
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        member_data (ProjectMemberCreate): 成员创建数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[ProjectMemberResponse]: 项目成员创建响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目或用户不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求向项目 {project_id} 添加成员 {member_data.user_id}，角色: {member_data.role_id}，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 检查项目操作权限
        has_admin_permission = check_project_permission(db, current_user.id, project_id, 'admin')
        if not has_admin_permission:
            logger.warning(f"用户 {current_user.username} 尝试向项目 {project_id} 添加成员，但权限不足")
            raise AuthorizationError(message="无项目成员管理权限")
        
        # 添加项目成员
        new_member = service.add_project_member(project_id, member_data.user_id, member_data.role_id)
        
        # 创建响应数据
        response_data = ProjectMemberResponse(
            user_id=new_member["user_id"],
            username=new_member["username"],
            role_id=new_member["role_id"],
            role_name=new_member["role_name"],
            is_active=new_member["is_active"],
            joined_at=new_member["joined_at"]
        )
        
        process_time = time.time() - start_time
        logger.info(f"向项目 {project_id} 添加成员成功，用户ID: {member_data.user_id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="成员添加成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"向项目 {project_id} 添加成员失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        if "Duplicate entry" in str(e) or "project_user_role_unique" in str(e):
            raise BusinessError(message="该用户已经拥有指定角色，无需重复添加")
        raise DatabaseError(message="添加项目成员失败", detail=str(e))

@router.delete("/{project_id}/users/{user_id}", response_model=Response)
async def remove_project_member(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    user_id: int = Path(..., description="用户ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    移除项目成员
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        user_id (int): 用户ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response: 移除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目或成员不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求从项目 {project_id} 移除成员 {user_id}，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 检查项目操作权限
        has_admin_permission = check_project_permission(db, current_user.id, project_id, 'admin')
        if not has_admin_permission:
            logger.warning(f"用户 {current_user.username} 尝试从项目 {project_id} 移除成员，但权限不足")
            raise AuthorizationError(message="无项目成员管理权限")
        
        # 不能移除自己
        if current_user.id == user_id:
            logger.warning(f"用户 {current_user.username} 尝试从项目 {project_id} 移除自己")
            raise BusinessError(message="不能移除自己的项目成员资格")
            
        service.remove_project_member(project_id, user_id)
        
        process_time = time.time() - start_time
        logger.info(f"从项目 {project_id} 移除成员 {user_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="成员移除成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"从项目 {project_id} 移除成员 {user_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="移除项目成员失败", detail=str(e))

@router.get("/{project_id}/stats", response_model=Response[Dict[str, Any]])
async def get_project_stats(
    request: Request,
    project_id: int = Path(..., title="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取项目统计信息
    
    Args:
        project_id (int): 项目ID
        
    Returns:
        Response: 项目统计信息
    """
    try:
        # 检查项目访问权限
        has_permission = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_permission:
            logger.warning(f"用户 {current_user.username} 尝试获取项目 {project_id} 详情，但权限不足")
            raise AuthorizationError(message="无权访问此项目")
        
        # 初始化服务
        project_service = ProjectService(db)
        issue_service = IssueService(db)
        review_service = ReviewService(db)
        code_analysis_service = CodeAnalysisService(db)
        
        # 获取项目信息
        project = project_service.get_project_by_id(project_id)
        
        # 获取项目统计信息
        issue_count = issue_service.get_issue_count(project_id=project_id)
        open_issue_count = issue_service.get_issue_count(
            project_id=project_id, 
            status_filter=["open", "in_progress"]
        )
        
        # 获取代码审查统计信息
        review_count = review_service.count(filters={"project_id": project_id})
        
        # 获取代码分析统计信息
        analysis_count = code_analysis_service.count(filters={"project_id": project_id})
        
 # 获取成员数量
        member_count = project_service.get_member_count(project_id)
        
        # 构建响应数据
        stats = {
            "project_name": project.name,
            "issue_count": issue_count,
            "open_issue_count": open_issue_count,
            "closed_issue_count": issue_count - open_issue_count,
            "completion_rate": round((issue_count - open_issue_count) / issue_count * 100, 2) if issue_count > 0 else 0,
            "review_count": review_count,
            "analysis_count": analysis_count,
            "member_count": member_count,
        }
        
        return Response(
            code=200,
            status="success",
            message="获取项目统计信息成功",
            data=stats
        )
    except ResourceNotFound as e:
        logger.warning(f"获取项目统计信息失败: {str(e)}")
        return Response(
            code=404,
            status="error",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"获取项目统计信息时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return Response(
            code=500,
            status="error",
            message="服务器内部错误"
        )

@router.get("/{project_id}/statistics", response_model=Response[Dict[str, Any]])
async def get_project_statistics(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取项目统计信息
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 项目统计信息响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 统计信息，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 检查用户是否有权限查看项目统计信息
        has_permission = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_permission:
            logger.warning(f"用户 {current_user.username} 尝试获取项目 {project_id} 统计信息，但权限不足")
            raise AuthorizationError(message="无权访问项目统计信息，需要项目成员资格")
        
        stats = service.get_project_statistics(project_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 统计信息成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=stats,
            message="获取项目统计信息成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 统计信息失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取项目统计信息失败", detail=str(e))

@router.get("/{project_id}/activities", response_model=Response[Dict[str, Any]])
async def get_project_activities(
    request: Request,
    project_id: int = Path(..., title="项目ID"),
    page: int = Query(1, ge=1, title="页码"),
    page_size: int = Query(10, ge=1, le=100, title="每页数量"),
    from_date: Optional[str] = Query(None, title="开始日期"),
    to_date: Optional[str] = Query(None, title="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取项目活动列表
    
    Args:
        project_id (int): 项目ID
        page (int): 页码
        page_size (int): 每页数量
        from_date (Optional[str]): 开始日期
        to_date (Optional[str]): 结束日期
        
    Returns:
        Response: 项目活动列表
    """
    try:
        # 检查项目访问权限
        # 检查用户是否有权限查看项目统计信息
        has_permission = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_permission:
            logger.warning(f"用户 {current_user.username} 尝试获取项目 {project_id} 统计信息，但权限不足")
            raise AuthorizationError(message="无权访问项目统计信息，需要项目成员资格")
        
        # 初始化服务
        project_service = ProjectService(db)
        
        # 解析日期参数
        start_date = None
        end_date = None
        
        if from_date:
            try:
                start_date = datetime.strptime(from_date, "%Y-%m-%d")
            except ValueError:
                return Response(
                    code=400,
                    status="error",
                    message="开始日期格式无效，请使用YYYY-MM-DD格式"
                )
        
        if to_date:
            try:
                end_date = datetime.strptime(to_date, "%Y-%m-%d") + timedelta(days=1)
            except ValueError:
                return Response(
                    code=400,
                    status="error",
                    message="结束日期格式无效，请使用YYYY-MM-DD格式"
                )
        
        # 获取项目活动
        filters = {
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date
        }
        
        activities = project_service.get_project_activities(
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        return Response(
            code=200,
            status="success",
            message="获取项目活动成功",
            data=activities
        )
    except ResourceNotFound as e:
        logger.warning(f"获取项目活动失败: {str(e)}")
        return Response(
            code=404,
            status="error",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"获取项目活动时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return Response(
            code=500,
            status="error",
            message="服务器内部错误"
        )


@router.get("/{project_id}/allRoles", response_model=Response[List[Dict[str, Any]]])
async def get_project_alleles(
        request: Request,
        project_id: int = Path(..., description="项目ID"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取项目可用角色列表

    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户

    Returns:
        Response[List[Dict[str, Any]]]: 项目角色列表响应

    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 角色列表，IP: {client_ip}")

    try:
        # 检查用户是否可以访问此项目
        service = ProjectService(db)

        # 检查用户是否有查看项目权限
        has_permission = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_permission:
            logger.warning(f"用户 {current_user.username} 尝试获取项目 {project_id} 角色列表，但权限不足")
            raise AuthorizationError(message="无权访问此项目角色")

        # 获取项目可用角色列表
        role_service = RoleService(db)
        project_roles = role_service.get_project_alleles(project_id)

        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 角色列表成功，共 {len(project_roles)} 个角色，处理时间: {process_time:.2f}秒")

        return Response(
            data=project_roles,
            message="获取项目角色列表成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 角色列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取项目角色列表失败", detail=str(e))
@router.get("/{project_id}/roles", response_model=Response[List[Dict[str, Any]]])
async def get_project_roles(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[List[Dict[str, Any]]]:
    """
    获取项目可用角色列表
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[List[Dict[str, Any]]]: 项目角色列表响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求获取项目 {project_id} 角色列表，IP: {client_ip}")
    
    try:
        # 检查用户是否可以访问此项目
        service = ProjectService(db)
        
        # 检查用户是否有查看项目权限
        has_permission = check_project_permission(db, current_user.id, project_id, 'view')
        if not has_permission:
            logger.warning(f"用户 {current_user.username} 尝试获取项目 {project_id} 角色列表，但权限不足")
            raise AuthorizationError(message="无权访问此项目角色")
        
        # 获取项目可用角色列表
        role_service = RoleService(db)
        project_roles = role_service.get_project_roles(project_id)
        
        process_time = time.time() - start_time
        logger.info(f"获取项目 {project_id} 角色列表成功，共 {len(project_roles)} 个角色，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=project_roles,
            message="获取项目角色列表成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"获取项目 {project_id} 角色列表失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="获取项目角色列表失败", detail=str(e))

@router.delete("/{project_id}/member/{user_id}/role/{role_id}", response_model=Response[Dict[str, Any]])
async def remove_project_role(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    user_id: int = Path(..., description="用户ID"),
    role_id: int = Path(..., description="角色ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    移除项目成员的角色
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        user_id (int): 用户ID
        role_id (int): 角色ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 角色移除响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目、用户或角色不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求移除项目 {project_id} 成员 {user_id} 的角色 {role_id}，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 检查权限：用户必须是项目管理员
        has_admin_permission = check_project_permission(db, current_user.id, project_id, 'admin')
        if not has_admin_permission:
            logger.warning(f"用户 {current_user.username} 尝试移除项目 {project_id} 成员 {user_id} 的角色，但权限不足")
            raise AuthorizationError(message="无权管理项目成员角色")
        
        # 检查用户是否为项目成员
        permission_service = PermissionService(db)
        if not permission_service.check_project_member(user_id, project_id):
            logger.warning(f"用户 {current_user.username} 尝试移除非项目成员 {user_id} 的角色")
            raise BusinessError(message="指定用户不是项目成员")
        
        # 移除项目角色
        result = service.remove_project_role(project_id, user_id, role_id)
        
        process_time = time.time() - start_time
        logger.info(f"移除项目 {project_id} 成员 {user_id} 的角色 {role_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=result,
            message="移除项目角色成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"移除项目 {project_id} 成员 {user_id} 的角色失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="移除项目角色失败", detail=str(e))

@router.post("/{project_id}/member/{user_id}/role", response_model=Response[Dict[str, Any]])
async def assign_project_role(
    request: Request,
    role_data: ProjectRoleAssignRequest,
    project_id: int = Path(..., description="项目ID"),
    user_id: int = Path(..., description="用户ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    为项目成员分配角色
    
    Args:
        request (Request): 请求对象
        role_data (ProjectRoleAssignRequest): 角色分配数据
        project_id (int): 项目ID
        user_id (int): 用户ID
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 角色分配响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目或用户不存在
        BusinessError: 业务逻辑错误
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求为项目 {project_id} 的成员 {user_id} 分配角色 {role_data.role_id}，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 检查权限：用户必须是项目管理员
        has_admin_permission = check_project_permission(db, current_user.id, project_id, 'admin')
        if not has_admin_permission:
            logger.warning(f"用户 {current_user.username} 尝试为项目 {project_id} 的成员 {user_id} 分配角色，但权限不足")
            raise AuthorizationError(message="无权管理项目成员角色")
        
        # 检查用户是否为项目成员
        permission_service = PermissionService(db)
        if not permission_service.check_project_member(user_id, project_id):
            logger.warning(f"用户 {current_user.username} 尝试为非项目成员 {user_id} 分配项目角色")
            raise BusinessError(message="指定用户不是项目成员")
        
        # 检查角色是否为项目角色
        role_service = RoleService(db)
        role = role_service.get_role(role_data.role_id)
        if role.role_type != "project":
            logger.warning(f"用户 {current_user.username} 尝试分配非项目角色 {role_data.role_id}")
            raise BusinessError(message="指定角色不是项目角色")
        
        # 分配项目角色
        result = service.assign_project_role(project_id, user_id, role_data.role_id)
        
        process_time = time.time() - start_time
        logger.info(f"为项目 {project_id} 的成员 {user_id} 分配角色 {role_data.role_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=result,
            message="分配项目角色成功"
        )
    except (AuthorizationError, ResourceNotFound, BusinessError):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"为项目 {project_id} 的成员 {user_id} 分配角色失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="分配项目角色失败", detail=str(e))

@router.put("/{project_id}", response_model=Response[ProjectResponse])
async def update_project(
    request: Request,
    project_id: int = Path(..., description="项目ID"),
    project_data: ProjectUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[ProjectResponse]:
    """
    更新项目信息
    
    Args:
        request (Request): 请求对象
        project_id (int): 项目ID
        project_data (ProjectUpdate): 项目更新数据
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[ProjectResponse]: 项目更新响应
        
    Raises:
        AuthorizationError: 权限不足
        ResourceNotFound: 项目不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {current_user.username} 请求更新项目 {project_id}，IP: {client_ip}")
    
    try:
        service = ProjectService(db)
        
        # 检查用户是否有权限更新项目
        has_permission = check_project_permission(db, current_user.id, project_id, 'admin')
        if not has_permission:
            logger.warning(f"用户 {current_user.username} 尝试更新项目 {project_id}，但权限不足")
            raise AuthorizationError(message="无权更新此项目")
        
        # 更新项目
        updated_project = service.update_project(project_id, {
            "name": project_data.name,
            "description": project_data.description,
            "repository_url": project_data.repository_url,
            "repository_type": project_data.repository_type,
            "branch": project_data.branch,
            "is_active": project_data.is_active
        })
        
        # 格式化响应
        response_data = ProjectResponse(
            id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description,
            repository_url=updated_project.repository_url,
            repository_type=updated_project.repository_type,
            branch=updated_project.branch,
            is_active=updated_project.is_active,
            created_by=updated_project.created_by,
            creator_name=updated_project.creator.username if updated_project.creator else None,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at
        )
        
        process_time = time.time() - start_time
        logger.info(f"更新项目 {project_id} 成功，处理时间: {process_time:.2f}秒")
        
        return Response(
            data=response_data,
            message="项目更新成功"
        )
    except (AuthorizationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"更新项目 {project_id} 失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="更新项目失败", detail=str(e))