import { get, post, put, del } from './request';
import type { ResponseBase } from './types';

// 获取所有项目角色
export function getAllProjectRoles() {
  return get('/roles', { params: { role_type: 'project' } });
}

// 获取项目可用角色列表
export const getProjectRoles = (projectId: number): Promise<ResponseBase<any>> => {
  return get(`/projects/${projectId}/roles`);
};

// 获取项目所有可用角色列表（包括未分配的角色）
export const getProjectAllRoles = (projectId: number): Promise<ResponseBase<any>> => {
  return get(`/projects/${projectId}/allRoles`);
};

// 分配项目角色
export function assignProjectRole(projectId: number, userId: number, roleId: number) {
  return post(`/projects/${projectId}/member/${userId}/role`, { role_id: roleId });
}

// 移除项目角色
export function removeProjectRole(projectId: number, userId: number, roleId: number) {
  return del(`/projects/${projectId}/member/${userId}/role/${roleId}`);
} 