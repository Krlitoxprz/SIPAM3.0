import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import type { Rol } from '../../types';
import { useAuthContext } from '../../context/AuthContext';

interface Props {
  children: ReactNode;
  allowedRoles?: Rol[];
}

export function ProtectedRoute({ children, allowedRoles }: Props) {
  const { isAuthenticated, user } = useAuthContext();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.rol)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}
