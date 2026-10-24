import { useState, useEffect, useCallback } from 'react';
import { FileText, BookOpen, Users, MapPin, DollarSign, Loader2, Download, AlertCircle, History } from 'lucide-react';
import { reportesService, exportarService, downloadBlob } from '../services/api';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface MonitorSeleccionado {
  postulacion_id: number;
  estudiante: string;
  codigo: string;
  convocatoria: string;
  asignatura: string;
  puntaje_final: number | null;
  periodo: string;
}

interface PracticaItem {
  id: number;
  nombre: string;
  asignatura: string;
  profesor: string;
  estado: string;
  periodo: string;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  num_alumnos: number;
  quorum_alcanzado: boolean;
  firmas_obtenidas: number;
  firmas_requeridas: number | null;
}

interface PresupuestoResumen {
  periodo: string;
  total_asignado: number;
  ejecutado: number;
  comprometido: number;
  disponible: number;
  porcentaje_ejecutado: number;
  estado: string;
}

interface Resumen {
  convocatorias: { total: number; por_estado: Record<string, number>; periodos: string[] };
  postulaciones: { total: number; por_estado: Record<string, number> };
  monitores_seleccionados: MonitorSeleccionado[];
  practicas: { total: number; por_estado: Record<string, number>; lista: PracticaItem[] };
  presupuesto: PresupuestoResumen[];
}

function formatCOP(v: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v);
}

const estadoPracticaLabel: Record<string, string> = {
  borrador: 'Borrador', solicitada: 'Solicitada', pendiente_quorum: 'Pend. Quórum',
  aprobada_curriculo: 'Aprobada Comité', aprobada_facultad: 'Avalada Facultad',
  aprobado_transporte: 'Aprobada Vicerrectoría', en_ejecucion: 'En Ejecución',
  finalizada: 'Finalizada', rechazada: 'Rechazada',
};
const estadoPracticaColor: Record<string, string> = {
  borrador: 'bg-gray-100 text-gray-600', solicitada: 'bg-blue-100 text-blue-700',
  pendiente_quorum: 'bg-yellow-100 text-yellow-700',
  aprobada_curriculo: 'bg-cyan-100 text-cyan-700', aprobada_facultad: 'bg-violet-100 text-violet-700',
  aprobado_transporte: 'bg-emerald-100 text-emerald-700',
  en_ejecucion: 'bg-indigo-100 text-indigo-700', finalizada: 'bg-gray-200 text-gray-700',
  rechazada: 'bg-red-100 text-red-700',
};

function StatCard({ label, value, icon, color }: { label: string; value: string | number; icon: React.ReactNode; color: string }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-center gap-4">
      <div className={`${color} text-white rounded-xl p-3 shrink-0`}>{icon}</div>
      <div>
        <p className="text-xs text-gray-400 mb-0.5">{label}</p>
        <p className="text-xl font-bold text-gray-800">{value}</p>
      </div>
    </div>
  );
}

interface AuditEntry {
  id: number;
  usuario: string;
  codigo: string;
  accion: string;
  entidad: string;
  entidad_id?: number | null;
  detalle?: string | null;
  created_at: string;
}

