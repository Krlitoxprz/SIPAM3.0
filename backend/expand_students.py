"""
SIPAM-USCO — Expansión de estudiantes: 30 por cohorte (2017-2026).
Actualiza también las cédulas del staff (profesores + admin).

Ejecutar con el servidor EN EJECUCIÓN o detenido:
    venv/Scripts/python expand_students.py
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, init_db
from app.models.user import User, RolEnum
from app.models.convocatoria import Asignatura, AsignaturaEstudiante
from app.core.security import get_password_hash

random.seed(2026)
PERIODO  = "2026-1"
_PERIODO_NUM = PERIODO.split("-")[1]  # "1" o "2"
PW       = get_password_hash("sipam2025")
TARGET   = 30  # estudiantes por cohorte

# ── Cédulas realistas (Huila/Neiva, Colombia) para staff ─────────────────────
# Mujeres:  363xxxxx  (Neiva)  /  Hombres: 77xxxxx (Pitalito/sur) o 127xxxxx (Neiva)
CEDULAS_STAFF = {
    "JEFE001":   "36313456",   # Martha Cecilia Perdomo Dussán
    "GASTOS001": "12791234",   # Hernán Darío Mosquera Ávila
    "PROF001":   "7754321",    # Carlos Alberto Ramírez Gutiérrez
    "PROF002":   "36279012",   # María Elena Torres Medina
    "PROF003":   "12789034",   # Juan Pablo Vargas Lozano
    "PROF004":   "36291045",   # Sandra Milena Ortiz Perdomo
    "PROF005":   "12783056",   # Andrés Felipe Castro Trujillo
    "PROF006":   "36312067",   # Patricia Monsalve Castro
    "PROF007":   "7759078",    # Roberto Niño Pastrana
    "PROF008":   "36298089",   # Claudia Peña Orozco
    "PROF009":   "12795091",   # Germán Quiñones Salcedo
    "PROF010":   "36321012",   # Liliana Soto Vergara
}

# ── Materias por cohorte (semestre actual en 2026-1) ─────────────────────────
#
#  Año ingreso → semestre actual → materias que cursa en 2026-1
#  ──────────────────────────────────────────────────────────────────────────
#  2026  →  sem 1  →  ISW-101, MAT-101
#  2025  →  sem 2  →  ISW-201, ISW-202, MAT-201
#  2024  →  sem 3  →  ISW-301, ISW-302, ISW-303, MAT-301
#  2023  →  sem 4  →  ISW-401, ISW-402, ISW-403, MAT-401
#  2022  →  sem 5  →  ISW-501, ISW-502, ISW-503
#  2021  →  sem 6  →  ISW-601, ISW-602, ISW-603
#  2020  →  sem 7  →  ISW-701
#  2019  →  sem 8  →  (avanzados — sin materias en catálogo)
#  2018  →  sem 9  →  (tesis / pasantía)
#  2017  →  sem 10 →  (graduandos)
#
COHORT_SUBJECTS: dict[int, list[str]] = {
    2026: ["ISW-101", "MAT-101"],
    2025: ["ISW-201", "ISW-202", "MAT-201"],
    2024: ["ISW-301", "ISW-302", "ISW-303", "MAT-301"],
    2023: ["ISW-401", "ISW-402", "ISW-403", "MAT-401"],
    2022: ["ISW-501", "ISW-502", "ISW-503"],
    2021: ["ISW-601", "ISW-602", "ISW-603"],
    2020: ["ISW-701"],
    2019: [],
    2018: [],
    2017: [],
}

SEM_LABEL = {
    2026: "sem 1", 2025: "sem 2", 2024: "sem 3", 2023: "sem 4",
    2022: "sem 5", 2021: "sem 6", 2020: "sem 7",
    2019: "sem 8", 2018: "sem 9", 2017: "sem 10",
}

# ── Nombres y apellidos colombianos ──────────────────────────────────────────
_NOMS_M = [
    "Andrés","Carlos","Daniel","David","Diego","Eduardo","Felipe","Gabriel",
    "Germán","Ivan","Jorge","Julián","Kevin","Luis","Mario","Miguel",
    "Nicolás","Oscar","Pablo","Rafael","Ricardo","Roberto","Sebastián","Tomás",
]
_NOMS_F = [
    "Alejandra","Andrea","Ángela","Camila","Carolina","Claudia","Diana",
    "Isabella","Juliana","Karen","Laura","Lorena","María","Natalia",
    "Paola","Patricia","Sandra","Sara","Sofía","Valentina","Vanessa","Yessica",
]
_APES = [
    "Agudelo","Bermúdez","Cárdenas","Castillo","Castro","Córdoba","Cruz",
    "Gómez","González","Hernández","Jiménez","López","Martínez","Medina",
    "Molina","Montoya","Mora","Morales","Muñoz","Niño","Ortiz","Ospina",
    "Perdomo","Pérez","Pineda","Pulido","Ramírez","Rivera","Roa","Ruiz",
    "Sánchez","Torres","Trujillo","Valencia","Vargas","Vega",
]

# Prefijos de cédula por cohorte (rangos realistas por edad/región Huila)
_CEDULA_PREFIX = {
    2026: 1090, 2025: 1089, 2024: 1088, 2023: 1087,
    2022: 1086, 2021: 1085, 2020: 1084, 2019: 1083,
    2018: 1082, 2017: 1081,
}


def _cedula(anio: int, num: int) -> str:
    prefix = _CEDULA_PREFIX.get(anio, 1080)
    return f"{prefix}{num:06d}"


def _slug(s: str) -> str:
    return s.lower().translate(str.maketrans("áéíóúñÁÉÍÓÚÑ", "aeiounaeioun"))


def run():
    init_db()
    db = SessionLocal()
    try:
        # ── 1. Actualizar cédulas del staff ───────────────────────────────────
        print("\n  Actualizando cédulas del staff...")
        updated = 0
        for codigo, nueva_cedula in CEDULAS_STAFF.items():
            u = db.query(User).filter(User.codigo == codigo).first()
            if u:
                conflicto = db.query(User).filter(
                    User.cedula == nueva_cedula,
                    User.id != u.id,
                ).first()
                if conflicto:
                    print(f"    ⚠  {codigo}: cédula {nueva_cedula} ya usada por {conflicto.codigo}")
                    continue
                if u.cedula != nueva_cedula:
                    u.cedula = nueva_cedula
                    updated += 1
                    print(f"    ✓  {codigo:12} cédula → {nueva_cedula}")
        db.flush()
        print(f"  ✓  {updated} cédula(s) de staff actualizadas.")

        # ── 2. Cargar asignaturas activas ─────────────────────────────────────
        asig_map: dict[str, Asignatura] = {
            a.codigo: a
            for a in db.query(Asignatura).filter(Asignatura.is_active == True).all()
        }
        print(f"\n  {len(asig_map)} asignaturas activas cargadas.")

        # Precargar cédulas y emails existentes para evitar duplicados
        used_cedulas: set[str] = {
            row[0] for row in db.query(User.cedula).filter(User.cedula != None).all()
        }
        used_emails: set[str] = {
            row[0] for row in db.query(User.email).filter(User.email != None).all()
        }

        # ── 3. Agregar estudiantes por cohorte ────────────────────────────────
        total_nuevos = 0
        print("\n  Procesando cohortes (objetivo: 30 estudiantes c/u):\n")

        for anio in sorted(COHORT_SUBJECTS.keys(), reverse=True):
            actuales = db.query(User).filter(
                User.rol == RolEnum.estudiante,
                User.codigo.like(f"{anio}%"),
            ).count()

            faltan = max(0, TARGET - actuales)
            label  = SEM_LABEL.get(anio, "?")
            mats   = COHORT_SUBJECTS[anio]

            print(f"    {anio}  ({label:5})  {actuales:3} existentes  →  +{faltan} nuevos", end="")

            if faltan == 0:
                print("  ✓")
                continue
            print()

            for j in range(faltan):
                idx = total_nuevos + j
                # Alternar sexo: 2 hombres, 1 mujer
                nombres_pool = _NOMS_F if idx % 3 == 0 else _NOMS_M
                nom  = nombres_pool[idx % len(nombres_pool)]
                ape1 = _APES[idx % len(_APES)]
                ape2 = _APES[(idx + 11) % len(_APES)]

                # Código único
                num  = 1000 + idx
                codigo = f"{anio}115{_PERIODO_NUM}{num:04d}"
                while db.query(User).filter(User.codigo == codigo).first():
                    num += 1
                    codigo = f"{anio}115{_PERIODO_NUM}{num:04d}"

                # Cédula única
                cedula = _cedula(anio, num)
                attempt = 0
                while cedula in used_cedulas:
                    attempt += 1
                    cedula = _cedula(anio, num + attempt * 100)
                used_cedulas.add(cedula)

                prom = round(random.uniform(2.5, 5.0), 2)
                pct  = round(random.uniform(15.0, 95.0), 1)
                base_email = f"{_slug(nom)}.{_slug(ape1)}{num}"
                email = f"{base_email}@usco.edu.co"
                suffix = 1
                while email in used_emails:
                    email = f"{base_email}x{suffix}@usco.edu.co"
                    suffix += 1
                used_emails.add(email)

                est = User(
                    codigo=codigo,
                    nombres=nom,
                    apellidos=f"{ape1} {ape2}",
                    email=email,
                    cedula=cedula,
                    hashed_password=PW,
                    rol=RolEnum.estudiante,
                    promedio=prom,
                    porcentaje_creditos=pct,
                    programa="Ingeniería de Software",
                    sede="Neiva",
                )
                db.add(est)
                db.flush()

                # Matricular en las materias del semestre
                for cod in mats:
                    asig = asig_map.get(cod)
                    if not asig:
                        continue
                    already = db.query(AsignaturaEstudiante).filter_by(
                        asignatura_id=asig.id,
                        estudiante_id=est.id,
                        periodo_academico=PERIODO,
                    ).first()
                    if not already:
                        db.add(AsignaturaEstudiante(
                            asignatura_id=asig.id,
                            estudiante_id=est.id,
                            periodo_academico=PERIODO,
                        ))

                total_nuevos += 1

        db.commit()

        # ── 4. Resumen ─────────────────────────────────────────────────────────
        total_est = db.query(User).filter(User.rol == RolEnum.estudiante).count()
        print(f"\n  ✓  {total_nuevos} estudiantes nuevos.  Total estudiantes: {total_est}\n")

        print("  Cobertura final por materia (período 2026-1):")
        print("  " + "─" * 62)
        for asig in db.query(Asignatura).order_by(Asignatura.semestre, Asignatura.codigo).all():
            n = db.query(AsignaturaEstudiante).filter(
                AsignaturaEstudiante.asignatura_id == asig.id,
                AsignaturaEstudiante.periodo_academico == PERIODO,
            ).count()
            bar  = "█" * (n // 5)
            mark = "✓" if n >= 5 else "⚠"
            print(f"  {mark} {asig.codigo:10} sem={asig.semestre}  {asig.nombre[:30]:30}  {n:3} est.  {bar}")

        print("\n  Totales por cohorte:")
        print("  " + "─" * 40)
        for anio in sorted(COHORT_SUBJECTS.keys(), reverse=True):
            n = db.query(User).filter(
                User.rol == RolEnum.estudiante,
                User.codigo.like(f"{anio}%"),
            ).count()
            label = SEM_LABEL.get(anio, "?")
            bar   = "█" * n
            print(f"  {anio}  ({label:5})  {n:3} est.  {bar}")

    except Exception as e:
        db.rollback()
        import traceback; traceback.print_exc()
        print(f"\n  ✗ ERROR: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
