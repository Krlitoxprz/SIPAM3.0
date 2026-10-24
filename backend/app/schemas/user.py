import re
from pydantic import BaseModel, EmailStr, field_validator, HttpUrl
from typing import Optional
from datetime import datetime, date
from app.models.user import RolEnum


class UserOut(BaseModel):
    id: int
    codigo: str
    nombres: str
    apellidos: str
    email: str
    cedula: str
    rol: RolEnum
    is_active: bool
    promedio: Optional[float] = None
    porcentaje_creditos: Optional[float] = None
    programa: Optional[str] = None
    sede: Optional[str] = None
    telefono: Optional[str] = None
    foto_url: Optional[str] = None
    email_personal: Optional[str] = None
    bio: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    ciudad: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    eps: Optional[str] = None
    arl: Optional[str] = None
    fondo_pensiones: Optional[str] = None
    tipo_docente: Optional[str] = None
    modalidad_docente: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[EmailStr] = None
    email_personal: Optional[EmailStr] = None
    telefono: Optional[str] = None
    bio: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    ciudad: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    eps: Optional[str] = None
    arl: Optional[str] = None
    fondo_pensiones: Optional[str] = None
    password_actual: Optional[str] = None
    password_nuevo: Optional[str] = None

    @field_validator("telefono")
    @classmethod
    def telefono_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if v and not re.fullmatch(r"\d{7,15}", v):
                raise ValueError("El teléfono debe contener solo dígitos (7-15 caracteres).")
        return v or None

    @field_validator("bio")
    @classmethod
    def bio_max(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > 500:
            raise ValueError("La biografía no puede superar los 500 caracteres.")
        return v or None

    @field_validator("linkedin_url", "github_url")
    @classmethod
    def url_basica(cls, v: Optional[str]) -> Optional[str]:
        if v:
            v = v.strip()
            if not v.startswith(("http://", "https://")):
                v = "https://" + v
        return v or None


class UserCreate(BaseModel):
    codigo: str
    nombres: str
    apellidos: str
    email: EmailStr
    cedula: str
    password: str
    rol: RolEnum
    promedio: Optional[float] = None
    porcentaje_creditos: Optional[float] = None
    programa: Optional[str] = None
    sede: Optional[str] = None

    @field_validator("cedula")
    @classmethod
    def cedula_solo_digitos(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r"\d{5,12}", v):
            raise ValueError("La cédula debe contener solo dígitos (entre 5 y 12 caracteres).")
        return v

    @field_validator("codigo")
    @classmethod
    def codigo_sin_espacios(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El código no puede estar vacío.")
        if " " in v:
            raise ValueError("El código no puede contener espacios.")
        return v.upper()

    @field_validator("promedio")
    @classmethod
    def promedio_rango(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("El promedio debe estar entre 0.0 y 5.0.")
        return v

    @field_validator("porcentaje_creditos")
    @classmethod
    def creditos_rango(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError("El porcentaje de créditos debe estar entre 0 y 100.")
        return v


class LoginRequest(BaseModel):
    codigo: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ValidacionAcademicaOut(BaseModel):
    codigo: str
    nombres: str
    apellidos: str
    promedio: float
    porcentaje_creditos: float
    apto: bool
    motivos_rechazo: list[str]
