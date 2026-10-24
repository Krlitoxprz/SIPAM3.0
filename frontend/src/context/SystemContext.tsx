import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { adminService } from '../services/api';
import { useAuthContext } from './AuthContext';

interface SystemContextType {
  testingMode: boolean;
  loadingMode: boolean;
  refreshMode: () => Promise<void>;
}

const SystemContext = createContext<SystemContextType>({
  testingMode: false,
  loadingMode: true,
  refreshMode: async () => {},
});

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

export function useSystemContext() {
  return useContext(SystemContext);
}
