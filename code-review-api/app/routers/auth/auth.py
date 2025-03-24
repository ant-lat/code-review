from fastapi import APIRouter, Depends, HTTPException, Path, Body, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import time
import traceback
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService
from app.core.security import get_current_user, get_user_permissions, verify_password
from app.models.user import User
from app.core.exceptions import AuthenticationError, DatabaseError, ResourceNotFound, ValidationError, BusinessError
from app.schemas.response import Response
from app.config.logging_config import logger
from app.config import config
from pydantic import BaseModel

from app.services.security import get_password_hash

# 创建路由器
router = APIRouter(
    prefix="/api/v1/auth",
    tags=["认证授权"],
    responses={
        401: {"description": "未授权"},
        403: {"description": "权限不足"},
        404: {"description": "资源未找到"},
        422: {"description": "验证错误"},
        500: {"description": "服务器内部错误"}
    }
)

# 配置JWT
SECRET_KEY = config.SECRET_KEY
REFRESH_SECRET_KEY = config.REFRESH_SECRET_KEY
ALGORITHM = config.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.ACCESS_TOKEN_EXPIRE_MINUTES if config.ACCESS_TOKEN_EXPIRE_MINUTES >= 5 else 5

if isinstance(SECRET_KEY, str):
    SECRET_KEY = SECRET_KEY.encode()
if isinstance(REFRESH_SECRET_KEY, str):
    REFRESH_SECRET_KEY = REFRESH_SECRET_KEY.encode()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7天有效期
# OAuth2密码Bearer流程
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class LoginRequest(BaseModel):
    """登录请求模型"""
    user_id: str
    password: str
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class PasswordChange(BaseModel):
    """密码修改请求模型"""
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    """忘记密码请求模型"""
    user_id: str
    

class VerifyInfoRequest(BaseModel):
    """验证信息请求模型"""
    user_id: str
    verification_type: str  # "phone", "email", "name" 之一
    answer: str  # 用户提供的答案


class ResetPasswordWithVerifyRequest(BaseModel):
    """通过验证信息重置密码请求模型"""
    user_id: str
    verification_type: str
    answer: str
    new_password: str
    confirm_password: str

    class Config:
        from_attributes = True

def aware_utcnow():
    return datetime.now(timezone.utc)


# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Args:
        data (dict): 要编码的数据
        expires_delta (Optional[timedelta], optional): 过期时间. Defaults to None.
    
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    expire = aware_utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire.timestamp()})
    to_encode.update({"iat": aware_utcnow().timestamp()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 创建刷新令牌
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Args:
        data (dict): 要编码的数据
        expires_delta (Optional[timedelta], optional): 过期时间. Defaults to None.
    
    Returns:
        str: JWT刷新令牌
    """
    to_encode = data.copy()
    expire = aware_utcnow() + (expires_delta if expires_delta else timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire.timestamp()})
    to_encode.update({"iat": aware_utcnow().timestamp()})
    encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)  # 注意这里使用的是 REFRESH_SECRET_KEY
    return encoded_jwt
    #
    # to_encode = data.copy()
    # iat = int(datetime.utcnow().timestamp())  # 确保 iat 是整数
    # exp = int((datetime.utcnow() + expires_delta).timestamp()) if expires_delta else int(
    #     (datetime.utcnow() + timedelta(minutes=7 * 24 * 60)).timestamp())
    # to_encode.update({"exp": exp})
    # to_encode.update({"iat": iat})  # 添加 iat 字段
    # encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/login", response_model=Response[Dict[str, Any]])
async def login(
        request: Request,
        login_data: LoginRequest = Body(...),
        db: Session = Depends(get_db)
) -> Response[Dict[str, Any]]:
    """
    用户登录
    
    Args:
        request (Request): 请求对象
        login_data (LoginRequest): 登录数据
        db (Session): 数据库会话
        
    Returns:
        Response[Dict[str, Any]]: 登录响应，只包含令牌信息，不包含用户详细信息
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"用户 {login_data.user_id} 请求登录，IP: {client_ip}")

    try:
        auth_service = AuthService(db)

        # 认证用户，使用 user_id 而不是 username
        user, _ = auth_service.authenticate_user(
            user_id=login_data.user_id,
            password=login_data.password
        )
        token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

        token_data = {
            "sub": user.user_id,
            "user_id": user.id,
            "role": [role.name for role in user.roles],
            "last_login": datetime.utcnow().isoformat()
        }

        access_token = create_access_token(
            data=token_data,
            expires_delta=token_expires
        )

        refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=refresh_token_expires
        )

        # 只返回token相关信息
        token_response = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "token_type": "bearer"
        }

        process_time = time.time() - start_time
        logger.info(f"用户 {login_data.user_id} 登录成功，处理时间: {process_time:.2f}秒")

        return Response(
            data=token_response,
            message="登录成功"
        )
    except AuthenticationError as e:
        logger.warning(f"用户 {login_data.user_id} 登录失败: {str(e)}")
        raise
    except Exception as e:
        raise DatabaseError(message="登录失败", detail=str(e))


