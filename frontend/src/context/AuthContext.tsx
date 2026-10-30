import type { ReactNode } from 'react';
import { useAuth } from '../hooks/useAuth';
import { AuthContext } from '../hooks/useAuthContext';
import type { Rol } from '../types';

export function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();

  const hasRole = (...roles: Rol[]) => {
    if (!auth.user) return false;
    return roles.includes(auth.user.rol);
  };

  return (
    <AuthContext.Provider value={{ ...auth, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}
