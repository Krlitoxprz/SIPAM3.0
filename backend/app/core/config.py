import os
import secrets
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator
from typing import List

DEFAULT_INSECURE_SECRET = "sipam-usco-super-secret-key-2024-change-in-production"


def parse_cors_origins() -> List[str]:
    """Parse CORS_ORIGINS from env var (comma-separated) or return defaults."""
    cors_env = os.getenv("CORS_ORIGINS", "")
    if cors_env:
        return [origin.strip() for origin in cors_env.split(",") if origin.strip()]
    return ["http://localhost:5173", "http://127.0.0.1:5173"]


class Settings(BaseSettings):
    APP_NAME: str = "SIPAM-USCO"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True   # Sobreescribir con DEBUG=False en .env de producción
    ENVIRONMENT: str = "development"  # development | production

    SECRET_KEY: str = ""  # MUST be set in .env for production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Reduced to 30 min for security
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # SQLite (desarrollo): sqlite:///./sipam_usco.db
    # PostgreSQL (producción): postgresql://user:pass@host:5432/sipam_db
    DATABASE_URL: str = "sqlite:///./sipam_usco.db"
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 5  # Reduced to 5 MB for security

    # CORS origins - se sobreescribe en producción via CORS_ORIGINS env var
    CORS_ORIGINS: List[str] = parse_cors_origins()

    ADMIN_PASSWORD: str = ""  # MUST be set in .env for production
    ORS_API_KEY: str = ""  # OpenRouteService — gratuito en openrouteservice.org

    # SMTP — correo electrónico (SF-02, SF-10). Configura en .env para habilitar.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = ""
    SMTP_TLS: bool = True

    # API key compartida para dispositivos IoT (ESP32 / simulador GPS)
    IOT_API_KEY: str = "iot_device_key_12345"

    # URL del microservicio de IA (OCR/NLP)
    AI_SERVICE_URL: str = "http://localhost:5001"

    # URL pública del frontend para links en emails
    FRONTEND_URL: str = "http://localhost:5173"

    # Cookie settings for JWT
    COOKIE_DOMAIN: str = ""
    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS)
    COOKIE_SAMESITE: str = "lax"

    @model_validator(mode="after")
    def _ensure_secret_key(self):
        """SECRET_KEY nunca puede quedar vacía ni ser la clave de ejemplo.

        Producción: se aborta el arranque. Desarrollo: se genera una clave
        aleatoria por proceso (las sesiones no sobreviven reinicios, que es
        aceptable en dev y evita firmar JWTs con una clave conocida/vacía).
        """
        if not self.SECRET_KEY or self.SECRET_KEY == DEFAULT_INSECURE_SECRET:
            if self.ENVIRONMENT == "production" or not self.DEBUG:
                raise ValueError(
                    "SECRET_KEY debe configurarse en .env con una clave segura (mín. 32 caracteres) "
                    "antes de arrancar en producción."
                )
            import warnings
            warnings.warn(
                "SECRET_KEY no configurada: se generó una clave aleatoria de desarrollo. "
                "Define SECRET_KEY en backend/.env para mantener sesiones entre reinicios."
            )
            self.SECRET_KEY = secrets.token_urlsafe(32)
        return self

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
