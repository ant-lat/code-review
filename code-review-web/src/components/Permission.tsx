import React from 'react';
import { getCurrentUser } from '../utils/auth';

/**
 * 权限控制组件的属性接口
 */
interface PermissionProps {
  /**
   * 需要的角色列表，用户拥有其中任一角色即可渲染子组件
   */
  roles?: string[];
  
  /**
   * 需要的权限代码列表，用户拥有其中任一权限即可渲染子组件
   */
  permissions?: string[];
  
  /**
   * 需要的项目角色列表，用户在当前项目中拥有其中任一角色即可渲染子组件
   */
  projectRoles?: string[];
  
  /**
   * 项目ID，如果提供了projectRoles，则需要同时提供项目ID
   */
  projectId?: number;
  
  /**
   * 子组件
   */
  children: React.ReactNode;
  
  /**
   * 无权限时的渲染内容，默认不渲染任何内容
   */
  fallback?: React.ReactNode;
  
  /**
   * 是否反转权限检查逻辑，默认为false
   * 设置为true时，当用户不满足权限条件时才渲染子组件
   */
  reverse?: boolean;
}

/**
 * 权限控制组件
 * 
 * 用于根据用户角色和权限控制UI元素的渲染
 * 
 * @example
 * // 只有管理员可见
 * <Permission roles={['admin']}>
 *   <Button>管理员操作</Button>
 * </Permission>
 * 
 * // 具有特定权限可见
 * <Permission permissions={['user:create', 'user:edit']}>
 *   <Button>添加用户</Button>
 * </Permission>
 * 
 * // 在项目中具有特定角色可见
 * <Permission projectRoles={['owner', 'manager']} projectId={1}>
 *   <Button>项目设置</Button>
 * </Permission>
 */
const Permission: React.FC<PermissionProps> = ({
  roles,
  permissions,
  projectRoles,
  projectId,
  children,
  fallback = null,
  reverse = false,
}) => {
  const currentUser = getCurrentUser();
  
  if (!currentUser) {
    return reverse ? children : fallback;
  }
  
  let hasPermission = false;
  
  // 检查系统角色
  if (roles && roles.length > 0) {
    hasPermission = roles.includes(currentUser.role);
  }
  
  // 检查权限代码（这里需要在用户对象中增加permissions属性）
  if (!hasPermission && permissions && permissions.length > 0 && (currentUser as any).permissions) {
    const userPermissions = (currentUser as any).permissions || [];
    hasPermission = permissions.some(p => userPermissions.includes(p));
  }
  
  // 检查项目角色（这里需要从其他地方获取用户在项目中的角色，如Redux中的状态）
  if (!hasPermission && projectRoles && projectRoles.length > 0 && projectId) {
    // 这里应该从某个地方获取用户在特定项目中的角色
    // 例如，从Redux中获取或者通过一个工具函数获取
    const projectRole = getUserProjectRole(currentUser.id, projectId);
    hasPermission = projectRole ? projectRoles.includes(projectRole) : false;
  }
  
  // 如果没有指定任何权限要求，默认有权限
  if (!roles && !permissions && !projectRoles) {
    hasPermission = true;
  }
  
  // 根据reverse属性决定渲染逻辑
  return (reverse ? !hasPermission : hasPermission) ? children : fallback;
};

/**
 * 获取用户在项目中的角色
 * 这是一个示例函数，实际实现应该从后端API获取或从Redux等状态管理中获取
 */
function getUserProjectRole(userId: number, projectId: number): string | null {
  // 在实际应用中，这里应该从Redux状态或其他状态管理工具中获取
  // 例如：
  // const { projectMembers } = useSelector((state: RootState) => state.projects);
  // const memberInfo = projectMembers.find(m => m.user_id === userId && m.project_id === projectId);
  // return memberInfo ? memberInfo.role : null;
  
  // 这里为了示例，返回null
  return null;
}

export default Permission; 