export function Reportes() {
  const [resumen, setResumen] = useState<Resumen | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<'monitores' | 'practicas' | 'presupuesto' | 'auditlog'>('monitores');
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);
  const [exportandoCsv, setExportandoCsv] = useState(false);

  async function exportarAuditCsv() {
    setExportandoCsv(true);
    try {
      const r = await exportarService.auditLogCsv(1000);
      downloadBlob(r.data, `audit_log_${new Date().toISOString().slice(0, 10)}.csv`);
    } catch { /* silencioso */ }
    finally { setExportandoCsv(false); }
  }

  useEffect(() => {
    reportesService.getResumen()
      .then(r => setResumen(r.data))
      .catch(() => setError('No se pudo cargar el resumen de reportes.'))
      .finally(() => setLoading(false));
  }, []);

  const cargarAudit = useCallback(async () => {
    setLoadingAudit(true);
    try { const r = await reportesService.getAuditLog(100); setAuditLog(r.data); }
    catch { setAuditLog([]); } finally { setLoadingAudit(false); }
  }, []);

  useEffect(() => { if (tab === 'auditlog') cargarAudit(); }, [tab, cargarAudit]);

  function exportarPDFMonitores() {
    if (!resumen) return;
    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
    const pageW = doc.internal.pageSize.width;
    const VINOTINTO: [number, number, number] = [141, 25, 29];
    const GRIS: [number, number, number] = [78, 100, 112];
    const fechaHoy = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

    // Header vinotinto strip
    doc.setFillColor(...VINOTINTO);
    doc.rect(0, 0, pageW, 2, 'F');
    doc.setFillColor(245, 242, 234);
    doc.rect(0, 4, pageW, 20, 'F');
    doc.setFontSize(13); doc.setFont('helvetica', 'bold'); doc.setTextColor(...VINOTINTO);
    doc.text('UNIVERSIDAD SURCOLOMBIANA', pageW / 2, 12, { align: 'center' });
    doc.setFontSize(10); doc.setFont('helvetica', 'normal'); doc.setTextColor(...GRIS);
    doc.text('ACTA DE SELECCIÓN DE MONITORES — MI-FOR-FO-14', pageW / 2, 18, { align: 'center' });
    doc.setFontSize(8); doc.setTextColor(120, 120, 120);
    doc.text(`Generado: ${fechaHoy}   ·   Períodos: ${[...new Set(resumen.monitores_seleccionados.map(m => m.periodo))].join(', ')}`, pageW / 2, 23, { align: 'center' });
    doc.setFillColor(...VINOTINTO);
    doc.rect(0, 26, pageW, 1, 'F');

    // Summary KPIs
    doc.setFontSize(9); doc.setFont('helvetica', 'bold'); doc.setTextColor(40, 40, 40);
    doc.text(`Total monitores seleccionados: ${resumen.monitores_seleccionados.length}`, 14, 33);
    doc.text(`Convocatorias totales: ${resumen.convocatorias.total}`, 100, 33);
    doc.text(`Postulaciones recibidas: ${resumen.postulaciones.total}`, 200, 33);

    autoTable(doc, {
      startY: 38,
      margin: { left: 10, right: 10 },
      head: [['#', 'Código', 'Nombre del Monitor', 'Asignatura', 'Convocatoria', 'Período', 'Nota×0.30', 'Prom×0.30', 'Ent×0.40', 'Puntaje Final']],
      body: resumen.monitores_seleccionados.map((m, i) => [
        i + 1, m.codigo, m.estudiante, m.asignatura, m.convocatoria, m.periodo,
        '—', '—', '—',
        m.puntaje_final != null
          ? { content: m.puntaje_final.toFixed(4), styles: { fontStyle: 'bold', textColor: VINOTINTO } }
          : '—',
      ]),
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: VINOTINTO, fontStyle: 'bold', fontSize: 8 },
      alternateRowStyles: { fillColor: [248, 248, 248] },
      columnStyles: {
        0: { halign: 'center', cellWidth: 10 },
        1: { cellWidth: 22, font: 'courier' },
        9: { halign: 'right', cellWidth: 26 },
      },
    });

    const finalY = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 10;
    if (finalY < doc.internal.pageSize.height - 30) {
      ['Docente / Coordinador', 'Decano(a) de Facultad', 'Firma SIPAM-USCO'].forEach((label, i) => {
        const fx = 14 + i * (pageW - 28) / 3;
        doc.setDrawColor(180, 180, 180);
        doc.line(fx, finalY + 14, fx + (pageW - 28) / 3 - 8, finalY + 14);
        doc.setFontSize(7.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(60, 60, 60);
        doc.text(label, fx + ((pageW - 28) / 3 - 8) / 2, finalY + 18, { align: 'center' });
      });
    }
    doc.setFillColor(...VINOTINTO);
    doc.rect(0, doc.internal.pageSize.height - 2, pageW, 2, 'F');
    doc.save(`FO-14_Acta_Monitores_${new Date().toISOString().slice(0, 10)}.pdf`);
  }

  function exportarPDFPracticas() {
    if (!resumen) return;
    const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
    const pageW = doc.internal.pageSize.width;
    const VINOTINTO: [number, number, number] = [141, 25, 29];
    const GRIS: [number, number, number] = [78, 100, 112];
    const fechaHoy = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

    doc.setFillColor(...VINOTINTO);
    doc.rect(0, 0, pageW, 2, 'F');
    doc.setFillColor(245, 242, 234);
    doc.rect(0, 4, pageW, 20, 'F');
    doc.setFontSize(13); doc.setFont('helvetica', 'bold'); doc.setTextColor(...VINOTINTO);
    doc.text('UNIVERSIDAD SURCOLOMBIANA', pageW / 2, 12, { align: 'center' });
    doc.setFontSize(10); doc.setFont('helvetica', 'normal'); doc.setTextColor(...GRIS);
    doc.text('RESUMEN PRÁCTICAS EXTRAMUROS — MI-FOR-FO-15', pageW / 2, 18, { align: 'center' });
    doc.setFontSize(8); doc.setTextColor(120, 120, 120);
    doc.text(`Generado: ${fechaHoy}   ·   Total prácticas: ${resumen.practicas.total}`, pageW / 2, 23, { align: 'center' });
    doc.setFillColor(...VINOTINTO);
    doc.rect(0, 26, pageW, 1, 'F');

    // KPIs por estado
    const estados = Object.entries(resumen.practicas.por_estado);
    const kpiW = (pageW - 20) / Math.max(estados.length, 1);
    estados.forEach(([estado, n], i) => {
      const kx = 10 + i * kpiW;
      doc.setFillColor(248, 248, 248);
      doc.rect(kx, 30, kpiW - 3, 10, 'F');
      doc.setFontSize(7); doc.setFont('helvetica', 'normal'); doc.setTextColor(120, 120, 120);
      doc.text((estadoPracticaLabel[estado] ?? estado).toUpperCase(), kx + (kpiW - 3) / 2, 35, { align: 'center' });
      doc.setFontSize(11); doc.setFont('helvetica', 'bold'); doc.setTextColor(...VINOTINTO);
      doc.text(String(n), kx + (kpiW - 3) / 2, 40, { align: 'center' });
    });

    autoTable(doc, {
      startY: 44,
      margin: { left: 10, right: 10 },
      head: [['#', 'Nombre Práctica', 'Asignatura', 'Docente Responsable', 'Fecha Inicio', 'Estado', 'Alumnos', 'Firmas', 'Quórum']],
      body: resumen.practicas.lista.map((p, i) => [
        i + 1, p.nombre, p.asignatura, p.profesor,
        p.fecha_inicio ?? '—',
        { content: estadoPracticaLabel[p.estado] ?? p.estado, styles: { fontStyle: 'bold' } },
        { content: p.num_alumnos, styles: { halign: 'center' } },
        { content: `${p.firmas_obtenidas}/${p.firmas_requeridas ?? p.num_alumnos}`, styles: { halign: 'center' } },
        {
          content: p.quorum_alcanzado ? '✔ Sí' : '✘ No',
          styles: { halign: 'center', fontStyle: 'bold', textColor: p.quorum_alcanzado ? [0, 120, 80] : [180, 50, 50] },
        },
      ]),
      styles: { fontSize: 8, cellPadding: 2 },
      headStyles: { fillColor: VINOTINTO, fontStyle: 'bold', fontSize: 8 },
      alternateRowStyles: { fillColor: [248, 248, 248] },
      columnStyles: {
        0: { halign: 'center', cellWidth: 10 },
        5: { cellWidth: 32 },
        6: { halign: 'center', cellWidth: 20 },
        7: { halign: 'center', cellWidth: 20 },
        8: { halign: 'center', cellWidth: 22 },
      },
    });

    doc.setFillColor(...GRIS);
    doc.rect(0, doc.internal.pageSize.height - 2, pageW, 2, 'F');
    doc.save(`FO-15_Resumen_Practicas_${new Date().toISOString().slice(0, 10)}.pdf`);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 size={26} className="animate-spin text-usco-vinotinto" />
      </div>
    );
  }

  if (error || !resumen) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-3 text-gray-400">
        <AlertCircle size={40} className="opacity-50" />
        <p className="text-sm">{error || 'Sin datos'}</p>
      </div>
    );
  }

  const { convocatorias, postulaciones, monitores_seleccionados, practicas, presupuesto } = resumen;
  const totalAprobadas = practicas.por_estado['aprobado_transporte'] ?? 0;
  const totalEjecutado = presupuesto.reduce((s, p) => s + p.ejecutado, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Reportes y Actas</h1>
          <p className="text-sm text-gray-500 mt-0.5">Estadísticas consolidadas del sistema SIPAM-USCO</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={exportarPDFMonitores}
            className="flex items-center gap-2 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-3 py-2 rounded-lg">
            <Download size={13} /> Acta Monitores
          </button>
          <button onClick={exportarPDFPracticas}
            className="flex items-center gap-2 text-xs font-semibold text-usco-vinotinto border border-usco-vinotinto/30 hover:bg-usco-vinotinto/5 px-3 py-2 rounded-lg">
            <Download size={13} /> Acta Prácticas
          </button>
          <button onClick={() => window.print()}
            className="flex items-center gap-2 text-sm font-semibold text-white bg-usco-vinotinto hover:bg-usco-vinotinto/90 px-4 py-2 rounded-lg">
            <Download size={15} /> Imprimir
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Convocatorias" value={convocatorias.total} icon={<BookOpen size={22} />} color="bg-usco-vinotinto" />
        <StatCard label="Monitores seleccionados" value={monitores_seleccionados.length} icon={<Users size={22} />} color="bg-indigo-600" />
        <StatCard label="Prácticas aprobadas" value={totalAprobadas} icon={<MapPin size={22} />} color="bg-emerald-600" />
        <StatCard label="Total ejecutado" value={formatCOP(totalEjecutado)} icon={<DollarSign size={22} />} color="bg-amber-500" />
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="flex border-b border-gray-100">
          {([
            { key: 'monitores', label: `Monitores (${monitores_seleccionados.length})`, icon: <Users size={15} /> },
            { key: 'practicas', label: `Prácticas (${practicas.total})`, icon: <MapPin size={15} /> },
            { key: 'presupuesto', label: `Presupuesto (${presupuesto.length})`, icon: <DollarSign size={15} /> },
            { key: 'auditlog', label: 'Bitácora', icon: <History size={15} /> },
          ] as const).map(t => (
            <button key={t.key} onClick={() => setTab(t.key)}
              className={`flex items-center gap-2 px-5 py-3.5 text-sm font-semibold border-b-2 transition-colors ${
                tab === t.key
                  ? 'border-usco-vinotinto text-usco-vinotinto'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        <div className="p-5">
          {/* Monitores seleccionados */}
          {tab === 'monitores' && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FileText size={16} className="text-usco-vinotinto" />
                <h2 className="text-sm font-bold text-gray-700">Acta de Selección de Monitores</h2>
              </div>
              {/* Resumen convocatorias */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                {Object.entries(convocatorias.por_estado).map(([estado, n]) => (
                  <div key={estado} className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-0.5 capitalize">{estado.replace('_', ' ')}</p>
                    <p className="text-lg font-bold text-gray-800">{n}</p>
                  </div>
                ))}
              </div>
              {monitores_seleccionados.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">No hay monitores seleccionados aún</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-4">Estudiante</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-4">Código</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-4">Asignatura</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-4">Período</th>
                        <th className="text-right text-xs font-semibold text-gray-500 pb-2">Puntaje RF-MON-05</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {monitores_seleccionados.map(m => (
                        <tr key={m.postulacion_id}>
                          <td className="py-2.5 pr-4 font-medium text-gray-800">{m.estudiante}</td>
                          <td className="py-2.5 pr-4 font-mono text-gray-500 text-xs">{m.codigo}</td>
                          <td className="py-2.5 pr-4 text-gray-600">{m.asignatura}</td>
                          <td className="py-2.5 pr-4 text-gray-500">{m.periodo}</td>
                          <td className="py-2.5 text-right font-bold text-usco-vinotinto">
                            {m.puntaje_final?.toFixed(4) ?? '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Prácticas */}
          {tab === 'practicas' && (
            <div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                {Object.entries(practicas.por_estado).map(([estado, n]) => (
                  <div key={estado} className="bg-gray-50 rounded-lg p-3 text-center">
                    <p className="text-xs text-gray-400 mb-0.5">{estadoPracticaLabel[estado] ?? estado}</p>
                    <p className="text-lg font-bold text-gray-800">{n}</p>
                  </div>
                ))}
              </div>
              {practicas.lista.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">No hay prácticas registradas</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-3">Práctica</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-3">Asignatura</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-3">Profesor</th>
                        <th className="text-center text-xs font-semibold text-gray-500 pb-2 pr-3">Alumnos</th>
                        <th className="text-center text-xs font-semibold text-gray-500 pb-2 pr-3">Quórum</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {practicas.lista.map(pr => (
                        <tr key={pr.id}>
                          <td className="py-2.5 pr-3 font-medium text-gray-800 max-w-[180px] truncate">{pr.nombre}</td>
                          <td className="py-2.5 pr-3 text-gray-600 text-xs">{pr.asignatura}</td>
                          <td className="py-2.5 pr-3 text-gray-500 text-xs">{pr.profesor}</td>
                          <td className="py-2.5 pr-3 text-center text-gray-700">{pr.num_alumnos}</td>
                          <td className="py-2.5 pr-3 text-center">
                            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${pr.quorum_alcanzado ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'}`}>
                              {pr.firmas_obtenidas}/{pr.firmas_requeridas ?? '?'}
                            </span>
                          </td>
                          <td className="py-2.5">
                            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${estadoPracticaColor[pr.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                              {estadoPracticaLabel[pr.estado] ?? pr.estado}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Presupuesto histórico */}
          {tab === 'auditlog' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-bold text-gray-700 flex items-center gap-2"><History size={15} className="text-usco-vinotinto" /> Bitácora de acciones del sistema</h2>
                <button onClick={exportarAuditCsv} disabled={exportandoCsv}
                  className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 border border-emerald-300 hover:bg-emerald-50 px-3 py-1.5 rounded-lg disabled:opacity-50">
                  {exportandoCsv ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
                  Exportar CSV
                </button>
              </div>
              {loadingAudit ? (
                <div className="flex justify-center py-8"><Loader2 size={20} className="animate-spin text-gray-400" /></div>
              ) : auditLog.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">Sin registros en la bitácora</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-3">Fecha</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-3">Usuario</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-3">Acción</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-3">Entidad</th>
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2">Detalle</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {auditLog.map(log => (
                        <tr key={log.id} className="hover:bg-gray-50/50">
                          <td className="py-2 pr-3 text-xs text-gray-400 whitespace-nowrap">{new Date(log.created_at).toLocaleString('es-CO')}</td>
                          <td className="py-2 pr-3">
                            <p className="text-xs font-semibold text-gray-700">{log.usuario}</p>
                            <p className="text-[10px] text-gray-400 font-mono">{log.codigo}</p>
                          </td>
                          <td className="py-2 pr-3"><span className="text-xs font-mono bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded">{log.accion}</span></td>
                          <td className="py-2 pr-3 text-xs text-gray-500">{log.entidad}{log.entidad_id ? ` #${log.entidad_id}` : ''}</td>
                          <td className="py-2 text-xs text-gray-400">{log.detalle ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {tab === 'presupuesto' && (
            <div>
              {presupuesto.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">Sin datos de presupuesto</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-100">
                        <th className="text-left text-xs font-semibold text-gray-500 pb-2 pr-4">Período</th>
                        <th className="text-right text-xs font-semibold text-gray-500 pb-2 pr-4">Asignado</th>
                        <th className="text-right text-xs font-semibold text-gray-500 pb-2 pr-4">Ejecutado</th>
                        <th className="text-right text-xs font-semibold text-gray-500 pb-2 pr-4">Comprometido</th>
                        <th className="text-right text-xs font-semibold text-gray-500 pb-2 pr-4">Disponible</th>
                        <th className="text-center text-xs font-semibold text-gray-500 pb-2 pr-4">% Ejecución</th>
                        <th className="text-center text-xs font-semibold text-gray-500 pb-2">Estado</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-50">
                      {presupuesto.map(p => {
                        const alerta = p.porcentaje_ejecutado >= 85;
                        const estadoColors: Record<string, string> = {
                          aprobado: 'bg-emerald-100 text-emerald-700',
                          solicitado: 'bg-blue-100 text-blue-700',
                          borrador: 'bg-gray-100 text-gray-600',
                          rechazado: 'bg-red-100 text-red-700',
                          modificacion: 'bg-amber-100 text-amber-700',
                        };
                        return (
                          <tr key={p.periodo}>
                            <td className="py-2.5 pr-4 font-bold text-gray-800">{p.periodo}</td>
                            <td className="py-2.5 pr-4 text-right text-gray-700">{formatCOP(p.total_asignado)}</td>
                            <td className="py-2.5 pr-4 text-right text-red-600 font-medium">{formatCOP(p.ejecutado)}</td>
                            <td className="py-2.5 pr-4 text-right text-amber-600">{formatCOP(p.comprometido)}</td>
                            <td className="py-2.5 pr-4 text-right text-emerald-600 font-medium">{formatCOP(p.disponible)}</td>
                            <td className="py-2.5 pr-4 text-center">
                              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${alerta ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}>
                                {p.porcentaje_ejecutado.toFixed(1)}%
                              </span>
                            </td>
                            <td className="py-2.5 text-center">
                              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full capitalize ${estadoColors[p.estado] ?? 'bg-gray-100 text-gray-600'}`}>
                                {p.estado}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot className="border-t-2 border-gray-200">
                      <tr>
                        <td className="pt-3 text-xs font-bold text-gray-600">TOTALES</td>
                        <td className="pt-3 text-right text-xs font-bold text-gray-800">{formatCOP(presupuesto.reduce((s, p) => s + p.total_asignado, 0))}</td>
                        <td className="pt-3 text-right text-xs font-bold text-red-600">{formatCOP(presupuesto.reduce((s, p) => s + p.ejecutado, 0))}</td>
                        <td className="pt-3 text-right text-xs font-bold text-amber-600">{formatCOP(presupuesto.reduce((s, p) => s + p.comprometido, 0))}</td>
                        <td className="pt-3 text-right text-xs font-bold text-emerald-600">{formatCOP(presupuesto.reduce((s, p) => s + p.disponible, 0))}</td>
                        <td colSpan={2} />
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Postulaciones por estado */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        <h2 className="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
          <BookOpen size={15} className="text-usco-vinotinto" /> Postulaciones por estado
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {Object.entries(postulaciones.por_estado).map(([estado, n]) => (
            <div key={estado} className="bg-gray-50 rounded-lg p-3 text-center">
              <p className="text-xs text-gray-400 mb-1 capitalize leading-tight">{estado.replace(/_/g, ' ')}</p>
              <p className="text-xl font-bold text-gray-800">{n}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-gray-400 mt-3 text-right">Total: {postulaciones.total} postulaciones</p>
      </div>
    </div>
  );
}
