import { get, post, put, del } from './request';
import type { 
  ResponseBase, 
  User, 
  UserRole, 
  UserCreateParams, 
  UserUpdateParams,
  PageResponse,
  Permission,
  PermissionGroup,
  PasswordChangeParams,
  PasswordResetParams,
  RolePermissionParams,
  UserPermissionParams
} from './types';

export interface UserQueryParams {
  page?: number;
  page_size?: number;
  username?: string;
  email?: string;
  role?: string;
  is_active?: boolean;
  skip?: number;
  limit?: number;
}

/**
 * 获取用户列表
 * @param params 查询参数
 */
export function getUsers(params: UserQueryParams = {}): Promise<ResponseBase<any>> {
  // 转换参数名称，以匹配后端API
  const apiParams: any = { ...params };
  return get<ResponseBase<any>>('users', apiParams);
}

/**
 * 获取用户详情
 * @param id 用户ID
 */
export function getUserById(id: number): Promise<ResponseBase<User>> {
  return get<ResponseBase<User>>(`/users/${id}`);
}

/**
 * 创建用户
 * @param data 用户数据
 */
export function createUser(data: UserCreateParams): Promise<ResponseBase<User>> {
  // 构建API参数，确保email字段存在
  const apiData = {
    ...data,
    email: data.email || `${data.username}@example.com` // 如果没有提供email，生成一个默认的
  };
  return post<ResponseBase<User>>('/users', apiData);
}

/**
 * 更新用户
 * @param id 用户ID
 * @param data 更新数据
 */
export function updateUser(id: number, data: UserUpdateParams): Promise<ResponseBase<User>> {
  return put<ResponseBase<User>>(`/users/${id}`, data);
}

/**
 * 删除用户
 * @param id 用户ID
 */
export function deleteUser(id: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/users/${id}`);
}

/**
 * 启用/禁用用户
 * @param id 用户ID
 * @param isActive 是否启用
 */
export function toggleUserStatus(id: number, isActive: boolean): Promise<ResponseBase<User>> {
  return put<ResponseBase<User>>(`/users/${id}`, { is_active: isActive });
}

/**
 * 修改用户密码（用户自己）
 * @param data 密码数据
 */
export function changePassword(data: PasswordChangeParams): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>('/users/change-password', data);
}

/**
 * 重置用户密码（管理员）
 * @param userId 用户ID
 * @param data 密码数据
 */
export function resetUserPassword(userId: number, data: PasswordResetRequest): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>(`/users/${userId}/reset-password`, data);
}

/**
 * 获取所有角色
 */
export function getRoles(): Promise<ResponseBase<UserRole[]>> {
  return get<ResponseBase<UserRole[]>>('/roles');
}

/**
 * 获取角色详情
 * @param id 角色ID
 */
export function getRoleById(id: number): Promise<ResponseBase<UserRole>> {
  return get<ResponseBase<UserRole>>(`/roles/${id}`);
}

/**
 * 创建角色
 * @param data 角色数据
 */
export function createRole(data: { name: string; description: string }): Promise<ResponseBase<UserRole>> {
  return post<ResponseBase<UserRole>>('/roles', data);
}

/**
 * 更新角色
 * @param id 角色ID
 * @param data 更新数据
 */
export function updateRole(id: number, data: { name?: string; description?: string }): Promise<ResponseBase<UserRole>> {
  return put<ResponseBase<UserRole>>(`/roles/${id}`, data);
}

/**
 * 删除角色
 * @param id 角色ID
 */
export function deleteRole(id: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/roles/${id}`);
}

/**
 * 获取所有权限
 */
export function getPermissions(): Promise<ResponseBase<Permission[]>> {
  return get<ResponseBase<Permission[]>>('/permissions');
}

/**
 * 获取按组分类的权限
 */
export function getPermissionGroups(): Promise<ResponseBase<PermissionGroup[]>> {
  return get<ResponseBase<PermissionGroup[]>>('/permissions/groups');
}

/**
 * 为角色分配权限
 * @param data 权限数据
 */
export function assignRolePermissions(data: RolePermissionParams): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>('/roles/permissions', data);
}

/**
 * 获取角色权限
 * @param roleId 角色ID
 */
export function getRolePermissions(roleId: number): Promise<ResponseBase<Permission[]>> {
  return get<ResponseBase<Permission[]>>(`/roles/${roleId}/permissions`);
}

/**
 * 为用户分配角色
 * @param userId 用户ID
 * @param roleIds 角色ID列表
 */
export function assignUserRoles(userId: number, roleIds: number[]): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>(`/users/${userId}/roles`, roleIds);
}

/**
 * 获取用户角色
 * @param userId 用户ID
 */
export function getUserRoles(userId: number): Promise<ResponseBase<any[]>> {
  return get<ResponseBase<any[]>>(`/users/${userId}/roles`);
}

/**
 * 从用户中移除角色
 * @param userId 用户ID
 * @param roleId 角色ID
 */
export function removeUserRole(userId: number, roleId: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/users/${userId}/roles/${roleId}`);
}

// 密码重置请求类型
export interface PasswordResetRequest {
  new_password: string;
  confirm_password: string;
} 