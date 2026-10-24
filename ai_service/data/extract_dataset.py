"""
AI-01 — Dataset extraction from sipam_db PostgreSQL database.
Generates synthetic applications using real student + subject data,
then applies the RF-MON-05 formula to label each record.
"""
import os
import random
import numpy as np
import pandas as pd
import psycopg2
from pathlib import Path

random.seed(42)
np.random.seed(42)

# ── DB connection ──────────────────────────────────────────────────────────
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:Sasuke24@localhost:5432/sipam_db",
)
os.environ.setdefault("PGCLIENTENCODING", "UTF8")


def get_connection():
    import re
    m = re.match(
        r"postgresql://([^:]+):([^@]+)@([^:/]+):(\d+)/(.+)", DB_URL
    )
    if not m:
        raise ValueError(f"Cannot parse DATABASE_URL: {DB_URL}")
    user, password, host, port, dbname = m.groups()
    return psycopg2.connect(
        dbname=dbname, user=user, password=password,
        host=host, port=int(port), client_encoding="utf8",
        options="-c client_encoding=UTF8",
    )


# ── Fetch real data ─────────────────────────────────────────────────────────
def fetch_students(conn) -> pd.DataFrame:
    query = """
        SELECT
            u.id,
            u.promedio,
            u.porcentaje_creditos,
            u.programa
        FROM users u
        WHERE u.rol = 'estudiante'
          AND u.is_active = TRUE
          AND u.promedio IS NOT NULL
          AND u.porcentaje_creditos IS NOT NULL
          AND u.promedio >= 3.5
          AND u.porcentaje_creditos >= 30
    """
    return pd.read_sql(query, conn)


def fetch_asignaturas(conn) -> pd.DataFrame:
    query = """
        SELECT
            a.id,
            a.nombre,
            a.creditos,
            a.semestre
        FROM asignaturas a
        WHERE a.is_active = TRUE
    """
    return pd.read_sql(query, conn)


# ── Synthetic data generation ───────────────────────────────────────────────
TIPO_MONITORIA_VALUES = [
    "nee", "regimenes_especiales", "academica_cursos", "laboratorios",
    "tic", "permanencia_graduacion", "deportiva", "cultural",
    "biblioteca", "acreditacion", "investigacion", "academica", "administrativa",
]


def _calcular_puntaje(nota_asig: float, promedio: float, entrevista: float) -> float:
    return round(nota_asig * 0.30 + promedio * 0.30 + entrevista * 0.40, 4)


def generate_dataset(
    students: pd.DataFrame,
    asignaturas: pd.DataFrame,
    n_convocatorias: int = 120,
    max_postulantes_per_conv: int = 12,
) -> pd.DataFrame:
    """
    Generates synthetic monitor applications.
    Each convocatoria selects the top-N students by puntaje_final.
    """
    rows = []

    for _ in range(n_convocatorias):
        tipo = random.choice(TIPO_MONITORIA_VALUES)
        n_monitores = random.randint(1, 4)
        asig = asignaturas.sample(1).iloc[0]
        n_postulantes = random.randint(max(n_monitores + 1, 3), max_postulantes_per_conv)

        # Sample eligible students
        pool = students.sample(min(n_postulantes, len(students)), replace=True)
        applicants = []

        for _, student in pool.iterrows():
            nota_asig = round(random.uniform(3.0, 5.0), 2)
            nota_entrev = round(random.uniform(2.5, 5.0), 2)
            puntaje = _calcular_puntaje(nota_asig, float(student["promedio"]), nota_entrev)
            applicants.append({
                "promedio": float(student["promedio"]),
                "porcentaje_creditos": float(student["porcentaje_creditos"]),
                "nota_asignatura": nota_asig,
                "nota_entrevista": nota_entrev,
                "puntaje_final": puntaje,
                "tipo_monitoria": tipo,
                "semestre_asignatura": int(asig["semestre"]),
                "creditos_asignatura": int(asig["creditos"]),
                "num_postulantes": n_postulantes,
                "num_monitores_requeridos": n_monitores,
            })

        # Label: top-N by puntaje are selected (1), rest not (0)
        applicants.sort(key=lambda x: x["puntaje_final"], reverse=True)
        for i, app in enumerate(applicants):
            app["seleccionado"] = 1 if i < n_monitores else 0
            # ── Engineered features ──────────────────────────────────────
            app["ratio_competencia"] = round(
                n_monitores / max(n_postulantes, 1), 4
            )
            app["puntaje_formula"] = app["puntaje_final"]
            rows.append(app)

    df = pd.DataFrame(rows)
    df.drop(columns=["puntaje_final"], inplace=True)
    return df


def main():
    print("[extract_dataset] Connecting to sipam_db ...")
    conn = get_connection()

    students = fetch_students(conn)
    asignaturas = fetch_asignaturas(conn)
    conn.close()

    print(f"[extract_dataset] Eligible students: {len(students)}")
    print(f"[extract_dataset] Active subjects:   {len(asignaturas)}")

    df = generate_dataset(students, asignaturas, n_convocatorias=200)

    out_path = Path(__file__).parent / "dataset.csv"
    df.to_csv(out_path, index=False)
    print(f"[extract_dataset] Dataset saved to {out_path}  ({len(df)} rows)")
    print(f"[extract_dataset] Class balance:\n{df['seleccionado'].value_counts()}")
    return df


if __name__ == "__main__":
    main()