@router.post("/refresh", response_model=Response[Dict[str, Any]])
async def refresh_token(
        request: Request,
        refresh_data: RefreshTokenRequest = Body(...),
        db: Session = Depends(get_db)
) -> Response[Dict[str, Any]]:
    """
    刷新访问令牌
    Args:
        request (Request): 请求对象
        refresh_data (RefreshTokenRequest): 刷新令牌数据
        db (Session): 数据库会话
        
    Returns:
        Response[Dict[str, Any]]: 刷新令牌响应，只包含新的访问令牌和刷新令牌
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"请求刷新令牌，IP: {client_ip}")

    try:
        try:
            payload = jwt.decode(refresh_data.refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
            user_login_id = payload.get("sub")
            user_id = payload.get("user_id")

            if not user_login_id or not user_id:
                logger.warning("刷新令牌无效：缺少用户标识")
                raise AuthenticationError(message="无效的刷新令牌")

        except JWTError as e:
            logger.warning(f"刷新令牌解析失败: {str(e)}")
            raise AuthenticationError(message="无效的刷新令牌")

        user = db.query(User).filter(User.user_id == user_login_id).first()
        if not user or user.id != user_id:
            logger.warning(f"刷新令牌中的用户不存在: {user_login_id}")
            raise AuthenticationError(message="无效的刷新令牌")
        token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": user.user_id,
            "user_id": user.id,
            "role": [role.name for role in user.roles] if hasattr(user, 'roles') and user.roles else []
        }
        new_access_token = create_access_token(
            data=token_data,
            expires_delta=token_expires
        )
        new_refresh_token = create_refresh_token(
            data=token_data,
            expires_delta=refresh_token_expires
        )
        # 只返回token相关信息
        token_response = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "token_type": "bearer"
        }

        process_time = time.time() - start_time
        logger.info(f"为用户 {user_login_id} 刷新令牌成功，处理时间: {process_time:.2f}秒")

        return Response(
            data=token_response,
            message="刷新令牌成功"
        )
    except AuthenticationError as e:
        logger.warning(f"刷新令牌失败: {str(e)}")
        raise
    except Exception as e:
        raise DatabaseError(message="刷新令牌失败", detail=str(e))

@router.get("/get_current_user", response_model=Response[Dict[str, Any]])
async def get_current_user_info(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取当前登录用户信息
    
    Args:
        request (Request): 请求对象
        db (Session): 数据库会话
        current_user (User): 当前用户
        
    Returns:
        Response[Dict[str, Any]]: 包含完整用户信息的响应
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()

    try:
        logger.info(f"用户 {current_user.user_id} 请求获取个人信息，IP: {client_ip}")

        if not current_user:
            logger.error("current_user为空")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="未认证",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 创建新的数据库会话实例，避免并发操作问题
        with next(get_db()) as new_db:
            auth_service = AuthService(new_db)

            # 获取用户详细信息
            try:
                user_info = auth_service.get_user_by_id(current_user.id)
                
                # 确保返回完整的用户信息
                if hasattr(current_user, 'roles') and current_user.roles:
                    user_info["roles"] = [{"id": role.id, "name": role.name} for role in current_user.roles]
                
                # 获取用户权限
                try:
                    # 使用新的会话获取权限
                    permissions = get_user_permissions(new_db, current_user.id)
                    user_info["permissions"] = permissions
                except Exception as e:
                    logger.warning(f"获取用户权限时发生错误: {str(e)}")
                    user_info["permissions"] = []
                
                logger.info(f"成功获取用户信息")
            except Exception as e:
                logger.error(f"获取用户信息时发生错误: {str(e)}")
                logger.debug(traceback.format_exc())
                raise DatabaseError(message="获取用户信息失败", detail=str(e))

        process_time = time.time() - start_time
        logger.info(f"获取用户 {current_user.user_id} 信息成功，处理时间: {process_time:.2f}秒")

        return Response(
            data=user_info,
            message="获取用户信息成功"
        )
    except HTTPException as e:
        # 直接重新抛出HTTP异常
        logger.error(f"HTTP异常: {str(e)}")
        raise
    except Exception as e:
        raise DatabaseError(message="获取用户信息失败", detail=str(e))


@router.post("/forgot-password", response_model=Response)
async def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest = Body(...),
    db: Session = Depends(get_db)
) -> Response:
    """
    忘记密码，返回随机验证问题
    
    Args:
        request (Request): 请求对象
        forgot_data (ForgotPasswordRequest): 忘记密码请求数据
        db (Session): 数据库会话
        
    Returns:
        Response: 验证问题响应
        
    Raises:
        ValidationError: 验证错误
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"请求忘记密码，用户ID: {forgot_data.user_id}，IP: {client_ip}")
    
    try:
        auth_service = AuthService(db)
        
        # 根据用户ID查询用户
        user = db.query(User).filter(User.user_id == forgot_data.user_id).first()
        if not user:
            logger.warning(f"忘记密码请求失败: 用户ID {forgot_data.user_id} 不存在")
            raise ResourceNotFound(message="该用户不存在")
        
        # 随机选择一种验证方式
        import random
        verification_types = []
        
        # 添加可用的验证方式
        if user.phone:
            verification_types.append("phone")
        if user.email:
            verification_types.append("email")
        if user.username:
            verification_types.append("name")
            
        if not verification_types:
            logger.warning(f"用户 {forgot_data.user_id} 没有可用的验证信息")
            raise BusinessError(message="无法使用当前验证方式，请联系管理员")
        
        verification_type = random.choice(verification_types)
        
        # 根据验证方式生成验证问题
        question = ""
        if verification_type == "phone":
            # 获取手机号后4位
            last_four_digits = user.phone[-4:] if user.phone else ""
            question = "请输入您注册时使用的手机号码后4位"
        elif verification_type == "email":
            question = "请输入您注册时使用的完整邮箱地址"
        elif verification_type == "name":
            question = "请输入您的真实姓名"
        
        # 返回验证问题和类型
        process_time = time.time() - start_time
        logger.info(f"成功生成验证问题，用户ID: {forgot_data.user_id}，处理时间: {process_time:.2f}秒")
        
        return Response(
            message="请回答验证问题以重置密码",
            data={
                "verification_type": verification_type,
                "question": question
            }
        )
    except ResourceNotFound:
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"忘记密码请求处理失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="处理忘记密码请求失败", detail=str(e))


