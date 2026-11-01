"""
Tests de la segunda ronda de revisión (Devin Review sobre el PR de auditoría).

Cubre:
- Middleware CSRF: match exacto de origen, cookie ambiental obliga a Origin,
  Authorization no desactiva la protección, clientes sin cookie no se afectan.
- Logout funciona con access token expirado (solo cookie refresh).
- IoT: API key equivocada, timestamp epoch-ms grande, RBAC de consultas GPS.
- Config: IOT_API_KEY por defecto no vale en producción.
"""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import PASSWORD, auth, get_token

ORIGIN_OK = "http://localhost:5173"


# ── CSRF middleware ───────────────────────────────────────────────────────────

def test_csrf_origen_sufijo_evil_403(client: TestClient, usuario_estudiante):
    """'localhost:5173.evil.com' ya no pasa el check (era startswith)."""
    get_token(client, "TEST_EST")
    r = client.post("/api/v1/auth/logout", headers={"Origin": "http://localhost:5173.evil.com"})
    assert r.status_code == 403


def test_csrf_origen_valido_pasa(client: TestClient, usuario_estudiante):
    get_token(client, "TEST_EST")
    r = client.post("/api/v1/auth/logout", headers={"Origin": ORIGIN_OK})
    assert r.status_code == 200


def test_csrf_cookie_sin_origen_403(client: TestClient, usuario_estudiante):
    """Con cookie de sesión, una mutación sin Origin/Referer se rechaza."""
    get_token(client, "TEST_EST")
    r = client.post("/api/v1/auth/logout", headers={"Origin": ""})
    assert r.status_code == 403


def test_csrf_authorization_no_desactiva_check(client: TestClient, usuario_estudiante):
    """Authorization no desactiva la defensa: con cookie presente y sin
    origen verificable sigue siendo 403 (get_current_user prioriza cookie)."""
    token = get_token(client, "TEST_EST")
    r = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "", "Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_csrf_sin_cookie_no_aplica(client: TestClient):
    """Sin cookie de sesión el middleware no bloquea (Authorization no es
    ambiental): /auth/refresh llega al endpoint y responde 401 propio, no 403."""
    client.cookies.clear()
    r = client.post("/api/v1/auth/refresh", headers={"Origin": ""})
    assert r.status_code == 401


# ── Logout con access expirado ────────────────────────────────────────────────

def test_logout_solo_con_refresh_cookie(client: TestClient, usuario_estudiante):
    """Con el access token ausente/expirado, logout debe revocar el refresh
    igualmente (antes daba 401 por get_current_user)."""
    get_token(client, "TEST_EST")
    client.cookies.delete("access_token")
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # El refresh quedó revocado: ya no renueva
    r2 = client.post("/api/v1/auth/refresh")
    assert r2.status_code == 401


def test_logout_sin_sesion_idempotente(client: TestClient):
    client.cookies.clear()
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200


# ── IoT ───────────────────────────────────────────────────────────────────────

def _iot_headers(key="iot_device_key_12345"):
    return {"x-api-key": key, "Origin": ORIGIN_OK}


def test_iot_post_epoch_ms_grande(client: TestClient):
    """Epoch en milisegundos (~1.7e12) desbordaba INTEGER de PostgreSQL."""
    r = client.post(
        "/api/v1/iot/tracking/",
        headers=_iot_headers(),
        json={
            "device_id": "ESP32_TEST_BIGTS",
            "practice_id": "PRAC_BIGTS",
            "timestamp": 1793540000000,
            "latitude": 2.44, "longitude": -76.60,
        },
    )
    assert r.status_code == 201, r.text


def test_iot_api_key_invalida_401(client: TestClient):
    r = client.post(
        "/api/v1/iot/tracking/",
        headers=_iot_headers("clave_falsa"),
        json={"device_id": "d", "practice_id": "p", "timestamp": 1,
              "latitude": 1.0, "longitude": 1.0},
    )
    assert r.status_code == 401


def test_iot_get_profesor_403_jefe_200(client: TestClient, usuario_profesor, usuario_jefe):
    """La consulta de recorridos GPS ya no es accesible por cualquier profesor."""
    tok_prof = get_token(client, "TEST_PROF")
    r = client.get("/api/v1/iot/tracking/PRAC_BIGTS", headers=auth(tok_prof))
    assert r.status_code == 403

    tok_jefe = get_token(client, "TEST_JEFE")
    r = client.get("/api/v1/iot/tracking/PRAC_BIGTS", headers=auth(tok_jefe))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_iot_key_default_falla_en_produccion():
    """El default público de IOT_API_KEY no es aceptable en producción."""
    from app.core.config import Settings, DEFAULT_IOT_API_KEY
    with pytest.raises(Exception):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="x" * 40,
            IOT_API_KEY=DEFAULT_IOT_API_KEY,
            _env_file=None,
        )
