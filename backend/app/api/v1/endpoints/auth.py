import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User, RolEnum
from app.models.monitor import AuditLog
from app.core.security import verify_password, create_access_token
from app.schemas.user import LoginRequest, Token, UserOut, UserCreate, ValidacionAcademicaOut
from app.api.deps import get_current_user, require_roles
from app.core.security import get_password_hash

PASSWORD_MIN_LEN = 8

# ── Protección fuerza bruta (DB-backed — multi-worker safe) ─────────────────
_MAX_ATTEMPTS = 5
_WINDOW = timedelta(minutes=15)

def _check_brute_force(identifier: str, db: Session) -> None:
    """Lanza 429 si el identificador tiene ≥5 login_fallido en los últimos 15 min (BD)."""
    from sqlalchemy import func as sa_func
    window_start = datetime.now(timezone.utc) - _WINDOW
    count = (
        db.query(sa_func.count(AuditLog.id))
        .filter(
            AuditLog.accion == "login_fallido",
            AuditLog.detalle.like(f"%{identifier}%"),
            AuditLog.created_at >= window_start,
        )
        .scalar() or 0
    )
    if count >= _MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Espera {_WINDOW.seconds // 60} minutos antes de intentar de nuevo.",
        )


def _register_failed(identifier: str, db: Session, user_id: Optional[int] = None) -> None:
    db.add(AuditLog(
        usuario_id=user_id,
        accion="login_fallido",
        entidad="auth",
        detalle=f"Intento fallido para {identifier}",
    ))
    db.commit()


def _clear_attempts(_identifier: str, _db: Session) -> None:
    pass  # No se necesita limpiar — las entradas expiran naturalmente por ventana de tiempo


router = APIRouter()


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    _check_brute_force(body.codigo, db)
    user = db.query(User).filter(User.codigo == body.codigo).first()
    if not user:
        user = db.query(User).filter(User.cedula == body.codigo).first()
    if not user or not verify_password(body.password, user.hashed_password):
        _register_failed(body.codigo, db, user_id=user.id if user else None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Código, cédula o contraseña incorrectos",
        )
    if not user.is_active:
        _register_failed(body.codigo, db, user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador.",
        )
    _clear_attempts(body.codigo, db)
    db.add(AuditLog(usuario_id=user.id, accion="login_exitoso", entidad="auth", detalle=f"Login desde rol {user.rol.value}"))
    db.commit()
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get(
    "/validar-academica/{codigo_estudiante}",
    response_model=ValidacionAcademicaOut,
    summary="Mock de validación académica (RF-MON-01)",
    description="Retorna promedio y % créditos aprobados del estudiante. Exige promedio >= 3.5 y créditos >= 30%.",
)
def validar_academica(
    codigo_estudiante: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RolEnum.profesor, RolEnum.jefe_programa, RolEnum.decano)),
):
    estudiante = db.query(User).filter(User.codigo == codigo_estudiante).first()
    if not estudiante:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")

    promedio = estudiante.promedio or 0.0
    pct_creditos = estudiante.porcentaje_creditos or 0.0
    motivos: list[str] = []

    if promedio < 3.5:
        motivos.append(f"Promedio {promedio:.2f} es menor al mínimo requerido (3.50)")
    if pct_creditos < 30.0:
        motivos.append(f"Créditos aprobados {pct_creditos:.1f}% es menor al mínimo requerido (30%)")

    return ValidacionAcademicaOut(
        codigo=estudiante.codigo,
        nombres=estudiante.nombres,
        apellidos=estudiante.apellidos,
        promedio=promedio,
        porcentaje_creditos=pct_creditos,
        apto=len(motivos) == 0,
        motivos_rechazo=motivos,
    )


