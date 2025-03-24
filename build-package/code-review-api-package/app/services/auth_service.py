"""
认证服务模块
@author: pgao
@date: 2024-03-13
"""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import time
from jose import jwt, JWTError

from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.menu import Menu
from app.models.role_menu import RoleMenu
from app.database import get_db
from app.config.logging_config import logger
from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError, AuthenticationError
from app.services.base_service import BaseService
from app.core.security import verify_password, get_password_hash, create_access_token, get_user_permissions
from app.config import config

class AuthService(BaseService):
    """认证授权服务类"""
    
    def __init__(self, db: Session):
        """
        初始化服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def authenticate_user(
        self, 
        user_id: str = None, 
        username: str = None, 
        email: str = None,
        password: str = None
    ) -> Tuple[User, Dict[str, Any]]:
        """
        验证用户凭据并返回用户对象
        
        Args:
            user_id (str, optional): 用户登录ID. Defaults to None.
            username (str, optional): 用户名. Defaults to None.
            email (str, optional): 电子邮件. Defaults to None.
            password (str, optional): 密码. Defaults to None.
            
        Returns:
            Tuple[User, Dict[str, Any]]: 用户对象和用户信息
            
        Raises:
            AuthenticationError: 认证错误
        """
        # 对于多种登录方式，优先级按照提供的参数顺序处理
        user = None
        if user_id:
            # 使用user_id查询用户
            user = self.db.query(User).filter(User.user_id == user_id).first()
        elif username:
            # 使用username查询用户
            user = self.db.query(User).filter(User.username == username).first()
        elif email:
            # 使用email查询用户
            user = self.db.query(User).filter(User.email == email).first()
        else:
            # 如果没有提供任何识别信息，则抛出错误
            raise AuthenticationError(message="请提供用户标识")
        
        # 检查用户是否存在
        if not user:
            raise AuthenticationError(message="用户不存在")
        
        # 检查用户状态
        if not user.is_active:
            raise AuthenticationError(message="用户账户已停用")
        
        # 验证密码
        if not password:
            raise AuthenticationError(message="密码不能为空")
        
        if not verify_password(password, user.password_hash):
            # 记录失败的登录尝试，这里可以添加更多的安全措施
            logger.warning(f"用户 {user.user_id} 登录尝试失败：密码错误")
            raise AuthenticationError(message="密码错误")
        
        # 生成或更新登录令牌
        self.db.commit()
        
        # 获取用户角色和权限
        user_roles = [role.name for role in user.roles] if user.roles else []
        
        # 组装用户信息，可以基于需求进行调整
        user_info = {
            "id": user.id,
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "roles": user_roles
        }
        
        return user, user_info
    
    def get_user_by_id(self, user_id: int) -> dict:
        """
        通过ID获取用户信息
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            dict: 用户信息
            
        Raises:
            ResourceNotFound: 用户不存在
        """
        def _query():
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(resource_type="用户", resource_id=user_id)
            
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        
        return self._safe_query(_query, f"获取用户信息失败: 用户ID {user_id}")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            email (str): 用户邮箱
            
        Returns:
            Optional[User]: 用户对象，不存在则返回None
        """
        def _query():
            return self.db.query(User).filter(User.email == email).first()
        
        return self._safe_query(_query, f"通过邮箱获取用户失败: {email}")
    
    def generate_verification_code(self, email: str) -> str:
        """
        生成验证码并存储
        
        Args:
            email (str): 用户邮箱
            
        Returns:
            str: 生成的验证码
        """
        import random
        import string
        from datetime import datetime, timedelta
        
        # 生成6位随机数字验证码
        code = ''.join(random.choices(string.digits, k=6))
        
        # 存储验证码及过期时间（15分钟后过期）
        expiry_time = datetime.utcnow() + timedelta(minutes=15)
        
        # 在实际项目中，应该将验证码存储在数据库或缓存中
        # 这里简化处理，使用全局变量存储
        if not hasattr(self, '_verification_codes'):
            self._verification_codes = {}
        
        self._verification_codes[email] = {
            'code': code,
            'expiry': expiry_time
        }
        
        return code
    
    def verify_code(self, email: str, code: str) -> bool:
        """
        验证邮箱验证码
        
        Args:
            email (str): 用户邮箱
            code (str): 验证码
            
        Returns:
            bool: 验证码是否有效
        """
        from datetime import datetime
        
        # 检查验证码是否存在
        if not hasattr(self, '_verification_codes') or email not in self._verification_codes:
            return False
        
        stored_data = self._verification_codes[email]
        stored_code = stored_data['code']
        expiry_time = stored_data['expiry']
        
        # 检查验证码是否过期
        if datetime.utcnow() > expiry_time:
            return False
        
        # 检查验证码是否匹配
        return code == stored_code
    
    def invalidate_verification_code(self, email: str) -> None:
        """
        使验证码失效
        
        Args:
            email (str): 用户邮箱
        """
        if hasattr(self, '_verification_codes') and email in self._verification_codes:
            del self._verification_codes[email]
    
    def reset_password(self, email: str, hashed_password: str) -> None:
        """
        重置用户密码
        
        Args:
            email (str): 用户邮箱
            hashed_password (str): 哈希后的密码
            
        Raises:
            ResourceNotFound: 用户不存在
        """
        def _query():
            user = self.get_user_by_email(email)
            if not user:
                raise ResourceNotFound(resource_type="用户", message=f"邮箱 {email} 不存在")
            
            user.password = hashed_password
            user.last_updated = datetime.utcnow()
            self.db.commit()
        
        return self._safe_query(_query, f"重置密码失败: {email}")
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        修改密码
        
        Args:
            user_id (int): 用户ID
            current_password (str): 当前密码
            new_password (str): 新密码
            
        Returns:
            bool: 是否成功
            
        Raises:
            BusinessError: 用户不存在
            AuthenticationError: 当前密码错误
        """
        def _query():
            # 查询用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(resource_type="用户", resource_id=user_id)
            
            # 验证当前密码
            if not verify_password(current_password, user.password_hash):
                raise AuthenticationError(message="当前密码错误")
            
            # 更新密码
            user.password_hash = get_password_hash(new_password)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            
            return True
        
        return self._safe_query(_query, f"修改密码失败: 用户ID {user_id}")
    
    def get_user_menus(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户菜单
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[Dict[str, Any]]: 菜单列表
        """
        def _query():
            # 查询用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(resource_type="用户", resource_id=user_id)
                
            # 查询用户角色
            role_ids = self.db.query(UserRole.role_id).filter(
                UserRole.user_id == user_id,
                UserRole.is_active == True
            ).all()
            
            role_id_list = [r.role_id for r in role_ids]
            
            # 如果没有角色，返回空列表
            if not role_id_list:
                return []
            
            # 查询角色菜单
            menus = self.db.query(Menu).join(
                RoleMenu, RoleMenu.menu_id == Menu.id
            ).filter(
                RoleMenu.role_id.in_(role_id_list),
                Menu.is_active == True
            ).order_by(
                Menu.parent_id.asc(),
                Menu.sort_order.asc()
            ).all()
            
            # 构建菜单树
            menu_dict = {}
            menu_tree = []
            
            # 首先将所有菜单转为字典
            for menu in menus:
                menu_item = {
                    "id": menu.id,
                    "name": menu.name,
                    "path": menu.path,
                    "component": menu.component,
                    "title": menu.title,
                    "icon": menu.icon,
                    "parent_id": menu.parent_id,
                    "sort_order": menu.sort_order,
                    "is_hidden": menu.is_hidden,
                    "children": []
                }
                menu_dict[menu.id] = menu_item
            
            # 构建树结构
            for menu_id, menu_item in menu_dict.items():
                parent_id = menu_item["parent_id"]
                if parent_id is None or parent_id == 0:
                    # 顶级菜单
                    menu_tree.append(menu_item)
                elif parent_id in menu_dict:
                    # 子菜单
                    menu_dict[parent_id]["children"].append(menu_item)
            
            return menu_tree
            
        return self._safe_query(_query, f"获取用户菜单失败: 用户ID {user_id}") 