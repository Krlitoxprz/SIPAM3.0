"""
Tests de permisos de descarga de documentos adjuntos.

Cubren los dos endpoints equivalentes:
- GET /api/v1/archivos/{id}
- GET /api/v1/postulaciones/documentos/{id}/descargar

Ambos deben aplicar las mismas reglas: propietario, admin/jefe/decano y
profesor titular de la convocatoria de la postulación.

Usa su propia asignatura/convocatoria/estudiante para no interferir con los
tests que asumen que usuario_estudiante aún no se postuló a `convocatoria`.
"""
import os

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.convocatoria import Asignatura, Convocatoria, EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.models.postulacion import ArchivoAdjunto, EstadoPostulacionEnum, Postulacion
from app.models.user import RolEnum, User
from tests.conftest import PASSWORD, auth, get_token


def _get_or_create_user(db, codigo, **kwargs):
    u = db.query(User).filter(User.codigo == codigo).first()
    if u:
        return u
    u = User(codigo=codigo, hashed_password=get_password_hash(PASSWORD), is_active=True, **kwargs)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture(scope="function")
def estudiante_dl(db):
    return _get_or_create_user(
        db, "TEST_EST_DL",
        nombres="Est", apellidos="Descarga", email="estdl.test@usco.edu.co",
        cedula="30000010", rol=RolEnum.estudiante, promedio=4.0, porcentaje_creditos=60.0,
        programa="Ingeniería de Software",
    )


@pytest.fixture(scope="function")
def profesor_otro(db):
    return _get_or_create_user(
        db, "TEST_PROF2",
        nombres="Otro", apellidos="Profesor", email="prof2.test@usco.edu.co",
        cedula="20000002", rol=RolEnum.profesor,
    )


@pytest.fixture(scope="function")
def convocatoria_dl(db, usuario_profesor):
    """Convocatoria propia para estas pruebas (titular: usuario_profesor)."""
    conv = db.query(Convocatoria).filter(Convocatoria.titulo == "Monitor DL test").first()
    if conv:
        return conv

    asig = db.query(Asignatura).filter(Asignatura.codigo == "DL-101").first()
    if not asig:
        asig = Asignatura(
            codigo="DL-101", nombre="Descarga Test", programa="Ingeniería de Software",
            facultad="Ingeniería", creditos=3, semestre=4, profesor_id=usuario_profesor.id,
            is_active=True, caracter_curso="teorico_practico", caracteristica_curso="especifico",
        )
        db.add(asig)
        db.commit()
        db.refresh(asig)

    from datetime import datetime, timedelta, timezone
    ahora = datetime.now(timezone.utc)
    conv = Convocatoria(
        titulo="Monitor DL test", asignatura_id=asig.id, profesor_id=usuario_profesor.id,
        tipo_monitoria=TipoMonitoriaEnum.academica_cursos, estado=EstadoConvocatoriaEnum.en_evaluacion,
        periodo_academico="2026-1",
        fecha_inicio_postulacion=ahora - timedelta(days=20),
        fecha_fin_postulacion=ahora - timedelta(days=10),
        num_monitores_requeridos=1, horas_semana=8, horas_semestre=120,
        promedio_minimo=3.5, creditos_minimo_pct=30.0,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@pytest.fixture(scope="function")
def archivo_postulacion(db, estudiante_dl, convocatoria_dl):
    """Postulación de estudiante_dl con un documento PDF real en UPLOAD_DIR."""
    post = db.query(Postulacion).filter(
        Postulacion.convocatoria_id == convocatoria_dl.id,
        Postulacion.estudiante_id == estudiante_dl.id,
    ).first()
    if not post:
        post = Postulacion(
            convocatoria_id=convocatoria_dl.id,
            estudiante_id=estudiante_dl.id,
            estado=EstadoPostulacionEnum.pendiente,
            promedio_estudiante=4.0,
            carta_motivacion="x" * 40,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

    rel_dir = os.path.join("postulaciones", "test_descarga")
    abs_dir = os.path.join(settings.UPLOAD_DIR, rel_dir)
    os.makedirs(abs_dir, exist_ok=True)
    nombre_almacenado = "doc_descarga_test.pdf"
    abs_path = os.path.join(abs_dir, nombre_almacenado)
    with open(abs_path, "wb") as f:
        f.write(b"%PDF-1.4 test")

    archivo = db.query(ArchivoAdjunto).filter(
        ArchivoAdjunto.postulacion_id == post.id,
        ArchivoAdjunto.tipo_documento == "cedula",
    ).first()
    if not archivo:
        archivo = ArchivoAdjunto(
            postulacion_id=post.id,
            usuario_id=estudiante_dl.id,
            tipo_documento="cedula",
            nombre_original="cedula.pdf",
            nombre_almacenado=nombre_almacenado,
            ruta_archivo=os.path.join(rel_dir, nombre_almacenado),
            ruta_completa=abs_path,
            tipo_mime="application/pdf",
            tamanio_bytes=14,
        )
        db.add(archivo)
        db.commit()
        db.refresh(archivo)
    return archivo


ENDPOINTS = [
    "/api/v1/archivos/{id}",
    "/api/v1/postulaciones/documentos/{id}/descargar",
]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_propietario_descarga(client: TestClient, estudiante_dl, archivo_postulacion, endpoint):
    token = get_token(client, "TEST_EST_DL")
    r = client.get(endpoint.format(id=archivo_postulacion.id), headers=auth(token))
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_profesor_titular_descarga(client: TestClient, usuario_profesor, archivo_postulacion, endpoint):
    token = get_token(client, "TEST_PROF")
    r = client.get(endpoint.format(id=archivo_postulacion.id), headers=auth(token))
    assert r.status_code == 200


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_profesor_no_titular_403(client: TestClient, profesor_otro, archivo_postulacion, endpoint):
    token = get_token(client, "TEST_PROF2")
    r = client.get(endpoint.format(id=archivo_postulacion.id), headers=auth(token))
    assert r.status_code == 403


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_jefe_descarga(client: TestClient, usuario_jefe, archivo_postulacion, endpoint):
    token = get_token(client, "TEST_JEFE")
    r = client.get(endpoint.format(id=archivo_postulacion.id), headers=auth(token))
    assert r.status_code == 200


@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_estudiante_ajeno_403(client: TestClient, usuario_estudiante, archivo_postulacion, endpoint):
    token = get_token(client, "TEST_EST")
    r = client.get(endpoint.format(id=archivo_postulacion.id), headers=auth(token))
    assert r.status_code == 403