@router.get("/usuarios", response_model=list[UserOut])
def listar_usuarios(
    rol: Optional[RolEnum] = Query(None, description="Filtrar por rol"),
    q: Optional[str] = Query(None, description="Buscar por código, nombre o email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    query = db.query(User)
    if rol:
        query = query.filter(User.rol == rol)
    if q:
        term = q.strip().lower()
        query = query.filter(
            func.lower(User.codigo).contains(term)
            | func.lower(User.nombres).contains(term)
            | func.lower(User.apellidos).contains(term)
            | func.lower(User.email).contains(term)
        )
    return query.order_by(User.rol, User.apellidos).all()


@router.patch("/usuarios/{user_id}/toggle-activo", response_model=UserOut)
def toggle_activo(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propia cuenta")
    user.is_active = not user.is_active
    accion = "activar_usuario" if user.is_active else "desactivar_usuario"
    db.add(AuditLog(usuario_id=current_user.id, accion=accion, entidad="user", entidad_id=user.id, detalle=f"Usuario {user.codigo} ({user.rol.value})"))
    db.commit()
    db.refresh(user)
    return user


@router.patch("/usuarios/{user_id}/toggle-sancionado", response_model=UserOut)
def toggle_sancionado(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    """Acuerdo 012/2023 Art.4.c — Activar/desactivar sanción disciplinaria de un estudiante."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.rol != RolEnum.estudiante:
        raise HTTPException(status_code=400, detail="Las sanciones disciplinarias solo aplican a estudiantes")
    user.sancionado_disciplinariamente = not user.sancionado_disciplinariamente
    accion = "sancionar_usuario" if user.sancionado_disciplinariamente else "levantar_sancion"
    db.add(AuditLog(
        usuario_id=current_user.id, accion=accion, entidad="user", entidad_id=user.id,
        detalle=f"Sanción disciplinaria {'activada' if user.sancionado_disciplinariamente else 'levantada'} para {user.codigo} (Acuerdo 012/2023 Art.4.c)",
    ))
    db.commit()
    db.refresh(user)
    return user


class ResetPasswordBody(BaseModel):
    nueva_password: Optional[str] = None


# ── Modo de prueba (bypass restricciones) ─────────────────────────────────────
@router.get("/sistema/testing-mode", response_model=dict)
def get_testing_mode(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Devuelve el estado actual del modo de prueba (accesible por cualquier usuario autenticado)."""
    from app.db.database import es_modo_prueba
    return {"testing_mode": es_modo_prueba(db)}


class TestingModeBody(BaseModel):
    enabled: bool


@router.patch("/sistema/testing-mode", response_model=dict)
def set_testing_mode(
    body: TestingModeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin)),
):
    """Activa/desactiva el modo de prueba (solo admin). Elimina restricciones de tiempo y quórum."""
    from sqlalchemy import text as _text
    db.execute(_text("UPDATE sistema_config SET testing_mode = :v WHERE id = 1"), {"v": body.enabled})
    db.commit()
    accion = "activar_modo_prueba" if body.enabled else "desactivar_modo_prueba"
    db.add(AuditLog(
        usuario_id=current_user.id, accion=accion, entidad="sistema", entidad_id=1,
        detalle=f"Modo de prueba {'ACTIVADO' if body.enabled else 'DESACTIVADO'} por {current_user.codigo}",
    ))
    db.commit()
    return {"testing_mode": body.enabled, "message": f"Modo de prueba {'activado' if body.enabled else 'desactivado'}"}


@router.patch("/usuarios/{user_id}/reset-password", response_model=dict)
def reset_password(
    user_id: int,
    body: ResetPasswordBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    """Administrador restablece la contraseña de un usuario. Si no se indica nueva_password se genera una temporal."""
    import secrets, string
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    auto_generada = not bool(body.nueva_password)
    if body.nueva_password:
        if len(body.nueva_password) < PASSWORD_MIN_LEN:
            raise HTTPException(status_code=400, detail=f"La contraseña debe tener al menos {PASSWORD_MIN_LEN} caracteres")
        nueva = body.nueva_password
    else:
        alphabet = string.ascii_letters + string.digits
        nueva = ''.join(secrets.choice(alphabet) for _ in range(10))
    user.hashed_password = get_password_hash(nueva)
    db.add(AuditLog(usuario_id=current_user.id, accion="reset_password", entidad="user", entidad_id=user.id, detalle=f"Contraseña restablecida para {user.codigo}"))
    db.commit()
    # Solo retornar la contraseña en claro si fue auto-generada (para que admin la comunique al usuario)
    respuesta: dict = {"ok": True, "mensaje": f"Contraseña de {user.codigo} restablecida exitosamente."}
    if auto_generada:
        respuesta["nueva_password"] = nueva
    return respuesta


class PerfilUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    foto_url: Optional[str] = None
    password_actual: Optional[str] = None
    password_nuevo: Optional[str] = None

    @field_validator("telefono")
    @classmethod
    def telefono_solo_digitos(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return v
        v = v.strip()
        if not re.fullmatch(r"\d{7,10}", v):
            raise ValueError("El teléfono debe contener solo dígitos (entre 7 y 10 caracteres).")
        return v

    @field_validator("nombres", "apellidos")
    @classmethod
    def no_vacios(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() == "":
            raise ValueError("Este campo no puede estar vacío.")
        return v.strip() if v else v


@router.patch("/me/perfil", response_model=UserOut)
def actualizar_perfil(
    body: PerfilUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.nombres:
        current_user.nombres = body.nombres
    if body.apellidos:
        current_user.apellidos = body.apellidos
    if body.email:
        existing = db.query(User).filter(User.email == body.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="El email ya está en uso por otro usuario")
        current_user.email = body.email
    if body.telefono is not None:
        current_user.telefono = body.telefono or None
    if body.foto_url is not None:
        current_user.foto_url = body.foto_url or None
    if body.password_nuevo:
        if not body.password_actual:
            raise HTTPException(status_code=400, detail="Debes ingresar tu contraseña actual para cambiarla")
        if not verify_password(body.password_actual, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")
        if len(body.password_nuevo) < PASSWORD_MIN_LEN:
            raise HTTPException(status_code=400, detail=f"La nueva contraseña debe tener al menos {PASSWORD_MIN_LEN} caracteres")
        current_user.hashed_password = get_password_hash(body.password_nuevo)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/usuarios", response_model=UserOut, status_code=201)
def crear_usuario(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RolEnum.admin, RolEnum.jefe_programa, RolEnum.decano)),
):
    if body.rol == RolEnum.admin:
        raise HTTPException(status_code=403, detail="No se pueden crear usuarios con rol administrador a través de esta interfaz.")
    if body.rol in _DEPRECATED_ROLES:
        raise HTTPException(status_code=400, detail=f"El rol '{body.rol.value}' está deshabilitado y no puede asignarse.")
    if current_user.rol in (RolEnum.jefe_programa, RolEnum.decano) and body.rol not in (RolEnum.estudiante, RolEnum.profesor):
        raise HTTPException(status_code=403, detail="El jefe de programa solo puede crear usuarios con rol estudiante o profesor.")
    if db.query(User).filter(User.codigo == body.codigo).first():
        raise HTTPException(status_code=400, detail="El código ya existe")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="El email ya existe")
    if db.query(User).filter(User.cedula == body.cedula).first():
        raise HTTPException(status_code=400, detail="La cédula ya existe")
    if len(body.password) < PASSWORD_MIN_LEN:
        raise HTTPException(status_code=400, detail=f"La contraseña debe tener al menos {PASSWORD_MIN_LEN} caracteres")

    user = User(
        codigo=body.codigo,
        nombres=body.nombres,
        apellidos=body.apellidos,
        email=body.email,
        cedula=body.cedula,
        hashed_password=get_password_hash(body.password),
        rol=body.rol,
        promedio=body.promedio,
        porcentaje_creditos=body.porcentaje_creditos,
        programa=body.programa,
        sede=body.sede,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Recuperación de contraseña por correo (SF-10) ────────────────────────────

class SolicitarResetRequest(BaseModel):
    email: str


class ConfirmarResetRequest(BaseModel):
    token: str
    nueva_password: str


@router.post("/solicitar-reset", status_code=200, summary="Solicitar reset de contraseña por email (SF-10)")
def solicitar_reset(body: SolicitarResetRequest, db: Session = Depends(get_db)):
    from app.models.password_reset import PasswordResetToken
    from app.services.email_service import send_password_reset_email
    from app.core.config import settings

    user = db.query(User).filter(User.email == body.email, User.is_active == True).first()
    # Respuesta genérica para no revelar si el email existe
    if not user:
        return {"message": "Si el correo está registrado, recibirás un enlace en los próximos minutos."}

    # Invalidar tokens anteriores del mismo usuario
    db.query(PasswordResetToken).filter(
        PasswordResetToken.usuario_id == user.id,
        PasswordResetToken.used == False,
    ).update({"used": True})

    token_str = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.add(PasswordResetToken(usuario_id=user.id, token=token_str, expires_at=expires))
    db.commit()

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token_str}"
    send_password_reset_email(user.email, f"{user.nombres} {user.apellidos}", reset_url)
    return {"message": "Si el correo está registrado, recibirás un enlace en los próximos minutos."}


@router.post("/confirmar-reset", status_code=200, summary="Confirmar reset de contraseña (SF-10)")
def confirmar_reset(body: ConfirmarResetRequest, db: Session = Depends(get_db)):
    from app.models.password_reset import PasswordResetToken

    if len(body.nueva_password) < PASSWORD_MIN_LEN:
        raise HTTPException(status_code=400, detail=f"La contraseña debe tener al menos {PASSWORD_MIN_LEN} caracteres")

    prt = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == False,
    ).first()
    if not prt:
        raise HTTPException(status_code=400, detail="Token inválido o ya utilizado")
    if datetime.now(timezone.utc).replace(tzinfo=None) > prt.expires_at.replace(tzinfo=None):
        raise HTTPException(status_code=400, detail="El enlace ha expirado. Solicita uno nuevo.")

    user = db.query(User).filter(User.id == prt.usuario_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    user.hashed_password = get_password_hash(body.nueva_password)
    prt.used = True
    db.commit()
    return {"message": "Contraseña restablecida exitosamente. Ya puedes iniciar sesión."}
