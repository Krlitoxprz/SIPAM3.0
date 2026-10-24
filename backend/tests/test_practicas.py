"""
test_practicas.py — Pruebas del flujo de Prácticas Extramuros
RF-PRA-01: Crear práctica
RF-PRA-02: Solicitar práctica (borrador → solicitada)
RF-PRA-03: Aprobar (jefe → decano → admin)
RF-PRA-07: Firma de consentimiento
RF-PRA-08: Iniciar y finalizar práctica
"""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from tests.conftest import get_token, auth, PASSWORD
from app.models.practica import EstadoPracticaEnum


def _practica_payload(asignatura_id: int, periodo: str = "2026-1") -> dict:
    ahora = datetime.now(timezone.utc)
    return {
        "nombre_practica": "Visita Empresa Acuícola del Huila",
        "asignatura_id": asignatura_id,
        "periodo_academico": periodo,
        "fecha_inicio": (ahora + timedelta(days=35)).isoformat(),
        "fecha_fin": (ahora + timedelta(days=37)).isoformat(),
        "num_alumnos": 20,
        "caracter_curso": "teorico_practico",
        "caracteristica_curso": "especifico",
        "modalidad_docente": "TCP",
        "tipo_docente": "planta",
        "hora_salida": "06:00",
        "hora_llegada": "18:00",
        "descripcion_practica": "Visita a empresa acuícola para aplicar conceptos de producción.",
        "justificacion": "Permite al estudiante relacionar teoría con práctica en ambiente real.",
        "metodologia": "Observación directa y entrevistas a operarios.",
        "evaluacion": "Informe técnico grupal.",
        "articulacion_curso": "Articulado con unidad 3 del microdiseño curricular.",
        "rutas": [
            {
                "orden": 1,
                "tipo_punto": "salida",
                "lugar": "USCO Sede Neiva",
                "municipio": "Neiva",
                "departamento": "Huila",
                "distancia_km": "0",
                "es_rural": False,
            },
            {
                "orden": 2,
                "tipo_punto": "destino",
                "lugar": "Empresa Acuícola El Juncal",
                "municipio": "Rivera",
                "departamento": "Huila",
                "distancia_km": "25",
                "es_rural": True,
            },
        ],
    }


# ── PP-001: Crear práctica en borrador ────────────────────────────────────────
def test_crear_practica(client: TestClient, usuario_profesor, asignatura, db):
    token = get_token(client, usuario_profesor.codigo)
    r = client.post("/api/v1/practicas/", headers=auth(token),
                    json=_practica_payload(asignatura.id))
    assert r.status_code == 201
    data = r.json()
    assert data["estado"] == "borrador"
    assert data["nombre_practica"] == "Visita Empresa Acuícola del Huila"


# ── PP-002: Solicitar práctica (borrador → solicitada) ─────────────────────────
def test_solicitar_practica(client: TestClient, usuario_profesor, asignatura, db):
    token = get_token(client, usuario_profesor.codigo)

    r = client.post("/api/v1/practicas/", headers=auth(token),
                    json=_practica_payload(asignatura.id, "2026-2"))
    assert r.status_code == 201
    practica_id = r.json()["id"]

    r2 = client.patch(f"/api/v1/practicas/{practica_id}/solicitar", headers=auth(token))
    assert r2.status_code == 200
    assert r2.json()["estado"] == "solicitada"


