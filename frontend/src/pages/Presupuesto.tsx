import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { DollarSign, TrendingUp, TrendingDown, AlertCircle, Loader2, ChevronDown, Settings, Send, CheckCircle, X, RefreshCw, MessageSquare, Plus, ArrowUpCircle, Info, Paperclip, Upload, Download, Trash2, FileText, Eye } from 'lucide-react';
import type { Presupuesto as PresupuestoType } from '../types';
import { presupuestoService, downloadAuthenticated } from '../services/api';
import { useAuthContext } from '../context/AuthContext';

interface MovimientoItem {
  id: number;
  tipo: string;
  monto: number;
  concepto: string;
  fecha: string | null;
}

interface PresupuestoExtended extends PresupuestoType {
  monto_disponible: number;
  porcentaje_ejecutado: number;
  estado?: string;
  observaciones_admin?: string | null;
  descripcion?: string | null;
  monto_solicitado?: number | null;
}

const ESTADO_BADGE: Record<string, { label: string; color: string }> = {
  borrador:     { label: 'Borrador',          color: 'bg-gray-100 text-gray-600' },
  solicitado:   { label: 'Solicitado',         color: 'bg-blue-100 text-blue-700' },
  aprobado:     { label: 'Aprobado',           color: 'bg-emerald-100 text-emerald-700' },
  rechazado:    { label: 'Rechazado',          color: 'bg-red-100 text-red-700' },
  modificacion: { label: 'Pend. modificación', color: 'bg-amber-100 text-amber-700' },
};

const tipoColor: Record<string, string> = {
  asignacion: 'text-emerald-600',
  comprometido: 'text-orange-600',
  ejecucion: 'text-red-600',
  ajuste: 'text-amber-600',
  devolucion: 'text-blue-600',
};

function formatCOP(val: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
}

