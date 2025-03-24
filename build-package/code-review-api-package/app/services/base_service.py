"""
基础服务模块
@author: pgao
@date: 2024-03-13
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Callable, Any, Type, Optional, List, Dict, TypeVar, Generic
import traceback

from app.config.logging_config import logger
from app.core.exceptions import DatabaseError, ResourceNotFound, BusinessError

T = TypeVar('T')  # 定义泛型类型变量，用于表示模型类型

class BaseService(Generic[T]):
    """
    基础服务类，提供通用的数据库操作和错误处理
    """
    
    def __init__(self, db: Session):
        """
        初始化基础服务
        
        Args:
            db (Session): 数据库会话
        """
        self.db = db
    
    def _safe_query(self, query_func: Callable, error_msg: str, default_value: Any = None) -> Any:
        """
        安全执行查询函数，统一处理异常
        
        Args:
            query_func (Callable): 查询函数
            error_msg (str): 错误消息
            default_value (Any): 发生异常时的默认返回值
            
        Returns:
            Any: 查询结果或默认值
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        try:
            return query_func()
        except SQLAlchemyError as e:
            logger.error(f"{error_msg}: {str(e)}")
            logger.debug(traceback.format_exc())
            self.db.rollback()
            raise DatabaseError(message=error_msg, detail=str(e))
        except Exception as e:
            logger.error(f"执行查询时发生未知错误: {str(e)}")
            logger.debug(traceback.format_exc())
            self.db.rollback()
            if default_value is not None:
                return default_value
            raise DatabaseError(message="查询执行失败", detail=str(e))
    
    def get_by_id(self, model_class: Type[T], entity_id: int) -> T:
        """
        通过ID获取实体
        
        Args:
            model_class (Type[T]): 模型类
            entity_id (int): 实体ID
            
        Returns:
            T: 实体对象
            
        Raises:
            ResourceNotFound: 实体不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            entity = self.db.query(model_class).filter(model_class.id == entity_id).first()
            if not entity:
                raise ResourceNotFound(message=f"{model_class.__name__} ID {entity_id} 不存在")
            return entity
        
        return self._safe_query(_query, f"获取 {model_class.__name__} (ID: {entity_id}) 失败")
    
    def get_all(self, model_class: Type[T], 
                skip: int = 0, 
                limit: int = 100, 
                filters: Optional[Dict[str, Any]] = None,
                order_by: Optional[List[Any]] = None) -> List[T]:
        """
        获取所有符合条件的实体
        
        Args:
            model_class (Type[T]): 模型类
            skip (int): 跳过记录数，默认0
            limit (int): 返回记录数，默认100
            filters (Optional[Dict[str, Any]]): 过滤条件
            order_by (Optional[List[Any]]): 排序条件
            
        Returns:
            List[T]: 实体列表
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        def _query():
            query = self.db.query(model_class)
            
            # 应用过滤条件
            if filters:
                for attr, value in filters.items():
                    if hasattr(model_class, attr):
                        if isinstance(value, list):
                            query = query.filter(getattr(model_class, attr).in_(value))
                        else:
                            query = query.filter(getattr(model_class, attr) == value)
            
            # 应用排序条件
            if order_by:
                for order in order_by:
                    query = query.order_by(order)
            
            # 应用分页
            query = query.offset(skip).limit(limit)
            
            return query.all()
        
        return self._safe_query(_query, f"获取 {model_class.__name__} 列表失败", [])
    
    def create(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """
        创建实体
        
        Args:
            model_class (Type[T]): 模型类
            data (Dict[str, Any]): 创建数据
            
        Returns:
            T: 创建的实体对象
            
        Raises:
            BusinessError: 业务逻辑错误
            DatabaseError: 数据库操作错误
        """
        def _query():
            entity = model_class(**data)
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        
        return self._safe_query(_query, f"创建 {model_class.__name__} 失败")
    
    def update(self, model_class: Type[T], entity_id: int, data: Dict[str, Any]) -> T:
        """
        更新实体
        
        Args:
            model_class (Type[T]): 模型类
            entity_id (int): 实体ID
            data (Dict[str, Any]): 更新数据
            
        Returns:
            T: 更新后的实体对象
            
        Raises:
            ResourceNotFound: 实体不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            entity = self.db.query(model_class).filter(model_class.id == entity_id).first()
            if not entity:
                raise ResourceNotFound(message=f"{model_class.__name__} ID {entity_id} 不存在")
            
            # 更新属性
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)
            
            self.db.commit()
            self.db.refresh(entity)
            return entity
        
        return self._safe_query(_query, f"更新 {model_class.__name__} (ID: {entity_id}) 失败")
    
    def delete(self, model_class: Type[T], entity_id: int) -> bool:
        """
        删除实体
        
        Args:
            model_class (Type[T]): 模型类
            entity_id (int): 实体ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            ResourceNotFound: 实体不存在
            DatabaseError: 数据库操作错误
        """
        def _query():
            entity = self.db.query(model_class).filter(model_class.id == entity_id).first()
            if not entity:
                raise ResourceNotFound(message=f"{model_class.__name__} ID {entity_id} 不存在")
            
            self.db.delete(entity)
            self.db.commit()
            return True
        
        return self._safe_query(_query, f"删除 {model_class.__name__} (ID: {entity_id}) 失败", False)
    
    def paginated_response(self, items: List[Any], total: int, page: int, page_size: int) -> Dict[str, Any]:
        """
        创建分页响应
        
        Args:
            items (List[Any]): 结果项目列表
            total (int): 总记录数
            page (int): 当前页码
            page_size (int): 每页大小
            
        Returns:
            Dict[str, Any]: 分页响应字典
        """
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size if page_size > 0 else 0
        }
    
    def standard_response(self, success: bool, data=None, message=None) -> Dict[str, Any]:
        """
        生成标准响应格式
        
        Args:
            success (bool): 操作是否成功
            data (Any, optional): 响应数据
            message (str, optional): 响应消息
            
        Returns:
            Dict[str, Any]: 标准响应
        """
        return {
            "success": success,
            "data": data,
            "message": message
        }
    
    def db_session(self, callback: Callable[[Session], Any]) -> Any:
        """
        执行数据库事务
        
        Args:
            callback (Callable): 要在事务中执行的回调函数，接收session参数
            
        Returns:
            Any: 回调函数的返回结果
            
        Raises:
            DatabaseError: 数据库操作错误
        """
        try:
            # 执行回调函数，传入session
            result = callback(self.db)
            
            # 提交事务
            self.db.commit()
            return result
        except SQLAlchemyError as e:
            # 发生SQLAlchemy异常时回滚事务
            self.db.rollback()
            logger.error(f"数据库事务执行失败: {str(e)}")
            logger.debug(traceback.format_exc())
            raise DatabaseError(message="数据库事务执行失败", detail=str(e))
        except Exception as e:
            # 发生其他异常时回滚事务
            self.db.rollback()
            logger.error(f"事务执行过程中发生异常: {str(e)}")
            logger.debug(traceback.format_exc())
            raise 