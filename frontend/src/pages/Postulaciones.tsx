import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ClipboardList, FileText, Upload, CheckCircle, XCircle, Clock, AlertTriangle, Loader2, MessageSquare, LogOut, QrCode, Download } from 'lucide-react';
import type { Postulacion, EstadoPostulacion } from '../types';
import { postulacionesService, qrService, downloadBlob } from '../services/api';
import { useAuthContext } from '../context/AuthContext';

const estadoConfig: Record<EstadoPostulacion, { label: string; color: string; icon: React.ReactNode }> = {
  pendiente: { label: 'Pendiente', color: 'bg-yellow-100 text-yellow-700', icon: <Clock size={14} /> },
  documentos_incompletos: { label: 'Docs. Incompletos', color: 'bg-orange-100 text-orange-700', icon: <AlertTriangle size={14} /> },
  en_revision: { label: 'En Revisión', color: 'bg-blue-100 text-blue-700', icon: <Clock size={14} /> },
  preseleccionado: { label: 'Preseleccionado', color: 'bg-indigo-100 text-indigo-700', icon: <CheckCircle size={14} /> },
  seleccionado: { label: '✓ Seleccionado', color: 'bg-emerald-100 text-emerald-700', icon: <CheckCircle size={14} /> },
  no_seleccionado: { label: 'No Seleccionado', color: 'bg-red-100 text-red-700', icon: <XCircle size={14} /> },
  desistido: { label: 'Desistido', color: 'bg-gray-100 text-gray-600', icon: <XCircle size={14} /> },
};

const TIPOS_DOC = [
  { value: 'cedula', label: 'Cédula de Ciudadanía' },
  { value: 'rut', label: 'RUT' },
  { value: 'certificado_bancario', label: 'Certificado Bancario' },
];

