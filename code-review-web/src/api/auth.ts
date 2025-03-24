import { get, post, put } from './request';
import type { 
  ResponseBase, 
  User, 
  UserUpdateParams,
  PasswordChangeParams,
  PasswordResetRequestParams,
  PasswordResetVerifyParams,
  PasswordResetCompleteParams,
  LoginResult
} from './types';

export interface LoginParams {
  user_id: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
  refresh_token?: string;
}

export interface VerifyInfoParams {
  user_id: string;
  verification_type: string;
  answer: string;
}

export interface PasswordResetWithVerifyParams {
  user_id: string;
  verification_type: string;
  answer: string;
  new_password: string;
  confirm_password: string;
}

/**
 * 用户登录
 * @param data 登录参数
 */
export function login(data: LoginParams): Promise<ResponseBase<LoginResponse>> {
  return post<ResponseBase<LoginResponse>>('/auth/login', {
    user_id: data.user_id,
    password: data.password
  });
}

/**
 * 获取当前用户信息
 * @param options 请求选项 
 */
export function getCurrentUser(options = {}): Promise<ResponseBase<User>> {
  return get<ResponseBase<User>>('/auth/get_current_user', {}, options);
}

/**
 * 修改密码
 * @param data 密码数据
 */
export function changePassword(data: PasswordChangeParams) {
  return put<ResponseBase<any>>('/auth/password', data);
}

/**
 * 退出登录
 */
export function logout(): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>('/auth/logout', {});
}

/**
 * 获取用户权限和菜单
 */
export function getPermissionsAndMenus() {
  return get<ResponseBase<{ permissions: string[]; menus: any[] }>>('/auth/permissions');
}

/**
 * 刷新Token
 */
export function refreshToken(refreshToken: string) {
  return post<ResponseBase<{ access_token: string; refresh_token: string; expires_in: number }>>('/auth/refresh', { refresh_token: refreshToken });
}

/**
 * 请求密码重置（忘记密码）
 * @param data 包含用户ID的请求数据
 */
export function requestPasswordReset(data: PasswordResetRequestParams) {
  return post<ResponseBase<{verification_type: string; question: string}>>('/auth/forgot-password', data);
}

/**
 * 验证用户信息
 * @param data 验证数据
 */
export function verifyInfo(data: VerifyInfoParams) {
  return post<ResponseBase<any>>('/auth/verify-info', data);
}

/**
 * 完成密码重置
 * @param data 重置数据
 */
export function resetPassword(data: PasswordResetWithVerifyParams) {
  return post<ResponseBase<any>>('/auth/reset-password-with-verify', data);
}

/**
 * 更新当前用户信息
 * @param data 用户数据
 */
export function updateCurrentUser(data: Partial<UserUpdateParams>) {
  return put<ResponseBase<User>>('/auth/user', data);
}

/**
 * 获取当前用户菜单
 */
export function getUserMenus(): Promise<ResponseBase<any[]>> {
  return get<ResponseBase<any[]>>('/user-access/menus');
}

/**
 * 获取当前用户权限
 */
export function getUserPermissions(): Promise<ResponseBase<any[]>> {
  return get<ResponseBase<any[]>>('/user-access/permissions');
}

/**
 * 获取所有系统权限
 * @param type 可选的权限类型过滤
 */
export function getAllPermissions(type?: string): Promise<ResponseBase<any[]>> {
  const params = type ? { type } : {};
  return get<ResponseBase<any[]>>('/user-access/all-permissions', params);
}

/**
 * 检查当前用户是否有特定权限
 * @param permissionCode 权限代码
 */
export function checkPermission(permissionCode: string): Promise<ResponseBase<boolean>> {
  return get<ResponseBase<boolean>>('/user-access/check-permission', { permission_code: permissionCode });
} 