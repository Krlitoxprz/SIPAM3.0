export type Rol = 'admin' | 'estudiante' | 'profesor' | 'jefe_programa' | 'decano';

export interface User {
  id: number;
  codigo: string;
  nombres: string;
  apellidos: string;
  email: string;
  cedula: string;
  rol: Rol;
  is_active: boolean;
  promedio?: number;
  porcentaje_creditos?: number;
  programa?: string;
  sede?: string;
  telefono?: string;
  foto_url?: string;
  email_personal?: string;
  bio?: string;
  fecha_nacimiento?: string;
  ciudad?: string;
  linkedin_url?: string;
  github_url?: string;
  eps?: string;
  arl?: string;
  fondo_pensiones?: string;
  tipo_docente?: string;
  modalidad_docente?: string;
  sancionado_disciplinariamente?: boolean;
  created_at?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export type EstadoConvocatoria = 'borrador' | 'abierta' | 'cerrada' | 'en_evaluacion' | 'finalizada';
export type TipoMonitoria =
  | 'nee'
  | 'regimenes_especiales'
  | 'academica_cursos'
  | 'laboratorios'
  | 'tic'
  | 'permanencia_graduacion'
  | 'deportiva'
  | 'cultural'
  | 'biblioteca'
  | 'acreditacion'
  | 'investigacion'
  | 'academica'         // legacy
  | 'administrativa';  // legacy

export type TipoDocente = 'planta' | 'catedra' | 'ocasional' | 'visitante';

export interface Convocatoria {
  id: number;
  titulo: string;
  descripcion?: string;
  asignatura_id: number;
  profesor_id: number;
  tipo_monitoria: TipoMonitoria;
  estado: EstadoConvocatoria;
  periodo_academico: string;
  fecha_inicio_postulacion: string;
  fecha_fin_postulacion: string;
  num_monitores_requeridos: number;
  horas_semana: number;
  horas_semestre: number;
  promedio_minimo: number;
  creditos_minimo_pct: number;
  descripcion_actividades?: string;
  sede?: string;
  fecha_publicacion_resultados?: string;
  asignatura?: Asignatura;
  profesor?: User;
  total_postulantes?: number;
}

export interface Asignatura {
  id: number;
  codigo: string;
  nombre: string;
  creditos: number;
  programa: string;
  semestre: number;
  facultad?: string | null;
  caracter_curso?: string | null;
  caracteristica_curso?: string | null;
  profesor_id?: number | null;
  is_active?: boolean;
  num_estudiantes?: number;
}

export type EstadoPostulacion =
  | 'pendiente'
  | 'documentos_incompletos'
  | 'en_revision'
  | 'preseleccionado'
  | 'seleccionado'
  | 'no_seleccionado'
  | 'desistido';

export interface ArchivoAdjunto {
  id: number;
  tipo_documento: string;
  nombre_original: string;
  nombre_almacenado: string;
  tamanio_bytes?: number;
  uploaded_at: string;
}

export interface Postulacion {
  id: number;
  convocatoria_id: number;
  estudiante_id: number;
  estado: EstadoPostulacion;
  nota_asignatura?: number;
  promedio_estudiante?: number;
  nota_entrevista?: number;
  puntaje_final?: number;
  puesto?: number;
  carta_motivacion?: string;
  fecha_postulacion: string;
  documentos_completos: boolean;
  convocatoria?: Convocatoria;
  estudiante?: User;
  archivos?: ArchivoAdjunto[];
}

export type EstadoPractica =
  | 'borrador'
  | 'solicitada'
  | 'pendiente_quorum'
  | 'aprobada_curriculo'
  | 'aprobada_facultad'
  | 'aprobado_transporte'
  | 'en_ejecucion'
  | 'finalizada'
  | 'rechazada';

export interface RutaPractica {
  id: number;
  orden: number;
  tipo_punto: string;
  lugar: string;
  municipio?: string;
  departamento?: string;
  distancia_km?: number;
}

export interface Practica {
  id: number;
  nombre_practica: string;
  asignatura_id: number;
  profesor_id: number;
  estado: EstadoPractica;
  periodo_academico: string;
  fecha_inicio: string;
  fecha_fin: string;
  duracion_dias: number;
  num_alumnos: number;
  total_firmas_requeridas?: number;
  total_firmas_obtenidas: number;
  quorum_alcanzado: boolean;
  tipo_docente?: TipoDocente;
  observaciones?: string;
  observaciones_jefe?: string;
  caracter_curso?: string | null;
  caracteristica_curso?: string | null;
  modalidad_docente?: string | null;
  hora_salida?: string | null;
  hora_llegada?: string | null;
  articulacion_curso?: string | null;
  descripcion_practica?: string | null;
  evaluacion?: string | null;
  justificacion?: string | null;
  metodologia?: string | null;
  carta_autorizacion_empresa?: string | null;
  asignatura?: Asignatura;
  profesor?: User;
  rutas?: RutaPractica[];
  porcentaje_quorum?: number;
  ya_firme?: boolean;
  puede_firmar_ahora?: boolean;
  ventana_firma_inicio?: string;
  ventana_firma_fin?: string;
  pago_registrado?: boolean;
}

export interface Presupuesto {
  id: number;
  periodo_academico: string;
  monto_total_asignado: number;
  monto_solicitado?: number | null;
  monto_ejecutado: number;
  monto_comprometido: number;
  monto_disponible: number;
  porcentaje_ejecutado: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}
