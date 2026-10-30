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



# ── PP-001b: No se puede crear práctica sobre asignatura ajena ─────────────────
def test_crear_practica_asignatura_ajena(client: TestClient, usuario_profesor, usuario_admin, db):
    from app.models.convocatoria import Asignatura

    ajenas = []
    for codigo, profesor_id in (("IS-AJENA-1", usuario_admin.id), ("IS-AJENA-2", None)):
        a = Asignatura(
            codigo=codigo,
            nombre=f"Asignatura {codigo}",
            programa="Ingeniería de Software",
            facultad="Ingeniería",
            creditos=3,
            semestre=5,
            profesor_id=profesor_id,
            is_active=True,
            caracter_curso="teorico_practico",
            caracteristica_curso="especifico",
        )
        db.add(a); db.commit(); db.refresh(a)
        ajenas.append(a)

    token = get_token(client, usuario_profesor.codigo)
    for a in ajenas:
        r = client.post("/api/v1/practicas/", headers=auth(token),
                        json=_practica_payload(a.id, "2098-1"))
        assert r.status_code == 403, r.text
        assert "asignaturas que usted dicta" in r.json()["detail"]

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


# ── PP-012: Eliminar práctica (DELETE /practicas/{id}) ───────────────────────
def _nueva_practica_db(db, asignatura, profesor_id, estado, periodo):
    from app.models.practica import Practica
    ahora = datetime.now(timezone.utc)
    p = Practica(
        nombre_practica="Práctica a eliminar",
        asignatura_id=asignatura.id,
        profesor_id=profesor_id,
        estado=estado,
        periodo_academico=periodo,
        fecha_inicio=ahora + timedelta(days=35),
        fecha_fin=ahora + timedelta(days=37),
        duracion_dias=3,
        num_alumnos=10,
    )
    db.add(p); db.commit(); db.refresh(p)
    return p


def test_eliminar_practica_borrador(client: TestClient, usuario_profesor, asignatura, db):
    from app.models.practica import RutaPractica
    token = get_token(client, usuario_profesor.codigo)
    r = client.post("/api/v1/practicas/", headers=auth(token),
                    json=_practica_payload(asignatura.id, "2099-1"))
    assert r.status_code == 201
    pid = r.json()["id"]

    rd = client.delete(f"/api/v1/practicas/{pid}", headers=auth(token))
    assert rd.status_code == 204
    assert client.get(f"/api/v1/practicas/{pid}", headers=auth(token)).status_code == 404
    # las rutas se eliminan por cascade ORM
    assert db.query(RutaPractica).filter(RutaPractica.practica_id == pid).count() == 0


def test_eliminar_practica_roles_denegados(client: TestClient, usuario_profesor, usuario_estudiante,
                                           usuario_jefe, usuario_decano, asignatura, db):
    p = _nueva_practica_db(db, asignatura, usuario_profesor.id,
                           EstadoPracticaEnum.borrador, "2099-2")
    for u in (usuario_estudiante, usuario_jefe, usuario_decano):
        t = get_token(client, u.codigo)
        r = client.delete(f"/api/v1/practicas/{p.id}", headers=auth(t))
        assert r.status_code == 403


def test_eliminar_practica_estados_no_permitidos(client: TestClient, usuario_profesor,
                                                 usuario_admin, asignatura, db):
    # profesor: solo borrador / solicitada / rechazada
    p = _nueva_practica_db(db, asignatura, usuario_profesor.id,
                           EstadoPracticaEnum.aprobada_curriculo, "2099-3")
    tp = get_token(client, usuario_profesor.codigo)
    assert client.delete(f"/api/v1/practicas/{p.id}", headers=auth(tp)).status_code == 400

    # admin: no en ejecución ni finalizada
    ta = get_token(client, usuario_admin.codigo)
    for i, estado in enumerate([EstadoPracticaEnum.en_ejecucion, EstadoPracticaEnum.finalizada]):
        p2 = _nueva_practica_db(db, asignatura, usuario_profesor.id, estado, f"2099-{i + 4}")
        assert client.delete(f"/api/v1/practicas/{p2.id}", headers=auth(ta)).status_code == 400


