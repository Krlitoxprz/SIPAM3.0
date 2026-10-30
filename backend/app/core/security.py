from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import hashlib
import bcrypt
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings


def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "typ": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """JWT de larga duración (REFRESH_TOKEN_EXPIRE_DAYS) marcado como typ=refresh.
    Incluye jti aleatorio: sin él, dos tokens emitidos en el mismo segundo serían idénticos."""
    import uuid
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "typ": "refresh", "jti": uuid.uuid4().hex}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def hash_refresh_token(token: str) -> str:
    """SHA-256 del refresh token; es lo único que se persiste en BD."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Tokens antiguos sin 'typ' se tratan como access tokens
        if payload.get("typ", "access") != token_type:
            return None
        return payload.get("sub")
    except InvalidTokenError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
