"""
角色服务模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.menu import Menu
from app.models.role_menu import RoleMenu
from app.models.user_role import UserRole
from app.models.project_role import ProjectRole
from app.database import get_db
from app.config.logging_config import logger
from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError
from app.services.base_service import BaseService

class RoleService(BaseService[Role]):
    """
    角色服务类，处理角色相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化角色服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def get_role(self, role_id: int) -> Role:
        """
        获取角色信息
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            Role: 角色对象
            
        Raises:
            ResourceNotFound: 角色不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        return self.get_by_id(Role, role_id)
    
    def get_roles(self, skip: int = 0, limit: int = 100, name: Optional[str] = None, role_type: Optional[str] = None) -> Tuple[List[Role], int]:
        """
        获取角色列表
        
        Args:
            skip (int): 跳过的记录数
            limit (int): 返回的记录数
            name (Optional[str]): 角色名称筛选
            role_type (Optional[str]): 角色类型筛选
            
        Returns:
            Tuple[List[Role], int]: 角色列表和总数
        """
        def _query():
            query = self.db.query(Role)
            
            if name:
                query = query.filter(Role.name.ilike(f"%{name}%"))
                
            if role_type:
                query = query.filter(Role.role_type == role_type)
                
            total = query.count()
            roles = query.order_by(desc(Role.id)).offset(skip).limit(limit).all()
            
            return roles, total
            
        return self._safe_query(_query, "获取角色列表失败", ([], 0))
    
    def create_role(self, data: Dict[str, Any]) -> Role:
        """
        创建角色
        
        Args:
            data (Dict[str, Any]): 角色数据
                - name (str): 角色名称
                - description (Optional[str]): 角色描述
                - role_type (str): 角色类型(project/user)
                - permissions (Optional[List[str]]): 权限列表
                - menu_ids (Optional[List[int]]): 菜单ID列表
            
        Returns:
            Role: 创建的角色对象
            
        Raises:
            BusinessError: 角色名已存在或参数无效
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查角色名是否已存在
            existing = self.db.query(Role).filter(Role.name == data["name"]).first()
            if existing:
                raise BusinessError(message=f"角色名 '{data['name']}' 已存在")
            
            # 验证角色类型
            role_type = data.get("role_type", "user")
            if role_type not in ["project", "user"]:
                raise BusinessError(message="角色类型必须是 'project' 或 'user'")
            
            # 验证菜单ID列表（如果提供）
            menu_ids = data.get("menu_ids", [])
            if menu_ids:
                menus = self.db.query(Menu).filter(Menu.id.in_(menu_ids)).all()
                found_menu_ids = {menu.id for menu in menus}
                missing_menu_ids = set(menu_ids) - found_menu_ids
                if missing_menu_ids:
                    raise BusinessError(message=f"菜单ID不存在: {missing_menu_ids}")
            
            now = datetime.utcnow()
            # 创建角色
            role = Role(
                name=data["name"],
                description=data.get("description", ""),
                role_type=role_type,
                permissions=data.get("permissions", []),
                created_at=now,
                updated_at=now
            )
            
            self.db.add(role)
            self.db.commit()
            self.db.refresh(role)
            
            # 如果提供了菜单列表，则关联菜单
            if menu_ids:
                for menu_id in menu_ids:
                    role_menu = RoleMenu(
                        role_id=role.id,
                        menu_id=menu_id,
                        assigned_at=now
                    )
                    self.db.add(role_menu)
                
                self.db.commit()
                self.db.refresh(role)
            
            logger.info(f"角色创建成功: {role.name} (ID: {role.id})")
            return role
            
        return self._safe_query(_query, f"创建角色失败: {data.get('name')}")
    
    def update_role(self, role_id: int, data: Dict[str, Any]) -> Role:
        """
        更新角色
        
        Args:
            role_id (int): 角色ID
            data (Dict[str, Any]): 角色数据
                - name (Optional[str]): 新角色名称
                - description (Optional[str]): 新角色描述
                - permissions (Optional[List[str]]): 新权限列表
                - role_type (Optional[str]): 新角色类型
                - menu_ids (Optional[List[int]]): 新菜单ID列表
            
        Returns:
            Role: 更新后的角色对象
            
        Raises:
            ResourceNotFound: 角色不存在
            BusinessError: 角色名已存在或参数无效
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 如果更新角色名，检查是否重复
            if "name" in data and data["name"] != role.name:
                existing = self.db.query(Role).filter(
                    and_(Role.name == data["name"], Role.id != role_id)
                ).first()
                if existing:
                    raise BusinessError(message=f"角色名 '{data['name']}' 已存在")
                role.name = data["name"]
            
            # 更新其他字段
            if "description" in data:
                role.description = data["description"]
                
            if "permissions" in data:
                role.permissions = data["permissions"]
                
            if "role_type" in data:
                if data["role_type"] not in ["project", "user"]:
                    raise BusinessError(message="角色类型必须是 'project' 或 'user'")
                role.role_type = data["role_type"]
            
            # 更新菜单关联
            if "menu_ids" in data:
                # 删除现有的菜单关联
                self.db.query(RoleMenu).filter(RoleMenu.role_id == role_id).delete()
                
                # 添加新的菜单关联
                for menu_id in data["menu_ids"]:
                    menu = self.db.query(Menu).filter(Menu.id == menu_id).first()
                    if menu:
                        role_menu = RoleMenu(
                            role_id=role_id,
                            menu_id=menu_id,
                            assigned_at=datetime.utcnow()
                        )
                        self.db.add(role_menu)
            
            role.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(role)
            
            logger.info(f"角色 {role_id} ({role.name}) 更新成功")
            return role
            
        return self._safe_query(_query, f"更新角色失败: ID {role_id}")
    
    def delete_role(self, role_id: int) -> bool:
        """
        删除角色
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            bool: 删除是否成功
        """
        def _query():
            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 删除角色
            self.db.delete(role)
            self.db.commit()
            
            return True
            
        return self._safe_query(_query, f"删除角色失败: ID {role_id}", False)
    
    def assign_menu(self, role_id: int, menu_id: int) -> Dict[str, Any]:
        """
        分配菜单给角色
        
        Args:
            role_id (int): 角色ID
            menu_id (int): 菜单ID
            
        Returns:
            Dict[str, Any]: 结果
        """
        def _query():
            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 检查菜单是否存在
            menu = self.db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise ResourceNotFound(message=f"菜单ID {menu_id} 不存在")
            
            # 检查是否已分配
            existing = self.db.query(RoleMenu).filter(
                and_(RoleMenu.role_id == role_id, RoleMenu.menu_id == menu_id)
            ).first()
            
            if existing:
                return {"message": f"菜单 '{menu.title}' 已分配给角色 '{role.name}'"}
            
            # 创建关联
            role_menu = RoleMenu(
                role_id=role_id,
                menu_id=menu_id,
                assigned_at=datetime.utcnow()
            )
            
            self.db.add(role_menu)
            self.db.commit()
            
            return {"message": f"菜单 '{menu.title}' 成功分配给角色 '{role.name}'"}
            
        return self._safe_query(_query, f"分配菜单给角色失败: 角色 {role_id}, 菜单 {menu_id}", {"message": "操作失败"})
    
    def revoke_menu(self, role_id: int, menu_id: int) -> Dict[str, Any]:
        """
        从角色撤销菜单
        
        Args:
            role_id (int): 角色ID
            menu_id (int): 菜单ID
            
        Returns:
            Dict[str, Any]: 结果
        """
        def _query():
            # 检查角色菜单关联是否存在
            role_menu = self.db.query(RoleMenu).filter(
                and_(RoleMenu.role_id == role_id, RoleMenu.menu_id == menu_id)
            ).first()
            
            if not role_menu:
                raise ResourceNotFound(message=f"角色 {role_id} 未分配菜单 {menu_id}")
            
            # 删除关联
            self.db.delete(role_menu)
            self.db.commit()
            
            return {"message": "菜单已从角色中撤销"}
            
        return self._safe_query(_query, f"从角色撤销菜单失败: 角色 {role_id}, 菜单 {menu_id}", {"message": "操作失败"})
    
    def add_permission(self, role_id: int, permission_id: int) -> Dict[str, Any]:
        """
        为角色添加权限
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            
        Returns:
            Dict[str, Any]: 添加结果
            
        Raises:
            ResourceNotFound: 角色或权限不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        def _query():
            # 检查角色是否存在
            role = self.get_by_id(Role, role_id)
            
            # 获取权限
            permission = self.get_by_id(Permission, permission_id)
            
            # 检查权限是否已分配
            existing = self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            ).first()
            
            if existing:
                return {"success": True, "message": f"权限 {permission.name} 已分配给角色 {role.name}"}
            
            # 创建角色权限关联
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                assigned_at=datetime.now()
            )
            
            self.db.add(role_permission)
            self.db.commit()
            
            return {"success": True, "message": f"成功将权限 {permission.name} 分配给角色 {role.name}"}
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"添加权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"添加权限失败: {str(e)}")
            raise DatabaseError(f"添加权限失败: {str(e)}")
    
    def remove_permission(self, role_id: int, permission_id: int) -> Dict[str, Any]:
        """
        从角色移除权限
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            
        Returns:
            Dict[str, Any]: 移除结果
            
        Raises:
            ResourceNotFound: 角色或权限不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        def _query():
            # 检查角色是否存在
            role = self.get_by_id(Role, role_id)
            
            try:
                # 获取权限
                permission = self.get_by_id(Permission, permission_id)
                
                # 找到角色权限关联
                role_permission = self.db.query(RolePermission).filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == permission_id
                ).first()
                
                if not role_permission:
                    return {"success": False, "message": f"角色 {role.name} 未分配权限 {permission.name}"}
                
                # 删除关联
                self.db.delete(role_permission)
                self.db.commit()
                
                return {"success": True, "message": f"成功从角色 {role.name} 移除权限 {permission.name}"}
            except ResourceNotFound:
                return {"success": False, "message": f"权限ID {permission_id} 不存在"}
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"移除权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"移除权限失败: {str(e)}")
            raise DatabaseError(f"移除权限失败: {str(e)}")
    
    def get_all_permissions(self) -> List[Dict[str, Any]]:
        """
        获取所有权限
        
        Returns:
            List[Dict[str, Any]]: 权限列表
            
        Raises:
            DatabaseError: 数据库操作错误时抛出
        """
        try:
            permissions = self.db.query(Permission).all()
            
            result = []
            # 按模块分组
            grouped = {}
            
            for permission in permissions:
                if permission.module not in grouped:
                    grouped[permission.module] = []
                
                grouped[permission.module].append({
                    "id": permission.id,
                    "code": permission.code,
                    "name": permission.name,
                    "description": permission.description
                })
            
            # 转换为列表
            for module, perms in grouped.items():
                result.append({
                    "module": module,
                    "permissions": perms
                })
            
            return result
        except Exception as e:
            logger.error(f"获取所有权限失败: {str(e)}")
            raise DatabaseError(f"获取所有权限失败: {str(e)}")
    
    def get_role_permissions(self, role_id: int) -> List[Dict[str, Any]]:
        """
        获取角色的所有权限
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            List[Dict[str, Any]]: 权限列表
            
        Raises:
            ResourceNotFound: 角色不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        def _query():
            # 检查角色是否存在
            role = self.get_by_id(Role, role_id)
            
            # 获取角色权限
            role_permissions = self.db.query(RolePermission, Permission).\
                join(Permission, RolePermission.permission_id == Permission.id).\
                filter(RolePermission.role_id == role_id).all()
            
            result = []
            # 按模块分组
            grouped = {}
            
            for rp, permission in role_permissions:
                if permission.module not in grouped:
                    grouped[permission.module] = []
                
                grouped[permission.module].append({
                    "id": permission.id,
                    "code": permission.code,
                    "name": permission.name,
                    "description": permission.description,
                    "assigned_at": rp.assigned_at.isoformat() if rp.assigned_at else None
                })
            
            # 转换为列表
            for module, perms in grouped.items():
                result.append({
                    "module": module,
                    "permissions": perms
                })
            
            return result
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"获取角色权限失败: {str(e)}")
            raise DatabaseError(f"获取角色权限失败: {str(e)}")
    
    def check_permission(self, role_id: int, permission_code: str = None, permission_id: int = None) -> bool:
        """
        检查角色是否拥有指定权限
        
        Args:
            role_id (int): 角色ID
            permission_code (str, optional): 权限代码
            permission_id (int, optional): 权限ID
            
        Returns:
            bool: 是否拥有权限
            
        Raises:
            ResourceNotFound: 角色不存在时抛出
            ValueError: 未提供permission_id或permission_code时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        if permission_id is None and permission_code is None:
            raise ValueError("必须提供permission_id或permission_code")
        
        def _query():
            # 检查角色是否存在
            role = self.get_by_id(Role, role_id)
            
            try:
                # 根据提供的参数获取权限ID
                if permission_id is not None:
                    # 直接使用提供的权限ID
                    perm_id = permission_id
                    # 验证权限ID是否存在
                    self.get_by_id(Permission, perm_id)
                else:
                    # 通过权限代码获取权限
                    permission = self.get_permission_by_code(permission_code)
                    perm_id = permission.id
                
                # 检查角色是否拥有该权限
                role_permission = self.db.query(RolePermission).filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id == perm_id
                ).first()
                
                return role_permission is not None
                
            except ResourceNotFound as e:
                logger.warning(f"检查权限失败: {str(e)}")
                return False
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"检查权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"检查权限失败: {str(e)}")
            raise DatabaseError(f"检查权限失败: {str(e)}")
    
    def assign_permissions(self, role_id: int, permission_codes: Optional[List[str]] = None, permission_ids: Optional[List[int]] = None, expires_at: Optional[datetime] = None) -> Dict[str, Any]:
        """
        为角色分配权限
        
        Args:
            role_id (int): 角色ID
            permission_codes (Optional[List[str]]): 权限代码列表
            permission_ids (Optional[List[int]]): 权限ID列表
            expires_at (Optional[datetime]): 权限过期时间
            
        Returns:
            Dict[str, Any]: 分配结果
            
        Raises:
            ResourceNotFound: 角色不存在时抛出
            ValueError: 未提供permission_codes或permission_ids时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        if not permission_codes and not permission_ids:
            raise ValueError("必须提供permission_codes或permission_ids")
        
        def _query():
            # 检查角色是否存在
            role = self.get_by_id(Role, role_id)
            
            # 清除现有权限
            self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id
            ).delete()
            
            # 添加新权限
            added_count = 0
            failed_count = 0
            failed_items = []
            
            # 处理权限ID列表
            if permission_ids:
                for perm_id in permission_ids:
                    try:
                        # 验证权限ID是否存在
                        permission = self.get_by_id(Permission, perm_id)
                        
                        # 创建角色权限关联
                        role_permission = RolePermission(
                            role_id=role_id,
                            permission_id=perm_id,
                            assigned_at=datetime.now(),
                            expires_at=expires_at
                        )
                        
                        self.db.add(role_permission)
                        added_count += 1
                    except Exception as e:
                        logger.error(f"添加权限ID {perm_id} 失败: {str(e)}")
                        failed_count += 1
                        failed_items.append(f"ID:{perm_id}")
            
            # 处理权限代码列表
            if permission_codes:
                for code in permission_codes:
                    try:
                        # 获取权限
                        permission = self.get_permission_by_code(code)
                        
                        # 创建角色权限关联
                        role_permission = RolePermission(
                            role_id=role_id,
                            permission_id=permission.id,
                            assigned_at=datetime.now(),
                            expires_at=expires_at
                        )
                        
                        self.db.add(role_permission)
                        added_count += 1
                    except Exception as e:
                        logger.error(f"添加权限代码 {code} 失败: {str(e)}")
                        failed_count += 1
                        failed_items.append(f"Code:{code}")
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"成功为角色 {role.name} 分配 {added_count} 个权限" + 
                          (f", {failed_count} 个失败" if failed_count > 0 else ""),
                "failed_items": failed_items if failed_count > 0 else []
            }
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"分配权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"分配权限失败: {str(e)}")
            raise DatabaseError(f"分配权限失败: {str(e)}")
    
    def assign_menus(self, role_id: int, menu_ids: List[int]) -> Dict[str, Any]:
        """
        批量分配菜单给角色
        
        Args:
            role_id (int): 角色ID
            menu_ids (List[int]): 菜单ID列表
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            ResourceNotFound: 角色不存在
            BusinessError: 菜单不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 验证所有菜单是否存在
            menus = self.db.query(Menu).filter(Menu.id.in_(menu_ids)).all()
            found_menu_ids = {menu.id for menu in menus}
            missing_menu_ids = set(menu_ids) - found_menu_ids
            if missing_menu_ids:
                raise BusinessError(message=f"菜单ID不存在: {missing_menu_ids}")
            
            # 获取已分配的菜单
            existing_menus = self.db.query(RoleMenu).filter(
                and_(RoleMenu.role_id == role_id, RoleMenu.menu_id.in_(menu_ids))
            ).all()
            existing_menu_ids = {rm.menu_id for rm in existing_menus}
            
            # 添加新的菜单关联
            now = datetime.utcnow()
            added_count = 0
            for menu_id in menu_ids:
                if menu_id not in existing_menu_ids:
                    role_menu = RoleMenu(
                        role_id=role_id,
                        menu_id=menu_id,
                        assigned_at=now
                    )
                    self.db.add(role_menu)
                    added_count += 1
            
            if added_count > 0:
                self.db.commit()
                
            return {
                "success": True,
                "message": f"成功为角色 '{role.name}' 分配 {added_count} 个新菜单",
                "total_assigned": len(existing_menu_ids) + added_count
            }
            
        return self._safe_query(_query, f"批量分配菜单失败: 角色 {role_id}", {
            "success": False,
            "message": "操作失败",
            "total_assigned": 0
        })
        
    def revoke_menus(self, role_id: int, menu_ids: List[int]) -> Dict[str, Any]:
        """
        批量撤销角色的菜单
        
        Args:
            role_id (int): 角色ID
            menu_ids (List[int]): 菜单ID列表
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            ResourceNotFound: 角色不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查角色是否存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 删除指定的菜单关联
            result = self.db.query(RoleMenu).filter(
                and_(RoleMenu.role_id == role_id, RoleMenu.menu_id.in_(menu_ids))
            ).delete(synchronize_session=False)
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"已从角色 '{role.name}' 撤销 {result} 个菜单"
            }
            
        return self._safe_query(_query, f"批量撤销菜单失败: 角色 {role_id}", {
            "success": False,
            "message": "操作失败"
        })
    
    def get_role_detail(self, role_id: int) -> Dict[str, Any]:
        """
        获取角色的详细信息
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            Dict[str, Any]: 角色详细信息
            
        Raises:
            ResourceNotFound: 角色不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 获取角色
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 获取角色的菜单
            menus = self.db.query(Menu).join(
                RoleMenu, RoleMenu.menu_id == Menu.id
            ).filter(
                RoleMenu.role_id == role_id
            ).all()
            
            # 获取角色的用户数量
            user_count = self.db.query(UserRole).filter(
                UserRole.role_id == role_id
            ).count()
            
            # 获取角色的项目数量
            project_count = self.db.query(ProjectRole).filter(
                ProjectRole.role_id == role_id
            ).count()
            
            # 构建返回数据
            result = role.to_dict()
            result.update({
                "menus": [menu.to_dict(include_children=False) for menu in menus],
                "user_count": user_count,
                "project_count": project_count
            })
            
            return result
            
        return self._safe_query(_query, f"获取角色详细信息失败: ID {role_id}", {})
    
    def get_role_project_count(self, role_id: int) -> int:
        """
        获取角色关联的项目数量
        
        Args:
            role_id (int): 角色ID
            
        Returns:
            int: 项目数量
        """
        try:
            return self.db.query(ProjectRole).filter(
                ProjectRole.role_id == role_id
            ).count()
        except Exception as e:
            logger.error(f"获取角色 {role_id} 关联项目数量失败: {str(e)}")
            return 0

    def get_project_alleles(self, project_id: int) -> List[Dict[str, Any]]:
        """
        获取项目可用角色列表

        Args:
            project_id (int): 项目ID

        Returns:
            List[Dict[str, Any]]: 项目角色列表

        Raises:
            ResourceNotFound: 项目不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        try:
            def _query():
                # 查询项目类型的角色
                roles = self.db.query(Role).filter(
                    Role.role_type == "project",
                ).all()

                # 格式化角色数据
                result = []
                for role in roles:
                    result.append({
                        "id": role.id,
                        "name": role.name,
                        "description": role.description,
                        "created_at": role.created_at.strftime("%Y-%m-%d %H:%M:%S") if role.created_at else None,
                    })

                return result

            return self.safe_query(_query)
        except Exception as e:
            logger.error(f"获取项目 {project_id} 角色列表失败: {str(e)}")
            raise DatabaseError(message="获取项目角色列表失败", detail=str(e))

    def get_project_roles(self, project_id: int) -> List[Dict[str, Any]]:
        """
        获取项目可用角色列表
        
        Args:
            project_id (int): 项目ID
            
        Returns:
            List[Dict[str, Any]]: 项目角色列表
            
        Raises:
            ResourceNotFound: 项目不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        try:
            def _query():
                # 查询项目类型的角色
                roles = self.db.query(Role).filter(
                    Role.role_type == "project",
                    Role.is_active == True
                ).all()
                
                # 获取项目已分配的角色
                project_roles = self.db.query(ProjectRole.role_id).filter(
                    ProjectRole.project_id == project_id
                ).distinct().all()
                project_role_ids = [r.role_id for r in project_roles]
                
                # 格式化角色数据
                result = []
                for role in roles:
                    result.append({
                        "id": role.id,
                        "name": role.name,
                        "code": role.code,
                        "description": role.description,
                        "is_default": role.is_default,
                        "is_active": role.is_active,
                        "is_used": role.id in project_role_ids,
                        "created_at": role.created_at.strftime("%Y-%m-%d %H:%M:%S") if role.created_at else None,
                    })
                
                return result
            
            return self.safe_query(_query)
        except Exception as e:
            logger.error(f"获取项目 {project_id} 角色列表失败: {str(e)}")
            raise DatabaseError(message="获取项目角色列表失败", detail=str(e))
    
    def get_permission(self, permission_id: int) -> Permission:
        """
        获取权限信息
        
        Args:
            permission_id (int): 权限ID
            
        Returns:
            Permission: 权限对象
            
        Raises:
            ResourceNotFound: 权限不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        return self.get_by_id(Permission, permission_id)
    
    def get_permission_by_code(self, code: str) -> Permission:
        """
        根据权限代码获取权限信息
        
        Args:
            code (str): 权限代码
            
        Returns:
            Permission: 权限对象
            
        Raises:
            ResourceNotFound: 权限不存在时抛出
            DatabaseError: 数据库操作错误时抛出
        """
        permission = self.db.query(Permission).filter(Permission.code == code).first()
        if not permission:
            raise ResourceNotFound(f"权限代码 {code} 不存在")
        return permission
    
    def get_permissions(self, 
                       skip: int = 0, 
                       limit: int = 100, 
                       code: Optional[str] = None, 
                       module: Optional[str] = None) -> Tuple[List[Permission], int]:
        """
        获取权限列表
        
        Args:
            skip (int): 跳过记录数
            limit (int): 限制返回记录数
            code (str, optional): 权限代码，用于模糊匹配
            module (str, optional): 所属模块
            
        Returns:
            Tuple[List[Permission], int]: 权限列表和总数
        """
        def _query():
            query = self.db.query(Permission)
            
            if code:
                query = query.filter(Permission.code.like(f"%{code}%"))
            if module:
                query = query.filter(Permission.module == module)
                
            return query
        
        total = _query().count()
        items = _query().order_by(desc(Permission.id)).offset(skip).limit(limit).all()
        
        return items, total
    
    def create_permission(self, data: Dict[str, Any]) -> Permission:
        """
        创建权限
        
        Args:
            data (Dict[str, Any]): 权限数据
                - code (str): 权限代码
                - name (str): 权限名称
                - description (str, optional): 权限描述
                - module (str): 所属模块
                
        Returns:
            Permission: 创建的权限对象
            
        Raises:
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查权限代码是否已存在
            existing_permission = self.db.query(Permission).filter(
                Permission.code == data["code"]
            ).first()
            
            if existing_permission:
                raise BusinessError(f"权限代码 {data['code']} 已存在")
            
            # 创建权限
            permission = Permission(
                code=data["code"],
                name=data["name"],
                description=data.get("description"),
                module=data["module"]
            )
            
            self.db.add(permission)
            self.db.commit()
            self.db.refresh(permission)
            
            return permission
        
        try:
            return self.db_operation(_query)
        except Exception as e:
            logger.error(f"创建权限失败: {str(e)}")
            raise DatabaseError(f"创建权限失败: {str(e)}")
    
    def update_permission(self, permission_id: int, data: Dict[str, Any]) -> Permission:
        """
        更新权限
        
        Args:
            permission_id (int): 权限ID
            data (Dict[str, Any]): 权限数据
                - name (str, optional): 权限名称
                - description (str, optional): 权限描述
                - module (str, optional): 所属模块
                
        Returns:
            Permission: 更新后的权限对象
            
        Raises:
            ResourceNotFound: 权限不存在时抛出
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查权限是否存在
            permission = self.get_by_id(Permission, permission_id)
            
            # 更新权限
            if "name" in data:
                permission.name = data["name"]
            if "description" in data:
                permission.description = data["description"]
            if "module" in data:
                permission.module = data["module"]
            
            permission.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(permission)
            
            return permission
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"更新权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"更新权限失败: {str(e)}")
            raise DatabaseError(f"更新权限失败: {str(e)}")
    
    def delete_permission(self, permission_id: int) -> bool:
        """
        删除权限
        
        Args:
            permission_id (int): 权限ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            ResourceNotFound: 权限不存在时抛出
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查权限是否存在
            permission = self.get_by_id(Permission, permission_id)
            
            # 检查权限是否已被角色使用
            role_permission_count = self.db.query(RolePermission).filter(
                RolePermission.permission_id == permission_id
            ).count()
            
            if role_permission_count > 0:
                raise BusinessError(f"权限 {permission.name} 已被 {role_permission_count} 个角色使用，无法删除")
            
            # 检查权限是否已被菜单使用
            menu_count = self.db.query(Menu).filter(
                Menu.permission_id == permission_id
            ).count()
            
            if menu_count > 0:
                raise BusinessError(f"权限 {permission.name} 已被 {menu_count} 个菜单使用，无法删除")
            
            # 删除权限
            self.db.delete(permission)
            self.db.commit()
            
            return True
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"删除权限失败: {str(e)}")
            raise e
        except BusinessError as e:
            logger.error(f"删除权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"删除权限失败: {str(e)}")
            raise DatabaseError(f"删除权限失败: {str(e)}")
    
    def assign_permission(self, role_id: int, permission_id: int) -> Dict[str, Any]:
        """
        为角色分配权限
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            ResourceNotFound: 角色或权限不存在时抛出
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查角色是否存在
            role = self.get_by_id(Role, role_id)
            
            # 检查权限是否存在
            permission = self.get_by_id(Permission, permission_id)
            
            # 检查是否已分配
            existing = self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            ).first()
            
            if existing:
                return {"success": True, "message": f"权限 {permission.name} 已分配给角色 {role.name}"}
            
            # 创建关联
            role_permission = RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                assigned_at=datetime.now()
            )
            
            self.db.add(role_permission)
            self.db.commit()
            
            return {"success": True, "message": f"成功将权限 {permission.name} 分配给角色 {role.name}"}
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"分配权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"分配权限失败: {str(e)}")
            raise DatabaseError(f"分配权限失败: {str(e)}")
    
    def revoke_permission(self, role_id: int, permission_id: int) -> Dict[str, Any]:
        """
        从角色撤销权限
        
        Args:
            role_id (int): 角色ID
            permission_id (int): 权限ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            ResourceNotFound: 角色或权限关联不存在时抛出
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 检查角色是否存在
            role = self.get_by_id(Role, role_id)
            
            # 检查权限是否存在
            permission = self.get_by_id(Permission, permission_id)
            
            # 检查角色权限关联是否存在
            role_permission = self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id,
                RolePermission.permission_id == permission_id
            ).first()
            
            if not role_permission:
                return {"success": False, "message": f"角色 {role.name} 未分配权限 {permission.name}"}
            
            # 删除关联
            self.db.delete(role_permission)
            self.db.commit()
            
            return {"success": True, "message": f"成功从角色 {role.name} 撤销权限 {permission.name}"}
        
        try:
            return self.db_operation(_query)
        except ResourceNotFound as e:
            logger.error(f"撤销权限失败: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"撤销权限失败: {str(e)}")
            raise DatabaseError(f"撤销权限失败: {str(e)}")