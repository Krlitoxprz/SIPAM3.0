from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.security import verify_token
from app.models.user import User, RolEnum

bearer_scheme = HTTPBearer(auto_error=False)

def get_token_from_request(request: Request) -> str | None:
    """Extract JWT token from cookie or Authorization header."""
    # Try cookie first (HttpOnly)
    token = request.cookies.get("access_token")
    if token:
        return token

    # Fall back to Authorization header
    return None

def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    # Try cookie first
    token = get_token_from_request(request)

    # Fall back to Authorization header
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionó token de autenticación",
        )

    user_id = verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )
    return user


def require_roles(*roles: RolEnum):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Rol requerido: {[r.value for r in roles]}",
            )
        return current_user
    return checker


def verificar_programa_jefe(current_user: User, programa: str | None) -> None:
    """Un jefe_programa solo puede mutar recursos de su propio programa.

    Se compara con `Asignatura.programa`, la misma dimensión que usan los listados.
    Un jefe sin programa asignado no tiene jurisdicción sobre ningún recurso.
    """
    if current_user.rol != RolEnum.jefe_programa:
        return
    if not current_user.programa or programa != current_user.programa:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo puede gestionar recursos de su propio programa académico",
        )
