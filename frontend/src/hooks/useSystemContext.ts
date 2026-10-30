import { createContext, useContext } from 'react';

export interface SystemContextType {
  testingMode: boolean;
  loadingMode: boolean;
  refreshMode: () => Promise<void>;
}

export const SystemContext = createContext<SystemContextType>({
  testingMode: false,
  loadingMode: true,
  refreshMode: async () => {},
});

export function useSystemContext() {
  return useContext(SystemContext);
}
