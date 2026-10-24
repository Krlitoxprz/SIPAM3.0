import { useState, useEffect, useCallback } from 'react';
import {
  Settings, Calendar, DollarSign, BookOpen, Plus, Edit2, CheckCircle,
  AlertCircle, Loader2, X, ToggleLeft, ToggleRight, Send, MessageSquare, Users,
} from 'lucide-react';
import { configuracionService, presupuestoService, asignaturasService, convocatoriasService } from '../services/api';
import { useAuthContext } from '../context/AuthContext';

// ─── tipos locales ──────────────────────────────────────────────────────────
interface CalendarioConfig {
  id: number;
  periodo_academico: string;
  semana_inicio_solicitudes: number;
  semana_fin_solicitudes: number;
  fecha_inicio_semestre: string;
  fecha_fin_semestre: string;
  is_active: boolean;
}

interface TarifaViatico {
  id: number;
  descripcion: string;
  valor_dia: number;
  aplica_desde: string;
  aplica_hasta?: string;
  is_active: boolean;
}

interface PresupuestoItem {
  id: number;
  periodo_academico: string;
  monto_total_asignado: number;
  monto_ejecutado: number;
  monto_comprometido: number;
  monto_disponible: number;
  porcentaje_ejecutado: number;
  estado?: string;
  observaciones_admin?: string | null;
  descripcion?: string | null;
}

interface ProfesorPrograma {
  profesor_id: number; codigo: string; nombre: string; email: string;
  total_materias: number; total_estudiantes: number;
  materias: { id: number; codigo: string; nombre: string; semestre: number; creditos: number; total_estudiantes: number }[];
}


const ESTADO_BADGE_CFG: Record<string, { label: string; color: string }> = {
  borrador:     { label: 'Borrador',            color: 'bg-gray-100 text-gray-600' },
  solicitado:   { label: 'Solicitado a Gastos', color: 'bg-blue-100 text-blue-700' },
  aprobado:     { label: 'Aprobado',             color: 'bg-emerald-100 text-emerald-700' },
  rechazado:    { label: 'Rechazado',            color: 'bg-red-100 text-red-700' },
  modificacion: { label: 'Pend. corrección',    color: 'bg-amber-100 text-amber-700' },
};

const CLP = (v: number) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v);

