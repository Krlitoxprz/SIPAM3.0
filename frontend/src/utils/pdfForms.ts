import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const VINOTINTO: [number, number, number] = [141, 25, 29];
const GRIS: [number, number, number] = [78, 100, 112];
const OCRE_BG: [number, number, number] = [245, 242, 234];

function formatCOP(v: number) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(v);
}

function drawHeader(doc: jsPDF, titulo: string, codigo: string, version: string, fecha: string) {
  // Borde superior vinotinto
  doc.setFillColor(...VINOTINTO);
  doc.rect(0, 0, doc.internal.pageSize.width, 2, 'F');

  // Recuadro logo USCO (izquierda)
  doc.setDrawColor(...VINOTINTO);
  doc.setLineWidth(0.5);
  doc.rect(10, 5, 40, 22);
  doc.setFontSize(7);
  doc.setTextColor(...VINOTINTO);
  doc.setFont('helvetica', 'bold');
  doc.text('UNIVERSIDAD', 13, 12);
  doc.text('SURCOLOMBIANA', 13, 16);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...GRIS);
  doc.setFontSize(6);
  doc.text('Neiva - Huila - Colombia', 13, 20);
  doc.text('www.usco.edu.co', 13, 24);

  // Título central
  doc.setFillColor(...OCRE_BG);
  doc.rect(52, 5, doc.internal.pageSize.width - 102, 22, 'F');
  doc.rect(52, 5, doc.internal.pageSize.width - 102, 22);
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...VINOTINTO);
  const titleLines = doc.splitTextToSize(titulo, doc.internal.pageSize.width - 110);
  const titleY = titleLines.length > 1 ? 12 : 17;
  doc.text(titleLines, doc.internal.pageSize.width / 2, titleY, { align: 'center' });

  // Recuadro código/versión (derecha)
  const rightX = doc.internal.pageSize.width - 48;
  doc.rect(rightX, 5, 38, 22);
  doc.setFontSize(7);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text('Código:', rightX + 2, 11);
  doc.setFont('helvetica', 'normal');
  doc.text(codigo, rightX + 2, 15);
  doc.setFont('helvetica', 'bold');
  doc.text('Versión:', rightX + 2, 19);
  doc.setFont('helvetica', 'normal');
  doc.text(version, rightX + 2, 23);

  // Línea separadora
  doc.setDrawColor(...VINOTINTO);
  doc.setLineWidth(0.8);
  doc.line(10, 29, doc.internal.pageSize.width - 10, 29);

  // Fecha generación
  doc.setFontSize(7);
  doc.setTextColor(120, 120, 120);
  doc.setFont('helvetica', 'normal');
  doc.text(`Documento generado: ${fecha}`, doc.internal.pageSize.width - 10, 34, { align: 'right' });

  return 38; // Y de inicio del contenido
}

function sectionLabel(doc: jsPDF, text: string, y: number, pageW: number) {
  doc.setFillColor(...VINOTINTO);
  doc.rect(10, y, pageW - 20, 6, 'F');
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text(text.toUpperCase(), 13, y + 4.2);
  return y + 8;
}

function infoRow(doc: jsPDF, label: string, value: string, x: number, y: number, labelW = 45) {
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text(label + ':', x, y);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(String(value ?? '—'), x + labelW, y);
}

// ─────────────────────────────────────────────────────────────────
// MI-FOR-FO-14  Requerimiento Monitores
// ─────────────────────────────────────────────────────────────────
const TIPO_MONITORIA_LABEL: Record<string, string> = {
  nee: 'a) Acompañamiento NEE (Bienestar)',
  regimenes_especiales: 'b) Regímenes Especiales',
  academica_cursos: 'c) Académica — Cursos/Asignaturas',
  laboratorios: 'd) Laboratorios',
  tic: 'e) TIC / Salas Informática',
  permanencia_graduacion: 'f) Permanencia y Graduación',
  deportiva: 'g) Deportiva (Bienestar)',
  cultural: 'h) Cultural y Artística (Bienestar)',
  biblioteca: 'i) Biblioteca',
  acreditacion: 'j) Acreditación y Registro Calificado',
  investigacion: 'k) Investigación / Proyección Social',
  academica: 'Académica',
  administrativa: 'Administrativa',
};

const TIPO_DOCENTE_LABEL: Record<string, string> = {
  planta: 'Docente de Planta',
  catedra: 'Docente Cátedra',
  ocasional: 'Nombramiento Ocasional',
  visitante: 'Cátedra Visitante',
};

export function generarFO14(data: {
  convocatoria: {
    titulo: string; periodo_academico: string; tipo_monitoria: string;
    horas_semana: number; horas_semestre: number; descripcion_actividades?: string | null;
    promedio_minimo: number; creditos_minimo_pct: number; sede?: string | null;
  };
  asignatura: { nombre: string; codigo: string; creditos: number; programa: string; facultad?: string | null; semestre: number };
  docente: { nombres: string; cedula: string; email: string };
  monitor: {
    nombres: string; codigo: string; cedula: string;
    promedio?: number | null; porcentaje_creditos?: number | null; programa?: string | null;
    nota_asignatura?: number | null; nota_entrevista?: number | null; puntaje_final?: number | null;
  } | null;
  total_postulantes: number;
}) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageW = doc.internal.pageSize.width;
  const fechaHoy = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

  let y = drawHeader(doc, 'REQUERIMIENTO MONITORES', 'MI-FOR-FO-14', '1', fechaHoy);

  const numSemanas = data.convocatoria.horas_semana > 0
    ? Math.round(data.convocatoria.horas_semestre / data.convocatoria.horas_semana)
    : 0;

  // SECCIÓN 1: DATOS INSTITUCIONALES
  y = sectionLabel(doc, '1. Datos Institucionales', y, pageW);
  infoRow(doc, 'Facultad', data.asignatura.facultad ?? 'No registrada', 12, y);
  infoRow(doc, 'Programa', data.asignatura.programa, 12, y + 5);
  infoRow(doc, 'Período académico', data.convocatoria.periodo_academico, 12, y + 10);
  infoRow(doc, 'Sede', data.convocatoria.sede ?? 'Neiva', 12, y + 15);
  infoRow(doc, 'Tipo de monitoría', TIPO_MONITORIA_LABEL[data.convocatoria.tipo_monitoria] ?? data.convocatoria.tipo_monitoria, 110, y);
  infoRow(doc, 'Horas / semana', String(data.convocatoria.horas_semana), 110, y + 5);
  infoRow(doc, 'N° semanas', String(numSemanas), 110, y + 10);
  infoRow(doc, 'Horas / semestre', String(data.convocatoria.horas_semestre), 110, y + 15);
  y += 23;

  // SECCIÓN 2: ASIGNATURA
  y = sectionLabel(doc, '2. Datos de la Asignatura', y, pageW);
  infoRow(doc, 'Nombre', data.asignatura.nombre, 12, y);
  infoRow(doc, 'Código', data.asignatura.codigo, 12, y + 5);
  infoRow(doc, 'Créditos', String(data.asignatura.creditos), 110, y);
  infoRow(doc, 'Semestre', String(data.asignatura.semestre) + '°', 110, y + 5);
  y += 13;

  // SECCIÓN 3: DOCENTE SOLICITANTE
  y = sectionLabel(doc, '3. Docente Solicitante', y, pageW);
  infoRow(doc, 'Nombre completo', data.docente.nombres, 12, y);
  infoRow(doc, 'Cédula', data.docente.cedula, 12, y + 5);
  infoRow(doc, 'Correo institucional', data.docente.email, 12, y + 10);
  y += 18;

  // SECCIÓN 4: MONITOR SELECCIONADO
  y = sectionLabel(doc, '4. Monitor Seleccionado', y, pageW);
  if (data.monitor) {
    infoRow(doc, 'Nombre completo', data.monitor.nombres, 12, y);
    infoRow(doc, 'Código estudiantil', data.monitor.codigo, 12, y + 5);
    infoRow(doc, 'Cédula', data.monitor.cedula, 12, y + 10);
    infoRow(doc, 'Programa', data.monitor.programa ?? '—', 12, y + 15);
    infoRow(doc, 'Promedio acumulado', data.monitor.promedio != null ? data.monitor.promedio.toFixed(2) : '—', 110, y);
    infoRow(doc, '% créditos aprobados', data.monitor.porcentaje_creditos != null ? data.monitor.porcentaje_creditos.toFixed(1) + '%' : '—', 110, y + 5);
    y += 23;
  } else {
    doc.setFontSize(8);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(180, 180, 180);
    doc.text('Aún no se ha seleccionado un monitor para esta convocatoria.', 12, y + 4);
    y += 12;
  }

  // SECCIÓN 5: CRITERIOS DE SELECCIÓN RF-MON-05
  y = sectionLabel(doc, '5. Criterios de Selección — RF-MON-05: (Nota×0.30) + (Promedio×0.30) + (Entrevista×0.40)', y, pageW);
  autoTable(doc, {
    startY: y,
    margin: { left: 10, right: 10 },
    head: [['Criterio', 'Ponderación', 'Valor obtenido', 'Contribución']],
    body: [
      ['Nota en la asignatura', '30%', data.monitor?.nota_asignatura != null ? data.monitor.nota_asignatura.toFixed(2) : '—', data.monitor?.nota_asignatura != null ? (data.monitor.nota_asignatura * 0.30).toFixed(4) : '—'],
      ['Promedio académico', '30%', data.monitor?.promedio != null ? data.monitor.promedio.toFixed(2) : '—', data.monitor?.promedio != null ? (data.monitor.promedio * 0.30).toFixed(4) : '—'],
      ['Resultado entrevista', '40%', data.monitor?.nota_entrevista != null ? data.monitor.nota_entrevista.toFixed(2) : '—', data.monitor?.nota_entrevista != null ? (data.monitor.nota_entrevista * 0.40).toFixed(4) : '—'],
      ['PUNTAJE FINAL', '100%', '', data.monitor?.puntaje_final != null ? data.monitor.puntaje_final.toFixed(4) : '—'],
    ],
    styles: { fontSize: 8, cellPadding: 2 },
    headStyles: { fillColor: VINOTINTO, fontStyle: 'bold' },
    bodyStyles: { textColor: [30, 30, 30] },
    columnStyles: { 0: { fontStyle: 'bold' }, 3: { fontStyle: 'bold' } },
    alternateRowStyles: { fillColor: [248, 248, 248] },
  });
  y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 5;

  // SECCIÓN 6: ACTIVIDADES
  y = sectionLabel(doc, '6. Actividades y Compromisos de la Monitoría', y, pageW);
  const actividades = data.convocatoria.descripcion_actividades ?? 'No registradas';
  const actLines = doc.splitTextToSize(actividades, pageW - 25);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(actLines, 12, y + 4);
  y += Math.max(4 + actLines.length * 4, 10) + 6;

  // SECCIÓN 7: DOCUMENTOS ADJUNTOS
  y = sectionLabel(doc, '7. Documentos Adjuntos Requeridos', y, pageW);
  const docs = [
    ['Fotocopia de cédula de ciudadanía', 'Obligatorio'],
    ['Certificado bancario (cuenta activa)', 'Obligatorio'],
    ['RUT (Registro Único Tributario)', 'Obligatorio'],
  ];
  autoTable(doc, {
    startY: y,
    margin: { left: 10, right: 10 },
    head: [['Documento', 'Estado']],
    body: docs,
    styles: { fontSize: 8 },
    headStyles: { fillColor: GRIS },
    columnStyles: { 1: { halign: 'center' } },
  });
  y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;

  // SECCIÓN 8: FIRMAS
  if (y > doc.internal.pageSize.height - 55) {
    doc.addPage();
    y = 15;
  }
  y = sectionLabel(doc, '8. Aprobación y Firmas', y, pageW);
  const firmaSlots = [
    { label: 'Docente Solicitante', detail: data.docente.nombres },
    { label: 'Monitor Seleccionado', detail: data.monitor ? data.monitor.nombres : '________________________' },
    { label: 'Jefe de Programa', detail: '________________________' },
    { label: 'Decano(a) de Facultad', detail: '________________________' },
  ];
  const firmaW = (pageW - 20) / firmaSlots.length;
  const firmaY = y;
  firmaSlots.forEach((s, i) => {
    const fx = 10 + i * firmaW;
    doc.setDrawColor(180, 180, 180);
    doc.setLineWidth(0.3);
    doc.rect(fx, firmaY, firmaW - 1, 28);
    doc.setFillColor(245, 242, 234);
    doc.rect(fx, firmaY, firmaW - 1, 6, 'F');
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...VINOTINTO);
    doc.text(s.label.toUpperCase(), fx + (firmaW - 1) / 2, firmaY + 4.2, { align: 'center' });
    doc.setDrawColor(120, 120, 120);
    doc.line(fx + 4, firmaY + 20, fx + firmaW - 5, firmaY + 20);
    const nameLines = doc.splitTextToSize(s.detail, firmaW - 8);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(40, 40, 40);
    doc.text(nameLines, fx + (firmaW - 1) / 2, firmaY + 24, { align: 'center' });
  });

  // Borde inferior vinotinto
  doc.setFillColor(...VINOTINTO);
  doc.rect(0, doc.internal.pageSize.height - 2, doc.internal.pageSize.width, 2, 'F');

  doc.save(`FO-14_Monitor_${data.asignatura.codigo}_${data.convocatoria.periodo_academico}.pdf`);
}

// ─────────────────────────────────────────────────────────────────
// CONSENTIMIENTO INFORMADO — Práctica Extramural (por estudiante)
// ─────────────────────────────────────────────────────────────────
type AutoTableDoc = jsPDF & { lastAutoTable: { finalY: number } };

