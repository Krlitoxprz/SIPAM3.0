"""
test_jefe_scoping_programa.py — Un jefe_programa solo puede mutar prácticas y
convocatorias de asignaturas de su propio programa.
"""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from tests.conftest import get_token, auth
from app.models.convocatoria import Convocatoria, EstadoConvocatoriaEnum, TipoMonitoriaEnum
from app.models.practica import Practica, EstadoPracticaEnum


def _crear_practica(db, asignatura, profesor, estado: EstadoPracticaEnum) -> Practica:
    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica scoping programa",
        asignatura_id=asignatura.id,
        profesor_id=profesor.id,
        estado=estado,
        periodo_academico="2099-9",
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=15,
        total_firmas_requeridas=10,
        total_firmas_obtenidas=10,
        quorum_alcanzado=True,
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


def _estado_practica(db, practica_id: int) -> EstadoPracticaEnum:
    db.expire_all()
    return db.query(Practica).filter(Practica.id == practica_id).first().estado


def test_jefe_otro_programa_no_aprueba_practica(client: TestClient, usuario_profesor,
                                                usuario_jefe_otro_programa, asignatura, db):
    p = _crear_practica(db, asignatura, usuario_profesor, EstadoPracticaEnum.solicitada)
    token = get_token(client, usuario_jefe_otro_programa.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/aprobar", headers=auth(token))
    assert r.status_code == 403
    assert _estado_practica(db, p.id) == EstadoPracticaEnum.solicitada


def test_jefe_otro_programa_no_rechaza_practica(client: TestClient, usuario_profesor,
                                                usuario_jefe_otro_programa, asignatura, db):
    p = _crear_practica(db, asignatura, usuario_profesor, EstadoPracticaEnum.solicitada)
    token = get_token(client, usuario_jefe_otro_programa.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/rechazar", headers=auth(token),
                     json={"observaciones_jefe": "No corresponde"})
    assert r.status_code == 403
    assert _estado_practica(db, p.id) == EstadoPracticaEnum.solicitada


def test_jefe_otro_programa_no_edita_practica(client: TestClient, usuario_profesor,
                                              usuario_jefe_otro_programa, asignatura, db):
    p = _crear_practica(db, asignatura, usuario_profesor, EstadoPracticaEnum.solicitada)
    token = get_token(client, usuario_jefe_otro_programa.codigo)
    r = client.put(f"/api/v1/practicas/{p.id}", headers=auth(token),
                   json={"nombre_practica": "Editada por jefe ajeno"})
    assert r.status_code == 403
    db.expire_all()
    assert db.query(Practica).filter(Practica.id == p.id).first().nombre_practica == "Práctica scoping programa"


def test_jefe_otro_programa_no_finaliza_practica(client: TestClient, usuario_profesor,
                                                 usuario_jefe_otro_programa, asignatura, db):
    p = _crear_practica(db, asignatura, usuario_profesor, EstadoPracticaEnum.en_ejecucion)
    token = get_token(client, usuario_jefe_otro_programa.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/finalizar", headers=auth(token),
                     json={"informe_resultados": "Cierre ajeno"})
    assert r.status_code == 403
    assert _estado_practica(db, p.id) == EstadoPracticaEnum.en_ejecucion


def test_jefe_mismo_programa_edita_practica(client: TestClient, usuario_profesor,
                                            usuario_jefe, asignatura, db):
    p = _crear_practica(db, asignatura, usuario_profesor, EstadoPracticaEnum.solicitada)
    token = get_token(client, usuario_jefe.codigo)
    r = client.put(f"/api/v1/practicas/{p.id}", headers=auth(token),
                   json={"nombre_practica": "Editada por jefe del programa"})
    assert r.status_code == 200
    assert r.json()["nombre_practica"] == "Editada por jefe del programa"


def _crear_convocatoria(db, asignatura, profesor, periodo: str) -> Convocatoria:
    ahora = datetime.now(timezone.utc)
    c = Convocatoria(
        titulo="Convocatoria scoping programa",
        asignatura_id=asignatura.id,
        profesor_id=profesor.id,
        tipo_monitoria=TipoMonitoriaEnum.academica_cursos,
        estado=EstadoConvocatoriaEnum.borrador,
        periodo_academico=periodo,
        fecha_inicio_postulacion=ahora + timedelta(days=1),
        fecha_fin_postulacion=ahora + timedelta(days=10),
        num_monitores_requeridos=1,
        horas_semana=8,
        horas_semestre=120,
        promedio_minimo=3.5,
        creditos_minimo_pct=30.0,
    )
    db.add(c); db.commit(); db.refresh(c)
    return c


def test_jefe_otro_programa_no_modifica_convocatoria(client: TestClient, usuario_profesor,
                                                     usuario_jefe_otro_programa, usuario_jefe,
                                                     asignatura, db):
    c = _crear_convocatoria(db, asignatura, usuario_profesor, "2099-8")
    token_otro = get_token(client, usuario_jefe_otro_programa.codigo)

    r = client.put(f"/api/v1/convocatorias/{c.id}", headers=auth(token_otro),
                   json={"titulo": "Editada por jefe ajeno", "promedio_minimo": 1.0})
    assert r.status_code == 403

    r = client.patch(f"/api/v1/convocatorias/{c.id}/estado", headers=auth(token_otro),
                     json={"estado": "abierta"})
    assert r.status_code == 403

    db.expire_all()
    conv = db.query(Convocatoria).filter(Convocatoria.id == c.id).first()
    assert conv.titulo == "Convocatoria scoping programa"
    assert conv.estado == EstadoConvocatoriaEnum.borrador

    token_jefe = get_token(client, usuario_jefe.codigo)
    r = client.put(f"/api/v1/convocatorias/{c.id}", headers=auth(token_jefe),
                   json={"titulo": "Editada por jefe del programa"})
    assert r.status_code == 200
    assert r.json()["titulo"] == "Editada por jefe del programa"


def test_jefe_otro_programa_no_crea_convocatoria(client: TestClient, usuario_profesor,
                                                 usuario_jefe_otro_programa, asignatura):
    ahora = datetime.now(timezone.utc)
    token = get_token(client, usuario_jefe_otro_programa.codigo)
    r = client.post("/api/v1/convocatorias/", headers=auth(token), json={
        "titulo": "Convocatoria ajena",
        "asignatura_id": asignatura.id,
        "profesor_id": usuario_profesor.id,
        "tipo_monitoria": "academica_cursos",
        "periodo_academico": "2099-7",
        "fecha_inicio_postulacion": (ahora + timedelta(days=1)).isoformat(),
        "fecha_fin_postulacion": (ahora + timedelta(days=10)).isoformat(),
        "num_monitores_requeridos": 1,
        "horas_semana": 8,
        "horas_semestre": 120,
        "promedio_minimo": 3.5,
        "creditos_minimo_pct": 30.0,
    })
    assert r.status_code == 403


def test_jefe_otro_programa_no_gestiona_asignatura_ajena(client: TestClient, usuario_jefe_otro_programa,
                                                         usuario_estudiante, asignatura, db):
    from app.models.convocatoria import Asignatura

    token = get_token(client, usuario_jefe_otro_programa.codigo)
    payload = {
        "codigo": asignatura.codigo,
        "nombre": asignatura.nombre,
        "creditos": asignatura.creditos,
        "programa": usuario_jefe_otro_programa.programa,
        "semestre": asignatura.semestre,
    }
    r = client.patch(f"/api/v1/convocatorias/asignaturas/{asignatura.id}", headers=auth(token), json=payload)
    assert r.status_code == 403
    db.expire_all()
    assert db.query(Asignatura).filter(Asignatura.id == asignatura.id).first().programa == "Ingeniería de Software"

    r = client.post(f"/api/v1/convocatorias/asignaturas/{asignatura.id}/matricular", headers=auth(token),
                    json={"estudiante_id": usuario_estudiante.id, "periodo_academico": "2099-6"})
    assert r.status_code == 403

    r = client.post("/api/v1/convocatorias/asignaturas/", headers=auth(token),
                    json={**payload, "codigo": "IS-AJENA-NEW", "programa": "Ingeniería de Software"})
    assert r.status_code == 403
