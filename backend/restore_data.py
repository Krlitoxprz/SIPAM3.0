"""
SIPAM-USCO — Restaurador de datos (sin tocar la tabla users).
Reconstruye asignaturas, matrículas, convocatorias, presupuesto y calendario
usando los profesores/estudiantes ya existentes en la BD.

Ejecutar con el servidor en ejecución o detenido:
    venv/Scripts/python restore_data.py
"""
import sys, os, random
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, init_db
from app.models.user import User, RolEnum
from app.models.convocatoria import (
    Convocatoria, Asignatura, AsignaturaEstudiante,
    EstadoConvocatoriaEnum, TipoMonitoriaEnum,
)
from app.models.postulacion import Postulacion, EstadoPostulacionEnum
from app.models.practica import TarifaViatico
from app.models.presupuesto import Presupuesto, ConfiguracionCalendario

random.seed(42)
PERIODO = "2026-1"

# ── Definición de asignaturas ────────────────────────────────────────────────
ASIGNATURAS_DATA = [
    ("ISW-101", "Fundamentos de Programación",      3, 1, "Ingeniería"),   # 0
    ("ISW-201", "Programación Orientada a Objetos", 4, 2, "Ingeniería"),   # 1
    ("ISW-202", "Estructuras de Datos",             4, 2, "Ingeniería"),   # 2
    ("MAT-101", "Cálculo Diferencial e Integral",   4, 1, "Ciencias"),     # 3
    ("MAT-201", "Álgebra Lineal",                   3, 2, "Ciencias"),     # 4
    ("ISW-301", "Bases de Datos I",                 4, 3, "Ingeniería"),   # 5
    ("ISW-302", "Ingeniería de Software I",         4, 3, "Ingeniería"),   # 6
    ("ISW-401", "Redes de Computadores",            3, 4, "Ingeniería"),   # 7
    ("ISW-402", "Sistemas Operativos",              4, 4, "Ingeniería"),   # 8
    ("ISW-501", "Desarrollo Web",                   3, 5, "Ingeniería"),   # 9
    ("ISW-502", "Seguridad Informática",            3, 5, "Ingeniería"),   # 10
    ("ISW-601", "Inteligencia Artificial",          4, 6, "Ingeniería"),   # 11
    ("ISW-602", "Computación en la Nube",           3, 6, "Ingeniería"),   # 12
    ("ISW-701", "Gestión de Proyectos TI",          3, 7, "Ingeniería"),   # 13
    ("MAT-301", "Estadística y Probabilidad",       3, 3, "Ciencias"),     # 14
    ("MAT-401", "Métodos Numéricos",                3, 4, "Ciencias"),     # 15
    ("ISW-303", "Algoritmos y Complejidad",         4, 3, "Ingeniería"),   # 16
    ("ISW-403", "Arquitectura de Software",         4, 4, "Ingeniería"),   # 17
    ("ISW-503", "Trabajo de Grado I",               3, 5, "Ingeniería"),   # 18
    ("ISW-603", "Trabajo de Grado II",              3, 6, "Ingeniería"),   # 19
]

PROF_ASIGNATURAS = {
    0: [0, 3],    # PROF001: ISW-101, MAT-101
    1: [1, 2],    # PROF002: ISW-201, ISW-202
    2: [4, 5],    # PROF003: MAT-201, ISW-301
    3: [6, 7],    # PROF004: ISW-302, ISW-401
    4: [8, 9],    # PROF005: ISW-402, ISW-501
    5: [10, 11],  # PROF006: ISW-502, ISW-601
    6: [12, 13],  # PROF007: ISW-602, ISW-701
    7: [14, 15],  # PROF008: MAT-301, MAT-401
    8: [16, 17],  # PROF009: ISW-303, ISW-403
    9: [18, 19],  # PROF010: ISW-503, ISW-603
}

# Matrícula por año de ingreso (cubre TODAS las 20 materias)
MATRICULAS_POR_ANIO = {
    2016: [17, 18, 19],
    2017: [13, 16, 17],
    2018: [10, 11, 12, 13],
    2019: [7, 8, 9, 10],
    2020: [5, 6, 7, 14],
    2021: [3, 4, 5, 15],
    2022: [1, 2, 4, 14],
    2023: [0, 1, 3, 15],
    2024: [0, 2, 3, 14],
}

PROFESORES_CODIGOS = [f"PROF{i+1:03d}" for i in range(10)]


