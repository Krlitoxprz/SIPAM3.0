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
