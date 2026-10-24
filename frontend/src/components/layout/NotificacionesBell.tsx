import { useState, useEffect, useRef, useCallback } from 'react';
import { Bell, X, CheckCheck, ExternalLink, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { notificacionesService } from '../../services/api';

interface Notificacion {
  id: number;
  tipo: string;
  titulo: string;
  mensaje: string;
  leida: boolean;
  url?: string | null;
  created_at: string;
}

const TIPO_COLOR: Record<string, string> = {
  presupuesto_solicitado: 'bg-blue-500',
  presupuesto_aprobado: 'bg-emerald-500',
  presupuesto_rechazado: 'bg-red-500',
  presupuesto_modificacion: 'bg-amber-500',
  practica_solicitada: 'bg-indigo-500',
  practica_aprobada: 'bg-emerald-500',
  practica_rechazada: 'bg-red-500',
  default: 'bg-gray-400',
};

function timeAgo(isoStr: string): string {
  const diff = Date.now() - new Date(isoStr).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 1) return 'ahora';
  if (min < 60) return `hace ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `hace ${h}h`;
  return `hace ${Math.floor(h / 24)}d`;
}

export function NotificacionesBell() {
  const [open, setOpen] = useState(false);
  const [nots, setNots] = useState<Notificacion[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const cargarCount = useCallback(async () => {
    try {
      const r = await notificacionesService.getCount();
      setCount(r.data.count);
    } catch { /* ignore */ }
  }, []);

  const cargarNots = useCallback(async () => {
    setLoading(true);
    try {
      const r = await notificacionesService.getMias();
      setNots(r.data);
      setCount(r.data.filter((n: Notificacion) => !n.leida).length);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    cargarCount();
    const interval = setInterval(cargarCount, 30000);
    return () => clearInterval(interval);
  }, [cargarCount]);

  useEffect(() => {
    if (open) cargarNots();
  }, [open, cargarNots]);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  async function marcarLeida(id: number) {
    await notificacionesService.marcarLeida(id);
    setNots(prev => prev.map(n => n.id === id ? { ...n, leida: true } : n));
    setCount(prev => Math.max(0, prev - 1));
  }

  async function marcarTodas() {
    await notificacionesService.marcarTodasLeidas();
    setNots(prev => prev.map(n => ({ ...n, leida: true })));
    setCount(0);
  }

  async function eliminar(id: number, e: React.MouseEvent) {
    e.stopPropagation();
    await notificacionesService.eliminar(id);
    setNots(prev => {
      const n = prev.find(x => x.id === id);
      if (n && !n.leida) setCount(c => Math.max(0, c - 1));
      return prev.filter(x => x.id !== id);
    });
  }

  function handleClick(n: Notificacion) {
    if (!n.leida) marcarLeida(n.id);
    if (n.url) { setOpen(false); navigate(n.url); }
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
      >
        <Bell size={20} />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {count > 9 ? '9+' : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl shadow-2xl border border-gray-100 z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
            <h3 className="text-sm font-bold text-gray-800">Notificaciones</h3>
            {nots.some(n => !n.leida) && (
              <button onClick={marcarTodas}
                className="flex items-center gap-1 text-xs text-usco-vinotinto hover:underline font-semibold">
                <CheckCheck size={12} /> Marcar todas
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
            {loading ? (
              <div className="flex justify-center py-6">
                <Loader2 size={20} className="animate-spin text-gray-400" />
              </div>
            ) : nots.length === 0 ? (
              <div className="py-8 text-center text-sm text-gray-400">Sin notificaciones</div>
            ) : nots.map(n => (
              <div
                key={n.id}
                onClick={() => handleClick(n)}
                className={`flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors ${!n.leida ? 'bg-blue-50/40' : ''}`}
              >
                <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${TIPO_COLOR[n.tipo] ?? TIPO_COLOR.default}`} />
                <div className="flex-1 min-w-0">
                  <p className={`text-xs font-semibold text-gray-800 leading-tight ${!n.leida ? '' : 'font-medium'}`}>
                    {n.titulo}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5 leading-snug line-clamp-2">{n.mensaje}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] text-gray-400">{timeAgo(n.created_at)}</span>
                    {n.url && <ExternalLink size={10} className="text-gray-400" />}
                  </div>
                </div>
                <button
                  onClick={(e) => eliminar(n.id, e)}
                  className="text-gray-300 hover:text-red-400 shrink-0 mt-0.5"
                >
                  <X size={13} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