function UploadDocumentoModal({
  postulacionId,
  tipoInicial,
  onClose,
  onSuccess,
}: {
  postulacionId: number;
  tipoInicial: string;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [tipo, setTipo] = useState(tipoInicial);
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleUpload() {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      await postulacionesService.subirDocumento(postulacionId, tipo, file);
      onSuccess();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setError(err.response?.data?.detail ?? 'Error al subir el documento');
    } finally {
      setLoading(false);
    }
  }

  const tipoLabel = TIPOS_DOC.find(t => t.value === tipo)?.label ?? tipo;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-1">Subir documento</h3>
        <p className="text-sm text-gray-500 mb-4">{tipoLabel}</p>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">
            {error}
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">Tipo de Documento</label>
            <select
              value={tipo}
              onChange={e => setTipo(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-usco-vinotinto"
            >
              {TIPOS_DOC.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">Archivo PDF</label>
            <label className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-gray-300 rounded-xl px-4 py-6 cursor-pointer hover:border-usco-vinotinto hover:bg-red-50 transition-colors">
              <Upload size={24} className="text-gray-400" />
              <span className="text-sm text-gray-500">
                {file ? file.name : 'Haz clic o arrastra un PDF aquí'}
              </span>
              {file && (
                <span className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</span>
              )}
              <input
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={e => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <p className="text-xs text-gray-400 mt-1.5">Solo PDF · máx. 10 MB</p>
          </div>
        </div>
        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-300 text-gray-700 font-semibold py-2.5 rounded-lg hover:bg-gray-50 transition-colors text-sm"
          >
            Cancelar
          </button>
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="flex-1 bg-usco-vinotinto hover:bg-usco-vinotinto/90 text-white font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-60 text-sm flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            {loading ? 'Subiendo...' : 'Subir PDF'}
          </button>
        </div>
      </div>
    </div>
  );
}

const ESTADOS_RETIRABLES: EstadoPostulacion[] = ['pendiente', 'documentos_incompletos', 'en_revision', 'preseleccionado'];

export function Postulaciones() {
  const { user } = useAuthContext();
  const [postulaciones, setPostulaciones] = useState<Postulacion[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadModal, setUploadModal] = useState<{ postId: number; tipo: string } | null>(null);
  const [desistiendo, setDesistiendo] = useState<number | null>(null);

  async function cargar() {
    setLoading(true);
    try {
      const res = await postulacionesService.getMias();
      setPostulaciones(res.data);
    } catch {
      setPostulaciones([]);
    } finally {
      setLoading(false);
    }
  }

  async function handleDesistir(post: Postulacion) {
    if (!window.confirm(`¿Seguro que deseas retirar tu postulación de "${post.convocatoria?.titulo}"? Esta acción no se puede deshacer.`)) return;
    setDesistiendo(post.id);
    try {
      await postulacionesService.desistir(post.id);
      cargar();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail ?? 'No se pudo retirar la postulación.');
    } finally {
      setDesistiendo(null);
    }
  }

  useEffect(() => { cargar(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 size={24} className="animate-spin text-usco-vinotinto" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {uploadModal !== null && (
        <UploadDocumentoModal
          postulacionId={uploadModal.postId}
          tipoInicial={uploadModal.tipo}
          onClose={() => setUploadModal(null)}
          onSuccess={() => { setUploadModal(null); cargar(); }}
        />
      )}

      <div>
        <h1 className="text-2xl font-bold text-gray-800">Mis Postulaciones</h1>
        <p className="text-gray-500 mt-1">Estado de tus postulaciones a convocatorias de monitoría.</p>
      </div>

      {postulaciones.length === 0 ? (
        <div className="text-center py-16 text-gray-400 bg-white rounded-xl border border-gray-100">
          <ClipboardList size={48} className="mx-auto mb-3 opacity-40" />
          <p className="text-lg font-medium">No tienes postulaciones activas</p>
          <p className="text-sm">
            <Link to="/convocatorias" className="text-usco-vinotinto font-semibold hover:underline">Ver convocatorias abiertas</Link>
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {postulaciones.map(post => {
            const cfg = estadoConfig[post.estado];
            const archivos = post.archivos ?? [];
            return (
              <div key={post.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-800 truncate">
                      {post.convocatoria?.titulo ?? `Convocatoria #${post.convocatoria_id}`}
                    </h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {post.convocatoria?.asignatura?.nombre} ·{' '}
                      Postulado: {new Date(post.fecha_postulacion).toLocaleDateString('es-CO')}
                    </p>
                  </div>
                  <span className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full shrink-0 ${cfg.color}`}>
                    {cfg.icon} {cfg.label}
                  </span>
                </div>

                <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1">Promedio</p>
                    <p className="font-bold text-gray-800">{post.promedio_estudiante?.toFixed(2) ?? '—'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1">Nota Asignatura</p>
                    <p className="font-bold text-gray-800">{post.nota_asignatura?.toFixed(2) ?? '—'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1">Entrevista</p>
                    <p className="font-bold text-gray-800">{post.nota_entrevista?.toFixed(2) ?? '—'}</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-1">Puntaje Final</p>
                    <p className={`font-bold ${post.puntaje_final ? 'text-usco-vinotinto' : 'text-gray-800'}`}>
                      {post.puntaje_final?.toFixed(4) ?? '—'}
                    </p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-semibold text-gray-700 flex items-center gap-1.5">
                      <FileText size={15} /> Documentos requeridos
                    </p>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${post.documentos_completos ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'}`}>
                      {post.documentos_completos ? 'Completos' : `${archivos.length}/3 subidos`}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {TIPOS_DOC.map(t => {
                      const archivo = archivos.find((a: { tipo_documento: string }) => a.tipo_documento === t.value);
                      const subido = !!archivo;
                      const puedeSubir = user?.rol === 'estudiante'
                        && !['seleccionado','no_seleccionado','desistido'].includes(post.estado)
                        && post.convocatoria?.estado !== 'finalizada';
                      return (
                        <div
                          key={t.value}
                          className={`flex flex-col gap-1.5 rounded-xl border px-3 py-2.5 ${
                            subido
                              ? 'border-emerald-200 bg-emerald-50'
                              : puedeSubir
                              ? 'border-dashed border-gray-300 bg-gray-50 hover:border-usco-vinotinto hover:bg-red-50 cursor-pointer transition-colors'
                              : 'border-gray-200 bg-gray-50'
                          }`}
                          onClick={() => {
                            if (!subido && puedeSubir) setUploadModal({ postId: post.id, tipo: t.value });
                          }}
                          role={!subido && puedeSubir ? 'button' : undefined}
                          tabIndex={!subido && puedeSubir ? 0 : undefined}
                          onKeyDown={e => { if (!subido && puedeSubir && (e.key === 'Enter' || e.key === ' ')) setUploadModal({ postId: post.id, tipo: t.value }); }}
                        >
                          <div className="flex items-center justify-between">
                            <span className={`text-xs font-semibold ${
                              subido ? 'text-emerald-700' : 'text-gray-500'
                            }`}>{t.label}</span>
                            {subido
                              ? <CheckCircle size={14} className="text-emerald-500 shrink-0" />
                              : puedeSubir
                              ? <Upload size={14} className="text-gray-400 shrink-0" />
                              : <XCircle size={14} className="text-gray-300 shrink-0" />}
                          </div>
                          {subido && archivo ? (
                            <>
                              <p className="text-[10px] text-gray-400 truncate">{archivo.nombre_original}</p>
                              <button
                                onClick={async e => {
                                  e.stopPropagation();
                                  try {
                                    const r = await postulacionesService.descargarDocumento(archivo.id);
                                    downloadBlob(r.data, archivo.nombre_original);
                                  } catch { /* silencioso */ }
                                }}
                                className="flex items-center gap-1 text-[10px] font-semibold text-usco-vinotinto hover:underline text-left"
                              >
                                <Download size={10} /> Descargar
                              </button>
                              {puedeSubir && (
                                <button
                                  onClick={e => { e.stopPropagation(); setUploadModal({ postId: post.id, tipo: t.value }); }}
                                  className="text-[10px] text-gray-400 hover:text-usco-vinotinto transition-colors text-left"
                                >
                                  Reemplazar
                                </button>
                              )}
                            </>
                          ) : (
                            puedeSubir && <p className="text-[10px] text-gray-400">Clic para subir PDF</p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  {post.estado === 'seleccionado' && (
                    <button
                      onClick={async () => {
                        try {
                          const r = await qrService.postulacion(post.id);
                          downloadBlob(r.data, `qr_postulacion_${post.id}.png`);
                        } catch { /* silencioso */ }
                      }}
                      className="mt-2 flex items-center gap-1.5 text-xs font-semibold text-indigo-500 hover:text-indigo-700 transition-colors"
                    >
                      <QrCode size={13} /> Descargar QR de verificación
                    </button>
                  )}
                  {user?.rol === 'estudiante' && ESTADOS_RETIRABLES.includes(post.estado) && (
                    <button
                      onClick={() => handleDesistir(post)}
                      disabled={desistiendo === post.id}
                      className="mt-2 flex items-center gap-1.5 text-xs font-semibold text-gray-400 hover:text-red-500 transition-colors disabled:opacity-40"
                    >
                      {desistiendo === post.id
                        ? <Loader2 size={13} className="animate-spin" />
                        : <LogOut size={13} />}
                      Retirar postulación
                    </button>
                  )}
                  {post.carta_motivacion && (
                    <div className="mt-3 bg-gray-50 rounded-lg px-3 py-2.5">
                      <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1">
                        <MessageSquare size={12} /> Carta de motivación
                      </p>
                      <p className="text-xs text-gray-600 line-clamp-3">{post.carta_motivacion}</p>
                    </div>
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