@router.post("/verify-info", response_model=Response)
async def verify_info(
    request: Request,
    verify_data: VerifyInfoRequest = Body(...),
    db: Session = Depends(get_db)
) -> Response:
    """
    验证用户信息
    
    Args:
        request (Request): 请求对象
        verify_data (VerifyInfoRequest): 验证信息请求数据
        db (Session): 数据库会话
        
    Returns:
        Response: 验证结果响应
        
    Raises:
        ValidationError: 验证错误
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"请求验证用户信息，用户ID: {verify_data.user_id}，验证类型: {verify_data.verification_type}，IP: {client_ip}")
    
    try:
        # 根据用户ID查询用户
        user = db.query(User).filter(User.user_id == verify_data.user_id).first()
        if not user:
            logger.warning(f"验证用户信息失败: 用户ID {verify_data.user_id} 不存在")
            raise ResourceNotFound(message="该用户不存在")
        
        # 根据验证类型验证答案
        is_valid = False
        if verify_data.verification_type == "phone":
            # 验证手机号后4位
            if user.phone and user.phone[-4:] == verify_data.answer:
                is_valid = True
        elif verify_data.verification_type == "email":
            # 验证完整邮箱地址
            if user.email and user.email.lower() == verify_data.answer.lower():
                is_valid = True
        elif verify_data.verification_type == "name":
            # 验证姓名
            if user.username and user.username == verify_data.answer:
                is_valid = True
        
        if not is_valid:
            logger.warning(f"验证用户信息失败: 用户ID {verify_data.user_id} 的验证信息不正确")
            raise ValidationError(message="验证信息不正确")
        
        process_time = time.time() - start_time
        logger.info(f"验证用户信息成功，用户ID: {verify_data.user_id}，处理时间: {process_time:.2f}秒")

        return Response(
            message="验证信息正确",
            data={
                "message": "验证信息正确"
            }
        )
    except (ValidationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"验证用户信息失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="验证用户信息失败", detail=str(e))


@router.post("/reset-password-with-verify", response_model=Response)
async def reset_password_with_verify(
    request: Request,
    reset_data: ResetPasswordWithVerifyRequest = Body(...),
    db: Session = Depends(get_db)
) -> Response:
    """
    通过验证信息重置密码
    
    Args:
        request (Request): 请求对象
        reset_data (ResetPasswordWithVerifyRequest): 重置密码请求数据
        db (Session): 数据库会话
        
    Returns:
        Response: 密码重置响应
        
    Raises:
        ValidationError: 验证错误
        ResourceNotFound: 用户不存在
        DatabaseError: 数据库操作错误
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = time.time()
    logger.info(f"请求通过验证信息重置密码，用户ID: {reset_data.user_id}，IP: {client_ip}")
    
    try:
        # 验证新密码和确认密码是否一致
        if reset_data.new_password != reset_data.confirm_password:
            logger.warning(f"重置密码失败: 新密码和确认密码不一致")
            raise ValidationError(message="新密码和确认密码不一致")
        
        # 根据用户ID查询用户
        user = db.query(User).filter(User.user_id == reset_data.user_id).first()
        if not user:
            logger.warning(f"重置密码失败: 用户ID {reset_data.user_id} 不存在")
            raise ResourceNotFound(message="该用户不存在")
        
        # 根据验证类型验证答案
        is_valid = False
        if reset_data.verification_type == "phone":
            # 验证手机号后4位
            if user.phone and user.phone[-4:] == reset_data.answer:
                is_valid = True
        elif reset_data.verification_type == "email":
            # 验证完整邮箱地址
            if user.email and user.email.lower() == reset_data.answer.lower():
                is_valid = True
        elif reset_data.verification_type == "name":
            # 验证姓名
            if user.username and user.username == reset_data.answer:
                is_valid = True
        
        if not is_valid:
            logger.warning(f"重置密码失败: 用户ID {reset_data.user_id} 的验证信息不正确")
            raise ValidationError(message="验证信息不正确")
        
        # 验证密码强度
        from app.routers.user_management.users import validate_password_strength
        
        is_valid, error_msg = validate_password_strength(reset_data.new_password)
        if not is_valid:
            logger.warning(f"重置密码失败: 新密码强度不足")
            raise ValidationError(message=f"新密码强度不足: {error_msg}")
        
        # 重置密码
        auth_service = AuthService(db)
        user.password_hash = get_password_hash(reset_data.new_password)
        db.commit()
        
        process_time = time.time() - start_time
        logger.info(f"通过验证信息重置密码成功，用户ID: {reset_data.user_id}，处理时间: {process_time:.2f}秒")

        return Response(
            message="密码重置成功，请使用新密码登录",
            data={
                "message": "密码重置成功，请使用新密码登录"
            }
        )
    except (ValidationError, ResourceNotFound):
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"通过验证信息重置密码失败: {str(e)}, 处理时间: {process_time:.2f}秒")
        logger.debug(traceback.format_exc())
        raise DatabaseError(message="重置密码失败", detail=str(e))

