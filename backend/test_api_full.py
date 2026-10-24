"""Prueba E2E completa de todos los modulos SIPAM-USCO."""
import httpx

BASE = "http://localhost:8000/api/v1"
OK = "\033[92m OK\033[0m"
FAIL = "\033[91mFAIL\033[0m"


def check(label: str, r: httpx.Response, expected: int = 200):
    icon = OK if r.status_code == expected else FAIL
    print(f"  [{icon}] {label} => {r.status_code}")
    if r.status_code not in (expected, 200, 201):
        print(f"       Body: {r.text[:200]}")
    return r


def run():
    print("=" * 65)
    print("  SIPAM-USCO -- Verificacion E2E completa")
    print("=" * 65)

    # ── Auth ────────────────────────────────────────────────────────
    print("\n[AUTH]")
    r = check("Health", httpx.get(f"{BASE}/health"))
    r = check("Login JEFE001", httpx.post(f"{BASE}/auth/login",
              json={"codigo": "JEFE001", "password": "sipam2025"}))
    jefe_token = r.json()["access_token"]
    jefe_h = {"Authorization": f"Bearer {jefe_token}"}

    r = check("Login PROF001", httpx.post(f"{BASE}/auth/login",
              json={"codigo": "PROF001", "password": "sipam2025"}))
    prof_token = r.json()["access_token"]
    prof_h = {"Authorization": f"Bearer {prof_token}"}

    r = check("Login GASTOS001", httpx.post(f"{BASE}/auth/login",
              json={"codigo": "GASTOS001", "password": "sipam2025"}))
    gastos_h = {"Authorization": f"Bearer {r.json()['access_token']}"}

    check("GET /auth/me (jefe)", httpx.get(f"{BASE}/auth/me", headers=jefe_h))
    check("Validacion academica (PROF001)", httpx.get(
        f"{BASE}/auth/validar-academica/PROF001", headers=jefe_h))
    check("Login contrasena incorrecta", httpx.post(
        f"{BASE}/auth/login", json={"codigo": "JEFE001", "password": "wrong"}), 401)
    check("Sin token => 401", httpx.get(f"{BASE}/convocatorias/"), 401)

    # ── Convocatorias ───────────────────────────────────────────────
    print("\n[CONVOCATORIAS]")
    r = check("Listar (jefe)", httpx.get(f"{BASE}/convocatorias/", headers=jefe_h))
    convs = r.json()
    print(f"         {len(convs)} convocatoria(s) encontradas")
    for c in convs:
        print(f"         [{c['estado']:15}] {c['titulo'][:45]} | {c['total_postulantes']} posts.")

    check("Listar (profesor)", httpx.get(f"{BASE}/convocatorias/", headers=prof_h))
    check("Obtener convocatoria #1", httpx.get(f"{BASE}/convocatorias/1", headers=jefe_h))

    r = check("Crear convocatoria (jefe)", httpx.post(f"{BASE}/convocatorias/", headers=jefe_h,
              json={
                  "titulo": "Monitoría TEST Automatizado",
                  "asignatura_id": 1,
                  "periodo_academico": "2025-1",
                  "fecha_inicio_postulacion": "2025-03-01T00:00:00",
                  "fecha_fin_postulacion": "2025-04-01T00:00:00",
                  "num_monitores_requeridos": 1,
                  "horas_semana": 4,
                  "horas_semestre": 64,
              }), 201)
    conv_test_id = r.json()["id"]

    check("Cambiar estado borrador->abierta", httpx.patch(
        f"{BASE}/convocatorias/{conv_test_id}/estado",
        headers=jefe_h, json={"estado": "abierta"}))
    check("Transicion invalida (abierta->finalizada) => 400", httpx.patch(
        f"{BASE}/convocatorias/{conv_test_id}/estado",
        headers=jefe_h, json={"estado": "finalizada"}), 400)

    # ── Seleccion ───────────────────────────────────────────────────
    print("\n[SELECCION RF-MON-05]")
    check("Resultados convocatoria #3", httpx.get(
        f"{BASE}/seleccion/convocatorias/3/resultados", headers=jefe_h))
    check("Ejecutar seleccion conv #1 (necesita estado cerrado) => 400", httpx.post(
        f"{BASE}/seleccion/convocatorias/1/ejecutar-seleccion", headers=prof_h), 400)

    # ── Presupuesto ─────────────────────────────────────────────────
    print("\n[PRESUPUESTO RF-PRA-06]")
    r = check("GET /presupuesto/actual", httpx.get(f"{BASE}/presupuesto/actual", headers=jefe_h))
    if r.status_code == 200:
        p = r.json()
        print(f"         Asignado: ${p['monto_total_asignado']:,.0f} | "
              f"Ejecutado: ${p['monto_ejecutado']:,.0f} | "
              f"Disponible: ${p['monto_disponible']:,.0f} | "
              f"{p['porcentaje_ejecutado']}%")
    check("GET /presupuesto/actual (gastos)", httpx.get(
        f"{BASE}/presupuesto/actual", headers=gastos_h))
    check("GET /presupuesto/movimientos/2025-1", httpx.get(
        f"{BASE}/presupuesto/movimientos/2025-1", headers=jefe_h))
    check("Presupuesto sin permiso (profesor) => 403", httpx.get(
        f"{BASE}/presupuesto/actual", headers=prof_h), 403)

    # ── Practicas ───────────────────────────────────────────────────
    print("\n[PRACTICAS RF-PRA]")
    r = check("Listar practicas (jefe)", httpx.get(f"{BASE}/practicas/", headers=jefe_h))
    print(f"         {len(r.json())} practica(s)")
    check("Tarifas viaticos vigentes", httpx.get(
        f"{BASE}/practicas/tarifas/vigentes", headers=jefe_h))

    r2 = check("Crear practica (profesor)", httpx.post(f"{BASE}/practicas/", headers=prof_h,
               json={
                   "nombre_practica": "Practica Test RF-PRA-01",
                   "asignatura_id": 1,
                   "periodo_academico": "2026-1",
                   "fecha_inicio": "2025-04-01T08:00:00",
                   "fecha_fin": "2025-04-03T18:00:00",
                   "num_alumnos": 20,
                   "observaciones": "Prueba automatizada",
                   "rutas": [
                       {"orden": 1, "tipo_punto": "origen", "lugar": "USCO Neiva", "municipio": "Neiva", "departamento": "Huila"},
                       {"orden": 2, "tipo_punto": "destino", "lugar": "Reserva Natural", "municipio": "Pitalito", "departamento": "Huila", "distancia_km": 235.5},
                   ]
               }), 201)

    if r2.status_code == 201:
        pid = r2.json()["id"]
        check("Calcular viaticos", httpx.get(
            f"{BASE}/practicas/{pid}/viaticos", headers=jefe_h))
        check("Solicitar practica", httpx.patch(
            f"{BASE}/practicas/{pid}/solicitar", headers=prof_h))
        check("Aprobar practica (jefe)", httpx.patch(
            f"{BASE}/practicas/{pid}/aprobar", headers=jefe_h))

    check("Crear practica estudiante => 403", httpx.post(
        f"{BASE}/practicas/", headers=gastos_h,
        json={"nombre_practica": "x", "asignatura_id": 1, "periodo_academico": "2025-1",
              "fecha_inicio": "2025-04-01T08:00:00", "fecha_fin": "2025-04-03T18:00:00",
              "num_alumnos": 5}), 403)

    # ── Limpieza ────────────────────────────────────────────────────
    print("\n[LIMPIEZA]")
    import app.models.user, app.models.convocatoria, app.models.postulacion, app.models.practica, app.models.presupuesto
    from app.db.database import SessionLocal
    from app.models.convocatoria import Convocatoria as _C
    from app.models.practica import Practica as _P, RutaPractica as _R, Viatico as _V
    db = SessionLocal()
    test_pracs = db.query(_P).filter(_P.nombre_practica.like("%Test RF-PRA%")).all()
    for p in test_pracs:
        db.query(_V).filter(_V.practica_id == p.id).delete()
        db.query(_R).filter(_R.practica_id == p.id).delete()
        db.delete(p)
    test_convs = db.query(_C).filter(_C.titulo == "Monitoría TEST Automatizado").all()
    for c in test_convs: db.delete(c)
    db.commit()
    db.close()
    print(f"  [ OK] {len(test_pracs)} practica(s) y {len(test_convs)} convocatoria(s) de prueba eliminadas")

    print("\n" + "=" * 65)
    print("  VERIFICACION COMPLETADA")
    print("=" * 65)


if __name__ == "__main__":
    run()