def test_eliminar_practica_limpia_relacionados(client: TestClient, usuario_profesor,
                                               usuario_admin, asignatura, db):
    from datetime import date
    from app.models.historial_estado import HistorialEstado
    from app.models.pago_viatico import PagoViatico
    from app.models.presupuesto import Presupuesto, MovimientoPresupuestal, TipoMovimientoEnum
    from app.models.practica import TarifaViatico, Viatico

    p = _nueva_practica_db(db, asignatura, usuario_profesor.id,
                           EstadoPracticaEnum.solicitada, "2099-6")
    db.add(HistorialEstado(entidad="practica", entidad_id=p.id,
                           estado_anterior="borrador", estado_nuevo="solicitada",
                           usuario_id=usuario_profesor.id))
    pres = Presupuesto(periodo_academico="2099-6", monto_total_asignado=1000000,
                       monto_comprometido=50000)
    db.add(pres); db.flush()
    db.add(MovimientoPresupuestal(presupuesto_id=pres.id, tipo=TipoMovimientoEnum.comprometido,
                                monto=50000, concepto="Viáticos práctica", practica_id=p.id))
    tarifa = TarifaViatico(descripcion="Urbano test", valor_dia=30000,
                           aplica_desde=date(2025, 1, 1))
    db.add(tarifa); db.flush()
    db.add(Viatico(practica_id=p.id, tarifa_id=tarifa.id, num_dias=2,
                   num_personas=10, valor_calculado=600000))
    db.commit()

    ta = get_token(client, usuario_admin.codigo)
    assert client.delete(f"/api/v1/practicas/{p.id}", headers=auth(ta)).status_code == 204

    assert db.query(HistorialEstado).filter(
        HistorialEstado.entidad == "practica", HistorialEstado.entidad_id == p.id).count() == 0
    assert db.query(MovimientoPresupuestal).filter(MovimientoPresupuestal.practica_id == p.id).count() == 0
    assert db.query(Viatico).filter(Viatico.practica_id == p.id).count() == 0
    # el compromiso de la práctica eliminada se revirtió en el presupuesto
    db.refresh(pres)
    assert float(pres.monto_comprometido) == 0.0


def test_eliminar_practica_con_pagos_bloqueada(client: TestClient, usuario_profesor,
                                               usuario_admin, asignatura, db):
    from app.models.pago_viatico import PagoViatico
    from app.models.practica import Practica

    p = _nueva_practica_db(db, asignatura, usuario_profesor.id,
                           EstadoPracticaEnum.aprobado_transporte, "2099-7")
    db.add(PagoViatico(practica_id=p.id, registrado_por_id=usuario_admin.id,
                       monto_pagado=100000, fecha_pago=datetime.now(timezone.utc)))
    db.commit()

    ta = get_token(client, usuario_admin.codigo)
    assert client.delete(f"/api/v1/practicas/{p.id}", headers=auth(ta)).status_code == 400
    assert db.query(Practica).filter(Practica.id == p.id).count() == 1
    assert db.query(PagoViatico).filter(PagoViatico.practica_id == p.id).count() == 1


def _practica_con_viaticos(db, asignatura, profesor_id, periodo, valor):
    from datetime import date
    from app.models.practica import TarifaViatico, Viatico

    p = _nueva_practica_db(db, asignatura, profesor_id,
                           EstadoPracticaEnum.aprobada_facultad, periodo)
    tarifa = TarifaViatico(descripcion=f"Tarifa {periodo}", valor_dia=30000,
                           aplica_desde=date(2025, 1, 1))
    db.add(tarifa); db.flush()
    db.add(Viatico(practica_id=p.id, tarifa_id=tarifa.id, num_dias=2,
                   num_personas=10, valor_calculado=valor))
    db.commit()
    return p


def test_admin_aprueba_compromete_presupuesto(client: TestClient, usuario_profesor,
                                              usuario_admin, asignatura, db):
    from app.models.presupuesto import Presupuesto, MovimientoPresupuestal, TipoMovimientoEnum

    pres = Presupuesto(periodo_academico="2098-1", monto_total_asignado=1000000,
                       monto_comprometido=300000, monto_ejecutado=100000)
    db.add(pres); db.commit()
    # 300.000 + 100.000 + 600.000 = 1.000.000: justo en el tope, se permite
    p = _practica_con_viaticos(db, asignatura, usuario_profesor.id, "2098-1", 600000)

    ta = get_token(client, usuario_admin.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/aprobar", headers=auth(ta))
    assert r.status_code == 200
    assert r.json()["estado"] == "aprobado_transporte"

    db.refresh(pres)
    assert float(pres.monto_comprometido) == 900000.0
    mov = db.query(MovimientoPresupuestal).filter(MovimientoPresupuestal.practica_id == p.id).one()
    assert mov.tipo == TipoMovimientoEnum.comprometido
    assert float(mov.monto) == 600000.0


def test_admin_aprueba_rechaza_si_excede_presupuesto(client: TestClient, usuario_profesor,
                                                     usuario_admin, asignatura, db):
    from app.models.presupuesto import Presupuesto, MovimientoPresupuestal
    from app.models.practica import Practica

    pres = Presupuesto(periodo_academico="2098-2", monto_total_asignado=1000000,
                       monto_comprometido=500000)
    db.add(pres); db.commit()
    p = _practica_con_viaticos(db, asignatura, usuario_profesor.id, "2098-2", 600000)

    ta = get_token(client, usuario_admin.codigo)
    r = client.patch(f"/api/v1/practicas/{p.id}/aprobar", headers=auth(ta))
    assert r.status_code == 400
    assert "Presupuesto insuficiente" in r.json()["detail"]

    db.expire_all()
    assert float(db.get(Presupuesto, pres.id).monto_comprometido) == 500000.0
    assert db.get(Practica, p.id).estado == EstadoPracticaEnum.aprobada_facultad
    assert db.query(MovimientoPresupuestal).filter(MovimientoPresupuestal.practica_id == p.id).count() == 0