function BarraProgreso({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>{label}</span>
        <span className="font-semibold">{pct.toFixed(1)}%</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3">
        <div className={`h-3 rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs text-gray-400 mt-0.5 text-right">{formatCOP(value)}</p>
    </div>
  );
}

interface DecisionModal {
  tipo: 'aprobar' | 'rechazar' | 'modificacion';
  periodo: string;
}

export function Presupuesto() {
  const { user } = useAuthContext();
  const [todos, setTodos] = useState<PresupuestoExtended[]>([]);
  const [periodoSel, setPeriodoSel] = useState('');
  const [presupuesto, setPresupuesto] = useState<PresupuestoExtended | null>(null);
  const [movimientos, setMovimientos] = useState<MovimientoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [flash, setFlash] = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);
  const [accionando, setAccionando] = useState(false);
  const [decisionModal, setDecisionModal] = useState<DecisionModal | null>(null);
  const [obsInput, setObsInput] = useState('');
  // Modales jefe
  const [modalNuevo, setModalNuevo] = useState(false);
  const [periodeSugerido, setPeriodeSugerido] = useState('');
  const [nuevoMonto, setNuevoMonto] = useState('');
  const [nuevaDesc, setNuevaDesc] = useState('');
  const [modalIncremento, setModalIncremento] = useState(false);
  const [incrementoMonto, setIncrementoMonto] = useState('');
  const [incrementoDesc, setIncrementoDesc] = useState('');
  // Modal: solicitar
  const [modalSolicitar, setModalSolicitar] = useState(false);
  // Archivos adjuntos durante la solicitud / incremento
  interface ArchivoNuevo { file: File; tipo: string; desc: string; }
  const [archivosSol, setArchivosSol] = useState<ArchivoNuevo[]>([]);
  const [archivosInc, setArchivosInc] = useState<ArchivoNuevo[]>([]);
  // Documentos de soporte
  interface DocItem { id: number; tipo_solicitud: string; nombre_original: string; descripcion: string | null; subido_por: string; created_at: string | null; download_url: string; }
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadTipo, setUploadTipo] = useState('solicitud');
  const [uploadDesc, setUploadDesc] = useState('');
  const [uploading, setUploading] = useState(false);
  const [deletingDocId, setDeletingDocId] = useState<number | null>(null);
  const [obsVisible, setObsVisible] = useState(true);
  const [obsModalOpen, setObsModalOpen] = useState(false);

  function showFlash(tipo: 'ok' | 'err', texto: string) {
    setFlash({ tipo, texto });
    setTimeout(() => setFlash(null), 4000);
  }

  async function cargar(periodo?: string) {
    setLoading(true);
    try {
      const all = await presupuestoService.getAll();
      const lista: PresupuestoExtended[] = all.data;
      setTodos(lista);
      const target = periodo ?? lista[0]?.periodo_academico;
      const actual = target
        ? await presupuestoService.getByPeriodo(target)
        : await presupuestoService.getActual();
      setPresupuesto(actual.data);
      setPeriodoSel(actual.data.periodo_academico);
      const rm = await presupuestoService.getMovimientos(actual.data.periodo_academico);
      setMovimientos(rm.data);
    } catch {
      setError('No se pudo cargar el presupuesto. Verifique que exista configuración para el período actual.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { cargar(); }, []);

  // Cargar docs cuando cambia el presupuesto
  useEffect(() => {
    if (presupuesto?.periodo_academico) cargarDocs(presupuesto.periodo_academico);
  }, [presupuesto?.periodo_academico]);

  async function abrirModalNuevo() {
    setModalNuevo(true);
    try {
      const r = await presupuestoService.siguientePeriodo();
      setPeriodeSugerido((r.data as { periodo_sugerido: string }).periodo_sugerido);
    } catch { setPeriodeSugerido(''); }
  }

  async function crearNuevoPeriodo() {
    if (!nuevoMonto) return;
    setAccionando(true);
    try {
      await presupuestoService.crear({ periodo_academico: periodeSugerido, monto_total_asignado: parseFloat(nuevoMonto.replace(/\./g, '').replace(',', '.')), descripcion: nuevaDesc || undefined });
      showFlash('ok', `Presupuesto ${periodeSugerido} creado en borrador. Ajusta el monto y envíalo a Gastos.`);
      setModalNuevo(false); setNuevoMonto(''); setNuevaDesc('');
      await cargar(periodeSugerido);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al crear el presupuesto.');
    } finally { setAccionando(false); }
  }

  async function ejecutarIncremento() {
    if (!presupuesto || !incrementoMonto) return;
    setAccionando(true);
    try {
      await presupuestoService.solicitarIncremento(presupuesto.periodo_academico, {
        nuevo_monto: parseFloat(incrementoMonto.replace(/\./g, '').replace(',', '.')),
        descripcion: incrementoDesc || undefined,
      });
      if (archivosInc.length > 0) {
        await subirArchivos(presupuesto.periodo_academico, archivosInc);
      }
      showFlash('ok', `Solicitud de incremento enviada al Administrador${archivosInc.length > 0 ? ` con ${archivosInc.length} documento(s) de soporte` : ''}.`);
      setModalIncremento(false); setIncrementoMonto(''); setIncrementoDesc(''); setArchivosInc([]);
      await cargar(presupuesto.periodo_academico);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al solicitar el incremento.');
    } finally { setAccionando(false); }
  }

  async function subirArchivos(periodo: string, archivos: { file: File; tipo: string; desc: string }[]) {
    for (const a of archivos) {
      const fd = new FormData();
      fd.append('file', a.file);
      fd.append('tipo_solicitud', a.tipo);
      if (a.desc) fd.append('descripcion', a.desc);
      await presupuestoService.subirDocumento(periodo, fd);
    }
  }

  async function cargarDocs(periodo: string) {
    setLoadingDocs(true);
    try {
      const r = await presupuestoService.listarDocumentos(periodo);
      setDocs(r.data as DocItem[]);
    } catch { setDocs([]); }
    finally { setLoadingDocs(false); }
  }

  async function subirDoc() {
    if (!uploadFile || !presupuesto) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('tipo_solicitud', uploadTipo);
      if (uploadDesc) fd.append('descripcion', uploadDesc);
      await presupuestoService.subirDocumento(presupuesto.periodo_academico, fd);
      showFlash('ok', 'Documento subido correctamente.');
      setUploadFile(null); setUploadDesc('');
      await cargarDocs(presupuesto.periodo_academico);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al subir el documento.');
    } finally { setUploading(false); }
  }

  async function eliminarDoc(docId: number) {
    if (!presupuesto) return;
    setDeletingDocId(docId);
    try {
      await presupuestoService.eliminarDocumento(presupuesto.periodo_academico, docId);
      setDocs(prev => prev.filter(d => d.id !== docId));
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al eliminar el documento.');
    } finally { setDeletingDocId(null); }
  }

  async function cambiarPeriodo(periodo: string) {
    setPeriodoSel(periodo);
    try {
      const r = await presupuestoService.getByPeriodo(periodo);
      setPresupuesto(r.data);
      const rm = await presupuestoService.getMovimientos(periodo);
      setMovimientos(rm.data);
      await cargarDocs(periodo);
    } catch { /* no cambia */ }
  }

  async function ejecutarSolicitar() {
    if (!presupuesto) return;
    setAccionando(true);
    try {
      await presupuestoService.solicitar(presupuesto.periodo_academico);
      if (archivosSol.length > 0) {
        await subirArchivos(presupuesto.periodo_academico, archivosSol);
      }
      showFlash('ok', `Solicitud enviada al Administrador${archivosSol.length > 0 ? ` con ${archivosSol.length} documento(s) de soporte` : ''}.`);
      setModalSolicitar(false);
      setArchivosSol([]);
      await cargar(presupuesto.periodo_academico);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al enviar la solicitud.');
    } finally { setAccionando(false); }
  }

  async function ejecutarDecision() {
    if (!decisionModal) return;
    setAccionando(true);
    const obs = obsInput.trim() || undefined;
    try {
      if (decisionModal.tipo === 'aprobar')
        await presupuestoService.aprobar(decisionModal.periodo, { observaciones: obs });
      else if (decisionModal.tipo === 'rechazar')
        await presupuestoService.rechazar(decisionModal.periodo, { observaciones: obs });
      else
        await presupuestoService.pedirModificacion(decisionModal.periodo, { observaciones: obs });
      showFlash('ok', decisionModal.tipo === 'aprobar' ? 'Presupuesto aprobado.' : decisionModal.tipo === 'rechazar' ? 'Presupuesto rechazado.' : 'Enviado al Jefe para corrección.');
      setDecisionModal(null); setObsInput('');
      await cargar(decisionModal.periodo);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al procesar la decisión.');
    } finally { setAccionando(false); }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 size={26} className="animate-spin text-usco-vinotinto" />
      </div>
    );
  }

  if (error || !presupuesto) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3 text-gray-400">
        <AlertCircle size={40} className="opacity-50" />
        <p className="text-sm">{error || 'Sin datos de presupuesto'}</p>
      </div>
    );
  }

  const p = presupuesto;
  const alertaPct = p.porcentaje_ejecutado >= 85;
  const estadoBadge = ESTADO_BADGE[p.estado ?? 'aprobado'] ?? ESTADO_BADGE.aprobado;

  const modalCfg = decisionModal ? {
    aprobar:     { titulo: 'Aprobar presupuesto',         btnColor: 'bg-emerald-600 hover:bg-emerald-700', icon: <CheckCircle size={15} /> },
    rechazar:    { titulo: 'Rechazar solicitud',          btnColor: 'bg-red-600 hover:bg-red-700',         icon: <X size={15} /> },
    modificacion:{ titulo: 'Pedir modificación al Jefe', btnColor: 'bg-amber-500 hover:bg-amber-600',     icon: <RefreshCw size={15} /> },
  }[decisionModal.tipo] : null;

  return (
    <div className="space-y-6">

      {/* Modal: Enviar solicitud a Gastos */}
      {modalSolicitar && presupuesto && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-800">Enviar solicitud de presupuesto</h3>
              <button onClick={() => setModalSolicitar(false)} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </div>

            <div className="bg-gray-50 rounded-xl px-4 py-3 mb-4 space-y-1">
              <p className="text-xs text-gray-500">Período: <span className="font-bold text-gray-800">{presupuesto.periodo_academico}</span></p>
              <p className="text-xs text-gray-500">Monto propuesto: <span className="font-bold text-usco-vinotinto">{formatCOP(presupuesto.monto_total_asignado)}</span></p>
              {presupuesto.estado === 'rechazado' && (
                <p className="text-xs text-red-600 font-medium">⚠️ Re-enviando solicitud previamente rechazada.</p>
              )}
              {presupuesto.estado === 'modificacion' && (
                <p className="text-xs text-amber-600 font-medium">🔄 Re-enviando solicitud con modificaciones.</p>
              )}
            </div>

            {/* Documentos de soporte */}
            <div className="mb-5">
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-bold text-gray-700 uppercase tracking-wide">Documentos de soporte</p>
                <label className="flex items-center gap-1.5 text-xs font-semibold text-usco-vinotinto cursor-pointer hover:underline">
                  <Plus size={13} /> Agregar archivo
                  <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                    onChange={e => {
                      const f = e.target.files?.[0];
                      if (f) setArchivosSol(prev => [...prev, { file: f, tipo: 'solicitud', desc: '' }]);
                      e.target.value = '';
                    }} />
                </label>
              </div>

              {archivosSol.length === 0 ? (
                <div className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center">
                  <Paperclip size={22} className="mx-auto text-gray-300 mb-2" />
                  <p className="text-xs text-gray-400">Adjunta los documentos que soporten esta solicitud</p>
                  <p className="text-[11px] text-gray-300 mt-1">PDF, Word, Excel, imágenes — máx. 10 MB c/u</p>
                  <label className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-usco-vinotinto px-3 py-1.5 rounded-lg cursor-pointer hover:bg-usco-vinotinto/90">
                    <Upload size={12} /> Seleccionar archivos
                    <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx" multiple
                      onChange={e => {
                        const files = Array.from(e.target.files ?? []);
                        setArchivosSol(prev => [...prev, ...files.map(f => ({ file: f, tipo: 'solicitud', desc: '' }))]);
                        e.target.value = '';
                      }} />
                  </label>
                </div>
              ) : (
                <div className="space-y-2">
                  {archivosSol.map((a, i) => (
                    <div key={i} className="bg-gray-50 border border-gray-100 rounded-xl p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <FileText size={14} className="text-usco-vinotinto shrink-0" />
                        <span className="text-xs font-medium text-gray-700 flex-1 truncate">{a.file.name}</span>
                        <span className="text-[10px] text-gray-400">{(a.file.size / 1024 / 1024).toFixed(1)} MB</span>
                        <button onClick={() => setArchivosSol(prev => prev.filter((_, j) => j !== i))}
                          className="text-red-400 hover:text-red-600 p-0.5"><X size={13} /></button>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[10px] text-gray-400 block mb-0.5">Tipo</label>
                          <select value={a.tipo} onChange={e => setArchivosSol(prev => prev.map((item, j) => j === i ? { ...item, tipo: e.target.value } : item))}
                            className="w-full text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-usco-vinotinto/30">
                            <option value="solicitud">Solicitud de presupuesto</option>
                            <option value="modificacion">Documento de modificación</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[10px] text-gray-400 block mb-0.5">Descripción (opcional)</label>
                          <input value={a.desc} onChange={e => setArchivosSol(prev => prev.map((item, j) => j === i ? { ...item, desc: e.target.value } : item))}
                            placeholder="Ej: Certificado de necesidad"
                            className="w-full text-xs border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-usco-vinotinto/30" />
                        </div>
                      </div>
                    </div>
                  ))}
                  <label className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer hover:text-usco-vinotinto mt-1">
                    <Plus size={12} /> Agregar otro archivo
                    <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                      onChange={e => {
                        const f = e.target.files?.[0];
                        if (f) setArchivosSol(prev => [...prev, { file: f, tipo: 'solicitud', desc: '' }]);
                        e.target.value = '';
                      }} />
                  </label>
                </div>
              )}
            </div>

            <div className="bg-blue-50 rounded-lg px-3 py-2 flex items-start gap-2 mb-5">
              <Info size={13} className="text-blue-500 mt-0.5 shrink-0" />
              <p className="text-xs text-blue-700">El Administrador podrá revisar estos documentos antes de tomar una decisión.</p>
            </div>

            <div className="flex gap-3">
              <button onClick={() => setModalSolicitar(false)}
                className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
              <button onClick={ejecutarSolicitar} disabled={accionando}
                className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
                {accionando ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                {accionando ? 'Enviando...' : `Enviar solicitud${archivosSol.length > 0 ? ` + ${archivosSol.length} doc.` : ''}`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Crear nuevo período */}
      {modalNuevo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-800">Nuevo presupuesto académico</h3>
              <button onClick={() => setModalNuevo(false)} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Período académico</label>
                <input value={periodeSugerido} onChange={e => setPeriodeSugerido(e.target.value)}
                  placeholder="ej. 2026-2"
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                <p className="text-xs text-gray-400 mt-1">Código sugerido basado en períodos existentes.</p>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Monto propuesto (COP) *</label>
                <input type="number" min="1000000" value={nuevoMonto} onChange={e => setNuevoMonto(e.target.value)}
                  placeholder="48000000"
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                {nuevoMonto && <p className="text-xs text-emerald-600 mt-1 font-medium">{formatCOP(parseFloat(nuevoMonto) || 0)}</p>}
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Descripción (opcional)</label>
                <textarea value={nuevaDesc} onChange={e => setNuevaDesc(e.target.value)} rows={2}
                  placeholder="Presupuesto semestre 2026-2..."
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 resize-none" />
              </div>
              <div className="bg-blue-50 rounded-lg px-3 py-2 flex items-start gap-2">
                <Info size={13} className="text-blue-500 mt-0.5 shrink-0" />
                <p className="text-xs text-blue-700">El presupuesto se crea en <strong>borrador</strong>. Podrás ajustar el monto antes de enviarlo al Administrador.</p>
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button onClick={() => setModalNuevo(false)}
                className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
              <button onClick={crearNuevoPeriodo} disabled={accionando || !periodeSugerido || !nuevoMonto}
                className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
                {accionando && <Loader2 size={13} className="animate-spin" />}
                Crear en borrador
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Solicitar incremento */}
      {modalIncremento && presupuesto && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-800">Solicitar incremento de presupuesto</h3>
              <button onClick={() => setModalIncremento(false)} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </div>
            <div className="bg-gray-50 rounded-lg px-4 py-3 mb-4">
              <p className="text-xs text-gray-500">Período: <span className="font-bold text-gray-800">{presupuesto.periodo_academico}</span></p>
              <p className="text-xs text-gray-500 mt-0.5">Monto actual aprobado: <span className="font-bold text-emerald-700">{formatCOP(presupuesto.monto_total_asignado)}</span></p>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Nuevo monto total solicitado (COP) *</label>
                <input type="number" value={incrementoMonto} onChange={e => setIncrementoMonto(e.target.value)}
                  placeholder={String(Math.ceil(presupuesto.monto_total_asignado * 1.2))}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                {incrementoMonto && parseFloat(incrementoMonto) > presupuesto.monto_total_asignado && (
                  <p className="text-xs text-emerald-600 mt-1 font-medium">
                    Incremento: +{formatCOP(parseFloat(incrementoMonto) - presupuesto.monto_total_asignado)}
                  </p>
                )}
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-600 block mb-1">Justificación (opcional)</label>
                <textarea value={incrementoDesc} onChange={e => setIncrementoDesc(e.target.value)} rows={2}
                  placeholder="Necesitamos recursos adicionales para..."
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 resize-none" />
              </div>
              <div className="bg-amber-50 rounded-lg px-3 py-2 flex items-start gap-2">
                <Info size={13} className="text-amber-500 mt-0.5 shrink-0" />
                <p className="text-xs text-amber-700">El presupuesto vuelve a estado <strong>solicitado</strong>. El Administrador recibirá la notificación para aprobar el nuevo monto.</p>
              </div>

              {/* Documentos de soporte para el incremento */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-bold text-gray-700">Documentos de soporte</p>
                  <label className="flex items-center gap-1 text-xs font-semibold text-usco-vinotinto cursor-pointer hover:underline">
                    <Plus size={12} /> Adjuntar
                    <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                      onChange={e => {
                        const f = e.target.files?.[0];
                        if (f) setArchivosInc(prev => [...prev, { file: f, tipo: 'incremento', desc: '' }]);
                        e.target.value = '';
                      }} />
                  </label>
                </div>

                {archivosInc.length === 0 ? (
                  <div className="border-2 border-dashed border-gray-200 rounded-xl p-4 text-center">
                    <label className="cursor-pointer">
                      <Paperclip size={20} className="mx-auto text-gray-300 mb-1" />
                      <p className="text-xs text-gray-400">Adjunta los soportes que justifiquen el incremento</p>
                      <p className="text-[10px] text-gray-300 mt-0.5">PDF, Word, Excel, imágenes — máx. 10 MB c/u</p>
                      <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx" multiple
                        onChange={e => {
                          const files = Array.from(e.target.files ?? []);
                          setArchivosInc(prev => [...prev, ...files.map(f => ({ file: f, tipo: 'incremento', desc: '' }))]);
                          e.target.value = '';
                        }} />
                    </label>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {archivosInc.map((a, i) => (
                      <div key={i} className="bg-gray-50 border border-gray-100 rounded-lg p-2">
                        <div className="flex items-center gap-2">
                          <FileText size={13} className="text-usco-vinotinto shrink-0" />
                          <span className="text-xs flex-1 truncate text-gray-700">{a.file.name}</span>
                          <span className="text-[10px] text-gray-400">{(a.file.size / 1024 / 1024).toFixed(1)} MB</span>
                          <button onClick={() => setArchivosInc(prev => prev.filter((_, j) => j !== i))}
                            className="text-red-400 hover:text-red-600"><X size={12} /></button>
                        </div>
                        <input value={a.desc} onChange={e => setArchivosInc(prev => prev.map((item, j) => j === i ? { ...item, desc: e.target.value } : item))}
                          placeholder="Descripción del documento (opcional)"
                          className="mt-1.5 w-full text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-usco-vinotinto/30" />
                      </div>
                    ))}
                    <label className="flex items-center gap-1 text-xs text-gray-400 cursor-pointer hover:text-usco-vinotinto">
                      <Plus size={11} /> Agregar otro
                      <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                        onChange={e => {
                          const f = e.target.files?.[0];
                          if (f) setArchivosInc(prev => [...prev, { file: f, tipo: 'incremento', desc: '' }]);
                          e.target.value = '';
                        }} />
                    </label>
                  </div>
                )}
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button onClick={() => { setModalIncremento(false); setArchivosInc([]); }}
                className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Cancelar</button>
              <button onClick={ejecutarIncremento}
                disabled={accionando || !incrementoMonto || parseFloat(incrementoMonto) <= presupuesto.monto_total_asignado}
                className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
                {accionando ? <Loader2 size={13} className="animate-spin" /> : <ArrowUpCircle size={13} />}
                {accionando ? 'Enviando...' : `Enviar${archivosInc.length > 0 ? ` + ${archivosInc.length} doc.` : ''}`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de decisión (gastos) */}
      {decisionModal && modalCfg && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-base font-bold text-gray-800 mb-4">{modalCfg.titulo}</h3>
            <div className="mb-3 bg-gray-50 rounded-lg px-4 py-3">
              <p className="text-xs text-gray-500">Período: <span className="font-bold text-gray-800">{decisionModal.periodo}</span></p>
              <p className="text-xs text-gray-500 mt-0.5">Monto establecido: <span className="font-bold text-gray-800">{formatCOP(p.monto_total_asignado)}</span></p>
              {decisionModal.tipo === 'modificacion' && (
                <p className="text-xs text-amber-700 mt-1 font-medium">El Jefe de Programa será notificado para que corrija el monto.</p>
              )}
            </div>
            <div className="mb-5">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Observaciones</label>
              <textarea value={obsInput} onChange={e => setObsInput(e.target.value)} rows={3}
                placeholder="Comentarios para el Jefe de Programa..."
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto resize-none" />
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => { setDecisionModal(null); setObsInput(''); }}
                className="px-4 py-2 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
              <button onClick={ejecutarDecision} disabled={accionando}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white rounded-lg transition-colors ${modalCfg.btnColor} disabled:opacity-60`}>
                {accionando ? <Loader2 size={14} className="animate-spin" /> : modalCfg.icon}
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Flash */}
      {flash && (
        <div className={`flex items-center gap-3 rounded-xl px-5 py-3 text-sm font-semibold ${
          flash.tipo === 'ok' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {flash.tipo === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {flash.texto}
        </div>
      )}

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-bold text-gray-800">Control Presupuestal</h1>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${estadoBadge.color}`}>
              {estadoBadge.label}
            </span>
          </div>
          <p className="text-sm text-gray-500">RF-PRA-06 · Período Académico {p.periodo_academico}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {p.observaciones_admin && (
            <button
              onClick={() => { setObsVisible(true); setObsModalOpen(true); }}
              className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-300 hover:bg-amber-100 px-3 py-2 rounded-lg transition-colors">
              <MessageSquare size={13} /> Nota de Gastos
            </button>
          )}
          {todos.length > 1 && (
            <div className="relative">
              <select value={periodoSel} onChange={e => cambiarPeriodo(e.target.value)}
                className="appearance-none pl-3 pr-8 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white font-medium">
                {todos.map(t => (
                  <option key={t.periodo_academico} value={t.periodo_academico}>{t.periodo_academico}</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            </div>
          )}
          {/* Jefe: solicitar si está en borrador o requiere modificación */}
          {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && (
            <button onClick={abrirModalNuevo}
              className="flex items-center gap-1.5 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-3 py-2 rounded-lg">
              <Plus size={13} /> Nuevo período
            </button>
          )}
          {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && p.estado === 'aprobado' && (
            <button onClick={() => setModalIncremento(true)}
              className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 border border-amber-300 hover:bg-amber-50 px-3 py-2 rounded-lg">
              <ArrowUpCircle size={13} /> Pedir más recursos
            </button>
          )}
          {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && ['borrador', 'modificacion', 'rechazado'].includes(p.estado ?? '') && (
            <button onClick={() => { setArchivosSol([]); setModalSolicitar(true); }} disabled={accionando}
              className="flex items-center gap-2 text-xs font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 px-3 py-2 rounded-lg transition-colors disabled:opacity-60">
              <Send size={13} /> Enviar solicitud a Gastos
            </button>
          )}
          {/* Gastos: aprobar / rechazar / pedir modificación si está solicitado */}
          {user?.rol === 'admin' && p.estado === 'solicitado' && (
            <>
              <button onClick={() => setDecisionModal({ tipo: 'aprobar', periodo: p.periodo_academico })}
                className="flex items-center gap-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 px-3 py-2 rounded-lg">
                <CheckCircle size={13} /> Aprobar
              </button>
              <button onClick={() => setDecisionModal({ tipo: 'modificacion', periodo: p.periodo_academico })}
                className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-3 py-2 rounded-lg">
                <RefreshCw size={13} /> Pedir ajuste
              </button>
              <button onClick={() => setDecisionModal({ tipo: 'rechazar', periodo: p.periodo_academico })}
                className="flex items-center gap-1.5 text-xs font-semibold text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 px-3 py-2 rounded-lg">
                <X size={13} /> Rechazar
              </button>
            </>
          )}
          {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && (
            <Link to="/configuracion"
              className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 hover:text-usco-vinotinto border border-gray-200 px-3 py-2 rounded-lg transition-colors">
              <Settings size={13} /> Configurar
            </Link>
          )}
        </div>
      </div>

      {/* Banner: incremento pendiente de aprobación */}
      {p.monto_solicitado && p.estado === 'solicitado' && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-300 text-amber-800 rounded-xl px-5 py-4">
          <ArrowUpCircle size={20} className="shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold">Incremento pendiente de aprobación</p>
            <p className="text-xs mt-0.5">
              Monto actual aprobado: <strong>{formatCOP(p.monto_total_asignado)}</strong>
              {' · '}Nuevo monto solicitado: <strong className="text-amber-900">{formatCOP(p.monto_solicitado)}</strong>
              {' · '}Incremento: <strong>+{formatCOP(p.monto_solicitado - p.monto_total_asignado)}</strong>
            </p>
            <p className="text-xs mt-1 opacity-75">El dashboard sigue mostrando el monto aprobado hasta que Gastos lo confirme.</p>
          </div>
        </div>
      )}

      {alertaPct && p.estado === 'aprobado' && (
        <div className="flex items-center gap-3 bg-red-50 border border-red-200 text-red-700 rounded-xl px-5 py-4">
          <AlertCircle size={20} className="shrink-0" />
          <div>
            <p className="text-sm font-semibold">
              ⚠️ Presupuesto ejecutado en un {p.porcentaje_ejecutado.toFixed(1)}%.
            </p>
            {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && (
              <p className="text-xs mt-0.5">
                Considera solicitar más recursos con el botón <strong>"Pedir más recursos"</strong>.
              </p>
            )}
          </div>
        </div>
      )}

      {/* Observaciones del Administrador — tarjeta en contenido principal */}
      {p.observaciones_admin && obsVisible && (
        <div className="bg-white rounded-xl border-l-4 border-amber-400 shadow-sm px-5 py-4 flex items-start gap-4">
          <div className="bg-amber-50 rounded-xl p-2.5 shrink-0">
            <MessageSquare size={18} className="text-amber-600" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <p className="text-sm font-bold text-gray-800">Nota del Administrador</p>
              <span className="text-[10px] font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full uppercase tracking-wide">
                {p.estado === 'modificacion' ? 'Corrección solicitada' : p.estado === 'rechazado' ? 'Solicitud rechazada' : 'Observación'}
              </span>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed">{p.observaciones_admin}</p>
          </div>
          <button
            onClick={() => setObsVisible(false)}
            className="text-gray-300 hover:text-gray-500 transition-colors shrink-0 mt-0.5"
            title="Ocultar (disponible en botón 'Nota de Gastos')">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Modal de observación completa */}
      {obsModalOpen && p.observaciones_admin && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="bg-amber-100 rounded-xl p-2">
                  <MessageSquare size={16} className="text-amber-600" />
                </div>
                <h3 className="text-base font-bold text-gray-800">Nota del Administrador</h3>
              </div>
              <button onClick={() => setObsModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-4 mb-4">
              <p className="text-sm text-gray-700 leading-relaxed">{p.observaciones_admin}</p>
            </div>
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-400">Período: <span className="font-semibold text-gray-600">{p.periodo_academico}</span></p>
              <button
                onClick={() => { setObsVisible(true); setObsModalOpen(false); }}
                className="text-xs font-semibold text-usco-vinotinto hover:underline">
                Mostrar en pantalla
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Guía de flujo para el jefe */}
      {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm px-5 py-4">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">Flujo de gestión presupuestal</p>
          <div className="flex items-center gap-1 flex-wrap">
            {[
              { estado: 'borrador',     label: '1. Borrador',        desc: 'Estableces el monto',     color: 'bg-gray-100 text-gray-600'   },
              { estado: 'solicitado',   label: '2. Solicitado',      desc: 'Enviado a Gastos',         color: 'bg-blue-100 text-blue-700'   },
              { estado: 'modificacion', label: '3. Corrección',      desc: 'Gastos pide ajuste',       color: 'bg-amber-100 text-amber-700' },
              { estado: 'aprobado',     label: '4. Aprobado ✓',      desc: 'Listo para ejecutar',      color: 'bg-emerald-100 text-emerald-700' },
            ].map((step, i, arr) => (
              <div key={step.estado} className="flex items-center gap-1">
                <div className={`rounded-lg px-3 py-1.5 transition-all ${
                  p.estado === step.estado
                    ? `${step.color} ring-2 ring-offset-1 ring-usco-vinotinto/40 font-bold`
                    : 'bg-gray-50 text-gray-400'
                }`}>
                  <p className="text-xs font-semibold">{step.label}</p>
                  <p className="text-[10px] opacity-70">{step.desc}</p>
                </div>
                {i < arr.length - 1 && <span className="text-gray-300 text-lg">›</span>}
              </div>
            ))}
            {p.estado === 'rechazado' && (
              <>
                <span className="text-gray-300 text-lg">›</span>
                <div className="rounded-lg px-3 py-1.5 bg-red-100 text-red-700 ring-2 ring-offset-1 ring-red-300/50">
                  <p className="text-xs font-bold">Rechazado</p>
                  <p className="text-[10px] opacity-70">Ajusta y re-envía</p>
                </div>
              </>
            )}
          </div>
          {p.estado === 'borrador' && (
            <p className="text-xs text-gray-400 mt-2">
              👉 Ajusta el monto en <strong>Configuración</strong> y luego usa <strong>"Enviar solicitud a Gastos"</strong>.
            </p>
          )}
          {p.estado === 'aprobado' && (
            <p className="text-xs text-gray-400 mt-2">
              ✅ Presupuesto activo. Si necesitas más fondos, usa <strong>"Pedir más recursos"</strong>. Para el próximo semestre, usa <strong>"Nuevo período"</strong>.
            </p>
          )}
          {p.estado === 'modificacion' && (
            <p className="text-xs text-amber-600 mt-2 font-medium">
              🔄 Gastos solicita una corrección. Edita el presupuesto en Configuración y vuelve a enviarlo.
            </p>
          )}
          {p.estado === 'rechazado' && (
            <p className="text-xs text-red-600 mt-2 font-medium">
              ❌ Solicitud rechazada. Revisa las observaciones, ajusta el monto y re-envía la solicitud.
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {[
          { label: 'Total Asignado', value: p.monto_total_asignado, icon: <DollarSign size={22} />, color: 'bg-usco-vinotinto' },
          { label: 'Ejecutado', value: p.monto_ejecutado, icon: <TrendingDown size={22} />, color: 'bg-red-500' },
          { label: 'Comprometido', value: p.monto_comprometido, icon: <TrendingUp size={22} />, color: 'bg-amber-500' },
          { label: 'Disponible', value: p.monto_disponible, icon: <DollarSign size={22} />, color: p.monto_disponible > 0 ? 'bg-emerald-600' : 'bg-gray-400' },
        ].map(item => (
          <div key={item.label} className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
            <div className={`${item.color} text-white rounded-xl p-3 shrink-0`}>{item.icon}</div>
            <div className="min-w-0">
              <p className="text-xs text-gray-400 mb-0.5">{item.label}</p>
              <p className="text-base font-bold text-gray-800 truncate">{formatCOP(item.value)}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-5">
            Distribución del Presupuesto — {p.periodo_academico}
          </h2>

          <div className="space-y-5 mb-6">
            <BarraProgreso
              label="Ejecutado"
              value={p.monto_ejecutado}
              max={p.monto_total_asignado}
              color="bg-red-500"
            />
            <BarraProgreso
              label="Comprometido"
              value={p.monto_comprometido}
              max={p.monto_total_asignado}
              color="bg-amber-400"
            />
            <BarraProgreso
              label="Disponible"
              value={Math.max(0, p.monto_disponible)}
              max={p.monto_total_asignado}
              color="bg-emerald-500"
            />
          </div>

          <div className="relative h-8 w-full bg-gray-100 rounded-full overflow-hidden">
            <div
              className="absolute left-0 h-full bg-red-500 transition-all"
              style={{ width: `${Math.min(100, (p.monto_ejecutado / p.monto_total_asignado) * 100)}%` }}
            />
            <div
              className="absolute h-full bg-amber-400 transition-all"
              style={{
                left: `${Math.min(100, (p.monto_ejecutado / p.monto_total_asignado) * 100)}%`,
                width: `${Math.min(100, (p.monto_comprometido / p.monto_total_asignado) * 100)}%`,
              }}
            />
          </div>
          <div className="flex justify-between text-xs text-gray-400 mt-1.5">
            <span>$0</span>
            <span>{formatCOP(p.monto_total_asignado)}</span>
          </div>

          <div className="flex flex-wrap gap-4 mt-5 text-xs">
            {[
              { color: 'bg-red-500', label: 'Ejecutado' },
              { color: 'bg-amber-400', label: 'Comprometido' },
              { color: 'bg-emerald-500', label: 'Disponible' },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 rounded-sm ${item.color}`} />
                <span className="text-gray-500">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-base font-semibold text-gray-700 mb-4">Movimientos Recientes</h2>
          {movimientos.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">Sin movimientos registrados</p>
          ) : (
            <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
              {movimientos.map(m => (
                <div key={m.id} className="flex items-start justify-between gap-3 border-b border-gray-50 pb-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 truncate">{m.concepto}</p>
                    <p className="text-xs text-gray-400">
                      {m.tipo.charAt(0).toUpperCase() + m.tipo.slice(1)} ·{' '}
                      {m.fecha ? new Date(m.fecha).toLocaleDateString('es-CO') : '—'}
                    </p>
                  </div>
                  <p className={`text-sm font-bold shrink-0 ${tipoColor[m.tipo] ?? 'text-gray-700'}`}>
                    {m.tipo === 'ejecucion' ? '-' : '+'}{formatCOP(m.monto)}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─── Documentos de soporte ──────────────────────────────────── */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Paperclip size={16} className="text-usco-vinotinto" />
            <h2 className="text-base font-semibold text-gray-700">Documentos de soporte</h2>
            {docs.length > 0 && (
              <span className="text-xs font-bold bg-usco-vinotinto/10 text-usco-vinotinto rounded-full px-2 py-0.5">{docs.length}</span>
            )}
          </div>
          {user?.rol === 'admin' && docs.length > 0 && (
            <p className="text-xs text-gray-400">Solo lectura — revisa los documentos antes de decidir</p>
          )}
        </div>

        {/* Upload — solo jefe */}
        {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && (
          <div className="bg-gray-50 rounded-xl p-4 mb-4 border border-dashed border-gray-200">
            <p className="text-xs font-semibold text-gray-600 mb-3">Adjuntar documento de soporte</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] text-gray-500 block mb-1">Tipo</label>
                <select value={uploadTipo} onChange={e => setUploadTipo(e.target.value)}
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30">
                  <option value="solicitud">Solicitud de presupuesto</option>
                  <option value="incremento">Justificación de incremento</option>
                  <option value="modificacion">Documento de modificación</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] text-gray-500 block mb-1">Descripción (opcional)</label>
                <input value={uploadDesc} onChange={e => setUploadDesc(e.target.value)}
                  placeholder="Ej: Certificado de necesidad"
                  className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
              </div>
              <div>
                <label className="text-[11px] text-gray-500 block mb-1">Archivo (PDF, Word, Excel, imagen)</label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <span className={`flex-1 text-sm border rounded-lg px-3 py-2 truncate ${
                    uploadFile ? 'border-usco-vinotinto/40 text-gray-800 bg-white' : 'border-gray-200 text-gray-400 bg-white'
                  }`}>
                    {uploadFile ? uploadFile.name : 'Seleccionar archivo…'}
                  </span>
                  <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.docx,.xlsx"
                    onChange={e => setUploadFile(e.target.files?.[0] ?? null)} />
                </label>
              </div>
            </div>
            <div className="flex justify-end mt-3">
              <button onClick={subirDoc} disabled={!uploadFile || uploading}
                className="flex items-center gap-2 text-sm font-semibold bg-usco-vinotinto text-white px-4 py-2 rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-50">
                {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
                Subir documento
              </button>
            </div>
          </div>
        )}

        {/* Lista de documentos */}
        {loadingDocs ? (
          <div className="flex justify-center py-6"><Loader2 size={20} className="animate-spin text-usco-vinotinto" /></div>
        ) : docs.length === 0 ? (
          <div className="flex flex-col items-center py-8 gap-2 text-gray-400">
            <FileText size={32} className="opacity-30" />
            <p className="text-sm">
              {(user?.rol === 'jefe_programa' || user?.rol === 'decano')
                ? 'Sube los documentos que justifiquen la solicitud o el incremento.'
                : 'El Jefe de Programa no ha adjuntado documentos aún.'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {docs.map(doc => {
              const tipoLabel: Record<string, string> = { solicitud: 'Solicitud', incremento: 'Incremento', modificacion: 'Modificación' };
              const tipoBg: Record<string, string> = { solicitud: 'bg-blue-50 text-blue-700', incremento: 'bg-amber-50 text-amber-700', modificacion: 'bg-violet-50 text-violet-700' };
              return (
                <div key={doc.id} className="flex items-center gap-3 bg-gray-50 border border-gray-100 rounded-xl px-4 py-3">
                  <FileText size={18} className="text-usco-vinotinto shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-medium text-gray-800 truncate">{doc.nombre_original}</p>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${tipoBg[doc.tipo_solicitud] ?? 'bg-gray-100 text-gray-600'}`}>
                        {tipoLabel[doc.tipo_solicitud] ?? doc.tipo_solicitud}
                      </span>
                    </div>
                    {doc.descripcion && <p className="text-xs text-gray-500 mt-0.5">{doc.descripcion}</p>}
                    <p className="text-[11px] text-gray-400 mt-0.5">
                      Por {doc.subido_por} · {doc.created_at ? new Date(doc.created_at).toLocaleDateString('es-CO') : ''}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => downloadAuthenticated(presupuestoService.getDownloadUrl(doc.id), doc.nombre_original)}
                      className="flex items-center gap-1 text-xs font-semibold text-usco-vinotinto hover:underline px-2 py-1.5 rounded-lg hover:bg-usco-vinotinto/5">
                      <Eye size={13} /> Ver
                    </button>
                    <button
                      onClick={() => downloadAuthenticated(presupuestoService.getDownloadUrl(doc.id), doc.nombre_original)}
                      className="flex items-center gap-1 text-xs font-semibold text-gray-500 hover:text-gray-700 px-2 py-1.5 rounded-lg hover:bg-gray-100">
                      <Download size={13} /> Descargar
                    </button>
                    {(user?.rol === 'jefe_programa' || user?.rol === 'decano') && p.estado !== 'aprobado' && (
                      <button onClick={() => eliminarDoc(doc.id)} disabled={deletingDocId === doc.id}
                        className="flex items-center gap-1 text-xs font-semibold text-red-500 hover:text-red-700 px-2 py-1.5 rounded-lg hover:bg-red-50 disabled:opacity-50">
                        {deletingDocId === doc.id ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {user?.rol === 'admin' && docs.length === 0 && p.estado === 'solicitado' && (
          <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2">
            <p className="text-xs text-amber-700 font-medium">⚠️ El Jefe no ha adjuntado documentos de soporte. Considera solicitar modificación antes de aprobar.</p>
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-base font-semibold text-gray-700 mb-4">Resumen Ejecutivo</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
          {[
            { label: 'Total Asignado', val: formatCOP(p.monto_total_asignado) },
            { label: '% Ejecutado', val: `${p.porcentaje_ejecutado.toFixed(1)}%` },
            { label: 'Disponible Real', val: formatCOP(Math.max(0, p.monto_disponible)) },
            { label: 'Período', val: p.periodo_academico },
          ].map(item => (
            <div key={item.label} className="bg-gray-50 rounded-lg p-3">
              <p className="text-xs text-gray-400 mb-1">{item.label}</p>
              <p className="font-bold text-gray-800">{item.val}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
