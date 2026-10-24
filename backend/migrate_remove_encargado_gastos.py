"""Migración: elimina el rol 'encargado_gastos' del enum PostgreSQL y del modelo User.

Pasos:
1. Verifica que no haya usuarios activos con ese rol (los migra a admin si los hay).
2. Renombra el enum actual.
3. Crea un nuevo enum sin 'encargado_gastos'.
4. Altera la columna users.rol para usar el nuevo enum.
5. Elimina el enum viejo.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.db.database import engine


def run():
    with engine.connect() as conn:
        # 1. Migrar usuarios con rol encargado_gastos a admin
        result = conn.execute(text(
            "SELECT COUNT(*) FROM users WHERE rol = 'encargado_gastos'"
        ))
        count = result.scalar()
        if count and count > 0:
            conn.execute(text(
                "UPDATE users SET rol = 'admin' WHERE rol = 'encargado_gastos'"
            ))
            print(f"  → {count} usuario(s) migrado(s) de encargado_gastos → admin")

        # 2. Verificar si el valor ya fue eliminado
        result = conn.execute(text(
            "SELECT enumlabel FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = 'rolenum' AND e.enumlabel = 'encargado_gastos'"
        ))
        if not result.fetchone():
            print("✓ El valor 'encargado_gastos' ya no existe en el enum 'rolenum'.")
            return

        # 3. Renombrar enum existente
        conn.execute(text("ALTER TYPE rolenum RENAME TO rolenum_old"))

        # 4. Crear nuevo enum sin encargado_gastos
        conn.execute(text(
            "CREATE TYPE rolenum AS ENUM "
            "('estudiante', 'profesor', 'jefe_programa', 'decano', 'admin')"
        ))

        # 5. Migrar columna
        conn.execute(text(
            "ALTER TABLE users ALTER COLUMN rol TYPE rolenum "
            "USING rol::text::rolenum"
        ))

        # 6. Eliminar enum viejo
        conn.execute(text("DROP TYPE rolenum_old"))

        conn.commit()
        print("✓ Rol 'encargado_gastos' eliminado del enum PostgreSQL correctamente.")


if __name__ == "__main__":
    run()
