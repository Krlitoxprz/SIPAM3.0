import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


def parse_cors_origins() -> List[str]:
    """Parse CORS_ORIGINS from env var (comma-separated) or return defaults."""
    cors_env = os.getenv("CORS_ORIGINS", "")
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


class Settings(BaseSettings):
    APP_NAME: str = "SIPAM-USCO"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True   # Sobreescribir con DEBUG=False en .env de producción

    SECRET_KEY: str = "sipam-usco-super-secret-key-2024-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # SQLite (desarrollo): sqlite:///./sipam_usco.db
    # PostgreSQL (producción): postgresql://user:pass@host:5432/sipam_db
    DATABASE_URL: str = "sqlite:///./sipam_usco.db"
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10

    # CORS origins - se sobreescribe en producción via CORS_ORIGINS env var
    CORS_ORIGINS: List[str] = parse_cors_origins()

    ADMIN_PASSWORD: str = "Sasuke24"  # Contraseña del superusuario admin — cambiar en .env
    ORS_API_KEY: str = ""  # OpenRouteService — gratuito en openrouteservice.org

    # SMTP — correo electrónico (SF-02, SF-10). Configura en .env para habilitar.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    SMTP_TLS: bool = True

    # URL pública del frontend para links en emails
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
