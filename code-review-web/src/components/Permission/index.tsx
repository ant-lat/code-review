import React, { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { checkUserPermission } from '../../api/permissions';

export interface PermissionProps {
  children: React.ReactNode;
  roles?: string[];
  codes?: string[];
  projectRoles?: string[];
  projectId?: number;
}

const Permission: React.FC<PermissionProps> = ({ 
  children, 
  roles = [], 
  codes = [],
  projectRoles = [], 
  projectId 
}) => {
  const { user, hasProjectRole } = useAuth();
  const [hasPermission, setHasPermission] = useState(false);

  useEffect(() => {
    const checkPermissions = async () => {
      if (!user) {
        setHasPermission(false);
        return;
      }

      // 检查用户角色权限
      const hasRole = roles.length === 0 || roles.some(role => user.roles?.includes(role));
      if (hasRole) {
        setHasPermission(true);
        return;
      }

      // 检查权限代码
      if (codes.length > 0) {
        try {
          const results = await Promise.all(
            codes.map(code => checkUserPermission(code))
          );
          if (results.some(res => res.data === true)) {
            setHasPermission(true);
            return;
          }
        } catch (error) {
          console.error('检查权限失败:', error);
        }
      }

      // 检查项目角色权限
      if (projectRoles.length > 0 && projectId) {
        const hasProjectRolePermission = projectRoles.some(role => hasProjectRole(projectId, role));
        if (hasProjectRolePermission) {
          setHasPermission(true);
          return;
        }
      }

      setHasPermission(false);
    };

    checkPermissions();
  }, [user, roles, codes, projectRoles, projectId]);

  if (!hasPermission) {
    return null;
  }

  return <>{children}</>;
};

export default Permission; 