/**
 * 权限控制工具函数
 * @author Claude
 * @date 2023-07-15
 */

import { getCurrentUser } from './auth';
import { permissionApi } from '../api';
import store from '../store';

// 权限类型定义
export type PermissionCode = string;
export type PermissionId = number;

// 权限对象定义，与API返回一致
export interface Permission {
  id: number;
  code: string;
  name: string;
  description?: string;
}

// 角色类型定义
export type Role = 'admin' | 'developer' | 'reviewer' | 'user';

/**
 * 获取当前用户的角色
 * @returns 用户角色
 */
export function getCurrentRole(): Role {
  const user = getCurrentUser();
  return (user?.role as Role) || 'user';
}

/**
 * 从Store中获取当前用户的权限列表
 * @returns 权限列表
 */
export function getCurrentPermissions(): Permission[] {
  // 从Redux store中获取权限列表
  const state = store.getState();
  // 根据实际状态结构调整
  const permissions = state.auth?.permissions || [];
  return permissions;
}

/**
 * 检查是否拥有指定角色
 * @param role 角色
 * @returns 是否拥有该角色
 */
export function hasRole(role: Role): boolean {
  return getCurrentRole() === role;
}

/**
 * 检查是否为管理员
 * @returns 是否为管理员
 */
export function isAdmin(): boolean {
  return hasRole('admin');
}

/**
 * 检查是否拥有指定权限代码
 * @param permissionCode 权限代码
 * @returns 是否拥有该权限
 */
export function hasPermissionByCode(permissionCode: PermissionCode): boolean {
  const permissions = getCurrentPermissions();
  return permissions.some(p => p.code === permissionCode);
}

/**
 * 检查是否拥有指定权限ID
 * @param permissionId 权限ID
 * @returns 是否拥有该权限
 */
export function hasPermissionById(permissionId: PermissionId): boolean {
  const permissions = getCurrentPermissions();
  return permissions.some(p => p.id === permissionId);
}

/**
 * 检查当前用户是否有特定权限
 * @param permission 权限代码或ID
 * @returns 是否拥有该权限
 */
export function hasPermission(permission: PermissionCode | PermissionId): boolean {
  const user = getCurrentUser();
  
  if (!user) return false;
  
  // 检查用户是否为管理员
  const isAdmin = user.roleNames?.includes('admin') ||
    (user.roles?.some(role => role.name === 'admin'));
    
  if (isAdmin) return true;

  // 如果权限是ID（数字类型）
  if (typeof permission === 'number') {
    // 检查permissions数组中是否包含此ID
    if (user.permissions && Array.isArray(user.permissions) && typeof user.permissions[0] === 'object') {
      return (user.permissions as Array<any>).some(p => p.id === permission);
    }
    return false;
  }
  
  // 如果权限是字符串代码
  const permCode = permission as string;
  
  // 先检查转换后的permissionCodes
  if (user.permissionCodes && user.permissionCodes.includes(permCode)) {
    return true;
  }
  
  // 检查原始的permissions数组
  if (user.permissions) {
    // 如果permissions是对象数组，检查code属性
    if (Array.isArray(user.permissions) && user.permissions.length > 0 && typeof user.permissions[0] === 'object') {
      return (user.permissions as Array<any>).some(p => p.code === permCode);
    }
    // 如果permissions是字符串数组
    else if (Array.isArray(user.permissions) && typeof user.permissions[0] === 'string') {
      return (user.permissions as string[]).includes(permCode);
    }
  }
  
  return false;
}

/**
 * 检查是否拥有指定权限中的任意一个
 * @param permissions 权限列表
 * @returns 是否拥有权限
 */
export function hasAnyPermission(permissions: (PermissionCode | PermissionId)[]): boolean {
  return permissions.some(permission => hasPermission(permission));
}

/**
 * 检查是否拥有指定权限中的所有权限
 * @param permissions 权限列表
 * @returns 是否拥有所有权限
 */
export function hasAllPermissions(permissions: (PermissionCode | PermissionId)[]): boolean {
  return permissions.every(permission => hasPermission(permission));
}

/**
 * 根据权限筛选菜单项
 * @param menuItems 菜单项列表
 * @returns 筛选后的菜单项
 */
export function filterMenuByPermission<T extends { permission?: PermissionCode | PermissionId | (PermissionCode | PermissionId)[] }>(menuItems: T[]): T[] {
  return menuItems.filter(item => {
    if (!item.permission) return true;
    
    if (Array.isArray(item.permission)) {
      return hasAnyPermission(item.permission);
    }
    
    return hasPermission(item.permission);
  });
}

/**
 * 检查当前用户是否有访问组件的权限
 * @param permission 所需权限或权限列表
 * @returns 是否有权限
 */
export function checkComponentPermission(permission: PermissionCode | PermissionId | (PermissionCode | PermissionId)[]): boolean {
  if (Array.isArray(permission)) {
    return hasAnyPermission(permission);
  }
  return hasPermission(permission);
}

/**
 * 异步检查权限
 * 这个方法会直接调用API进行权限检查，而不是从本地缓存获取
 * @param permission 权限代码或ID
 * @returns Promise<boolean>
 */
export async function checkPermissionAsync(permission: PermissionCode | PermissionId): Promise<boolean> {
  try {
    if (typeof permission === 'number') {
      const resp = await permissionApi.checkPermissionById(permission);
      return resp.data === true;
    } else {
      const resp = await permissionApi.checkPermissionByCode(permission);
      return resp.data === true;
    }
  } catch (error) {
    console.error('权限检查失败', error);
    return false;
  }
} 