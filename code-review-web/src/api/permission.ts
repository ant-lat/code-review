import { get } from './request';
import type { ResponseBase } from './types';

/**
 * 权限对象接口
 */
export interface Permission {
  id: number;
  code: string;
  name: string;
  description?: string;
  module?: string;
}

/**
 * 菜单对象接口
 */
export interface Menu {
  id: number;
  title: string;
  path?: string;
  icon?: string;
  parent_id?: number;
  order_num?: number;
  permission_id?: number;
  permission?: Permission;
  children?: Menu[];
}

/**
 * 获取当前用户所有权限
 * @returns 用户拥有的所有权限列表
 */
export function getUserPermissions(): Promise<ResponseBase<Permission[]>> {
  return get<ResponseBase<Permission[]>>('/user-access/permissions');
}

/**
 * 根据权限代码检查当前用户权限
 * @param permissionCode 权限代码
 * @returns 是否拥有此权限
 */
export function checkPermissionByCode(permissionCode: string): Promise<ResponseBase<boolean>> {
  return get<ResponseBase<boolean>>(`/user-access/check-permission?permission_code=${encodeURIComponent(permissionCode)}`);
}

/**
 * 根据权限ID检查当前用户权限
 * @param permissionId 权限ID
 * @returns 是否拥有此权限
 */
export function checkPermissionById(permissionId: number): Promise<ResponseBase<boolean>> {
  return get<ResponseBase<boolean>>(`/user-access/check-permission?permission_id=${permissionId}`);
}

/**
 * 获取当前用户的菜单
 * @returns 用户有权限访问的所有菜单，包括嵌套结构
 */
export function getUserMenus(): Promise<ResponseBase<Menu[]>> {
  return get<ResponseBase<Menu[]>>('/user-access/menus');
} 