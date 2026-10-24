import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Search, Filter, BookOpen, Calendar, Users, Loader2,
  CheckCircle, AlertCircle, X, Eye, Edit2, FileText, ArrowRight,
  ChevronRight, ChevronDown, Star, ListChecks, Sparkles, TrendingUp, Clock,
} from 'lucide-react';
import type { Convocatoria, EstadoConvocatoria, Postulacion, Asignatura } from '../types';
import { convocatoriasService, postulacionesService, seleccionService, reportesService, iaService, pdfService, downloadBlob } from '../services/api';
import { generarFO46 } from '../utils/pdfForms';
import { useAuthContext } from '../context/AuthContext';
import { useSystemContext } from '../context/SystemContext';

interface RecomendacionIA {
  convocatoria_id: number;
  titulo: string;
  asignatura: string;
  programa: string;
  tipo_monitoria: string;
  sede: string;
  dias_restantes: number;
  horas_semana: number;
  promedio_minimo: number;
  docente: string;
  num_postulantes: number;
  num_requeridos: number;
  probabilidad_pct: number;
  programa_match: boolean;
}

// ─── constantes de UI ───────────────────────────────────────────────────────
const estadoBadge: Record<EstadoConvocatoria, string> = {
  borrador: 'bg-gray-100 text-gray-600',
  abierta: 'bg-emerald-100 text-emerald-700',
  cerrada: 'bg-red-100 text-red-700',
  en_evaluacion: 'bg-amber-100 text-amber-700',
  finalizada: 'bg-amber-50 text-amber-800',
};

const estadoLabel: Record<EstadoConvocatoria, string> = {
  borrador: 'Borrador',
  abierta: 'Abierta',
  cerrada: 'Cerrada',
  en_evaluacion: 'En Evaluación',
  finalizada: 'Finalizada',
};

const TRANSICION: Record<EstadoConvocatoria, EstadoConvocatoria | null> = {
  borrador: 'abierta',
  abierta: 'cerrada',
  cerrada: 'en_evaluacion',
  en_evaluacion: 'finalizada',
  finalizada: null,
};

const TRANSICION_LABEL: Record<EstadoConvocatoria, string> = {
  borrador: 'Publicar',
  abierta: 'Cerrar postulaciones',
  cerrada: 'Iniciar evaluación',
  en_evaluacion: 'Finalizar',
  finalizada: '',
};

// ─── tipos locales ──────────────────────────────────────────────────────────
interface ProfesorOption { id: number; codigo: string; nombre: string; }

interface ConvForm {
  titulo: string; descripcion: string; descripcion_actividades: string; asignatura_id: string;
  profesor_id: string; tipo_monitoria: string; periodo_academico: string;
  fecha_inicio_postulacion: string; fecha_fin_postulacion: string;
  fecha_publicacion_resultados: string;
  num_monitores_requeridos: string; horas_semana: string; horas_semestre: string;
  promedio_minimo: string; creditos_minimo_pct: string;
  sede: string;
}

const TIPO_MONITORIA_LABELS: Record<string, string> = {
  nee: 'a) Acompañamiento NEE (Bienestar)',
  regimenes_especiales: 'b) Regímenes Especiales',
  academica_cursos: 'c) Académica — Cursos / Asignaturas',
  laboratorios: 'd) Laboratorios',
  tic: 'e) TIC / Salas Informática',
  permanencia_graduacion: 'f) Permanencia y Graduación Estudiantil',
  deportiva: 'g) Deportiva (Bienestar)',
  cultural: 'h) Cultural y Artística (Bienestar)',
  biblioteca: 'i) Biblioteca',
  acreditacion: 'j) Acreditación y Registro Calificado',
  investigacion: 'k) Investigación / Proyección Social',
};

const SEDES_USCO = ['Neiva', 'Pitalito', 'La Plata', 'Garzón'];

const CONV_FORM_INIT: ConvForm = {
  titulo: '', descripcion: '', descripcion_actividades: '', asignatura_id: '', profesor_id: '',
  tipo_monitoria: 'academica_cursos', periodo_academico: '2026-1',
  fecha_inicio_postulacion: '', fecha_fin_postulacion: '',
  fecha_publicacion_resultados: '',
  num_monitores_requeridos: '1', horas_semana: '8', horas_semestre: '128',
  promedio_minimo: '3.5', creditos_minimo_pct: '30',
  sede: 'Neiva',
};

