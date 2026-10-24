import { useState, useEffect, useCallback } from 'react';
import {
  ClipboardList, ChevronLeft, Star, MessageSquare, CheckCircle,
  XCircle, Clock, AlertTriangle, Loader2, Play, Trophy, X, FileText,
  AlertCircle,
} from 'lucide-react';
import type { Convocatoria, Postulacion, EstadoPostulacion } from '../types';
import { convocatoriasService, postulacionesService, seleccionService, pdfService, downloadBlob } from '../services/api';
import { useAuthContext } from '../context/AuthContext';

// ─── helpers ──────────────────────────────────────────────────────────────────
const estadoBadge: Record<EstadoPostulacion, { label: string; color: string }> = {
  pendiente:               { label: 'Pendiente',      color: 'bg-yellow-100 text-yellow-700' },
  documentos_incompletos:  { label: 'Docs. incompletos', color: 'bg-orange-100 text-orange-700' },
  en_revision:             { label: 'En revisión',    color: 'bg-blue-100 text-blue-700' },
  preseleccionado:         { label: 'Preseleccionado', color: 'bg-indigo-100 text-indigo-700' },
  seleccionado:            { label: '✓ Seleccionado', color: 'bg-emerald-100 text-emerald-700' },
  no_seleccionado:         { label: 'No seleccionado', color: 'bg-red-100 text-red-700' },
  desistido:               { label: 'Desistido',      color: 'bg-gray-100 text-gray-500' },
};

const estadoConvBadge: Record<string, string> = {
  borrador:      'bg-gray-100 text-gray-500',
  abierta:       'bg-emerald-100 text-emerald-700',
  cerrada:       'bg-orange-100 text-orange-700',
  en_evaluacion: 'bg-blue-100 text-blue-700',
  finalizada:    'bg-purple-100 text-purple-700',
};

