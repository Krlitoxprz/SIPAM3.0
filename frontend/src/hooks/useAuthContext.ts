import { createContext, useContext } from 'react';
import type { User, Rol } from '../types';

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (codigo: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  hasRole: (...roles: Rol[]) => boolean;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used inside AuthProvider');
  return ctx;
}