// ─── Modal Calendario ────────────────────────────────────────────────────────
function ModalCalendario({
  item, onClose, onSuccess,
}: { item: CalendarioConfig | null; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState({
    periodo_academico: item?.periodo_academico ?? '',
    semana_inicio_solicitudes: String(item?.semana_inicio_solicitudes ?? 3),
    semana_fin_solicitudes: String(item?.semana_fin_solicitudes ?? 14),
    fecha_inicio_semestre: item?.fecha_inicio_semestre?.slice(0, 16) ?? '',
    fecha_fin_semestre: item?.fecha_fin_semestre?.slice(0, 16) ?? '',
    is_active: item?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const f = (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm(p => ({ ...p, [k]: e.target.value }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError('');
    const payload = {
      periodo_academico: form.periodo_academico,
      semana_inicio_solicitudes: parseInt(form.semana_inicio_solicitudes),
      semana_fin_solicitudes: parseInt(form.semana_fin_solicitudes),
      fecha_inicio_semestre: new Date(form.fecha_inicio_semestre).toISOString(),
      fecha_fin_semestre: new Date(form.fecha_fin_semestre).toISOString(),
      is_active: form.is_active,
    };
    try {
      if (item) {
        await configuracionService.actualizarCalendario(item.id, payload);
      } else {
        await configuracionService.crearCalendario(payload);
      }
      onSuccess();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Error al guardar');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-800">{item ? 'Editar Calendario' : 'Nuevo Período'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          {error && <div className="bg-red-50 text-red-700 text-xs px-3 py-2 rounded-lg border border-red-200">{error}</div>}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Período académico *</label>
            <input required value={form.periodo_academico} onChange={f('periodo_academico')} placeholder="2025-1"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Semana inicio sol.</label>
              <input required type="number" min="1" max="18" value={form.semana_inicio_solicitudes} onChange={f('semana_inicio_solicitudes')}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Semana fin sol.</label>
              <input required type="number" min="1" max="18" value={form.semana_fin_solicitudes} onChange={f('semana_fin_solicitudes')}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Inicio semestre *</label>
              <input required type="datetime-local" value={form.fecha_inicio_semestre} onChange={f('fecha_inicio_semestre')}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Fin semestre *</label>
              <input required type="datetime-local" value={form.fecha_fin_semestre} onChange={f('fecha_fin_semestre')}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
            <input type="checkbox" checked={form.is_active} onChange={e => setForm(p => ({ ...p, is_active: e.target.checked }))}
              className="rounded accent-usco-vinotinto" />
            <span className="text-gray-600 font-medium">Período activo</span>
          </label>
          <div className="flex gap-3 pt-2 border-t border-gray-100">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 size={14} className="animate-spin" />}
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Modal Tarifa ────────────────────────────────────────────────────────────
function ModalTarifa({
  item, onClose, onSuccess,
}: { item: TarifaViatico | null; onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState({
    descripcion: item?.descripcion ?? '',
    valor_dia: String(item?.valor_dia ?? ''),
    aplica_desde: item?.aplica_desde ?? '',
    is_active: item?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError('');
    const payload = {
      descripcion: form.descripcion,
      valor_dia: parseFloat(form.valor_dia),
      aplica_desde: form.aplica_desde,
      is_active: form.is_active,
    };
    try {
      if (item) {
        await configuracionService.actualizarTarifa(item.id, payload);
      } else {
        await configuracionService.crearTarifa(payload);
      }
      onSuccess();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Error al guardar');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-800">{item ? 'Editar Tarifa' : 'Nueva Tarifa'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          {error && <div className="bg-red-50 text-red-700 text-xs px-3 py-2 rounded-lg border border-red-200">{error}</div>}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Descripción *</label>
            <input required value={form.descripcion} onChange={e => setForm(p => ({ ...p, descripcion: e.target.value }))}
              placeholder="Ej: Alimentación diaria"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Valor por día (COP) *</label>
            <input required type="number" min="0" step="100" value={form.valor_dia}
              onChange={e => setForm(p => ({ ...p, valor_dia: e.target.value }))}
              placeholder="50000"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Aplica desde *</label>
            <input required type="date" value={form.aplica_desde}
              onChange={e => setForm(p => ({ ...p, aplica_desde: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
            <input type="checkbox" checked={form.is_active} onChange={e => setForm(p => ({ ...p, is_active: e.target.checked }))}
              className="rounded accent-usco-vinotinto" />
            <span className="text-gray-600 font-medium">Tarifa activa</span>
          </label>
          <div className="flex gap-3 pt-2 border-t border-gray-100">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 size={14} className="animate-spin" />}
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Modal Presupuesto (crear) ────────────────────────────────────────────────
function ModalPresupuesto({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [form, setForm] = useState({ periodo_academico: '', monto_total_asignado: '', descripcion: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError('');
    try {
      await presupuestoService.crear({
        periodo_academico: form.periodo_academico,
        monto_total_asignado: parseFloat(form.monto_total_asignado),
        descripcion: form.descripcion || null,
      });
      onSuccess();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Error al crear');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-800">Establecer Presupuesto</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          {error && <div className="bg-red-50 text-red-700 text-xs px-3 py-2 rounded-lg border border-red-200">{error}</div>}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Período académico *</label>
            <input required value={form.periodo_academico}
              onChange={e => setForm(p => ({ ...p, periodo_academico: e.target.value }))}
              placeholder="2026-1"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Monto a solicitar (COP) *</label>
            <input required type="number" min="0" step="1000" value={form.monto_total_asignado}
              onChange={e => setForm(p => ({ ...p, monto_total_asignado: e.target.value }))}
              placeholder="5000000"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Descripción / justificación</label>
            <input value={form.descripcion} onChange={e => setForm(p => ({ ...p, descripcion: e.target.value }))}
              placeholder="Ej: Presupuesto para prácticas extramurales 2026-1"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <p className="text-xs text-gray-400">El presupuesto quedará en <strong>Borrador</strong> hasta que lo envíes al Administrador desde esta misma vista.</p>
          <div className="flex gap-3 pt-2 border-t border-gray-100">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 size={14} className="animate-spin" />}
              {saving ? 'Guardando...' : 'Establecer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Modal Editar Presupuesto (jefe corrige monto) ────────────────────────────
function ModalEditarPresupuesto({
  item, onClose, onSuccess,
}: { item: PresupuestoItem; onClose: () => void; onSuccess: () => void }) {
  const [monto, setMonto] = useState(String(item.monto_total_asignado));
  const [descripcion, setDescripcion] = useState(item.descripcion ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError('');
    try {
      await presupuestoService.editar(item.periodo_academico, {
        monto_total_asignado: parseFloat(monto),
        descripcion: descripcion || undefined,
      });
      onSuccess();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Error al guardar');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-800">Corregir Presupuesto — {item.periodo_academico}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          {item.observaciones_admin && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              <p className="text-xs font-semibold text-amber-700 mb-0.5">Observaciones del Administrador:</p>
              <p className="text-xs text-amber-800">{item.observaciones_admin}</p>
            </div>
          )}
          {error && <div className="bg-red-50 text-red-700 text-xs px-3 py-2 rounded-lg border border-red-200">{error}</div>}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Monto a solicitar (COP) *</label>
            <input required type="number" min="0" step="1000" value={monto}
              onChange={e => setMonto(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Descripción / justificación</label>
            <input value={descripcion} onChange={e => setDescripcion(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div className="flex gap-3 pt-2 border-t border-gray-100">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 size={14} className="animate-spin" />}
              {saving ? 'Guardando...' : 'Guardar correción'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Componente principal ────────────────────────────────────────────────────
export function Configuracion() {
  const { user } = useAuthContext();
  const [tab, setTab] = useState<'calendario' | 'tarifas' | 'presupuesto' | 'asignaturas' | 'programa'>('calendario');

  const [calendarios, setCalendarios] = useState<CalendarioConfig[]>([]);
  const [tarifas, setTarifas] = useState<TarifaViatico[]>([]);
  const [presupuestos, setPresupuestos] = useState<PresupuestoItem[]>([]);
  interface AsigItem { id: number; codigo: string; nombre: string; creditos: number; semestre: number; programa: string; facultad?: string | null; profesor_id?: number | null; is_active: boolean; }
  interface ProfeItem { id: number; codigo: string; nombre: string; }
  const [asignaturas, setAsignaturas] = useState<AsigItem[]>([]);
  const [profesores, setProfesores] = useState<ProfeItem[]>([]);
  const [modalAsig, setModalAsig] = useState<AsigItem | null | true>(null);
  const [loadingAsig, setLoadingAsig] = useState(false);

  const [programaAcademico, setProgramaAcademico] = useState<ProfesorPrograma[]>([]);
  const [expandedProf, setExpandedProf] = useState<number | null>(null);
  const [loadingPA, setLoadingPA] = useState(false);

  const [loadingCal, setLoadingCal] = useState(false);
  const [loadingTar, setLoadingTar] = useState(false);
  const [loadingPre, setLoadingPre] = useState(false);

  const [flash, setFlash] = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);

  const [modalCal, setModalCal] = useState<CalendarioConfig | null | true>(null);
  const [modalTar, setModalTar] = useState<TarifaViatico | null | true>(null);
  const [modalPre, setModalPre] = useState(false);
  const [modalEditar, setModalEditar] = useState<PresupuestoItem | null>(null);
  const [solicitando, setSolicitando] = useState<string | null>(null);

  async function ejecutarSolicitar(periodo: string) {
    setSolicitando(periodo);
    try {
      await presupuestoService.solicitar(periodo);
      cargarPresupuestos();
      showFlash('ok', `Solicitud de presupuesto ${periodo} enviada al Administrador.`);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al enviar la solicitud.');
    } finally { setSolicitando(null); }
  }

  const showFlash = (tipo: 'ok' | 'err', texto: string) => {
    setFlash({ tipo, texto });
    setTimeout(() => setFlash(null), 4000);
  };

  const cargarCalendarios = useCallback(async () => {
    setLoadingCal(true);
    try { const r = await configuracionService.getCalendarios(); setCalendarios(r.data); }
    catch { setCalendarios([]); } finally { setLoadingCal(false); }
  }, []);

  const cargarTarifas = useCallback(async () => {
    setLoadingTar(true);
    try { const r = await configuracionService.getTarifasTodas(); setTarifas(r.data); }
    catch { setTarifas([]); } finally { setLoadingTar(false); }
  }, []);

  const cargarPresupuestos = useCallback(async () => {
    setLoadingPre(true);
    try { const r = await presupuestoService.getAll(); setPresupuestos(r.data); }
    catch { setPresupuestos([]); } finally { setLoadingPre(false); }
  }, []);

  const cargarProgramaAcademico = useCallback(async () => {
    setLoadingPA(true);
    try { const r = await convocatoriasService.getProgramaAcademico(); setProgramaAcademico(r.data); }
    catch { setProgramaAcademico([]); } finally { setLoadingPA(false); }
  }, []);

  const cargarAsignaturas = useCallback(async () => {
    setLoadingAsig(true);
    try {
      const [ar, pr] = await Promise.all([
        convocatoriasService.getAsignaturas(true),
        convocatoriasService.getProfesores(),
      ]);
      setAsignaturas(ar.data);
      setProfesores(pr.data);
    } catch { setAsignaturas([]); }
    finally { setLoadingAsig(false); }
  }, []);

  useEffect(() => { cargarCalendarios(); cargarTarifas(); cargarPresupuestos(); cargarAsignaturas(); cargarProgramaAcademico(); }, [cargarCalendarios, cargarTarifas, cargarPresupuestos, cargarAsignaturas, cargarProgramaAcademico]);

  if (user?.rol !== 'admin') {
    return (
      <div className="text-center py-24 text-gray-400">
        <Settings size={48} className="mx-auto mb-3 opacity-40" />
        <p className="font-medium text-lg">Acceso restringido</p>
        <p className="text-sm">Solo el Administrador puede acceder a esta sección.</p>
      </div>
    );
  }

  const tabs = [
    { id: 'calendario' as const, label: 'Calendario Académico', icon: Calendar },
    { id: 'tarifas' as const, label: 'Tarifas de Viáticos', icon: DollarSign },
    { id: 'presupuesto' as const, label: 'Presupuestos', icon: BookOpen },
    { id: 'asignaturas' as const, label: 'Asignaturas', icon: BookOpen },
    { id: 'programa' as const, label: 'Programa Académico', icon: Users },
  ];

  return (
    <div className="space-y-5">
      {/* Modales */}
      {modalCal !== null && (
        <ModalCalendario
          item={modalCal === true ? null : modalCal}
          onClose={() => setModalCal(null)}
          onSuccess={() => { setModalCal(null); cargarCalendarios(); showFlash('ok', 'Calendario guardado.'); }}
        />
      )}
      {modalTar !== null && (
        <ModalTarifa
          item={modalTar === true ? null : modalTar}
          onClose={() => setModalTar(null)}
          onSuccess={() => { setModalTar(null); cargarTarifas(); showFlash('ok', 'Tarifa guardada.'); }}
        />
      )}
      {modalPre && (
        <ModalPresupuesto
          onClose={() => setModalPre(false)}
          onSuccess={() => { setModalPre(false); cargarPresupuestos(); showFlash('ok', 'Presupuesto establecido. Ahora envíalo al Administrador.'); }}
        />
      )}
      {modalEditar && (
        <ModalEditarPresupuesto
          item={modalEditar}
          onClose={() => setModalEditar(null)}
          onSuccess={() => { setModalEditar(null); cargarPresupuestos(); showFlash('ok', 'Presupuesto corregido. Puedes reenviarlo al Administrador.'); }}
        />
      )}

      {/* Flash */}
      {flash && (
        <div className={`flex items-center gap-3 rounded-xl px-5 py-3 text-sm font-medium ${
          flash.tipo === 'ok' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-red-50 border border-red-200 text-red-700'}`}>
          {flash.tipo === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {flash.texto}
        </div>
      )}

      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Settings size={20} className="text-usco-vinotinto" /> Configuración del Sistema
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">Parámetros académicos, tarifas de viáticos y presupuestos por período.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
        {tabs.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                tab === t.id ? 'bg-white shadow-sm text-usco-vinotinto' : 'text-gray-500 hover:text-gray-700'
              }`}>
              <Icon size={15} /> {t.label}
            </button>
          );
        })}
      </div>

      {/* ─── TAB: Calendario ─────────────────────────────────────────────── */}
      {tab === 'calendario' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="font-bold text-gray-700 text-sm">Períodos académicos</h2>
            <button onClick={() => setModalCal(true)}
              className="flex items-center gap-1.5 text-xs font-semibold bg-usco-vinotinto text-white px-3 py-2 rounded-lg hover:bg-usco-vinotinto/90">
              <Plus size={13} /> Nuevo período
            </button>
          </div>
          {loadingCal ? (
            <div className="flex justify-center items-center py-10"><Loader2 size={22} className="animate-spin text-usco-vinotinto" /></div>
          ) : calendarios.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">Sin períodos configurados</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {calendarios.map(c => (
                <div key={c.id} className="flex items-center justify-between px-5 py-4 hover:bg-gray-50/50">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-gray-800 text-sm">{c.periodo_academico}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${c.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                        {c.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">
                      Solicitudes: semanas {c.semana_inicio_solicitudes}–{c.semana_fin_solicitudes} ·{' '}
                      {new Date(c.fecha_inicio_semestre).toLocaleDateString('es-CO')} →{' '}
                      {new Date(c.fecha_fin_semestre).toLocaleDateString('es-CO')}
                    </p>
                  </div>
                  <button onClick={() => setModalCal(c)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-usco-vinotinto border border-gray-200 px-3 py-1.5 rounded-lg">
                    <Edit2 size={12} /> Editar
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─── TAB: Tarifas ────────────────────────────────────────────────── */}
      {tab === 'tarifas' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <div>
              <h2 className="font-bold text-gray-700 text-sm">Tarifas de viáticos</h2>
              <p className="text-xs text-gray-400 mt-0.5">Valores por persona/día para cálculo de viáticos en prácticas.</p>
            </div>
            <button onClick={() => setModalTar(true)}
              className="flex items-center gap-1.5 text-xs font-semibold bg-usco-vinotinto text-white px-3 py-2 rounded-lg hover:bg-usco-vinotinto/90">
              <Plus size={13} /> Nueva tarifa
            </button>
          </div>
          {loadingTar ? (
            <div className="flex justify-center items-center py-10"><Loader2 size={22} className="animate-spin text-usco-vinotinto" /></div>
          ) : tarifas.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">Sin tarifas configuradas</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {tarifas.map(t => (
                <div key={t.id} className="flex items-center justify-between px-5 py-4 hover:bg-gray-50/50">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-gray-800 text-sm">{t.descripcion}</span>
                      {t.is_active
                        ? <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-semibold flex items-center gap-1"><ToggleRight size={11} /> Activa</span>
                        : <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500 font-semibold flex items-center gap-1"><ToggleLeft size={11} /> Inactiva</span>
                      }
                    </div>
                    <p className="text-xs text-gray-500">
                      {CLP(t.valor_dia)}/día · vigente desde {new Date(t.aplica_desde).toLocaleDateString('es-CO')}
                    </p>
                  </div>
                  <button onClick={() => setModalTar(t)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-usco-vinotinto border border-gray-200 px-3 py-1.5 rounded-lg">
                    <Edit2 size={12} /> Editar
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─── TAB: Presupuesto ────────────────────────────────────────────── */}
      {tab === 'presupuesto' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <h2 className="font-bold text-gray-700 text-sm">Presupuestos por período</h2>
            <button onClick={() => setModalPre(true)}
              className="flex items-center gap-1.5 text-xs font-semibold bg-usco-vinotinto text-white px-3 py-2 rounded-lg hover:bg-usco-vinotinto/90">
              <Plus size={13} /> Nuevo presupuesto
            </button>
          </div>
          {loadingPre ? (
            <div className="flex justify-center items-center py-10"><Loader2 size={22} className="animate-spin text-usco-vinotinto" /></div>
          ) : presupuestos.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">Sin presupuestos registrados</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {presupuestos.map(p => {
                const pctEje = p.monto_total_asignado > 0
                  ? Math.round((p.monto_ejecutado / p.monto_total_asignado) * 100) : 0;
                const pctCom = p.monto_total_asignado > 0
                  ? Math.round((p.monto_comprometido / p.monto_total_asignado) * 100) : 0;
                const badge = ESTADO_BADGE_CFG[p.estado ?? 'aprobado'] ?? ESTADO_BADGE_CFG.aprobado;
                const puedeEditar = ['borrador', 'modificacion', 'rechazado'].includes(p.estado ?? '');
                const puedeSolicitar = ['borrador', 'modificacion', 'rechazado'].includes(p.estado ?? '');
                return (
                  <div key={p.id} className="px-5 py-4 hover:bg-gray-50/50">
                    {/* Cabecera: período, monto, estado */}
                    <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-gray-800">{p.periodo_academico}</span>
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badge.color}`}>
                          {badge.label}
                        </span>
                      </div>
                      <span className="text-sm font-bold text-usco-vinotinto">{CLP(p.monto_total_asignado)}</span>
                    </div>

                    {/* Obs. del admin cuando hay corrección pendiente */}
                    {p.observaciones_admin && puedeEditar && (
                      <div className="flex items-start gap-1.5 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-2">
                        <MessageSquare size={12} className="shrink-0 text-amber-600 mt-0.5" />
                        <p className="text-xs text-amber-700">
                          <strong>Administrador indica:</strong> {p.observaciones_admin}
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-3 gap-3 mb-3 text-center">
                      <div className="bg-gray-50 rounded-lg p-2">
                        <p className="text-xs text-gray-400">Disponible</p>
                        <p className="text-sm font-bold text-emerald-600">{CLP(p.monto_disponible)}</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-2">
                        <p className="text-xs text-gray-400">Comprometido</p>
                        <p className="text-sm font-bold text-orange-500">{CLP(p.monto_comprometido)}</p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-2">
                        <p className="text-xs text-gray-400">Ejecutado</p>
                        <p className="text-sm font-bold text-red-500">{CLP(p.monto_ejecutado)}</p>
                      </div>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden mb-1">
                      <div className="h-2 flex">
                        <div className="bg-red-400 h-full" style={{ width: `${pctEje}%` }} />
                        <div className="bg-orange-300 h-full" style={{ width: `${pctCom}%` }} />
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-gray-400">
                        Ejecutado: {pctEje}% · Comprometido: {pctCom}%
                      </p>
                      {/* Acciones del Jefe */}
                      <div className="flex gap-2">
                        {puedeEditar && (
                          <button onClick={() => setModalEditar(p)}
                            className="flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-usco-vinotinto border border-gray-200 px-2.5 py-1.5 rounded-lg">
                            <Edit2 size={11} /> Corregir
                          </button>
                        )}
                        {puedeSolicitar && (
                          <button
                            onClick={() => ejecutarSolicitar(p.periodo_academico)}
                            disabled={solicitando === p.periodo_academico}
                            className="flex items-center gap-1 text-xs font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 px-2.5 py-1.5 rounded-lg disabled:opacity-60">
                            {solicitando === p.periodo_academico
                              ? <Loader2 size={11} className="animate-spin" />
                              : <Send size={11} />}
                            Enviar a Gastos
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ─── TAB: Programa Académico ─────────────────────────────────────────── */}
      {tab === 'programa' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users size={16} className="text-usco-vinotinto" />
              <h2 className="font-bold text-gray-700 text-sm">Programa académico — profesores y matrículas</h2>
            </div>
            <span className="text-xs text-gray-400">
              {programaAcademico.length} profesores · {programaAcademico.reduce((s, p) => s + p.total_estudiantes, 0)} matrículas
            </span>
          </div>
          {loadingPA ? (
            <div className="flex justify-center items-center py-10"><Loader2 size={22} className="animate-spin text-usco-vinotinto" /></div>
          ) : programaAcademico.length === 0 ? (
            <div className="text-center py-10 text-gray-400 text-sm">Sin datos del programa académico</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {programaAcademico.map(prof => (
                <div key={prof.profesor_id}>
                  <button
                    onClick={() => setExpandedProf(expandedProf === prof.profesor_id ? null : prof.profesor_id)}
                    className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50 transition-colors text-left">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-usco-vinotinto/10 flex items-center justify-center shrink-0">
                        <span className="text-xs font-bold text-usco-vinotinto">{prof.nombre.charAt(0)}</span>
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-800">{prof.nombre}</p>
                        <p className="text-xs text-gray-400 font-mono">{prof.codigo}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 shrink-0">
                      <div className="text-right">
                        <p className="text-xs text-gray-400">{prof.total_materias} materias</p>
                        <p className="text-sm font-bold text-usco-vinotinto">{prof.total_estudiantes} est.</p>
                      </div>
                      <span className="text-xs text-gray-300">{expandedProf === prof.profesor_id ? '▲' : '▼'}</span>
                    </div>
                  </button>
                  {expandedProf === prof.profesor_id && (
                    <div className="bg-gray-50 px-5 pb-3">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="text-gray-400 uppercase tracking-wide">
                            <th className="text-left py-2 pr-3">Código</th>
                            <th className="text-left py-2 pr-3">Asignatura</th>
                            <th className="text-center py-2 pr-3">Sem.</th>
                            <th className="text-center py-2 pr-3">Créditos</th>
                            <th className="text-right py-2">Estudiantes</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {prof.materias.map(m => (
                            <tr key={m.id} className="hover:bg-white">
                              <td className="py-1.5 pr-3 font-mono text-usco-vinotinto font-semibold">{m.codigo}</td>
                              <td className="py-1.5 pr-3 text-gray-700">{m.nombre}</td>
                              <td className="py-1.5 pr-3 text-center text-gray-500">{m.semestre}°</td>
                              <td className="py-1.5 pr-3 text-center text-gray-500">{m.creditos}</td>
                              <td className="py-1.5 text-right font-bold text-gray-800">{m.total_estudiantes}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ─── TAB: Asignaturas ───────────────────────────────────────────────────── */}
      {tab === 'asignaturas' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
            <div>
              <h2 className="font-bold text-gray-700 text-sm">Asignaturas del programa</h2>
              <p className="text-xs text-gray-400 mt-0.5">Gestión de materias y asignación de profesores.</p>
            </div>
            <button onClick={() => setModalAsig(true)}
              className="flex items-center gap-1.5 text-xs font-semibold bg-usco-vinotinto text-white px-3 py-2 rounded-lg hover:bg-usco-vinotinto/90">
              <Plus size={13} /> Nueva asignatura
            </button>
          </div>

          {/* Modal crear / editar asignatura */}
          {modalAsig !== null && (
            <ModalAsignatura
              item={modalAsig === true ? null : modalAsig}
              profesores={profesores}
              onClose={() => setModalAsig(null)}
              onSuccess={() => {
                const editing = modalAsig !== true;
                setModalAsig(null);
                cargarAsignaturas();
                showFlash('ok', editing ? 'Asignatura actualizada.' : 'Asignatura creada.');
              }}
            />
          )}

          {loadingAsig ? (
            <div className="flex justify-center py-10"><Loader2 size={22} className="animate-spin text-usco-vinotinto" /></div>
          ) : asignaturas.length === 0 ? (
            <div className="text-center py-10 text-sm text-gray-400">Sin asignaturas registradas</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    <th className="px-5 py-3 text-left">Código</th>
                    <th className="px-5 py-3 text-left">Asignatura</th>
                    <th className="px-5 py-3 text-center">Sem.</th>
                    <th className="px-5 py-3 text-center">Créditos</th>
                    <th className="px-5 py-3 text-left">Profesor</th>
                    <th className="px-5 py-3 text-center">Estado</th>
                    <th className="px-5 py-3 text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {asignaturas.map(a => {
                    const prof = profesores.find(p => p.id === a.profesor_id);
                    return (
                      <tr key={a.id} className="hover:bg-gray-50/50">
                        <td className="px-5 py-3 font-mono text-xs text-gray-600">{a.codigo}</td>
                        <td className="px-5 py-3 font-semibold text-gray-800">{a.nombre}</td>
                        <td className="px-5 py-3 text-center text-gray-500">{a.semestre}°</td>
                        <td className="px-5 py-3 text-center text-gray-500">{a.creditos}</td>
                        <td className="px-5 py-3 text-gray-500 text-xs">{prof ? prof.nombre : <span className="text-gray-300">Sin asignar</span>}</td>
                        <td className="px-5 py-3 text-center">
                          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${a.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                            {a.is_active ? 'Activa' : 'Inactiva'}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-center">
                          <button onClick={() => setModalAsig(a)}
                            className="flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-usco-vinotinto border border-gray-200 px-2.5 py-1.5 rounded-lg mx-auto">
                            <Edit2 size={11} /> Editar
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Modal Asignatura (crear / editar) ───────────────────────────────────────
function ModalAsignatura({
  item, profesores, onClose, onSuccess,
}: {
  item: { id: number; codigo: string; nombre: string; creditos: number; semestre: number; programa: string; facultad?: string | null; profesor_id?: number | null; is_active: boolean } | null;
  profesores: { id: number; codigo: string; nombre: string }[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [form, setForm] = useState({
    codigo: item?.codigo ?? '',
    nombre: item?.nombre ?? '',
    creditos: String(item?.creditos ?? 3),
    semestre: String(item?.semestre ?? 1),
    programa: item?.programa ?? 'Ingeniería de Software',
    facultad: item?.facultad ?? '',
    profesor_id: String(item?.profesor_id ?? ''),
    is_active: item?.is_active ?? true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError('');
    const payload = {
      codigo: form.codigo,
      nombre: form.nombre,
      creditos: parseInt(form.creditos),
      semestre: parseInt(form.semestre),
      programa: form.programa,
      facultad: form.facultad || null,
      profesor_id: form.profesor_id ? parseInt(form.profesor_id) : null,
      is_active: form.is_active,
    };
    try {
      if (item) {
        await asignaturasService.actualizar(item.id, payload);
      } else {
        await asignaturasService.crear(payload);
      }
      onSuccess();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Error al guardar');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <h2 className="text-base font-bold text-gray-800">{item ? 'Editar Asignatura' : 'Nueva Asignatura'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          {error && <div className="bg-red-50 text-red-700 text-xs px-3 py-2 rounded-lg border border-red-200">{error}</div>}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Código *</label>
              <input required value={form.codigo} onChange={e => setForm(p => ({ ...p, codigo: e.target.value }))}
                placeholder="ISW-101"
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Semestre *</label>
              <input required type="number" min="1" max="10" value={form.semestre}
                onChange={e => setForm(p => ({ ...p, semestre: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Nombre *</label>
            <input required value={form.nombre} onChange={e => setForm(p => ({ ...p, nombre: e.target.value }))}
              placeholder="Fundamentos de Programación"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Facultad</label>
            <input value={form.facultad} onChange={e => setForm(p => ({ ...p, facultad: e.target.value }))}
              placeholder="Facultad de Ingeniería"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Créditos *</label>
              <input required type="number" min="1" max="10" value={form.creditos}
                onChange={e => setForm(p => ({ ...p, creditos: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Profesor</label>
              <select value={form.profesor_id} onChange={e => setForm(p => ({ ...p, profesor_id: e.target.value }))}
                className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                <option value="">Sin asignar</option>
                {profesores.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
              </select>
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
            <input type="checkbox" checked={form.is_active} onChange={e => setForm(p => ({ ...p, is_active: e.target.checked }))}
              className="rounded accent-usco-vinotinto" />
            <span className="text-gray-600 font-medium">Asignatura activa</span>
          </label>
          <div className="flex gap-3 pt-2 border-t border-gray-100">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving}
              className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 size={14} className="animate-spin" />}
              {saving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
