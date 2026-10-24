import { useState, useEffect, useCallback } from 'react';
import { Clock, Plus, CheckCircle, Loader2, AlertCircle, BookOpen, Download, Star, DollarSign } from 'lucide-react';
import { monitorService, convocatoriasService, evaluacionMonitorService, exportarService, downloadBlob } from '../services/api';
import { useAuthContext } from '../context/AuthContext';

interface HoraItem {
  id: number;
  semana: number;
  horas: number;
  descripcion?: string;
  aprobado: boolean;
}

interface MonitorData {
  postulacion: { id: number; convocatoria: string; asignatura: string } | null;
  horas: HoraItem[];
  total_horas: number;
}

interface MonitorProfesor {
  postulacion_id: number;
  estudiante: string;
  codigo: string;
  total_horas: number;
  horas: HoraItem[];
}

// ── Estímulo económico monitor USCO (Acuerdo 003-2017) ──────────────────────
// 1 SMMLV/mes ÷ 160 h/mes = tarifa hora
const SMMLV_2026 = 1_423_500;                            // COP/mes vigente 2026
const HORAS_MES   = 160;                                  // h/mes jornada parcial
const TARIFA_HORA = Math.round(SMMLV_2026 / HORAS_MES);  // ≈ $8 897/h
const fmtCOP = (v: number) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v);

