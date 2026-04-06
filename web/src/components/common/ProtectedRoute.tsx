/**
 * Protected Route component that requires authentication
 */

import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, token } = useAuthStore();
  const { user, isCheckingAuth } = useAuth();

  // If no token, redirect to login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // Hold protected content until the persisted token has been validated.
  if (isCheckingAuth) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Spin size="large" tip="Verifying authentication..." />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};
