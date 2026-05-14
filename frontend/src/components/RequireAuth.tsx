/**
 * Route guard component.
 */

import { Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from '@/stores/useAuthStore';
import { getAccessToken } from '@/utils/token';

interface RequireAuthProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
  allowedRoles?: string[];
}

const RequireAuth = ({ children, requireAdmin = false, allowedRoles }: RequireAuthProps) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const loading = useAuthStore((s) => s.loading);
  const getCurrentUser = useAuthStore((s) => s.getCurrentUser);

  useEffect(() => {
    if (!isAuthenticated && !loading && getAccessToken()) {
      getCurrentUser().catch(() => {
        // request interceptor handles expired/invalid tokens
      });
    }
  }, [getCurrentUser, isAuthenticated, loading]);

  if (loading || (!isAuthenticated && getAccessToken())) {
    return <div>加载中...</div>;
  }

  if (!isAuthenticated) {
    // Redirect to admin login for admin routes, regular login otherwise
    return <Navigate to={requireAdmin ? '/admin/login' : '/login'} replace />;
  }

  const roles = requireAdmin ? ['admin'] : allowedRoles;
  if (roles && (!user?.role || !roles.includes(user.role))) {
    return <Navigate to="/chat" replace />;
  }

  return <>{children}</>;
};

export default RequireAuth;