function addPageFooter(doc: jsPDF, pageNum: number, totalPages: number) {
  const pageW = doc.internal.pageSize.width;
  const pageH = doc.internal.pageSize.height;
  doc.setFillColor(...VINOTINTO);
  doc.rect(0, pageH - 8, pageW, 8, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(255, 255, 255);
  doc.text('Universidad Surcolombiana — Vicerrectoría Académica', 12, pageH - 3.5);
  doc.text(`Página ${pageNum} de ${totalPages}`, pageW - 12, pageH - 3.5, { align: 'right' });
}

const LABEL_STYLE = { fontStyle: 'bold' as const, fillColor: [245, 242, 234] as [number, number, number], textColor: [60, 60, 60] as [number, number, number], cellPadding: { top: 2, bottom: 2, left: 3, right: 2 } };
const VALUE_STYLE = { fontStyle: 'normal' as const, textColor: [20, 20, 20] as [number, number, number], cellPadding: { top: 2, bottom: 2, left: 3, right: 2 } };

export function generarConsentimientoPDF(data: {
  estudiante: { nombres: string; codigo: string; cedula: string; programa?: string | null };
  practica: { id: number; nombre: string; periodo_academico: string; fecha_inicio?: string | null; fecha_fin?: string | null; duracion_dias: number; num_alumnos: number; observaciones?: string | null };
  asignatura: { nombre: string; codigo: string; programa: string; facultad?: string | null };
  docente: { nombres: string; email: string };
  origen: string; origen_municipio: string;
  destino: string; destino_municipio: string;
  rutas: Array<{ orden: number; tipo_punto: string; lugar: string; municipio?: string | null; distancia_km?: number | null }>;
  fecha_firma?: string | null;
  ip_firma?: string | null;
}) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' }) as AutoTableDoc;
  const pageW = doc.internal.pageSize.width;
  const pageH = doc.internal.pageSize.height;
  const MARGIN = 12;
  const CONTENT_W = pageW - MARGIN * 2;

  const now = new Date();
  const fechaHoy = now.toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });
  const anio = now.getFullYear();
  const refDoc = `NR-CI-${data.estudiante.codigo}-${data.practica.id}-${anio}`;

  const fmtDate = (iso?: string | null) => {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  // ── CABECERA ─────────────────────────────────────────────────────────────────
  let y = drawHeader(doc, 'CONSENTIMIENTO INFORMADO — PRÁCTICA EXTRAMURAL', 'MI-FOR-FO-15-C', '1', fechaHoy);

  // Número de referencia del documento
  doc.setFillColor(245, 242, 234);
  doc.rect(MARGIN, y, CONTENT_W, 7, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CONTENT_W, 7);
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(100, 70, 20);
  doc.text('N° Referencia:', MARGIN + 3, y + 4.5);
  doc.setFont('helvetica', 'normal');
  doc.text(refDoc, MARGIN + 32, y + 4.5);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(120, 120, 120);
  doc.text(
    'Este documento certifica que el/la estudiante ha otorgado su consentimiento informado para participar en la práctica extramural.',
    pageW - MARGIN - 3, y + 4.5, { align: 'right', maxWidth: CONTENT_W - 95 }
  );
  y += 11;

  // ── SECCIÓN 1: IDENTIFICACIÓN DEL ESTUDIANTE ─────────────────────────────────
  y = sectionLabel(doc, '1. Identificación del Estudiante', y, pageW);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Nombre completo', styles: LABEL_STYLE },
        { content: data.estudiante.nombres, styles: { ...VALUE_STYLE, cellWidth: 'auto' } },
        { content: 'Código estudiantil', styles: LABEL_STYLE },
        { content: data.estudiante.codigo, styles: VALUE_STYLE },
      ],
      [
        { content: 'Cédula de ciudadanía', styles: LABEL_STYLE },
        { content: data.estudiante.cedula, styles: VALUE_STYLE },
        { content: 'Programa académico', styles: LABEL_STYLE },
        { content: data.estudiante.programa ?? data.asignatura.programa, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 42 }, 2: { cellWidth: 38 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── SECCIÓN 2: DATOS DE LA PRÁCTICA ──────────────────────────────────────────
  y = sectionLabel(doc, '2. Información de la Práctica Extramural', y, pageW);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Nombre de la práctica', styles: LABEL_STYLE },
        { content: data.practica.nombre, styles: { ...VALUE_STYLE, cellWidth: 'auto' } },
        { content: 'Período académico', styles: LABEL_STYLE },
        { content: data.practica.periodo_academico, styles: VALUE_STYLE },
      ],
      [
        { content: 'Asignatura', styles: LABEL_STYLE },
        { content: data.asignatura.nombre, styles: VALUE_STYLE },
        { content: 'Código asignatura', styles: LABEL_STYLE },
        { content: data.asignatura.codigo, styles: VALUE_STYLE },
      ],
      [
        { content: 'Facultad', styles: LABEL_STYLE },
        { content: data.asignatura.facultad ?? '—', styles: VALUE_STYLE },
        { content: 'Docente responsable', styles: LABEL_STYLE },
        { content: data.docente.nombres, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 42 }, 2: { cellWidth: 38 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── SECCIÓN 3: FECHAS Y LUGAR ─────────────────────────────────────────────────
  y = sectionLabel(doc, '3. Fechas y Lugar de la Práctica', y, pageW);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Fecha de inicio', styles: LABEL_STYLE },
        { content: fmtDate(data.practica.fecha_inicio), styles: VALUE_STYLE },
        { content: 'Fecha de finalización', styles: LABEL_STYLE },
        { content: fmtDate(data.practica.fecha_fin), styles: VALUE_STYLE },
      ],
      [
        { content: 'Duración', styles: LABEL_STYLE },
        { content: `${data.practica.duracion_dias} día(s)`, styles: VALUE_STYLE },
        { content: 'N° de participantes', styles: LABEL_STYLE },
        { content: String(data.practica.num_alumnos), styles: VALUE_STYLE },
      ],
      [
        { content: 'Lugar de origen', styles: LABEL_STYLE },
        { content: `${data.origen}${data.origen_municipio ? ' — ' + data.origen_municipio : ''}`, styles: VALUE_STYLE },
        { content: 'Lugar de destino', styles: LABEL_STYLE },
        { content: `${data.destino}${data.destino_municipio ? ' — ' + data.destino_municipio : ''}`, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 42 }, 2: { cellWidth: 38 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── SECCIÓN 4: ITINERARIO ─────────────────────────────────────────────────────
  if (data.rutas.length > 0) {
    y = sectionLabel(doc, '4. Itinerario de la Práctica', y, pageW);
    autoTable(doc, {
      startY: y,
      margin: { left: MARGIN, right: MARGIN },
      head: [[
        { content: '#', styles: { halign: 'center' } },
        'Tipo de Punto',
        'Lugar / Sitio',
        'Municipio',
        { content: 'Distancia', styles: { halign: 'right' } },
      ]],
      body: data.rutas.map(r => [
        { content: r.orden, styles: { halign: 'center' } },
        r.tipo_punto === 'origen' ? 'Origen' : r.tipo_punto === 'destino' ? 'Destino' : 'Intermedio',
        r.lugar,
        r.municipio ?? '—',
        { content: r.distancia_km != null ? `${r.distancia_km.toFixed(1)} km` : '—', styles: { halign: 'right' } },
      ]),
      styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3 },
      headStyles: { fillColor: GRIS, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 8 },
      alternateRowStyles: { fillColor: [249, 249, 249] },
      columnStyles: { 0: { cellWidth: 12 }, 1: { cellWidth: 28 }, 4: { cellWidth: 24 } },
      theme: 'grid',
    });
    y = doc.lastAutoTable.finalY + 5;
  }

  // ── SECCIÓN 5: DECLARACIÓN DE CONSENTIMIENTO ──────────────────────────────────
  const declaracionH = 62;
  if (y + declaracionH > pageH - 15) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '5. Declaración de Consentimiento', y, pageW);

  // Marco de la declaración
  doc.setDrawColor(...VINOTINTO);
  doc.setLineWidth(0.4);
  doc.rect(MARGIN, y, CONTENT_W, declaracionH);
  doc.setFillColor(252, 250, 248);
  doc.rect(MARGIN, y, CONTENT_W, declaracionH, 'F');
  doc.setDrawColor(...VINOTINTO);
  doc.rect(MARGIN, y, CONTENT_W, declaracionH);

  // Línea decorativa izquierda
  doc.setFillColor(...VINOTINTO);
  doc.rect(MARGIN, y, 1.5, declaracionH, 'F');

  const prog = data.estudiante.programa ?? data.asignatura.programa;
  const declaracion = `Yo, ${data.estudiante.nombres}, identificado(a) con cédula de ciudadanía N° ${data.estudiante.cedula}, estudiante del programa de ${prog} de la Universidad Surcolombiana, en pleno uso de mis facultades y de manera libre y voluntaria,`;

  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  const introLines = doc.splitTextToSize(declaracion, CONTENT_W - 12);
  let ty = y + 5;
  doc.text(introLines, MARGIN + 5, ty);
  ty += introLines.length * 4.5 + 2;

  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...VINOTINTO);
  doc.text('MANIFIESTO Y CONSIENTO:', MARGIN + 5, ty);
  ty += 6;

  const items = [
    'Fui debidamente informado(a) sobre los objetivos, actividades, itinerario y condiciones de la práctica extramural.',
    'Conozco los lugares, fechas y medios de transporte que se utilizarán durante la práctica.',
    'Acepto participar voluntariamente y me comprometo a cumplir las normas de seguridad y convivencia.',
    'Autorizo a la Universidad Surcolombiana el registro de actividades académicas con fines institucionales.',
    'En caso de emergencia, autorizo al docente responsable a tomar decisiones pertinentes para mi seguridad.',
  ];
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.setFontSize(8);
  items.forEach((item, idx) => {
    const lines = doc.splitTextToSize(`${idx + 1}. ${item}`, CONTENT_W - 15);
    doc.text(lines, MARGIN + 6, ty);
    ty += lines.length * 4.2 + 0.5;
  });
  y += declaracionH + 5;

  // ── SECCIÓN 6: REGISTRO DE FIRMA DIGITAL ──────────────────────────────────────
  if (y > pageH - 65) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '6. Registro de Firma Digital', y, pageW);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Método de firma', styles: LABEL_STYLE },
        { content: 'Firma electrónica — Sistema SIPAM-USCO', styles: VALUE_STYLE },
        { content: 'Documento de referencia', styles: LABEL_STYLE },
        { content: refDoc, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
      ],
      [
        { content: 'Fecha y hora de firma', styles: LABEL_STYLE },
        { content: data.fecha_firma ?? 'No registrada', styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
        { content: 'Dirección IP registrada', styles: LABEL_STYLE },
        { content: data.ip_firma ?? '—', styles: VALUE_STYLE },
      ],
      [
        { content: 'Validez legal', styles: LABEL_STYLE },
        {
          content: 'Conforme al Art. 7 de la Ley 527 de 1999 — Firma Electrónica con plena validez jurídica',
          colSpan: 3,
          styles: { ...VALUE_STYLE, fontStyle: 'italic', textColor: [80, 80, 80] },
        },
      ],
    ],
    styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 42 }, 2: { cellWidth: 38 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 6;

  // ── SECCIÓN 7: FIRMAS ─────────────────────────────────────────────────────────
  if (y > pageH - 52) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '7. Firmas', y, pageW);
  const sigH = 30;
  const sigW = (CONTENT_W - 6) / 3;
  const sigLabels = [
    { title: 'Estudiante', sub: data.estudiante.nombres, detail: `Cód. ${data.estudiante.codigo}` },
    { title: 'Docente Responsable', sub: data.docente.nombres, detail: data.docente.email },
    { title: 'Coordinador de Práctica', sub: '___________________________', detail: 'Cargo / Firma' },
  ];

  sigLabels.forEach((s, i) => {
    const sx = MARGIN + i * (sigW + 3);
    doc.setDrawColor(180, 180, 180);
    doc.setLineWidth(0.3);
    doc.rect(sx, y, sigW, sigH);

    // Header de la celda de firma
    doc.setFillColor(245, 242, 234);
    doc.rect(sx, y, sigW, 6, 'F');
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...VINOTINTO);
    doc.text(s.title.toUpperCase(), sx + sigW / 2, y + 4.2, { align: 'center' });

    // Línea de firma
    doc.setDrawColor(100, 100, 100);
    doc.setLineWidth(0.3);
    doc.line(sx + 6, y + sigH - 12, sx + sigW - 6, y + sigH - 12);

    // Nombre y detalle
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(40, 40, 40);
    const nameLines = doc.splitTextToSize(s.sub, sigW - 8);
    doc.text(nameLines, sx + sigW / 2, y + sigH - 8, { align: 'center' });
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(120, 120, 120);
    doc.setFontSize(6.5);
    doc.text(s.detail, sx + sigW / 2, y + sigH - 3.5, { align: 'center' });
  });
  y += sigH + 5;

  // Nota legal al pie
  if (y < pageH - 20) {
    doc.setFillColor(245, 245, 245);
    doc.rect(MARGIN, y, CONTENT_W, 8, 'F');
    doc.setDrawColor(200, 200, 200);
    doc.rect(MARGIN, y, CONTENT_W, 8);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(120, 120, 120);
    doc.text(
      'Documento generado por el Sistema de Información de Prácticas y Monitorias (SIPAM-USCO). Conservar original firmado en la carpeta de la asignatura.',
      MARGIN + 3, y + 3.2
    );
    doc.text(
      'Resolución Rectoría N° 0142-2019 — Ley 527/1999 Art. 7 — Acuerdo 003/2012 USCO',
      MARGIN + 3, y + 6.5
    );
  }

  // ── FOOTERS ────────────────────────────────────────────────────────────────────
  const totalPages = (doc.internal as unknown as { getNumberOfPages: () => number }).getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    addPageFooter(doc, p, totalPages);
  }

  doc.save(`Consentimiento_${data.estudiante.codigo}_Practica${data.practica.id}.pdf`);
}

// ─────────────────────────────────────────────────────────────────
// MI-FOR-FO-16  Justificación Prácticas Extramuros (3 páginas)
// ─────────────────────────────────────────────────────────────────
const CARACTER_LABEL: Record<string, string> = {
  teorico: 'Teórico',
  teorico_practico: 'Teórico Práctico',
};
const CARACTERISTICA_LABEL: Record<string, string> = {
  especifico: 'Específico',
  facultad: 'De Facultad',
  institucional: 'Institucional',
  componente_flexible: 'Componente Flexible',
};

function checkRow(doc: jsPDF, options: string[], selected: string | null | undefined, x: number, y: number, colW = 40) {
  doc.setFontSize(8);
  options.forEach((opt, i) => {
    const cx = x + i * colW;
    const isSelected = selected === opt;
    doc.setDrawColor(...VINOTINTO);
    doc.setLineWidth(0.4);
    doc.rect(cx, y - 3, 4, 4);
    if (isSelected) {
      doc.setFillColor(...VINOTINTO);
      doc.rect(cx + 0.5, y - 2.5, 3, 3, 'F');
    }
    doc.setFont('helvetica', isSelected ? 'bold' : 'normal');
    doc.setTextColor(isSelected ? VINOTINTO[0] : 40, isSelected ? VINOTINTO[1] : 40, isSelected ? VINOTINTO[2] : 40);
    doc.text(opt, cx + 5.5, y);
  });
}

