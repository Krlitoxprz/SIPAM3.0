import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sipam_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sipam_token');
      localStorage.removeItem('sipam_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

export async function downloadAuthenticated(url: string, filename: string): Promise<void> {
  const response = await api.get(url, { responseType: 'blob' });
  const href = URL.createObjectURL(response.data);
  try {
    const link = document.createElement('a');
    link.href = href;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } finally {
    URL.revokeObjectURL(href);
  }
}

export const authService = {
  login: (codigo: string, password: string) =>
    api.post('/auth/login', { codigo, password }),
  me: () => api.get('/auth/me'),
  validarAcademica: (codigoEstudiante: string) =>
    api.get(`/auth/validar-academica/${codigoEstudiante}`),
};

export const convocatoriasService = {
  getAll: (params?: Record<string, unknown>) =>
    api.get('/convocatorias/', { params }),
  getById: (id: number) => api.get(`/convocatorias/${id}`),
  create: (data: unknown) => api.post('/convocatorias/', data),
  update: (id: number, data: unknown) => api.put(`/convocatorias/${id}`, data),
  cambiarEstado: (id: number, estado: string) =>
    api.patch(`/convocatorias/${id}/estado`, { estado }),
  getAsignaturas: (includeInactive?: boolean) => api.get('/convocatorias/asignaturas/todas', { params: includeInactive ? { include_inactive: true } : undefined }),
  getProfesores: () => api.get('/convocatorias/profesores'),
  getMisMaterias: () => api.get('/convocatorias/mis-materias'),
  getProgramaAcademico: () => api.get('/convocatorias/programa-academico'),
  getPlantillas: (params?: { programa?: string; asignatura_id?: number; profesor_id?: number }) =>
    api.get('/convocatorias/plantillas', { params }),
};

export const postulacionesService = {
  getMias: () => api.get('/postulaciones/mis-postulaciones'),
  getPorConvocatoria: (convId: number, params?: Record<string, unknown>) =>
    api.get(`/postulaciones/convocatoria/${convId}`, { params }),
  postular: (convocatoriaId: number, data: unknown) =>
    api.post(`/postulaciones/convocatoria/${convocatoriaId}`, data),
  subirDocumento: (postulacionId: number, tipoDocumento: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tipo_documento', tipoDocumento);
    return api.post(`/postulaciones/${postulacionId}/documentos`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  descargarDocumento: (archivoId: number) =>
    api.get(`/postulaciones/documentos/${archivoId}/descargar`, { responseType: 'blob' }),
  setNotaAsignatura: (postId: number, nota: number) =>
    api.patch(`/postulaciones/${postId}/nota-asignatura`, null, { params: { nota } }),
  setEntrevista: (postId: number, nota_entrevista: number, observaciones?: string) =>
    api.patch(`/postulaciones/${postId}/entrevista`, { nota_entrevista, observaciones }),
  desistir: (postId: number) =>
    api.patch(`/postulaciones/${postId}/desistir`),
};

export const seleccionService = {
  getResultados: (convId: number) =>
    api.get(`/seleccion/convocatorias/${convId}/resultados`),
  ejecutarAlgoritmo: (convId: number) =>
    api.post(`/seleccion/convocatorias/${convId}/ejecutar-seleccion`),
};

export const practicasService = {
  getAll: (params?: Record<string, unknown>) =>
    api.get('/practicas/', { params }),
  getById: (id: number) => api.get(`/practicas/${id}`),
  create: (data: unknown) => api.post('/practicas/', data),
  update: (id: number, data: unknown) => api.put(`/practicas/${id}`, data),
  solicitar: (id: number) => api.patch(`/practicas/${id}/solicitar`),
  aprobar: (id: number) => api.patch(`/practicas/${id}/aprobar`),
  rechazar: (id: number, observaciones_jefe?: string) =>
    api.patch(`/practicas/${id}/rechazar`, { observaciones_jefe: observaciones_jefe ?? null }),
  iniciar: (id: number) => api.patch(`/practicas/${id}/iniciar`),
  finalizar: (id: number, data: { informe_resultados: string; observaciones?: string }) =>
    api.patch(`/practicas/${id}/finalizar`, data),
  firmarConsentimiento: (practicaId: number) =>
    api.post(`/practicas/${practicaId}/firmar-consentimiento`),
  calcularViaticos: (id: number) => api.get(`/practicas/${id}/viaticos`),
  getTarifas: () => api.get('/practicas/tarifas/vigentes'),
  getPlantillas: (programa?: string) => api.get('/practicas/plantillas', { params: programa ? { programa } : undefined }),
  autocompletar: (asignatura_id: number) => api.get('/practicas/autocompletar', { params: { asignatura_id } }),
  datosAsignatura: (asignatura_id: number) => api.get('/practicas/datos-asignatura', { params: { asignatura_id } }),
  limitesDuracion: () => api.get('/practicas/limites-duracion'),
};

export const usuariosService = {
  getAll: (params?: Record<string, unknown>) =>
    api.get('/auth/usuarios', { params }),
  create: (data: unknown) => api.post('/auth/usuarios', data),
  toggleActivo: (id: number) => api.patch(`/auth/usuarios/${id}/toggle-activo`),
  toggleSancionado: (id: number) => api.patch(`/auth/usuarios/${id}/toggle-sancionado`),
  resetPassword: (id: number, nueva_password?: string) =>
    api.patch(`/auth/usuarios/${id}/reset-password`, { nueva_password: nueva_password ?? null }),
};

export const presupuestoService = {
  getActual: () => api.get('/presupuesto/actual'),
  getAll: () => api.get('/presupuesto/'),
  getByPeriodo: (periodo: string) => api.get(`/presupuesto/${periodo}`),
  getMovimientos: (periodo: string) => api.get(`/presupuesto/movimientos/${periodo}`),
  crear: (data: unknown) => api.post('/presupuesto/', data),
  solicitar: (periodo: string) => api.patch(`/presupuesto/${periodo}/solicitar`),
  editar: (periodo: string, data: { monto_total_asignado?: number; descripcion?: string }) =>
    api.patch(`/presupuesto/${periodo}/editar`, data),
  aprobar: (periodo: string, data?: { observaciones?: string }) =>
    api.patch(`/presupuesto/${periodo}/aprobar`, data ?? {}),
  rechazar: (periodo: string, data?: { observaciones?: string }) =>
    api.patch(`/presupuesto/${periodo}/rechazar`, data ?? {}),
  pedirModificacion: (periodo: string, data?: { observaciones?: string }) =>
    api.patch(`/presupuesto/${periodo}/pedir-modificacion`, data ?? {}),
  siguientePeriodo: () => api.get('/presupuesto/siguiente-periodo'),
  solicitarIncremento: (periodo: string, data: { nuevo_monto: number; descripcion?: string }) =>
    api.patch(`/presupuesto/${periodo}/solicitar-incremento`, data),
  // Documentos de soporte
  subirDocumento: (periodo: string, formData: FormData) =>
    api.post(`/presupuesto/${periodo}/documentos`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  listarDocumentos: (periodo: string) => api.get(`/presupuesto/${periodo}/documentos`),
  eliminarDocumento: (periodo: string, docId: number) =>
    api.delete(`/presupuesto/${periodo}/documentos/${docId}`),
  getDownloadUrl: (docId: number) => `${api.defaults.baseURL}/presupuesto/documentos/${docId}/descargar`,
  // Admin-only endpoints
  ampliarSemestre: (calId: number, data: { semanas_adicionales: number; nueva_fecha_fin?: string }) =>
    api.patch(`/presupuesto/configuracion-calendario/${calId}/ampliar-semestre`, data),
  aumentarMonto: (periodo: string, data: { nuevo_monto: number; razon?: string }) =>
    api.patch(`/presupuesto/${periodo}/aumentar-monto`, data),
  forzarEstado: (periodo: string, data: { estado: string; observaciones?: string }) =>
    api.patch(`/presupuesto/${periodo}/forzar-estado`, data),
  eliminarPresupuesto: (periodo: string) => api.delete(`/presupuesto/${periodo}`),
  estadisticasGlobales: () => api.get('/presupuesto/admin/estadisticas-globales'),
  listarCalendarios: () => api.get('/presupuesto/configuracion-calendario/'),
};

export const adminService = {
  // Semestres
  getSemestres: () => api.get('/admin/semestres'),
  crearSemestre: (data: {
    periodo_academico: string;
    fecha_inicio_semestre: string;
    fecha_fin_semestre: string;
    semana_inicio_solicitudes: number;
    semana_fin_solicitudes: number;
    is_active: boolean;
  }) => api.post('/admin/semestres', data),
  actualizarSemestre: (id: number, data: {
    fecha_inicio_semestre?: string;
    fecha_fin_semestre?: string;
    semana_inicio_solicitudes?: number;
    semana_fin_solicitudes?: number;
    is_active?: boolean;
  }) => api.patch(`/admin/semestres/${id}`, data),
  activarSemestre: (id: number) => api.patch(`/admin/semestres/${id}/activar`),
  eliminarSemestre: (id: number) => api.delete(`/admin/semestres/${id}`),
  // Monitorías
  getMonitorias: (params?: { estado?: string; q?: string }) =>
    api.get('/admin/monitorias', { params }),
  getPostulacionesConvocatoria: (convId: number) =>
    api.get(`/admin/monitorias/${convId}/postulaciones`),
  eliminarConvocatoria: (convId: number) => api.delete(`/admin/monitorias/${convId}`),
  eliminarPostulacion: (postId: number) =>
    api.delete(`/admin/monitorias/postulaciones/${postId}`),
  // Prácticas
  getPracticasAdmin: (params?: { estado?: string; programa?: string; q?: string }) =>
    api.get('/admin/practicas', { params }),
  eliminarPractica: (practicaId: number) => api.delete(`/admin/practicas/${practicaId}`),
  // Sistema
  getTestingMode: () => api.get('/auth/sistema/testing-mode'),
  setTestingMode: (enabled: boolean) => api.patch('/auth/sistema/testing-mode', { enabled }),
};

export const reportesService = {
  getResumen: () => api.get('/reportes/resumen'),
  getAuditLog: (limit?: number) => api.get('/monitor/audit-log', { params: { limit } }),
  getFO14: (convocatoriaId: number) => api.get(`/reportes/fo14/${convocatoriaId}`),
  getFO16: (practicaId: number) => api.get(`/reportes/fo16/${practicaId}`),
  getFO15: (practicaId: number) => api.get(`/reportes/fo15/${practicaId}`),
  getConsentimiento: (practicaId: number) => api.get(`/reportes/consentimiento/${practicaId}`),
  getFO46: (convocatoriaId: number) => api.get(`/reportes/fo46/${convocatoriaId}`),
  getFO05: (practicaId: number) => api.get(`/reportes/fo05/${practicaId}`),
  getPracticasPrograma: (params?: { programa?: string; periodo?: string }) =>
    api.get('/reportes/practicas-programa', { params }),
  getFO15Programa: (params?: { periodo?: string }) =>
    api.get('/reportes/practicas-programa', { params }),
};

export const notificacionesService = {
  getMias: () => api.get('/notificaciones/'),
  getCount: () => api.get('/notificaciones/no-leidas/count'),
  marcarLeida: (id: number) => api.patch(`/notificaciones/${id}/leer`),
  marcarTodasLeidas: () => api.patch('/notificaciones/leer-todas'),
  eliminar: (id: number) => api.delete(`/notificaciones/${id}`),
};

export const monitorService = {
  registrarHoras: (data: { semana: number; horas: number; descripcion?: string }) =>
    api.post('/monitor/registrar-horas', data),
  misHoras: () => api.get('/monitor/mis-horas'),
  horasPorConvocatoria: (convId: number) => api.get(`/monitor/convocatoria/${convId}`),
  aprobarHoras: (horaId: number) => api.patch(`/monitor/horas/${horaId}/aprobar`),
  corregirHoras: (horaId: number, data: { horas?: number; descripcion?: string }) =>
    api.patch(`/monitor/horas/${horaId}`, data),
};

export const asignaturasService = {
  crear: (data: unknown) => api.post('/convocatorias/asignaturas/', data),
  actualizar: (id: number, data: unknown) => api.patch(`/convocatorias/asignaturas/${id}`, data),
  getEstudiantes: (id: number) => api.get(`/convocatorias/asignaturas/${id}/estudiantes`),
  matricular: (asigId: number, data: { estudiante_id: number; periodo_academico: string }) =>
    api.post(`/convocatorias/asignaturas/${asigId}/matricular`, data),
  desmatricular: (matriculaId: number) =>
    api.delete(`/convocatorias/asignaturas/matricula/${matriculaId}`),
};

export const perfilService = {
  get: () => api.get('/perfil/me'),
  actualizar: (data: {
    nombres?: string;
    apellidos?: string;
    email?: string;
    email_personal?: string;
    telefono?: string;
    bio?: string;
    fecha_nacimiento?: string;
    ciudad?: string;
    linkedin_url?: string;
    github_url?: string;
    eps?: string;
    arl?: string;
    fondo_pensiones?: string;
    password_actual?: string;
    password_nuevo?: string;
  }) => api.patch('/perfil/me', data),
  subirFoto: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/perfil/me/foto', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  eliminarFoto: () => api.delete('/perfil/me/foto'),
};

export const geoService = {
  getDepartamentos: () => api.get('/geo/departamentos'),
  getMunicipios: (departamento: string) =>
    api.get('/geo/municipios', { params: { departamento } }),
  geocodificar: (municipio: string, departamento: string) =>
    api.post('/geo/geocodificar', { municipio, departamento }),
  getDistancia: (data: {
    origen_municipio: string;
    origen_departamento: string;
    destino_municipio: string;
    destino_departamento: string;
  }) => api.post('/geo/distancia', data),
};

export const transporteService = {
  getParametros: () => api.get('/transporte/parametros'),
  getPrecios: () => api.get('/transporte/combustible/precios'),
  getPeajes: (params?: { departamento?: string; corredor?: string }) =>
    api.get('/transporte/peajes', { params }),
  calcularRuta: (data: {
    origen: string;
    destino: string;
    tipo_vehiculo?: string;
    num_vehiculos?: number;
    categoria_peaje?: number;
    tipo_combustible?: string;
  }) => api.post('/transporte/rutas/calcular', data),
  getCostosPractica: (practicaId: number, params?: {
    tipo_vehiculo?: string;
    num_vehiculos?: number;
    categoria_peaje?: number;
  }) => api.get(`/transporte/costos/${practicaId}`, { params }),
  getCostos: (practicaId: number, tipoVehiculo: string, numVehiculos: number, categoriaPeaje: number = 3) =>
    api.get(`/transporte/costos/${practicaId}`, {
      params: { tipo_vehiculo: tipoVehiculo, num_vehiculos: numVehiculos, categoria_peaje: categoriaPeaje },
    }),
  calcularDistancias: (practicaId: number) =>
    api.post(`/transporte/rutas/${practicaId}/calcular-distancias`),
  getPeajesRuta: (practicaId: number, params?: { categoria_peaje?: number; num_vehiculos?: number }) =>
    api.get(`/transporte/peajes-ruta/${practicaId}`, { params }),
};

export const configuracionService = {
  getPeriodoActivo: () => api.get('/presupuesto/periodo-activo'),
  getCalendarios: () => api.get('/presupuesto/configuracion-calendario/'),
  crearCalendario: (data: unknown) => api.post('/presupuesto/configuracion-calendario/', data),
  actualizarCalendario: (id: number, data: unknown) => api.patch(`/presupuesto/configuracion-calendario/${id}`, data),
  getTarifasTodas: () => api.get('/practicas/tarifas/todas'),
  crearTarifa: (data: unknown) => api.post('/practicas/tarifas/', data),
  actualizarTarifa: (id: number, data: unknown) => api.patch(`/practicas/tarifas/${id}`, data),
};

// SF-03: Evaluación del monitor
export const evaluacionMonitorService = {
  crear: (postId: number, data: { nota_desempeno: number; puntualidad?: number; calidad_academica?: number; observaciones?: string }) =>
    api.post(`/monitor/postulaciones/${postId}/evaluacion`, data),
  get: (postId: number) => api.get(`/monitor/postulaciones/${postId}/evaluacion`),
};

// SF-04: Exportar CSV
export const exportarService = {
  auditLogCsv: (limit?: number) =>
    api.get('/monitor/audit-log/exportar', { params: { limit }, responseType: 'blob' }),
  horasMonitorCsv: (convId: number) =>
    api.get(`/monitor/convocatoria/${convId}/exportar`, { responseType: 'blob' }),
};

// SF-06: Historial de estados
export const historialService = {
  practica: (praId: number) => api.get(`/practicas/${praId}/historial`),
  convocatoria: (convId: number) => api.get(`/convocatorias/${convId}/historial`),
};

// SF-07: Búsqueda global
export const busquedaService = {
  buscar: (q: string) => api.get('/busqueda/', { params: { q } }),
};

// SF-09: Pagos de viáticos
export const pagoViaticosService = {
  registrar: (praId: number, data: { monto_pagado: number; fecha_pago: string; observaciones?: string }) =>
    api.post(`/practicas/${praId}/registrar-pago`, data),
  listar: (praId: number) => api.get(`/practicas/${praId}/pagos`),
};

// SF-10: Reset de contraseña
export const resetPasswordService = {
  solicitar: (email: string) => api.post('/auth/solicitar-reset', { email }),
  confirmar: (token: string, nueva_password: string) =>
    api.post('/auth/confirmar-reset', { token, nueva_password }),
};

// SF-12: Códigos QR de verificación
export const qrService = {
  convocatoria: (id: number) => api.get(`/qr/convocatoria/${id}`, { responseType: 'blob' }),
  practica: (id: number) => api.get(`/qr/practica/${id}`, { responseType: 'blob' }),
  postulacion: (id: number) => api.get(`/qr/postulacion/${id}`, { responseType: 'blob' }),
};

// IA Service — predicción + recomendaciones
export const iaService = {
  predecir: (data: Record<string, unknown>) => api.post('/ia/predecir', data),
  getRecomendaciones: (limite = 5) =>
    api.get('/ia/recomendaciones', { params: { limite } }),
};

// PDF Server-side — descarga PDF generado con WeasyPrint
export const pdfService = {
  fo14: (convocatoriaId: number) =>
    api.get(`/pdf/fo14/${convocatoriaId}`, { responseType: 'blob' }),
  fo15: (practicaId: number) =>
    api.get(`/pdf/fo15/${practicaId}`, { responseType: 'blob' }),
  fo16: (practicaId: number) =>
    api.get(`/pdf/fo16/${practicaId}`, { responseType: 'blob' }),
};

export function downloadBlob(blob: Blob, filename: string) {
  const href = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = href;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(href);
}
