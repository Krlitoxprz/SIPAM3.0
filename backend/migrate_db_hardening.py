"""
Migración: Fortalecimiento y optimización del esquema PostgreSQL.

Cambios:
  CHECK constraints faltantes (7):
    1. tarifas_viaticos.valor_dia > 0
    2. monitoria_plantillas.horas_semana > 0
    3. monitoria_plantillas.horas_semestre > 0
    4. monitoria_plantillas.num_monitores_sugerido > 0
    5. monitoria_plantillas.promedio_minimo BETWEEN 0 AND 5
    6. postulaciones.puntaje_final BETWEEN 0 AND 5
    7. convocatorias.fecha_fin_postulacion > fecha_inicio_postulacion
    8. convocatorias.creditos_minimo_pct BETWEEN 0 AND 100
    9. precios_combustible.precio_litro > 0
   10. rutas_practica.distancia_km > 0 (nullable)
   11. practicas.total_firmas_obtenidas >= 0

  Índices faltantes (6):
    - tarifas_viaticos(is_active)
    - practicas(asignatura_id, periodo_academico)
    - practicas(fecha_inicio)
    - postulaciones(estado)
    - presupuestos(estado)
    - monitoria_plantillas(tipo_monitoria)

  Índice duplicado (1):
    - DROP ix_prt_token en password_reset_tokens.token

  DEFAULT en BD faltantes (3):
    - practicas.total_firmas_obtenidas DEFAULT 0
    - practicas.quorum_alcanzado DEFAULT false
    - notificaciones.leida DEFAULT false
    - users.is_active DEFAULT true
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.db.database import engine

CHECKS = [
    (
        "ck_tarifa_valor_dia",
        "tarifas_viaticos",
        "valor_dia > 0",
    ),
    (
        "ck_plantilla_horas_semana",
        "monitoria_plantillas",
        "horas_semana > 0",
    ),
    (
        "ck_plantilla_horas_semestre",
        "monitoria_plantillas",
        "horas_semestre > 0",
    ),
    (
        "ck_plantilla_monitores",
        "monitoria_plantillas",
        "num_monitores_sugerido > 0",
    ),
    (
        "ck_plantilla_promedio",
        "monitoria_plantillas",
        "promedio_minimo >= 0 AND promedio_minimo <= 5",
    ),
    (
        "ck_postulacion_puntaje",
        "postulaciones",
        "puntaje_final IS NULL OR (puntaje_final >= 0 AND puntaje_final <= 5)",
    ),
    (
        "ck_convocatoria_fechas",
        "convocatorias",
        "fecha_fin_postulacion > fecha_inicio_postulacion",
    ),
    (
        "ck_convocatoria_creditos_pct",
        "convocatorias",
        "creditos_minimo_pct IS NULL OR (creditos_minimo_pct >= 0 AND creditos_minimo_pct <= 100)",
    ),
    (
        "ck_precio_combustible_positivo",
        "precios_combustible",
        "precio_litro > 0",
    ),
    (
        "ck_ruta_distancia",
        "rutas_practica",
        "distancia_km IS NULL OR distancia_km > 0",
    ),
    (
        "ck_practica_firmas_obtenidas",
        "practicas",
        "total_firmas_obtenidas >= 0",
    ),
]

INDEXES = [
    ("ix_tarifas_is_active",       "CREATE INDEX IF NOT EXISTS ix_tarifas_is_active ON tarifas_viaticos (is_active)"),
    ("ix_practicas_asig_periodo",  "CREATE INDEX IF NOT EXISTS ix_practicas_asig_periodo ON practicas (asignatura_id, periodo_academico)"),
    ("ix_practicas_fecha_inicio",  "CREATE INDEX IF NOT EXISTS ix_practicas_fecha_inicio ON practicas (fecha_inicio)"),
    ("ix_postulaciones_estado",    "CREATE INDEX IF NOT EXISTS ix_postulaciones_estado ON postulaciones (estado)"),
    ("ix_presupuestos_estado",     "CREATE INDEX IF NOT EXISTS ix_presupuestos_estado ON presupuestos (estado)"),
    ("ix_plantillas_tipo",         "CREATE INDEX IF NOT EXISTS ix_plantillas_tipo ON monitoria_plantillas (tipo_monitoria)"),
]

DEFAULTS = [
    ("practicas",      "total_firmas_obtenidas", "0"),
    ("practicas",      "quorum_alcanzado",        "false"),
    ("notificaciones", "leida",                   "false"),
    ("users",          "is_active",               "true"),
]

DROP_DUPE_IDX = "ix_prt_token"


def constraint_exists(conn, name, table):
    r = conn.execute(text(
        "SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
        "WHERE c.conname = :name AND t.relname = :table"
    ), {"name": name, "table": table})
    return r.fetchone() is not None


def index_exists(conn, name):
    r = conn.execute(text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :name"
    ), {"name": name})
    return r.fetchone() is not None


def column_has_default(conn, table, column):
    r = conn.execute(text(
        "SELECT column_default FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    row = r.fetchone()
    return row and row[0] is not None


def run():
    print("=== Iniciando migración de fortalecimiento BD ===\n")
    with engine.connect() as conn:

        # ── CHECK CONSTRAINTS ──────────────────────────────────────────────
        print("► CHECK constraints:")
        for name, table, expr in CHECKS:
            if constraint_exists(conn, name, table):
                print(f"  ✓ Ya existe: {name}")
            else:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ({expr})"
                ))
                print(f"  + Creado:    {name}  ({table})")

        # ── ÍNDICES ────────────────────────────────────────────────────────
        print("\n► Índices:")
        for idx_name, ddl in INDEXES:
            if index_exists(conn, idx_name):
                print(f"  ✓ Ya existe: {idx_name}")
            else:
                conn.execute(text(ddl))
                print(f"  + Creado:    {idx_name}")

        # ── ÍNDICE DUPLICADO ───────────────────────────────────────────────
        print("\n► Índice duplicado:")
        if index_exists(conn, DROP_DUPE_IDX):
            conn.execute(text(f"DROP INDEX {DROP_DUPE_IDX}"))
            print(f"  - Eliminado: {DROP_DUPE_IDX} (duplicado de ix_password_reset_tokens_token)")
        else:
            print(f"  ✓ Ya no existe: {DROP_DUPE_IDX}")

        # ── DEFAULTS ──────────────────────────────────────────────────────
        print("\n► DEFAULT en BD:")
        for table, column, default in DEFAULTS:
            if column_has_default(conn, table, column):
                print(f"  ✓ Ya tiene DEFAULT: {table}.{column}")
            else:
                conn.execute(text(
                    f"ALTER TABLE {table} ALTER COLUMN {column} SET DEFAULT {default}"
                ))
                print(f"  + DEFAULT {default} → {table}.{column}")

        conn.commit()

    print("\n=== Migración completada exitosamente ===")


if __name__ == "__main__":
    run()
