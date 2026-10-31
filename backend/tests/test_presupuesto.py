"""Pruebas de eliminación de presupuestos (DELETE /presupuesto/{periodo})."""
import os

from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.documento_presupuesto import DocumentoPresupuesto
from app.models.presupuesto import (
    EstadoPresupuestoEnum,
    MovimientoPresupuestal,
    Presupuesto,
    TipoMovimientoEnum,
)
from tests.conftest import auth, get_token


def _presupuesto(db, periodo, estado, **kw):
    p = Presupuesto(periodo_academico=periodo, monto_total_asignado=1000000, estado=estado, **kw)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def test_eliminar_presupuesto_aprobado_bloqueado(client: TestClient, usuario_admin, db):
    _presupuesto(db, "2098-1", EstadoPresupuestoEnum.aprobado)
    ta = get_token(client, usuario_admin.codigo)
    r = client.delete("/api/v1/presupuesto/2098-1", headers=auth(ta))
    assert r.status_code == 409
    assert db.query(Presupuesto).filter(Presupuesto.periodo_academico == "2098-1").count() == 1


def test_eliminar_presupuesto_con_compromisos_bloqueado(client: TestClient, usuario_admin, db):
    # Un estado forzado a "rechazado" no permite saltarse la protección de montos comprometidos.
    p = _presupuesto(db, "2098-2", EstadoPresupuestoEnum.rechazado, monto_comprometido=50000)
    db.add(MovimientoPresupuestal(presupuesto_id=p.id, tipo=TipoMovimientoEnum.comprometido,
                                  monto=50000, concepto="Viáticos práctica"))
    db.commit()
    ta = get_token(client, usuario_admin.codigo)
    assert client.delete("/api/v1/presupuesto/2098-2", headers=auth(ta)).status_code == 409

    p.monto_comprometido = 0
    db.commit()
    assert client.delete("/api/v1/presupuesto/2098-2", headers=auth(ta)).status_code == 409
    assert db.query(MovimientoPresupuestal).filter(MovimientoPresupuestal.presupuesto_id == p.id).count() == 1


def test_eliminar_presupuesto_con_ejecutado_bloqueado(client: TestClient, usuario_admin, db):
    _presupuesto(db, "2098-3", EstadoPresupuestoEnum.modificacion, monto_ejecutado=10000)
    ta = get_token(client, usuario_admin.codigo)
    assert client.delete("/api/v1/presupuesto/2098-3", headers=auth(ta)).status_code == 409


def test_eliminar_presupuesto_borra_documentos_y_archivos(client: TestClient, usuario_admin,
                                                         usuario_jefe, db, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path))
    p = _presupuesto(db, "2098-4", EstadoPresupuestoEnum.rechazado)
    db.add(MovimientoPresupuestal(presupuesto_id=p.id, tipo=TipoMovimientoEnum.asignacion,
                                  monto=1000000, concepto="Asignación inicial"))
    ruta = os.path.join("presupuesto", "2098-4", "soporte.pdf")
    os.makedirs(tmp_path / "presupuesto" / "2098-4")
    (tmp_path / ruta).write_bytes(b"%PDF-1.4 test")
    db.add(DocumentoPresupuesto(presupuesto_id=p.id, subido_por_id=usuario_jefe.id,
                                tipo_solicitud="solicitud", nombre_original="soporte.pdf",
                                nombre_almacenado="soporte.pdf", ruta=ruta))
    db.commit()
    pid = p.id

    ta = get_token(client, usuario_admin.codigo)
    assert client.delete("/api/v1/presupuesto/2098-4", headers=auth(ta)).status_code == 204

    db.expire_all()
    assert db.query(Presupuesto).filter(Presupuesto.id == pid).count() == 0
    assert db.query(MovimientoPresupuestal).filter(MovimientoPresupuestal.presupuesto_id == pid).count() == 0
    assert db.query(DocumentoPresupuesto).filter(DocumentoPresupuesto.presupuesto_id == pid).count() == 0
    assert not (tmp_path / ruta).exists()


def test_eliminar_presupuesto_solo_admin(client: TestClient, usuario_jefe, db):
    _presupuesto(db, "2098-5", EstadoPresupuestoEnum.borrador)
    tj = get_token(client, usuario_jefe.codigo)
    assert client.delete("/api/v1/presupuesto/2098-5", headers=auth(tj)).status_code == 403