def run():
    init_db()
    db = SessionLocal()
    try:
        # ── Verificar usuarios ────────────────────────────────────────────────
        total_users = db.query(User).count()
        profs = db.query(User).filter(User.rol == RolEnum.profesor).order_by(User.codigo).all()
        estudiantes = db.query(User).filter(User.rol == RolEnum.estudiante).all()
        print(f"\n  Usuarios encontrados: {total_users} total, {len(profs)} profesores, {len(estudiantes)} estudiantes")

        if len(profs) < 10:
            print(f"  ✗ Se esperaban 10 profesores, hay {len(profs)}. Verifica la BD.")
            return

        # ── Asignaturas ───────────────────────────────────────────────────────
        existing = db.query(Asignatura.codigo).all()
        existing_codigos = {r[0] for r in existing}
        asignaturas_db = []

        print("\n  Creando asignaturas...")
        for i, (cod, nom, cred, sem, fac) in enumerate(ASIGNATURAS_DATA):
            # Buscar asignatura existente o crearla
            asig = db.query(Asignatura).filter(Asignatura.codigo == cod).first()
            if asig:
                asignaturas_db.append(asig)
                print(f"    {cod:10} ya existe (id={asig.id})")
                continue

            # Determinar qué profesor dicta esta materia
            prof_idx = next(pi for pi, idxs in PROF_ASIGNATURAS.items() if i in idxs)
            prof_db = profs[prof_idx] if prof_idx < len(profs) else profs[0]

            asig = Asignatura(
                codigo=cod, nombre=nom, creditos=cred, semestre=sem,
                facultad=fac, programa="Ingeniería de Software",
                profesor_id=prof_db.id, is_active=True,
            )
            db.add(asig)
            asignaturas_db.append(asig)
            print(f"    {cod:10} creada → prof: {prof_db.codigo}")

        db.flush()
        print(f"\n  ✓ {len(asignaturas_db)} asignaturas disponibles.")

        # ── Matrículas (AsignaturaEstudiante) ─────────────────────────────────
        print("\n  Matriculando estudiantes según año de ingreso...")
        matriculas_count = 0
        skip_count = 0

        for est in estudiantes:
            try:
                anio = int(est.codigo[:4])
            except (ValueError, IndexError):
                continue
            asig_idxs = MATRICULAS_POR_ANIO.get(anio, [0, 1])

            for ai in asig_idxs:
                if ai >= len(asignaturas_db):
                    continue
                asig = asignaturas_db[ai]
                if asig.id is None:
                    continue
                # Evitar duplicados
                exists = db.query(AsignaturaEstudiante).filter_by(
                    asignatura_id=asig.id,
                    estudiante_id=est.id,
                    periodo_academico=PERIODO,
                ).first()
                if exists:
                    skip_count += 1
                    continue
                db.add(AsignaturaEstudiante(
                    asignatura_id=asig.id,
                    estudiante_id=est.id,
                    periodo_academico=PERIODO,
                ))
                matriculas_count += 1

        db.flush()
        print(f"  ✓ {matriculas_count} matrículas nuevas creadas ({skip_count} ya existían).")

        # ── Convocatorias ─────────────────────────────────────────────────────
        if db.query(Convocatoria).count() == 0:
            print("\n  Creando 8 convocatorias de monitoría...")
            fecha_base = datetime(2026, 2, 9)
            convs_cfg = [
                {"asig_idx": 3, "tipo": TipoMonitoriaEnum.academica_cursos,  "estado": EstadoConvocatoriaEnum.abierta,       "num": 2, "h_sem": 6},
                {"asig_idx": 0, "tipo": TipoMonitoriaEnum.nee,               "estado": EstadoConvocatoriaEnum.abierta,       "num": 1, "h_sem": 4},
                {"asig_idx": 4, "tipo": TipoMonitoriaEnum.academica_cursos,  "estado": EstadoConvocatoriaEnum.en_evaluacion, "num": 2, "h_sem": 5},
                {"asig_idx": 5, "tipo": TipoMonitoriaEnum.laboratorios,      "estado": EstadoConvocatoriaEnum.en_evaluacion, "num": 1, "h_sem": 6},
                {"asig_idx": 7, "tipo": TipoMonitoriaEnum.tic,               "estado": EstadoConvocatoriaEnum.cerrada,       "num": 1, "h_sem": 4},
                {"asig_idx": 1, "tipo": TipoMonitoriaEnum.academica_cursos,  "estado": EstadoConvocatoriaEnum.finalizada,    "num": 2, "h_sem": 6},
                {"asig_idx": 8, "tipo": TipoMonitoriaEnum.laboratorios,      "estado": EstadoConvocatoriaEnum.borrador,      "num": 1, "h_sem": 5},
                {"asig_idx": 16,"tipo": TipoMonitoriaEnum.academica_cursos,  "estado": EstadoConvocatoriaEnum.borrador,      "num": 1, "h_sem": 4},
            ]
            for cfg in convs_cfg:
                asig = asignaturas_db[cfg["asig_idx"]]
                prof_idx = next(pi for pi, idxs in PROF_ASIGNATURAS.items() if cfg["asig_idx"] in idxs)
                prof = profs[prof_idx]
                conv = Convocatoria(
                    titulo=f"Monitoría {asig.nombre} — {PERIODO}",
                    descripcion=f"Convocatoria de monitoría para {asig.nombre}.",
                    asignatura_id=asig.id,
                    profesor_id=prof.id,
                    tipo_monitoria=cfg["tipo"],
                    estado=cfg["estado"],
                    periodo_academico=PERIODO,
                    fecha_inicio_postulacion=fecha_base,
                    fecha_fin_postulacion=fecha_base + __import__('datetime').timedelta(days=14),
                    num_monitores_requeridos=cfg["num"],
                    horas_semana=cfg["h_sem"],
                    horas_semestre=cfg["h_sem"] * 16,
                    promedio_minimo=3.5, creditos_minimo_pct=30.0,
                )
                db.add(conv)
            db.flush()
            print(f"  ✓ 8 convocatorias creadas.")
        else:
            print(f"  ✓ Convocatorias ya existen ({db.query(Convocatoria).count()}).")

        # ── Presupuesto ───────────────────────────────────────────────────────
        if db.query(Presupuesto).count() == 0:
            print("\n  Creando presupuesto y calendarios...")
            db.add(Presupuesto(
                periodo_academico="2025-1",
                monto_total_asignado=40_000_000.0, monto_ejecutado=32_700_000.0,
                monto_comprometido=0.0,
                descripcion="Presupuesto histórico 2025-1 (cerrado).",
            ))
            db.add(Presupuesto(
                periodo_academico=PERIODO,
                monto_total_asignado=48_000_000.0, monto_ejecutado=3_200_000.0,
                monto_comprometido=1_500_000.0,
                descripcion="Presupuesto asignado para monitorías y prácticas 2026-1.",
            ))
            db.add(ConfiguracionCalendario(
                periodo_academico="2025-1",
                semana_inicio_solicitudes=3, semana_fin_solicitudes=14,
                fecha_inicio_semestre=datetime(2025, 1, 27),
                fecha_fin_semestre=datetime(2025, 6, 13, 23, 59),
                is_active=False,
            ))
            db.add(ConfiguracionCalendario(
                periodo_academico=PERIODO,
                semana_inicio_solicitudes=3, semana_fin_solicitudes=14,
                fecha_inicio_semestre=datetime(2026, 1, 26),
                fecha_fin_semestre=datetime(2026, 6, 12, 23, 59),
                is_active=True,
            ))
            db.flush()
            print("  ✓ Presupuesto y calendario creados.")
        else:
            print(f"  ✓ Presupuesto ya existe ({db.query(Presupuesto).count()} registros).")

        # ── Tarifas de viáticos ───────────────────────────────────────────────
        if db.query(TarifaViatico).count() == 0:
            print("\n  Creando tarifas de viáticos...")
            from datetime import date
            for desc, val in [
                ("Desayuno 2026 (Decreto USCO)",    16_026),
                ("Almuerzo 2026 (Decreto USCO)",    27_471),
                ("Cena 2026 (Decreto USCO)",        16_026),
                ("Alojamiento 2026 (Decreto USCO)", 107_742),
            ]:
                db.add(TarifaViatico(
                    descripcion=desc, valor_dia=float(val),
                    aplica_desde=date(2026, 1, 1), is_active=True,
                ))
            db.flush()
            print("  ✓ 4 tarifas creadas.")

        db.commit()

        # ── Resumen final ─────────────────────────────────────────────────────
        print("\n" + "=" * 65)
        print("  RESTAURACIÓN COMPLETADA — Cobertura por materia:")
        print("=" * 65)
        for asig in db.query(Asignatura).order_by(Asignatura.semestre, Asignatura.codigo).all():
            n = db.query(AsignaturaEstudiante).filter(
                AsignaturaEstudiante.asignatura_id == asig.id,
                AsignaturaEstudiante.periodo_academico == PERIODO,
            ).count()
            bar = "█" * (n // 5)
            status = "✓" if n >= 5 else "⚠"
            print(f"  {status} {asig.codigo:10} sem={asig.semestre} {asig.nombre[:32]:32} {n:3} est. {bar}")

    except Exception as e:
        db.rollback()
        import traceback; traceback.print_exc()
        print(f"\n  ✗ ERROR: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
