"""
用户服务模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import logging
import traceback

from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.database import get_db
from app.config.logging_config import logger
from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError, AuthenticationError
from app.services.base_service import BaseService
from app.core.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)

class UserService(BaseService[User]):
    """
    用户服务类，处理用户相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化用户服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def _safe_query(self, query_func, error_message, default_value=None):
        """
        安全执行数据库查询，处理异常
        
        Args:
            query_func: 查询函数
            error_message: 错误消息
            default_value: 发生异常时返回的默认值
            
        Returns:
            查询结果或默认值
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        try:
            return query_func()
        except (ResourceNotFound, BusinessError, AuthenticationError) as e:
            # 重新抛出业务异常
            raise
        except Exception as e:
            logger.error(f"{error_message}: {str(e)}", exc_info=True)
            raise DatabaseError(message=f"{error_message}: {str(e)}")
    
    def create_user(self, data: Dict[str, Any]) -> User:
        """
        创建用户
        
        Args:
            data (Dict[str, Any]): 用户数据
                - user_id (str): 用户登录ID
                - username (str): 用户真实姓名
                - email (Optional[str]): 电子邮箱
                - phone (Optional[str]): 手机号
                - password (str): 密码
                - role_ids (Optional[List[int]]): 角色ID列表
                - is_active (Optional[bool]): 是否激活
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            BusinessError: 用户ID、用户名、邮箱或手机号已存在，或格式无效
            DatabaseError: 数据库操作错误
        """
        try:
            # 验证用户ID字段
            if "user_id" not in data or not data["user_id"]:
                raise BusinessError(message="用户登录ID是必需的")
                
            # 验证用户名格式
            if "username" not in data or not data["username"]:
                raise BusinessError(message="用户名是必需的")
                
            if not self._validate_username(data["username"]):
                raise BusinessError(message="用户名格式无效：只能包含字母、数字和下划线，长度3-20")
            
            # 验证邮箱和手机号至少一个有效
            has_email = "email" in data and data["email"]
            has_phone = "phone" in data and data["phone"]
            
            if not has_email and not has_phone:
                raise BusinessError(message="邮箱和手机号至少需要提供一个")
                
            # 如果提供了邮箱，验证格式
            if has_email and not self._validate_email(data["email"]):
                raise BusinessError(message="邮箱格式无效")
                
            # 如果提供了手机号，验证格式
            if has_phone and not self._validate_phone(data["phone"]):
                raise BusinessError(message="手机号格式无效")
                
            # 验证密码强度
            if "password" not in data or not data["password"]:
                raise BusinessError(message="密码是必需的")
                
            if not self._validate_password(data["password"]):
                raise BusinessError(message="密码强度不足：至少8位，包含大小写字母和数字")
                
            # 检查用户ID、用户名、邮箱和手机号是否已存在
            filter_conditions = [
                User.user_id == data["user_id"],
                User.username == data["username"]
            ]
            
            if has_email:
                filter_conditions.append(User.email == data["email"])
                
            if has_phone:
                filter_conditions.append(User.phone == data["phone"])
                
            existing_user = self.db.query(User).filter(or_(*filter_conditions)).first()
    
            if existing_user:
                if existing_user.user_id == data["user_id"]:
                    raise BusinessError(message=f"用户登录ID '{data['user_id']}' 已被使用")
                elif existing_user.username == data["username"]:
                    raise BusinessError(message=f"用户名 '{data['username']}' 已被使用")
                elif has_email and existing_user.email == data["email"]:
                    raise BusinessError(message=f"邮箱 '{data['email']}' 已被使用")
                elif has_phone and existing_user.phone == data["phone"]:
                    raise BusinessError(message=f"手机号 '{data['phone']}' 已被使用")

            # 处理角色分配
            role_ids = []
            
            # 优先使用role_ids参数
            if "role_ids" in data and data["role_ids"]:
                role_ids = data["role_ids"]
            
            # 如果没有角色，默认使用"user"角色
            if not role_ids:
                # 找不到角色，使用默认的"user"角色
                default_role = self.db.query(Role).filter(Role.name == "user").first()
                if default_role:
                    role_ids = [default_role.id]
                else:
                    logger.warning(f"无法找到默认角色'user'，将不会为用户 {data['username']} 分配角色")
            
            # 验证角色是否存在
            if role_ids:
                roles = self.db.query(Role).filter(Role.id.in_(role_ids)).all()
                found_role_ids = {role.id for role in roles}
                missing_role_ids = set(role_ids) - found_role_ids
                if missing_role_ids:
                    raise BusinessError(message=f"角色ID不存在: {missing_role_ids}")
            
            # 创建用户
            now = datetime.utcnow()
            new_user = User(
                user_id=data["user_id"],
                username=data["username"],
                email=data.get("email"),
                phone=data.get("phone"),
                password_hash=get_password_hash(data["password"]),
                is_active=data.get("is_active", True),
                created_at=now,
                updated_at=now
            )
            
            # 添加到数据库
            self.db.add(new_user)
            self.db.flush()
            
            # 关联角色
            if role_ids and roles:
                for role in roles:
                    user_role = UserRole(
                        user_id=new_user.id,
                        role_id=role.id,
                        is_active=True,
                        created_at=now
                    )
                    self.db.add(user_role)
                
            # 提交事务
            self.db.commit()
            self.db.refresh(new_user)
            
            return new_user
            
        except (BusinessError, ResourceNotFound) as e:
            # 回滚事务并重新抛出业务异常
            self.db.rollback()
            raise
        except Exception as e:
            # 回滚事务并记录错误
            self.db.rollback()
            logger.error(f"创建用户失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise DatabaseError(message=f"创建用户失败: {str(e)}")
    
    def get_user_by_username(self, username: str) -> User:
        """
        通过用户名获取用户
        
        Args:
            username (str): 用户名
            
        Returns:
            User: 用户对象
            
        Raises:
            ResourceNotFound: 用户不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            user = self.db.query(User).filter(User.username == username).first()
            if not user:
                raise ResourceNotFound(message=f"用户名 '{username}' 不存在")
            return user
        
        return self._safe_query(_query, f"获取用户失败: 用户名 {username}")
    
    def get_user_by_email(self, email: str) -> User:
        """
        通过电子邮箱获取用户
        
        Args:
            email (str): 电子邮箱
            
        Returns:
            User: 用户对象
            
        Raises:
            ResourceNotFound: 用户不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                raise ResourceNotFound(message=f"邮箱 '{email}' 不存在")
            return user
        
        return self._safe_query(_query, f"获取用户失败: 邮箱 {email}")
    
    def authenticate_user(self, username: str, password: str) -> User:
        """
        用户认证
        
        Args:
            username (str): 用户名或邮箱
            password (str): 密码
            
        Returns:
            User: 认证成功的用户对象
            
        Raises:
            AuthenticationError: 认证失败
            DatabaseError: 数据库操作错误
        """
        try:
            # 支持用户名或邮箱登录
            user = self.db.query(User).filter(
                or_(User.username == username, User.email == username)
            ).first()
            
            if not user:
                raise AuthenticationError(message="用户名或密码错误")
            
            if not user.is_active:
                raise AuthenticationError(message="用户已被禁用")
            
            if not verify_password(password, user.password_hash):
                raise AuthenticationError(message="用户名或密码错误")
            
            # 更新上次登录时间
            user.last_login = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            
            return user
        except AuthenticationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"用户认证失败: {str(e)}")
            raise DatabaseError(message="用户认证失败", detail=str(e))
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> User:
        """
        更新用户信息
        
        Args:
            user_id (int): 用户ID
            data (Dict[str, Any]): 更新数据
            
        Returns:
            User: 更新后的用户对象
            
        Raises:
            ResourceNotFound: 用户不存在
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证用户存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(resource_type="用户", resource_id=user_id)
                
            # 检查更新字段
            if not data:
                raise BusinessError(message="未提供有效的更新字段")
                
            # 验证邮箱和手机号
            has_email = user.email if "email" not in data else data["email"]
            has_phone = user.phone if "phone" not in data else data["phone"]
            
            # 如果更新会导致邮箱和手机号都为空，则拒绝
            if not has_email and not has_phone:
                raise BusinessError(message="邮箱和手机号至少需要提供一个")
                
            # 验证更新的邮箱格式（如果有）
            if "email" in data and data["email"] and not self._validate_email(data["email"]):
                raise BusinessError(message="邮箱格式无效")
                
            # 检查邮箱是否已被其他用户使用
            if "email" in data and data["email"] and data["email"] != user.email:
                existing_email = self.db.query(User).filter(
                    User.email == data["email"],
                    User.id != user_id
                ).first()
                if existing_email:
                    raise BusinessError(message=f"邮箱 '{data['email']}' 已被其他用户使用")
                    
            # 验证更新的手机号格式（如果有）
            if "phone" in data and data["phone"] and not self._validate_phone(data["phone"]):
                raise BusinessError(message="手机号格式无效")
                
            # 检查手机号是否已被其他用户使用
            if "phone" in data and data["phone"] and data["phone"] != user.phone:
                existing_phone = self.db.query(User).filter(
                    User.phone == data["phone"],
                    User.id != user_id
                ).first()
                if existing_phone:
                    raise BusinessError(message=f"手机号 '{data['phone']}' 已被其他用户使用")
                    
            # 验证用户名格式（如果更新）
            if "username" in data and data["username"] and not self._validate_username(data["username"]):
                raise BusinessError(message="用户名格式无效：只能包含字母、数字和下划线，长度3-20")
                
            # 检查用户名是否已被其他用户使用
            if "username" in data and data["username"] and data["username"] != user.username:
                existing_username = self.db.query(User).filter(
                    User.username == data["username"],
                    User.id != user_id
                ).first()
                if existing_username:
                    raise BusinessError(message=f"用户名 '{data['username']}' 已被其他用户使用")
                    
            # 检查用户ID是否已被其他用户使用
            if "user_id" in data and data["user_id"] and data["user_id"] != user.user_id:
                existing_user_id = self.db.query(User).filter(
                    User.user_id == data["user_id"],
                    User.id != user_id
                ).first()
                if existing_user_id:
                    raise BusinessError(message=f"用户ID '{data['user_id']}' 已被其他用户使用")
            
            # 更新用户字段
            for key, value in data.items():
                if hasattr(user, key) and key != 'id':  # 防止更新主键
                    setattr(user, key, value)
                    
            # 更新时间戳
            user.updated_at = datetime.utcnow()
            
            # 提交更改
            self.db.commit()
            self.db.refresh(user)
            
            return user
            
        return self._safe_query(_query, f"更新用户信息失败: 用户ID {user_id}")
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        修改用户密码
        
        Args:
            user_id (int): 用户ID
            current_password (str): 当前密码
            new_password (str): 新密码
            
        Returns:
            bool: 是否修改成功
            
        Raises:
            ResourceNotFound: 用户不存在
            AuthenticationError: 当前密码错误
            BusinessError: 新密码强度不足
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证用户存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 验证当前密码
            if not verify_password(current_password, user.password_hash):
                raise AuthenticationError(message="当前密码错误")
            
            # 验证新密码强度
            if not self._validate_password(new_password):
                raise BusinessError(message="新密码强度不足：至少8位，包含大小写字母和数字")
            
            # 不允许新密码与旧密码相同
            if verify_password(new_password, user.password_hash):
                raise BusinessError(message="新密码不能与当前密码相同")
            
            # 更新密码
            user.password_hash = get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"用户 {user_id} 密码已修改")
            return True
        
        return self._safe_query(_query, f"修改密码失败: 用户ID {user_id}", False)
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """
        重置用户密码（管理员操作）
        
        Args:
            user_id (int): 用户ID
            new_password (str): 新密码
            
        Returns:
            bool: 是否重置成功
            
        Raises:
            ResourceNotFound: 用户不存在
            BusinessError: 新密码强度不足
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证用户存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 验证新密码强度
            if not self._validate_password(new_password):
                raise BusinessError(message="新密码强度不足：至少8位，包含大小写字母和数字")
            
            # 更新密码
            user.password_hash = get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"用户 {user_id} 密码已被管理员重置")
            return True
        
        return self._safe_query(_query, f"重置密码失败: 用户ID {user_id}", False)
    
    def assign_role(self, user_id: int, role_id: int) -> UserRole:
        """
        为用户分配角色
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            UserRole: 创建的用户角色关系对象
            
        Raises:
            ResourceNotFound: 用户或角色不存在
            BusinessError: 用户已拥有该角色
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证用户存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 验证角色存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 检查用户是否已拥有该角色
            existing_role = self.db.query(UserRole).filter(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            ).first()
            if existing_role:
                raise BusinessError(message=f"用户已拥有角色 '{role.name}'")
            
            # 分配角色
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id
            )
            
            self.db.add(user_role)
            self.db.commit()
            self.db.refresh(user_role)
            
            logger.info(f"为用户 {user_id} 分配了角色 {role_id} ({role.name})")
            return user_role
        
        return self._safe_query(_query, f"为用户分配角色失败: 用户 {user_id}, 角色 {role_id}")
    
    def revoke_role(self, user_id: int, role_id: int) -> bool:
        """
        撤销用户角色
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            bool: 是否撤销成功
            
        Raises:
            ResourceNotFound: 用户或角色关系不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证用户角色关系存在
            user_role = self.db.query(UserRole).filter(
                and_(UserRole.user_id == user_id, UserRole.role_id == role_id)
            ).first()
            if not user_role:
                raise ResourceNotFound(message=f"用户 {user_id} 没有角色 {role_id}")
            
            # 撤销角色
            self.db.delete(user_role)
            self.db.commit()
            
            logger.info(f"已撤销用户 {user_id} 的角色 {role_id}")
            return True
        
        return self._safe_query(_query, f"撤销用户角色失败: 用户 {user_id}, 角色 {role_id}", False)
    
    def get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户角色列表
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[Dict[str, Any]]: 角色列表
            
        Raises:
            ResourceNotFound: 用户不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证用户存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 获取用户角色
            roles = self.db.query(Role).join(
                UserRole, UserRole.role_id == Role.id
            ).filter(
                UserRole.user_id == user_id
            ).all()
            
            # 格式化结果
            result = []
            for role in roles:
                result.append({
                    "id": role.id,
                    "name": role.name,
                    "description": role.description
                })
            
            return result
        
        return self._safe_query(_query, f"获取用户角色列表失败: 用户ID {user_id}", [])
    
    def search_users(self, filters: Dict[str, Any], skip: int = 0, limit: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        """
        搜索用户
        
        Args:
            filters (Dict[str, Any]): 搜索条件
                - query (Optional[str]): 搜索关键词（用户名、邮箱、手机号）
                - is_active (Optional[bool]): 过滤活跃状态
                - role_id (Optional[int]): 按角色ID过滤
                - created_after (Optional[datetime]): 创建时间起始
                - created_before (Optional[datetime]): 创建时间结束
            skip (int): 跳过的记录数
            limit (int): 返回的记录数
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: 用户列表和总数
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 构建基本查询
            query = self.db.query(User)
            
            # 关键词搜索
            if "query" in filters and filters["query"]:
                search_query = f"%{filters['query']}%"
                query = query.filter(
                    or_(
                        User.username.ilike(search_query),
                        User.email.ilike(search_query),
                        User.phone.ilike(search_query)
                    )
                )
            
            # 过滤活跃状态
            if "is_active" in filters:
                query = query.filter(User.is_active == filters["is_active"])
            
            # 按角色过滤
            if "role_id" in filters and filters["role_id"]:
                query = query.join(UserRole).filter(UserRole.role_id == filters["role_id"])
            
            # 按创建时间过滤
            if "created_after" in filters and filters["created_after"]:
                query = query.filter(User.created_at >= filters["created_after"])
            
            if "created_before" in filters and filters["created_before"]:
                query = query.filter(User.created_at <= filters["created_before"])
            
            # 获取总数
            total = query.count()
            
            # 应用分页和排序
            users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
            
            # 格式化返回结果
            result = []
            for user in users:
                # 获取用户角色
                roles = []
                for role in getattr(user, 'roles', []):
                    roles.append({
                        "id": role.id,
                        "name": role.name,
                        "code": getattr(role, 'code', None)
                    })
                
                user_dict = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "avatar_url": getattr(user, 'avatar_url', None),
                    "phone": getattr(user, 'phone', None),
                    "is_active": user.is_active,
                    "roles": roles,
                    "created_at": user.created_at.isoformat() if getattr(user, 'created_at', None) else None,
                    "updated_at": user.updated_at.isoformat() if getattr(user, 'updated_at', None) else None,
                    "last_login": user.last_login.isoformat() if getattr(user, 'last_login', None) else None
                }
                result.append(user_dict)
            
            return (result, total)
        
        return self._safe_query(_query, f"搜索用户失败: 条件 {filters}", ([], 0))
    
    def _validate_username(self, username: str) -> bool:
        """
        验证用户名格式
        
        Args:
            username (str): 用户名
            
        Returns:
            bool: 是否符合格式要求
        """
        if not username or not isinstance(username, str):
            return False
        
        # 用户名只允许字母、数字、下划线，长度4-20位
        pattern = r"^[a-zA-Z0-9_]{4,20}$"
        return bool(re.match(pattern, username))
    
    def _validate_email(self, email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email (str): 电子邮箱
            
        Returns:
            bool: 是否符合格式要求
        """
        if not email or not isinstance(email, str):
            return False
        
        # 邮箱格式验证
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email))
    
    def _validate_password(self, password: str) -> bool:
        """
        验证密码强度
        
        Args:
            password (str): 密码
            
        Returns:
            bool: 是否符合强度要求
        """
        if not password or not isinstance(password, str):
            return False
        
        # 密码至少8位，包含大小写字母和数字
        if len(password) < 8:
            return False
        
        patterns = [
            r"[A-Z]",  # 至少一个大写字母
            r"[a-z]",  # 至少一个小写字母
            r"[0-9]"   # 至少一个数字
        ]
        
        return all(bool(re.search(pattern, password)) for pattern in patterns)
    
    def _validate_phone(self, phone: str) -> bool:
        """
        验证手机号格式
        
        Args:
            phone (str): 手机号
            
        Returns:
            bool: 是否符合格式要求
        """
        if not phone or not isinstance(phone, str):
            return False
        
        # 手机号格式验证（中国大陆手机号）
        pattern = r"^1[3-9]\d{9}$"
        return bool(re.match(pattern, phone))
    
    def get_user_menus(self, user_id: int) -> List[dict]:
        """
        获取用户可访问的菜单列表
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[dict]: 用户菜单列表
        """
        with db_session() as db:
            try:
                from app.services.menu_service import MenuService
                menus = MenuService.get_user_menus(db, user_id)
                
                # 构建菜单树
                menu_tree = []
                menu_map = {}
                
                # 创建菜单映射
                for menu in menus:
                    menu_dict = menu.to_dict(include_children=False)
                    menu_dict['children'] = []
                    menu_map[menu.id] = menu_dict
                
                # 构建树形结构
                for menu_id, menu_dict in menu_map.items():
                    parent_id = menu_dict.get('parent_id')
                    
                    if parent_id is None or parent_id not in menu_map:
                        menu_tree.append(menu_dict)
                    else:
                        parent = menu_map[parent_id]
                        parent['children'].append(menu_dict)
                
                return menu_tree
            except Exception as e:
                logger.error(f"获取用户菜单失败: {str(e)}")
                logger.debug(traceback.format_exc())
                raise BusinessError(f"获取用户菜单失败: {str(e)}")
    
    def get_users(self, filters: Dict[str, Any] = None, page: int = 1, page_size: int = 20) -> Tuple[List[User], int]:
        """
        获取用户列表
        
        Args:
            filters (Dict[str, Any], optional): 过滤条件
                - username (Optional[str]): 用户名（模糊匹配）
                - email (Optional[str]): 邮箱（模糊匹配）
                - is_active (Optional[bool]): 是否激活
                - role_id (Optional[int]): 角色ID
                - role (Optional[str]): 角色名称
            page (int): 页码（从1开始）
            page_size (int): 每页数量
            
        Returns:
            Tuple[List[User], int]: 用户实体对象列表和总数
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 构建基本查询
            query = self.db.query(User)
            
            # 应用过滤条件
            if filters:
                if "username" in filters and filters["username"]:
                    query = query.filter(User.username.ilike(f"%{filters['username']}%"))
                
                if "email" in filters and filters["email"]:
                    query = query.filter(User.email.ilike(f"%{filters['email']}%"))
                
                if "is_active" in filters and filters["is_active"] is not None:
                    query = query.filter(User.is_active == filters["is_active"])
                
                if "role_id" in filters and filters["role_id"]:
                    query = query.join(UserRole).filter(UserRole.role_id == filters["role_id"])
                    
                if "role" in filters and filters["role"]:
                    query = query.join(UserRole).join(Role).filter(Role.name == filters["role"])
            
            # 计算总数
            total = query.count()
            
            # 分页
            query = query.order_by(User.created_at.desc())
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 获取用户列表并返回实体对象
            users = query.all()
            
            # 确保加载用户角色关系
            for user in users:
                if hasattr(user, 'roles'):
                    _ = [role.id for role in user.roles]
            
            return users, total
        
        return self._safe_query(_query, "获取用户列表失败", ([], 0))

    def delete_user(self, user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否删除成功

        Raises:
            ResourceNotFound: 用户不存在
            BusinessError: 业务逻辑错误（例如不能删除管理员）
            DatabaseError: 数据库操作错误
        """
        try:
            # 验证用户存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(resource_type="用户", resource_id=user_id)

            logger.info(f"开始删除用户 {user_id} ({user.username})")

            # 检查是否为管理员用户（可选：保护管理员不被删除）
            is_admin = False
            for role in user.roles:
                if role.name == "admin":
                    is_admin = True
                    break

            if is_admin:
                # 如果是唯一的管理员，则不允许删除
                admin_count = self.db.query(User).join(UserRole).join(Role).filter(Role.name == "admin").count()
                if admin_count <= 1:
                    raise BusinessError(message="不能删除唯一的管理员用户")

            # 开始删除过程
            try:
                # 重要：采用重新创建会话的方式避免会话缓存问题
                self.db.commit()  # 提交之前的所有更改
                
                from app.models.project_role import ProjectRole
                from app.models.issue_comment import IssueComment
                from app.models.issue_history import IssueHistory
                from app.models.notification import Notification
                from sqlalchemy import text
                
                # 使用纯原生SQL方式删除关联数据
                logger.info(f"使用原生SQL批量删除用户 {user_id} 的所有关联数据")
                
                # 保存用户名用于日志记录，避免后续访问已删除的对象
                username = user.username
                
                # 1. 首先，处理所有外键关联关系
                # 为每个表定义正确的列名和SQL语句
                relation_tables = [
                    {"name": "user_roles", "column": "user_id"},
                    {"name": "project_roles", "column": "user_id"},
                    {"name": "notifications", "column": "recipient_id"},
                    {"name": "issue_comments", "column": "user_id"},
                    {"name": "issue_history", "column": "user_id"}
                ]
                
                # 执行删除
                for table_info in relation_tables:
                    table_name = table_info["name"]
                    column_name = table_info["column"]
                    
                    sql = text(f"DELETE FROM {table_name} WHERE {column_name} = :user_id")
                    result = self.db.execute(sql, {"user_id": user_id})
                    logger.info(f"从表 {table_name} 删除了 {result.rowcount} 条关联记录")
                
                # 2. 刷新会话，确保所有关联数据已删除
                self.db.flush()
                
                # 3. 最后删除用户本身
                logger.info(f"删除用户 {user_id} 本身")
                sql = text("DELETE FROM users WHERE id = :user_id")
                result = self.db.execute(sql, {"user_id": user_id})
                logger.info(f"从users表删除了 {result.rowcount} 条记录")
                
                # 提交事务
                self.db.commit()
                
                logger.info(f"用户 {user_id} ({username}) 已成功删除")
                return True
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"删除用户 {user_id} 过程中出错: {str(e)}", exc_info=True)
                # 尝试备选方案
                return self._fallback_delete_user(user_id)

        except (ResourceNotFound, BusinessError) as e:
            # 如果是业务层面的错误，直接抛出
            logger.warning(f"删除用户 {user_id} 时遇到业务限制: {str(e)}")
            raise
        except Exception as e:
            # 其他异常，记录并抛出数据库错误
            logger.error(f"删除用户 {user_id} 失败: {str(e)}", exc_info=True)
            raise DatabaseError(message=f"删除用户失败: {str(e)}")

    def _fallback_delete_user(self, user_id: int) -> bool:
        """
        备选的用户删除方法，当主方法失败时使用
        使用更直接的方式删除用户

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 是否删除成功
        """
        try:
            logger.info(f"尝试使用备选方法删除用户 {user_id}")
            
            # 重新获取用户对象，避免使用可能状态不一致的对象
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"备选方法: 用户 {user_id} 已不存在")
                return True  # 如果用户已不存在，视为删除成功
                
            # 使用最原始的方式 - 直接执行DELETE语句
            # 创建一个新的会话以避免缓存问题
            try:
                # 1. 手动断开所有关联
                logger.info(f"备选方法：手动删除所有关联数据")
                
                # 使用存储过程或多条SQL语句
                queries = [
                    "DELETE FROM user_roles WHERE user_id = :id",
                    "DELETE FROM project_roles WHERE user_id = :id",
                    "DELETE FROM notifications WHERE recipient_id = :id",
                    "DELETE FROM issue_comments WHERE user_id = :id",
                    "DELETE FROM issue_history WHERE user_id = :id",
                    # 最后删除用户
                    "DELETE FROM users WHERE id = :id"
                ]
                
                from sqlalchemy import text
                for query in queries:
                    try:
                        result = self.db.execute(text(query), {"id": user_id})
                        logger.info(f"备选方法执行: {query.split()[1]} -> 删除了 {result.rowcount} 条记录")
                        self.db.flush()  # 每条语句后刷新
                    except Exception as q_error:
                        logger.warning(f"备选方法执行 {query} 时出错: {str(q_error)}")
                        # 继续执行下一条
                
                # 提交所有更改
                self.db.commit()
                logger.info(f"备选方法: 用户 {user_id} 已成功删除")
                return True
                
            except Exception as inner_e:
                self.db.rollback()
                logger.error(f"备选删除方法也失败: {str(inner_e)}", exc_info=True)
                # 继续尝试最后一种方法
                return self._emergency_delete_user(user_id)
                
        except Exception as e:
            logger.error(f"备选方法删除用户 {user_id} 失败: {str(e)}", exc_info=True)
            raise DatabaseError(message=f"删除用户失败 (备选方法): {str(e)}")
            
    def _emergency_delete_user(self, user_id: int) -> bool:
        """
        紧急删除方法 - 当所有其他方法都失败时的最后尝试
        直接使用存储过程或事务方式删除
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            logger.info(f"尝试紧急方法删除用户 {user_id}")
            
            # 使用多条语句的事务
            from sqlalchemy import text
            
            transaction_sql = """
            START TRANSACTION;
            
            -- 首先删除所有关联数据
            DELETE FROM user_roles WHERE user_id = :user_id;
            DELETE FROM project_roles WHERE user_id = :user_id;
            DELETE FROM notifications WHERE recipient_id = :user_id;
            DELETE FROM issue_history WHERE user_id = :user_id;
            DELETE FROM issue_comments WHERE user_id = :user_id;
            
            -- 最后删除用户本身
            DELETE FROM users WHERE id = :user_id;
            
            COMMIT;
            """
            
            # 创建新连接执行事务
            from app.database import engine
            with engine.connect() as connection:
                # 关闭自动提交
                connection = connection.execution_options(
                    isolation_level="SERIALIZABLE"
                )
                
                # 开始事务
                with connection.begin():
                    # 分别执行每条语句
                    for statement in transaction_sql.strip().split(';'):
                        if statement.strip() and not statement.strip().startswith('--'):
                            stmt = text(statement)
                            connection.execute(stmt, {"user_id": user_id})
            
            logger.info(f"紧急方法: 用户 {user_id} 已成功删除")
            return True
            
        except Exception as e:
            logger.error(f"紧急删除方法也失败: {str(e)}", exc_info=True)
            raise DatabaseError(message=f"所有删除方法均失败: {str(e)}")