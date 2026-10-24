import { useState, useRef, useEffect } from 'react';
import { LogOut, User, Search, BookOpen, GraduationCap, MapPin, Users, X, Menu } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';
import { NotificacionesBell } from './NotificacionesBell';
import { busquedaService } from '../../services/api';

const rolLabels: Record<string, string> = {
  estudiante: 'Estudiante',
  profesor: 'Profesor',
  jefe_programa: 'Jefe de Programa',
  decano: 'Decano de Facultad',
};

interface BusqResultados {
  convocatorias: { id: number; titulo: string; estado: string }[];
  asignaturas: { id: number; codigo: string; nombre: string }[];
  practicas: { id: number; nombre: string; estado: string }[];
  usuarios: { id: number; nombre: string; codigo: string; rol: string }[];
}

export function Header({ onMenuToggle }: { onMenuToggle?: () => void }) {
  const { user, logout } = useAuthContext();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [resultados, setResultados] = useState<BusqResultados | null>(null);
  const [buscando, setBuscando] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (query.length < 2) { setResultados(null); return; }
    const t = setTimeout(async () => {
      setBuscando(true);
      try { const r = await busquedaService.buscar(query); setResultados(r.data.resultados); }
      catch { setResultados(null); }
      finally { setBuscando(false); }
    }, 350);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (dropRef.current && !dropRef.current.contains(e.target as Node) &&
          inputRef.current && !inputRef.current.contains(e.target as Node)) {
        setQuery(''); setResultados(null);
      }
    }
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  function irA(url: string) { setQuery(''); setResultados(null); navigate(url); }
  const totalRes = resultados ? Object.values(resultados).reduce((s, a) => s + a.length, 0) : 0;

  return (
    <header className="bg-usco-vinotinto text-white shadow-lg z-50">
      <div className="flex items-center justify-between px-6 py-3 gap-4">
        {onMenuToggle && (
          <button
            onClick={onMenuToggle}
            className="lg:hidden p-2 rounded-lg hover:bg-usco-vinotinto-dark transition-colors shrink-0"
            aria-label="Menú"
          >
            <Menu size={20} />
          </button>
        )}
        <div className="flex flex-col shrink-0">
          <span className="font-bold text-lg leading-tight tracking-wide">SIPAM-USCO</span>
          <span className="text-xs text-usco-ocre leading-tight">Sistema de Prácticas y Monitorías</span>
        </div>

        {/* Barra de búsqueda global (SF-07) */}
        <div className="relative flex-1 max-w-md">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/50 pointer-events-none" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Buscar convocatorias, asignaturas, prácticas…"
            className="w-full bg-white/15 text-white placeholder-white/50 pl-9 pr-8 py-2 rounded-lg text-sm focus:outline-none focus:bg-white/25 transition-colors"
          />
          {query && (
            <button onClick={() => { setQuery(''); setResultados(null); }}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-white/50 hover:text-white">
              <X size={14} />
            </button>
          )}

          {/* Dropdown de resultados */}
          {(buscando || (resultados && query.length >= 2)) && (
            <div ref={dropRef}
              className="absolute top-full left-0 right-0 mt-1 bg-white text-gray-800 rounded-xl shadow-2xl border border-gray-100 z-50 overflow-hidden max-h-80 overflow-y-auto">
              {buscando && (
                <div className="px-4 py-3 text-sm text-gray-400 text-center">Buscando…</div>
              )}
              {!buscando && totalRes === 0 && (
                <div className="px-4 py-3 text-sm text-gray-400 text-center">Sin resultados para "{query}"</div>
              )}
              {!buscando && resultados && resultados.convocatorias.length > 0 && (
                <div>
                  <p className="px-3 pt-2 pb-1 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Convocatorias</p>
                  {resultados.convocatorias.map(c => (
                    <button key={c.id} onClick={() => irA('/convocatorias')}
                      className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 text-left">
                      <BookOpen size={13} className="text-usco-vinotinto shrink-0" />
                      <span className="text-sm truncate">{c.titulo}</span>
                      <span className="ml-auto text-[10px] text-gray-400 shrink-0">{c.estado}</span>
                    </button>
                  ))}
                </div>
              )}
              {!buscando && resultados && resultados.asignaturas.length > 0 && (
                <div>
                  <p className="px-3 pt-2 pb-1 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Asignaturas</p>
                  {resultados.asignaturas.map(a => (
                    <button key={a.id} onClick={() => irA('/configuracion')}
                      className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 text-left">
                      <GraduationCap size={13} className="text-indigo-500 shrink-0" />
                      <span className="text-sm truncate">{a.nombre}</span>
                      <span className="ml-auto text-[10px] font-mono text-gray-400 shrink-0">{a.codigo}</span>
                    </button>
                  ))}
                </div>
              )}
              {!buscando && resultados && resultados.practicas.length > 0 && (
                <div>
                  <p className="px-3 pt-2 pb-1 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Prácticas</p>
                  {resultados.practicas.map(p => (
                    <button key={p.id} onClick={() => irA('/practicas')}
                      className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 text-left">
                      <MapPin size={13} className="text-emerald-500 shrink-0" />
                      <span className="text-sm truncate">{p.nombre}</span>
                      <span className="ml-auto text-[10px] text-gray-400 shrink-0">{p.estado}</span>
                    </button>
                  ))}
                </div>
              )}
              {!buscando && resultados && resultados.usuarios.length > 0 && (
                <div>
                  <p className="px-3 pt-2 pb-1 text-[10px] font-bold text-gray-400 uppercase tracking-widest">Usuarios</p>
                  {resultados.usuarios.map(u => (
                    <button key={u.id} onClick={() => irA('/usuarios')}
                      className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-50 text-left">
                      <Users size={13} className="text-amber-500 shrink-0" />
                      <span className="text-sm truncate">{u.nombre}</span>
                      <span className="ml-auto text-[10px] font-mono text-gray-400 shrink-0">{u.codigo}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <NotificacionesBell />
          <Link to="/perfil" className="flex items-center gap-2 bg-usco-vinotinto-dark rounded-lg px-3 py-2 hover:bg-black/20 transition-colors">
            <div className="bg-usco-ocre text-usco-vinotinto rounded-full p-1">
              <User size={16} />
            </div>
            <div className="flex flex-col text-right">
              <span className="text-sm font-semibold leading-tight">{user?.nombres} {user?.apellidos}</span>
              <span className="text-xs text-usco-ocre leading-tight">{user ? rolLabels[user.rol] : ''} · {user?.codigo}</span>
            </div>
          </Link>
          <button onClick={logout} className="p-2 rounded-full hover:bg-usco-vinotinto-dark transition-colors" title="Cerrar sesión">
            <LogOut size={20} />
          </button>
        </div>
      </div>
    </header>
  );
}
