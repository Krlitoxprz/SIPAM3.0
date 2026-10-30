"""add_check_constraints

Revision ID: a240a12162b2
Revises: b1e2f3a4c5d6
Create Date: 2026-10-24 16:47:23.563822

Traslada a los modelos (y por tanto a migraciones) lo que antes aplicaba el
script manual migrate_db_hardening.py:
- 11 CheckConstraint de validación de dominio (autogen no las emite sobre
  SQLite; se agregan manualmente — en Postgres son ALTER TABLE nativo y en
  SQLite el DDL queda en el CREATE TABLE de instalaciones nuevas)
- 6 índices de consulta frecuente
- 4 server_default para columnas con backfill ya aplicado
- Corrección de drift: ix_refresh_tokens_token_hash pasa a UNIQUE (el modelo
  ya lo declaraba unique=True)

Todas las operaciones son idempotentes/tolerantes a ausencia: las tablas que
hoy existen solo por create_all (no por migraciones) se saltan si faltan, y
los objetos ya creados por migrate_db_hardening.py no rompen la migración.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a240a12162b2'
down_revision: Union[str, Sequence[str], None] = 'b1e2f3a4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _safe(fn):
    """Ejecuta fn() dentro de un SAVEPOINT ignorando SOLO errores de
    idempotencia ('ya existe' / duplicados — DB previamente endurecida) sin
    abortar la transacción en PostgreSQL. Errores de validación (p. ej. filas
    existentes que violan un CHECK nuevo) se propagan para que la revisión
    falle y pueda reintentarse tras corregir los datos."""
    sp = op.get_bind().begin_nested()
    try:
        fn()
        sp.commit()
    except Exception as e:
        sp.rollback()
        msg = str(e).lower()
        if "already exists" not in msg and "duplicate" not in msg:
            raise


def upgrade() -> None:
    """Upgrade schema."""
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    # Índices
    indexes = [
        ('ix_plantillas_tipo', 'monitoria_plantillas', ['tipo_monitoria']),
        ('ix_postulaciones_estado', 'postulaciones', ['estado']),
        ('ix_practicas_asig_periodo', 'practicas', ['asignatura_id', 'periodo_academico']),
        ('ix_practicas_fecha_inicio', 'practicas', ['fecha_inicio']),
        ('ix_presupuestos_estado', 'presupuestos', ['estado']),
        ('ix_tarifas_is_active', 'tarifas_viaticos', ['is_active']),
    ]
    for name, table, cols in indexes:
        if table in existing:
            _safe(lambda n=name, t=table, c=cols: op.create_index(n, t, c, unique=False))

    # Drift: token_hash ya es unique=True en el modelo
    if 'refresh_tokens' in existing:
        _safe(lambda: op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens'))
        _safe(lambda: op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True))

    # CheckConstraints — manuales (autogenerate no las emite sobre SQLite).
    # En SQLite batch_alter_table recrea la tabla; en Postgres es ALTER nativo.
    checks = [
        ("tarifas_viaticos", "ck_tarifa_valor_dia", "valor_dia > 0"),
        ("monitoria_plantillas", "ck_plantilla_horas_semana", "horas_semana > 0"),
        ("monitoria_plantillas", "ck_plantilla_horas_semestre", "horas_semestre > 0"),
        ("monitoria_plantillas", "ck_plantilla_monitores", "num_monitores_sugerido > 0"),
        ("monitoria_plantillas", "ck_plantilla_promedio", "promedio_minimo >= 0 AND promedio_minimo <= 5"),
        ("postulaciones", "ck_postulacion_puntaje", "puntaje_final IS NULL OR (puntaje_final >= 0 AND puntaje_final <= 5)"),
        ("convocatorias", "ck_convocatoria_fechas", "fecha_fin_postulacion > fecha_inicio_postulacion"),
        ("convocatorias", "ck_convocatoria_creditos_pct", "creditos_minimo_pct IS NULL OR (creditos_minimo_pct >= 0 AND creditos_minimo_pct <= 100)"),
        ("precios_combustible", "ck_precio_combustible_positivo", "precio_litro > 0"),
        ("rutas_practica", "ck_ruta_distancia", "distancia_km IS NULL OR distancia_km >= 0"),
        ("practicas", "ck_practica_firmas_obtenidas", "total_firmas_obtenidas >= 0"),
    ]
    for table, name, expr in checks:
        if table not in existing:
            continue
        def _add(t=table, n=name, e=expr):
            with op.batch_alter_table(t) as batch:
                batch.create_check_constraint(n, sa.text(e))
        _safe(_add)

    # server_default (backfill ya garantizado por migrate_db_hardening.py)
    if 'practicas' in existing:
        def _pr():
            with op.batch_alter_table("practicas") as batch:
                batch.alter_column("total_firmas_obtenidas", existing_type=sa.Integer(), server_default="0")
                batch.alter_column("quorum_alcanzado", existing_type=sa.Boolean(), server_default=sa.false())
        _safe(_pr)
    if 'notificaciones' in existing:
        def _nt():
            with op.batch_alter_table("notificaciones") as batch:
                batch.alter_column("leida", existing_type=sa.Boolean(), server_default=sa.false())
        _safe(_nt)
    if 'users' in existing:
        def _us():
            with op.batch_alter_table("users") as batch:
                batch.alter_column("is_active", existing_type=sa.Boolean(), server_default=sa.true())
        _safe(_us)


def downgrade() -> None:
    """Downgrade schema."""
    existing = set(sa.inspect(op.get_bind()).get_table_names())

    if 'users' in existing:
        def _us():
            with op.batch_alter_table("users") as batch:
                batch.alter_column("is_active", existing_type=sa.Boolean(), server_default=None)
        _safe(_us)
    if 'notificaciones' in existing:
        def _nt():
            with op.batch_alter_table("notificaciones") as batch:
                batch.alter_column("leida", existing_type=sa.Boolean(), server_default=None)
        _safe(_nt)
    if 'practicas' in existing:
        def _pr():
            with op.batch_alter_table("practicas") as batch:
                batch.alter_column("quorum_alcanzado", existing_type=sa.Boolean(), server_default=None)
                batch.alter_column("total_firmas_obtenidas", existing_type=sa.Integer(), server_default=None)
        _safe(_pr)

    checks = [
        ("tarifas_viaticos", "ck_tarifa_valor_dia"),
        ("monitoria_plantillas", "ck_plantilla_horas_semana"),
        ("monitoria_plantillas", "ck_plantilla_horas_semestre"),
        ("monitoria_plantillas", "ck_plantilla_monitores"),
        ("monitoria_plantillas", "ck_plantilla_promedio"),
        ("postulaciones", "ck_postulacion_puntaje"),
        ("convocatorias", "ck_convocatoria_fechas"),
        ("convocatorias", "ck_convocatoria_creditos_pct"),
        ("precios_combustible", "ck_precio_combustible_positivo"),
        ("rutas_practica", "ck_ruta_distancia"),
        ("practicas", "ck_practica_firmas_obtenidas"),
    ]
    for table, name in checks:
        if table not in existing:
            continue
        def _drop(t=table, n=name):
            with op.batch_alter_table(t) as batch:
                batch.drop_constraint(n, type_="check")
        _safe(_drop)

    if 'refresh_tokens' in existing:
        _safe(lambda: op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens'))
        _safe(lambda: op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=False))

    # NOTA: no se eliminan los índices ix_* en downgrade. Pueden haber
    # preexistido a esta revisión (DB endurecida a mano) y solo afectan
    # rendimiento, no el esquema.
