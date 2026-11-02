"""iot_tracking_points.device_timestamp → BigInteger

Los dispositivos/simulador envían epoch en milisegundos (~1.7e12), que
desborda INTEGER de PostgreSQL (máx ~2.1e9) y hacía fallar cada INSERT.

Revision ID: c7d8e9f0a1b2
Revises: a240a12162b2
Create Date: 2026-10-24 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'a240a12162b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "iot_tracking_points",
        "device_timestamp",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "iot_tracking_points",
        "device_timestamp",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
    )