@router.get("/permissions", response_model=Response[Dict[str, Any]])
async def get_user_permissions_and_menus(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response[Dict[str, Any]]:
    """
    获取当前用户的权限和菜单
    
    Returns:
        Response: 权限和菜单数据
    """
    try:
        # 初始化服务
        auth_service = AuthService(db)
        permission_service = PermissionService(db)
        
        # 获取用户权限
        permissions = permission_service.get_user_permissions(current_user.id)
        permission_codes = [p["code"] for p in permissions]
        
        # 获取用户菜单
        menus = auth_service.get_user_menus(current_user.id)
        
        return Response(
            code=200,
            status="success",
            message="获取权限和菜单成功",
            data={
                "permissions": permission_codes,
                "menus": menus
            }
        )
    except ResourceNotFound as e:
        logger.warning(f"获取权限和菜单失败: {str(e)}")
        return Response(
            code=404,
            status="error",
            message=str(e),
        )
    except Exception as e:
        logger.error(f"获取权限和菜单时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return Response(
            code=500,
            status="error",
            message="服务器内部错误"
        )

@router.put("/password", response_model=Response)
async def change_password(
    request: Request,
    password_data: PasswordChange = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    修改当前用户密码
    
    Args:
        password_data (PasswordChange): 密码修改数据
        
    Returns:
        Response: 操作结果
    """
    try:
        # 初始化服务
        auth_service = AuthService(db)
        
        # 更新密码
        auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        return Response(
            code=200,
            status="success",
            message="密码修改成功"
        )
    except AuthenticationError as e:
        logger.warning(f"密码修改失败: {str(e)}")
        return Response(
            code=401,
            status="error",
            message=str(e)
        )
    except ResourceNotFound as e:
        logger.warning(f"密码修改失败: {str(e)}")
        return Response(
            code=404,
            status="error",
            message=str(e)
        )
    except Exception as e:
        logger.error(f"密码修改时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return Response(
            code=500,
            status="error",
            message="服务器内部错误"
        )

@router.post("/logout", response_model=Response)
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    用户登出
    
    Returns:
        Response: 操作结果
    """
    try:
        # 记录日志
        logger.info(f"用户 {current_user.user_id} 登出系统")
        
        # 在实际应用中，这里可能需要处理token的失效等逻辑
        # 例如将token加入黑名单，或者更新用户的最后登出时间
        
        return Response(
            code=200,
            status="success",
            message="登出成功"
        )
    except Exception as e:
        logger.error(f"登出时出错: {str(e)}")
        logger.debug(traceback.format_exc())
        return Response(
            code=500,
            status="error",
            message="服务器内部错误"
        )
