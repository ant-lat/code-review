import { get } from './request';
import type { ResponseBase } from './types';

// 获取所有权限列表
export const getAllPermissions = (type?: string): Promise<ResponseBase<any>> => {
  return get('/user-access/all-permissions', { params: { type } });
};

// 获取当前用户权限列表
export const getCurrentUserPermissions = (): Promise<ResponseBase<any>> => {
  return get('/user-access/permissions');
};

// 检查用户是否有指定权限
export const checkUserPermission = (permissionCode: string): Promise<ResponseBase<any>> => {
  return get('/user-access/check-permission', { params: { permission_code: permissionCode } });
}; 