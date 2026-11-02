import json
import os
import secrets
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator
from typing import List

DEFAULT_INSECURE_SECRET = "sipam-usco-super-secret-key-2024-change-in-production"
DEFAULT_IOT_API_KEY = "iot_device_key_12345"  # clave pública de ejemplo; inaceptable en producción

# Prefijos típicos de plantillas .env.example que indican "reemplazar aquí".
# Se comparan como prefijo (no substring) para no rechazar claves legítimas
# que casualmente contengan estas palabras (p. ej. 'my-replacement-key').
_PLACEHOLDER_PREFIXES = (
    "GENERA_", "GENERA-", "CAMBIA_", "CAMBIA-",
    "CHANGE_ME", "TU_IP_", "TU_IP-", "REPLACE_", "REPLACE-",
)

# Valores exactos publicados en .env.example / .env.production.example:
# copiarlos tal cual también debe fallar en producción.
_KNOWN_TEMPLATE_VALUES = {
    "CAMBIA-ESTA-CLAVE-EN-PRODUCCION-MIN-32-CARACTERES",
    "CAMBIA-ESTA-CLAVE-IOT",
    "GENERA_UNA_CLAVE_SEGURA_CON_OPENSSL_RAND_-HEX_32",
    "GENERA_UNA_CLAVE_SECRETA_CON_OPENSSL_RAND_-HEX_24",
}


def _es_placeholder(valor: str) -> bool:
    """True si el valor parece un marcador de plantilla que el operador olvidó
    reemplazar (p. ej. 'GENERA_UNA_CLAVE_SECRETA_CON_openssl_rand_-hex_24')."""
    v = (valor or "").upper()
    return v in _KNOWN_TEMPLATE_VALUES or any(v.startswith(m) for m in _PLACEHOLDER_PREFIXES)


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

    # CORS origins - se sobreescribe en producción via CORS_ORIGINS env var.
    # Typed str (no List): pydantic-settings decodifica campos List como JSON y
    # falla con valores separados por coma; cors_origin_list acepta ambos.
    CORS_ORIGINS: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        s = self.CORS_ORIGINS.strip()
        if not s:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        if s.startswith("["):
            try:
                return [str(o).strip() for o in json.loads(s)]
            except (json.JSONDecodeError, TypeError):
                pass
        return [o.strip() for o in s.split(",") if o.strip()]

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
    IOT_API_KEY: str = DEFAULT_IOT_API_KEY

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
        if not self.SECRET_KEY or self.SECRET_KEY == DEFAULT_INSECURE_SECRET or _es_placeholder(self.SECRET_KEY):
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

    @model_validator(mode="after")
    def _ensure_iot_api_key(self):
        """La clave IoT de ejemplo es pública: en producción debe reemplazarse
        por una secreta o cualquiera puede inyectar puntos GPS falsos.
        En desarrollo se permite el default para que el simulador funcione."""
        if self.ENVIRONMENT == "production" or not self.DEBUG:
            if not self.IOT_API_KEY or self.IOT_API_KEY == DEFAULT_IOT_API_KEY or _es_placeholder(self.IOT_API_KEY):
                raise ValueError(
                    "IOT_API_KEY debe configurarse en .env con una clave secreta "
                    "antes de arrancar en producción (la de ejemplo es pública)."
                )
        return self

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
