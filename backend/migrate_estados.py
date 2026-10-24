"""
Migración: añade los nuevos valores al enum estadopracticaenum en PostgreSQL.
Ejecutar una sola vez: python migrate_estados.py
"""
import psycopg2

conn = psycopg2.connect(
    dbname="sipam_db", user="sipam_user", password="sipam_pass",
    host="localhost", port=5432,
)
conn.autocommit = True
cur = conn.cursor()

nuevos_valores = [
    ("aprobada_curriculo",   "solicitada"),       # jefe_programa aprueba → va al decano
    ("aprobada_facultad",    "aprobada_curriculo"), # decano avala → va al admin
]

for valor, _ in nuevos_valores:
    cur.execute(
        "SELECT 1 FROM pg_enum WHERE enumlabel=%s "
        "AND enumtypid=(SELECT oid FROM pg_type WHERE typname='estadopracticaenum')",
        (valor,),
    )
    if cur.fetchone():
        print(f"  Ya existe: {valor}")
    else:
        cur.execute(f"ALTER TYPE estadopracticaenum ADD VALUE '{valor}'")
        print(f"  Añadido: {valor}")

cur.close()
conn.close()
print("Migración completada.")
