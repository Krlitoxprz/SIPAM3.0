from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_DB_URL: str = settings.DATABASE_URL
if _DB_URL.startswith("postgres://"):
    _DB_URL = _DB_URL.replace("postgres://", "postgresql://", 1)

_IS_SQLITE: bool = _DB_URL.startswith("sqlite")

if _IS_SQLITE:
    engine = create_engine(
        _DB_URL,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        """Enable FK enforcement and WAL mode on every new SQLite connection."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.execute("PRAGMA synchronous = NORMAL")
        cursor.close()

else:
    engine = create_engine(
        _DB_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import user, convocatoria, postulacion, practica, presupuesto, notificacion, monitor, transporte  # noqa
    from app.models import documento_presupuesto, historial_estado, evaluacion_monitor, pago_viatico, password_reset  # noqa
    Base.metadata.create_all(bind=engine)
    _run_cross_migrations()   # ALTER TABLE — funciona en SQLite Y PostgreSQL
    if _IS_SQLITE:
        _run_migrations()     # Migraciones adicionales solo para SQLite
    try:
        _seed_plantillas()
    except Exception:
        pass
    try:
        _seed_monitoria_plantillas()
    except Exception:
        pass
    try:
        _seed_sistema_config()
    except Exception:
        pass
    try:
        _seed_precios_combustible()
    except Exception:
        pass
    try:
        _seed_peajes_nacionales()
    except Exception:
        pass


def _run_cross_migrations():
    """ALTER TABLE incremental — se ejecuta en AMBOS dialectos (SQLite y PostgreSQL).
    Cada sentencia falla silenciosamente si la columna ya existe."""
    cross_migrations = [
        # ── Campos previos necesarios en PostgreSQL ────────────────────────────
        "ALTER TABLE presupuestos ADD COLUMN monto_solicitado REAL",
        "ALTER TABLE practicas ADD COLUMN observaciones_jefe TEXT",
        "ALTER TABLE asignaturas ADD COLUMN facultad VARCHAR(200)",
        "ALTER TABLE convocatorias ADD COLUMN descripcion_actividades TEXT",
        "ALTER TABLE convocatorias ADD COLUMN sede VARCHAR(100)",
        "ALTER TABLE convocatorias ADD COLUMN fecha_publicacion_resultados TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE practicas ADD COLUMN tipo_docente VARCHAR(20)",
        "ALTER TABLE horas_monitor ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE configuracion_calendario ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "ALTER TABLE configuracion_calendario ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE audit_logs ADD COLUMN ip_address VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN telefono VARCHAR(30)",
        "ALTER TABLE users ADD COLUMN foto_url VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN email_personal VARCHAR(200)",
        "ALTER TABLE users ADD COLUMN bio TEXT",
        "ALTER TABLE users ADD COLUMN fecha_nacimiento DATE",
        "ALTER TABLE users ADD COLUMN ciudad VARCHAR(100)",
        "ALTER TABLE users ADD COLUMN linkedin_url VARCHAR(300)",
        "ALTER TABLE users ADD COLUMN github_url VARCHAR(300)",
        "ALTER TABLE rutas_practica ADD COLUMN vereda VARCHAR(200)",
        "ALTER TABLE rutas_practica ADD COLUMN es_rural INTEGER NOT NULL DEFAULT 0",
        # ── FO-16 Justificación Práctica Extramuros ────────────────────────────
        "ALTER TABLE practicas ADD COLUMN caracter_curso VARCHAR(30)",
        "ALTER TABLE practicas ADD COLUMN caracteristica_curso VARCHAR(30)",
        "ALTER TABLE practicas ADD COLUMN modalidad_docente VARCHAR(10)",
        "ALTER TABLE practicas ADD COLUMN hora_salida VARCHAR(5)",
        "ALTER TABLE practicas ADD COLUMN hora_llegada VARCHAR(5)",
        "ALTER TABLE practicas ADD COLUMN articulacion_curso TEXT",
        "ALTER TABLE practicas ADD COLUMN descripcion_practica TEXT",
        "ALTER TABLE practicas ADD COLUMN evaluacion TEXT",
        # ── Seguridad social estudiantes (AP-INF-FO-05) ───────────────────────
        "ALTER TABLE users ADD COLUMN eps VARCHAR(150)",
        "ALTER TABLE users ADD COLUMN arl VARCHAR(150)",
        "ALTER TABLE users ADD COLUMN fondo_pensiones VARCHAR(150)",
        # ── Índices FK faltantes (mejora de rendimiento en JOINs) ─────────────
        "CREATE INDEX IF NOT EXISTS ix_archivos_postulacion ON archivos_adjuntos (postulacion_id)",
        "CREATE INDEX IF NOT EXISTS ix_archivos_usuario ON archivos_adjuntos (usuario_id)",
        "CREATE INDEX IF NOT EXISTS ix_asignaturas_profesor ON asignaturas (profesor_id)",
        "CREATE INDEX IF NOT EXISTS ix_docs_presupuesto ON documentos_presupuesto (presupuesto_id)",
        "CREATE INDEX IF NOT EXISTS ix_docs_subido_por ON documentos_presupuesto (subido_por_id)",
        "CREATE INDEX IF NOT EXISTS ix_evaluacion_evaluado_por ON evaluaciones_monitor (evaluado_por_id)",
        "CREATE INDEX IF NOT EXISTS ix_historial_usuario ON historial_estados (usuario_id)",
        "CREATE INDEX IF NOT EXISTS ix_horas_aprobado_por ON horas_monitor (aprobado_por_id)",
        "CREATE INDEX IF NOT EXISTS ix_movimientos_practica_id ON movimientos_presupuestales (practica_id)",
        "CREATE INDEX IF NOT EXISTS ix_movimientos_responsable ON movimientos_presupuestales (responsable_id)",
        "CREATE INDEX IF NOT EXISTS ix_pass_reset_usuario ON password_reset_tokens (usuario_id)",
        "CREATE INDEX IF NOT EXISTS ix_practicas_asignatura ON practicas (asignatura_id)",
        "CREATE INDEX IF NOT EXISTS ix_viaticos_tarifa ON viaticos (tarifa_id)",
        # ── Índices extra de alto impacto ─────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS ix_practicas_profesor ON practicas (profesor_id)",
        "CREATE INDEX IF NOT EXISTS ix_firmas_estudiante ON firmas_consentimiento (estudiante_id)",
        "CREATE INDEX IF NOT EXISTS ix_users_programa ON users (programa)",
        "CREATE INDEX IF NOT EXISTS ix_users_sede ON users (sede)",
        # ── Índices compuestos (rendimiento en filtros frecuentes) ─────────────
        "CREATE INDEX IF NOT EXISTS ix_users_rol_activo ON users (rol, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_users_rol_programa ON users (rol, programa)",
        "CREATE INDEX IF NOT EXISTS ix_asignaturas_prof_activo ON asignaturas (profesor_id, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_asignaturas_prog_activo ON asignaturas (programa, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_matriculas_asig_periodo ON asignatura_estudiantes (asignatura_id, periodo_academico)",
        "CREATE INDEX IF NOT EXISTS ix_matriculas_est_periodo ON asignatura_estudiantes (estudiante_id, periodo_academico)",
        "CREATE INDEX IF NOT EXISTS ix_practicas_periodo_estado ON practicas (periodo_academico, estado)",
        "CREATE INDEX IF NOT EXISTS ix_convocatorias_prog_estado ON convocatorias (estado, periodo_academico)",
        "CREATE INDEX IF NOT EXISTS ix_audit_accion ON audit_logs (accion)",
        # ── NOT NULL en columnas de estado con default (solo PostgreSQL) ───────
        "UPDATE practicas SET estado = 'borrador' WHERE estado IS NULL",
        "UPDATE postulaciones SET estado = 'pendiente' WHERE estado IS NULL",
        # ── Float → NUMERIC en campos monetarios (exactitud financiera) ────────
        "ALTER TABLE presupuestos ALTER COLUMN monto_total_asignado TYPE NUMERIC(14,2) USING monto_total_asignado::NUMERIC(14,2)",
        "ALTER TABLE presupuestos ALTER COLUMN monto_solicitado TYPE NUMERIC(14,2) USING monto_solicitado::NUMERIC(14,2)",
        "ALTER TABLE presupuestos ALTER COLUMN monto_ejecutado TYPE NUMERIC(14,2) USING monto_ejecutado::NUMERIC(14,2)",
        "ALTER TABLE presupuestos ALTER COLUMN monto_comprometido TYPE NUMERIC(14,2) USING monto_comprometido::NUMERIC(14,2)",
        "ALTER TABLE movimientos_presupuestales ALTER COLUMN monto TYPE NUMERIC(14,2) USING monto::NUMERIC(14,2)",
        "ALTER TABLE tarifas_viaticos ALTER COLUMN valor_dia TYPE NUMERIC(14,2) USING valor_dia::NUMERIC(14,2)",
        "ALTER TABLE viaticos ALTER COLUMN valor_calculado TYPE NUMERIC(14,2) USING valor_calculado::NUMERIC(14,2)",
        "ALTER TABLE practica_plantillas ALTER COLUMN costo_bus_externo TYPE NUMERIC(14,2) USING costo_bus_externo::NUMERIC(14,2)",
        "ALTER TABLE practica_plantillas ALTER COLUMN costo_tiquetes TYPE NUMERIC(14,2) USING costo_tiquetes::NUMERIC(14,2)",
        "ALTER TABLE practica_plantillas ALTER COLUMN viat_docente_dias TYPE NUMERIC(4,1) USING viat_docente_dias::NUMERIC(4,1)",
        "ALTER TABLE practica_plantillas ALTER COLUMN viat_docente_valor_dia TYPE NUMERIC(14,2) USING viat_docente_valor_dia::NUMERIC(14,2)",
        # ── Float → NUMERIC en campos académicos (precisión exacta) ───────────
        "ALTER TABLE users ALTER COLUMN promedio TYPE NUMERIC(4,2) USING promedio::NUMERIC(4,2)",
        "ALTER TABLE users ALTER COLUMN porcentaje_creditos TYPE NUMERIC(5,2) USING porcentaje_creditos::NUMERIC(5,2)",
        "ALTER TABLE convocatorias ALTER COLUMN promedio_minimo TYPE NUMERIC(3,2) USING promedio_minimo::NUMERIC(3,2)",
        "ALTER TABLE convocatorias ALTER COLUMN creditos_minimo_pct TYPE NUMERIC(5,2) USING creditos_minimo_pct::NUMERIC(5,2)",
        "ALTER TABLE postulaciones ALTER COLUMN nota_asignatura TYPE NUMERIC(4,2) USING nota_asignatura::NUMERIC(4,2)",
        "ALTER TABLE postulaciones ALTER COLUMN promedio_estudiante TYPE NUMERIC(4,2) USING promedio_estudiante::NUMERIC(4,2)",
        "ALTER TABLE postulaciones ALTER COLUMN nota_entrevista TYPE NUMERIC(4,2) USING nota_entrevista::NUMERIC(4,2)",
        "ALTER TABLE postulaciones ALTER COLUMN puntaje_final TYPE NUMERIC(6,3) USING puntaje_final::NUMERIC(6,3)",
        "ALTER TABLE horas_monitor ALTER COLUMN horas TYPE NUMERIC(5,2) USING horas::NUMERIC(5,2)",
        "ALTER TABLE evaluaciones_monitor ALTER COLUMN nota_desempeno TYPE NUMERIC(4,2) USING nota_desempeno::NUMERIC(4,2)",
        "ALTER TABLE evaluaciones_monitor ALTER COLUMN puntualidad TYPE NUMERIC(4,2) USING puntualidad::NUMERIC(4,2)",
        "ALTER TABLE evaluaciones_monitor ALTER COLUMN calidad_academica TYPE NUMERIC(4,2) USING calidad_academica::NUMERIC(4,2)",
        "ALTER TABLE rutas_practica ALTER COLUMN distancia_km TYPE NUMERIC(8,3) USING distancia_km::NUMERIC(8,3)",
        "ALTER TABLE pagos_viaticos ALTER COLUMN monto_pagado TYPE NUMERIC(14,2) USING monto_pagado::NUMERIC(14,2)",
        "ALTER TABLE precios_combustible ALTER COLUMN precio_litro TYPE NUMERIC(10,4) USING precio_litro::NUMERIC(10,4)",
        # ── Acuerdo 003/2012 Art.3.e / Art.3.l / Art.7 ───────────────────────
        "ALTER TABLE practicas ADD COLUMN justificacion TEXT",
        "ALTER TABLE practicas ADD COLUMN metodologia TEXT",
        "ALTER TABLE practicas ADD COLUMN carta_autorizacion_empresa TEXT",
        "ALTER TABLE practicas ADD COLUMN informe_resultados TEXT",
        "ALTER TABLE practicas ADD COLUMN fecha_informe TIMESTAMP WITH TIME ZONE",
        # ── AP-INF-FO-05 — Desplazamiento vial ───────────────────────────────
        "ALTER TABLE practicas ADD COLUMN placa_vehiculo VARCHAR(20)",
        "ALTER TABLE practicas ADD COLUMN tipo_vehiculo VARCHAR(50)",
        "ALTER TABLE practicas ADD COLUMN empresa_transporte VARCHAR(200)",
        "ALTER TABLE practicas ADD COLUMN conductor_nombre VARCHAR(200)",
        # ── Perfil docente en usuario ─────────────────────────────────────────
        "ALTER TABLE users ADD COLUMN tipo_docente VARCHAR(20)",
        "ALTER TABLE users ADD COLUMN modalidad_docente VARCHAR(10)",
        # ── Acuerdo 012/2023 Art.4.c — Sanción disciplinaria ─────────────────
        "ALTER TABLE users ADD COLUMN sancionado_disciplinariamente BOOLEAN DEFAULT FALSE",
        # ── Configuración global del sistema (modo prueba) ────────────────────
        """CREATE TABLE IF NOT EXISTS sistema_config (
            id INTEGER PRIMARY KEY DEFAULT 1,
            testing_mode BOOLEAN NOT NULL DEFAULT FALSE
        )""",
        # ── Deduplicar y añadir UNIQUE a tablas de referencia de transporte ─────
        "DELETE FROM precios_combustible WHERE id NOT IN (SELECT MIN(id) FROM precios_combustible GROUP BY tipo, departamento, fecha_vigencia)",
        "DELETE FROM peajes_nacionales WHERE id NOT IN (SELECT MIN(id) FROM peajes_nacionales GROUP BY nombre)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_precio_combustible ON precios_combustible (tipo, departamento, fecha_vigencia)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_peaje_nombre ON peajes_nacionales (nombre)",
        # ── FK ON DELETE — corrige comportamiento en BD existente ─────────────
        "ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_usuario_id_fkey",
        "ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE historial_estados DROP CONSTRAINT IF EXISTS historial_estados_usuario_id_fkey",
        "ALTER TABLE historial_estados ADD CONSTRAINT historial_estados_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE SET NULL",
        "ALTER TABLE notificaciones DROP CONSTRAINT IF EXISTS notificaciones_usuario_id_fkey",
        "ALTER TABLE notificaciones ADD CONSTRAINT notificaciones_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE CASCADE",
        "ALTER TABLE password_reset_tokens DROP CONSTRAINT IF EXISTS password_reset_tokens_usuario_id_fkey",
        "ALTER TABLE password_reset_tokens ADD CONSTRAINT password_reset_tokens_usuario_id_fkey FOREIGN KEY (usuario_id) REFERENCES users(id) ON DELETE CASCADE",
        # ── NOT NULL en estado (se actualiza el default primero) ──────────────
        "ALTER TABLE practicas ALTER COLUMN estado SET DEFAULT 'borrador'",
        "ALTER TABLE practicas ALTER COLUMN estado SET NOT NULL",
        "ALTER TABLE postulaciones ALTER COLUMN estado SET DEFAULT 'pendiente'",
        "ALTER TABLE postulaciones ALTER COLUMN estado SET NOT NULL",
    ]
    for sql in cross_migrations:
        with engine.connect() as conn:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                conn.rollback()  # liberar la transacción fallida antes de devolver al pool


def _run_migrations():
    """Apply incremental schema changes for SQLite (new columns/indexes on existing tables).
    PostgreSQL omits this — create_all() already creates the full schema from the models."""
    migrations = [
        # ── Columnas nuevas ───────────────────────────────────────────────────
        "ALTER TABLE presupuestos ADD COLUMN monto_solicitado REAL",
        "ALTER TABLE practicas ADD COLUMN observaciones_jefe TEXT",
        "ALTER TABLE asignaturas ADD COLUMN facultad VARCHAR(200)",
        "ALTER TABLE convocatorias ADD COLUMN descripcion_actividades TEXT",
        "ALTER TABLE convocatorias ADD COLUMN sede VARCHAR(100)",
        "ALTER TABLE convocatorias ADD COLUMN fecha_publicacion_resultados DATETIME",
        "ALTER TABLE practicas ADD COLUMN tipo_docente VARCHAR(20)",
        "ALTER TABLE horas_monitor ADD COLUMN updated_at DATETIME",
        "ALTER TABLE configuracion_calendario ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE configuracion_calendario ADD COLUMN updated_at DATETIME",
        "ALTER TABLE audit_logs ADD COLUMN ip_address VARCHAR(50)",
        "ALTER TABLE users ADD COLUMN telefono VARCHAR(30)",
        "ALTER TABLE users ADD COLUMN foto_url VARCHAR(500)",
        # ── Tabla documentos presupuesto ──────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS documentos_presupuesto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            presupuesto_id INTEGER NOT NULL REFERENCES presupuestos(id),
            subido_por_id INTEGER NOT NULL REFERENCES users(id),
            tipo_solicitud VARCHAR(30) NOT NULL,
            nombre_original VARCHAR(255) NOT NULL,
            nombre_almacenado VARCHAR(255) NOT NULL,
            ruta VARCHAR(500) NOT NULL,
            descripcion TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        # ── Índices de rendimiento ────────────────────────────────────────────
        "CREATE INDEX IF NOT EXISTS ix_convocatorias_estado ON convocatorias (estado)",
        "CREATE INDEX IF NOT EXISTS ix_convocatorias_periodo ON convocatorias (periodo_academico)",
        "CREATE INDEX IF NOT EXISTS ix_convocatorias_profesor ON convocatorias (profesor_id)",
        "CREATE INDEX IF NOT EXISTS ix_asignaturas_programa ON asignaturas (programa)",
        "CREATE INDEX IF NOT EXISTS ix_matriculas_estudiante ON asignatura_estudiantes (estudiante_id)",
        "CREATE INDEX IF NOT EXISTS ix_postulaciones_estudiante ON postulaciones (estudiante_id)",
        "CREATE INDEX IF NOT EXISTS ix_postulaciones_conv_estado ON postulaciones (convocatoria_id, estado)",
        "CREATE INDEX IF NOT EXISTS ix_practicas_estado ON practicas (estado)",
        "CREATE INDEX IF NOT EXISTS ix_practicas_periodo_prof ON practicas (periodo_academico, profesor_id)",
        "CREATE INDEX IF NOT EXISTS ix_rutas_practica ON rutas_practica (practica_id)",
        "CREATE INDEX IF NOT EXISTS ix_firmas_practica ON firmas_consentimiento (practica_id)",
        "CREATE INDEX IF NOT EXISTS ix_viaticos_practica ON viaticos (practica_id)",
        "CREATE INDEX IF NOT EXISTS ix_horas_postulacion ON horas_monitor (postulacion_id)",
        "CREATE INDEX IF NOT EXISTS ix_audit_usuario ON audit_logs (usuario_id)",
        "CREATE INDEX IF NOT EXISTS ix_audit_entidad ON audit_logs (entidad, entidad_id)",
        "CREATE INDEX IF NOT EXISTS ix_audit_created ON audit_logs (created_at)",
        "CREATE INDEX IF NOT EXISTS ix_notificaciones_usuario_leida ON notificaciones (usuario_id, leida)",
        "CREATE INDEX IF NOT EXISTS ix_notificaciones_created ON notificaciones (created_at)",
        "CREATE INDEX IF NOT EXISTS ix_movimientos_presupuesto ON movimientos_presupuestales (presupuesto_id)",
        "CREATE INDEX IF NOT EXISTS ix_movimientos_fecha ON movimientos_presupuestales (fecha_movimiento)",
        "CREATE INDEX IF NOT EXISTS ix_users_rol ON users (rol)",
        "CREATE INDEX IF NOT EXISTS ix_users_cedula ON users (cedula)",
        # ── Índices adicionales (revisión v2) ────────────────────────────────
        "CREATE INDEX IF NOT EXISTS ix_users_rol_activo ON users (rol, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_asignaturas_prof_activo ON asignaturas (profesor_id, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_matriculas_asig_periodo ON asignatura_estudiantes (asignatura_id, periodo_academico)",
        "CREATE INDEX IF NOT EXISTS ix_archivos_postulacion ON archivos_adjuntos (postulacion_id)",
        "CREATE INDEX IF NOT EXISTS ix_audit_accion ON audit_logs (accion)",
        "CREATE INDEX IF NOT EXISTS ix_pago_viatico_practica ON pagos_viaticos (practica_id)",
        "CREATE INDEX IF NOT EXISTS ix_historial_entidad ON historial_estados (entidad, entidad_id)",
        "CREATE INDEX IF NOT EXISTS ix_historial_created ON historial_estados (created_at)",
        # ── Restricciones de unicidad (no duplicados) ─────────────────────────
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_matricula ON asignatura_estudiantes (asignatura_id, estudiante_id, periodo_academico)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_postulacion ON postulaciones (convocatoria_id, estudiante_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_firma_practica ON firmas_consentimiento (practica_id, estudiante_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ruta_orden ON rutas_practica (practica_id, orden)",
        # ── Campos geográficos en rutas_practica ─────────────────────────────
        "ALTER TABLE rutas_practica ADD COLUMN vereda VARCHAR(200)",
        "ALTER TABLE rutas_practica ADD COLUMN es_rural INTEGER NOT NULL DEFAULT 0",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_horas_semana ON horas_monitor (postulacion_id, semana)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_convocatoria_asig_periodo ON convocatorias (asignatura_id, periodo_academico)",
        # ── Campos FO-16 Justificación Práctica Extramuros ───────────────────
        "ALTER TABLE practicas ADD COLUMN caracter_curso VARCHAR(30)",
        "ALTER TABLE practicas ADD COLUMN caracteristica_curso VARCHAR(30)",
        "ALTER TABLE practicas ADD COLUMN modalidad_docente VARCHAR(10)",
        "ALTER TABLE practicas ADD COLUMN hora_salida VARCHAR(5)",
        "ALTER TABLE practicas ADD COLUMN hora_llegada VARCHAR(5)",
        "ALTER TABLE practicas ADD COLUMN articulacion_curso TEXT",
        "ALTER TABLE practicas ADD COLUMN descripcion_practica TEXT",
        "ALTER TABLE practicas ADD COLUMN evaluacion TEXT",
        # ── Renombrado de roles (reestructuración jerarquía) ──────────────────
        "UPDATE users SET rol = 'jefe_programa' WHERE rol = 'encargado_facultad'",
        # ── Seguridad social estudiantes (AP-INF-FO-05) ───────────────────────
        "ALTER TABLE users ADD COLUMN eps VARCHAR(150)",
        "ALTER TABLE users ADD COLUMN arl VARCHAR(150)",
        "ALTER TABLE users ADD COLUMN fondo_pensiones VARCHAR(150)",
        # ── Plantillas de prácticas extramuros (Excel institucional) ──────────
        """CREATE TABLE IF NOT EXISTS practica_plantillas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(500) NOT NULL,
            programa VARCHAR(200),
            sede VARCHAR(100),
            asignatura VARCHAR(300),
            profesor VARCHAR(300),
            caracter_curso VARCHAR(5),
            ruta_texto TEXT,
            visitas_fo16 TEXT,
            tipo_bus VARCHAR(20),
            costo_bus_externo REAL,
            costo_tiquetes REAL,
            viat_docente_dias REAL,
            viat_docente_valor_dia REAL
        )""",
        "CREATE INDEX IF NOT EXISTS ix_plantillas_programa ON practica_plantillas (programa)",
        # ── Columna profesor en plantillas (fuerza re-seed con datos del Excel) ──
        "ALTER TABLE practica_plantillas ADD COLUMN IF NOT EXISTS profesor VARCHAR(300)",
        "DELETE FROM practica_plantillas WHERE profesor IS NULL",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # ya existe — ignorar
    try:
        _seed_plantillas()
    except Exception:
        pass  # seed nunca debe romper el arranque


def _seed_plantillas():
    """Inserta plantillas de prácticas extramuros si la tabla está vacía (datos del Excel institucional 2026)."""
    # (nombre, programa, sede, asignatura, caracter_curso, ruta_texto, tipo_bus,
    #  costo_bus_externo, costo_tiquetes, viat_docente_dias, viat_docente_valor_dia, profesor)
    _PLANTILLAS = [
        # ── Ingeniería Agrícola ──────────────────────────────────────────────
        # ── Ingeniería Agrícola ──────────────────────────────────────────────────
        ("Práctica integral de suelos","Ingeniería Agrícola","Neiva / La Plata","Suelos","TP","La Plata (Usco) - Neiva (Usco) - Bogotá (Jardín Botánico, Museo IGAC, Universidad Nacional, Museo Geológico) Tabaitata (Agrosavia) - Neiva (Usco) - La Plata (Usco)","EXTERNO",3340000.0,None,2.5,444947.0,"Jhon Jairo Arévalo Hernández · Johnny Mauricio Gutierrez Marroquín"),
        ("Práctica integral de ingeniería drenajes // Práctica integral para el reconocimiento de riegos","Ingeniería Agrícola","Neiva / La Plata","Drenajes agrícolas / Riegos II","TP","La Plata (Usco) - Neiva (Usco) Valle, La Unión (Asorut, hotel CasaBlanca) - Ingenio Riopaila Zarzal - Neiva (Usco) - La Plata (Usco)","EXTERNO",2740000.0,None,3.5,410032.0,"Oscar Eduardo Gutiérrez Olaya · Javier Eduardo Bonilla Perdomo"),
        ("Práctica integral de fertilidad y nutrición","Ingeniería Agrícola","Neiva / La Plata","Fertilidad y nutrición","TP","La Plata (Usco) - Neiva (Usco) - Palermo (Dolomitas Rivera) - Espinal, Tolima (Agrosavia) - Neiva (Usco) - La Plata (Usco)","EXTERNO",3740000.0,None,1.5,205016.0,"Johnny Mauricio Gutierrez Marroquín"),
        ("Producción de semillas y tecnologías de producción (Agrosavia)","Ingeniería Agrícola","Neiva","Fisiología vegetal","TP","Neiva (Usco) - Natagaima (Agrosavia) - Mosquera, Cundinamarca (Agrosavia Tabaitata) - Neiva (Usco)","EXTERNO",3420000.0,None,1.5,205016.0,"Wilmer Licerio Ladino Garzón"),
        ("Visita de construcciones rurales a Cundinamarca","Ingeniería Agrícola","Neiva","Construcciones rurales","TP","Neiva (Usco) - Fomeque, Choachí y Ubaqué - Neiva (Usco)","EXTERNO",2630000.0,None,3.5,329834.0,"Wilson Javier Erazo Espinosa"),
        ("Reconocimiento perfiles de suelo, abonos orgánicos e invertebrados - Casa Luker (Garzón)","Ingeniería Agrícola","Garzón","Suelos","TP","Garzón (Usco) - Agrado (Casa Luker, Granja Experimental) - Garzón (Usco)","EXTERNO",530000.0,None,0.7,205016.0,"Daniel Felipe Fernández Reyes"),
        ("Identificación de factores en manejo y conservación de productos agropecuarios (Garzón)","Ingeniería Agrícola","Garzón / La Plata","Manejo y conservación de productos agropecuarios","TP","Garzón (Usco) - Pitalito, Vía Guacayo (Herrera café, TecnoparqueYamboró) - Bruselas, Pitalito (Asociación Glorietas) - Garzón (Usco)","INTERNO",None,None,2.5,410032.0,"Oscar Mauricio Barrera Bermeo · Yaneth Liliana Ruíz Osorio"),
        ("Visita a planta para visualizar conceptos de secado (Garzón)","Ingeniería Agrícola","Garzón","Secado de productos biológicos","TP","Garzón (Usco) - Garzón (Quimbo fish, panificadora Fellini) - Gigante (Fedecacao) - Pitalito (café Herrera, hacienda Laboyos) - vía batallón","TIQUETES",None,None,2.5,205016.0,"Oscar Mauricio Barrera Bermeo"),
        ("Características de los ecosistemas - Garzón / La Plata","Ingeniería Agrícola","Garzón / La Plata","Ecología","TP","Garzón (Usco) - Garzón (vía vereda Zuluaga) - Gigante (vereda Vega) - Villavieja (Desierto de la Tatacoa) - Garzón (Usco)","EXTERNO",1920000.0,None,1.5,410032.0,"Martha Lucía Peña Quimbaya · Yanet Caridad Apin Campos"),
        ("Práctica de motores de combustión interna (Garzón / Pitalito)","Ingeniería Agrícola","Garzón / Pitalito","Fuentes de potencia","TP","Pitalito (Usco) - Garzón (Usco) - Laboratorio combustión Universidad de Ibagué - Garzón (Usco) - Pitalito (Usco)","EXTERNO",3240000.0,None,1.0,205016.0,"Miyer Javier Valdés Ortiz · Giovanni Andrés Vargas Galván"),
        ("Implementación y tecnologías de agricultura de precisión en Pajonales (Garzón)","Ingeniería Agrícola","Garzón / La Plata / Pitalito","Máquinas agrícolas","TP","Pitalito (Usco) - Garzón (Usco) - La Plata (Usco) - Pajonales - Ambalema - Tolima - La Plata (Usco) - Garzón (Usco) - Pitalito (Usco)","INTERNO",None,None,1.5,615048.0,"Jairo Murcia Leal · Miyer Javier Valdés Ortiz · Giovanni Andrés Vargas Galván"),
        ("Práctica integral para obras hidráulicas en distrito de riego (Garzón)","Ingeniería Agrícola","Garzón","Hidráulica","TP","La Plata (Usco) - Garzón (Usco) - Distrito triángulo del Tolima - Neiva (Usco) - Garzón (Usco) - La Plata (Usco)","EXTERNO",1790000.0,None,2.5,205016.0,"Héctor Jair Beltrán Vargas"),
        ("Componentes de estación meteorológica","Ingeniería Agrícola","Garzón / La Plata","Hidrología","TP","La Plata (Usco) - Garzón (Usco) - Distrito Triángulo del Tolima - Neiva (Usco) - Garzón (Usco) - La Plata (Usco)","EXTERNO",1790000.0,None,1.0,205016.0,"Héctor Jair Beltrán Vargas"),
        ("Práctica integral para el reconocimiento de sistemas de riegos en Valle del Cauca (Garzón)","Ingeniería Agrícola","Garzón / Pitalito","Ingeniería de riegos II","TP","Garzón (Usco) - Valle del Cauca, La Unión - Garzón (Usco)","EXTERNO",3230000.0,None,3.5,410032.0,"Jhon Jairo Vargas Hoyos · Jhon Jairo Beltrán Díaz"),
        ("Reconocimiento de componentes y sistemas de drenajes agrícolas (Garzón)","Ingeniería Agrícola","Garzón / Pitalito","Drenajes agrícolas","TP","Garzón (Usco) - Palmira (Ingenio providencia, Ingenio Incauca, Ortigal) - Garzón (Usco)","INTERNO",None,None,3.5,410032.0,"Jhon Jairo Vargas Hoyos · Edinson Mujica Rodríguez"),
        ("Práctica para la identificación y evaluación de estructuras hidráulicas (Garzón / La Plata)","Ingeniería Agrícola","Garzón / La Plata","Hidráulica","TP","La Plata (Usco) - Triángulo del Tolima (Coyaima) - Palermo (Distrito el Juncal) - La Ulloa - Rivera - Usoigua - Campoalegre - La Plata (Usco)","EXTERNO",1920000.0,None,2.5,410032.0,"Oscar Eduardo Gutiérrez Olaya · Héctor Jair Beltrán Vargas"),
        ("Identificación de factores en manejo y conservación de productos (Garzón / La Plata)","Ingeniería Agrícola","Garzón / La Plata","Manejo y conservación de productos agropecuarios","TP","Garzón (Usco) - La Plata (Usco) - Paicol (Apigranja) - Pitalito (Café Herrera) - Hacienda laboyanos - La Plata (Usco) - Garzón (Usco)","INTERNO",None,None,2.5,410032.0,"Oscar Mauricio Barrera Bermeo · Yaneth Liliana Ruíz Osorio"),
        ("Características morfológicas de los granos (La Plata)","Ingeniería Agrícola","La Plata","Secado de productos biológicos","TP","La Plata (Usco) - Garzón (Parque industrial Coocentral) - Garzón, Huila - La Plata (Usco)","TIQUETES",None,None,0.7,205016.0,"Dennis Milena Villamil Ospina"),
        ("Reconocimiento de prácticas de manejo en cuenca del río Las Ceibas","Ingeniería Agrícola","La Plata","Manejo y conservación de suelos","TP","La Plata (Usco) - Vereda Santa Lucia, corregimiento Vegalarga (Reserva de Veragua) - Palermo (Finca Villa Lavi) - La Plata (Usco)","EXTERNO",1250000.0,None,0.7,205016.0,"Johnny Mauricio Gutiérrez Marroquín"),
        ("Manejo del microclima dentro del invernadero y cultivo de tomate","Ingeniería Agrícola","La Plata","Manejo de cultivos en invernadero","TP","La Plata (Usco) - Nataga - Finca los Naranjos - Vereda el Triunfo - La Plata (Usco)","EXTERNO",800000.0,None,0.7,205016.0,"Eddinson Ortega Martínez"),
        ("Reconocimiento y caracterización de planta de tratamiento PTAR (La Plata)","Ingeniería Agrícola","La Plata","Calidad de aguas","TP","La Plata (Usco) - Altamira (Planta de tratamiento de agua residual, PTAR) - La Plata (Usco)","EXTERNO",2530000.0,None,0.7,205016.0,"Yanet Caridad Apin Campos"),
        ("Fisiología aplicada al mejoramiento vegetal (La Plata)","Ingeniería Agrícola","La Plata","Fisiología Vegetal","TP","La Plata (Usco) - Campoalegre (Centro de formación Agroindustrial la Angostura Sena) - La Plata (Usco)","EXTERNO",1410000.0,None,0.7,205016.0,"Yanet Caridad Apin Campos"),
        ("Identificación de tecnologías para poscosecha del café - Vereda (La Plata)","Ingeniería Agrícola","La Plata","Tecnología del Café","TP","La Plata (Usco) - Vereda Alto Cañada (Asociación de caficultores) - La Plata (Usco)","EXTERNO",910000.0,None,0.7,205016.0,"Yaneth Liliana Ruíz Osorio"),
        ("Identificación de tecnologías para poscosecha del café - Cersucafé (La Plata)","Ingeniería Agrícola","La Plata","Tecnología del Café","TP","La Plata (Usco) - Neiva (Cersucafé) - La Plata (Usco)","EXTERNO",1520000.0,None,0.7,205016.0,"Yaneth Liliana Ruíz Osorio"),
        ("Implementación y tecnologías de agricultura de precisión en Pajonales (La Plata)","Ingeniería Agrícola","Garzón / La Plata / Pitalito","Máquinas agrícolas","TP","Pitalito (Usco) - Garzón (Usco) - La Plata (Usco) - Pajonales - Ambalema - Tolima - La Plata (Usco) - Garzón (Usco) - Pitalito (Usco)","EXTERNO",3230000.0,None,1.5,615048.0,"Miyer Javier Valdés Ortiz · Jairo Murcia Leal · Giovanni Andrés Vargas Galvan"),
        ("Práctica integral para la identificación de distritos de riego (La Plata)","Ingeniería Agrícola","La Plata","Pequeña Irrigación","TP","La Plata (Usco) - Usoigua - Ovejeras - Campoalegre - La Ulloa - Rivera - Triangulo del Tolima - Coyaima Tolima - La Plata (Usco)","EXTERNO",1690000.0,None,2.5,205016.0,"Oscar Eduardo Gutiérrez Olaya"),
        ("Identificación de elementos de sistema de riego y diseño (La Plata / Garzón)","Ingeniería Agrícola","Garzón / La Plata","Ingeniería de riegos I","TP","La Plata (Usco) - Pital - Agrado - Garzón - La Plata (Usco)","EXTERNO",950000.0,None,1.5,205016.0,"Oscar Eduardo Gutiérrez Olaya"),
        ("El desarrollo sostenible entorno en la finca agroecológica","Ingeniería Agrícola","La Plata","Desarrollo sostenible y medio ambiente","TP","La Plata (Usco) - Tesalia - Vereda el Dave - Vereda el Moral - La Plata (Usco)","EXTERNO",2530000.0,None,0.7,205016.0,"Martha Lucia Peña Quimbaya"),
        ("Práctica integral para obras hidráulicas en canales (Pitalito)","Ingeniería Agrícola","Pitalito","Hidráulica","TP","Pitalito (Usco) - Garzón (Usco) - Neiva (Usco) - Distrito de riego el Juncal - Distrito San Alfonso - Villavieja - Garzón (Usco) - Pitalito (Usco)","EXTERNO",1750000.0,None,2.5,205016.0,"Jhon Jairo Beltrán Díaz"),
        ("Reconocimiento de la reserva El Encanto para identificar especies bióticas y abióticas","Ingeniería Agrícola","Pitalito","Ecología","TP","Pitalito (Usco) - Palestina (Reserva el Encanto) - Pitalito (Usco)","TIQUETES",72000.0,None,1.5,205016.0,"Damaris Perdomo Medina"),
        ("Caracterización in situ de la fuente hídrica Guachicos","Ingeniería Agrícola","Pitalito","Calidad de aguas","TP","Pitalito (Usco) - Río Guachicos - Pitalito (Usco)","EXTERNO",800000.0,None,1.0,30000.0,"Damaris Perdomo Medina"),
        ("El desarrollo rural del sector agrícola en el sur del Huila","Ingeniería Agrícola","Pitalito","Desarrollo y extensión rural","T","Pitalito (Usco) - Garzón (Quimbo Fix) - Agrado (Chocolate la Hermandad) - Pitalito (Finca Villa Valentina) - San Agustín (finca Llanada) - Pitalito (Usco)","EXTERNO",3840000.0,None,1.5,205016.0,"Luisa Marcela Cerquera Barrera"),
        ("Tecnificación de drenaje agrícola superficial y subsuperficial (Pitalito)","Ingeniería Agrícola","Garzón / Pitalito","Drenajes agrícolas","TP","Pitalito (Usco) - Garzón (Usco) - Neiva - Natagaima - Espinal - Palmira - Ingenio Incauca y providencia - Palmaseca - Garzón (Usco) - Pitalito (Usco)","INTERNO",None,None,3.5,410032.0,"Jhon Jairo Vargas Hoyos · Edison Mujica Rodríguez"),
        ("Práctica integral para riegos por aspersión en distrito RUT - Valle del Cauca","Ingeniería Agrícola","Garzón / Pitalito","Ingeniería de riegos II","TP","Pitalito (Usco) - Garzón (Usco) - Distrito de riego y drenaje el Rut (Asorut) Riopaila - Garzón (Usco) - Pitalito (Usco)","EXTERNO",3840000.0,None,3.5,410032.0,"Jhon Jairo Beltrán Díaz · Jhon Jairo Vargas Hoyos"),
        ("Identificación de factores en manejo y conservación de productos agropecuarios (Pitalito)","Ingeniería Agrícola","Pitalito","Manejo y conservación de productos agropecuarios","TP","Pitalito (Usco) - Isnos (Café especial VB) y empresas Pulpifruit - Pitalito (Usco)","EXTERNO",1560000.0,None,1.0,30000.0,"Victor Manuel Martínez Castro"),
        ("Visita a planta para visualizar conceptos de secado (Pitalito)","Ingeniería Agrícola","Pitalito","Secado de productos biológicos","TP","Pitalito (Usco) - Purificación, Tolima (Molino Sonora) - El Agrado (Finca poscosecha cacao) - Garzón (parque industrial Coocentral) - Pitalito (Usco)","EXTERNO",None,None,1.5,205016.0,"Victor Manuel Martínez Castro"),
        ("Identificación de tecnologías para poscosecha e industrialización del café (Pitalito)","Ingeniería Agrícola","Pitalito","Tecnología del Café","TP","Pitalito (Usco) - Neiva (Universidad Surcolombiana, Cersucafé) - Pitalito (Usco)","TIQUETES",None,140000.0,0.7,205016.0,"Victor Manuel Martínez Castro"),
        ("Práctica de motores de combustión interna (Pitalito)","Ingeniería Agrícola","Garzón / Pitalito","Fuentes de potencia","TP","Pitalito (Usco) - Garzón (Usco) - Ibagué, Tolima (Laboratorio combustión Universidad de Ibagué) - Garzón (Usco) - Pitalito (Usco)","TIQUETES",None,240000.0,1.0,205016.0,"Miyer Javier Valdés Ortiz · Giovanny Andrés Vargas Galvan"),
        ("Implementación y tecnologías de agricultura de precisión en Pajonales (Pitalito)","Ingeniería Agrícola","Garzón / La Plata / Pitalito","Máquinas agrícolas","TP","Pitalito (Usco) - Garzón (Usco) - La Plata (Usco) - Pajonales - Ambalema - Tolima - La Plata (Usco) - Garzón (Usco) - Pitalito (Usco)","INTERNO",None,None,1.5,615048.0,"Miyer Javier Valdés Ortiz · Jairo Murcia Leal · Giovanny Andrés Vargas Galvan"),
        ("Visita a plantas de tratamiento de aguas residuales y Pajonales","Ingeniería Agrícola","Pitalito","Saneamiento urbano y rural","TP","Pitalito (Usco) - San Agustín - Timaná - Neiva - Yaguará - Palermo - Campoalegre - Hobo - Pitalito (Usco)","INTERNO",None,None,1.5,205016.0,"Edison Mujica Rodríguez"),
        # ── Ing. Agrícola — Prácticas en Granja / Laboratorios ─────────────────
        ("Prácticas contempladas en el microdiseño - Máquinas Agrícolas (Neiva)","Ingeniería Agrícola","Neiva","Máquinas Agrícolas","TP","Neiva (Usco) - Palermo (Granja Experimental) - Neiva (Usco)","EXTERNO",860000.0,None,1.0,30000.0,"Miguel Ángel Díaz Herrera"),
        ("Curso Teórico-Práctico en Granja Experimental - Producción Agrícola","Ingeniería Agrícola","Neiva","Producción Agrícola","T","Neiva (Usco) - Palermo (Granja Experimental) - Neiva (Usco)","EXTERNO",910000.0,None,1.0,30000.0,"Nadia Brigitte Sanabria Méndez"),
        ("Curso Teórico-Práctico en Granja Experimental - Fuentes de Potencia","Ingeniería Agrícola","Neiva","Fuentes de Potencia","TP","Neiva (Usco) - Palermo (Granja Experimental) - Neiva (Usco)","EXTERNO",860000.0,None,1.0,30000.0,"José Daniel Cardona Cárdenas"),
        ("Curso Teórico-Práctico en Granja Experimental - Fertilidad y Nutrición","Ingeniería Agrícola","Neiva / La Plata","Fertilidad y Nutrición","TP","Neiva (Usco) - Palermo (Granja Experimental) - Neiva (Usco)","INTERNO",None,None,1.0,30000.0,"Johnny Mauricio Gutierrez Marroquín"),
        ("Práctica de tractores - Patinamiento","Ingeniería Agrícola","Garzón / La Plata / Pitalito","Fuentes de Potencia","TP","Pitalito (Usco) - Garzón (Usco) - La Plata (Usco) - Palermo (Granja Experimental) - La Plata (Usco) - Garzón (Usco) - Pitalito (Usco)","INTERNO",None,None,0.7,205016.0,"Miyer Javier Valdés Ortiz · Jairo Murcia Leal · Giovanni Andrés Vargas Galván"),
        ("Práctica de sistemas mecánicos en maquinaria agrícola","Ingeniería Agrícola","Garzón / Pitalito","Elementos de máquinas","TP","Pitalito (Usco) - Garzón (Usco) - Palermo (Granja Experimental) - Garzón (Usco) - Pitalito (Usco)","EXTERNO",2220000.0,None,0.7,205016.0,"Miyer Javier Valdés Ortiz · Giovanni Andrés Vargas Galván"),
        ("Práctica de libranza primaria y secundaria siembra, fertilización y protección","Ingeniería Agrícola","Garzón / La Plata / Pitalito","Máquinas Agrícolas","TP","Pitalito (Usco) - Garzón (Usco) - La Plata (Usco) - Palermo (Granja Experimental) - La Plata (Usco) - Garzón (Usco) - Pitalito (Usco)","INTERNO",None,None,0.7,205016.0,"Miyer Javier Valdés Ortiz · Jairo Murcia Leal · Giovanni Andrés Vargas Galván"),
        ("Práctica de cultivo, recolección, manejo y acondicionamiento de forrajes","Ingeniería Agrícola","Garzón / La Plata / Pitalito","Máquinas Agrícolas","TP","Pitalito (Usco) - Garzón (Usco) - La Plata (Usco) - Palermo (Granja Experimental) - La Plata (Usco) - Garzón (Usco) - Pitalito (Usco)","EXTERNO",2820000.0,944000.0,0.7,205016.0,"Jairo Murcia Leal · Miyer Javier Valdés Ortiz · Giovanni Andrés Vargas Galván"),
        ("Determinación de uniformidad de riego y velocidad de infiltración (Garzón / Pitalito)","Ingeniería Agrícola","Garzón / Pitalito","Ingeniería de riegos I y II","TP","Pitalito (Usco) - Garzón (Usco) - Palermo (Granja Experimental) - Garzón (Usco) - Pitalito (Usco)","EXTERNO",2220000.0,None,0.7,205016.0,"Jhon Jairo Vargas Hoyos · Jhon Jairo Beltrán Díaz"),
        ("Determinación de uniformidad de riego y velocidad de infiltración (La Plata)","Ingeniería Agrícola","La Plata","Ingeniería de riegos I","TP","La Plata (Usco) - Palermo (Granja Experimental) - La Plata (Usco)","EXTERNO",1270000.0,None,0.7,205016.0,"Oscar Eduardo Gutiérrez Olaya"),
        ("Determinación de velocidad de infiltración en Granja Experimental (Neiva)","Ingeniería Agrícola","Neiva","Ingeniería de riegos I","TP","Neiva (Usco) - Palermo (Granja Experimental) - Neiva (Usco)","INTERNO",None,None,1.0,30000.0,"Jhon Jairo Arévalo Hernández"),
        ("Evaluación del sistema de riego por aspersión y goteo en Granja Experimental (Neiva)","Ingeniería Agrícola","Neiva","Ingeniería de riegos I","TP","Neiva (Usco) - Palermo (Granja Experimental) - Neiva (Usco)","EXTERNO",850000.0,None,1.0,30000.0,"Jhon Jairo Arévalo Hernández"),
        ("Evaluación de estándares de calidad y legislación en agua potable (Garzón)","Ingeniería Agrícola","Garzón","Calidad de aguas","","Garzón (Usco) - Palermo (Granja Experimental) - Garzón (Usco)","",None,None,1.0,30000.0,"Silvia Cristina Carrera Quintana"),
        ("Producción, procesos y comercialización de productos acuícolas","Ingeniería Agrícola","Garzón","Procesos agroindustriales en la acuicultura","","Garzón (Usco) - Palermo (Granja Experimental) - Garzón (Usco)","",None,None,1.0,30000.0,"Silvia Cristina Carrera Quintana"),
        # ── Ing. Agrícola — Laboratorios en USCO Neiva ─────────────────────────
        ("Prácticas de laboratorio física electromagnética (La Plata)","Ingeniería Agrícola","La Plata","Física Electromagnética","","La Plata (Usco) - Neiva (Universidad Surcolombiana) - La Plata (Usco)","TIQUETES",None,118000.0,0.7,205016.0,"Arbey Sánchez Rodríguez"),
        ("Prácticas de laboratorio física mecánica (La Plata)","Ingeniería Agrícola","La Plata","Física Mecánica","","La Plata (Usco) - Neiva (Universidad Surcolombiana) - La Plata (Usco)","TIQUETES",None,118000.0,0.7,205016.0,"Carlos Alberto Paloma"),
        ("Laboratorio de mecánica de fluidos (La Plata)","Ingeniería Agrícola","La Plata","Mecánica de fluidos","TP","La Plata (Usco) - Neiva (Universidad Surcolombiana, laboratorio mecánica de fluidos) - La Plata (Usco)","TIQUETES",None,118000.0,0.7,205016.0,"Javier Eduardo Bonilla Perdomo"),
        ("Laboratorio de calidad de aguas (La Plata)","Ingeniería Agrícola","La Plata","Calidad de aguas","TP","La Plata (Usco) - Neiva (Universidad Surcolombiana, laboratorio calidad de aguas) - La Plata (Usco)","TIQUETES",None,118000.0,0.7,205016.0,"Yanet Caridad Apin Campos"),
        ("Laboratorio de física mecánica (La Plata)","Ingeniería Agrícola","La Plata","Física mecánica","","La Plata (Usco) - Neiva (Universidad Surcolombiana) - La Plata (Usco)","TIQUETES",None,118000.0,0.7,205016.0,"Carlos Alberto Paloma"),
        ("Compactación - consolidación y capacidad portante del suelo (Garzón)","Ingeniería Agrícola","Garzón","Mecánica de suelos","TP","Garzón (Usco) - Neiva (Universidad Surcolombiana) - Garzón (Usco)","TIQUETES",None,100000.0,0.7,205016.0,"Oscar Fabián Losada Gómez"),
        ("Laboratorio de mecánica de fluidos (Garzón)","Ingeniería Agrícola","Garzón","Mecánica de fluidos","TP","Garzón (Usco) - Neiva (Universidad Surcolombiana, laboratorio mecánica de fluidos) - Garzón (Usco)","TIQUETES",None,100000.0,0.7,205016.0,"Jhon Jairo Vargas Hoyos"),
        ("Laboratorio de mecánica de fluidos (Pitalito)","Ingeniería Agrícola","Pitalito","Mecánica de fluidos","TP","Pitalito (Usco) - Neiva (Universidad Surcolombiana, laboratorio mecánica de fluidos) - Pitalito (Usco)","TIQUETES",None,140000.0,0.7,205016.0,"Edinson Mujica Rodríguez"),
        ("Contextualización en análisis de laboratorio de suelos y gestión en cultivos cálidos","Ingeniería Agrícola","Pitalito","Suelos","TP","Pitalito (Usco) - Neiva (Universidad Surcolombiana, laboratorios de suelos) - Pitalito (Usco)","TIQUETES",None,140000.0,0.7,205016.0,"Yony Arley Chavez Parra"),
        # ── Ingeniería Agroindustrial ──────────────────────────────────────────
        ("Visita Casa Grajales","Ingeniería Agroindustrial","Neiva","Enología","TP","Neiva (Usco) - La Unión Valle (casa Grajales - Planta Fabrica Vinícola - Museo de la Uva y el Vino) - Neiva (Usco)","INTERNO",None,None,2.5,205016.0,"Eduardo Pastrana Bonilla"),
        ("Control de calidad en la Agroindustrial del café y cacao","Ingeniería Agroindustrial","Neiva","Control de calidad instrumental en alimentos","TP","Neiva (Usco) - Piendamo, Cauca (Tenicafe) - La venta de Cajibio Cauca - Universidad del Cauca - Las Guacas Popayan, Cauca (Cubiotec y Agrosavia) - Neiva (Usco)","EXTERNO",3330000.0,None,2.5,205016.0,"Andrés Felipe Bahamon Monje"),
        ("Visita a centros de investigación agrícola de Colombia","Ingeniería Agroindustrial","Neiva","Sistemas productivos agrícolas","TP","Neiva (Usco) - Agrosavia (Natagaima) - Centro Nacional de Investigaciones de Café - Caldas Chinchana - Buencafe Liofilizado de Colombia - Universidad del Tolima, Ibagué - Neiva (Usco)","INTERNO",None,None,2.5,205016.0,"Andrés Felipe Bahamon Monje"),
        ("Practica integral: Sistemas de producción pecuaria","Ingeniería Agroindustrial","Neiva","Producción pecuaria y acuícola","TP","Neiva (Usco) - Centro de Formación Angostura, Campoalegre - Piscícola Marpez SAS Botero - Neiva (Usco)","EXTERNO",1210000.0,None,1.5,205016.0,"Beatriz Elena Zapata Berruecos"),
        ("Producción y manejo pos cosecha de flores","Ingeniería Agroindustrial","Neiva","Industrialización de productos no alimentarios","TP","Neiva (Usco) - Facatitva, Pardo Carrizosa Navas S.A.S - Neiva (Usco)","EXTERNO",6460000.0,None,1.5,205016.0,"Laura Nathalia Ochoa Ospitia"),
        ("Procesamiento y almacenamiento de arroz","Ingeniería Agroindustrial","Neiva","Procesos industriales granos y semillas","TP","Neiva (Usco) - Fedearroz - Espinal - Neiva (Usco)","EXTERNO",1520000.0,None,1.0,578425.0,"Jaime Daniel Bustos Vanegas"),
        ("Procesamiento de café y cacao","Ingeniería Agroindustrial","Neiva","Tecnología de café y cacao","","Neiva (Usco) - Sena Angostura Campoalegre - Neiva (Usco)","EXTERNO",1110000.0,None,1.0,30000.0,"Jaime Daniel Bustos Vanegas"),
        ("Sistemas de empaques para alimentos","Ingeniería Agroindustrial","Neiva","Almacenamiento de productos biológicos","TP","Neiva (Usco) - Medellín - Neiva (Usco)","TIQUETES",None,320000.0,2.5,578425.0,"Jaime Daniel Bustos Vanegas"),
        ("Reconocimiento del proceso de transformación de la tilapia e identificar etapas de procesamiento de reses","Ingeniería Agroindustrial","Neiva","Procesos industriales cárnicos","TP","Neiva (Usco) - Hobo (Piscícola Botero) - Rivera (Ceagrodex) - Neiva (Usco)","INTERNO",None,None,0.7,205016.0,"Andrea Elinor Lara Sánchez"),
        ("Practica integral: Manejo post-cosecha de pescado (externo)","Ingeniería Agroindustrial","Neiva","Procesamiento transformación e inocuidad de productos piscícolas","","Neiva (Usco) - Palermo (Harinas Cárnicas del Huila S.A.S) - Hobo Piscícola Botero - Neiva (Usco)","EXTERNO",1610000.0,None,0.7,205016.0,"Angélica María Otero Paternina"),
        ("Practica integral: Manejo post-cosecha de pescado (interno)","Ingeniería Agroindustrial","Neiva","Procesamiento transformación e inocuidad de productos piscícolas","","Neiva (Usco) - Palermo (Harinas Cárnicas del Huila S.A.S) - Hobo Piscícola Botero - Neiva (Usco)","INTERNO",None,None,0.7,205016.0,"Angélica María Otero Paternina"),
        ("Reconocimiento de los procesos productivos, diseños y ubicación de la planta","Ingeniería Agroindustrial","Neiva","Diseño de plantas agroindustriales","T","Neiva (Usco) - (Italcol Planta Palermo) - Neiva (Usco)","EXTERNO",1410000.0,None,1.0,30000.0,"Natalia Puentes"),
        ("Laboratorios sistemas de producción acuícola","Ingeniería Agroindustrial","Neiva","Producción pecuaria y acuícola","","Neiva (Usco) - Palermo (Granja Experimental) - Neiva (Usco)","INTERNO",None,None,1.0,30000.0,"Beatriz Elena Zapata Berruecos"),
        # ── Ingeniería Civil ────────────────────────────────────────────────────
        ("Caracterización Geo ambiental del Territorio - Valle Superior del Magdalena (interno)","Ingeniería Civil","Neiva","Geología para ingenieros","TP","Neiva (Usco) - Betania - Hobo - La Plata - Inza - San Andrés de Pisimbala - Timana - Garzón - Pitalito - Altamira - Gigante - Neiva (Usco)","INTERNO",None,None,2.5,205016.0,"Isauro Trujillo Vásquez"),
        ("Caracterización Geo ambiental del Territorio - Valle Superior del Magdalena (externo)","Ingeniería Civil","Neiva","Geología para ingenieros","TP","Neiva (Usco) - Betania - Hobo - La Plata - Inza - San Andrés de Pisimbala - Timana - Garzón - Pitalito - Altamira - Gigante - Neiva (Usco)","EXTERNO",3230000.0,None,2.5,205016.0,"Isauro Trujillo Vásquez"),
        ("Medición de Caudales","Ingeniería Civil","Neiva","Hidrología","TP","Neiva (Usco) - Yaguará - Neiva (Usco)","TIQUETES",None,80000.0,0.7,205016.0,"Jaime Izquierdo Bautista"),
        ("Estructuras hidráulicas de una presa y de un distrito de riego","Ingeniería Civil","Neiva","Estructuras hidráulicas","TP","Neiva (Usco) - Yaguará - Neiva (Usco)","TIQUETES",None,80000.0,0.7,205016.0,"Jaime Izquierdo Bautista"),
        ("Practica para identificación y evaluación de estructuras hidráulicas en canales abiertos (Cátedra)","Ingeniería Civil","Neiva","Hidráulica","TP","Neiva (Usco) - Palermo distrito de riego el Juncal - Campoalegre Aso ovejeras vía Sena la angostura - Neiva (Usco)","EXTERNO",1870000.0,None,1.5,205016.0,"Mario German Trujillo Vela"),
        ("Practica para identificación y evaluación de estructuras hidráulicas en canales abiertos (Planta)","Ingeniería Civil","Neiva","Hidráulica","TP","Neiva (Usco) - Palermo distrito de riego el Juncal - Campoalegre Aso ovejeras vía Sena la angostura - Neiva (Usco)","EXTERNO",1870000.0,None,1.5,205016.0,"Nadia Brigitte Sanabria Méndez"),
        ("Practica para identificación de estación de niveles y medición de caudales (Civil)","Ingeniería Civil","Neiva","Hidrología","TP","Neiva (Usco) - Bocatoma del acueducto del Guayabo - Granja Experimental USCO - Palermo - Neiva (Usco)","EXTERNO",1460000.0,None,1.0,30000.0,"Mario German Trujillo Vela"),
        # ── Ingeniería de Petróleos ─────────────────────────────────────────────
        ("Reconocimiento geológico estratigrafía yacimientos carbonatados Valle Superior del Magdalena","Ingeniería de Petróleos","Neiva","Sedimentología y geología del petróleo","TP","Neiva (Usco) - Mariquita - Armero - Guaduas - Villeta - La Vega - Neiva (Usco)","EXTERNO",4000000.0,None,3.5,578425.0,"Ingrid Natalia Muñoz Quijano"),
        ("Reconocimiento geológico estructural introducción a la geotermia de la cordillera central","Ingeniería de Petróleos","Neiva","Geología estructural e introducción a la geotermia","TP","Neiva (Usco) - Manizales - Villamaría - La Enea - Mariquita - Neiva (Usco)","INTERNO",None,None,3.5,578425.0,"Ingrid Natalia Muñoz Quijano"),
        ("Manejo de cartografías aéreas y toma de datos con GPS (IGAC Bogotá)","Ingeniería de Petróleos","Neiva","Sistemas de información geográfica","TP","Neiva (Usco) - Bogotá (IGAC, cra 30 calle 50) - Neiva (Usco)","INTERNO",None,None,2.5,699661.0,"Jorge Orlando Mayorga Bautista"),
        ("Reconocimiento Geológico de la estratigrafía de las subcuencas de Prado y Girardot - Geología 1","Ingeniería de Petróleos","Neiva","Geología General I","TP","Neiva (Usco) - Girardot (parque central) - Saldaña - Km 10 vía Dolores - Barzalosa - Ibagué - Payandé - Neiva (Usco)","EXTERNO",3640000.0,None,3.5,699661.0,"Roberto Vargas Cuervo"),
        ("Reconocimiento Geológico de la estratigrafía de las subcuencas de Prado y Girardot - Geología 2","Ingeniería de Petróleos","Neiva","Geología General II","TP","Neiva (Usco) - Girardot (parque central) - Saldaña - Km 10 vía Dolores - Barzalosa - Ibagué - Payandé - Neiva (Usco)","EXTERNO",3640000.0,None,3.5,699661.0,"Roberto Vargas Cuervo"),
        # ── Ingeniería de Software ─────────────────────────────────────────────
        ("Práctica temprana en la industria de software - Algoritmia","Ingeniería de Software","Neiva","Algoritmia I","TP","Neiva (Usco) - Empresas de Bogotá - Neiva (Usco)","TIQUETES",None,210000.0,1.5,329834.0,"Jorge Eliecer Martínez Gaitán"),
        ("Práctica temprana en la industria de software - Bases de Datos","Ingeniería de Software","Neiva","Base de datos","TP","Neiva (Usco) - Empresas de Bogotá - Neiva (Usco)","TIQUETES",None,210000.0,1.5,205016.0,"Euripides Triana Tucuma"),
    ]

    try:
        with engine.connect() as conn:
            try:
                count = conn.execute(text("SELECT COUNT(*) FROM practica_plantillas")).scalar()
                if count and count > 0:
                    return
            except Exception:
                return
            for (nombre, programa, sede, asignatura, caracter, ruta, tipo_bus,
                 costo_ext, costo_tiq, viat_dias, viat_val, profesor) in _PLANTILLAS:
                conn.execute(text(
                    "INSERT INTO practica_plantillas "
                    "(nombre,programa,sede,asignatura,caracter_curso,ruta_texto,tipo_bus,"
                    "costo_bus_externo,costo_tiquetes,viat_docente_dias,viat_docente_valor_dia,profesor) "
                    "VALUES (:n,:p,:s,:a,:c,:r,:t,:ce,:ct,:vd,:vv,:pr)"
                ), {"n": nombre, "p": programa, "s": sede, "a": asignatura,
                    "c": caracter, "r": ruta, "t": tipo_bus,
                    "ce": costo_ext, "ct": costo_tiq, "vd": viat_dias, "vv": viat_val,
                    "pr": profesor})
            conn.commit()
    except Exception:
        pass


def _seed_precios_combustible():
    """Precios de referencia SICOM – Huila (vigentes enero 2026)."""
    _PRECIOS = [
        ("gasolina_corriente", 15_500.00, "HUILA"),
        ("gasolina_extra",     18_200.00, "HUILA"),
        ("diesel",             13_800.00, "HUILA"),
    ]
    try:
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM precios_combustible")).scalar()
            if count and count > 0:
                return
            for tipo, precio, dpto in _PRECIOS:
                conn.execute(text(
                    "INSERT INTO precios_combustible (tipo, precio_litro, departamento, fecha_vigencia, fuente) "
                    "VALUES (:t, :p, :d, '2026-01-01', 'SICOM')"
                ), {"t": tipo, "p": precio, "d": dpto})
            conn.commit()
    except Exception:
        pass


def _seed_peajes_nacionales():
    """Peajes INVIAS/ANI en corredores usados por la USCO (tarifas 2025)."""
    # (nombre, departamento, municipio, corredor, tarifa_cat1, tarifa_cat2, tarifa_cat3, administrado_por)
    _PEAJES = [
        ("Peaje Neiva - Bogotá (La Mona)",    "HUILA",  "Rivera",      "Neiva-Bogotá",      6_700, 10_700, 14_500, "INVIAS"),
        ("Peaje La Plata (Ruta 45A)",          "HUILA",  "La Plata",    "Neiva-La Plata",    5_900,  9_500, 12_800, "INVIAS"),
        ("Peaje Altamira",                     "HUILA",  "Altamira",    "Neiva-Pitalito",    6_200, 10_000, 13_500, "INVIAS"),
        ("Peaje Gigante",                      "HUILA",  "Gigante",     "Neiva-Garzón",      5_600,  9_000, 12_200, "INVIAS"),
        ("Peaje Espinal",                      "TOLIMA", "Espinal",     "Bogotá-Cali",       8_100, 13_000, 17_600, "ANI Concesión CCFC"),
        ("Peaje Palmira (Variante Sur)",       "VALLE",  "Palmira",     "Cali-Armenia",      7_300, 11_700, 15_800, "ANI Concesión"),
        ("Peaje Campoalegre (Ruta 45)",        "HUILA",  "Campoalegre", "Neiva-Bogotá",      6_000,  9_700, 13_100, "INVIAS"),
        ("Peaje Aipe",                         "HUILA",  "Aipe",        "Neiva-Bogotá",      6_000,  9_700, 13_100, "INVIAS"),
        ("Peaje La Victoria (Ruta 45)",        "HUILA",  "Hobo",        "Neiva-Bogotá",      6_000,  9_700, 13_100, "INVIAS"),
        ("Peaje Suaza (Ruta 45)",              "HUILA",  "Suaza",       "Pitalito-Neiva",    5_900,  9_500, 12_800, "INVIAS"),
    ]
    try:
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM peajes_nacionales")).scalar()
            if count and count > 0:
                return
            for nombre, dpto, mpio, corredor, t1, t2, t3, admin in _PEAJES:
                conn.execute(text(
                    "INSERT INTO peajes_nacionales "
                    "(nombre, departamento, municipio, corredor, tarifa_cat1, tarifa_cat2, tarifa_cat3, administrado_por, vigente_desde, is_active) "
                    "VALUES (:n, :d, :m, :c, :t1, :t2, :t3, :a, '2025-01-01', true)"
                ), {"n": nombre, "d": dpto, "m": mpio, "c": corredor,
                    "t1": t1, "t2": t2, "t3": t3, "a": admin})
            conn.commit()
    except Exception:
        pass


def _seed_sistema_config():
    """Inserta la fila singleton (id=1) si no existe aún."""
    with engine.connect() as conn:
        exists = conn.execute(text("SELECT id FROM sistema_config WHERE id = 1")).fetchone()
        if not exists:
            conn.execute(text("INSERT INTO sistema_config (id, testing_mode) VALUES (1, false)"))
            conn.commit()


def es_modo_prueba(db) -> bool:
    """Devuelve True si el modo de prueba está activo (bypasa restricciones de tiempo/quórum)."""
    try:
        row = db.execute(text("SELECT testing_mode FROM sistema_config WHERE id = 1")).fetchone()
        return bool(row[0]) if row else False
    except Exception:
        return False

def _seed_monitoria_plantillas():
    """Genera plantillas de monitorias por asignatura (Acuerdo 012/2023 Art. 3)."""
    import unicodedata

    def _strip(s):
        return "".join(
            c for c in unicodedata.normalize("NFD", s.lower())
            if unicodedata.category(c) != "Mn"
        )

    _LAB = {"laboratorio", "fisica", "mecanica", "hidraulica", "fluidos", "suelos",
            "calidad de aguas", "geologia", "sedimentologia"}
    _TIC = {"algoritmia", "base de datos", "informatica", "computacion",
            "software", "programacion", "sig", "informacion geografica"}

    def _tipo(nombre):
        n = _strip(nombre)
        if any(k in n for k in _TIC):
            return "tic"
        if any(k in n for k in _LAB):
            return "laboratorios"
        return "academica_cursos"

    def _horas(tipo):
        return (6, 96) if tipo in ("laboratorios", "tic") else (8, 128)

    def _desc(tipo, nombre):
        if tipo == "laboratorios":
            return ("Preparacion y supervision de practicas de laboratorio en " + nombre +
                    ". Apoyo en manejo de equipos e instrumentos. Elaboracion de guias. "
                    "Registro de asistencia y seguimiento de resultados experimentales.")
        if tipo == "tic":
            return ("Apoyo en el uso de herramientas TIC aplicadas a " + nombre +
                    ". Acompanamiento en salas de informatica. Soporte tecnico basico. "
                    "Elaboracion de tutoriales y material digital de apoyo.")
        return ("Apoyo en clases presenciales de " + nombre +
                ". Atencion de consultas y dudas academicas de estudiantes. "
                "Elaboracion de material didactico, guias de estudio y talleres. "
                "Seguimiento academico y registro de asistencia.")

    # SQL con CAST explicito para columna ENUM en PostgreSQL
    _SQL = (
        "INSERT INTO monitoria_plantillas "
        "(nombre_sugerido,programa,asignatura_id,asignatura_nombre,tipo_monitoria,"
        "descripcion_actividades,horas_semana,horas_semestre,promedio_minimo,"
        "creditos_minimo_pct,num_monitores_sugerido,semestre_asignatura,creditos_asignatura,caracter_curso) "
        "VALUES (:ns,:p,:ai,:an,CAST(:tm AS tipomonitoriaenum),:da,:hs,:hse,:pm,:cm,:nm,:sa,:ca,:cc)"
        if not _IS_SQLITE else
        "INSERT INTO monitoria_plantillas "
        "(nombre_sugerido,programa,asignatura_id,asignatura_nombre,tipo_monitoria,"
        "descripcion_actividades,horas_semana,horas_semestre,promedio_minimo,"
        "creditos_minimo_pct,num_monitores_sugerido,semestre_asignatura,creditos_asignatura,caracter_curso) "
        "VALUES (:ns,:p,:ai,:an,:tm,:da,:hs,:hse,:pm,:cm,:nm,:sa,:ca,:cc)"
    )

    try:
        with engine.connect() as conn:
            try:
                count = conn.execute(text("SELECT COUNT(*) FROM monitoria_plantillas")).scalar()
                if count and count > 0:
                    return
            except Exception:
                return
            rows = conn.execute(text(
                "SELECT id, nombre, programa, semestre, creditos, caracter_curso "
                "FROM asignaturas WHERE is_active = true"
            )).fetchall()
            if not rows:
                return
            for row in rows:
                asig_id, nombre, programa, semestre, creditos, caracter = row
                caracter = caracter or "teorico"
                tipo = _tipo(nombre)
                hs, hse = _horas(tipo)
                conn.execute(text(_SQL), {
                    "ns": "Monitoria " + nombre, "p": programa, "ai": asig_id,
                    "an": nombre, "tm": tipo, "da": _desc(tipo, nombre),
                    "hs": hs, "hse": hse, "pm": 3.50, "cm": 30.00, "nm": 1,
                    "sa": semestre, "ca": creditos, "cc": caracter,
                })
            conn.commit()
    except Exception:
        pass

