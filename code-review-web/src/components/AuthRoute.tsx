import React, { useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { isLoggedIn, hasRole, hasPermission } from '../utils/auth';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { hasMenuPermission, selectMenus } from '../store/slices/menuSlice';

interface AuthRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
}

/**
 * 路由权限控制组件
 * @param children 子组件
 * @param requiredRole 需要的角色，旧版方式
 * @param requiredPermission 需要的权限代码，推荐使用
 */
const AuthRoute: React.FC<AuthRouteProps> = ({ 
  children, 
  requiredRole, 
  requiredPermission 
}) => {
  const location = useLocation();
  const menus = useSelector(selectMenus);
  
  // 添加调试日志
  useEffect(() => {
    console.log('🔒 AuthRoute渲染:', {
      path: location.pathname,
      isLoggedIn: isLoggedIn(),
      requiredRole,
      requiredPermission,
    });
  }, [location.pathname, requiredRole, requiredPermission]);
  
  // 判断是否登录
  if (!isLoggedIn()) {
    // 重定向到登录页，并记录来源页面
    console.log('⚠️ 用户未登录，重定向到登录页，来源:', location.pathname);
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  // 权限检查 - 优先使用菜单权限检查
  if (menus.length > 0) {
    const hasMenuAccess = hasMenuPermission(menus, location.pathname);
    if (!hasMenuAccess) {
      console.log('⚠️ 用户无菜单权限，重定向到403页面，路径:', location.pathname);
      return <Navigate to="/403" replace />;
    }
  } 
  // 兼容旧版基于角色和直接权限代码的检查
  else if (requiredPermission && !hasPermission(requiredPermission)) {
    // 如果是dashboard页面，允许访问
    if (location.pathname === '/dashboard') {
      console.log('✅ dashboard页面允许访问');
      return <>{children}</>;
    }
    console.log('⚠️ 用户无权限，重定向到403页面，所需权限:', requiredPermission);
    return <Navigate to="/403" replace />;
  }
  else if (requiredRole && !hasRole(requiredRole)) {
    // 最不推荐的方式：直接基于角色判断
    console.log('⚠️ 用户无角色权限，重定向到403页面，所需角色:', requiredRole);
    return <Navigate to="/403" replace />;
  }
  
  console.log('✅ 认证通过，渲染受保护内容');
  return <>{children}</>;
};

export default AuthRoute; 