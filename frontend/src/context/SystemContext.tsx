import { useState, useEffect, useCallback, type ReactNode } from 'react';
import { adminService } from '../services/api';
import { useAuthContext } from '../hooks/useAuthContext';
import { SystemContext } from '../hooks/useSystemContext';

export function SystemProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuthContext();
  const [testingMode, setTestingMode] = useState(false);
  const [loadingMode, setLoadingMode] = useState(true);

  const refreshMode = useCallback(async () => {
    if (!isAuthenticated) { setLoadingMode(false); return; }
    try {
      const r = await adminService.getTestingMode();
      setTestingMode(r.data.testing_mode ?? false);
    } catch {
      setTestingMode(false);
    } finally {
      setLoadingMode(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshMode();
  }, [refreshMode]);

  return (
    <SystemContext.Provider value={{ testingMode, loadingMode, refreshMode }}>
      {children}
    </SystemContext.Provider>
  );
}
