import { useState, useEffect, useCallback } from 'react';
import type { User } from '../types';
import { authService } from '../services/api';

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('sipam_user');
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem('sipam_token')
  );
  const [loading, setLoading] = useState(false);

  const login = useCallback(async (codigo: string, password: string) => {
    setLoading(true);
    try {
      const res = await authService.login(codigo, password);
      const { access_token, user: userData } = res.data;
      localStorage.setItem('sipam_token', access_token);
      localStorage.setItem('sipam_user', JSON.stringify(userData));
      setToken(access_token);
      setUser(userData);
      return userData;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('sipam_token');
    localStorage.removeItem('sipam_user');
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    if (token && !user) {
      authService.me().then((res) => {
        setUser(res.data);
        localStorage.setItem('sipam_user', JSON.stringify(res.data));
      }).catch(() => logout());
    }
  }, [token, user, logout]);

  const refreshUser = useCallback(async () => {
    try {
      const res = await authService.me();
      setUser(res.data);
      localStorage.setItem('sipam_user', JSON.stringify(res.data));
    } catch { /* ignore */ }
  }, []);

  return {
    user,
    token,
    isAuthenticated: !!token && !!user,
    loading,
    login,
    logout,
    refreshUser,
  };
}
