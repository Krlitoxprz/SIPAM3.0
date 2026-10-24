import { useEffect, useState, useCallback } from 'react';
import {
  CalendarDays, BookOpen, MapPin, Trash2, Plus, Pencil,
  CheckCircle, ChevronDown, ChevronUp, Loader2,
  AlertTriangle, Search, RefreshCw, ToggleLeft, ToggleRight,
} from 'lucide-react';
import { adminService } from '../services/api';

// ── Tipos ──────────────────────────────────────────────────────────────────

interface Semestre {
  id: number;
  periodo_academico: string;
  fecha_inicio_semestre: string;
  fecha_fin_semestre: string;
  semana_inicio_solicitudes: number;
  semana_fin_solicitudes: number;
  is_active: boolean;
  estado: 'activo' | 'futuro' | 'pasado' | 'inactivo';
  created_at: string | null;
  updated_at: string | null;
}

interface MonitoriaItem {
  id: number;
  titulo: string;
  estado: string;
  periodo_academico: string;
  tipo_monitoria: string | null;
  asignatura: string | null;
  profesor: string | null;
  num_monitores_requeridos: number;
  postulaciones: number;
  created_at: string | null;
}

interface PostulacionItem {
  id: number;
  estado: string;
  estudiante: string | null;
  codigo_estudiante: string | null;
  promedio: number | null;
  created_at: string | null;
}

interface PracticaItem {
  id: number;
  nombre_practica: string;
  estado: string;
  periodo_academico: string;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  asignatura: string | null;
  programa: string | null;
  profesor: string | null;
  municipio: string | null;
  created_at: string | null;
}

// ── Helpers ────────────────────────────────────────────────────────────────

const fmtDate = (iso: string | null) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' });
};

const ESTADO_SEMESTRE: Record<string, { label: string; color: string }> = {
  activo:   { label: 'Activo',   color: 'bg-emerald-100 text-emerald-700' },
  futuro:   { label: 'Futuro',   color: 'bg-blue-100 text-blue-700' },
  pasado:   { label: 'Pasado',   color: 'bg-gray-100 text-gray-500' },
  inactivo: { label: 'Inactivo', color: 'bg-amber-100 text-amber-600' },
};

const ESTADO_MONITORIA: Record<string, string> = {
  borrador: 'bg-gray-100 text-gray-600',
  abierta: 'bg-emerald-100 text-emerald-700',
  cerrada: 'bg-amber-100 text-amber-700',
  en_evaluacion: 'bg-blue-100 text-blue-700',
  finalizada: 'bg-usco-vinotinto/10 text-usco-vinotinto',
};

const ESTADO_PRACTICA: Record<string, string> = {
  borrador: 'bg-gray-100 text-gray-600',
  solicitada: 'bg-blue-100 text-blue-700',
  pendiente_quorum: 'bg-amber-100 text-amber-700',
  aprobada_curriculo: 'bg-cyan-100 text-cyan-700',
  aprobada_facultad: 'bg-violet-100 text-violet-700',
  rechazada: 'bg-red-100 text-red-700',
  aprobado_transporte: 'bg-emerald-100 text-emerald-700',
  en_ejecucion: 'bg-indigo-100 text-indigo-700',
  finalizada: 'bg-usco-vinotinto/10 text-usco-vinotinto',
};

const PROGRAMAS = [
  'Ingeniería Agroindustrial',
  'Ingeniería Agrícola',
  'Ingeniería Civil',
  'Ingeniería de Petróleos',
  'Ingeniería de Software',
];

// ── Confirm Dialog ─────────────────────────────────────────────────────────