export function MonitorHoras() {
  const { user } = useAuthContext();
  const [data, setData] = useState<MonitorData | null>(null);
  const [dataProf, setDataProf] = useState<MonitorProfesor[]>([]);
  const [convSel, setConvSel] = useState<number | null>(null);
  const [convs, setConvs] = useState<{ id: number; titulo: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [flash, setFlash] = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);
  const [form, setForm] = useState({ semana: '', horas: '', descripcion: '' });
  const [saving, setSaving] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [evalModal, setEvalModal] = useState<number | null>(null);
  const [evalForm, setEvalForm] = useState({ nota_desempeno: '', puntualidad: '', calidad_academica: '', observaciones: '' });
  const [savingEval, setSavingEval] = useState(false);
  const [exportandoHoras, setExportandoHoras] = useState(false);
  const [corrigiendo, setCorrigiendo] = useState<{ id: number; horas: string; descripcion: string } | null>(null);
  const [savingCorrec, setSavingCorrec] = useState(false);

  const showFlash = (tipo: 'ok' | 'err', texto: string) => {
    setFlash({ tipo, texto });
    setTimeout(() => setFlash(null), 4000);
  };

  const cargarEstudiante = useCallback(async () => {
    setLoading(true);
    try {
      const r = await monitorService.misHoras();
      setData(r.data);
    } catch { setData(null); }
    finally { setLoading(false); }
  }, []);

  const cargarProfesor = useCallback(async (convId: number) => {
    setLoading(true);
    try {
      const r = await monitorService.horasPorConvocatoria(convId);
      setDataProf(r.data);
    } catch { setDataProf([]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    if (user?.rol === 'estudiante') {
      cargarEstudiante();
    } else if (user?.rol === 'profesor' || user?.rol === 'jefe_programa' || user?.rol === 'decano') {
      convocatoriasService.getAll().then(r => {
        const lista = r.data.map((c: { id: number; titulo: string }) => ({ id: c.id, titulo: c.titulo }));
        setConvs(lista);
        if (lista.length > 0) {
          setConvSel(lista[0].id);
          cargarProfesor(lista[0].id);
        } else { setLoading(false); }
      }).catch(() => setLoading(false));
    }
  }, [user, cargarEstudiante, cargarProfesor]);

  async function registrarHoras(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await monitorService.registrarHoras({
        semana: parseInt(form.semana),
        horas: parseFloat(form.horas),
        descripcion: form.descripcion || undefined,
      });
      setForm({ semana: '', horas: '', descripcion: '' });
      setShowForm(false);
      showFlash('ok', 'Horas registradas correctamente.');
      cargarEstudiante();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al registrar horas.');
    } finally { setSaving(false); }
  }

  async function exportarHorasCsv() {
    if (!convSel) return;
    setExportandoHoras(true);
    try {
      const r = await exportarService.horasMonitorCsv(convSel);
      downloadBlob(r.data, `horas_monitor_conv${convSel}_${new Date().toISOString().slice(0,10)}.csv`);
    } catch { /* silencioso */ }
    finally { setExportandoHoras(false); }
  }

  async function guardarEvaluacion(postId: number) {
    if (!evalForm.nota_desempeno) { showFlash('err', 'La nota de desempeño es obligatoria.'); return; }
    setSavingEval(true);
    try {
      await evaluacionMonitorService.crear(postId, {
        nota_desempeno: parseFloat(evalForm.nota_desempeno),
        puntualidad: evalForm.puntualidad ? parseFloat(evalForm.puntualidad) : undefined,
        calidad_academica: evalForm.calidad_academica ? parseFloat(evalForm.calidad_academica) : undefined,
        observaciones: evalForm.observaciones || undefined,
      });
      showFlash('ok', 'Evaluación guardada correctamente.');
      setEvalModal(null);
      setEvalForm({ nota_desempeno: '', puntualidad: '', calidad_academica: '', observaciones: '' });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al guardar la evaluación.');
    } finally { setSavingEval(false); }
  }

  async function aprobarHoras(horaId: number) {
    try {
      await monitorService.aprobarHoras(horaId);
      if (convSel) cargarProfesor(convSel);
      showFlash('ok', 'Horas aprobadas.');
    } catch {
      showFlash('err', 'Error al aprobar horas.');
    }
  }

  async function guardarCorreccion() {
    if (!corrigiendo) return;
    setSavingCorrec(true);
    try {
      await monitorService.corregirHoras(corrigiendo.id, {
        horas: parseFloat(corrigiendo.horas) || undefined,
        descripcion: corrigiendo.descripcion || undefined,
      });
      setCorrigiendo(null);
      if (convSel) cargarProfesor(convSel);
      showFlash('ok', 'Horas corregidas.');
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al corregir horas.');
    } finally { setSavingCorrec(false); }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 size={26} className="animate-spin text-usco-vinotinto" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {flash && (
        <div className={`flex items-center gap-3 rounded-xl px-5 py-3 text-sm font-semibold ${
          flash.tipo === 'ok' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {flash.tipo === 'ok' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {flash.texto}
        </div>
      )}

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Clock size={20} className="text-usco-vinotinto" /> Seguimiento de Horas — Monitor
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {user?.rol === 'estudiante'
              ? 'Registra tus horas de monitoría por semana.'
              : 'Revisa y aprueba las horas de tus monitores.'}
          </p>
        </div>
        {user?.rol === 'estudiante' && data?.postulacion && (
          <button onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 text-sm font-semibold bg-usco-vinotinto text-white px-4 py-2 rounded-lg hover:bg-usco-vinotinto/90">
            <Plus size={15} /> Registrar horas
          </button>
        )}
      </div>

      {/* Vista estudiante */}
      {user?.rol === 'estudiante' && (
        <>
          {!data?.postulacion ? (
            <div className="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400">
              <BookOpen size={40} className="mx-auto mb-3 opacity-40" />
              <p className="font-medium">No eres monitor seleccionado en ninguna convocatoria activa.</p>
              <p className="text-sm mt-1">Cuando seas seleccionado, podrás registrar tus horas aquí.</p>
            </div>
          ) : (
            <>
              {/* Info convocatoria */}
              <div className="bg-white rounded-xl border border-gray-100 p-5">
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <div>
                    <p className="text-sm font-bold text-gray-800">{data.postulacion.convocatoria}</p>
                    <p className="text-xs text-gray-500">{data.postulacion.asignatura}</p>
                  </div>
                  <div className="flex gap-5 text-right">
                    <div>
                      <p className="text-2xl font-bold text-usco-vinotinto">{data.total_horas.toFixed(1)}h</p>
                      <p className="text-xs text-gray-400">Total registradas</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-emerald-600">
                        {fmtCOP(data.horas.filter(h => h.aprobado).reduce((s, h) => s + h.horas, 0) * TARIFA_HORA)}
                      </p>
                      <p className="text-xs text-gray-400">Estímulo acumulado</p>
                    </div>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-2 text-xs text-gray-400">
                  <DollarSign size={12} className="text-emerald-500 shrink-0" />
                  <span>Tarifa: <span className="font-semibold text-gray-600">{fmtCOP(TARIFA_HORA)}/h</span> · Base SMMLV 2026 ({fmtCOP(SMMLV_2026)}/mes ÷ {HORAS_MES} h) · Solo horas aprobadas generan estímulo.</span>
                </div>
              </div>

              {/* Formulario registrar horas */}
              {showForm && (
                <form onSubmit={registrarHoras} className="bg-white rounded-xl border border-gray-100 p-5 space-y-4">
                  <h3 className="text-sm font-bold text-gray-700">Nuevo registro de horas</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">Semana (1-18)</label>
                      <input required type="number" min="1" max="18" value={form.semana}
                        onChange={e => setForm(p => ({ ...p, semana: e.target.value }))}
                        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-gray-600 mb-1">Horas</label>
                      <input required type="number" min="0.5" step="0.5" max="40" value={form.horas}
                        onChange={e => setForm(p => ({ ...p, horas: e.target.value }))}
                        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gray-600 mb-1">Descripción de actividades</label>
                    <input value={form.descripcion} onChange={e => setForm(p => ({ ...p, descripcion: e.target.value }))}
                      placeholder="Ej: Tutoría grupal álgebra lineal, 2h. Revisión de talleres, 1h."
                      className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30" />
                  </div>
                  <div className="flex gap-3 justify-end">
                    <button type="button" onClick={() => setShowForm(false)}
                      className="px-4 py-2 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                      Cancelar
                    </button>
                    <button type="submit" disabled={saving}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg disabled:opacity-60">
                      {saving ? <Loader2 size={13} className="animate-spin" /> : <CheckCircle size={13} />}
                      Guardar
                    </button>
                  </div>
                </form>
              )}

              {/* Tabla de horas */}
              <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
                <div className="px-5 py-4 border-b border-gray-100">
                  <h3 className="font-bold text-sm text-gray-700">Historial de horas registradas</h3>
                </div>
                {data.horas.length === 0 ? (
                  <div className="text-center py-8 text-sm text-gray-400">Sin registros aún</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                        <th className="px-5 py-3 text-left">Semana</th>
                        <th className="px-5 py-3 text-right">Horas</th>
                        <th className="px-5 py-3 text-left">Descripción</th>
                        <th className="px-5 py-3 text-center">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {data.horas.map(h => (
                        <tr key={h.id} className="hover:bg-gray-50/50">
                          <td className="px-5 py-3 font-semibold text-gray-800">Sem. {h.semana}</td>
                          <td className="px-5 py-3 text-right font-bold text-usco-vinotinto">{h.horas}h</td>
                          <td className="px-5 py-3 text-gray-500 text-xs">{h.descripcion || '—'}</td>
                          <td className="px-5 py-3 text-center">
                            {h.aprobado
                              ? <span className="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Aprobado</span>
                              : <span className="text-xs font-semibold bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">Pendiente</span>
                            }
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-gray-50 font-bold text-sm">
                        <td className="px-5 py-3">Total</td>
                        <td className="px-5 py-3 text-right text-usco-vinotinto">{data.total_horas.toFixed(1)}h</td>
                        <td className="px-5 py-3 text-right text-emerald-600 text-xs font-semibold" colSpan={2}>
                          {fmtCOP(data.horas.filter(h => h.aprobado).reduce((s, h) => s + h.horas, 0) * TARIFA_HORA)}
                          <span className="text-gray-400 font-normal ml-1">(horas aprobadas)</span>
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                )}
              </div>
            </>
          )}
        </>
      )}

      {/* Vista profesor / jefe */}
      {(user?.rol === 'profesor' || user?.rol === 'jefe_programa' || user?.rol === 'decano') && (
        <>
          {convs.length > 0 && (
            <div className="flex items-center gap-3 flex-wrap">
              <label className="text-sm font-semibold text-gray-600 shrink-0">Convocatoria:</label>
              <select
                value={convSel ?? ''}
                onChange={e => { const id = parseInt(e.target.value); setConvSel(id); cargarProfesor(id); }}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 bg-white">
                {convs.map(c => <option key={c.id} value={c.id}>{c.titulo}</option>)}
              </select>
              <button onClick={exportarHorasCsv} disabled={exportandoHoras || !convSel}
                className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 border border-emerald-300 hover:bg-emerald-50 px-3 py-1.5 rounded-lg ml-auto disabled:opacity-50">
                {exportandoHoras ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />} Exportar CSV
              </button>
            </div>
          )}

          {dataProf.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-100 p-8 text-center text-gray-400">
              <Clock size={40} className="mx-auto mb-3 opacity-40" />
              <p>No hay monitores seleccionados con registros de horas en esta convocatoria.</p>
            </div>
          ) : dataProf.map(monitor => (
            <div key={monitor.postulacion_id} className="bg-white rounded-xl border border-gray-100 overflow-hidden">
              <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
                <div>
                  <p className="font-bold text-gray-800 text-sm">{monitor.estudiante}</p>
                  <p className="text-xs text-gray-400 font-mono">{monitor.codigo}</p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-lg font-bold text-usco-vinotinto">{monitor.total_horas.toFixed(1)}h</p>
                    <p className="text-xs font-semibold text-emerald-600 flex items-center gap-0.5 justify-end">
                      <DollarSign size={11} />
                      {fmtCOP(monitor.horas.filter(h => h.aprobado).reduce((s, h) => s + h.horas, 0) * TARIFA_HORA)}
                    </p>
                    <p className="text-[10px] text-gray-400">{fmtCOP(TARIFA_HORA)}/h · SMMLV 2026</p>
                  </div>
                  <button onClick={() => { setEvalModal(monitor.postulacion_id); setEvalForm({ nota_desempeno: '', puntualidad: '', calidad_academica: '', observaciones: '' }); }}
                    className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 border border-indigo-300 hover:bg-indigo-50 px-2.5 py-1.5 rounded-lg">
                    <Star size={11} /> Evaluar
                  </button>
                </div>
              </div>
              {monitor.horas.length === 0 ? (
                <div className="text-center py-4 text-sm text-gray-400">Sin registros</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      <th className="px-5 py-2 text-left">Semana</th>
                      <th className="px-5 py-2 text-right">Horas</th>
                      <th className="px-5 py-2 text-left">Descripción</th>
                      <th className="px-5 py-2 text-center">Estado</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {monitor.horas.map(h => (
                      corrigiendo?.id === h.id ? (
                        <tr key={h.id} className="bg-amber-50">
                          <td className="px-5 py-2 font-semibold text-gray-600">Sem. {h.semana}</td>
                          <td className="px-3 py-1.5">
                            <input type="number" min="0.5" step="0.5" max="40"
                              value={corrigiendo.horas}
                              onChange={e => setCorrigiendo(p => p ? { ...p, horas: e.target.value } : p)}
                              className="w-20 px-2 py-1 text-sm border border-amber-300 rounded focus:outline-none focus:ring-1 focus:ring-amber-400" />
                          </td>
                          <td className="px-3 py-1.5" colSpan={1}>
                            <input type="text"
                              value={corrigiendo.descripcion}
                              onChange={e => setCorrigiendo(p => p ? { ...p, descripcion: e.target.value } : p)}
                              className="w-full px-2 py-1 text-sm border border-amber-300 rounded focus:outline-none focus:ring-1 focus:ring-amber-400" />
                          </td>
                          <td className="px-3 py-1.5 text-center">
                            <div className="flex items-center gap-1.5 justify-center">
                              <button onClick={guardarCorreccion} disabled={savingCorrec}
                                className="text-xs font-semibold bg-emerald-600 text-white px-2.5 py-1 rounded-lg hover:bg-emerald-700 disabled:opacity-60">
                                {savingCorrec ? '...' : 'Guardar'}
                              </button>
                              <button onClick={() => setCorrigiendo(null)}
                                className="text-xs font-semibold text-gray-500 border border-gray-200 px-2 py-1 rounded-lg hover:bg-gray-50">✕</button>
                            </div>
                          </td>
                        </tr>
                      ) : (
                        <tr key={h.id} className="hover:bg-gray-50/50">
                          <td className="px-5 py-2 font-semibold">Sem. {h.semana}</td>
                          <td className="px-5 py-2 text-right font-bold text-usco-vinotinto">{h.horas}h</td>
                          <td className="px-5 py-2 text-gray-500 text-xs">{h.descripcion || '—'}</td>
                          <td className="px-5 py-2 text-center">
                            <div className="flex items-center gap-1.5 justify-center">
                              {h.aprobado ? (
                                <span className="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Aprobado</span>
                              ) : (
                                <button onClick={() => aprobarHoras(h.id)}
                                  className="text-xs font-semibold bg-usco-vinotinto text-white px-2.5 py-1 rounded-lg hover:bg-usco-vinotinto/90">
                                  Aprobar
                                </button>
                              )}
                              <button
                                onClick={() => setCorrigiendo({ id: h.id, horas: String(h.horas), descripcion: h.descripcion ?? '' })}
                                className="text-xs font-semibold text-amber-600 border border-amber-200 hover:bg-amber-50 px-2 py-0.5 rounded-lg">
                                Corregir
                              </button>
                            </div>
                          </td>
                        </tr>
                      )
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          ))}
        </>
      )}

      {/* Modal evaluación SF-03 */}
      {evalModal !== null && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h3 className="text-base font-bold text-gray-800 mb-1 flex items-center gap-2">
              <Star size={16} className="text-indigo-500" /> Evaluar desempeño del monitor
            </h3>
            <p className="text-xs text-gray-400 mb-5">Notas de 0.0 a 5.0. La convocatoria debe estar finalizada.</p>
            <div className="space-y-3">
              {[
                { key: 'nota_desempeno', label: 'Nota de desempeño *' },
                { key: 'puntualidad', label: 'Puntualidad' },
                { key: 'calidad_academica', label: 'Calidad académica' },
              ].map(f => (
                <div key={f.key}>
                  <label className="block text-xs font-semibold text-gray-600 mb-1">{f.label}</label>
                  <input type="number" min="0" max="5" step="0.1"
                    value={evalForm[f.key as keyof typeof evalForm]}
                    onChange={e => setEvalForm(p => ({ ...p, [f.key]: e.target.value }))}
                    placeholder="0.0 – 5.0"
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300" />
                </div>
              ))}
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Observaciones</label>
                <textarea rows={2} value={evalForm.observaciones}
                  onChange={e => setEvalForm(p => ({ ...p, observaciones: e.target.value }))}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-300 resize-none" />
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button onClick={() => setEvalModal(null)}
                className="flex-1 border border-gray-300 text-gray-700 font-semibold py-2.5 rounded-lg hover:bg-gray-50 text-sm">
                Cancelar
              </button>
              <button onClick={() => guardarEvaluacion(evalModal)} disabled={savingEval}
                className="flex-1 bg-indigo-600 text-white font-semibold py-2.5 rounded-lg hover:bg-indigo-700 disabled:opacity-60 text-sm flex items-center justify-center gap-2">
                {savingEval ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                Guardar evaluación
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
