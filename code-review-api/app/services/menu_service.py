"""
菜单服务模块
提供菜单相关的业务逻辑功能
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc, func
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from app.models.menu import Menu
from app.models.role_menu import RoleMenu
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.database import get_db, db_session
from app.config.logging_config import logger
from app.core.exceptions import ResourceNotFound, BusinessError, DatabaseError, AuthenticationError
from app.services.base_service import BaseService

class MenuService(BaseService[Menu]):
    """
    菜单服务类，处理菜单相关的业务逻辑
    """
    
    def __init__(self, db: Session):
        """
        初始化菜单服务
        
        Args:
            db (Session): 数据库会话
        """
        super().__init__(db)
    
    def create_menu(self, menu_data: Dict[str, Any]) -> Menu:
        """
        创建菜单
        
        Args:
            menu_data (Dict[str, Any]): 菜单数据
                - title (str): 菜单标题
                - path (str): 菜单路径
                - icon (Optional[str]): 菜单图标
                - parent_id (Optional[int]): 父菜单ID
                - order_num (Optional[int]): 排序号
                - permission_id (Optional[int]): 权限ID
                - component (Optional[str]): 组件路径
                - is_visible (Optional[bool]): 是否可见
                - is_cache (Optional[bool]): 是否缓存
                - menu_type (Optional[str]): 菜单类型(menu/button)
                
        Returns:
            Menu: 创建的菜单对象
            
        Raises:
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证父菜单存在
            if menu_data.get("parent_id"):
                parent_menu = self.db.query(Menu).filter(Menu.id == menu_data["parent_id"]).first()
                if not parent_menu:
                    raise ResourceNotFound(message=f"父菜单ID {menu_data['parent_id']} 不存在")
            
            # 验证路径唯一性
            if "path" in menu_data and menu_data["path"]:
                existing_menu = self.db.query(Menu).filter(Menu.path == menu_data["path"]).first()
                if existing_menu:
                    raise BusinessError(message=f"菜单路径 '{menu_data['path']}' 已存在")
            
            # 验证菜单类型
            menu_type = menu_data.get("menu_type", "menu")
            if menu_type not in ["menu", "button"]:
                raise BusinessError(message="菜单类型必须是 'menu' 或 'button'")
            
            # 验证权限ID是否存在
            permission_id = menu_data.get("permission_id")
            if permission_id is not None:
                permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
                if not permission:
                    raise ResourceNotFound(message=f"权限ID {permission_id} 不存在")
            
            # 创建菜单
            now = datetime.utcnow()
            
            new_menu = Menu(
                title=menu_data["title"],
                path=menu_data.get("path"),
                icon=menu_data.get("icon"),
                parent_id=menu_data.get("parent_id"),
                order_num=menu_data.get("order_num", 0),
                permission_id=permission_id,
                component=menu_data.get("component"),
                is_visible=menu_data.get("is_visible", True),
                is_cache=menu_data.get("is_cache", False),
                menu_type=menu_type,
                created_at=now,
                updated_at=now
            )
            
            self.db.add(new_menu)
            self.db.commit()
            self.db.refresh(new_menu)
            
            logger.info(f"菜单创建成功: {menu_data['title']}")
            return new_menu
        
        return self._safe_query(_query, f"创建菜单失败: {menu_data.get('title')}")
    
    def get_menu_by_id(self, menu_id: int) -> Menu:
        """
        通过ID获取菜单
        
        Args:
            menu_id (int): 菜单ID
            
        Returns:
            Menu: 菜单对象
            
        Raises:
            ResourceNotFound: 菜单不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            menu = self.db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise ResourceNotFound(message=f"菜单ID {menu_id} 不存在")
            return menu
        
        return self._safe_query(_query, f"获取菜单失败: 菜单ID {menu_id}")
    
    def update_menu(self, menu_id: int, menu_data: Dict[str, Any]) -> Menu:
        """
        更新菜单
        
        Args:
            menu_id (int): 菜单ID
            menu_data (Dict[str, Any]): 菜单数据
                - title (Optional[str]): 菜单标题
                - path (Optional[str]): 菜单路径
                - icon (Optional[str]): 菜单图标
                - parent_id (Optional[int]): 父菜单ID
                - order_num (Optional[int]): 排序号
                - permission_id (Optional[int]): 权限ID
                - component (Optional[str]): 组件路径
                - is_visible (Optional[bool]): 是否可见
                - is_cache (Optional[bool]): 是否缓存
                - menu_type (Optional[str]): 菜单类型(menu/button)
                
        Returns:
            Menu: 更新后的菜单对象
            
        Raises:
            ResourceNotFound: 菜单或父菜单不存在
            BusinessError: 菜单路径已存在或参数无效
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 获取菜单
            menu = self.db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise ResourceNotFound(message=f"菜单ID {menu_id} 不存在")
            
            # 验证父菜单存在
            parent_id = menu_data.get("parent_id")
            if parent_id is not None:
                # 不能将菜单的父菜单设置为自己
                if parent_id == menu_id:
                    raise BusinessError(message="不能将菜单的父菜单设置为自己")
                
                # 验证父菜单存在
                if parent_id:
                    parent = self.db.query(Menu).filter(Menu.id == parent_id).first()
                    if not parent:
                        raise ResourceNotFound(message=f"父菜单ID {parent_id} 不存在")
                
                menu.parent_id = parent_id
            
            # 如果更新路径，验证路径唯一性
            path = menu_data.get("path")
            if path and path != menu.path:
                existing_menu = self.db.query(Menu).filter(
                    and_(Menu.path == path, Menu.id != menu_id)
                ).first()
                if existing_menu:
                    raise BusinessError(message=f"菜单路径 '{path}' 已存在")
                
                menu.path = path
            
            # 验证菜单类型
            menu_type = menu_data.get("menu_type")
            if menu_type is not None:
                if menu_type not in ["menu", "button"]:
                    raise BusinessError(message="菜单类型必须是 'menu' 或 'button'")
                menu.menu_type = menu_type
            
            # 更新其他字段
            title = menu_data.get("title")
            if title:
                menu.title = title
            
            icon = menu_data.get("icon")
            if icon is not None:
                menu.icon = icon
            
            order_num = menu_data.get("order_num")
            if order_num is not None:
                menu.order_num = order_num
                
            permission_id = menu_data.get("permission_id")
            if permission_id is not None:
                menu.permission_id = permission_id
            
            component = menu_data.get("component")
            if component is not None:
                menu.component = component
            
            is_visible = menu_data.get("is_visible")
            if is_visible is not None:
                menu.is_visible = is_visible
            
            is_cache = menu_data.get("is_cache")
            if is_cache is not None:
                menu.is_cache = is_cache
            
            menu.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(menu)
            
            logger.info(f"菜单 {menu_id} 更新成功")
            return menu
        
        return self._safe_query(_query, f"更新菜单失败: 菜单ID {menu_id}")
    
    def delete_menu(self, menu_id: int) -> bool:
        """
        删除菜单
        
        Args:
            menu_id (int): 菜单ID
            
        Returns:
            bool: 删除是否成功
            
        Raises:
            ResourceNotFound: 菜单不存在
            BusinessError: 菜单有子菜单，无法删除
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 获取菜单
            menu = self.db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise ResourceNotFound(message=f"菜单ID {menu_id} 不存在")
            
            # 检查是否有子菜单
            has_children = self.db.query(Menu).filter(Menu.parent_id == menu_id).count() > 0
            if has_children:
                raise BusinessError(message="菜单有子菜单，请先删除子菜单")
            
            # 删除菜单
            self.db.delete(menu)
            self.db.commit()
            
            logger.info(f"菜单 {menu_id} 删除成功")
            return True
        
        return self._safe_query(_query, f"删除菜单失败: 菜单ID {menu_id}", False)
    
    def get_menu_tree(self, parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取菜单树
        
        Args:
            parent_id (Optional[int]): 父菜单ID
            
        Returns:
            List[Dict[str, Any]]: 菜单树
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def build_tree(p_id: Optional[int] = None) -> List[Dict[str, Any]]:
            # 查询子菜单
            menus = self.db.query(Menu).filter(Menu.parent_id == p_id).order_by(asc(Menu.order_num)).all()
            
            result = []
            for menu in menus:
                menu_dict = menu.to_dict(include_children=False)
                children = build_tree(menu.id)
                if children:
                    menu_dict['children'] = children
                result.append(menu_dict)
            return result
        
        def _query():
            return build_tree(parent_id)
        
        return self._safe_query(_query, "获取菜单树失败", [])
    
    def get_menus(self, skip: int = 0, limit: int = 50, parent_id: Optional[int] = None) -> Tuple[List[Menu], int]:
        """
        获取菜单列表
        
        Args:
            skip (int): 跳过的记录数
            limit (int): 返回的记录数
            parent_id (Optional[int]): 父菜单ID
            
        Returns:
            Tuple[List[Menu], int]: 菜单列表和总数
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 构建查询
            query = self.db.query(Menu)
            
            # 应用过滤条件
            if parent_id is not None:
                query = query.filter(Menu.parent_id == parent_id)
            
            # 获取总数
            total = query.count()
            
            # 应用分页和排序
            items = query.order_by(Menu.parent_id, Menu.order_num).offset(skip).limit(limit).all()
            
            return items, total
        
        return self._safe_query(_query, "获取菜单列表失败", ([], 0))
    
    @staticmethod
    def get_all_menus(db: Session) -> List[Menu]:
        """
        获取所有菜单
        
        Args:
            db (Session): 数据库会话
            
        Returns:
            List[Menu]: 菜单列表
        """
        return db.query(Menu).order_by(asc(Menu.order_num)).all()
    
    def get_user_menus(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户可访问的菜单列表
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            List[Dict[str, Any]]: 用户可访问的菜单树
            
        Raises:
            ResourceNotFound: 用户不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 获取用户
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ResourceNotFound(message=f"用户ID {user_id} 不存在")
            
            # 获取用户角色关联的所有菜单
            menu_ids = self.db.query(Menu.id).join(
                RoleMenu, Menu.id == RoleMenu.menu_id
            ).join(
                Role, RoleMenu.role_id == Role.id
            ).join(
                User, Role.id.in_([r.id for r in user.roles])
            ).distinct().all()
            
            menu_ids = [m[0] for m in menu_ids]
            
            def build_user_tree(p_id: Optional[int] = None) -> List[Dict[str, Any]]:
                menus = self.db.query(Menu).filter(
                    and_(
                        Menu.parent_id == p_id,
                        Menu.id.in_(menu_ids),
                        Menu.is_visible == True
                    )
                ).order_by(asc(Menu.order_num)).all()
                
                result = []
                for menu in menus:
                    menu_dict = menu.to_dict(include_children=False)
                    children = build_user_tree(menu.id)
                    if children:
                        menu_dict['children'] = children
                    result.append(menu_dict)
                return result
            
            return build_user_tree(None)
        
        return self._safe_query(_query, f"获取用户菜单失败: 用户ID {user_id}", [])
    
    @staticmethod
    def get_role_menus(db: Session, role_id: int) -> List[Menu]:
        """
        获取角色可访问的菜单
        
        Args:
            db (Session): 数据库会话
            role_id (int): 角色ID
            
        Returns:
            List[Menu]: 角色可访问的菜单列表
        """
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return []
            
        return role.menus
    
    def assign_menu_to_role(self, role_id: int, menu_id: int) -> Dict[str, Any]:
        """
        分配菜单给角色
        
        Args:
            role_id (int): 角色ID
            menu_id (int): 菜单ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            ResourceNotFound: 角色或菜单不存在
            BusinessError: 菜单已分配给角色
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证角色存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 验证菜单存在
            menu = self.db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise ResourceNotFound(message=f"菜单ID {menu_id} 不存在")
            
            # 检查是否已分配
            existing = self.db.query(RoleMenu).filter(
                and_(RoleMenu.role_id == role_id, RoleMenu.menu_id == menu_id)
            ).first()
            
            if existing:
                raise BusinessError(message=f"菜单 '{menu.title}' 已分配给角色 '{role.name}'")
            
            # 创建关联
            role_menu = RoleMenu(
                role_id=role_id,
                menu_id=menu_id,
                assigned_at=datetime.utcnow()
            )
            
            self.db.add(role_menu)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"菜单 '{menu.title}' 成功分配给角色 '{role.name}'"
            }
        
        return self._safe_query(_query, f"分配菜单失败: 角色 {role_id}, 菜单 {menu_id}", {
            "success": False,
            "message": "操作失败"
        })
    
    def revoke_menu_from_role(self, role_id: int, menu_id: int) -> Dict[str, Any]:
        """
        从角色撤销菜单
        
        Args:
            role_id (int): 角色ID
            menu_id (int): 菜单ID
            
        Returns:
            Dict[str, Any]: 操作结果
            
        Raises:
            ResourceNotFound: 角色或菜单不存在
            BusinessError: 菜单未分配给角色
            DatabaseError: 数据库操作错误
        """
        def _query():
            # 验证角色存在
            role = self.db.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise ResourceNotFound(message=f"角色ID {role_id} 不存在")
            
            # 验证菜单存在
            menu = self.db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                raise ResourceNotFound(message=f"菜单ID {menu_id} 不存在")
            
            # 检查是否已分配
            role_menu = self.db.query(RoleMenu).filter(
                and_(RoleMenu.role_id == role_id, RoleMenu.menu_id == menu_id)
            ).first()
            
            if not role_menu:
                raise BusinessError(message=f"菜单 '{menu.title}' 未分配给角色 '{role.name}'")
            
            # 删除关联
            self.db.delete(role_menu)
            self.db.commit()
            
            return {
                "success": True,
                "message": f"已从角色 '{role.name}' 撤销菜单 '{menu.title}'"
            }
        
        return self._safe_query(_query, f"撤销菜单失败: 角色 {role_id}, 菜单 {menu_id}", {
            "success": False,
            "message": "操作失败"
        }) 