# ── PP-003: Jefe aprueba práctica (solicitada → aprobada_curriculo) ────────────
def test_jefe_aprueba_practica(client: TestClient, usuario_profesor, usuario_jefe, asignatura, db):
    from app.models.practica import Practica

    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica Test Aprobación",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.solicitada,
        periodo_academico="2026-1",
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=15,
        total_firmas_requeridas=10,
        total_firmas_obtenidas=10,
        quorum_alcanzado=True,
    )
    db.add(p); db.commit(); db.refresh(p)

    token = get_token(client, usuario_jefe.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/aprobar", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["estado"] == "aprobada_curriculo"


# ── PP-004: Decano avala práctica (aprobada_curriculo → aprobada_facultad) ─────
def test_decano_avala_practica(client: TestClient, usuario_profesor, usuario_decano, asignatura, db):
    from app.models.practica import Practica

    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica Test Decano",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.aprobada_curriculo,
        periodo_academico="2026-1",
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=15,
        total_firmas_requeridas=10,
        total_firmas_obtenidas=10,
        quorum_alcanzado=True,
    )
    db.add(p); db.commit(); db.refresh(p)

    token = get_token(client, usuario_decano.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/aprobar", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["estado"] == "aprobada_facultad"


# ── PP-005: Admin aprueba final (aprobada_facultad → aprobado_transporte) ──────
def test_admin_aprueba_final(client: TestClient, usuario_profesor, usuario_admin, asignatura, db):
    from app.models.practica import Practica

    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica Test Admin",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.aprobada_facultad,
        periodo_academico="2026-1",
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=15,
        total_firmas_requeridas=10,
        total_firmas_obtenidas=10,
        quorum_alcanzado=True,
    )
    db.add(p); db.commit(); db.refresh(p)

    token = get_token(client, usuario_admin.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/aprobar", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["estado"] == "aprobado_transporte"


# ── PP-006: Rechazar práctica ─────────────────────────────────────────────────
def test_rechazar_practica(client: TestClient, usuario_profesor, usuario_jefe, asignatura, db):
    from app.models.practica import Practica

    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica Rechazada",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.solicitada,
        periodo_academico="2026-1",
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=15,
    )
    db.add(p); db.commit(); db.refresh(p)

    token = get_token(client, usuario_jefe.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/rechazar", headers=auth(token),
                     json={"observaciones_jefe": "Falta documentación requerida."})
    assert r.status_code == 200
    assert r.json()["estado"] == "rechazada"


# ── PP-007: Iniciar práctica ──────────────────────────────────────────────────
def test_iniciar_practica(client: TestClient, usuario_profesor, asignatura, db):
    from app.models.practica import Practica

    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica Para Iniciar",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.aprobado_transporte,
        periodo_academico="2026-1",
        fecha_inicio=ahora - timedelta(days=1),
        fecha_fin=ahora + timedelta(days=1),
        duracion_dias=3,
        num_alumnos=10,
    )
    db.add(p); db.commit(); db.refresh(p)

    token = get_token(client, usuario_profesor.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/iniciar", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["estado"] == "en_ejecucion"


# ── PP-008: Finalizar práctica con informe ────────────────────────────────────
def test_finalizar_practica(client: TestClient, usuario_profesor, asignatura, db):
    from app.models.practica import Practica

    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica Para Finalizar",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.en_ejecucion,
        periodo_academico="2026-1",
        fecha_inicio=ahora - timedelta(days=3),
        fecha_fin=ahora - timedelta(days=1),
        duracion_dias=3,
        num_alumnos=10,
    )
    db.add(p); db.commit(); db.refresh(p)

    token = get_token(client, usuario_profesor.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/finalizar", headers=auth(token),
                     json={
                         "informe_resultados": "Se visitó la empresa y se cumplieron todos los objetivos.",
                         "observaciones": "Sin novedad.",
                     })
    assert r.status_code == 200
    assert r.json()["estado"] == "finalizada"


# ── PP-009: Listar prácticas ──────────────────────────────────────────────────
def test_listar_practicas(client: TestClient, usuario_profesor):
    token = get_token(client, usuario_profesor.codigo)
    r = client.get("/api/v1/practicas/", headers=auth(token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── PP-010: Historial de estados ──────────────────────────────────────────────
def test_historial_practica(client: TestClient, usuario_profesor, asignatura, db):
    from app.models.practica import Practica

    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica Historial",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        estado=EstadoPracticaEnum.solicitada,
        periodo_academico="2026-1",
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=10,
    )
    db.add(p); db.commit(); db.refresh(p)

    from app.utils.historial import registrar_historial
    from app.db.database import get_db as real_get_db
    registrar_historial(db, "practica", p.id, "borrador", "solicitada", usuario_profesor.id)
    db.commit()

    token = get_token(client, usuario_profesor.codigo)
    r = client.get(f"/api/v1/practicas/{p.id}/historial", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 1
