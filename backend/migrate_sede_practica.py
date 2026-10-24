"""Migración: agrega columna `sede` a la tabla practicas."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text
from app.db.database import SessionLocal, engine


def run():
    with engine.connect() as conn:
        # Verificar si la columna ya existe
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='practicas' AND column_name='sede'"
        ))
        if result.fetchone():
            print("✓ La columna 'sede' ya existe en practicas.")
            return
        conn.execute(text("ALTER TABLE practicas ADD COLUMN sede VARCHAR(100)"))
        conn.commit()
        print("✓ Columna 'sede' agregada exitosamente a practicas.")


if __name__ == "__main__":
    run()
