from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.postulacion import EstadoPostulacionEnum
from app.schemas.user import UserOut
from app.schemas.convocatoria import ConvocatoriaOut


class PostulacionCreate(BaseModel):
    carta_motivacion: Optional[str] = None


class NotaEntrevistaRequest(BaseModel):
    nota_entrevista: float
    observaciones: Optional[str] = None


class ArchivoAdjuntoOut(BaseModel):
    id: int
    tipo_documento: str
    nombre_original: str
    nombre_almacenado: str
    tamanio_bytes: Optional[int] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class PostulacionOut(BaseModel):
    id: int
    convocatoria_id: int
    estudiante_id: int
    estado: EstadoPostulacionEnum
    nota_asignatura: Optional[float] = None
    promedio_estudiante: Optional[float] = None
    nota_entrevista: Optional[float] = None
    puntaje_final: Optional[float] = None
    puesto: Optional[int] = None
    carta_motivacion: Optional[str] = None
    fecha_postulacion: datetime
    fecha_entrevista: Optional[datetime] = None
    fecha_evaluacion: Optional[datetime] = None
    observaciones_evaluador: Optional[str] = None
    documentos_completos: bool
    convocatoria: Optional[ConvocatoriaOut] = None
    estudiante: Optional[UserOut] = None
    archivos: list[ArchivoAdjuntoOut] = []

    model_config = {"from_attributes": True}


class ResultadoSeleccionOut(BaseModel):
    postulacion_id: int
    estudiante_codigo: str
    estudiante_nombre: str
    nota_asignatura: float
    promedio: float
    nota_entrevista: float
    puntaje_final: float
    puesto: Optional[int] = None
    estado: EstadoPostulacionEnum
