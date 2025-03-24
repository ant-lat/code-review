import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  const { user, setUser } = context;

  const hasPermission = (code: string): boolean => {
    if (!user || !user.permissions) {
      return false;
    }
    return user.permissions.includes(code);
  };

  const hasProjectRole = (projectId: number, role: string): boolean => {
    if (!user || !user.projectRoles) {
      return false;
    }
    return user.projectRoles.some(pr => 
      pr.projectId === projectId && pr.roleName === role && pr.isActive
    );
  };

  return {
    user,
    setUser,
    hasPermission,
    hasProjectRole,
  };
};

export type { User } from '../contexts/AuthContext'; 