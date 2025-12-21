// components/PrivateRoute.tsx
// 路由保护组件

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAppStore } from '@/store/useAppStore';

interface PrivateRouteProps {
  children: React.ReactNode;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ children }) => {
  const { currentUser, token } = useAppStore();
  const isAuthenticated = !!(currentUser && token);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default PrivateRoute;
