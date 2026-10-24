from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.convocatoria import EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.schemas.user import UserOut


class AsignaturaOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    creditos: int
    programa: str
    facultad: Optional[str] = None
    semestre: int
    profesor_id: Optional[int] = None
    caracter_curso: Optional[str] = None
    caracteristica_curso: Optional[str] = None
    is_active: bool = True
    num_estudiantes: Optional[int] = None

    model_config = {"from_attributes": True}


class ConvocatoriaCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    asignatura_id: int
    profesor_id: Optional[int] = None
    tipo_monitoria: TipoMonitoriaEnum = TipoMonitoriaEnum.academica_cursos
    periodo_academico: str
    fecha_inicio_postulacion: datetime
    fecha_fin_postulacion: datetime
    fecha_publicacion_resultados: Optional[datetime] = None
    num_monitores_requeridos: int = 1
    horas_semana: int
    horas_semestre: int
    promedio_minimo: float = 3.5
    creditos_minimo_pct: float = 30.0
    descripcion_actividades: Optional[str] = None
    sede: Optional[str] = None


class ConvocatoriaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    asignatura_id: Optional[int] = None
    profesor_id: Optional[int] = None
    tipo_monitoria: Optional[TipoMonitoriaEnum] = None
    periodo_academico: Optional[str] = None
    fecha_inicio_postulacion: Optional[datetime] = None
    fecha_fin_postulacion: Optional[datetime] = None
    fecha_publicacion_resultados: Optional[datetime] = None
    num_monitores_requeridos: Optional[int] = None
    horas_semana: Optional[int] = None
    horas_semestre: Optional[int] = None
    promedio_minimo: Optional[float] = None
    creditos_minimo_pct: Optional[float] = None
    descripcion_actividades: Optional[str] = None
    sede: Optional[str] = None


class CambiarEstadoRequest(BaseModel):
    estado: EstadoConvocatoriaEnum


class ConvocatoriaOut(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str] = None
    asignatura_id: int
    profesor_id: int
    tipo_monitoria: TipoMonitoriaEnum
    estado: EstadoConvocatoriaEnum
    periodo_academico: str
    fecha_inicio_postulacion: datetime
    fecha_fin_postulacion: datetime
    num_monitores_requeridos: int
    horas_semana: int
    horas_semestre: int
    promedio_minimo: float
    creditos_minimo_pct: float
    descripcion_actividades: Optional[str] = None
    sede: Optional[str] = None
    fecha_publicacion_resultados: Optional[datetime] = None
    created_at: Optional[datetime] = None
    asignatura: Optional[AsignaturaOut] = None
    profesor: Optional[UserOut] = None
    total_postulantes: Optional[int] = None

    model_config = {"from_attributes": True}
