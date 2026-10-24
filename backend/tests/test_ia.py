"""
test_ia.py — Pruebas del módulo de Inteligencia Artificial
RF-IA-01: Endpoint de recomendaciones (con fallback heurístico)
RF-IA-02: Endpoint de predicción
"""
import pytest
from fastapi.testclient import TestClient
from tests.conftest import get_token, auth


# ── PIA-001: Recomendaciones retornan estructura correcta ─────────────────────
def test_recomendaciones_estructura(client: TestClient, usuario_estudiante):
    token = get_token(client, usuario_estudiante.codigo)
    r = client.get("/api/v1/ia/recomendaciones", headers=auth(token))
    assert r.status_code == 200
    data = r.json()
    assert "recomendaciones" in data
    assert "total_elegibles" in data
    assert "fuente" in data
    assert isinstance(data["recomendaciones"], list)


# ── PIA-002: Solo estudiantes pueden pedir recomendaciones ────────────────────
def test_recomendaciones_solo_estudiante(client: TestClient, usuario_profesor):
    token = get_token(client, usuario_profesor.codigo)
    r = client.get("/api/v1/ia/recomendaciones", headers=auth(token))
    assert r.status_code == 403


# ── PIA-003: Recomendaciones sin convocatorias abiertas retorna lista vacía ───
def test_recomendaciones_sin_convocatorias(client: TestClient, usuario_estudiante):
    token = get_token(client, usuario_estudiante.codigo)
    r = client.get("/api/v1/ia/recomendaciones?limite=5", headers=auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total_elegibles"] == 0
    assert data["recomendaciones"] == []


# ── PIA-004: Con convocatoria abierta elegible ────────────────────────────────
def test_recomendaciones_con_convocatoria_elegible(
    client: TestClient, usuario_estudiante, convocatoria
):
    token = get_token(client, usuario_estudiante.codigo)
    r = client.get("/api/v1/ia/recomendaciones?limite=10", headers=auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total_elegibles"] >= 1
    rec = data["recomendaciones"][0]
    assert "probabilidad_pct" in rec
    assert "titulo" in rec
    assert "programa_match" in rec
    assert 0.0 <= rec["probabilidad_pct"] <= 100.0


# ── PIA-005: Parámetro limite funciona ────────────────────────────────────────
def test_recomendaciones_limite(client: TestClient, usuario_estudiante, convocatoria):
    token = get_token(client, usuario_estudiante.codigo)
    r = client.get("/api/v1/ia/recomendaciones?limite=1", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()["recomendaciones"]) <= 1


# ── PIA-006: Predicción IA sin servicio Flask → error 503 ────────────────────
def test_prediccion_sin_servicio_ia(client: TestClient, usuario_profesor):
    """Si el servicio Flask no está disponible, retorna 503."""
    import os
    original = os.environ.get("AI_SERVICE_URL", "http://localhost:5001")
    os.environ["AI_SERVICE_URL"] = "http://localhost:9999"  # puerto imposible

    token = get_token(client, usuario_profesor.codigo)
    r = client.post("/api/v1/ia/predecir", headers=auth(token), json={
        "promedio": 4.0,
        "porcentaje_creditos": 60.0,
        "nota_asignatura": 4.2,
        "nota_entrevista": 3.8,
        "tipo_monitoria": "academica_cursos",
        "semestre_asignatura": 4,
        "creditos_asignatura": 3,
        "num_postulantes": 5,
        "num_monitores_requeridos": 1,
    })
    os.environ["AI_SERVICE_URL"] = original
    assert r.status_code in (200, 503, 504)


# ── PIA-007: Validación parámetros predicción ─────────────────────────────────
def test_prediccion_parametros_invalidos(client: TestClient, usuario_profesor):
    token = get_token(client, usuario_profesor.codigo)
    r = client.post("/api/v1/ia/predecir", headers=auth(token), json={
        "promedio": 10.0,   # inválido: máximo es 5.0
        "porcentaje_creditos": 60.0,
        "nota_asignatura": 4.0,
        "nota_entrevista": 3.5,
    })
    assert r.status_code == 422
