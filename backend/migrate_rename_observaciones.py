"""Migración: renombra observaciones_gastos → observaciones_admin en la tabla presupuestos
y elimina el rol 'encargado_gastos' del enum PostgreSQL si todavía existe.

Ejecutar UNA sola vez:
    python migrate_rename_observaciones.py
"""
import os
from sqlalchemy import text
from app.db.database import engine


def run():
    with engine.connect() as conn:

        # ── 1. Renombrar columna observaciones_gastos → observaciones_admin ────
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='presupuestos' AND column_name='observaciones_gastos'"
        ))
        if result.fetchone():
            conn.execute(text(
                "ALTER TABLE presupuestos "
                "RENAME COLUMN observaciones_gastos TO observaciones_admin"
            ))
            print("✓ Columna 'observaciones_gastos' renombrada a 'observaciones_admin'.")
        else:
            result2 = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='presupuestos' AND column_name='observaciones_admin'"
            ))
            if result2.fetchone():
                print("✓ La columna ya se llama 'observaciones_admin'. Sin cambios.")
            else:
                print("⚠  No se encontró ninguna de las columnas en 'presupuestos'.")

        # ── 2. Migrar y eliminar rol encargado_gastos del enum ─────────────────
        result = conn.execute(text(
            "SELECT enumlabel FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = 'rolenum' AND e.enumlabel = 'encargado_gastos'"
        ))
        if not result.fetchone():
            print("✓ El valor 'encargado_gastos' ya no existe en el enum 'rolenum'.")
        else:
            # Migrar usuarios con ese rol a admin
            upd = conn.execute(text(
                "UPDATE users SET rol = 'admin' WHERE rol = 'encargado_gastos'"
            ))
            if upd.rowcount:
                print(f"  → {upd.rowcount} usuario(s) migrado(s): encargado_gastos → admin")

            # Eliminar usuario GASTOS001 del seed si existe
            conn.execute(text(
                "DELETE FROM users WHERE codigo = 'GASTOS001'"
            ))
            print("  → Usuario GASTOS001 eliminado (si existía).")

            # Recrear el enum sin encargado_gastos
            conn.execute(text("ALTER TYPE rolenum RENAME TO rolenum_old"))
            conn.execute(text(
                "CREATE TYPE rolenum AS ENUM "
                "('admin','estudiante','profesor','jefe_programa','decano')"
            ))
            conn.execute(text(
                "ALTER TABLE users ALTER COLUMN rol TYPE rolenum "
                "USING rol::text::rolenum"
            ))
            conn.execute(text("DROP TYPE rolenum_old"))
            print("✓ Enum 'rolenum' actualizado — 'encargado_gastos' eliminado.")

        conn.commit()
        print("\n✅ Migración completada exitosamente.")


if __name__ == "__main__":
    run()