function ConfirmDialog({
  message,
  onConfirm,
  onCancel,
}: {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm mx-4">
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle size={22} className="text-red-500 shrink-0" />
          <p className="text-sm text-gray-700 font-medium">{message}</p>
        </div>
        <div className="flex gap-3 justify-end">
          <button onClick={onCancel}
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
            Cancelar
          </button>
          <button onClick={onConfirm}
            className="px-4 py-2 text-sm font-semibold text-white bg-red-600 hover:bg-red-700 rounded-lg">
            Eliminar
          </button>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
//  TAB: SEMESTRES
// ══════════════════════════════════════════════════════════════════════════

const EMPTY_FORM = {
  periodo_academico: '',
  fecha_inicio_semestre: '',
  fecha_fin_semestre: '',
  semana_inicio_solicitudes: 3,
  semana_fin_solicitudes: 14,
  is_active: false,
};

function SemestresTab() {
  const [semestres, setSemestres] = useState<Semestre[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [modal, setModal] = useState<'crear' | 'editar' | null>(null);
  const [editTarget, setEditTarget] = useState<Semestre | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [confirm, setConfirm] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await adminService.getSemestres();
      setSemestres(r.data);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCrear = () => {
    setForm(EMPTY_FORM);
    setEditTarget(null);
    setModal('crear');
    setError('');
  };

  const openEditar = (s: Semestre) => {
    setEditTarget(s);
    setForm({
      periodo_academico: s.periodo_academico,
      fecha_inicio_semestre: s.fecha_inicio_semestre.slice(0, 16),
      fecha_fin_semestre: s.fecha_fin_semestre.slice(0, 16),
      semana_inicio_solicitudes: s.semana_inicio_solicitudes,
      semana_fin_solicitudes: s.semana_fin_solicitudes,
      is_active: s.is_active,
    });
    setModal('editar');
    setError('');
  };

  const guardar = async () => {
    setError('');
    if (!form.periodo_academico || !form.fecha_inicio_semestre || !form.fecha_fin_semestre) {
      setError('Todos los campos son obligatorios.');
      return;
    }
    if (form.semana_inicio_solicitudes >= form.semana_fin_solicitudes) {
      setError('La semana de inicio debe ser menor a la semana de fin.');
      return;
    }
    setSaving(true);
    try {
      const payload = {
        ...form,
        fecha_inicio_semestre: new Date(form.fecha_inicio_semestre).toISOString(),
        fecha_fin_semestre: new Date(form.fecha_fin_semestre).toISOString(),
      };
      if (modal === 'crear') {
        await adminService.crearSemestre(payload);
      } else if (editTarget) {
        const { periodo_academico: _, ...updatePayload } = payload;
        void _;
        await adminService.actualizarSemestre(editTarget.id, updatePayload);
      }
      setModal(null);
      await load();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al guardar. Revisa los datos.');
    } finally { setSaving(false); }
  };

  const activar = async (id: number) => {
    try {
      await adminService.activarSemestre(id);
      await load();
    } catch { /* silent */ }
  };

  const eliminar = async (id: number) => {
    try {
      await adminService.eliminarSemestre(id);
      setConfirm(null);
      await load();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      alert(msg || 'No se pudo eliminar el semestre.');
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{semestres.length} semestres registrados</p>
        <button onClick={openCrear}
          className="flex items-center gap-2 text-sm font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 px-4 py-2 rounded-xl transition-colors">
          <Plus size={15} /> Nuevo semestre
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={28} className="animate-spin text-usco-vinotinto" /></div>
      ) : semestres.length === 0 ? (
        <div className="text-center py-12 text-sm text-gray-400">No hay semestres configurados.</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-100">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left">Período</th>
                <th className="px-4 py-3 text-left">Inicio</th>
                <th className="px-4 py-3 text-left">Fin</th>
                <th className="px-4 py-3 text-center">Sem. solicitudes</th>
                <th className="px-4 py-3 text-center">Estado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {semestres.map(s => {
                const est = ESTADO_SEMESTRE[s.estado] ?? ESTADO_SEMESTRE.inactivo;
                return (
                  <tr key={s.id} className="hover:bg-gray-50/60 transition-colors">
                    <td className="px-4 py-3 font-semibold text-gray-800">{s.periodo_academico}</td>
                    <td className="px-4 py-3 text-gray-600">{fmtDate(s.fecha_inicio_semestre)}</td>
                    <td className="px-4 py-3 text-gray-600">{fmtDate(s.fecha_fin_semestre)}</td>
                    <td className="px-4 py-3 text-center text-gray-600">
                      Sem. {s.semana_inicio_solicitudes} → {s.semana_fin_solicitudes}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${est.color}`}>
                        {est.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 justify-end">
                        {!s.is_active && (
                          <button onClick={() => activar(s.id)} title="Activar semestre"
                            className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors">
                            <ToggleLeft size={16} />
                          </button>
                        )}
                        {s.is_active && s.estado === 'activo' && (
                          <span title="Semestre en curso" className="p-1.5 text-emerald-500">
                            <ToggleRight size={16} />
                          </span>
                        )}
                        <button onClick={() => openEditar(s)} title="Editar"
                          className="p-1.5 text-usco-gris hover:bg-gray-100 rounded-lg transition-colors">
                          <Pencil size={14} />
                        </button>
                        <button onClick={() => setConfirm(s.id)} title="Eliminar"
                          className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal crear/editar */}
      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-lg mx-4">
            <h2 className="text-base font-bold text-gray-800 mb-4">
              {modal === 'crear' ? 'Nuevo semestre' : `Editar — ${editTarget?.periodo_academico}`}
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="text-xs font-semibold text-gray-600 mb-1 block">Período académico</label>
                <input
                  value={form.periodo_academico}
                  onChange={e => setForm(f => ({ ...f, periodo_academico: e.target.value }))}
                  disabled={modal === 'editar'}
                  placeholder="Ej: 2026-1"
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 disabled:bg-gray-50"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">Inicio del semestre</label>
                <input type="datetime-local"
                  value={form.fecha_inicio_semestre}
                  onChange={e => setForm(f => ({ ...f, fecha_inicio_semestre: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">Fin del semestre</label>
                <input type="datetime-local"
                  value={form.fecha_fin_semestre}
                  onChange={e => setForm(f => ({ ...f, fecha_fin_semestre: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">Semana inicio solicitudes</label>
                <input type="number" min={1} max={30}
                  value={form.semana_inicio_solicitudes}
                  onChange={e => setForm(f => ({ ...f, semana_inicio_solicitudes: Number(e.target.value) }))}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 mb-1 block">Semana fin solicitudes</label>
                <input type="number" min={1} max={32}
                  value={form.semana_fin_solicitudes}
                  onChange={e => setForm(f => ({ ...f, semana_fin_solicitudes: Number(e.target.value) }))}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
                />
              </div>
              <div className="sm:col-span-2 flex items-center gap-3">
                <input type="checkbox" id="isActive"
                  checked={form.is_active}
                  onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))}
                  className="w-4 h-4 accent-usco-vinotinto"
                />
                <label htmlFor="isActive" className="text-sm text-gray-700">
                  Designar como semestre activo
                  <span className="ml-1 text-xs text-gray-400">(desactivará los demás)</span>
                </label>
              </div>
            </div>

            {error && (
              <div className="mt-3 flex items-center gap-2 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                <AlertTriangle size={14} className="text-red-500 shrink-0" />
                <p className="text-xs text-red-700">{error}</p>
              </div>
            )}

            <div className="flex gap-3 mt-5 justify-end">
              <button onClick={() => setModal(null)}
                className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50">
                Cancelar
              </button>
              <button onClick={guardar} disabled={saving}
                className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 rounded-xl disabled:opacity-60">
                {saving ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                {modal === 'crear' ? 'Crear semestre' : 'Guardar cambios'}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirm !== null && (
        <ConfirmDialog
          message="¿Eliminar este semestre? Esta acción es irreversible."
          onConfirm={() => eliminar(confirm)}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
//  TAB: MONITORÍAS
// ══════════════════════════════════════════════════════════════════════════

function MonitoriasTab() {
  const [items, setItems] = useState<MonitoriaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [estado, setEstado] = useState('');
  const [expanded, setExpanded] = useState<number | null>(null);
  const [posts, setPosts] = useState<PostulacionItem[]>([]);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [confirm, setConfirm] = useState<{ type: 'conv' | 'post'; id: number } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await adminService.getMonitorias({ estado: estado || undefined, q: q || undefined });
      setItems(r.data);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [q, estado]);

  useEffect(() => { load(); }, [load]);

  const expandir = async (id: number) => {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    setLoadingPosts(true);
    try {
      const r = await adminService.getPostulacionesConvocatoria(id);
      setPosts(r.data);
    } catch { /* silent */ }
    finally { setLoadingPosts(false); }
  };

  const eliminar = async () => {
    if (!confirm) return;
    try {
      if (confirm.type === 'conv') {
        await adminService.eliminarConvocatoria(confirm.id);
        await load();
        setExpanded(null);
      } else {
        await adminService.eliminarPostulacion(confirm.id);
        if (expanded) {
          const r = await adminService.getPostulacionesConvocatoria(expanded);
          setPosts(r.data);
        }
      }
    } catch { /* silent */ }
    setConfirm(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Buscar por título o período..."
            className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
          />
        </div>
        <select value={estado} onChange={e => setEstado(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
          <option value="">Todos los estados</option>
          {['borrador', 'abierta', 'cerrada', 'en_evaluacion', 'finalizada'].map(e => (
            <option key={e} value={e}>{e.replace('_', ' ')}</option>
          ))}
        </select>
        <button onClick={load} className="p-2 text-gray-500 hover:bg-gray-100 rounded-xl">
          <RefreshCw size={15} />
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={28} className="animate-spin text-usco-vinotinto" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-sm text-gray-400">No se encontraron convocatorias.</div>
      ) : (
        <div className="space-y-2">
          {items.map(conv => (
            <div key={conv.id} className="border border-gray-100 rounded-xl overflow-hidden">
              <div className="flex items-center gap-3 px-4 py-3 bg-white hover:bg-gray-50/60 transition-colors">
                <button onClick={() => expandir(conv.id)} className="flex-1 flex items-center gap-3 text-left min-w-0">
                  {expanded === conv.id ? <ChevronUp size={15} className="shrink-0 text-gray-400" /> : <ChevronDown size={15} className="shrink-0 text-gray-400" />}
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{conv.titulo}</p>
                    <p className="text-xs text-gray-400">{conv.asignatura} · {conv.profesor} · {conv.periodo_academico}</p>
                  </div>
                </button>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${ESTADO_MONITORIA[conv.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                  {conv.estado.replace('_', ' ')}
                </span>
                <span className="text-xs text-gray-400 shrink-0">{conv.postulaciones} postulaciones</span>
                <button onClick={() => setConfirm({ type: 'conv', id: conv.id })}
                  className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg shrink-0">
                  <Trash2 size={14} />
                </button>
              </div>

              {expanded === conv.id && (
                <div className="border-t border-gray-100 bg-gray-50/60 px-4 py-3">
                  {loadingPosts ? (
                    <div className="flex justify-center py-4"><Loader2 size={18} className="animate-spin text-usco-vinotinto" /></div>
                  ) : posts.length === 0 ? (
                    <p className="text-xs text-gray-400 text-center py-2">Sin postulaciones.</p>
                  ) : (
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-gray-400 uppercase tracking-wide">
                          <th className="pb-2 text-left font-semibold">Estudiante</th>
                          <th className="pb-2 text-left font-semibold">Código</th>
                          <th className="pb-2 text-center font-semibold">Promedio</th>
                          <th className="pb-2 text-center font-semibold">Estado</th>
                          <th className="pb-2 text-right font-semibold">Acción</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {posts.map(p => (
                          <tr key={p.id}>
                            <td className="py-1.5 text-gray-700">{p.estudiante}</td>
                            <td className="py-1.5 text-gray-500">{p.codigo_estudiante}</td>
                            <td className="py-1.5 text-center text-gray-600">{p.promedio?.toFixed(2) ?? '—'}</td>
                            <td className="py-1.5 text-center">
                              <span className={`px-2 py-0.5 rounded-full font-semibold ${ESTADO_MONITORIA[p.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                                {p.estado}
                              </span>
                            </td>
                            <td className="py-1.5 text-right">
                              <button onClick={() => setConfirm({ type: 'post', id: p.id })}
                                className="p-1 text-red-400 hover:bg-red-50 rounded">
                                <Trash2 size={12} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {confirm && (
        <ConfirmDialog
          message={confirm.type === 'conv'
            ? '¿Eliminar esta convocatoria y todas sus postulaciones? Acción irreversible.'
            : '¿Eliminar esta postulación?'}
          onConfirm={eliminar}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
//  TAB: PRÁCTICAS
// ══════════════════════════════════════════════════════════════════════════

function PracticasTab() {
  const [items, setItems] = useState<PracticaItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [estado, setEstado] = useState('');
  const [programa, setPrograma] = useState('');
  const [confirm, setConfirm] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await adminService.getPracticasAdmin({
        estado: estado || undefined,
        programa: programa || undefined,
        q: q || undefined,
      });
      setItems(r.data);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [q, estado, programa]);

  useEffect(() => { load(); }, [load]);

  const eliminar = async (id: number) => {
    try {
      await adminService.eliminarPractica(id);
      setConfirm(null);
      await load();
    } catch { /* silent */ }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[180px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={q}
            onChange={e => setQ(e.target.value)}
            placeholder="Buscar práctica..."
            className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
          />
        </div>
        <select value={estado} onChange={e => setEstado(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none bg-white">
          <option value="">Todos los estados</option>
          {['borrador', 'solicitada', 'pendiente_quorum', 'rechazada', 'aprobado_transporte', 'en_ejecucion', 'finalizada'].map(e => (
            <option key={e} value={e}>{e.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <select value={programa} onChange={e => setPrograma(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none bg-white">
          <option value="">Todos los programas</option>
          {PROGRAMAS.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <button onClick={load} className="p-2 text-gray-500 hover:bg-gray-100 rounded-xl">
          <RefreshCw size={15} />
        </button>
      </div>

      <p className="text-xs text-gray-400">{items.length} prácticas encontradas</p>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={28} className="animate-spin text-usco-vinotinto" /></div>
      ) : items.length === 0 ? (
        <div className="text-center py-12 text-sm text-gray-400">No se encontraron prácticas.</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-gray-100">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="px-4 py-3 text-left">Práctica</th>
                <th className="px-4 py-3 text-left">Asignatura / Programa</th>
                <th className="px-4 py-3 text-left">Profesor</th>
                <th className="px-4 py-3 text-center">Período</th>
                <th className="px-4 py-3 text-center">Estado</th>
                <th className="px-4 py-3 text-center">Municipio</th>
                <th className="px-4 py-3 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {items.map(p => (
                <tr key={p.id} className="hover:bg-gray-50/60 transition-colors">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-800 max-w-[200px] truncate" title={p.nombre_practica}>
                      {p.nombre_practica}
                    </p>
                    <p className="text-xs text-gray-400">{fmtDate(p.fecha_inicio)} → {fmtDate(p.fecha_fin)}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    <p className="text-xs truncate max-w-[160px]" title={p.asignatura ?? ''}>{p.asignatura}</p>
                    <p className="text-xs text-gray-400 truncate max-w-[160px]">{p.programa}</p>
                  </td>
                  <td className="px-4 py-3 text-gray-600 text-xs">{p.profesor}</td>
                  <td className="px-4 py-3 text-center text-xs text-gray-500">{p.periodo_academico}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${ESTADO_PRACTICA[p.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                      {({'borrador':'Borrador','solicitada':'Solicitada','pendiente_quorum':'Pend. Quórum','aprobada_curriculo':'Aprobada Comité','aprobada_facultad':'Avalada Facultad','aprobado_transporte':'Aprobada Vicerrectoría','en_ejecucion':'En Ejecución','finalizada':'Finalizada','rechazada':'Rechazada'} as Record<string,string>)[p.estado] ?? p.estado.replace(/_/g,' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-gray-500">{p.municipio ?? '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => setConfirm(p.id)}
                      className="p-1.5 text-red-400 hover:bg-red-50 rounded-lg transition-colors">
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {confirm !== null && (
        <ConfirmDialog
          message="¿Eliminar esta práctica y todos sus datos (rutas, viáticos, firmas)? Acción irreversible."
          onConfirm={() => eliminar(confirm)}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
//  PÁGINA PRINCIPAL
// ══════════════════════════════════════════════════════════════════════════

type Tab = 'semestres' | 'monitorias' | 'practicas';

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'semestres',  label: 'Semestres',  icon: <CalendarDays size={16} /> },
  { id: 'monitorias', label: 'Monitorías', icon: <BookOpen size={16} /> },
  { id: 'practicas',  label: 'Prácticas',  icon: <MapPin size={16} /> },
];

export function AdminPanel() {
  const [tab, setTab] = useState<Tab>('semestres');

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-usco-vinotinto flex items-center justify-center">
          <CheckCircle size={20} className="text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Panel de Control</h1>
          <p className="text-sm text-gray-400">Administración global del sistema SIPAM</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
              tab === t.id
                ? 'bg-white text-usco-vinotinto shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        {tab === 'semestres'  && <SemestresTab />}
        {tab === 'monitorias' && <MonitoriasTab />}
        {tab === 'practicas'  && <PracticasTab />}
      </div>

      {/* Warning banner */}
      <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3">
        <AlertTriangle size={16} className="text-amber-600 shrink-0 mt-0.5" />
        <p className="text-xs text-amber-700">
          <span className="font-bold">Zona de administración:</span> las eliminaciones son permanentes e irreversibles.
          Actúa con precaución. Los datos eliminados no se pueden recuperar.
        </p>
      </div>
    </div>
  );
}

export default AdminPanel;