// ─── Modal: Nueva / Editar Convocatoria ─────────────────────────────────────
function ModalConvocatoria({
  convocatoria, onClose, onSuccess,
}: {
  convocatoria: Convocatoria | null;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const { user } = useAuthContext();
  const ext = convocatoria as (typeof convocatoria & { descripcion_actividades?: string; sede?: string; fecha_publicacion_resultados?: string }) | null;
  const [form, setForm] = useState<ConvForm>(
    convocatoria ? {
      titulo: convocatoria.titulo,
      descripcion: convocatoria.descripcion ?? '',
      descripcion_actividades: ext?.descripcion_actividades ?? '',
      asignatura_id: String(convocatoria.asignatura_id),
      profesor_id: String(convocatoria.profesor_id),
      tipo_monitoria: convocatoria.tipo_monitoria,
      periodo_academico: convocatoria.periodo_academico,
      fecha_inicio_postulacion: convocatoria.fecha_inicio_postulacion.slice(0, 16),
      fecha_fin_postulacion: convocatoria.fecha_fin_postulacion.slice(0, 16),
      fecha_publicacion_resultados: ext?.fecha_publicacion_resultados?.slice(0, 16) ?? '',
      num_monitores_requeridos: String(convocatoria.num_monitores_requeridos),
      horas_semana: String(convocatoria.horas_semana),
      horas_semestre: String(convocatoria.horas_semestre),
      promedio_minimo: String(convocatoria.promedio_minimo),
      creditos_minimo_pct: String(convocatoria.creditos_minimo_pct),
      sede: ext?.sede ?? 'Neiva',
    } : CONV_FORM_INIT
  );
  const [asignaturas, setAsignaturas] = useState<Asignatura[]>([]);
  const [profesores, setProfesores] = useState<ProfesorOption[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const esJefe = user?.rol === 'jefe_programa' || user?.rol === 'decano';

  type Plantilla = {
    id: number; nombre_sugerido: string; programa: string;
    asignatura_id: number; asignatura_nombre: string;
    tipo_monitoria: string; descripcion_actividades: string;
    horas_semana: number; horas_semestre: number;
    promedio_minimo: number; creditos_minimo_pct: number;
    num_monitores_sugerido: number; semestre_asignatura: number;
    creditos_asignatura: number; caracter_curso: string;
  };
  const [plantillas, setPlantillas] = useState<Plantilla[]>([]);
  const [showPlantillaPanel, setShowPlantillaPanel] = useState(false);
  const [filterProg, setFilterProg] = useState('');
  const [filterAsig, setFilterAsig] = useState('');

  useEffect(() => {
    convocatoriasService.getAsignaturas().then(r => setAsignaturas(r.data));
    if (esJefe) convocatoriasService.getProfesores().then(r => setProfesores(r.data));
    if (!convocatoria) {
      convocatoriasService.getPlantillas().then(r => setPlantillas(r.data as Plantilla[])).catch(() => {});
    }
  }, [esJefe, convocatoria]);

  function applyPlantilla(pl: Plantilla) {
    setForm(prev => ({
      ...prev,
      titulo: pl.nombre_sugerido,
      tipo_monitoria: pl.tipo_monitoria,
      asignatura_id: pl.asignatura_id ? String(pl.asignatura_id) : prev.asignatura_id,
      descripcion_actividades: pl.descripcion_actividades ?? '',
      horas_semana: String(pl.horas_semana),
      horas_semestre: String(pl.horas_semestre),
      promedio_minimo: pl.promedio_minimo != null ? String(pl.promedio_minimo) : prev.promedio_minimo,
      creditos_minimo_pct: pl.creditos_minimo_pct != null ? String(pl.creditos_minimo_pct) : prev.creditos_minimo_pct,
      num_monitores_requeridos: pl.num_monitores_sugerido ? String(pl.num_monitores_sugerido) : prev.num_monitores_requeridos,
    }));
    setShowPlantillaPanel(false);
  }

  // Auto-populate profesor_id when asignatura changes
  useEffect(() => {
    if (!form.asignatura_id || asignaturas.length === 0) return;
    const asig = asignaturas.find(a => String(a.id) === form.asignatura_id);
    if (asig?.profesor_id) {
      setForm(p => ({ ...p, profesor_id: String(asig.profesor_id) }));
    } else {
      setForm(p => ({ ...p, profesor_id: '' }));
    }
  }, [form.asignatura_id, asignaturas]);

  const asigSeleccionada = asignaturas.find(a => String(a.id) === form.asignatura_id);
  const profesoresFiltrados = asigSeleccionada?.profesor_id
    ? profesores.filter(p => p.id === asigSeleccionada.profesor_id)
    : profesores;

  const f = (k: keyof ConvForm) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setForm(p => ({ ...p, [k]: e.target.value }));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true); setError('');
    try {
      const payload = {
        titulo: form.titulo,
        descripcion: form.descripcion || null,
        descripcion_actividades: form.descripcion_actividades || null,
        asignatura_id: parseInt(form.asignatura_id),
        ...(esJefe && { profesor_id: parseInt(form.profesor_id) }),
        tipo_monitoria: form.tipo_monitoria,
        periodo_academico: form.periodo_academico,
        fecha_inicio_postulacion: new Date(form.fecha_inicio_postulacion).toISOString(),
        fecha_fin_postulacion: new Date(form.fecha_fin_postulacion).toISOString(),
        fecha_publicacion_resultados: form.fecha_publicacion_resultados ? new Date(form.fecha_publicacion_resultados).toISOString() : null,
        num_monitores_requeridos: parseInt(form.num_monitores_requeridos),
        horas_semana: parseInt(form.horas_semana),
        horas_semestre: parseInt(form.horas_semestre),
        promedio_minimo: parseFloat(form.promedio_minimo),
        creditos_minimo_pct: parseFloat(form.creditos_minimo_pct),
        sede: form.sede || null,
      };
      if (convocatoria) {
        await convocatoriasService.update(convocatoria.id, payload);
      } else {
        await convocatoriasService.create(payload);
      }
      onSuccess();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Error al guardar');
    } finally { setSaving(false); }
  }

  const [sec1Open, setSec1Open] = useState(true);
  const [sec2Open, setSec2Open] = useState(true);
  const [sec3Open, setSec3Open] = useState(true);

  const inputCls = "w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto bg-white";

  function SectionHeader({ n, label, sub, color, open, onToggle }: {
    n: number; label: string; sub: string; color: string; open: boolean; onToggle: () => void;
  }) {
    return (
      <button type="button" onClick={onToggle}
        className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border transition-colors ${open ? color : 'bg-gray-50 border-gray-200'}`}>
        <div className="flex items-center gap-2.5">
          <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${open ? 'bg-usco-vinotinto' : 'bg-gray-400'}`}>{n}</span>
          <span className="text-sm font-bold text-gray-800">{label}</span>
          <span className="text-xs text-gray-500 hidden sm:inline">— {sub}</span>
        </div>
        {open ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronRight size={16} className="text-gray-400" />}
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[90vh]">

        {/* ── Sticky header vinotinto ── */}
        <div className="bg-linear-to-r from-usco-vinotinto to-usco-vinotinto-dark rounded-t-2xl px-6 py-4 flex items-start justify-between shrink-0">
          <div>
            <h2 className="text-base font-bold text-white leading-tight">
              {convocatoria ? 'Editar Convocatoria' : 'Nueva Convocatoria de Monitoría'}
            </h2>
            <p className="text-xs text-white/70 mt-0.5">Formato MI-FOR-FO-14 · Acuerdo 012/2023 USCO</p>
          </div>
          <button onClick={onClose} className="text-white/70 hover:text-white mt-0.5"><X size={20} /></button>
        </div>

        {/* ── Scrollable body ── */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
          {error && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <p className="text-xs leading-relaxed">{error}</p>
            </div>
          )}

          {/* Catálogo de plantillas */}
          {!convocatoria && plantillas.length > 0 && (() => {
            const programas = Array.from(new Set(plantillas.map(p => p.programa).filter(Boolean))).sort();
            const asigs = Array.from(new Set(
              plantillas.filter(p => !filterProg || p.programa === filterProg).map(p => p.asignatura_nombre)
            )).sort();
            const filtradas = plantillas.filter(p =>
              (!filterProg || p.programa === filterProg) &&
              (!filterAsig || p.asignatura_nombre === filterAsig)
            );
            return (
              <div className="border border-emerald-200 rounded-xl overflow-hidden">
                <button type="button" onClick={() => setShowPlantillaPanel(v => !v)}
                  className="w-full flex items-center justify-between px-4 py-3 bg-emerald-50 hover:bg-emerald-100 transition-colors">
                  <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1.5">
                    <ListChecks size={13} /> Cargar desde catálogo institucional de monitorías
                  </span>
                  <span className="text-xs text-emerald-500">{showPlantillaPanel ? '▲ Ocultar' : '▼ Ver catálogo'}</span>
                </button>
                {showPlantillaPanel && (
                  <div className="p-3 bg-white border-t border-emerald-100 space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <select value={filterProg} onChange={e => { setFilterProg(e.target.value); setFilterAsig(''); }}
                        className="px-2.5 py-1.5 text-xs border border-gray-200 rounded-lg bg-white focus:outline-none">
                        <option value="">Todos los programas</option>
                        {programas.map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                      <select value={filterAsig} onChange={e => setFilterAsig(e.target.value)}
                        className="px-2.5 py-1.5 text-xs border border-gray-200 rounded-lg bg-white focus:outline-none">
                        <option value="">Todas las asignaturas</option>
                        {asigs.map(a => <option key={a} value={a}>{a}</option>)}
                      </select>
                    </div>
                    <div className="max-h-52 overflow-y-auto divide-y divide-gray-50 rounded-lg border border-gray-100">
                      {filtradas.length === 0
                        ? <p className="px-4 py-3 text-xs text-gray-400 italic">Sin resultados.</p>
                        : filtradas.map(pl => (
                          <button key={pl.id} type="button" onClick={() => applyPlantilla(pl)}
                            className="w-full text-left px-3 py-2.5 hover:bg-emerald-50 transition-colors group">
                            <p className="text-sm font-semibold text-gray-800 group-hover:text-emerald-700">{pl.nombre_sugerido}</p>
                            <div className="flex flex-wrap gap-x-3 mt-0.5">
                              <span className="text-xs text-gray-500">{pl.asignatura_nombre}</span>
                              <span className="text-xs text-emerald-600">{pl.horas_semana}h/sem · {pl.horas_semestre}h/sem·est</span>
                            </div>
                          </button>
                        ))}
                    </div>
                    <p className="text-[10px] text-gray-400 italic">Los campos se autocompletan. Puedes ajustar fechas y monitores.</p>
                  </div>
                )}
              </div>
            );
          })()}

          {/* ── Sección ① Datos Básicos ── */}
          <SectionHeader n={1} label="Datos Básicos" sub="Identificación de la convocatoria"
            color="bg-blue-50 border-blue-200" open={sec1Open} onToggle={() => setSec1Open(v => !v)} />
          {sec1Open && (
            <div className="bg-gray-50/60 border border-gray-200 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-400 italic">Campos obligatorios *</span>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Título *</label>
                <input required value={form.titulo} onChange={f('titulo')} placeholder="Ej: Monitoría Cálculo I — 2026-1"
                  className={inputCls} />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Asignatura *</label>
                  <select required value={form.asignatura_id} onChange={f('asignatura_id')} className={inputCls}>
                    <option value="">Seleccionar...</option>
                    {asignaturas.map(a => <option key={a.id} value={a.id}>{a.nombre}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Sede</label>
                  <select value={form.sede} onChange={f('sede')} className={inputCls}>
                    {SEDES_USCO.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              {esJefe && (
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Profesor *</label>
                  <select required value={form.profesor_id} onChange={f('profesor_id')} className={inputCls}>
                    <option value="">Seleccionar...</option>
                    {profesoresFiltrados.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Tipo de monitoría <span className="text-gray-400 font-normal text-xs">(Art. 3)</span></label>
                  <select value={form.tipo_monitoria} onChange={f('tipo_monitoria')} className={inputCls}>
                    {Object.entries(TIPO_MONITORIA_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Período académico *</label>
                  <input required value={form.periodo_academico} onChange={f('periodo_academico')} placeholder="2026-1"
                    className={inputCls} />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Monitores requeridos *</label>
                <input required type="number" min="1" value={form.num_monitores_requeridos} onChange={f('num_monitores_requeridos')}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto" />
              </div>
            </div>
          )}

          {/* ── Sección ② Postulaciones — MI-FOR-FO-14 ── */}
          <SectionHeader n={2} label="Postulaciones" sub="Ventana y fechas del proceso — MI-FOR-FO-14"
            color="bg-indigo-50 border-indigo-200" open={sec2Open} onToggle={() => setSec2Open(v => !v)} />
          {sec2Open && (
            <div className="bg-gray-50/60 border border-gray-200 rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Inicio postulaciones *</label>
                  <input required type="datetime-local" value={form.fecha_inicio_postulacion} onChange={f('fecha_inicio_postulacion')}
                    className={inputCls} />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Cierre postulaciones *</label>
                  <input required type="datetime-local" value={form.fecha_fin_postulacion} onChange={f('fecha_fin_postulacion')}
                    className={inputCls} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Publicación de resultados <span className="text-gray-400 font-normal text-xs">(Art. 8)</span></label>
                <input type="datetime-local" value={form.fecha_publicacion_resultados} onChange={f('fecha_publicacion_resultados')}
                  className={inputCls} />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Horas / semana *</label>
                  <input required type="number" min="1" value={form.horas_semana} onChange={f('horas_semana')} className={inputCls} />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Horas / semestre *</label>
                  <input required type="number" min="1" value={form.horas_semestre} onChange={f('horas_semestre')} className={inputCls} />
                </div>
              </div>
            </div>
          )}

          {/* ── Sección ③ Requisitos y Actividades ── */}
          <SectionHeader n={3} label="Requisitos y Actividades" sub="Perfil del monitor — Acuerdo 012/2023 Art. 4"
            color="bg-amber-50 border-amber-200" open={sec3Open} onToggle={() => setSec3Open(v => !v)} />
          {sec3Open && (
            <div className="bg-gray-50/60 border border-gray-200 rounded-xl p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">Promedio mínimo</label>
                  <input type="number" step="0.1" min="0" max="5" value={form.promedio_minimo} onChange={f('promedio_minimo')} className={inputCls} />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">% Créditos mínimo</label>
                  <input type="number" step="1" min="0" max="100" value={form.creditos_minimo_pct} onChange={f('creditos_minimo_pct')} className={inputCls} />
                </div>
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Descripción general</label>
                <textarea value={form.descripcion} onChange={f('descripcion')} rows={2}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto resize-none" />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Actividades del monitor <span className="text-gray-400 font-normal text-xs">(para FO-14)</span></label>
                <textarea value={form.descripcion_actividades} onChange={f('descripcion_actividades')} rows={3}
                  placeholder="Ej: Apoyo en clases presenciales, atención de consultas..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto resize-none" />
              </div>
            </div>
          )}
        </form>

        {/* ── Sticky footer ── */}
        <div className="px-6 py-4 border-t border-gray-100 flex gap-3 shrink-0 bg-white rounded-b-2xl">
          <button type="button" onClick={onClose}
            className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
            Cancelar
          </button>
          <button type="submit" form="" disabled={saving} onClick={handleSubmit}
            className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-xl hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2 transition-colors">
            {saving && <Loader2 size={15} className="animate-spin" />}
            {saving ? 'Guardando...' : (convocatoria ? 'Guardar cambios' : '+ Crear Convocatoria')}
          </button>
        </div>

      </div>
    </div>
  );
}

// ─── Modal: Ver Detalle ──────────────────────────────────────────────────────
function ModalDetalle({
  convocatoria, onClose, onRefresh,
}: { convocatoria: Convocatoria; onClose: () => void; onRefresh: () => void; }) {
  const { user } = useAuthContext();
  const [postulantes, setPostulantes] = useState<Postulacion[]>([]);
  const [loadingPost, setLoadingPost] = useState(false);
  const [cambiandoEstado, setCambiandoEstado] = useState(false);
  const [ejecutandoSeleccion, setEjecutandoSeleccion] = useState(false);
  const [msg, setMsg] = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);
  const canSeePostulantes = user?.rol === 'jefe_programa' || user?.rol === 'decano' || user?.rol === 'profesor';
  const sigEstado = TRANSICION[convocatoria.estado];

  useEffect(() => {
    if (!canSeePostulantes) return;
    setLoadingPost(true);
    postulacionesService.getPorConvocatoria(convocatoria.id)
      .then(r => setPostulantes(r.data))
      .catch(() => setPostulantes([]))
      .finally(() => setLoadingPost(false));
  }, [convocatoria.id, canSeePostulantes]);

  async function avanzarEstado() {
    if (!sigEstado) return;
    setCambiandoEstado(true); setMsg(null);
    try {
      await convocatoriasService.cambiarEstado(convocatoria.id, sigEstado);
      setMsg({ tipo: 'ok', texto: `Estado cambiado a: ${estadoLabel[sigEstado]}` });
      onRefresh();
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMsg({ tipo: 'err', texto: m ?? 'Error al cambiar estado' });
    } finally { setCambiandoEstado(false); }
  }

  async function ejecutarSeleccion() {
    setEjecutandoSeleccion(true); setMsg(null);
    try {
      await seleccionService.ejecutarAlgoritmo(convocatoria.id);
      setMsg({ tipo: 'ok', texto: 'Algoritmo ejecutado. Resultados actualizados.' });
      setLoadingPost(true);
      postulacionesService.getPorConvocatoria(convocatoria.id)
        .then(r => setPostulantes(r.data)).finally(() => setLoadingPost(false));
    } catch (e: unknown) {
      const m = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMsg({ tipo: 'err', texto: m ?? 'Error al ejecutar selección' });
    } finally { setEjecutandoSeleccion(false); }
  }

  const estadoBadgePost: Record<string, string> = {
    pendiente: 'bg-gray-100 text-gray-600',
    en_revision: 'bg-blue-100 text-blue-700',
    preseleccionado: 'bg-amber-100 text-amber-700',
    seleccionado: 'bg-emerald-100 text-emerald-700',
    no_seleccionado: 'bg-red-100 text-red-600',
    desistido: 'bg-gray-100 text-gray-400',
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl my-4">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-bold text-gray-800">{convocatoria.titulo}</h2>
            <p className="text-xs text-gray-400 mt-0.5">{convocatoria.asignatura?.nombre} · {convocatoria.periodo_academico}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>

        <div className="px-6 py-4 space-y-4 max-h-[75vh] overflow-y-auto">
          {msg && (
            <div className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${msg.tipo === 'ok' ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
              {msg.tipo === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
              {msg.texto}
            </div>
          )}

          {/* Info general */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {[
              ['Estado', <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${estadoBadge[convocatoria.estado]}`}>{estadoLabel[convocatoria.estado]}</span>],
              ['Profesor', convocatoria.profesor ? `${convocatoria.profesor.nombres} ${convocatoria.profesor.apellidos}` : '—'],
              ['Monitores req.', convocatoria.num_monitores_requeridos],
              ['Horas/semana', `${convocatoria.horas_semana}h`],
              ['Horas/semestre', `${convocatoria.horas_semestre}h`],
              ['Promedio mín.', convocatoria.promedio_minimo],
              ['Créditos mín.', `${convocatoria.creditos_minimo_pct}%`],
              ['Postulantes', convocatoria.total_postulantes ?? 0],
              ['Cierre', new Date(convocatoria.fecha_fin_postulacion).toLocaleDateString('es-CO')],
            ].map(([label, value], i) => (
              <div key={i} className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-400 mb-0.5">{label}</p>
                <p className="text-sm font-semibold text-gray-800">{value}</p>
              </div>
            ))}
          </div>

          {convocatoria.descripcion && (
            <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3">{convocatoria.descripcion}</p>
          )}

          {/* Acciones de estado — solo jefe_programa/decano */}
          {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && (
            <div className="flex flex-wrap gap-2 pt-1 border-t border-gray-100">
              {sigEstado && (
                <button onClick={avanzarEstado} disabled={cambiandoEstado}
                  className="flex items-center gap-1.5 text-xs font-semibold bg-usco-vinotinto text-white px-4 py-2 rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60">
                  {cambiandoEstado ? <Loader2 size={13} className="animate-spin" /> : <ChevronRight size={13} />}
                  {TRANSICION_LABEL[convocatoria.estado]}
                </button>
              )}
              {convocatoria.estado === 'en_evaluacion' && (
                <button onClick={ejecutarSeleccion} disabled={ejecutandoSeleccion}
                  className="flex items-center gap-1.5 text-xs font-semibold bg-amber-500 text-white px-4 py-2 rounded-lg hover:bg-amber-600 disabled:opacity-60">
                  {ejecutandoSeleccion ? <Loader2 size={13} className="animate-spin" /> : <Star size={13} />}
                  Ejecutar selección RF-MON-05
                </button>
              )}
            </div>
          )}

          {/* Descargar FO-46 / FO-14 */}
          {canSeePostulantes && (
            <div className="pt-1 border-t border-gray-100 flex flex-wrap gap-2">
              <button
                onClick={async () => {
                  try {
                    const r = await reportesService.getFO46(convocatoria.id);
                    generarFO46(r.data);
                  } catch { /* silencioso */ }
                }}
                className="flex items-center gap-2 text-xs font-semibold text-usco-gris border border-gray-200 hover:text-usco-vinotinto hover:border-usco-vinotinto/30 px-3 py-2 rounded-lg transition-colors">
                <FileText size={13} /> FO-46 Cartel Convocatoria
              </button>
              {(convocatoria.estado === 'en_evaluacion' || convocatoria.estado === 'finalizada') && (
                <button
                  onClick={async () => {
                    try {
                      const r = await pdfService.fo14(convocatoria.id);
                      downloadBlob(new Blob([r.data], { type: 'application/pdf' }),
                        `FO-14_Monitor_${convocatoria.id}.pdf`);
                    } catch (err) {
                      console.error('Error descargando FO-14:', err);
                      alert('Error al generar el documento FO-14. Verifique que haya un monitor seleccionado.');
                    }
                  }}
                  className="flex items-center gap-2 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-3 py-2 rounded-lg transition-colors">
                  <FileText size={13} /> FO-14 Requerimiento Monitores
                </button>
              )}
            </div>
          )}

          {/* Lista de postulantes */}
          {canSeePostulantes && (
            <div>
              <h3 className="text-sm font-bold text-gray-700 mb-3 flex items-center gap-1.5">
                <FileText size={15} /> Postulantes ({postulantes.length})
              </h3>
              {loadingPost ? (
                <div className="flex items-center justify-center py-6 text-gray-400"><Loader2 size={20} className="animate-spin mr-2" />Cargando...</div>
              ) : postulantes.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">Sin postulantes aún</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {postulantes.map(p => (
                    <div key={p.id} className="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2">
                      <div>
                        <p className="text-sm font-medium text-gray-800">
                          {p.estudiante ? `${p.estudiante.nombres} ${p.estudiante.apellidos}` : `#${p.estudiante_id}`}
                        </p>
                        <p className="text-xs text-gray-400">
                          Prom: {p.promedio_estudiante?.toFixed(2) ?? '—'} · Nota: {p.nota_asignatura?.toFixed(2) ?? '—'}
                          {p.puntaje_final != null && ` · Puntaje: ${p.puntaje_final.toFixed(4)}`}
                          {p.puesto != null && ` · #${p.puesto}`}
                        </p>
                      </div>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${estadoBadgePost[p.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                        {p.estado.replace('_', ' ')}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Modal: Postularse (estudiante) ─────────────────────────────────────────
function ModalPostularse({
  convocatoria, onClose, onSuccess,
}: { convocatoria: Convocatoria; onClose: () => void; onSuccess: () => void; }) {
  const [carta, setCarta] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const { testingMode } = useSystemContext();
  const postulacionCerrada = !testingMode && new Date(convocatoria.fecha_fin_postulacion) < new Date();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (carta.trim().length < 30) { setError('La carta debe tener al menos 30 caracteres.'); return; }
    setSaving(true); setError('');
    try {
      await postulacionesService.postular(convocatoria.id, { carta_motivacion: carta });
      onSuccess();
    } catch (err: unknown) {
      const raw = (err as { response?: { data?: { detail?: string | { mensaje?: string } } } })?.response?.data?.detail;
      setError(typeof raw === 'string' ? raw : (raw as { mensaje?: string })?.mensaje ?? 'Error al postularse');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
        <div className="flex items-center justify-between px-6 pt-5 pb-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-bold text-gray-800">Postularse a Monitoría</h2>
            <p className="text-xs text-gray-400 mt-0.5">{convocatoria.titulo}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-3">
          {postulacionCerrada && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-lg flex items-center gap-1.5">
              <AlertCircle size={14} />
              El período de postulación ha cerrado. Finalizó el {new Date(convocatoria.fecha_fin_postulacion).toLocaleDateString('es-CO')}.
            </div>
          )}
          {error && (
            <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <p className="text-xs leading-relaxed">{error}</p>
            </div>
          )}
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-600 space-y-1">
            <p><strong>Asignatura:</strong> {convocatoria.asignatura?.nombre}</p>
            <p><strong>Promedio mínimo requerido:</strong> {convocatoria.promedio_minimo}</p>
            <p><strong>Créditos mínimos:</strong> {convocatoria.creditos_minimo_pct}%</p>
            <p><strong>Cierre:</strong> {new Date(convocatoria.fecha_fin_postulacion).toLocaleDateString('es-CO')}</p>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">
              Carta de motivación * <span className="text-gray-400 font-normal">(mín. 30 caracteres)</span>
            </label>
            <textarea
              required minLength={30} rows={5} value={carta}
              onChange={e => setCarta(e.target.value)}
              placeholder="Explica por qué deseas ser monitor de esta asignatura, qué habilidades tienes y cómo aportarías..."
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 resize-none"
            />
            <p className="text-right text-xs text-gray-400 mt-1">{carta.length} caracteres</p>
          </div>
          <div className="flex gap-3 pt-2 border-t border-gray-100">
            <button type="button" onClick={onClose}
              className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
            <button type="submit" disabled={saving || postulacionCerrada}
              className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 size={15} className="animate-spin" />}
              {saving ? 'Enviando...' : 'Enviar postulación'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Componente principal ────────────────────────────────────────────────────
export function Convocatorias() {
  const { user } = useAuthContext();
  const { testingMode } = useSystemContext();
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>([]);
  const [search, setSearch] = useState('');
  const [filterEstado, setFilterEstado] = useState<string>('');
  const [filterSede, setFilterSede] = useState('');
  const [filterFacultad, setFilterFacultad] = useState('');
  const [filterPrograma, setFilterPrograma] = useState('');
  const [filterProfesorC, setFilterProfesorC] = useState('');
  const [filterAsignaturaC, setFilterAsignaturaC] = useState('');
  const [loading, setLoading] = useState(true);
  const [mensaje, setMensaje] = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);

  const [modalCrear, setModalCrear] = useState(false);
  const [modalEditar, setModalEditar] = useState<Convocatoria | null>(null);
  const [modalDetalle, setModalDetalle] = useState<Convocatoria | null>(null);
  const [modalPostularse, setModalPostularse] = useState<Convocatoria | null>(null);
  const [misPostIds, setMisPostIds] = useState<Set<number>>(new Set());
  const [recomendaciones, setRecomendaciones] = useState<RecomendacionIA[]>([]);
  const [loadingRec, setLoadingRec] = useState(false);

  const cargarMisPost = useCallback(async () => {
    if (user?.rol !== 'estudiante') return;
    try {
      const r = await postulacionesService.getMias();
      setMisPostIds(new Set(r.data.map((p: Postulacion) => p.convocatoria_id)));
    } catch { /* ignore */ }
  }, [user?.rol]);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const r = await convocatoriasService.getAll();
      setConvocatorias(r.data);
    } catch { setConvocatorias([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);
  useEffect(() => { cargarMisPost(); }, [cargarMisPost]);
  useEffect(() => {
    if (user?.rol !== 'estudiante') return;
    setLoadingRec(true);
    iaService.getRecomendaciones(5)
      .then(r => setRecomendaciones(r.data.recomendaciones || []))
      .catch(() => setRecomendaciones([]))
      .finally(() => setLoadingRec(false));
  }, [user?.rol]);

  const sedesUnicasC = Array.from(new Set(convocatorias.map(c => c.sede || c.profesor?.sede).filter(Boolean))).sort() as string[];
  const facultadesUnicasC = Array.from(new Set(convocatorias.map(c => c.asignatura?.facultad).filter(Boolean))).sort() as string[];
  const programasUnicosC = Array.from(new Set(convocatorias.map(c => c.asignatura?.programa).filter(Boolean))).sort() as string[];
  const profesoresUnicosC = Array.from(new Set(convocatorias.map(c => c.profesor ? `${c.profesor.nombres} ${c.profesor.apellidos}`.trim() : '').filter(Boolean))).sort();
  const asignaturasUnicasC = Array.from(new Set(convocatorias.map(c => c.asignatura?.nombre).filter(Boolean))).sort() as string[];

  const filtered = convocatorias.filter((c) => {
    const matchSearch = c.titulo.toLowerCase().includes(search.toLowerCase()) ||
      (c.asignatura?.nombre.toLowerCase().includes(search.toLowerCase()) ?? false);
    const matchEstado = filterEstado ? c.estado === filterEstado : true;
    const matchSede = !filterSede || (c.sede || c.profesor?.sede) === filterSede;
    const matchFacultad = !filterFacultad || c.asignatura?.facultad === filterFacultad;
    const matchPrograma = !filterPrograma || c.asignatura?.programa === filterPrograma;
    const matchProfesor = !filterProfesorC || `${c.profesor?.nombres ?? ''} ${c.profesor?.apellidos ?? ''}`.toLowerCase().includes(filterProfesorC.toLowerCase());
    const matchAsignatura = !filterAsignaturaC || c.asignatura?.nombre === filterAsignaturaC;
    return matchSearch && matchEstado && matchSede && matchFacultad && matchPrograma && matchProfesor && matchAsignatura;
  });

  const canCreate = user?.rol === 'jefe_programa' || user?.rol === 'decano' || user?.rol === 'profesor';

  function showMsg(tipo: 'ok' | 'err', texto: string) {
    setMensaje({ tipo, texto });
    setTimeout(() => setMensaje(null), 4000);
  }

  return (
    <div className="space-y-5">
      {/* Modales */}
      {modalCrear && (
        <ModalConvocatoria convocatoria={null} onClose={() => setModalCrear(false)}
          onSuccess={() => { setModalCrear(false); cargar(); showMsg('ok', 'Convocatoria creada en borrador.'); }} />
      )}
      {modalEditar && (
        <ModalConvocatoria convocatoria={modalEditar} onClose={() => setModalEditar(null)}
          onSuccess={() => { setModalEditar(null); cargar(); showMsg('ok', 'Convocatoria actualizada.'); }} />
      )}
      {modalDetalle && (
        <ModalDetalle convocatoria={modalDetalle} onClose={() => setModalDetalle(null)}
          onRefresh={() => { cargar(); setModalDetalle(null); }} />
      )}
      {modalPostularse && (
        <ModalPostularse convocatoria={modalPostularse} onClose={() => setModalPostularse(null)}
          onSuccess={() => { setModalPostularse(null); cargar(); cargarMisPost(); showMsg('ok', '¡Postulación enviada correctamente!'); }} />
      )}

      {/* Mensaje flash */}
      {mensaje && (
        <div className={`flex items-center gap-3 rounded-xl px-5 py-3 text-sm font-medium ${
          mensaje.tipo === 'ok' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-red-50 border border-red-200 text-red-700'}`}>
          {mensaje.tipo === 'ok' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          {mensaje.texto}
        </div>
      )}

      {/* Widget IA — solo estudiantes */}
      {user?.rol === 'estudiante' && (recomendaciones.length > 0 || loadingRec) && (
        <div className="bg-gradient-to-br from-usco-vinotinto/5 to-usco-vinotinto/10 border border-usco-vinotinto/20 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles size={18} className="text-usco-vinotinto" />
            <h2 className="font-bold text-gray-800 text-sm">Recomendaciones IA — Convocatorias para ti</h2>
            <span className="ml-auto text-xs text-gray-400 italic">Ordenadas por probabilidad de selección</span>
          </div>
          {loadingRec ? (
            <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
              <Loader2 size={15} className="animate-spin" /> Calculando recomendaciones...
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {recomendaciones.map((rec) => (
                <div key={rec.convocatoria_id}
                  className="bg-white rounded-xl border border-usco-vinotinto/15 p-4 flex flex-col gap-2 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-bold text-gray-800 leading-tight line-clamp-2">{rec.titulo}</p>
                    {rec.programa_match && (
                      <span className="shrink-0 text-[10px] font-semibold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Tu programa</span>
                    )}
                  </div>
                  <p className="text-[11px] text-gray-500">{rec.asignatura}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <div className="flex-1 bg-gray-100 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          rec.probabilidad_pct >= 70 ? 'bg-emerald-500'
                          : rec.probabilidad_pct >= 40 ? 'bg-amber-400'
                          : 'bg-usco-vinotinto'}`}
                        style={{ width: `${Math.min(rec.probabilidad_pct, 100)}%` }}
                      />
                    </div>
                    <span className={`text-xs font-bold ${
                      rec.probabilidad_pct >= 70 ? 'text-emerald-600'
                      : rec.probabilidad_pct >= 40 ? 'text-amber-600'
                      : 'text-usco-vinotinto'}`}>
                      {rec.probabilidad_pct}%
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-gray-500">
                    <span className="flex items-center gap-1"><Clock size={11} />{rec.dias_restantes}d restantes</span>
                    <span className="flex items-center gap-1"><TrendingUp size={11} />{rec.horas_semana}h/sem</span>
                    <span className="flex items-center gap-1"><Users size={11} />{rec.num_postulantes} postulantes</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-800">Convocatorias de Monitoría</h1>
          <p className="text-sm text-gray-500 mt-0.5">{filtered.length} convocatoria(s)</p>
        </div>
        {canCreate && (
          <button onClick={() => setModalCrear(true)}
            className="flex items-center gap-2 bg-usco-vinotinto hover:bg-usco-vinotinto/90 text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm">
            <Plus size={16} /> Nueva Convocatoria
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input type="text" placeholder="Buscar por título o asignatura..." value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full border border-gray-200 rounded-lg pl-9 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Filter size={15} className="text-gray-400" />
          <select value={filterEstado} onChange={(e) => setFilterEstado(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
            <option value="">Todos los estados</option>
            {Object.entries(estadoLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          {programasUnicosC.length > 1 && (
            <select value={filterPrograma} onChange={e => setFilterPrograma(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
              <option value="">Todos los programas</option>
              {programasUnicosC.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          )}
          {asignaturasUnicasC.length > 1 && (
            <select value={filterAsignaturaC} onChange={e => setFilterAsignaturaC(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
              <option value="">Todas las materias</option>
              {asignaturasUnicasC.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          )}
          {sedesUnicasC.length > 1 && (
            <select value={filterSede} onChange={e => setFilterSede(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
              <option value="">Todas las sedes</option>
              {sedesUnicasC.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          )}
          {facultadesUnicasC.length > 1 && (
            <select value={filterFacultad} onChange={e => setFilterFacultad(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
              <option value="">Todas las facultades</option>
              {facultadesUnicasC.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          )}
          {(user?.rol === 'admin' || user?.rol === 'decano') && profesoresUnicosC.length > 1 && (
            <select value={filterProfesorC} onChange={e => setFilterProfesorC(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
              <option value="">Todos los profesores</option>
              {profesoresUnicosC.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          )}
        </div>
      </div>

      {/* Lista */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <Loader2 size={24} className="animate-spin text-usco-vinotinto" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-400 bg-white rounded-xl border border-gray-100">
          <BookOpen size={48} className="mx-auto mb-3 opacity-40" />
          <p className="font-medium">No se encontraron convocatorias</p>
          <p className="text-sm">Intenta con otro filtro o término de búsqueda.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((conv) => (
            <div key={conv.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow flex flex-col">
              <div className="flex items-start justify-between gap-2 mb-3">
                <div className="bg-usco-vinotinto/10 rounded-lg p-2">
                  <BookOpen size={18} className="text-usco-vinotinto" />
                </div>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${estadoBadge[conv.estado]}`}>
                  {estadoLabel[conv.estado]}
                </span>
              </div>

              <h3 className="font-semibold text-gray-800 text-sm leading-snug mb-1">{conv.titulo}</h3>
              {conv.asignatura && (
                <p className="text-xs text-usco-vinotinto font-medium mb-2">{conv.asignatura.nombre}</p>
              )}

              <div className="space-y-1.5 text-xs text-gray-500 flex-1">
                <div className="flex items-center gap-1.5">
                  <Users size={12} />
                  <span>{conv.num_monitores_requeridos} monitor(es)
                    {conv.total_postulantes != null && (
                      <span className="ml-1 font-semibold text-usco-gris">· {conv.total_postulantes} postulante(s)</span>
                    )}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Calendar size={12} />
                  <span>Cierre: {new Date(conv.fecha_fin_postulacion).toLocaleDateString('es-CO')}</span>
                </div>
                <p className="font-medium">{conv.horas_semana}h/sem · {conv.horas_semestre}h total</p>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 flex gap-2 flex-wrap">
                <button onClick={() => setModalDetalle(conv)}
                  className="flex items-center gap-1.5 text-xs font-semibold text-usco-gris hover:text-usco-vinotinto border border-gray-200 px-3 py-1.5 rounded-lg transition-colors">
                  <Eye size={13} /> Ver detalle
                </button>

                {/* Editar — jefe_programa/decano o profesor dueño en borrador/abierta */}
                {((user?.rol === 'jefe_programa' || user?.rol === 'decano') || (user?.rol === 'profesor' && conv.profesor_id === user?.id)) &&
                  ['borrador', 'abierta'].includes(conv.estado) && (
                  <button onClick={() => setModalEditar(conv)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-usco-vinotinto border border-gray-200 px-3 py-1.5 rounded-lg transition-colors">
                    <Edit2 size={13} /> Editar
                  </button>
                )}

                {/* Avanzar estado — solo jefe_programa/decano */}
                {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && TRANSICION[conv.estado] && (
                  <button onClick={() => setModalDetalle(conv)}
                    className="flex items-center gap-1.5 text-xs font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 px-3 py-1.5 rounded-lg transition-colors">
                    <ArrowRight size={13} /> {TRANSICION_LABEL[conv.estado]}
                  </button>
                )}

                {/* Postularse — estudiante */}
                {user?.rol === 'estudiante' &&
                  (testingMode
                    ? conv.estado !== 'finalizada'
                    : conv.estado === 'abierta' && new Date(conv.fecha_fin_postulacion) > new Date()
                  ) && (
                  misPostIds.has(conv.id)
                    ? <div className="flex-1 text-xs font-semibold bg-emerald-50 border border-emerald-200 text-emerald-700 py-1.5 rounded-lg flex items-center justify-center gap-1.5">
                        <CheckCircle size={13} /> Ya postulado
                      </div>
                    : <button onClick={() => setModalPostularse(conv)}
                        className={`flex-1 text-xs font-semibold py-1.5 rounded-lg transition-colors flex items-center justify-center gap-1.5 ${
                          testingMode && conv.estado !== 'abierta'
                            ? 'bg-amber-500 hover:bg-amber-600 text-white'
                            : 'bg-usco-vinotinto hover:bg-usco-vinotinto/90 text-white'
                        }`}>
                        {testingMode && conv.estado !== 'abierta' && '🧪 '}
                        Postularme
                      </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
