import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { useSystemContext } from '../../context/SystemContext';
import { FlaskConical } from 'lucide-react';

export function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { testingMode } = useSystemContext();

  return (
    <div className="flex flex-col h-screen">
      {testingMode && (
        <div className="bg-amber-400 text-amber-900 text-xs font-bold flex items-center justify-center gap-2 py-1.5 px-4 shrink-0">
          <FlaskConical size={14} />
          MODO DE PRUEBA ACTIVO — Todas las restricciones de tiempo, quórum y requisitos académicos están deshabilitadas
          <FlaskConical size={14} />
        </div>
      )}
      <Header onMenuToggle={() => setSidebarOpen(o => !o)} />
      <div className="flex flex-1 overflow-hidden">
        <div className="hidden lg:flex lg:shrink-0">
          <Sidebar />
        </div>
        <div className="lg:hidden">
          <Sidebar
            isOpen={sidebarOpen}
            onClose={() => setSidebarOpen(false)}
          />
        </div>
        <main className="flex-1 overflow-auto bg-gray-50 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
