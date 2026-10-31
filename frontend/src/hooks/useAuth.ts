import { useState, useEffect, useCallback } from 'react';
import type { User } from '../types';
import { authService } from '../services/api';

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('sipam_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [loading, setLoading] = useState(false);

  const login = useCallback(async (codigo: string, password: string) => {
    setLoading(true);
    try {
      const res = await authService.login(codigo, password);
      const userData = res.data.user ?? res.data;
      // Token is now stored in HttpOnly cookie by the backend
      localStorage.setItem('sipam_user', JSON.stringify(userData));
      setUser(userData);
      return userData;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('sipam_user');
      setUser(null);
    }
  }, []);

  // Revalida la sesión contra el backend al montar: el usuario guardado en
  // localStorage puede tener datos desactualizados (rol, estado, foto) o el
  // token/cookie puede haber expirado.
  useEffect(() => {
    authService.me().then((res) => {
      setUser(res.data);
      localStorage.setItem('sipam_user', JSON.stringify(res.data));
    }).catch(() => {
      // Token invalid or expired
      localStorage.removeItem('sipam_user');
      setUser(null);
    });
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const res = await authService.me();
      setUser(res.data);
      localStorage.setItem('sipam_user', JSON.stringify(res.data));
    } catch { /* ignore */ }
  }, []);

  return {
    user,
    isAuthenticated: !!user,
    loading,
    login,
    logout,
    refreshUser,
  };
}
