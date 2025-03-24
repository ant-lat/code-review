/**
 * 权限Hook
 * @author Claude
 * @date 2023-07-15
 */

import { useCallback } from 'react';
import { 
  hasPermission, 
  hasAnyPermission, 
  hasAllPermissions, 
  hasRole, 
  getCurrentPermissions,
  getCurrentRole,
  isAdmin as checkIfAdmin,
  Permission,
  Role
} from '../utils/permission';

/**
 * 权限Hook，提供在组件中使用的权限检查函数
 */
export default function usePermission() {
  /**
   * 检查是否拥有指定权限
   */
  const checkPermission = useCallback((permission: Permission) => {
    return hasPermission(permission);
  }, []);
  
  /**
   * 检查是否拥有指定权限中的任意一个
   */
  const checkAnyPermission = useCallback((permissions: Permission[]) => {
    return hasAnyPermission(permissions);
  }, []);
  
  /**
   * 检查是否拥有指定权限中的所有权限
   */
  const checkAllPermissions = useCallback((permissions: Permission[]) => {
    return hasAllPermissions(permissions);
  }, []);
  
  /**
   * 检查是否拥有指定角色
   */
  const checkRole = useCallback((role: Role) => {
    return hasRole(role);
  }, []);
  
  /**
   * 获取当前用户的权限列表
   */
  const getUserPermissions = useCallback(() => {
    return getCurrentPermissions();
  }, []);
  
  /**
   * 获取当前用户的角色
   */
  const getUserRole = useCallback(() => {
    return getCurrentRole();
  }, []);
  
  /**
   * 检查是否为管理员
   */
  const isAdmin = useCallback(() => {
    return checkIfAdmin();
  }, []);
  
  return {
    checkPermission,
    checkAnyPermission,
    checkAllPermissions,
    checkRole,
    getUserPermissions,
    getUserRole,
    isAdmin
  };
} 