from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from app.models.practica import EstadoPracticaEnum, TipoDocenteEnum, CaracterCursoEnum, CaracteristicaCursoEnum, ModalidadDocenteEnum
from app.schemas.user import UserOut
from app.schemas.convocatoria import AsignaturaOut


class RutaPracticaCreate(BaseModel):
    orden: int
    tipo_punto: str
    lugar: str
    municipio: Optional[str] = None
    departamento: Optional[str] = None
    distancia_km: Optional[float] = None
    vereda: Optional[str] = None
    es_rural: bool = False


class RutaPracticaOut(BaseModel):
    id: int
    orden: int
    tipo_punto: str
    lugar: str
    municipio: Optional[str] = None
    departamento: Optional[str] = None
    distancia_km: Optional[float] = None
    vereda: Optional[str] = None
    es_rural: bool = False

    model_config = {"from_attributes": True}


class PracticaCreate(BaseModel):
    nombre_practica: str
    asignatura_id: int
    periodo_academico: str
    fecha_inicio: datetime
    fecha_fin: datetime
    num_alumnos: int
    tipo_docente: Optional[TipoDocenteEnum] = None
    observaciones: Optional[str] = None
    rutas: list[RutaPracticaCreate] = []
    # Campos FO-16
    caracter_curso: Optional[CaracterCursoEnum] = None
    caracteristica_curso: Optional[CaracteristicaCursoEnum] = None
    modalidad_docente: Optional[ModalidadDocenteEnum] = None
    hora_salida: Optional[str] = None
    hora_llegada: Optional[str] = None
    articulacion_curso: Optional[str] = None
    descripcion_practica: Optional[str] = None
    evaluacion: Optional[str] = None
    justificacion: Optional[str] = None
    metodologia: Optional[str] = None
    carta_autorizacion_empresa: Optional[str] = None
    placa_vehiculo: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    empresa_transporte: Optional[str] = None
    conductor_nombre: Optional[str] = None
    sede: Optional[str] = None


class PracticaUpdate(BaseModel):
    nombre_practica: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    num_alumnos: Optional[int] = None
    tipo_docente: Optional[TipoDocenteEnum] = None
    observaciones: Optional[str] = None
    rutas: Optional[list[RutaPracticaCreate]] = None
    # Campos FO-16
    caracter_curso: Optional[CaracterCursoEnum] = None
    caracteristica_curso: Optional[CaracteristicaCursoEnum] = None
    modalidad_docente: Optional[ModalidadDocenteEnum] = None
    hora_salida: Optional[str] = None
    hora_llegada: Optional[str] = None
    articulacion_curso: Optional[str] = None
    descripcion_practica: Optional[str] = None
    evaluacion: Optional[str] = None
    justificacion: Optional[str] = None
    metodologia: Optional[str] = None
    carta_autorizacion_empresa: Optional[str] = None
    placa_vehiculo: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    empresa_transporte: Optional[str] = None
    conductor_nombre: Optional[str] = None
    sede: Optional[str] = None


class ViaticosCalculadoOut(BaseModel):
    tarifa_id: int
    descripcion: str
    valor_dia: float
    num_dias: int
    num_personas: int
    subtotal: float


class PracticaOut(BaseModel):
    id: int
    nombre_practica: str
    asignatura_id: int
    profesor_id: int
    estado: EstadoPracticaEnum
    periodo_academico: str
    fecha_inicio: datetime
    fecha_fin: datetime
    duracion_dias: int
    num_alumnos: int
    total_firmas_requeridas: Optional[int] = None
    total_firmas_obtenidas: int
    quorum_alcanzado: bool
    tipo_docente: Optional[TipoDocenteEnum] = None
    observaciones: Optional[str] = None
    observaciones_jefe: Optional[str] = None
    # Campos FO-16
    caracter_curso: Optional[CaracterCursoEnum] = None
    caracteristica_curso: Optional[CaracteristicaCursoEnum] = None
    modalidad_docente: Optional[ModalidadDocenteEnum] = None
    hora_salida: Optional[str] = None
    hora_llegada: Optional[str] = None
    articulacion_curso: Optional[str] = None
    descripcion_practica: Optional[str] = None
    evaluacion: Optional[str] = None
    justificacion: Optional[str] = None
    metodologia: Optional[str] = None
    carta_autorizacion_empresa: Optional[str] = None
    sede: Optional[str] = None
    created_at: Optional[datetime] = None
    asignatura: Optional[AsignaturaOut] = None
    profesor: Optional[UserOut] = None
    rutas: list[RutaPracticaOut] = []
    porcentaje_quorum: Optional[float] = None
    ya_firme: Optional[bool] = None
    puede_firmar_ahora: Optional[bool] = None
    ventana_firma_inicio: Optional[datetime] = None
    ventana_firma_fin: Optional[datetime] = None
    pago_registrado: Optional[bool] = None

    model_config = {"from_attributes": True}


class FirmaConsentimientoOut(BaseModel):
    id: int
    practica_id: int
    estudiante_id: int
    ip_address: Optional[str] = None
    signed_at: datetime

    model_config = {"from_attributes": True}


class TarifaViaticoOut(BaseModel):
    id: int
    descripcion: str
    valor_dia: float
    aplica_desde: date
    aplica_hasta: Optional[date] = None
    is_active: bool

    model_config = {"from_attributes": True}


class PresupuestoOut(BaseModel):
    id: int
    periodo_academico: str
    monto_total_asignado: float
    monto_solicitado: float | None = None  # incremento pendiente de aprobación
    monto_ejecutado: float
    monto_comprometido: float
    monto_disponible: float
    porcentaje_ejecutado: float
    estado: str = "aprobado"
    observaciones_admin: str | None = None
    descripcion: str | None = None

    model_config = {"from_attributes": True}
