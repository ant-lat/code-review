import { get, post, put, del } from './request';
import type { ResponseBase, Project, ProjectCreateParams, ProjectMember, PageResponse } from './types';

export interface ProjectQueryParams {
  page?: number;
  page_size?: number;
  name?: string;
  repository_type?: string;
  is_active?: boolean;
}

/**
 * 获取项目列表
 * @param params 查询参数
 */
export function getProjects(params: ProjectQueryParams = {}): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/projects', params);
}

/**
 * 获取项目详情
 * @param id 项目ID
 * @param silent 是否静默处理错误（不显示错误提示）
 */
export function getProjectById(id: number, silent: boolean = true): Promise<ResponseBase<Project>> {
  return get<ResponseBase<Project>>(`/projects/${id}`, {}, { headers: { silent: String(silent) } });
}

/**
 * 创建项目
 * @param data 项目数据
 */
export function createProject(data: ProjectCreateParams): Promise<ResponseBase<Project>> {
  return post<ResponseBase<Project>>('/projects', data);
}

/**
 * 更新项目
 * @param id 项目ID
 * @param data 更新数据
 */
export function updateProject(id: number, data: Partial<ProjectCreateParams>): Promise<ResponseBase<Project>> {
  return put<ResponseBase<Project>>(`/projects/${id}`, data);
}

/**
 * 删除项目
 * @param id 项目ID
 */
export function deleteProject(id: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/projects/${id}`);
}

/**
 * 获取项目成员
 * @param projectId 项目ID
 * @param params 分页参数
 */
export function getProjectMembers(
  projectId: number, 
  params: { page?: number; page_size?: number } = {}
): Promise<PageResponse<ProjectMember>> {
  return get<PageResponse<ProjectMember>>(`/projects/${projectId}/members`, params);
}

/**
 * 获取项目可用角色
 */
export function getProjectRoles(): Promise<ResponseBase<any[]>> {
  return get<ResponseBase<any[]>>('/allRoles?role_type=project');
}

/**
 * 添加项目成员
 * @param projectId 项目ID
 * @param userId 用户ID
 * @param roleId 角色ID
 */
export function addProjectMember(
  projectId: number, 
  userId: number, 
  roleId: number
): Promise<ResponseBase<ProjectMember>> {
  return post<ResponseBase<ProjectMember>>(`/projects/${projectId}/members`, { 
    user_id: userId, 
    role_id: roleId 
  });
}

/**
 * 更新项目成员角色
 * @param projectId 项目ID
 * @param userId 用户ID
 * @param role 新角色
 */
export function updateProjectMemberRole(
  projectId: number, 
  userId: number, 
  role: string
): Promise<ResponseBase<ProjectMember>> {
  return put<ResponseBase<ProjectMember>>(`/projects/${projectId}/members/${userId}`, { role });
}

/**
 * 删除项目成员
 * @param projectId 项目ID
 * @param userId 用户ID
 */
export function removeProjectMember(projectId: number, userId: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/projects/${projectId}/users/${userId}`);
}

/**
 * 获取项目统计信息
 * @param projectId 项目ID
 * @param silent 是否静默处理错误（不显示错误提示）
 */
export function getProjectStats(projectId: number, silent: boolean = true): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>(`/projects/${projectId}/stats`, {}, { headers: { silent: String(silent) } });
}

/**
 * 获取项目活动
 * @param projectId 项目ID
 * @param params 分页参数
 * @param silent 是否静默处理错误（不显示错误提示）
 */
export function getProjectActivities(
  projectId: number, 
  params: { page?: number; page_size?: number; from_date?: string; to_date?: string } = {},
  silent: boolean = true
): Promise<PageResponse<any>> {
  return get<PageResponse<any>>(`/projects/${projectId}/activities`, params, { headers: { silent: String(silent) } });
}

/**
 * 获取项目详细统计数据
 * @param projectId 项目ID
 */
export function getProjectStatistics(projectId: number): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>(`/projects/${projectId}/statistics`);
} 