import { User } from '../api/types';
import { jwtDecode } from 'jwt-decode';

const TOKEN_KEY = 'token';
const USER_INFO_KEY = 'user';

// 为后端返回的权限定义接口
interface Permission {
  id: number;
  permission_id: number;
  code: string;
  name: string;
  description: string;
}

// 为后端返回的角色定义接口
interface Role {
  id: number;
  name: string;
  code?: string;
}

// 扩展User接口以匹配后端返回的数据
interface ExtendedUser extends Omit<User, 'roles'> {
  permissions?: Permission[];
  roles: Array<Role | string>;
}

/**
 * 获取Token
 */
export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * 设置Token
 * @param token Token字符串
 */
export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token);
};

/**
 * 移除Token
 */
export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * 判断是否有token
 */
export const hasToken = (): boolean => {
  return !!getToken();
};

/**
 * 获取当前用户信息
 */
export const getCurrentUser = (): ExtendedUser | null => {
  const userStr = localStorage.getItem(USER_INFO_KEY);
  if (userStr && userStr !== 'undefined' && userStr !== 'null') {
    try {
      return JSON.parse(userStr) as ExtendedUser;
    } catch (e) {
      console.error('解析用户信息失败:', e);
      return null;
    }
  }
  return null;
};

/**
 * 设置当前用户信息
 * @param user 用户信息
 */
export const setCurrentUser = (user: User): void => {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(user));
};

/**
 * 移除当前用户信息
 */
export const removeCurrentUser = (): void => {
  localStorage.removeItem(USER_INFO_KEY);
};

/**
 * 判断用户是否登录
 */
export const isLoggedIn = (): boolean => {
  const token = getToken();
  const userInfo = getCurrentUser();
  
  console.log('检查用户登录状态:', { hasToken: !!token, hasUserInfo: !!userInfo });
  
  // 简单检查token存在并且未过期
  if (!token) return false;
  
  // 检查token是否过期
  try {
    const decoded: any = jwtDecode(token);
    const currentTime = Date.now() / 1000;
    if (decoded.exp && decoded.exp < currentTime) {
      console.log('Token已过期');
      return false;
    }
  } catch (e) {
    console.error('解析token失败:', e);
    return false;
  }
  
  return true;
};

/**
 * 完整的登出操作
 */
export const logout = (): void => {
  removeToken();
  removeCurrentUser();
  // 可以在这里添加其他清除操作
  window.location.href = '/login';
};

/**
 * 检查用户是否有权限
 * @param requiredPermission 需要的权限代码
 */
export const hasPermission = (requiredPermission: string): boolean => {
  const user = getCurrentUser();
  if (!user) return false;
  
  // 管理员默认拥有所有权限
  if (user.roles && user.roles.some(role => 
    (typeof role === 'string' && role === 'admin') || 
    (typeof role === 'object' && (role.name === 'admin' || role.code === 'system_admin'))
  )) {
    return true;
  }
  
  // 使用后端返回的permissions数组
  const userPermissions = user.permissions || [];
  
  // 检查是否有指定的权限代码
  return userPermissions.some(permission => permission.code === requiredPermission);
};

/**
 * 检查用户是否有角色
 * @param requiredRole 需要的角色
 */
export const hasRole = (requiredRole: string): boolean => {
  const user = getCurrentUser();
  if (!user) return false;
  
  // 处理角色可能是对象或字符串的情况
  return user.roles.some(role => 
    (typeof role === 'string' && role === requiredRole) || 
    (typeof role === 'object' && (role.name === requiredRole || role.code === requiredRole))
  );
};

/**
 * 检查token是否过期
 */
export const isTokenExpired = (): boolean => {
  const token = getToken();
  if (!token) return true;

  try {
    const decoded: any = jwtDecode(token);
    // 将过期时间提前一分钟，避免边界情况
    const expTime = decoded.exp * 1000 - 60 * 1000;
    return Date.now() >= expTime;
  } catch (error) {
    console.error('解析token失败:', error);
    return true;
  }
};

/**
 * 保存用户信息到localStorage
 */
export const setUserInfo = (userInfo: any): void => {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
};

/**
 * 从localStorage获取用户信息
 */
export const getUserInfo = (): any => {
  const userInfoStr = localStorage.getItem(USER_INFO_KEY);
  if (!userInfoStr || userInfoStr === 'undefined' || userInfoStr === 'null') {
    return null;
  }
  try {
    return JSON.parse(userInfoStr);
  } catch (e) {
    console.error('解析用户信息失败:', e);
    return null;
  }
};

/**
 * 从localStorage移除用户信息
 */
export const removeUserInfo = (): void => {
  localStorage.removeItem(USER_INFO_KEY);
}; 