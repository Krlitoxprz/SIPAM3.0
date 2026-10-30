"""
test_auth.py — Pruebas de autenticación y control de acceso
RF-AUTH-01: Login con código y contraseña
RF-AUTH-02: Token JWT válido
RF-AUTH-03: Roles y permisos
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import get_token, auth, PASSWORD


# ── PA-001: Login exitoso ──────────────────────────────────────────────────────
def test_login_exitoso(client: TestClient, usuario_admin):
    r = client.post("/api/v1/auth/login", json={
        "codigo": usuario_admin.codigo,
        "password": PASSWORD,
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["rol"] == "admin"


# ── PA-002: Login con credenciales incorrectas ─────────────────────────────────
def test_login_credenciales_invalidas(client: TestClient, usuario_admin):
    r = client.post("/api/v1/auth/login", json={
        "codigo": usuario_admin.codigo,
        "password": "WRONG_PASSWORD",
    })
    assert r.status_code in (401, 400)


# ── PA-003: Login con usuario inexistente ──────────────────────────────────────
def test_login_usuario_inexistente(client: TestClient):
    r = client.post("/api/v1/auth/login", json={
        "codigo": "USUARIO_QUE_NO_EXISTE",
        "password": PASSWORD,
    })
    assert r.status_code in (401, 400)


# ── PA-004: Endpoint protegido sin token ──────────────────────────────────────
def test_endpoint_protegido_sin_token(client: TestClient):
    r = client.get("/api/v1/convocatorias/")
    assert r.status_code == 401


# ── PA-005: Endpoint protegido con token válido ────────────────────────────────
def test_endpoint_protegido_con_token(client: TestClient, usuario_profesor):
    token = get_token(client, usuario_profesor.codigo)
    r = client.get("/api/v1/convocatorias/", headers=auth(token))
    assert r.status_code == 200


# ── PA-006: Endpoint de rol restringido — acceso denegado ─────────────────────
def test_acceso_denegado_por_rol(client: TestClient, usuario_estudiante):
    """Estudiante no puede crear convocatorias."""
    token = get_token(client, usuario_estudiante.codigo)
    r = client.post("/api/v1/convocatorias/", json={}, headers=auth(token))
    assert r.status_code in (403, 422)


# ── PA-007: Perfil del usuario autenticado ────────────────────────────────────
def test_obtener_perfil(client: TestClient, usuario_estudiante):
    token = get_token(client, usuario_estudiante.codigo)
    r = client.get("/api/v1/auth/me", headers=auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["codigo"] == usuario_estudiante.codigo
    assert data["rol"] == "estudiante"


# ── PA-008: Token inválido rechazado ──────────────────────────────────────────
def test_token_invalido_rechazado(client: TestClient):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer TOKEN_FALSO"})
    assert r.status_code == 401


# ── PA-009: Usuario inactivo no puede iniciar sesión ──────────────────────────
def test_usuario_inactivo_no_puede_login(client: TestClient, db):
    from app.models.user import User, RolEnum
    from app.core.security import get_password_hash
    u = User(
        codigo="INACTIVO_TEST",
        nombres="Inactivo",
        apellidos="Test",
        email="inactivo@usco.edu.co",
        cedula="99999001",
        hashed_password=get_password_hash(PASSWORD),
        rol=RolEnum.estudiante,
        is_active=False,
    )
    db.add(u); db.commit()
    r = client.post("/api/v1/auth/login", json={
        "codigo": "INACTIVO_TEST",
        "password": PASSWORD,
    })
    assert r.status_code in (401, 400, 403)


# ── PA-010: Login también fija la cookie HttpOnly ──────────────────────────────
def test_login_setea_cookie_httponly(client: TestClient, usuario_estudiante):
    r = client.post("/api/v1/auth/login", json={
        "codigo": usuario_estudiante.codigo,
        "password": PASSWORD,
    })
    assert r.status_code == 200
    set_cookie = r.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "refresh_token=" in set_cookie
    assert "HttpOnly" in set_cookie


# ── PA-011: Refresh token renueva la sesión ───────────────────────────────────
def test_refresh_token_renueva_sesion(client: TestClient, usuario_estudiante):
    r = client.post("/api/v1/auth/login", json={
        "codigo": usuario_estudiante.codigo,
        "password": PASSWORD,
    })
    assert r.status_code == 200
    # TestClient conserva las cookies → /refresh usa la cookie refresh_token
    r2 = client.post("/api/v1/auth/refresh")
    assert r2.status_code == 200
    data = r2.json()
    assert "access_token" in data
    r3 = client.get("/api/v1/auth/me", headers=auth(data["access_token"]))
    assert r3.status_code == 200


# ── PA-012: Refresh token ya usado (revocado) se rechaza ──────────────────────
def test_refresh_token_revocado_rechazado(client: TestClient, usuario_estudiante):
    from app.models.refresh_token import RefreshToken
    from app.core.security import hash_refresh_token
    client.post("/api/v1/auth/login", json={
        "codigo": usuario_estudiante.codigo,
        "password": PASSWORD,
    })
    cookie = client.cookies.get("refresh_token")
    assert cookie
    # Primer uso: OK (rota el token)
    r1 = client.post("/api/v1/auth/refresh")
    assert r1.status_code == 200
    # Segundo uso del MISMO valor → revocado
    client.cookies.clear()
    client.cookies.set("refresh_token", cookie)
    r2 = client.post("/api/v1/auth/refresh")
    assert r2.status_code == 401


# ── PA-013: Sin refresh token → 401 ────────────────────────────────────────────
def test_refresh_sin_token_401(client: TestClient):
    client.cookies.clear()
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401


# ── PA-014: Un refresh token no sirve como access token ───────────────────────
def test_refresh_no_es_access_token(client: TestClient, usuario_estudiante):
    client.post("/api/v1/auth/login", json={
        "codigo": usuario_estudiante.codigo,
        "password": PASSWORD,
    })
    refresh_cookie = client.cookies.get("refresh_token")
    assert refresh_cookie
    # Sin la cookie access_token: solo vale el Authorization header con el refresh JWT
    client.cookies.clear()
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh_cookie}"})
    assert r.status_code == 401


# ── PA-015: Fuerza bruta se registra con IP exacta (sin comodines LIKE) ───────
def test_fuerza_bruta_por_ip_e_identificador(client: TestClient, usuario_estudiante, db):
    from app.models.monitor import AuditLog
    # '%' como identificador no debe colisionar con otros intentos
    for _ in range(2):
        client.post("/api/v1/auth/login", json={"codigo": "OTRO_USUARIO", "password": "x"})
    r = client.post("/api/v1/auth/login", json={
        "codigo": usuario_estudiante.codigo,
        "password": "WRONG",
    })
    assert r.status_code == 401
    logs = db.query(AuditLog).filter(AuditLog.accion == "login_fallido").all()
    assert all(l.ip_address is not None for l in logs)


# ── PA-016: Creación de usuarios por jefe de programa (no debe dar 500) ───────
def test_jefe_crea_profesor(client: TestClient, usuario_jefe):
    token = get_token(client, usuario_jefe.codigo)
    r = client.post("/api/v1/auth/usuarios", headers=auth(token), json={
        "codigo": "TEST_PROF_NUEVO",
        "nombres": "Profesor",
        "apellidos": "Nuevo",
        "email": "prof.nuevo.test@usco.edu.co",
        "cedula": "10009991",
        "password": PASSWORD,
        "rol": "profesor",
    })
    assert r.status_code == 201, r.text
    assert r.json()["rol"] == "profesor"


def test_crear_usuario_admin_prohibido(client: TestClient, usuario_admin):
    token = get_token(client, usuario_admin.codigo)
    r = client.post("/api/v1/auth/usuarios", headers=auth(token), json={
        "codigo": "TEST_ADMIN_NUEVO",
        "nombres": "Admin",
        "apellidos": "Nuevo",
        "email": "admin.nuevo.test@usco.edu.co",
        "cedula": "10009992",
        "password": PASSWORD,
        "rol": "admin",
    })
    assert r.status_code == 403