export function generarFO16(data: {
  practica: {
    id: number; nombre: string; periodo_academico: string;
    fecha_inicio?: string | null; fecha_fin?: string | null; duracion_dias: number;
    num_alumnos: number; hora_salida?: string | null; hora_llegada?: string | null;
    caracter_curso?: string | null; caracteristica_curso?: string | null;
    modalidad_docente?: string | null;
    articulacion_curso?: string | null; descripcion_practica?: string | null;
    justificacion?: string | null; metodologia?: string | null;
    carta_autorizacion_empresa?: string | null;
    evaluacion?: string | null; observaciones?: string | null;
    informe_resultados?: string | null; fecha_informe?: string | null;
  };
  asignatura: { nombre: string; codigo: string; creditos: number; semestre: number; programa: string; facultad?: string | null };
  docente: { nombres: string; cedula: string; email: string };
  rutas: Array<{ orden: number; tipo_punto: string; lugar: string; municipio?: string | null; departamento?: string | null; distancia_km?: number | null; vereda?: string | null }>;
}) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' }) as AutoTableDoc;
  const pageW = doc.internal.pageSize.width;
  const pageH = doc.internal.pageSize.height;
  const MARGIN = 12;
  const CW = pageW - MARGIN * 2;
  const fechaHoy = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

  const fmtDate = (iso?: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };
  const fmtDateShort = (iso?: string | null) => {
    if (!iso) return 'dd-mm-aa';
    const d = new Date(iso);
    return `${String(d.getDate()).padStart(2,'0')}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getFullYear()).slice(-2)}`;
  };

  // ── PÁGINA 1 ─────────────────────────────────────────────────────────────────
  let y = drawHeader(doc, 'JUSTIFICACIÓN PRÁCTICAS EXTRAMUROS', 'MI-FOR-FO-16', '7', fechaHoy);

  // Versión / Vigencia banner
  doc.setFillColor(245, 242, 234);
  doc.rect(MARGIN, y, CW, 6, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CW, 6);
  doc.setFontSize(7);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(120, 100, 40);
  doc.text('Vigencia 2025 · La versión controlada se consulta en www.usco.edu.co — Sistema Gestión de Calidad', MARGIN + 3, y + 4);
  y += 9;

  // ── Bloque 1: datos del curso ─────────────────────────────────────────────
  y = sectionLabel(doc, '1. Datos del Curso y Práctica', y, pageW);

  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Nombre del Curso / Asignatura', styles: LABEL_STYLE },
        { content: data.asignatura.nombre, colSpan: 3, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
      ],
      [
        { content: 'Código del Curso', styles: LABEL_STYLE },
        { content: data.asignatura.codigo, styles: VALUE_STYLE },
        { content: 'Semestre', styles: LABEL_STYLE },
        { content: `${data.asignatura.semestre}°`, styles: VALUE_STYLE },
      ],
      [
        { content: 'Nombre de la Práctica Extramuros', styles: LABEL_STYLE },
        { content: data.practica.nombre, colSpan: 3, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
      ],
      [
        { content: 'Período Académico', styles: LABEL_STYLE },
        { content: data.practica.periodo_academico, styles: VALUE_STYLE },
        { content: 'Cupo máx. de estudiantes', styles: LABEL_STYLE },
        { content: String(data.practica.num_alumnos), styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 55 }, 2: { cellWidth: 45 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 3;

  // ── Carácter del Curso ────────────────────────────────────────────────────
  doc.setDrawColor(200, 200, 200);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CW, 10);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text('Carácter del Curso:', MARGIN + 2, y + 4);
  doc.setFont('helvetica', 'normal');
  const caracterOptions = ['Teórico', 'Teórico Práctico'];
  const selectedCaracter = data.practica.caracter_curso ? CARACTER_LABEL[data.practica.caracter_curso] : null;
  checkRow(doc, caracterOptions, selectedCaracter, MARGIN + 50, y + 4, 42);
  y += 12;

  // ── Característica del Curso ──────────────────────────────────────────────
  doc.rect(MARGIN, y, CW, 10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text('Característica del Curso:', MARGIN + 2, y + 4);
  doc.setFont('helvetica', 'normal');
  const caracteristicaOptions = ['Específico', 'De Facultad', 'Institucional', 'Componente Flexible'];
  const selectedCaracteristica = data.practica.caracteristica_curso ? CARACTERISTICA_LABEL[data.practica.caracteristica_curso] : null;
  checkRow(doc, caracteristicaOptions, selectedCaracteristica, MARGIN + 55, y + 4, 38);
  y += 12;

  // ── Bloque 2: datos del docente ───────────────────────────────────────────
  y = sectionLabel(doc, '2. Datos del Docente', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Nombre del Docente', styles: LABEL_STYLE },
        { content: data.docente.nombres, colSpan: 3, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
      ],
      [
        { content: 'Programa / Departamento', styles: LABEL_STYLE },
        { content: data.asignatura.programa, styles: VALUE_STYLE },
        { content: 'Facultad', styles: LABEL_STYLE },
        { content: data.asignatura.facultad ?? '—', styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 55 }, 2: { cellWidth: 30 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 3;

  // ── Modalidad del Docente ─────────────────────────────────────────────────
  doc.setDrawColor(200, 200, 200);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CW, 10);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text('Modalidad:', MARGIN + 2, y + 4);
  const modalidadOpts = ['TCP', 'TCO', 'MTP', 'MTO', 'CAT'];
  checkRow(doc, modalidadOpts, data.practica.modalidad_docente, MARGIN + 28, y + 4, 33);
  y += 12;

  // ── Bloque 3: fechas y horarios ───────────────────────────────────────────
  y = sectionLabel(doc, '3. Fechas y Horarios de la Práctica', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Fecha de inicio', styles: LABEL_STYLE },
        { content: `${fmtDateShort(data.practica.fecha_inicio)}  ${data.practica.hora_salida ?? '—'}`, styles: VALUE_STYLE },
        { content: 'Fecha de finalización', styles: LABEL_STYLE },
        { content: `${fmtDateShort(data.practica.fecha_fin)}  ${data.practica.hora_llegada ?? '—'}`, styles: VALUE_STYLE },
      ],
      [
        { content: 'Duración en días', styles: LABEL_STYLE },
        { content: `${data.practica.duracion_dias} día(s)`, styles: VALUE_STYLE },
        { content: 'Horario de Salida de la Universidad', styles: LABEL_STYLE },
        { content: data.practica.hora_salida ?? '—', styles: VALUE_STYLE },
      ],
      [
        { content: 'Horario de Llegada a la Universidad', styles: LABEL_STYLE },
        { content: data.practica.hora_llegada ?? '—', styles: VALUE_STYLE },
        { content: 'Fecha de realización', styles: LABEL_STYLE },
        { content: `${fmtDate(data.practica.fecha_inicio)} al ${fmtDate(data.practica.fecha_fin)}`, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 55 }, 2: { cellWidth: 55 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── PÁGINA 2 — Itinerario día por día ─────────────────────────────────────
  doc.addPage();
  y = drawHeader(doc, 'JUSTIFICACIÓN PRÁCTICAS EXTRAMUROS', 'MI-FOR-FO-16', '7', fechaHoy);
  doc.setFillColor(245, 242, 234);
  doc.rect(MARGIN, y, CW, 6, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(120, 100, 40);
  doc.text('Sitio de realización de la práctica (Ruta) — Describa hora, lugar, municipio y dirección exacta día por día', MARGIN + 3, y + 4);
  y += 9;

  y = sectionLabel(doc, '4. Itinerario Día por Día', y, pageW);

  // Agrupar rutas por día (duracion_dias define el número de días)
  const nDias = data.practica.duracion_dias || 1;
  const rutasOrdenadas = [...data.rutas].sort((a, b) => a.orden - b.orden);
  const origen = rutasOrdenadas.find(r => r.tipo_punto === 'origen') || rutasOrdenadas[0];
  const destino = rutasOrdenadas.find(r => r.tipo_punto === 'destino') || rutasOrdenadas[rutasOrdenadas.length - 1];
  const intermedios = rutasOrdenadas.filter(r => r.tipo_punto === 'intermedio');

  for (let dia = 1; dia <= Math.min(nDias, 6); dia++) {
    if (y > pageH - 50) { doc.addPage(); y = 15; }
    // Header del día
    doc.setFillColor(...GRIS);
    doc.rect(MARGIN, y, CW, 5.5, 'F');
    doc.setFontSize(8);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(255, 255, 255);
    doc.text(`DÍA ${dia}`, MARGIN + 3, y + 3.8);
    y += 6.5;

    const fechaDia = data.practica.fecha_inicio
      ? new Date(new Date(data.practica.fecha_inicio).getTime() + (dia - 1) * 86400000)
      : null;
    const fechaDiaStr = fechaDia
      ? fechaDia.toLocaleDateString('es-CO', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
      : '';

    // Lugar de salida
    const esUltimoDia = dia === nDias;
    const salida = dia === 1 ? origen : (intermedios[dia - 2] || origen);
    const llegada = esUltimoDia ? destino : (intermedios[dia - 1] || destino);

    autoTable(doc, {
      startY: y, margin: { left: MARGIN, right: MARGIN },
      body: [
        [
          { content: 'Fecha', styles: LABEL_STYLE },
          { content: fechaDiaStr, colSpan: 3, styles: VALUE_STYLE },
        ],
        [
          { content: 'Lugar de salida', styles: LABEL_STYLE },
          { content: salida?.lugar ?? '—', styles: VALUE_STYLE },
          { content: 'Municipio', styles: LABEL_STYLE },
          { content: salida?.municipio ?? '—', styles: VALUE_STYLE },
        ],
        [
          { content: 'Lugar de llegada', styles: LABEL_STYLE },
          { content: llegada?.lugar ?? '—', styles: VALUE_STYLE },
          { content: 'Municipio', styles: LABEL_STYLE },
          { content: llegada?.municipio ?? '—', styles: VALUE_STYLE },
        ],
        [
          { content: 'Departamento / Dirección', styles: LABEL_STYLE },
          { content: llegada?.departamento ?? '—', styles: VALUE_STYLE },
          { content: 'Vereda / Rural', styles: LABEL_STYLE },
          { content: llegada?.vereda ?? '—', styles: VALUE_STYLE },
        ],
        [
          { content: 'Otras actividades / Hora salida al hotel', styles: LABEL_STYLE },
          { content: '—', colSpan: 3, styles: VALUE_STYLE },
        ],
      ],
      styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3 },
      columnStyles: { 0: { cellWidth: 50 }, 2: { cellWidth: 30 } },
      theme: 'grid',
    });
    y = doc.lastAutoTable.finalY + 4;
  }

  // Articulación
  if (y > pageH - 55) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '5. Articulación de la Práctica con el Área del Curso y con los Procesos de Evaluación', y, pageW);
  const artLines = doc.splitTextToSize(data.practica.articulacion_curso || '(No registrada)', CW - 6);
  const artH = Math.max(18, artLines.length * 4.5 + 8);
  doc.setFillColor(252, 250, 248);
  doc.rect(MARGIN, y, CW, artH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CW, artH);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(artLines, MARGIN + 3, y + 5);
  y += artH + 4;

  // Descripción de la práctica
  if (y > pageH - 45) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '6. Descripción de la Práctica', y, pageW);
  const descLines = doc.splitTextToSize(data.practica.descripcion_practica || '(No registrada)', CW - 6);
  const descH = Math.max(18, descLines.length * 4.5 + 8);
  doc.setFillColor(252, 250, 248);
  doc.rect(MARGIN, y, CW, descH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.rect(MARGIN, y, CW, descH);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(descLines, MARGIN + 3, y + 5);
  y += descH + 4;

  // ── Justificación (Art.3.e) ─────────────────────────────────────────────
  if (y > pageH - 45) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '7. Justificación de la Práctica — Art.3.e Acuerdo 003/2012', y, pageW);
  const justLines = doc.splitTextToSize(data.practica.justificacion || '(No registrada)', CW - 6);
  const justH = Math.max(18, justLines.length * 4.5 + 8);
  doc.setFillColor(252, 250, 248);
  doc.rect(MARGIN, y, CW, justH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.rect(MARGIN, y, CW, justH);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(justLines, MARGIN + 3, y + 5);
  y += justH + 4;

  // ── Metodología (Art.3.e) ─────────────────────────────────────────────────
  if (y > pageH - 45) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '8. Metodología de la Práctica — Art.3.e Acuerdo 003/2012', y, pageW);
  const metLines = doc.splitTextToSize(data.practica.metodologia || '(No registrada)', CW - 6);
  const metH = Math.max(18, metLines.length * 4.5 + 8);
  doc.setFillColor(252, 250, 248);
  doc.rect(MARGIN, y, CW, metH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.rect(MARGIN, y, CW, metH);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(metLines, MARGIN + 3, y + 5);
  y += metH + 4;

  // ── PÁGINA 3 — Evaluación y firma ────────────────────────────────────────
  doc.addPage();
  y = drawHeader(doc, 'JUSTIFICACIÓN PRÁCTICAS EXTRAMUROS', 'MI-FOR-FO-16', '7', fechaHoy);

  // Evaluación
  y = sectionLabel(doc, '9. Evaluación', y, pageW);
  const evalLines = doc.splitTextToSize(data.practica.evaluacion || '(No registrada)', CW - 6);
  const evalH = Math.max(30, evalLines.length * 4.5 + 8);
  doc.setFillColor(252, 250, 248);
  doc.rect(MARGIN, y, CW, evalH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.rect(MARGIN, y, CW, evalH);
  doc.setFontSize(8.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(evalLines, MARGIN + 3, y + 5);
  y += evalH + 6;

  // Anexos
  y = sectionLabel(doc, '10. Anexos', y, pageW);
  const cartaOk = !!data.practica.carta_autorizacion_empresa;
  const anexosH = 22;
  doc.setFillColor(252, 250, 248);
  doc.rect(MARGIN, y, CW, anexosH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.rect(MARGIN, y, CW, anexosH);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(40, 40, 40);
  doc.setFont('helvetica', cartaOk ? 'bold' : 'normal');
  doc.setTextColor(cartaOk ? 21 : 40, cartaOk ? 128 : 40, cartaOk ? 61 : 40);
  doc.text((cartaOk ? '☑' : '□') + '  Carta de solicitud de autorización a la empresa/institución (Art.3.l) — ' + (cartaOk ? 'ADJUNTA en sistema' : 'Pendiente'), MARGIN + 4, y + 5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(40, 40, 40);
  doc.text('□  Consentimiento informado firmado por los estudiantes participantes (MI-FOR-FO-15-C).', MARGIN + 4, y + 11);
  doc.text('□  AP-INF-FO-05 Solicitud de Desplazamiento Vial.', MARGIN + 4, y + 17);
  y += 26;

  // Observaciones
  if (data.practica.observaciones) {
    y = sectionLabel(doc, '11. Observaciones', y, pageW);
    const obsLines = doc.splitTextToSize(data.practica.observaciones, CW - 6);
    const obsH = Math.max(12, obsLines.length * 4.5 + 6);
    doc.setFillColor(252, 250, 248);
    doc.rect(MARGIN, y, CW, obsH, 'F');
    doc.setDrawColor(200, 185, 155);
    doc.rect(MARGIN, y, CW, obsH);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(40, 40, 40);
    doc.text(obsLines, MARGIN + 3, y + 5);
    y += obsH + 6;
  }

  // Firma del docente
  if (y > pageH - 40) { doc.addPage(); y = 15; }
  y += 10;
  const firmaX = MARGIN + CW / 4;
  const firmaW2 = CW / 2;
  doc.setDrawColor(180, 180, 180);
  doc.setLineWidth(0.4);
  doc.line(firmaX, y, firmaX + firmaW2, y);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text('Firma del Docente', firmaX + firmaW2 / 2, y + 5, { align: 'center' });
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 100, 100);
  doc.text(data.docente.nombres, firmaX + firmaW2 / 2, y + 10, { align: 'center' });
  doc.setFontSize(7.5);
  doc.text(`C.C. ${data.docente.cedula}  ·  ${data.docente.email}`, firmaX + firmaW2 / 2, y + 15, { align: 'center' });

  // Firmas: Jefe de Programa y Decano
  y += 28;
  if (y > pageH - 40) { doc.addPage(); y = 15; }
  const firmaW3 = CW / 3 - 6;
  const posiciones = [MARGIN, MARGIN + CW / 3 + 3, MARGIN + (CW * 2) / 3 + 3];
  const etiquetas = ['Firma del Docente (Visto Bueno)', 'Firma del Jefe de Programa', 'Firma del Decano'];
  for (let i = 0; i < 3; i++) {
    const fx = posiciones[i];
    doc.setDrawColor(180, 180, 180);
    doc.setLineWidth(0.4);
    doc.line(fx, y, fx + firmaW3, y);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(60, 60, 60);
    doc.text(etiquetas[i], fx + firmaW3 / 2, y + 5, { align: 'center' });
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(140, 140, 140);
    doc.text('Nombre: ___________________________', fx, y + 11);
    doc.text('Fecha: ____________________________', fx, y + 17);
  }
  y += 22;

  // Footer normativo
  const pg3H = pageH;
  if (y + 30 < pg3H) {
    doc.setFillColor(245, 245, 245);
    doc.rect(MARGIN, pg3H - 15, CW, 8, 'F');
    doc.setDrawColor(200, 200, 200);
    doc.rect(MARGIN, pg3H - 15, CW, 8);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(120, 120, 120);
    doc.text('MI-FOR-FO-16 v7 · Acuerdo 003/2012 USCO · Prácticas Extramuros', MARGIN + 3, pg3H - 10.5);
    doc.text('Generado por SIPAM-USCO', pageW - MARGIN - 3, pg3H - 10.5, { align: 'right' });
  }

  doc.save(`FO-16_Justificacion_Practica${data.practica.id}_${data.practica.periodo_academico}.pdf`);
}


// ─────────────────────────────────────────────────────────────────
// MI-FOR-FO-15  Requerimiento Prácticas Extramuros
// ─────────────────────────────────────────────────────────────────
export function generarFO15(data: {
  practica: {
    id: number; nombre: string; periodo_academico: string; estado: string;
    fecha_inicio?: string | null; fecha_fin?: string | null; duracion_dias: number;
    num_alumnos: number; quorum_alcanzado: boolean; firmas_obtenidas: number;
    firmas_requeridas?: number | null; observaciones?: string | null;
    tipo_docente?: string | null; hora_salida?: string | null; hora_llegada?: string | null;
  };
  asignatura: { nombre: string; codigo: string; programa: string; facultad?: string | null };
  docente: { nombres: string; cedula: string; email: string };
  rutas: Array<{ orden: number; tipo_punto: string; lugar: string; municipio?: string | null; departamento?: string | null; distancia_km?: number | null }>;
  participantes: Array<{ nombres: string; codigo: string; cedula: string; fecha_firma?: string | null; eps?: string | null; arl?: string | null; fondo_pensiones?: string | null }>;
  viaticos: Array<{ descripcion: string; valor_dia: number; num_dias: number; num_personas: number; total: number }>;
  total_viaticos: number;
}) {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' }) as AutoTableDoc;
  const pageW = doc.internal.pageSize.width;
  const pageH = doc.internal.pageSize.height;
  const MARGIN = 12;
  const CONTENT_W = pageW - MARGIN * 2;

  const now = new Date();
  const fechaHoy = now.toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });
  const anio = now.getFullYear();
  const refDoc = `NR-FO15-${data.practica.id}-${data.practica.periodo_academico}-${anio}`;

  const fmtDate = (iso?: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const estadoLabel: Record<string, string> = {
    borrador: 'Borrador', solicitada: 'Solicitada', pendiente_quorum: 'Pendiente Quórum',
    aprobada_curriculo: 'Aprobada Comité Currículo', aprobada_facultad: 'Avalada Consejo Facultad',
    aprobado_transporte: 'Aprobada Vicerrectoría', en_ejecucion: 'En Ejecución',
    finalizada: 'Finalizada', rechazada: 'Rechazada',
  };

  // ── CABECERA ─────────────────────────────────────────────────────────────────
  let y = drawHeader(doc, 'REQUERIMIENTO PRÁCTICAS EXTRAMUROS', 'MI-FOR-FO-15', '1', fechaHoy);

  // Número de referencia + aviso
  doc.setFillColor(245, 242, 234);
  doc.rect(MARGIN, y, CONTENT_W, 7, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.setLineWidth(0.3);
  doc.rect(MARGIN, y, CONTENT_W, 7);
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(100, 70, 20);
  doc.text('N° Referencia:', MARGIN + 3, y + 4.5);
  doc.setFont('helvetica', 'normal');
  doc.text(refDoc, MARGIN + 32, y + 4.5);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(120, 120, 120);
  doc.text(
    'Documento oficial — Acuerdo 003/2012 USCO · Requerimiento de Prácticas Extramuros',
    pageW - MARGIN - 3, y + 4.5, { align: 'right', maxWidth: CONTENT_W - 100 }
  );
  y += 11;

  // ── SECCIÓN 1: DATOS INSTITUCIONALES ─────────────────────────────────────────
  y = sectionLabel(doc, '1. Datos Institucionales', y, pageW);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Facultad', styles: LABEL_STYLE },
        { content: data.asignatura.facultad ?? 'No registrada', styles: VALUE_STYLE },
        { content: 'Programa académico', styles: LABEL_STYLE },
        { content: data.asignatura.programa, styles: VALUE_STYLE },
        { content: 'Período académico', styles: LABEL_STYLE },
        { content: data.practica.periodo_academico, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
      ],
      [
        { content: 'Nombre de la práctica', styles: LABEL_STYLE },
        { content: data.practica.nombre, colSpan: 3, styles: VALUE_STYLE },
        { content: 'Estado', styles: LABEL_STYLE },
        { content: estadoLabel[data.practica.estado] ?? data.practica.estado, styles: VALUE_STYLE },
      ],
      [
        { content: 'Asignatura', styles: LABEL_STYLE },
        { content: data.asignatura.nombre, styles: VALUE_STYLE },
        { content: 'Código asignatura', styles: LABEL_STYLE },
        { content: data.asignatura.codigo, styles: VALUE_STYLE },
        { content: 'Docente responsable', styles: LABEL_STYLE },
        { content: data.docente.nombres, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 40 }, 2: { cellWidth: 38 }, 4: { cellWidth: 40 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── SECCIÓN 2: DETALLE DE LA PRÁCTICA ────────────────────────────────────────
  y = sectionLabel(doc, '2. Detalle de la Práctica', y, pageW);
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    body: [
      [
        { content: 'Fecha de inicio', styles: LABEL_STYLE },
        { content: `${fmtDate(data.practica.fecha_inicio)}${data.practica.hora_salida ? '  ' + data.practica.hora_salida : ''}`, styles: VALUE_STYLE },
        { content: 'Fecha de finalización', styles: LABEL_STYLE },
        { content: `${fmtDate(data.practica.fecha_fin)}${data.practica.hora_llegada ? '  ' + data.practica.hora_llegada : ''}`, styles: VALUE_STYLE },
        { content: 'Duración', styles: LABEL_STYLE },
        { content: `${data.practica.duracion_dias} día(s)`, styles: VALUE_STYLE },
      ],
      [
        { content: 'Horario salida USCO', styles: LABEL_STYLE },
        { content: data.practica.hora_salida ?? '—', styles: VALUE_STYLE },
        { content: 'Horario llegada USCO', styles: LABEL_STYLE },
        { content: data.practica.hora_llegada ?? '—', styles: VALUE_STYLE },
        { content: 'Fecha de realización', styles: LABEL_STYLE },
        { content: `${fmtDate(data.practica.fecha_inicio)} al ${fmtDate(data.practica.fecha_fin)}`, styles: VALUE_STYLE },
      ],
      [
        { content: 'N° alumnos inscritos', styles: LABEL_STYLE },
        { content: String(data.practica.num_alumnos), styles: VALUE_STYLE },
        { content: 'Consentimientos', styles: LABEL_STYLE },
        { content: `${data.practica.firmas_obtenidas} / ${data.practica.firmas_requeridas ?? data.practica.num_alumnos}`, styles: VALUE_STYLE },
        { content: 'Quórum (≥66%)', styles: LABEL_STYLE },
        {
          content: data.practica.quorum_alcanzado ? 'SÍ — Alcanzado' : 'NO — Pendiente',
          styles: {
            ...VALUE_STYLE,
            fontStyle: 'bold',
            textColor: data.practica.quorum_alcanzado ? [21, 128, 61] as [number,number,number] : [180, 100, 0] as [number,number,number],
          },
        },
      ],
      [
        { content: 'Cédula docente', styles: LABEL_STYLE },
        { content: data.docente.cedula, styles: VALUE_STYLE },
        { content: 'Correo docente', styles: LABEL_STYLE },
        { content: data.docente.email, styles: VALUE_STYLE },
        { content: 'Tipo docente', styles: LABEL_STYLE },
        { content: data.practica.tipo_docente ? (TIPO_DOCENTE_LABEL[data.practica.tipo_docente] ?? data.practica.tipo_docente) : '—', styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 40 }, 2: { cellWidth: 38 }, 4: { cellWidth: 40 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── SECCIÓN 3: ITINERARIO ─────────────────────────────────────────────────────
  if (data.rutas.length > 0) {
    y = sectionLabel(doc, '3. Itinerario / Rutas', y, pageW);
    autoTable(doc, {
      startY: y,
      margin: { left: MARGIN, right: MARGIN },
      head: [['#', 'Tipo de Punto', 'Lugar / Sitio', 'Municipio', 'Departamento', 'Distancia (km)']],
      body: data.rutas.map(r => [
        { content: r.orden, styles: { halign: 'center' } },
        r.tipo_punto === 'origen' ? 'Origen' : r.tipo_punto === 'destino' ? 'Destino' : 'Intermedio',
        r.lugar,
        r.municipio ?? '—',
        r.departamento ?? '—',
        { content: r.distancia_km != null ? `${r.distancia_km.toFixed(1)} km` : '—', styles: { halign: 'right' } },
      ]),
      styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3 },
      headStyles: { fillColor: GRIS, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: [249, 249, 249] },
      columnStyles: { 0: { cellWidth: 12, halign: 'center' }, 1: { cellWidth: 30 }, 5: { cellWidth: 30, halign: 'right' } },
      theme: 'grid',
    });
    y = doc.lastAutoTable.finalY + 5;
  }

  // ── SECCIÓN 4: PARTICIPANTES — AP-INF-FO-05 ────────────────────────────────────
  y = sectionLabel(doc, '4. Participantes — Consentimiento Informado (AP-INF-FO-05)', y, pageW);
  const partBody = data.participantes.length > 0
    ? data.participantes.map((p, i) => [
        { content: i + 1, styles: { halign: 'center' as const } },
        p.codigo, p.nombres, p.cedula,
        p.eps ?? '—', p.arl ?? '—', p.fondo_pensiones ?? '—',
        { content: p.fecha_firma ?? '—', styles: { halign: 'center' as const } },
      ])
    : [[{ content: '—', styles: { halign: 'center' as const } }, '', 'Sin consentimientos registrados aún', '', '', '', '', '']];

  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    head: [['#', 'Código', 'Nombre completo', 'Cédula', 'EPS', 'ARL', 'F. Pensiones', 'Firma / Fecha']],
    body: partBody,
    styles: { fontSize: 7.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    headStyles: { fillColor: VINOTINTO, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 7.5 },
    alternateRowStyles: { fillColor: [248, 248, 248] },
    columnStyles: {
      0: { halign: 'center' as const, cellWidth: 10 },
      1: { cellWidth: 28 },
      3: { cellWidth: 26 },
      4: { cellWidth: 28 },
      5: { cellWidth: 28 },
      6: { cellWidth: 28 },
      7: { halign: 'center' as const, cellWidth: 32 },
    },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── SECCIÓN 5: VIÁTICOS ───────────────────────────────────────────────────────
  if (data.viaticos.length > 0) {
    if (y > pageH - 60) { doc.addPage(); y = 15; }
    y = sectionLabel(doc, '5. Viáticos Solicitados', y, pageW);
    autoTable(doc, {
      startY: y,
      margin: { left: MARGIN, right: MARGIN },
      head: [['Descripción del concepto', 'Valor / día', 'N° días', 'N° personas', 'Total']],
      body: [
        ...data.viaticos.map(v => [
          v.descripcion,
          { content: formatCOP(v.valor_dia), styles: { halign: 'right' as const } },
          { content: v.num_dias, styles: { halign: 'center' as const } },
          { content: v.num_personas, styles: { halign: 'center' as const } },
          { content: formatCOP(v.total), styles: { halign: 'right' as const, fontStyle: 'bold' as const } },
        ]),
        [
          { content: 'TOTAL GENERAL', colSpan: 4, styles: { ...LABEL_STYLE, halign: 'right' as const } },
          { content: formatCOP(data.total_viaticos), styles: { halign: 'right' as const, fontStyle: 'bold' as const, textColor: VINOTINTO } },
        ],
      ],
      styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
      headStyles: { fillColor: GRIS, textColor: [255, 255, 255], fontStyle: 'bold' },
      alternateRowStyles: { fillColor: [249, 249, 249] },
      theme: 'grid',
    });
    y = doc.lastAutoTable.finalY + 5;
  }

  // Observaciones
  if (data.practica.observaciones) {
    if (y > pageH - 30) { doc.addPage(); y = 15; }
    y = sectionLabel(doc, '6. Observaciones', y, pageW);
    doc.setFillColor(252, 250, 248);
    const obsLines = doc.splitTextToSize(data.practica.observaciones, CONTENT_W - 8);
    const obsH = Math.max(10, obsLines.length * 4.5 + 6);
    doc.rect(MARGIN, y, CONTENT_W, obsH, 'F');
    doc.setDrawColor(200, 185, 155);
    doc.setLineWidth(0.3);
    doc.rect(MARGIN, y, CONTENT_W, obsH);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(40, 40, 40);
    doc.text(obsLines, MARGIN + 4, y + 5);
    y += obsH + 5;
  }

  // ── SECCIÓN FIRMAS ────────────────────────────────────────────────────────────
  const secNum = data.practica.observaciones ? '7' : '6';
  if (y > pageH - 52) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, `${secNum}. Aprobación y Firmas`, y, pageW);
  const sigH = 30;
  const sigW = (CONTENT_W - 6) / 4;
  const sigLabels = [
    { title: 'Docente Responsable', sub: data.docente.nombres, detail: data.docente.cedula },
    { title: 'Jefe de Programa', sub: '___________________________', detail: 'Firma / Fecha' },
    { title: 'Decano(a) de Facultad', sub: '___________________________', detail: 'Firma / Fecha' },
    { title: 'Vicerrectoría Académica', sub: '___________________________', detail: 'Firma / Fecha' },
  ];

  sigLabels.forEach((s, i) => {
    const sx = MARGIN + i * (sigW + 2);
    doc.setDrawColor(180, 180, 180);
    doc.setLineWidth(0.3);
    doc.rect(sx, y, sigW, sigH);
    doc.setFillColor(245, 242, 234);
    doc.rect(sx, y, sigW, 6, 'F');
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...VINOTINTO);
    doc.text(s.title.toUpperCase(), sx + sigW / 2, y + 4.2, { align: 'center' });
    doc.setDrawColor(100, 100, 100);
    doc.setLineWidth(0.3);
    doc.line(sx + 5, y + sigH - 12, sx + sigW - 5, y + sigH - 12);
    const nameLines = doc.splitTextToSize(s.sub, sigW - 6);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(40, 40, 40);
    doc.text(nameLines, sx + sigW / 2, y + sigH - 8, { align: 'center' });
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(120, 120, 120);
    doc.setFontSize(6);
    doc.text(s.detail, sx + sigW / 2, y + sigH - 3.5, { align: 'center' });
  });
  y += sigH + 5;

  // Nota normativa
  if (y < pageH - 12) {
    doc.setFillColor(245, 245, 245);
    doc.rect(MARGIN, y, CONTENT_W, 7, 'F');
    doc.setDrawColor(200, 200, 200);
    doc.rect(MARGIN, y, CONTENT_W, 7);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(120, 120, 120);
    doc.text(
      `Documento generado por SIPAM-USCO · N° Ref: ${refDoc}`,
      MARGIN + 3, y + 3
    );
    doc.text(
      'Acuerdo 003/2012 USCO — Resolución Rectoría N° 0142-2019 — Ley 30/1992 Art. 119',
      MARGIN + 3, y + 6.2
    );
  }

  // ── FOOTERS ────────────────────────────────────────────────────────────────────
  const totalPages = (doc.internal as unknown as { getNumberOfPages: () => number }).getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    addPageFooter(doc, p, totalPages);
  }

  doc.save(`FO-15_Practica_${data.practica.id}_${data.practica.periodo_academico}.pdf`);
}


// ─────────────────────────────────────────────────────────────────
// MI-FOR-FO-15  Requerimiento Prácticas Extramuros — CONSOLIDADO
// Formato exacto: 1 página landscape con tabla de todas las prácticas
// del programa académico (para Jefe de Programa)
// ─────────────────────────────────────────────────────────────────
export function generarFO15Consolidado(data: {
  facultad: string;
  programa: string;
  periodo_academico: string;
  sede?: string;
  jefe_nombre?: string;
  practicas: Array<{
    nombre: string;
    asignatura: string;
    asignatura_codigo: string;
    docente: string;
    fecha_inicio?: string | null;
    hora_salida?: string | null;
    fecha_fin?: string | null;
    hora_llegada?: string | null;
    ruta?: string | null;
    duracion_dias: number;
    num_alumnos: number;
  }>;
}) {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' }) as AutoTableDoc;
  const pageW = doc.internal.pageSize.width;
  const pageH = doc.internal.pageSize.height;
  const M = 10;
  const CW = pageW - M * 2;

  const now = new Date();
  const fechaHoy = now.toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });
  const anio = String(now.getFullYear());

  // ── CABECERA formato exacto universidad ────────────────────────
  // Left: USCO logo box
  doc.setDrawColor(...VINOTINTO);
  doc.setLineWidth(0.5);
  doc.rect(M, 4, 30, 23);
  doc.setFontSize(6.5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...VINOTINTO);
  doc.text('UNIVERSIDAD', M + 2, 10);
  doc.text('SURCOLOMBIANA', M + 2, 14);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(...GRIS);
  doc.setFontSize(5.5);
  doc.text('Neiva - Huila - Colombia', M + 2, 18);
  doc.text('www.usco.edu.co', M + 2, 21.5);

  // Center: red band “UNIVERSIDAD SURCOLOMBIANA / FORMACIÓN”
  const cx = M + 32;
  const rx = pageW - M - 50;
  const cw = rx - cx;
  doc.setFillColor(...VINOTINTO);
  doc.rect(cx, 4, cw, 12, 'F');
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text('UNIVERSIDAD SURCOLOMBIANA', cx + cw / 2, 10.5, { align: 'center' });
  doc.setFontSize(7);
  doc.text('FORMACIÓN', cx + cw / 2, 14.5, { align: 'center' });

  // Center: white section — main title
  doc.setFillColor(255, 255, 255);
  doc.setDrawColor(...VINOTINTO);
  doc.setLineWidth(0.4);
  doc.rect(cx, 16, cw, 11);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(20, 20, 20);
  doc.text('REQUERIMIENTO PRACTICAS EXTRAMUROS', cx + cw / 2, 23, { align: 'center' });

  // Right: code box (alternating red/white rows)
  doc.setDrawColor(...VINOTINTO);
  doc.setLineWidth(0.4);
  doc.rect(rx, 4, 50, 23);
  doc.setFontSize(5.5);
  doc.setFillColor(...VINOTINTO); doc.rect(rx, 4, 50, 5.5, 'F');
  doc.setFont('helvetica', 'bold'); doc.setTextColor(255, 255, 255);
  doc.text('CÓDIGO:', rx + 2, 8); doc.setFont('helvetica', 'normal'); doc.text('MI-FOR-FO-15', rx + 18, 8);
  doc.setFillColor(255, 255, 255); doc.rect(rx, 9.5, 50, 4.5, 'F');
  doc.setFont('helvetica', 'bold'); doc.setTextColor(40, 40, 40);
  doc.text('VERSIÓN:', rx + 2, 13); doc.setFont('helvetica', 'normal'); doc.text('8', rx + 22, 13);
  doc.setFillColor(...VINOTINTO); doc.rect(rx, 14, 50, 4.5, 'F');
  doc.setFont('helvetica', 'bold'); doc.setTextColor(255, 255, 255);
  doc.text('VIGENCIA:', rx + 2, 17.5); doc.setFont('helvetica', 'normal'); doc.text('2025', rx + 22, 17.5);
  doc.setFillColor(255, 255, 255); doc.rect(rx, 18.5, 50, 4.5, 'F');
  doc.setFont('helvetica', 'bold'); doc.setTextColor(40, 40, 40);
  doc.text('PÁGINA:', rx + 2, 22); doc.setFont('helvetica', 'normal'); doc.text('1 de 1', rx + 22, 22);

  // Full-width vinotinto code bar
  doc.setFillColor(...VINOTINTO);
  doc.rect(M, 27, pageW - M * 2, 6, 'F');
  doc.setFontSize(5.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(255, 255, 255);
  ['CÓDIGO', 'MI-FOR-FO-15', 'VERSIÓN', '8', 'VIGENCIA', '2025', 'PÁGINA', '1 de 1'].forEach((txt, i) => {
    const bw = (pageW - M * 2) / 8;
    doc.setFont('helvetica', i % 2 === 0 ? 'bold' : 'normal');
    doc.text(txt, M + i * bw + bw / 2, 31.2, { align: 'center' });
  });

  let y = 35;

  // ── Fila: Facultad / Programa / Período / Fecha / Año / Sede ────
  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    body: [
      [
        { content: 'FACULTAD', styles: LABEL_STYLE },
        { content: data.facultad, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
        { content: 'PROGRAMA:', styles: LABEL_STYLE },
        { content: data.programa, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
        { content: 'PERÍODO ACADÉMICO:', styles: LABEL_STYLE },
        { content: data.periodo_academico, styles: { ...VALUE_STYLE, fontStyle: 'bold', textColor: VINOTINTO } },
        { content: 'FECHA:', styles: LABEL_STYLE },
        { content: fechaHoy, styles: VALUE_STYLE },
        { content: 'AÑO:', styles: LABEL_STYLE },
        { content: anio, styles: VALUE_STYLE },
        { content: 'SEDE:', styles: LABEL_STYLE },
        { content: data.sede ?? 'Neiva', styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 7.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 20 }, 2: { cellWidth: 24 }, 4: { cellWidth: 30 }, 6: { cellWidth: 18 }, 8: { cellWidth: 14 }, 10: { cellWidth: 14 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 3;

  // ── Tabla de prácticas ───────────────────────────────────────────
  const estadoLabel: Record<string, string> = {
    borrador: 'Borrador', solicitada: 'Solicitada', pendiente_quorum: 'Pend. Quórum',
    aprobada_curriculo: 'Ap. Currículo', aprobada_facultad: 'Ap. Facultad',
    aprobado_transporte: 'Ap. Transporte', en_ejecucion: 'En Ejecución',
    finalizada: 'Finalizada', rechazada: 'Rechazada',
  };
  void estadoLabel;

  const tableBody = data.practicas.length > 0
    ? data.practicas.map((p, i) => [
        { content: i + 1, styles: { halign: 'center' as const } },
        p.nombre + (p.asignatura ? `\n${p.asignatura}` : ''),
        p.asignatura_codigo,
        p.docente,
        p.fecha_inicio ? `${p.fecha_inicio}\n${p.hora_salida ?? ''}` : '—',
        p.fecha_fin   ? `${p.fecha_fin}\n${p.hora_llegada ?? ''}` : '—',
        p.ruta ?? '—',
        { content: String(p.duracion_dias), styles: { halign: 'center' as const } },
        { content: String(p.num_alumnos),   styles: { halign: 'center' as const } },
        '',
        '',
      ])
    : [[{ content: '— Sin prácticas registradas para este período —', colSpan: 11, styles: { halign: 'center' as const, fontStyle: 'italic' as const, textColor: [120,120,120] as [number,number,number] } }]];

  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    head: [[
      { content: 'N°', styles: { halign: 'center' as const } },
      'NOMBRE DE LA PRÁCTICA Y EL CURSO',
      { content: 'N°\nASIG.', styles: { halign: 'center' as const } },
      'NOMBRE DEL PROFESOR',
      'FECHA Y HORA\nINICIO\n(DD/MM/AA)',
      'FECHA Y HORA\nFIN\n(DD/MM/AA)',
      'RUTA',
      { content: 'DURAC.\nEN\nDÍAS', styles: { halign: 'center' as const } },
      { content: 'No. DE\nALUMNOS', styles: { halign: 'center' as const } },
      'FECHA DE\nRECIBIDO',
      'FECHA DE\nREALIZACIÓN',
    ]],
    body: tableBody,
    styles: { fontSize: 7, lineColor: [200, 200, 200], lineWidth: 0.3, cellPadding: { top: 2, bottom: 2, left: 2, right: 2 } },
    headStyles: { fillColor: VINOTINTO, textColor: [255, 255, 255] as [number,number,number], fontStyle: 'bold', fontSize: 6.5, halign: 'center' },
    alternateRowStyles: { fillColor: [249, 249, 249] },
    columnStyles: {
      0:  { cellWidth: 9,  halign: 'center' as const },
      1:  { cellWidth: 58 },
      2:  { cellWidth: 18, halign: 'center' as const },
      3:  { cellWidth: 40 },
      4:  { cellWidth: 26, halign: 'center' as const },
      5:  { cellWidth: 26, halign: 'center' as const },
      6:  { cellWidth: 44 },
      7:  { cellWidth: 14, halign: 'center' as const },
      8:  { cellWidth: 16, halign: 'center' as const },
      9:  { cellWidth: 22, halign: 'center' as const },
      10: { cellWidth: 22, halign: 'center' as const },
    },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // ── Sección de firmas — formato exacto ─────────────────────────────
  if (y > pageH - 52) { y = pageH - 52; }

  // Cuadro Vicerrectoría (derecha) — FECHA RECIBIDO + FECHA REALIZACIÓN
  const vbX = M + CW / 2 + 2;
  const vbW = CW / 2 - 2;
  const vbH = 28;
  doc.setDrawColor(180, 180, 180);
  doc.setLineWidth(0.3);
  doc.rect(vbX, y, vbW, vbH);
  // Row 1 header
  doc.setFillColor(...VINOTINTO);
  doc.rect(vbX, y, vbW, 5, 'F');
  doc.setFontSize(5.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(255, 255, 255);
  doc.text('FECHA DE RECIBIDO', vbX + vbW * 0.25, y + 3.5, { align: 'center' });
  doc.text('FECHA DE REALIZACIÓN', vbX + vbW * 0.75, y + 3.5, { align: 'center' });
  // DD/MM/AA boxes row
  const boxW = 7, boxH = 5;
  const ry1 = y + 5;
  doc.setTextColor(80, 80, 80); doc.setFontSize(5);
  ['DD', 'MM', 'AA'].forEach((lbl, i) => {
    const bx1 = vbX + 8 + i * (boxW + 1);
    const bx2 = vbX + vbW / 2 + 8 + i * (boxW + 1);
    doc.setDrawColor(160, 160, 160); doc.rect(bx1, ry1, boxW, boxH); doc.rect(bx2, ry1, boxW, boxH);
    doc.text(lbl, bx1 + boxW / 2, ry1 + 3.5, { align: 'center' });
    doc.text(lbl, bx2 + boxW / 2, ry1 + 3.5, { align: 'center' });
  });
  // HORA row
  const ry2 = ry1 + boxH + 1;
  doc.setFontSize(5.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(40, 40, 40);
  doc.text('HORA', vbX + 2, ry2 + 4);
  doc.text('HORA', vbX + vbW / 2 + 2, ry2 + 4);
  doc.setDrawColor(160, 160, 160);
  doc.line(vbX + 12, ry2 + 4, vbX + vbW / 2 - 2, ry2 + 4);
  doc.line(vbX + vbW / 2 + 12, ry2 + 4, vbX + vbW - 2, ry2 + 4);
  // FIRMA row
  const ry3 = ry2 + 7;
  doc.setFontSize(5.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(...VINOTINTO);
  doc.text('FIRMA  EXCLUSIVO VICERRECTORÍA ACADÉMICA', vbX + 2, ry3 + 3.5, { maxWidth: vbW - 4 });

  // Vertical divider inside box
  doc.setDrawColor(180, 180, 180);
  doc.line(vbX + vbW / 2, y, vbX + vbW / 2, y + vbH);

  // Signatures row: JEFE (left) + DECANO (right)
  const sigY = y + vbH + 6;
  const sigW2 = (CW - 4) / 2;
  [{
    label: 'FIRMA DEL JEFE DE PROGRAMA',
    nombre: data.jefe_nombre ?? '___________________________________',
  }, {
    label: 'FIRMA DEL DECANO (A)',
    nombre: '___________________________________',
  }].forEach((s, i) => {
    const sx = M + i * (sigW2 + 4);
    doc.setDrawColor(120, 120, 120);
    doc.setLineWidth(0.4);
    doc.line(sx + 8, sigY, sx + sigW2 - 8, sigY);
    doc.setFontSize(7); doc.setFont('helvetica', 'bold'); doc.setTextColor(20, 20, 20);
    doc.text(s.label, sx + sigW2 / 2, sigY + 4.5, { align: 'center' });
    doc.setFontSize(6.5); doc.setFont('helvetica', 'normal'); doc.setTextColor(60, 60, 60);
    doc.text('NOMBRE', sx + 2, sigY + 10);
    doc.line(sx + 20, sigY + 10, sx + sigW2 - 4, sigY + 10);
    doc.setFontSize(7); doc.setFont('helvetica', 'normal');
    doc.text(s.nombre, sx + 22, sigY + 9.5, { maxWidth: sigW2 - 24 });
  });

  // Pie normativo
  doc.setFontSize(5.5);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(150, 150, 150);
  doc.text('Vigilada Mineducación  ·  La versión vigente de este documento se consulta en www.usco.edu.co, link Sistema Gestión de Calidad.  ·  Generado por SIPAM-USCO · ' + fechaHoy, M, pageH - 2.5, { maxWidth: CW });

  doc.save(`FO-15_Consolidado_${data.programa.replace(/\s+/g, '_')}_${data.periodo_academico}.pdf`);
}


// ─────────────────────────────────────────────────────────────────
// MI-FOR-FO-46  Convocatoria para Monitores (cartel público)
// ─────────────────────────────────────────────────────────────────
const TIPO_MON_LABEL: Record<string, string> = {
  nee: 'a) Acompañamiento NEE',
  regimenes_especiales: 'b) Regímenes Especiales',
  academica_cursos: 'c) Académica — Cursos/Asignaturas',
  laboratorios: 'd) Laboratorios',
  tic: 'e) TIC / Salas Informática',
  permanencia_graduacion: 'f) Permanencia y Graduación',
  deportiva: 'g) Deportiva',
  cultural: 'h) Cultural y Artística',
  biblioteca: 'i) Biblioteca',
  acreditacion: 'j) Acreditación',
  investigacion: 'k) Investigación / Proyección Social',
};

export function generarFO46(data: {
  convocatoria: {
    id: number; titulo: string; periodo_academico: string; tipo_monitoria: string;
    horas_semana: number; horas_semestre: number; descripcion_actividades?: string | null;
    promedio_minimo: number; creditos_minimo_pct: number;
    fecha_inicio_postulacion?: string | null; fecha_fin_postulacion?: string | null;
    num_monitores_requeridos?: number | null; sede?: string | null; estado: string;
  };
  asignatura: { nombre: string; codigo: string; creditos: number; semestre: number; programa: string; facultad?: string | null };
  docente: { nombres: string; cedula: string; email: string; programa?: string | null };
}) {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' }) as AutoTableDoc;
  const pageW = doc.internal.pageSize.width;
  const pageH = doc.internal.pageSize.height;
  const MARGIN = 12;
  const CW = pageW - MARGIN * 2;
  const fechaHoy = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

  const fmtDate = (iso?: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });
  };

  let y = drawHeader(doc, 'CONVOCATORIA PARA MONITORES', 'MI-FOR-FO-46', '1', fechaHoy);

  // Banner de período
  doc.setFillColor(...VINOTINTO);
  doc.rect(MARGIN, y, CW, 8, 'F');
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text(`PERÍODO ACADÉMICO ${data.convocatoria.periodo_academico}  ·  ${data.asignatura.programa}`, MARGIN + 4, y + 5.5);
  y += 11;

  // Título convocatoria
  doc.setFillColor(...OCRE_BG);
  doc.rect(MARGIN, y, CW, 12, 'F');
  doc.setDrawColor(...VINOTINTO);
  doc.setLineWidth(0.5);
  doc.rect(MARGIN, y, CW, 12);
  doc.setFontSize(13);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...VINOTINTO);
  const titleLines = doc.splitTextToSize(data.convocatoria.titulo, CW - 8);
  doc.text(titleLines, MARGIN + CW / 2, y + 7, { align: 'center' });
  y += 16;

  // Sección 1 — Datos institucionales
  y = sectionLabel(doc, '1. Información Institucional', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      [{ content: 'Facultad', styles: LABEL_STYLE }, { content: data.asignatura.facultad ?? 'Facultad de Ingeniería', styles: VALUE_STYLE },
       { content: 'Programa', styles: LABEL_STYLE }, { content: data.asignatura.programa, styles: VALUE_STYLE }],
      [{ content: 'Asignatura', styles: LABEL_STYLE }, { content: data.asignatura.nombre, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
       { content: 'Código', styles: LABEL_STYLE }, { content: data.asignatura.codigo, styles: VALUE_STYLE }],
      [{ content: 'Semestre', styles: LABEL_STYLE }, { content: `${data.asignatura.semestre}° semestre`, styles: VALUE_STYLE },
       { content: 'Créditos', styles: LABEL_STYLE }, { content: String(data.asignatura.creditos), styles: VALUE_STYLE }],
      [{ content: 'Docente responsable', styles: LABEL_STYLE }, { content: data.docente.nombres, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
       { content: 'Correo', styles: LABEL_STYLE }, { content: data.docente.email, styles: VALUE_STYLE }],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 40 }, 2: { cellWidth: 30 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // Sección 2 — Tipo y condiciones
  y = sectionLabel(doc, '2. Tipo de Monitoría y Condiciones', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      [{ content: 'Tipo de monitoría', styles: LABEL_STYLE },
       { content: TIPO_MON_LABEL[data.convocatoria.tipo_monitoria] ?? data.convocatoria.tipo_monitoria, colSpan: 3, styles: { ...VALUE_STYLE, fontStyle: 'bold' } }],
      [{ content: 'Horas / semana', styles: LABEL_STYLE }, { content: String(data.convocatoria.horas_semana), styles: VALUE_STYLE },
       { content: 'Horas / semestre', styles: LABEL_STYLE }, { content: String(data.convocatoria.horas_semestre), styles: VALUE_STYLE }],
      [{ content: 'N° monitores requeridos', styles: LABEL_STYLE }, { content: String(data.convocatoria.num_monitores_requeridos ?? 1), styles: VALUE_STYLE },
       { content: 'Sede', styles: LABEL_STYLE }, { content: data.convocatoria.sede ?? 'Neiva', styles: VALUE_STYLE }],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 45 }, 2: { cellWidth: 40 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // Sección 3 — Requisitos
  y = sectionLabel(doc, '3. Requisitos del Candidato — Acuerdo 012/2023', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      [{ content: 'Promedio acumulado mínimo', styles: LABEL_STYLE }, { content: data.convocatoria.promedio_minimo.toFixed(2), styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
       { content: '% créditos aprobados mínimo', styles: LABEL_STYLE }, { content: `${data.convocatoria.creditos_minimo_pct.toFixed(1)}%`, styles: { ...VALUE_STYLE, fontStyle: 'bold' } }],
      [{ content: 'Nota aprobatoria en la asignatura', styles: LABEL_STYLE }, { content: '≥ 3.0 (requerida)', styles: VALUE_STYLE },
       { content: 'Sin sanción disciplinaria vigente', styles: LABEL_STYLE }, { content: 'Obligatorio (Art.4.c)', styles: VALUE_STYLE }],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 55 }, 2: { cellWidth: 55 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // Sección 4 — Fechas postulación
  y = sectionLabel(doc, '4. Período de Postulación', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      [{ content: 'Apertura de postulaciones', styles: LABEL_STYLE }, { content: fmtDate(data.convocatoria.fecha_inicio_postulacion), styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
       { content: 'Cierre de postulaciones', styles: LABEL_STYLE }, { content: fmtDate(data.convocatoria.fecha_fin_postulacion), styles: { ...VALUE_STYLE, fontStyle: 'bold' } }],
    ],
    styles: { fontSize: 8.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    columnStyles: { 0: { cellWidth: 55 }, 2: { cellWidth: 40 } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // Sección 5 — Actividades
  if (data.convocatoria.descripcion_actividades) {
    y = sectionLabel(doc, '5. Actividades y Compromisos del Monitor', y, pageW);
    const actLines = doc.splitTextToSize(data.convocatoria.descripcion_actividades, CW - 6);
    const actH = Math.max(16, actLines.length * 4.5 + 8);
    doc.setFillColor(252, 250, 248);
    doc.rect(MARGIN, y, CW, actH, 'F');
    doc.setDrawColor(200, 185, 155);
    doc.setLineWidth(0.3);
    doc.rect(MARGIN, y, CW, actH);
    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(30, 30, 30);
    doc.text(actLines, MARGIN + 3, y + 5);
    y += actH + 5;
  }

  // Sección 6 — Criterios de selección
  y = sectionLabel(doc, '6. Criterios de Selección — RF-MON-05', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    head: [['Criterio', 'Ponderación']],
    body: [
      ['Nota obtenida en la asignatura', '30%'],
      ['Promedio académico acumulado', '30%'],
      ['Resultado de entrevista', '40%'],
    ],
    styles: { fontSize: 8.5 },
    headStyles: { fillColor: GRIS },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 5;

  // Sección 7 — Documentos a presentar
  if (y > pageH - 45) { doc.addPage(); y = 15; }
  y = sectionLabel(doc, '7. Documentos Requeridos', y, pageW);
  autoTable(doc, {
    startY: y, margin: { left: MARGIN, right: MARGIN },
    body: [
      ['1.', 'Fotocopia de cédula de ciudadanía'],
      ['2.', 'Certificado bancario (cuenta de ahorros activa)'],
      ['3.', 'RUT — Registro Único Tributario'],
      ['4.', 'Paz y salvo académico y financiero'],
    ],
    styles: { fontSize: 8.5 },
    columnStyles: { 0: { cellWidth: 12, halign: 'center' } },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 8;

  // Firma del docente
  if (y > pageH - 40) { doc.addPage(); y = 15; }
  const fX = MARGIN + CW / 4;
  const fW = CW / 2;
  doc.setDrawColor(150, 150, 150);
  doc.setLineWidth(0.4);
  doc.line(fX, y + 18, fX + fW, y + 18);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text('Docente Responsable', fX + fW / 2, y + 23, { align: 'center' });
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100, 100, 100);
  doc.setFontSize(7.5);
  doc.text(data.docente.nombres, fX + fW / 2, y + 28, { align: 'center' });
  doc.text(`C.C. ${data.docente.cedula}  ·  ${data.docente.email}`, fX + fW / 2, y + 32, { align: 'center' });

  // Footer normativo
  doc.setFillColor(245, 245, 245);
  doc.rect(MARGIN, pageH - 14, CW, 8, 'F');
  doc.setFontSize(6.5);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(120, 120, 120);
  doc.text('MI-FOR-FO-46 · Acuerdo 012/2023 USCO — Sistema SIPAM-USCO', MARGIN + 3, pageH - 9.5);
  doc.text(fechaHoy, pageW - MARGIN - 3, pageH - 9.5, { align: 'right' });

  doc.save(`FO-46_Convocatoria_${data.convocatoria.id}_${data.convocatoria.periodo_academico}.pdf`);
}


// ─────────────────────────────────────────────────────────────────
// AP-INF-FO-05  Solicitud de Desplazamiento Vial (Versión 7 · 2026)
// Formato exacto: 5 páginas (p1 datos, p2 plan vial, p3 reglamento+firmas, p4+ listado)
// ─────────────────────────────────────────────────────────────────
export function generarFO05(data: {
  practica: {
    id: number; nombre: string; periodo_academico: string;
    fecha_inicio?: string | null; fecha_fin?: string | null;
    hora_salida?: string | null; hora_llegada?: string | null;
    num_alumnos: number; duracion_dias: number;
    placa_vehiculo?: string | null; tipo_vehiculo?: string | null;
    empresa_transporte?: string | null; conductor_nombre?: string | null;
    observaciones?: string | null;
  };
  asignatura: { nombre: string; codigo: string; programa: string; facultad?: string | null };
  docente: { nombres: string; cedula: string; email: string };
  rutas: Array<{ orden: number; tipo_punto: string; lugar: string; municipio?: string | null; departamento?: string | null; distancia_km?: number | null }>;
  participantes: Array<{ nombres: string; codigo: string; cedula: string; eps?: string | null; arl?: string | null; fondo_pensiones?: string | null }>;
}) {
  const PER_PAGE = 16;
  const partPages = Math.max(1, Math.ceil(data.participantes.length / PER_PAGE));
  const totalPages = 4 + partPages;  // p1 datos + p2 plan vial + p3 reglamento + p4s lista + p5 consentimiento

  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' }) as AutoTableDoc;
  const pageW = 210;   // portrait A4
  const pageH = 297;
  const M = 10;
  const CW = pageW - M * 2;

  const now = new Date();
  const dd = String(now.getDate()).padStart(2, '0');
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const yyyy = String(now.getFullYear());
  const fechaHoy = now.toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

  const fmtDate = (iso?: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('es-CO', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  const origen = data.rutas.find(r => r.tipo_punto === 'origen') ?? data.rutas[0] ?? null;
  const destino = data.rutas.find(r => r.tipo_punto === 'destino') ?? (data.rutas.length > 0 ? data.rutas[data.rutas.length - 1] : null);
  const rutaIda = data.rutas.map(r => `${r.lugar}${r.municipio ? ' – ' + r.municipio : ''}`).join(' → ') || '—';
  const rutaRetorno = [...data.rutas].reverse().map(r => `${r.lugar}${r.municipio ? ' – ' + r.municipio : ''}`).join(' → ') || '—';

  function fo05Header(pageNum: number) {
    // USCO left box
    doc.setDrawColor(...VINOTINTO);
    doc.setLineWidth(0.5);
    doc.rect(M, 4, 42, 23);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...VINOTINTO);
    doc.text('UNIVERSIDAD', M + 3, 11);
    doc.text('SURCOLOMBIANA', M + 3, 15.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...GRIS);
    doc.setFontSize(6);
    doc.text('Neiva - Huila - Colombia', M + 3, 19.5);
    doc.text('www.usco.edu.co', M + 3, 23);

    // Center: process label + main title
    const w = doc.internal.pageSize.getWidth();
    const cx = M + 44;
    const cw = w - M - 52 - cx;
    doc.setDrawColor(200, 200, 200);
    doc.setLineWidth(0.3);
    doc.setFillColor(240, 240, 240);
    doc.rect(cx, 4, cw, 8, 'F');
    doc.rect(cx, 4, cw, 8);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(80, 80, 80);
    doc.text('GESTIÓN DE INFRAESTRUCTURA', cx + cw / 2, 9.5, { align: 'center' });

    doc.setFillColor(...OCRE_BG);
    doc.rect(cx, 12, cw, 15, 'F');
    doc.setDrawColor(...VINOTINTO);
    doc.rect(cx, 12, cw, 15);
    doc.setFontSize(8.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...VINOTINTO);
    const tLines = doc.splitTextToSize('SOLICITUD DESPLAZAMIENTO VIAL PARA PRÁCTICAS ACADÉMICAS Y OTRAS ACTIVIDADES RELACIONADAS', cw - 6);
    const tY = tLines.length > 1 ? 17 : 21;
    doc.text(tLines, cx + cw / 2, tY, { align: 'center' });

    // Right: code box
    const rx = w - M - 50;
    doc.setDrawColor(...VINOTINTO);
    doc.setLineWidth(0.4);
    doc.rect(rx, 4, 50, 23);
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(40, 40, 40);
    const col1 = rx + 2, col2 = rx + 22;
    doc.text('CÓDIGO:', col1, 9);   doc.setFont('h', 'normal'); doc.text('AP-INF-FO-05', col2, 9);
    doc.setFont('helvetica', 'bold');
    doc.text('VERSIÓN:', col1, 13);  doc.setFont('h', 'normal'); doc.text('7', col2, 13);
    doc.setFont('helvetica', 'bold');
    doc.text('VIGENCIA:', col1, 17); doc.setFont('h', 'normal'); doc.text('2026', col2, 17);
    doc.setFont('helvetica', 'bold');
    doc.text('PÁGINA:', col1, 21);   doc.setFont('h', 'normal'); doc.text(`${pageNum} de ${totalPages}`, col2, 21);

    // Separator
    doc.setDrawColor(...VINOTINTO);
    doc.setLineWidth(0.7);
    doc.line(M, 29, w - M, 29);
    return 32;
  }

  // ══════════════════════════════════════════════════════════════
  // PÁGINA 1 — Datos Generales
  // ══════════════════════════════════════════════════════════════
  let y = fo05Header(1);

  // Fecha
  doc.setFillColor(245, 245, 245);
  doc.rect(M, y, CW, 8, 'F');
  doc.setDrawColor(200, 200, 200);
  doc.setLineWidth(0.3);
  doc.rect(M, y, CW, 8);
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(60, 60, 60);
  doc.text('FECHA:', M + 3, y + 5.5);
  const boxes = [{ label: 'DÍA', val: dd, w: 16 }, { label: 'MES', val: mm, w: 16 }, { label: 'AÑO', val: yyyy, w: 22 }];
  let bx = M + 22;
  boxes.forEach(b => {
    doc.setDrawColor(180, 180, 180);
    doc.rect(bx, y + 1, b.w, 6);
    doc.setFontSize(5.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(120, 120, 120);
    doc.text(b.label, bx + b.w / 2, y + 3.2, { align: 'center' });
    doc.setFontSize(7);
    doc.setTextColor(20, 20, 20);
    doc.text(b.val, bx + b.w / 2, y + 6.5, { align: 'center' });
    bx += b.w + 3;
  });
  y += 10;

  // DATOS GENERALES header
  doc.setFillColor(...VINOTINTO);
  doc.rect(M, y, CW, 5.5, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text('DATOS GENERALES', M + 3, y + 3.8);
  y += 6.5;

  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    body: [
      [
        { content: 'NOMBRE DEL COORDINADOR DE LA ACTIVIDAD\nY/O ADMINISTRADOR DEL RIESGO', styles: { ...LABEL_STYLE, cellWidth: 72 } },
        { content: data.docente.nombres, colSpan: 2, styles: VALUE_STYLE },
        { content: 'No. TELÉFONO / CELULAR', styles: LABEL_STYLE },
        { content: data.docente.email, styles: VALUE_STYLE },
      ],
      [
        { content: 'NOMBRE DE LA ACTIVIDAD Y/O PRÁCTICA A DESARROLLAR\n(Si es Práctica Académica, indique asignatura y código)', styles: { ...LABEL_STYLE, cellWidth: 72 } },
        { content: data.practica.nombre, colSpan: 2, styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
        { content: 'ASIGNATURA / CÓDIGO', styles: LABEL_STYLE },
        { content: `${data.asignatura.nombre}  /  ${data.asignatura.codigo}`, styles: VALUE_STYLE },
      ],
      [
        { content: 'FACULTAD', styles: LABEL_STYLE },
        { content: data.asignatura.facultad ?? '—', styles: VALUE_STYLE },
        { content: 'PROGRAMA ACADÉMICO', styles: LABEL_STYLE },
        { content: data.asignatura.programa, colSpan: 2, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3 },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 2;

  // LUGAR DE ORIGEN / DESTINO
  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    body: [
      [
        { content: 'LUGAR DE ORIGEN', rowSpan: 2, styles: { ...LABEL_STYLE, valign: 'middle' as const, cellWidth: 38 } } as any,
        { content: 'SALIDA', styles: { ...LABEL_STYLE, halign: 'center' as const, cellWidth: 22 } },
        { content: `${fmtDate(data.practica.fecha_inicio)}  ${data.practica.hora_salida ?? ''}`, styles: VALUE_STYLE },
        { content: 'SEDE', styles: { ...LABEL_STYLE, cellWidth: 20 } },
        { content: origen ? (origen.municipio ?? origen.lugar) : 'Neiva', styles: VALUE_STYLE },
        { content: 'LUGAR DE DESTINO', rowSpan: 2, styles: { ...LABEL_STYLE, valign: 'middle' as const, cellWidth: 38 } } as any,
        { content: 'LLEGADA', styles: { ...LABEL_STYLE, halign: 'center' as const, cellWidth: 22 } },
        { content: `${fmtDate(data.practica.fecha_inicio)}  ${data.practica.hora_salida ?? ''}`, styles: VALUE_STYLE },
      ],
      [
        { content: 'LLEGADA', styles: { ...LABEL_STYLE, halign: 'center' as const } },
        { content: `${fmtDate(data.practica.fecha_fin)}  ${data.practica.hora_llegada ?? ''}`, styles: VALUE_STYLE },
        { content: 'SEDE', styles: LABEL_STYLE },
        { content: origen ? (origen.municipio ?? origen.lugar) : 'Neiva', styles: VALUE_STYLE },
        { content: 'SALIDA', styles: { ...LABEL_STYLE, halign: 'center' as const } },
        { content: `${fmtDate(data.practica.fecha_fin)}  ${data.practica.hora_llegada ?? ''}`, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 7.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 2;

  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    body: [
      [
        { content: 'NOMBRE DEL CONDUCTOR PRINCIPAL', styles: { ...LABEL_STYLE, cellWidth: 65 } },
        { content: data.practica.conductor_nombre ?? '—', styles: { ...VALUE_STYLE, fontStyle: 'bold' } },
        { content: 'NOMBRE DEL CONDUCTOR AUXILIAR (SI APLICA)', styles: { ...LABEL_STYLE, cellWidth: 65 } },
        { content: '—', styles: VALUE_STYLE },
      ],
      [
        { content: 'RUTAS AUTORIZADAS', styles: { ...LABEL_STYLE, cellWidth: 65 } },
        { content: rutaIda, colSpan: 3, styles: VALUE_STYLE },
      ],
    ],
    styles: { fontSize: 7.5, lineColor: [200, 200, 200], lineWidth: 0.3 },
    theme: 'grid',
  });

  // Vigilada Mineducación footer
  doc.setFontSize(5.5);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(150, 150, 150);
  doc.text('Vigilada Mineducación  ·  La versión vigente y controlada de este documento, solo podrá ser consultada a través del sitio web Institucional www.usco.edu.co, link Sistema Gestión de Calidad.', M, pageH - 4, { maxWidth: CW });

  // ══════════════════════════════════════════════════════════════
  // PÁGINA 2 — Plan Vial + Requisitos
  // ══════════════════════════════════════════════════════════════
  doc.addPage();
  y = fo05Header(2);

  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    body: [
      [{ content: 'RUTA PRINCIPAL A SEGUIR (IDA):', styles: { ...LABEL_STYLE, cellWidth: 68 } }, { content: rutaIda, colSpan: 3, styles: VALUE_STYLE }],
      [{ content: 'TIEMPO DE VIAJE:', styles: LABEL_STYLE }, { content: `${data.practica.duracion_dias > 0 ? data.practica.duracion_dias + ' día(s)' : '—'}`, styles: VALUE_STYLE },
       { content: 'HORA SALIDA:', styles: LABEL_STYLE }, { content: data.practica.hora_salida ?? '—', styles: VALUE_STYLE }],
      [{ content: 'SITIO DE REPORTE Y DESCANSO 1:', styles: LABEL_STYLE }, { content: destino ? (destino.lugar + (destino.municipio ? ' – ' + destino.municipio : '')) : '—', styles: VALUE_STYLE },
       { content: 'HORA:', styles: LABEL_STYLE }, { content: '—', styles: VALUE_STYLE }],
      [{ content: 'SITIO PARA PERNOCTAR (SI APLICA):', styles: LABEL_STYLE }, { content: data.practica.duracion_dias > 1 ? (destino ? destino.lugar : '—') : 'No aplica', colSpan: 3, styles: VALUE_STYLE }],
      [{ content: 'RUTA PRINCIPAL A SEGUIR (RETORNO):', styles: LABEL_STYLE }, { content: rutaRetorno, colSpan: 3, styles: VALUE_STYLE }],
      [{ content: 'TIEMPO DE VIAJE RETORNO:', styles: LABEL_STYLE }, { content: '—', styles: VALUE_STYLE },
       { content: 'HORA LLEGADA:', styles: LABEL_STYLE }, { content: data.practica.hora_llegada ?? '—', styles: VALUE_STYLE }],
      [{ content: 'RUTA ALTERNA:', styles: LABEL_STYLE },
       { content: '(En caso de usarla, el conductor deberá reportar y justificar antes de tomar dicha ruta)', colSpan: 3, styles: { ...VALUE_STYLE, fontStyle: 'italic', textColor: [100, 100, 100] as [number,number,number] } }],
      [{ content: 'MEDIO DE TRANSPORTE:', styles: LABEL_STYLE }, { content: data.practica.tipo_vehiculo ?? '—', styles: VALUE_STYLE },
       { content: 'EMPRESA / PLACA:', styles: LABEL_STYLE }, { content: `${data.practica.empresa_transporte ?? '—'}  /  ${data.practica.placa_vehiculo ?? '—'}`, styles: VALUE_STYLE }],
    ],
    styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3 },
    theme: 'grid',
    columnStyles: { 0: { cellWidth: 68 }, 2: { cellWidth: 40 } },
  });
  y = doc.lastAutoTable.finalY + 4;

  // Requisitos
  doc.setFillColor(...VINOTINTO);
  doc.rect(M, y, CW, 5.5, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text('REQUISITOS', M + 3, y + 3.8);
  y += 6.5;

  const reqText = 'El Coordinador de la actividad debe anexar:\n▪ PLAN VIAL PARA PRÁCTICAS ACADÉMICAS Y OTRAS ACTIVIDADES RELACIONADAS (Anexo 1) debidamente diligenciado por la totalidad de los participantes incluyendo el Coordinador de la actividad y el Conductor.\n▪ El ACTA DE CONSENTIMIENTO INFORMADO (Anexo 2) debidamente diligenciada por cada uno de los participantes; para el caso de los menores de edad también se debe diligenciar la Autorización de los padres o acudientes.\n▪ El Mapa donde figure la ruta a seguir.\n▪ Listado de los estudiantes matriculados en la Asignatura y/o Curso.\nTodos los documentos deben ser entregados 2 semanas antes de la fecha de salida, de lo contrario su práctica será cancelada (Acuerdo 003 de 2012 – Artículo 6ª numeral 9).';
  const reqLines = doc.splitTextToSize(reqText, CW - 6);
  const reqH = reqLines.length * 3.9 + 6;
  doc.setFillColor(252, 250, 245);
  doc.rect(M, y, CW, reqH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.setLineWidth(0.3);
  doc.rect(M, y, CW, reqH);
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(40, 40, 40);
  doc.text(reqLines, M + 3, y + 4.5);
  y += reqH + 4;

  // Observaciones
  doc.setFillColor(...VINOTINTO);
  doc.rect(M, y, CW, 5.5, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text('OBSERVACIONES', M + 3, y + 3.8);
  y += 6.5;
  const obsText = data.practica.observaciones ?? '';
  const obsLines = doc.splitTextToSize(obsText || ' ', CW - 6);
  const obsH = Math.max(14, obsLines.length * 3.9 + 6);
  doc.setFillColor(252, 250, 248);
  doc.rect(M, y, CW, obsH, 'F');
  doc.setDrawColor(200, 185, 155);
  doc.rect(M, y, CW, obsH);
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(40, 40, 40);
  if (obsText) doc.text(obsLines, M + 3, y + 4.5);

  doc.setFontSize(5.5);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(150, 150, 150);
  doc.text('NOTA: Participante que no firme el LISTADO DE PERSONAL PARA DESPLAZAMIENTO VIAL o no anexe el ACTA DE CONSENTIMIENTO INFORMADO debidamente diligenciada, no podrá hacer parte del desplazamiento en el vehículo oficial o contratado por la Universidad (Acuerdo 003/2012 – Plan Estratégico de Seguridad Vial USCO).', M, pageH - 7, { maxWidth: CW });
  doc.text('Vigilada Mineducación', M, pageH - 4);

  // ══════════════════════════════════════════════════════════════
  // PÁGINA 3 — Reglamento + Firmas
  // ══════════════════════════════════════════════════════════════
  doc.addPage();
  y = fo05Header(3);

  const reglText = '▪ El conductor deberá reportar y descansar cada cuatro (4) horas continuas de conducción y deberá cumplir con el programa de pausas activas (estiramientos).\n▪ El Coordinador de Transporte podrá establecer horarios flexibles de entrada o salida a la jornada laboral de los conductores, y deberán ser acatados por parte de los conductores y el Coordinador de la actividad y/o Administrador del riesgo.\n▪ La jornada laboral de los conductores de la Universidad Surcolombiana, no podrá exceder las ocho (08) horas diarias de trabajo.\n▪ En caso de desplazamientos con un tiempo de viaje mayor a siete (7) horas, se deberá designar un conductor adicional quien deberá realizar el respectivo relevo.\n\nBajo la gravedad de juramento doy fe que los datos y documentos suministrados son ciertos y me responsabilizo de que cualquier omisión o falsedad podría provocar atrasos, rechazos o inconvenientes en el trámite que estoy solicitando.';
  const reglLines = doc.splitTextToSize(reglText, CW - 6);
  const reglH = reglLines.length * 3.9 + 8;
  doc.setFillColor(252, 252, 252);
  doc.rect(M, y, CW, reglH, 'F');
  doc.setDrawColor(200, 200, 200);
  doc.setLineWidth(0.3);
  doc.rect(M, y, CW, reglH);
  doc.setFontSize(7.5);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(40, 40, 40);
  doc.text(reglLines, M + 3, y + 5);
  y += reglH + 8;

  const sigH3 = 32;
  const sigW3 = (CW - 4) / 2;
  [
    { title: 'COORDINADOR DE LA ACTIVIDAD / ADMINISTRADOR DEL RIESGO', name: data.docente.nombres, detail: `C.C. ${data.docente.cedula}` },
    { title: 'COORDINADOR DE TRANSPORTE', name: '___________________________________', detail: 'NOMBRE  /  FIRMA  /  FECHA' },
  ].forEach((s, i) => {
    const sx = M + i * (sigW3 + 4);
    doc.setDrawColor(180, 180, 180);
    doc.setLineWidth(0.3);
    doc.rect(sx, y, sigW3, sigH3);
    doc.setFillColor(245, 242, 234);
    doc.rect(sx, y, sigW3, 6, 'F');
    doc.setFontSize(6.5);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...VINOTINTO);
    doc.text(s.title, sx + sigW3 / 2, y + 4.2, { align: 'center', maxWidth: sigW3 - 4 });
    doc.setDrawColor(120, 120, 120);
    doc.line(sx + 6, y + sigH3 - 11, sx + sigW3 - 6, y + sigH3 - 11);
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(40, 40, 40);
    doc.text(s.name, sx + sigW3 / 2, y + sigH3 - 7, { align: 'center', maxWidth: sigW3 - 6 });
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(120, 120, 120);
    doc.setFontSize(6.5);
    doc.text(s.detail, sx + sigW3 / 2, y + sigH3 - 3, { align: 'center' });
  });

  doc.setFontSize(5.5);
  doc.setFont('helvetica', 'italic');
  doc.setTextColor(150, 150, 150);
  doc.text('Vigilada Mineducación  ·  www.usco.edu.co', M, pageH - 4);

  // ══════════════════════════════════════════════════════════════
  // PÁGINAS 4+ — Listado de Personal para Desplazamiento Vial
  // ══════════════════════════════════════════════════════════════
  for (let pg = 0; pg < partPages; pg++) {
    doc.addPage('a4', 'landscape');
    const lW = doc.internal.pageSize.getWidth();
    const lH = doc.internal.pageSize.getHeight();
    const lCW = lW - M * 2;
    y = fo05Header(4 + pg);

    // Section header
    doc.setFillColor(...VINOTINTO);
    doc.rect(M, y, lCW, 5.5, 'F');
    doc.setFontSize(7);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(255, 255, 255);
    doc.text('ESTAMENTO   —   DATOS DE CONTACTO', M + 3, y + 3.8);
    y += 6.5;

    const chunk = data.participantes.slice(pg * PER_PAGE, (pg + 1) * PER_PAGE);
    const rows = [...chunk];
    while (rows.length < PER_PAGE) {
      rows.push({ nombres: '', codigo: '', cedula: '', eps: '', arl: '', fondo_pensiones: '' });
    }

    autoTable(doc, {
      startY: y, margin: { left: M, right: M },
      head: [[
        { content: 'No', styles: { halign: 'center' as const } },
        'NOMBRE',
        'No. DOCUMENTO\nDE IDENTIDAD',
        'CÓDIGO',
        'EPS',
        'ARL',
        'F.P.',
        { content: 'D', styles: { halign: 'center' as const } },
        { content: 'A', styles: { halign: 'center' as const } },
        { content: 'TO', styles: { halign: 'center' as const } },
        { content: 'EST.\nPRE.', styles: { halign: 'center' as const } },
        { content: 'EST.\nPOS.', styles: { halign: 'center' as const } },
        { content: 'CO', styles: { halign: 'center' as const } },
        { content: 'P', styles: { halign: 'center' as const } },
        'NOMBRE CONTACTO',
        'TELÉFONO',
        'FIRMA',
      ]],
      body: rows.map((p, i) => [
        { content: pg * PER_PAGE + i + 1, styles: { halign: 'center' as const } },
        p.nombres,
        p.cedula,
        p.codigo,
        p.eps ?? '',
        p.arl ?? '',
        p.fondo_pensiones ?? '',
        { content: '', styles: { halign: 'center' as const } },
        { content: '', styles: { halign: 'center' as const } },
        { content: '', styles: { halign: 'center' as const } },
        { content: p.nombres ? 'X' : '', styles: { halign: 'center' as const, fontStyle: 'bold' as const } },
        { content: '', styles: { halign: 'center' as const } },
        { content: '', styles: { halign: 'center' as const } },
        { content: '', styles: { halign: 'center' as const } },
        '',
        '',
        '',
      ]),
      styles: { fontSize: 7, lineColor: [200, 200, 200], lineWidth: 0.3, minCellHeight: 6.5 },
      headStyles: { fillColor: VINOTINTO, textColor: [255, 255, 255] as [number,number,number], fontStyle: 'bold', fontSize: 6 },
      columnStyles: {
        0:  { cellWidth: 7,  halign: 'center' as const },
        1:  { cellWidth: 40 },
        2:  { cellWidth: 22 },
        3:  { cellWidth: 17 },
        4:  { cellWidth: 16 },
        5:  { cellWidth: 16 },
        6:  { cellWidth: 13 },
        7:  { cellWidth: 7,  halign: 'center' as const },
        8:  { cellWidth: 7,  halign: 'center' as const },
        9:  { cellWidth: 7,  halign: 'center' as const },
        10: { cellWidth: 9,  halign: 'center' as const },
        11: { cellWidth: 9,  halign: 'center' as const },
        12: { cellWidth: 7,  halign: 'center' as const },
        13: { cellWidth: 7,  halign: 'center' as const },
        14: { cellWidth: 33 },
        15: { cellWidth: 21 },
        16: { cellWidth: 21 },
      },
      theme: 'grid',
    });

    doc.setFontSize(5.5);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(150, 150, 150);
    doc.text('D= Docente  A= Administrativo  TO= Trabajador Oficial  CO= Contratista  EST.PRE= Estudiante Pregrado  EST.POS= Estudiante Posgrado  P= Particular  |  Vigilada Mineducación', M, lH - 4, { maxWidth: lCW });
  }

  // ══════════════════════════════════════════════════════════════
  // PÁGINA 5 — Acta de Consentimiento Informado
  // ══════════════════════════════════════════════════════════════
  doc.addPage('a4', 'portrait');
  y = fo05Header(4 + partPages);

  // Header acta
  doc.setFillColor(...VINOTINTO);
  doc.rect(M, y, CW, 6, 'F');
  doc.setFontSize(8);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text('ACTA DE CONSENTIMIENTO INFORMADO', M + CW / 2, y + 4.2, { align: 'center' });
  y += 7;

  // Tipo vinculación
  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    body: [[
      { content: 'TIPO DE VINCULACIÓN CON LA USCO\n(Seleccione con una X)', styles: { ...LABEL_STYLE, cellWidth: 65 } },
      { content: 'D', styles: { halign: 'center' as const, fontStyle: 'bold' as const, cellWidth: 14 } },
      { content: 'A', styles: { halign: 'center' as const, cellWidth: 14 } },
      { content: 'TO.', styles: { halign: 'center' as const, cellWidth: 14 } },
      { content: 'CO.', styles: { halign: 'center' as const, cellWidth: 14 } },
      { content: 'EST.', styles: { halign: 'center' as const, fontStyle: 'bold' as const, cellWidth: 14 } },
      { content: 'P.', styles: { halign: 'center' as const, cellWidth: 14 } },
    ]],
    styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3 },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 3;

  const consentText = `El suscrito ______________________________________________ identificado con el documento de identidad: CC____ TI____ No. __________________, conforme al número que aparece al pie de mi firma, manifiesto que estoy suficientemente enterado de los procedimientos administrativos que realiza la Institución para la realización de las prácticas extramuros y académicas y/o evento institucional establecido en la programación de actividades curriculares y no curriculares correspondientes al presente período académico. (Si es estudiante, escriba el nombre del programa al que pertenece y su código estudiantil) Programa_______________________________ Código_______________.

La Universidad me ha comunicado de los trámites básicos de la práctica y/o evento institucional, sus ventajas, desventajas, riesgos y posibles complicaciones que puedan ocurrir durante el desplazamiento y realización de la misma, teniendo en cuenta la difícil situación de orden público que actualmente afecta a la región Surcolombiana y al país en general.

Declaro que comprendo los siguientes aspectos:
• La Universidad cumplirá a cabalidad los procedimientos fijados en la normatividad de la Institución sobre las prácticas y/o evento institucional en procura de garantizar el éxito de la gestión y obtener las mayores medidas de seguridad previas a cada desplazamiento.
• La Universidad verificará previamente la situación de orden público en el lugar donde se realizará la práctica y/o evento institucional.
• El Coordinador responsable de la práctica y/o evento institucional portará un listado oficial de los participantes.
• Mis únicos documentos que debo portar son la cédula de ciudadanía o tarjeta de identidad, carné estudiantil y libreta militar.
• En calidad de participante de la actividad me acojo a mis obligaciones establecidas en el Manual de Convivencia tales como el NO consumo y/o transporte de sustancias alcohólicas, estupefacientes y toda clase de armas en el transcurso de la actividad.

Conforme lo expuesto voluntariamente consiento la realización de la práctica extramuros o académica y/o evento institucional que se llevará a cabo en _____________________ (lugar) el Día____ Mes____ Año______ correspondiente al programa u actividad _______________________________________________.

FIRMA _____________________________ C.C. o T.I. ______________ FECHA __________________`;
  const cLines = doc.splitTextToSize(consentText, CW - 4);
  const cH = cLines.length * 3.6 + 6;
  doc.setFillColor(252, 252, 252);
  doc.rect(M, y, CW, cH, 'F');
  doc.setDrawColor(210, 210, 210);
  doc.setLineWidth(0.3);
  doc.rect(M, y, CW, cH);
  doc.setFontSize(7);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(30, 30, 30);
  doc.text(cLines, M + 3, y + 4);
  y += cH + 4;

  // Nota menor de edad
  doc.setFontSize(6.5);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...VINOTINTO);
  doc.text('Nota: Si el participante es menor de edad, el padre, madre o su responsable debe autorizar la salida diligenciando el cuadro que está al final del documento.', M, y, { maxWidth: CW });
  y += 8;

  // Sección autorización menor
  doc.setFillColor(...VINOTINTO);
  doc.rect(M, y, CW, 5.5, 'F');
  doc.setFontSize(7);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text('ESPACIO RESERVADO PARA LA AUTORIZACIÓN DEL PADRE, MADRE O RESPONSABLE DEL MENOR DE EDAD', M + 3, y + 3.8);
  y += 6.5;

  autoTable(doc, {
    startY: y, margin: { left: M, right: M },
    head: [['NOMBRE COMPLETO', 'CÉDULA', 'PARENTESCO', 'TELÉFONO FIJO Y/O CELULAR', 'FIRMA']],
    body: [['', '', '', '', ''], ['', '', '', '', '']],
    styles: { fontSize: 8, lineColor: [200, 200, 200], lineWidth: 0.3, minCellHeight: 10 },
    headStyles: { fillColor: VINOTINTO, textColor: [255, 255, 255] as [number,number,number], fontStyle: 'bold', fontSize: 7 },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 4;

  doc.setFontSize(6);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(80, 80, 80);
  doc.text('D= Docente  A= Administrativo  TO= Trabajador Oficial  CO= Contratista  EST.= Estudiante  P= Particular', M, y);

  // Pie normativo en todas las páginas
  const totalPagesReal = (doc.internal as unknown as { getNumberOfPages: () => number }).getNumberOfPages();
  for (let p = 1; p <= totalPagesReal; p++) {
    doc.setPage(p);
    const curW = doc.internal.pageSize.getWidth();
    const curH = doc.internal.pageSize.getHeight();
    doc.setFontSize(6);
    doc.setFont('helvetica', 'italic');
    doc.setTextColor(140, 140, 140);
    doc.text(`AP-INF-FO-05 · Versión 7 · Acuerdo 003/2012 USCO · Generado por SIPAM-USCO · ${fechaHoy}`, curW - M, curH - 1.5, { align: 'right' });
  }

  doc.save(`FO-05_Desplazamiento_Practica${data.practica.id}_${data.practica.periodo_academico}.pdf`);
}


// ─────────────────────────────────────────────────────────────────
// Lista consolidada de prácticas por programa — Consejo Académico
// ─────────────────────────────────────────────────────────────────
const ESTADO_LABEL: Record<string, string> = {
  borrador: 'Borrador', solicitada: 'Solicitada', pendiente_quorum: 'Pend. Quórum',
  aprobada_curriculo: 'Aprobada Comité', aprobada_facultad: 'Avalada Facultad',
  aprobado_transporte: 'Aprobada Vicerrectoría', en_ejecucion: 'En Ejecución',
  finalizada: 'Finalizada', rechazada: 'Rechazada',
};

export function generarConsolidadoPracticas(data: {
  programa: string; periodo: string;
  practicas: Array<{
    id: number; nombre: string; asignatura: string; docente: string;
    fecha_inicio?: string | null; fecha_fin?: string | null; duracion_dias: number;
    num_alumnos: number; quorum_alcanzado: boolean;
    destino: string; municipio_destino?: string | null;
    total_viaticos: number; placa_vehiculo?: string | null; tipo_vehiculo?: string | null;
    estado: string;
  }>;
}) {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' }) as AutoTableDoc;
  const pageW = doc.internal.pageSize.width;
  const MARGIN = 12;
  const CW = pageW - MARGIN * 2;
  const fechaHoy = new Date().toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' });

  let y = drawHeader(doc, 'CONSOLIDADO PRÁCTICAS EXTRAMUROS — CONSEJO ACADÉMICO', 'MI-CONS-PE', '1', fechaHoy);

  // Banner de programa/período
  doc.setFillColor(...VINOTINTO);
  doc.rect(MARGIN, y, CW, 8, 'F');
  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(255, 255, 255);
  doc.text(`${data.programa}  ·  PERÍODO ${data.periodo}  ·  Total: ${data.practicas.length} prácticas`, MARGIN + 4, y + 5.5);
  y += 12;

  // Tabla consolidada
  autoTable(doc, {
    startY: y,
    margin: { left: MARGIN, right: MARGIN },
    head: [['#', 'Nombre de la práctica', 'Asignatura', 'Docente', 'Inicio', 'Fin', 'Días', 'Alumnos', 'Destino', 'Viáticos', 'Vehículo', 'Estado']],
    body: data.practicas.map((p, i) => [
      { content: i + 1, styles: { halign: 'center' as const } },
      p.nombre,
      p.asignatura,
      p.docente,
      p.fecha_inicio ?? '—',
      p.fecha_fin ?? '—',
      { content: p.duracion_dias, styles: { halign: 'center' as const } },
      { content: p.num_alumnos, styles: { halign: 'center' as const } },
      `${p.destino}${p.municipio_destino ? ' (' + p.municipio_destino + ')' : ''}`,
      { content: new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(p.total_viaticos), styles: { halign: 'right' as const } },
      p.placa_vehiculo ? `${p.placa_vehiculo}${p.tipo_vehiculo ? ' / ' + p.tipo_vehiculo : ''}` : '—',
      {
        content: ESTADO_LABEL[p.estado] ?? p.estado,
        styles: {
          fontStyle: 'bold' as const,
          textColor: p.estado === 'finalizada' ? [21, 128, 61] as [number,number,number]
            : p.estado === 'rechazada' ? [180, 0, 0] as [number,number,number]
            : p.estado === 'en_ejecucion' ? [21, 100, 180] as [number,number,number]
            : [80, 80, 80] as [number,number,number],
        },
      },
    ]),
    styles: { fontSize: 7, lineColor: [200, 200, 200], lineWidth: 0.3, cellPadding: 2 },
    headStyles: { fillColor: VINOTINTO, textColor: [255, 255, 255], fontStyle: 'bold', fontSize: 7 },
    alternateRowStyles: { fillColor: [248, 248, 248] },
    columnStyles: {
      0: { cellWidth: 10, halign: 'center' as const },
      4: { cellWidth: 18 }, 5: { cellWidth: 18 },
      6: { cellWidth: 10, halign: 'center' as const },
      7: { cellWidth: 16, halign: 'center' as const },
      9: { cellWidth: 26, halign: 'right' as const },
      10: { cellWidth: 22 },
      11: { cellWidth: 22 },
    },
    theme: 'grid',
  });
  y = doc.lastAutoTable.finalY + 8;

  // Totales
  const totalViat = data.practicas.reduce((s, p) => s + p.total_viaticos, 0);
  const totalAlumnos = data.practicas.reduce((s, p) => s + p.num_alumnos, 0);
  doc.setFontSize(9);
  doc.setFont('helvetica', 'bold');
  doc.setTextColor(...VINOTINTO);
  doc.text(`Total estudiantes: ${totalAlumnos}   ·   Total viáticos: ${new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(totalViat)}`, MARGIN, y);

  // Footer
  const totalPages = (doc.internal as unknown as { getNumberOfPages: () => number }).getNumberOfPages();
  for (let p = 1; p <= totalPages; p++) {
    doc.setPage(p);
    addPageFooter(doc, p, totalPages);
  }

  doc.save(`Consolidado_Practicas_${data.programa.replace(/\s+/g, '_')}_${data.periodo}.pdf`);
}