// ─── Modal de notas ───────────────────────────────────────────────────────────
function ModalNotas({
  post, onClose, onSaved,
}: { post: Postulacion; onClose: () => void; onSaved: (updated: Postulacion) => void }) {
  const [notaAsg, setNotaAsg] = useState(String(post.nota_asignatura ?? ''));
  const [notaEnt, setNotaEnt] = useState(String(post.nota_entrevista ?? ''));
  const [obs, setObs]         = useState('');
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState('');

  const nombre = `${post.estudiante?.nombres ?? ''} ${post.estudiante?.apellidos ?? ''}`.trim();

  async function handleGuardar() {
    setSaving(true); setError('');
    try {
      let updated = post;
      if (notaAsg !== '' && notaAsg !== String(post.nota_asignatura)) {
        const r = await postulacionesService.setNotaAsignatura(post.id, parseFloat(notaAsg));
        updated = r.data;
      }
      if (notaEnt !== '' && notaEnt !== String(post.nota_entrevista)) {
        const r = await postulacionesService.setEntrevista(post.id, parseFloat(notaEnt), obs || undefined);
        updated = r.data;
      }
      onSaved(updated);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg ?? 'Error al guardar las notas');
    } finally { setSaving(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm">
        <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-gray-100">
          <div>
            <h3 className="font-bold text-gray-800 text-sm">Registrar notas</h3>
            <p className="text-xs text-gray-400 mt-0.5">{nombre}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <div className="px-5 py-4 space-y-3">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-xs px-3 py-2 rounded-lg">{error}</div>
          )}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">
              Nota asignatura (0–5)
            </label>
            <input
              type="number" min="0" max="5" step="0.01"
              value={notaAsg}
              onChange={e => setNotaAsg(e.target.value)}
              placeholder="Ej: 4.50"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">
              Nota entrevista (0–5)
            </label>
            <input
              type="number" min="0" max="5" step="0.01"
              value={notaEnt}
              onChange={e => setNotaEnt(e.target.value)}
              placeholder="Ej: 3.80"
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Observaciones</label>
            <textarea
              rows={2} value={obs} onChange={e => setObs(e.target.value)}
              placeholder="Opcional..."
              className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-usco-vinotinto/30 resize-none"
            />
          </div>
          <div className="flex gap-3 pt-1 border-t border-gray-100">
            <button onClick={onClose} className="flex-1 py-2.5 text-sm font-semibold text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
              Cancelar
            </button>
            <button onClick={handleGuardar} disabled={saving}
              className="flex-1 py-2.5 text-sm font-semibold bg-usco-vinotinto text-white rounded-lg hover:bg-usco-vinotinto/90 disabled:opacity-60 flex items-center justify-center gap-2">
              {saving && <Loader2 size={13} className="animate-spin" />}
              Guardar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Vista de postulantes de una convocatoria ─────────────────────────────────
function VistaPostulantes({
  conv, onBack,
}: { conv: Convocatoria; onBack: () => void }) {
  const [postulaciones, setPostulaciones] = useState<Postulacion[]>([]);
  const [loading, setLoading]       = useState(true);
  const [modalPost, setModalPost]   = useState<Postulacion | null>(null);
  const [running, setRunning]       = useState(false);
  const [flash, setFlash]           = useState<{ tipo: 'ok' | 'err'; texto: string } | null>(null);
  const [resultados, setResultados] = useState<unknown[] | null>(null);

  const cargar = useCallback(async () => {
    setLoading(true);
    try {
      const r = await postulacionesService.getPorConvocatoria(conv.id);
      setPostulaciones(r.data);
    } catch { setPostulaciones([]); }
    finally { setLoading(false); }
  }, [conv.id]);

  useEffect(() => { cargar(); }, [cargar]);

  function showFlash(tipo: 'ok' | 'err', texto: string) {
    setFlash({ tipo, texto });
    setTimeout(() => setFlash(null), 5000);
  }

  async function ejecutarSeleccion() {
    setRunning(true);
    try {
      const r = await seleccionService.ejecutarAlgoritmo(conv.id);
      setResultados(r.data.resultados ?? r.data);
      showFlash('ok', 'Selección ejecutada correctamente.');
      cargar();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      showFlash('err', msg ?? 'Error al ejecutar la selección');
    } finally { setRunning(false); }
  }

  const listos = postulaciones.filter(
    p => p.nota_asignatura != null && p.nota_entrevista != null && p.promedio_estudiante != null
  );
  const pctListos = postulaciones.length > 0 ? Math.round((listos.length / postulaciones.length) * 100) : 0;

  return (
    <div className="space-y-4">
      {modalPost && (
        <ModalNotas
          post={modalPost}
          onClose={() => setModalPost(null)}
          onSaved={(updated) => {
            setPostulaciones(prev => prev.map(p => p.id === updated.id ? updated : p));
            setModalPost(null);
          }}
        />
      )}

      {/* Header */}
      <div className="flex items-start gap-3">
        <button onClick={onBack}
          className="flex items-center gap-1.5 text-sm font-semibold text-gray-500 hover:text-usco-vinotinto mt-0.5">
          <ChevronLeft size={16} /> Volver
        </button>
        <div className="flex-1">
          <h2 className="text-lg font-bold text-gray-800 leading-tight">{conv.titulo}</h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {conv.asignatura?.nombre} · {conv.periodo_academico} ·{' '}
            {conv.num_monitores_requeridos} cupo(s)
          </p>
        </div>
        {conv.estado === 'en_evaluacion' && (
          <button onClick={ejecutarSeleccion} disabled={running || listos.length === 0}
            className="flex items-center gap-1.5 text-sm font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 px-4 py-2 rounded-lg disabled:opacity-50 shrink-0">
            {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Ejecutar RF-MON-05
          </button>
        )}
      </div>

      {/* Flash */}
      {flash && (
        <div className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium ${
          flash.tipo === 'ok' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700'
            : 'bg-red-50 border border-red-200 text-red-700'}`}>
          {flash.tipo === 'ok' ? <CheckCircle size={15} /> : <AlertCircle size={15} />}
          {flash.texto}
        </div>
      )}

      {/* Estadísticas */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-gray-100 p-3 text-center">
          <p className="text-xs text-gray-400">Total postulantes</p>
          <p className="text-2xl font-bold text-gray-800">{postulaciones.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-3 text-center">
          <p className="text-xs text-gray-400">Con notas completas</p>
          <p className={`text-2xl font-bold ${listos.length === postulaciones.length && postulaciones.length > 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
            {listos.length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-gray-100 p-3 text-center">
          <p className="text-xs text-gray-400">Progreso evaluación</p>
          <p className={`text-2xl font-bold ${pctListos === 100 ? 'text-emerald-600' : 'text-gray-800'}`}>{pctListos}%</p>
        </div>
      </div>

      {/* Barra progreso */}
      {postulaciones.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 px-4 py-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1.5">
            <span>Postulantes evaluados</span>
            <span className="font-semibold">{listos.length} / {postulaciones.length}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2.5">
            <div className={`h-2.5 rounded-full transition-all ${pctListos === 100 ? 'bg-emerald-500' : 'bg-usco-vinotinto'}`}
              style={{ width: `${pctListos}%` }} />
          </div>
          {listos.length > 0 && listos.length < postulaciones.length && (
            <p className="text-xs text-amber-600 mt-1.5 flex items-center gap-1">
              <AlertTriangle size={12} /> Faltan {postulaciones.length - listos.length} postulante(s) por evaluar
            </p>
          )}
        </div>
      )}

      {/* Resultados de selección */}
      {resultados && Array.isArray(resultados) && resultados.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border-b border-emerald-100">
            <Trophy size={16} className="text-emerald-600" />
            <h3 className="text-sm font-bold text-emerald-700">Resultados de Selección RF-MON-05</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {(resultados as Array<{puesto: number; estudiante_nombre: string; puntaje_final: number; nota_asignatura: number; promedio: number; nota_entrevista: number; estado: string}>).map(r => (
              <div key={r.puesto} className="flex items-center gap-3 px-4 py-3">
                <span className={`w-7 h-7 rounded-full text-xs font-bold flex items-center justify-center shrink-0 ${
                  r.puesto <= conv.num_monitores_requeridos ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'
                }`}>{r.puesto}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-800 truncate">{r.estudiante_nombre}</p>
                  <p className="text-xs text-gray-400">
                    Asig: {r.nota_asignatura.toFixed(2)} · Prom: {r.promedio.toFixed(2)} · Ent: {r.nota_entrevista.toFixed(2)}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-bold text-usco-vinotinto">{r.puntaje_final.toFixed(4)}</p>
                  <span className={`text-xs px-1.5 py-0.5 rounded font-semibold ${
                    r.estado === 'seleccionado' ? 'text-emerald-600' : 'text-gray-400'
                  }`}>{r.estado === 'seleccionado' ? '✓ Monitor' : 'Lista espera'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lista postulantes */}
      {loading ? (
        <div className="flex justify-center py-10">
          <Loader2 size={24} className="animate-spin text-usco-vinotinto" />
        </div>
      ) : postulaciones.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl border border-gray-100 text-gray-400">
          <ClipboardList size={40} className="mx-auto mb-2 opacity-40" />
          <p className="font-medium">Sin postulantes aún</p>
        </div>
      ) : (
        <div className="space-y-3">
          {postulaciones.map(p => {
            const cfg = estadoBadge[p.estado];
            const nombre = `${p.estudiante?.nombres ?? ''} ${p.estudiante?.apellidos ?? ''}`.trim();
            const completo = p.nota_asignatura != null && p.nota_entrevista != null && p.promedio_estudiante != null;
            return (
              <div key={p.id} className="bg-white rounded-xl border border-gray-100 p-4">
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-semibold text-gray-800 text-sm">{nombre}</p>
                      {p.estudiante?.codigo && (
                        <span className="text-xs font-mono text-gray-400">{p.estudiante.codigo}</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Postulado: {new Date(p.fecha_postulacion).toLocaleDateString('es-CO')}
                      {p.documentos_completos && <span className="ml-2 text-emerald-600">· Docs. completos</span>}
                    </p>
                  </div>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${cfg.color}`}>
                    {cfg.label}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                  {[
                    { label: 'Promedio', val: p.promedio_estudiante?.toFixed(2), ok: p.promedio_estudiante != null },
                    { label: 'Nota asig.', val: p.nota_asignatura?.toFixed(2), ok: p.nota_asignatura != null },
                    { label: 'Entrevista', val: p.nota_entrevista?.toFixed(2), ok: p.nota_entrevista != null },
                    { label: 'Puntaje final', val: p.puntaje_final?.toFixed(4), ok: p.puntaje_final != null },
                  ].map(item => (
                    <div key={item.label} className={`rounded-lg p-2.5 text-center ${item.ok ? 'bg-gray-50' : 'bg-amber-50 border border-amber-100'}`}>
                      <p className="text-xs text-gray-400">{item.label}</p>
                      <p className={`text-sm font-bold mt-0.5 ${item.ok ? 'text-gray-800' : 'text-amber-500'}`}>
                        {item.val ?? '—'}
                      </p>
                    </div>
                  ))}
                </div>

                {p.carta_motivacion && (
                  <div className="mb-3 bg-gray-50 rounded-lg px-3 py-2.5">
                    <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1">
                      <FileText size={12} /> Carta de motivación
                    </p>
                    <p className="text-xs text-gray-600 line-clamp-2">{p.carta_motivacion}</p>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {completo ? (
                      <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium">
                        <CheckCircle size={13} /> Evaluación completa
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-amber-600 font-medium">
                        <Clock size={13} /> Pendiente evaluación
                      </span>
                    )}
                  </div>
                  {!['seleccionado', 'no_seleccionado', 'desistido'].includes(p.estado) && (
                    <button onClick={() => setModalPost(p)}
                      className="flex items-center gap-1.5 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-3 py-1.5 rounded-lg transition-colors">
                      <Star size={12} /> {completo ? 'Editar notas' : 'Registrar notas'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Componente principal ─────────────────────────────────────────────────────
export function Evaluaciones() {
  const { user } = useAuthContext();
  const [convocatorias, setConvocatorias] = useState<Convocatoria[]>([]);
  const [loading, setLoading]             = useState(true);
  const [seleccionada, setSeleccionada]   = useState<Convocatoria | null>(null);

  useEffect(() => {
    async function cargar() {
      setLoading(true);
      try {
        const r = await convocatoriasService.getAll();
        const mias = (r.data as Convocatoria[]).filter(c => c.profesor_id === user?.id);
        setConvocatorias(mias);
      } catch { setConvocatorias([]); }
      finally { setLoading(false); }
    }
    if (user) cargar();
  }, [user]);

  if (seleccionada) {
    return (
      <VistaPostulantes
        conv={seleccionada}
        onBack={() => setSeleccionada(null)}
      />
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
          <Star size={20} className="text-usco-vinotinto" /> Mis Evaluaciones
        </h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Registra notas de asignatura y entrevista, y ejecuta el algoritmo RF-MON-05.
        </p>
      </div>

      {/* Fórmula RF-MON-05 */}
      <div className="bg-usco-vinotinto/5 border border-usco-vinotinto/20 rounded-xl px-5 py-3 text-sm">
        <p className="font-semibold text-usco-vinotinto mb-1">Fórmula RF-MON-05</p>
        <p className="text-gray-600 font-mono text-xs">
          Puntaje = (Nota_Asig × 0.30) + (Promedio × 0.30) + (Entrevista × 0.40)
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Empate: 1° mejor entrevista · 2° mejor promedio · 3° mejor nota asignatura
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 size={26} className="animate-spin text-usco-vinotinto" />
        </div>
      ) : convocatorias.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-100 text-gray-400">
          <ClipboardList size={48} className="mx-auto mb-3 opacity-40" />
          <p className="font-medium">No tienes convocatorias asignadas</p>
          <p className="text-sm">Ve a Convocatorias para crear una.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {convocatorias.map(c => {
            const canEval = ['cerrada', 'en_evaluacion', 'finalizada'].includes(c.estado);
            return (
              <button
                key={c.id}
                onClick={() => setSeleccionada(c)}
                className="w-full bg-white rounded-xl border border-gray-100 p-4 text-left hover:border-usco-vinotinto/40 hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-800 text-sm truncate">{c.titulo}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {c.asignatura?.nombre} · {c.periodo_academico} ·{' '}
                      {c.num_monitores_requeridos} monitor(es)
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${estadoConvBadge[c.estado] ?? 'bg-gray-100 text-gray-500'}`}>
                      {c.estado.replace('_', ' ')}
                    </span>
                    {canEval ? (
                      <span className="text-xs text-usco-vinotinto font-semibold flex items-center gap-1">
                        <MessageSquare size={12} /> Evaluar →
                      </span>
                    ) : (
                      <span className="text-xs text-gray-300 flex items-center gap-1">
                        {c.estado === 'borrador' || c.estado === 'abierta'
                          ? <><Clock size={12} /> Aún abierta</>
                          : <><XCircle size={12} /> Finalizada</>
                        }
                      </span>
                    )}
                    {c.estado === 'finalizada' && (
                      <button
                        onClick={async (e) => {
                          e.stopPropagation();
                          try {
                            const r = await pdfService.fo14(c.id);
                            downloadBlob(new Blob([r.data], { type: 'application/pdf' }),
                              `FO-14_Monitor_${c.id}.pdf`);
                          } catch { /* silent */ }
                        }}
                        className="flex items-center gap-1 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-2 py-1 rounded-lg transition-colors">
                        <FileText size={12} /> FO-14
                      </button>
                    )}
                  </div>
                </div>
                <div className="flex gap-4 mt-3 text-xs text-gray-400">
                  <span>Postulantes: <strong className="text-gray-700">{c.total_postulantes ?? '—'}</strong></span>
                  <span>Tipo: <strong className="text-gray-700">{c.tipo_monitoria === 'academica' ? 'Académica' : 'Administrativa'}</strong></span>
                  <span>Promedio mín: <strong className="text-gray-700">{c.promedio_minimo.toFixed(1)}</strong></span>
                </div>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
