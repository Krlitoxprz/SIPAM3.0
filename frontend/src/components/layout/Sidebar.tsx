import { NavLink } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
  LayoutDashboard, BookOpen, ClipboardList, MapPin,
  DollarSign, Users, FileText, Settings, Star, Clock, UserCircle, Bell, ShieldCheck, Truck, CalendarDays, LogOut,
} from 'lucide-react';
import { notificacionesService } from '../../services/api';
import type { Rol } from '../../types';
import { useAuthContext } from '../../context/AuthContext';

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  roles: Rol[];
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: 'General',
    items: [
      { to: '/dashboard', label: 'Inicio', icon: <LayoutDashboard size={18} />, roles: ['admin', 'estudiante', 'profesor', 'jefe_programa', 'decano'] },
      { to: '/calendario', label: 'Calendario', icon: <CalendarDays size={18} />, roles: ['admin', 'estudiante', 'profesor', 'jefe_programa', 'decano'] },
    ],
  },
  {
    label: 'Monitorías',
    items: [
      { to: '/convocatorias', label: 'Convocatorias', icon: <BookOpen size={18} />, roles: ['admin', 'estudiante', 'profesor', 'jefe_programa', 'decano'] },
      { to: '/postulaciones', label: 'Mis Postulaciones', icon: <ClipboardList size={18} />, roles: ['estudiante'] },
      { to: '/evaluaciones', label: 'Evaluaciones', icon: <Star size={18} />, roles: ['profesor'] },
      { to: '/monitor-horas', label: 'Horas Monitor', icon: <Clock size={18} />, roles: ['admin', 'estudiante', 'profesor', 'jefe_programa', 'decano'] },
    ],
  },
  {
    label: 'Prácticas',
    items: [
      { to: '/practicas', label: 'Prácticas Extramuros', icon: <MapPin size={18} />, roles: ['admin', 'estudiante', 'profesor', 'jefe_programa', 'decano'] },
      { to: '/transporte', label: 'Transporte', icon: <Truck size={18} />, roles: ['admin'] },
    ],
  },
  {
    label: 'Administración',
    items: [
      { to: '/presupuesto', label: 'Presupuesto', icon: <DollarSign size={18} />, roles: ['jefe_programa', 'decano', 'admin'] },
      { to: '/reportes', label: 'Reportes', icon: <FileText size={18} />, roles: ['decano', 'admin'] },
      { to: '/configuracion', label: 'Configuración', icon: <Settings size={18} />, roles: ['admin'] },
      { to: '/admin', label: 'Panel de Control', icon: <ShieldCheck size={18} />, roles: ['admin'] },
      { to: '/usuarios', label: 'Usuarios', icon: <Users size={18} />, roles: ['admin'] },
    ],
  },
  {
    label: 'Mi Cuenta',
    items: [
      { to: '/notificaciones', label: 'Notificaciones', icon: <Bell size={18} />, roles: ['admin', 'estudiante', 'profesor', 'jefe_programa', 'decano'] },
      { to: '/perfil', label: 'Mi Perfil', icon: <UserCircle size={18} />, roles: ['admin', 'estudiante', 'profesor', 'jefe_programa', 'decano'] },
    ],
  },
];

const rolLabel: Record<Rol, string> = {
  admin: 'Administrador',
  estudiante: 'Estudiante',
  profesor: 'Profesor',
  jefe_programa: 'Jefe de Programa',
  decano: 'Decano de Facultad',
};

const rolColor: Record<Rol, string> = {
  admin: 'bg-purple-500/20 text-purple-300',
  estudiante: 'bg-emerald-500/20 text-emerald-300',
  profesor: 'bg-indigo-500/20 text-indigo-300',
  jefe_programa: 'bg-usco-vinotinto/30 text-red-200',
  decano: 'bg-rose-600/30 text-rose-200',
};

const rolIcon: Record<Rol, React.ReactNode> = {
  admin: <ShieldCheck size={11} />,
  estudiante: null, profesor: null, jefe_programa: null, decano: null,
};

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen = true, onClose }: SidebarProps) {
  const { user, logout } = useAuthContext();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!user) return;
    const poll = async () => {
      try { const r = await notificacionesService.getCount(); setUnread((r.data as { count: number }).count); } catch { /* silencioso */ }
    };
    poll();
    const id = setInterval(poll, 30000);
    return () => clearInterval(id);
  }, [user]);

  return (
    <>
      {onClose && isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={onClose}
        />
      )}
      <aside className={`
        w-64 bg-usco-gris text-white flex flex-col shadow-xl transition-transform duration-300
        ${onClose ? 'fixed inset-y-0 left-0 z-40 lg:relative lg:translate-x-0' : ''}
        ${onClose && !isOpen ? '-translate-x-full' : 'translate-x-0'}
      `}>
        <div className="px-4 py-4 border-b border-white/10">
          <p className="text-xs font-semibold uppercase tracking-widest text-usco-ocre mb-0.5">
            Facultad de Ingeniería
          </p>
          <p className="text-xs text-gray-300 truncate">
            {user?.programa ?? 'Universidad Surcolombiana'}
          </p>
        </div>

        <nav className="flex-1 px-2 py-3 overflow-y-auto space-y-3 no-scrollbar">
          {navGroups.map((group) => {
            const visibleItems = group.items.filter(item => user && item.roles.includes(user.rol));
            if (visibleItems.length === 0) return null;
            return (
              <div key={group.label}>
                <p className="px-3 mb-1 text-[10px] font-bold uppercase tracking-widest text-gray-500 select-none">
                  {group.label}
                </p>
                <div className="space-y-0.5">
                  {visibleItems.map((item) => (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      onClick={onClose}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                          isActive
                            ? 'bg-usco-vinotinto text-white shadow-sm'
                            : 'text-gray-300 hover:bg-white/10 hover:text-white'
                        }`
                      }
                    >
                      <span className="shrink-0">{item.icon}</span>
                      <span className="flex-1 truncate">{item.label}</span>
                      {item.to === '/notificaciones' && unread > 0 && (
                        <span className="text-[10px] font-bold bg-red-500 text-white rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 animate-pulse">
                          {unread > 99 ? '99+' : unread}
                        </span>
                      )}
                    </NavLink>
                  ))}
                </div>
              </div>
            );
          })}
        </nav>

        {user && (
          <div className="px-2 pb-2 border-t border-white/10 pt-2 space-y-1">
            <div className="bg-white/5 rounded-xl px-3 py-2.5">
              <p className="text-xs font-semibold text-white truncate">
                {user.nombres} {user.apellidos}
              </p>
              <div className="flex items-center justify-between mt-1">
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold flex items-center gap-1 ${rolColor[user.rol]}`}>
                  {rolIcon[user.rol]}
                  {rolLabel[user.rol]}
                </span>
                <span className="text-xs font-mono text-gray-400">{user.codigo}</span>
              </div>
            </div>
            <button
              onClick={logout}
              className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-red-500/20 hover:text-red-300 transition-colors"
            >
              <LogOut size={16} />
              <span>Cerrar sesión</span>
            </button>
          </div>
        )}

        <div className="px-4 py-1.5 border-t border-white/10">
          <p className="text-[10px] text-gray-600 text-center">
            SIPAM-USCO v1.0 · {new Date().getFullYear()}
          </p>
        </div>
      </aside>
    </>
  );
}
