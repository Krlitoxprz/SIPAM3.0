import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell, BellOff, CheckCheck, Trash2, Loader2, RefreshCw,
  DollarSign, MapPin, BookOpen, AlertCircle, CheckCircle,
} from 'lucide-react';
import { notificacionesService } from '../services/api';

interface Notificacion {
  id: number;
  tipo: string;
  titulo: string;
  mensaje: string;
  leida: boolean;
  url?: string | null;
  created_at: string | null;
}

const TIPO_ICON: Record<string, React.ReactNode> = {
  presupuesto_solicitado:  <DollarSign size={16} className="text-blue-600" />,
  presupuesto_aprobado:    <CheckCircle size={16} className="text-emerald-600" />,
  presupuesto_rechazado:   <AlertCircle size={16} className="text-red-600" />,
  presupuesto_modificacion:<RefreshCw size={16} className="text-amber-600" />,
  presupuesto_incremento:  <DollarSign size={16} className="text-amber-600" />,
  practica_solicitada:     <MapPin size={16} className="text-blue-600" />,
  practica_aprobada:       <MapPin size={16} className="text-emerald-600" />,
  practica_rechazada:      <MapPin size={16} className="text-red-600" />,
  convocatoria:            <BookOpen size={16} className="text-indigo-600" />,
};

const TIPO_BG: Record<string, string> = {
  presupuesto_aprobado:    'bg-emerald-50 border-emerald-200',
  presupuesto_rechazado:   'bg-red-50 border-red-200',
  practica_rechazada:      'bg-red-50 border-red-200',
  practica_aprobada:       'bg-emerald-50 border-emerald-200',
  presupuesto_modificacion:'bg-amber-50 border-amber-200',
  presupuesto_incremento:  'bg-amber-50 border-amber-200',
};

function tiempoRelativo(fechaStr: string | null): string {
  if (!fechaStr) return '';
  const diff = (Date.now() - new Date(fechaStr).getTime()) / 1000;
  if (diff < 60) return 'Ahora';
  if (diff < 3600) return `Hace ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `Hace ${Math.floor(diff / 3600)}h`;
  if (diff < 604800) return `Hace ${Math.floor(diff / 86400)}d`;
  return new Date(fechaStr).toLocaleDateString('es-CO');
}

export function Notificaciones() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Notificacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'todas' | 'no_leidas'>('todas');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [markingAll, setMarkingAll] = useState(false);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const r = await notificacionesService.getMias();
      setItems(r.data);
    } catch { setItems([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  async function marcarLeida(id: number) {
    await notificacionesService.marcarLeida(id);
    setItems(prev => prev.map(n => n.id === id ? { ...n, leida: true } : n));
  }

  async function eliminar(id: number) {
    setDeletingId(id);
    await notificacionesService.eliminar(id);
    setItems(prev => prev.filter(n => n.id !== id));
    setDeletingId(null);
  }

  async function marcarTodas() {
    setMarkingAll(true);
    await notificacionesService.marcarTodasLeidas();
    setItems(prev => prev.map(n => ({ ...n, leida: true })));
    setMarkingAll(false);
  }

  async function handleClick(n: Notificacion) {
    if (!n.leida) await marcarLeida(n.id);
    if (n.url) navigate(n.url);
  }

  const visibles = tab === 'todas' ? items : items.filter(n => !n.leida);
  const noLeidas = items.filter(n => !n.leida).length;

  return (
    <div className="space-y-5 max-w-2xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Notificaciones</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {noLeidas > 0 ? `${noLeidas} sin leer` : 'Todo al día'}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={cargar} className="p-2 rounded-lg border border-gray-200 text-gray-500 hover:text-gray-700 hover:bg-gray-50">
            <RefreshCw size={15} />
          </button>
          {noLeidas > 0 && (
            <button onClick={marcarTodas} disabled={markingAll}
              className="flex items-center gap-1.5 text-xs font-semibold text-gray-600 border border-gray-200 px-3 py-2 rounded-lg hover:bg-gray-50 disabled:opacity-60">
              {markingAll ? <Loader2 size={13} className="animate-spin" /> : <CheckCheck size={13} />}
              Marcar todas leídas
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
        {([
          { key: 'todas', label: `Todas (${items.length})` },
          { key: 'no_leidas', label: `Sin leer (${noLeidas})` },
        ] as const).map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-1.5 text-sm font-semibold rounded-lg transition-all ${
              tab === t.key ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Lista */}
      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 size={24} className="animate-spin text-usco-vinotinto" />
        </div>
      ) : visibles.length === 0 ? (
        <div className="flex flex-col items-center py-20 gap-3 text-gray-400">
          <BellOff size={40} className="opacity-40" />
          <p className="text-sm">
            {tab === 'no_leidas' ? 'No tienes notificaciones sin leer.' : 'Aún no tienes notificaciones.'}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {visibles.map(n => {
            const bg = !n.leida
              ? (TIPO_BG[n.tipo] ?? 'bg-blue-50 border-blue-200')
              : 'bg-white border-gray-100';
            const icon = TIPO_ICON[n.tipo] ?? <Bell size={16} className="text-gray-400" />;
            return (
              <div key={n.id}
                className={`relative border rounded-xl px-4 py-3.5 transition-all ${bg} ${n.url ? 'cursor-pointer hover:shadow-sm' : ''}`}
                onClick={() => n.url && handleClick(n)}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 p-1.5 rounded-lg shrink-0 ${!n.leida ? 'bg-white shadow-sm' : 'bg-gray-50'}`}>
                    {icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-sm font-semibold leading-tight ${!n.leida ? 'text-gray-900' : 'text-gray-700'}`}>
                        {n.titulo}
                        {!n.leida && <span className="ml-2 inline-block w-1.5 h-1.5 bg-usco-vinotinto rounded-full align-middle" />}
                      </p>
                      <span className="text-[10px] text-gray-400 whitespace-nowrap shrink-0">{tiempoRelativo(n.created_at)}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed">{n.mensaje}</p>
                    {n.url && (
                      <p className="text-[11px] text-usco-vinotinto mt-1.5 font-medium">
                        Ver detalle →
                      </p>
                    )}
                  </div>
                </div>

                {/* Acciones */}
                <div className="flex gap-2 mt-2.5 pt-2.5 border-t border-white/60">
                  {!n.leida && (
                    <button
                      onClick={e => { e.stopPropagation(); marcarLeida(n.id); }}
                      className="flex items-center gap-1 text-[11px] font-semibold text-gray-500 hover:text-emerald-700 transition-colors">
                      <CheckCircle size={12} /> Marcar leída
                    </button>
                  )}
                  <button
                    onClick={e => { e.stopPropagation(); eliminar(n.id); }}
                    disabled={deletingId === n.id}
                    className="flex items-center gap-1 text-[11px] font-semibold text-gray-400 hover:text-red-600 transition-colors ml-auto">
                    {deletingId === n.id ? <Loader2 size={11} className="animate-spin" /> : <Trash2 size={11} />}
                    Eliminar
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {visibles.length > 0 && (
        <p className="text-center text-xs text-gray-400 pb-4">
          Mostrando {visibles.length} notificación{visibles.length !== 1 ? 'es' : ''}
        </p>
      )}
    </div>
  );
}
