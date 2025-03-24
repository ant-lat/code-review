"""
用户角色服务模块
@author: pgao
@date: 2024-03-13
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.services.base_service import BaseService
from app.core.exceptions import ResourceNotFound, BusinessError
from datetime import datetime

class UserRoleService(BaseService[UserRole]):
    """用户角色服务类"""
    
    def __init__(self, db: Session):
        """
        初始化用户角色服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def assign_role_to_user(self, user_id: int, role_id: int) -> Dict[str, Any]:
        """
        为用户分配角色
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        def _query():
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
                
            # 验证角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
                
            # 检查是否已存在关联
            exists = self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id
            ).first()
            
            if exists:
                # 如果关联已存在但处于非激活状态，则重新激活
                if not exists.is_active:
                    exists.is_active = True
                    self.db.commit()
                    return self.standard_response(True, message=f"已重新激活用户 '{user.username}' 的角色 '{role.name}'")
                else:
                    return self.standard_response(False, message=f"用户 '{user.username}' 已拥有角色 '{role.name}'")
            
            # 创建新的用户角色关联
            now = datetime.utcnow()
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                is_active=True,
                assigned_at=now
            )
            self.db.add(user_role)
            self.db.commit()
            
            return self.standard_response(True, data={
                "user_id": user_id,
                "role_id": role_id,
                "username": user.username,
                "role_name": role.name,
                "assigned_at": now.isoformat()
            }, message=f"已成功为用户 '{user.username}' 分配角色 '{role.name}'")
            
        return self._safe_query(_query, f"为用户分配角色失败: 用户ID {user_id}, 角色ID {role_id}")
    
    def revoke_role_from_user(self, user_id: int, role_id: int) -> Dict[str, Any]:
        """
        撤销用户的角色
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        def _query():
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
                
            # 验证角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 验证用户角色关系是否存在
            user_role = self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active == True
            ).first()
            
            if not user_role:
                return self.standard_response(False, message=f"用户 '{user.username}' 没有角色 '{role.name}' 或该角色已被撤销")
                
            # 撤销角色（设置为非激活状态）
            user_role.is_active = False
            user_role.revoked_at = datetime.utcnow()
            self.db.commit()
            
            return self.standard_response(True, message=f"已成功撤销用户 '{user.username}' 的角色 '{role.name}'")
            
        return self._safe_query(_query, f"撤销用户角色失败: 用户ID {user_id}, 角色ID {role_id}")
    
    def get_user_roles(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户的所有角色
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            Dict[str, Any]: 包含用户角色的响应
        """
        def _query():
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
                
            # 获取激活状态的用户角色
            roles = self.db.query(Role).join(
                UserRole, and_(
                    UserRole.role_id == Role.id,
                    UserRole.user_id == user_id,
                    UserRole.is_active == True
                )
            ).all()
            
            # 转换为字典列表
            result = []
            for role in roles:
                # 获取角色分配时间
                user_role = self.db.query(UserRole).filter(
                    UserRole.user_id == user_id,
                    UserRole.role_id == role.id,
                    UserRole.is_active == True
                ).first()
                
                role_dict = role.to_dict() if hasattr(role, 'to_dict') else {
                    "id": role.id,
                    "name": role.name,
                    "description": role.description,
                    "role_type": role.role_type if hasattr(role, 'role_type') else None
                }
                
                # 添加分配时间
                if user_role and user_role.assigned_at:
                    role_dict["assigned_at"] = user_role.assigned_at.isoformat()
                
                result.append(role_dict)
            
            return self.standard_response(True, data={
                "user_id": user_id,
                "username": user.username,
                "roles": result
            })
            
        return self._safe_query(_query, f"获取用户角色失败: 用户ID {user_id}")
    
    def get_role_users(self, role_id: int, include_inactive: bool = False) -> Dict[str, Any]:
        """
        获取拥有特定角色的所有用户
        
        Args:
            role_id (int): 角色ID
            include_inactive (bool): 是否包含非激活状态的用户关联
            
        Returns:
            Dict[str, Any]: 包含用户列表的响应
        """
        def _query():
            # 验证角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
                
            # 构建查询
            query = self.db.query(User).join(
                UserRole, and_(
                    UserRole.user_id == User.id,
                    UserRole.role_id == role_id
                )
            )
            
            # 是否只包含激活状态的关联
            if not include_inactive:
                query = query.filter(UserRole.is_active == True)
            
            # 获取用户列表
            users = query.all()
            
            # 转换为字典列表
            result = []
            for user in users:
                # 获取用户角色关联信息
                user_role = self.db.query(UserRole).filter(
                    UserRole.user_id == user.id,
                    UserRole.role_id == role_id
                ).first()
                
                user_dict = user.to_dict() if hasattr(user, 'to_dict') else {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email if hasattr(user, 'email') else None,
                    "is_active": user.is_active if hasattr(user, 'is_active') else None
                }
                
                # 添加角色关联信息
                if user_role:
                    user_dict["role_status"] = {
                        "is_active": user_role.is_active,
                        "assigned_at": user_role.assigned_at.isoformat() if user_role.assigned_at else None,
                        "revoked_at": user_role.revoked_at.isoformat() if hasattr(user_role, 'revoked_at') and user_role.revoked_at else None
                    }
                
                result.append(user_dict)
            
            return self.standard_response(True, data={
                "role_id": role_id,
                "role_name": role.name,
                "users": result,
                "total": len(result)
            })
            
        return self._safe_query(_query, f"获取角色用户失败: 角色ID {role_id}")
    
    def check_user_has_role(self, user_id: int, role_id: int) -> Dict[str, Any]:
        """
        检查用户是否拥有特定角色
        
        Args:
            user_id (int): 用户ID
            role_id (int): 角色ID
            
        Returns:
            Dict[str, Any]: 包含检查结果的响应
        """
        def _query():
            # 验证用户是否存在
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
                
            # 验证角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 查询用户是否拥有该角色
            has_role = self.db.query(UserRole).filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.is_active == True
            ).count() > 0
            
            return self.standard_response(True, data={
                "user_id": user_id,
                "role_id": role_id,
                "username": user.username,
                "role_name": role.name,
                "has_role": has_role
            })
            
        return self._safe_query(_query, f"检查用户角色失败: 用户ID {user_id}, 角色ID {role_id}") 