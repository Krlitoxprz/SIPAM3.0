"""
test_monitorias.py — Pruebas del flujo completo de Monitorías
RF-MON-01: Crear convocatoria
RF-MON-02: Postularse
RF-MON-03: Subir documentos
RF-MON-04: Desistir postulación
RF-MON-05: Ejecutar selección
RF-MON-06: Cambiar estado convocatoria
"""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from tests.conftest import get_token, auth, PASSWORD
from app.models.convocatoria import EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.models.postulacion import EstadoPostulacionEnum


# ── PM-001: Listar convocatorias ───────────────────────────────────────────────
def test_listar_convocatorias(client: TestClient, usuario_profesor):
    token = get_token(client, usuario_profesor.codigo)
    r = client.get("/api/v1/convocatorias/", headers=auth(token))
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── PM-002: Crear convocatoria (profesor para su asignatura) ──────────────────
def test_crear_convocatoria(client: TestClient, usuario_profesor, asignatura, db):
    token = get_token(client, usuario_profesor.codigo)
    ahora = datetime.now(timezone.utc)
    r = client.post("/api/v1/convocatorias/", headers=auth(token), json={
        "titulo": "Monitor IS-101 2026-2",
        "asignatura_id": asignatura.id,
        "tipo_monitoria": "academica_cursos",
        "periodo_academico": "2026-2",
        "fecha_inicio_postulacion": (ahora + timedelta(days=1)).isoformat(),
        "fecha_fin_postulacion": (ahora + timedelta(days=12)).isoformat(),
        "num_monitores_requeridos": 1,
        "horas_semana": 8,
        "horas_semestre": 120,
        "promedio_minimo": 3.5,
        "creditos_minimo_pct": 30.0,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["estado"] == "borrador"
    assert data["titulo"] == "Monitor IS-101 2026-2"


# ── PM-003: Estudiante se postula a convocatoria abierta ──────────────────────
def test_postularse_a_convocatoria(client: TestClient, usuario_estudiante, convocatoria):
    token = get_token(client, usuario_estudiante.codigo)
    r = client.post(
        f"/api/v1/postulaciones/convocatoria/{convocatoria.id}",
        headers=auth(token),
        json={"carta_motivacion": "Me interesa ser monitor de IS-101."},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["estado"] == "pendiente"
    assert data["convocatoria_id"] == convocatoria.id


# ── PM-004: Estudiante no puede postularse dos veces ─────────────────────────
def test_postularse_duplicado(client: TestClient, usuario_estudiante, convocatoria, db):
    from app.models.postulacion import Postulacion
    # Asegurar que haya exactamente una postulación (limpia y recrea)
    db.query(Postulacion).filter(
        Postulacion.convocatoria_id == convocatoria.id,
        Postulacion.estudiante_id == usuario_estudiante.id,
    ).delete()
    db.commit()
    p = Postulacion(
        convocatoria_id=convocatoria.id,
        estudiante_id=usuario_estudiante.id,
        promedio_estudiante=4.0,
        carta_motivacion="Ya postulado.",
        estado=EstadoPostulacionEnum.pendiente,
    )
    db.add(p); db.commit()

    token = get_token(client, usuario_estudiante.codigo)
    r = client.post(
        f"/api/v1/postulaciones/convocatoria/{convocatoria.id}",
        headers=auth(token),
        json={"carta_motivacion": "Intento duplicado."},
    )
    assert r.status_code == 409


# ── PM-005: Estudiante no cumple promedio mínimo ──────────────────────────────
def test_postular_sin_promedio_suficiente(client: TestClient, db, usuario_profesor, asignatura):
    from app.models.user import User, RolEnum
    from app.core.security import get_password_hash

    est_bajo = User(
        codigo="EST_BAJO",
        nombres="Estudiante",
        apellidos="Bajo",
        email="bajo@usco.edu.co",
        cedula="99000001",
        hashed_password=get_password_hash(PASSWORD),
        rol=RolEnum.estudiante,
        is_active=True,
        promedio=2.5,
        porcentaje_creditos=60.0,
    )
    db.add(est_bajo); db.commit()

    ahora = datetime.now(timezone.utc)
    conv = Convocatoria_local(
        titulo="Conv promedio alto",
        asignatura_id=asignatura.id,
        profesor_id=usuario_profesor.id,
        tipo_monitoria=TipoMonitoriaEnum.academica_cursos,
        estado=EstadoConvocatoriaEnum.abierta,
        periodo_academico="2026-3",
        fecha_inicio_postulacion=ahora - timedelta(days=1),
        fecha_fin_postulacion=ahora + timedelta(days=10),
        num_monitores_requeridos=1,
        horas_semana=8,
        horas_semestre=120,
        promedio_minimo=4.5,
        creditos_minimo_pct=50.0,
    )
    db.add(conv); db.commit()

    token = get_token(client, est_bajo.codigo)
    r = client.post(
        f"/api/v1/postulaciones/convocatoria/{conv.id}",
        headers=auth(token),
        json={"carta_motivacion": "Promedio insuficiente — debe ser bloqueado."},
    )
    # Los requisitos académicos se aplican siempre, incluso en modo prueba
    assert r.status_code == 422
    assert "requisitos acad" in r.json()["detail"]["mensaje"].lower()


# ── PM-006: Mis postulaciones ─────────────────────────────────────────────────
def test_mis_postulaciones(client: TestClient, usuario_estudiante, convocatoria, db):
    from app.models.postulacion import Postulacion
    # Garantizar que existe al menos una postulación
    existe = db.query(Postulacion).filter(
        Postulacion.convocatoria_id == convocatoria.id,
        Postulacion.estudiante_id == usuario_estudiante.id,
    ).first()
    if not existe:
        db.add(Postulacion(
            convocatoria_id=convocatoria.id,
            estudiante_id=usuario_estudiante.id,
            promedio_estudiante=4.0,
            carta_motivacion="Mi postulación.",
            estado=EstadoPostulacionEnum.pendiente,
        ))
        db.commit()

    token = get_token(client, usuario_estudiante.codigo)
    r = client.get("/api/v1/postulaciones/mis-postulaciones", headers=auth(token))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ── PM-007: Desistir postulación ──────────────────────────────────────────────
def test_desistir_postulacion(client: TestClient, usuario_estudiante, convocatoria, db):
    from app.models.postulacion import Postulacion
    # Limpiar postulación previa si existe
    db.query(Postulacion).filter(
        Postulacion.convocatoria_id == convocatoria.id,
        Postulacion.estudiante_id == usuario_estudiante.id,
    ).delete()
    db.commit()

    p = Postulacion(
        convocatoria_id=convocatoria.id,
        estudiante_id=usuario_estudiante.id,
        promedio_estudiante=4.0,
        carta_motivacion="Me retiro.",
        estado=EstadoPostulacionEnum.pendiente,
    )
    db.add(p); db.commit(); db.refresh(p)

    token = get_token(client, usuario_estudiante.codigo)
    r = client.patch(f"/api/v1/postulaciones/{p.id}/desistir", headers=auth(token))
    assert r.status_code == 200
    assert r.json()["estado"] == "desistido"


# ── PM-008: Ejecutar algoritmo de selección ───────────────────────────────────
def test_ejecutar_seleccion(client: TestClient, usuario_profesor, usuario_estudiante, convocatoria, db):
    from app.models.postulacion import Postulacion
    from app.models.convocatoria import Convocatoria

    conv = db.query(Convocatoria).filter(Convocatoria.id == convocatoria.id).first()
    conv.estado = EstadoConvocatoriaEnum.cerrada
    db.commit()

    # Limpiar postulación previa si existe
    db.query(Postulacion).filter(
        Postulacion.convocatoria_id == convocatoria.id,
        Postulacion.estudiante_id == usuario_estudiante.id,
    ).delete()
    db.commit()

    p = Postulacion(
        convocatoria_id=convocatoria.id,
        estudiante_id=usuario_estudiante.id,
        promedio_estudiante=4.0,
        nota_asignatura=4.2,
        nota_entrevista=4.5,
        carta_motivacion="Listo para selección.",
        estado=EstadoPostulacionEnum.en_revision,
    )
    db.add(p); db.commit()

    token = get_token(client, usuario_profesor.codigo)
    r = client.post(
        f"/api/v1/seleccion/convocatorias/{convocatoria.id}/ejecutar-seleccion",
        headers=auth(token),
    )
    assert r.status_code == 200
    resultados = r.json()
    assert len(resultados) >= 1
    assert resultados[0]["estado"] == "seleccionado"


# ── PM-009: Cambiar estado — en_evaluacion → finalizada ──────────────────────
def test_cambiar_estado_a_cerrada(client: TestClient, usuario_jefe, convocatoria, db):
    from app.models.convocatoria import Convocatoria
    # Asegurar que la convocatoria está en en_evaluacion para pasar a finalizada
    conv = db.query(Convocatoria).filter(Convocatoria.id == convocatoria.id).first()
    conv.estado = EstadoConvocatoriaEnum.en_evaluacion
    db.commit()

    token = get_token(client, usuario_jefe.codigo)
    r = client.patch(
        f"/api/v1/convocatorias/{convocatoria.id}/estado",
        headers=auth(token),
        json={"estado": "finalizada"},
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "finalizada"


# ── PM-010: Postulantes de una convocatoria ───────────────────────────────────
def test_listar_postulantes_convocatoria(client: TestClient, usuario_profesor, convocatoria):
    """Lista postulantes — no requiere crear uno nuevo, usa los existentes."""
    token = get_token(client, usuario_profesor.codigo)
    r = client.get(
        f"/api/v1/postulaciones/convocatoria/{convocatoria.id}",
        headers=auth(token),
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# helper local para PM-005
from app.models.convocatoria import Convocatoria as Convocatoria_local
