"""refresh_tokens + iot_tracking_points

Revision ID: b1e2f3a4c5d6
Revises: 9d750e052479
Create Date: 2026-10-24 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1e2f3a4c5d6'
down_revision: Union[str, Sequence[str], None] = '9d750e052479'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('revoked', sa.Boolean(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index('ix_refresh_token_usuario', 'refresh_tokens', ['usuario_id'])
    op.create_index(op.f('ix_refresh_tokens_id'), 'refresh_tokens', ['id'])
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'])

    op.create_table(
        'iot_tracking_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(length=64), nullable=False),
        sa.Column('practice_id', sa.String(length=64), nullable=False),
        sa.Column('device_timestamp', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('speed_kmh', sa.Float(), nullable=True),
        sa.Column('course', sa.Float(), nullable=True),
        sa.Column('satellites', sa.Integer(), nullable=True),
        sa.Column('hdop', sa.Float(), nullable=True),
        sa.Column('datetime_gps', sa.String(length=64), nullable=True),
        sa.Column('battery_voltage', sa.Float(), nullable=True),
        sa.Column('wifi_rssi', sa.Integer(), nullable=True),
        sa.Column('uptime_seconds', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_iot_tracking_practice', 'iot_tracking_points', ['practice_id'])
    op.create_index('ix_iot_tracking_device', 'iot_tracking_points', ['device_id'])
    op.create_index(op.f('ix_iot_tracking_points_id'), 'iot_tracking_points', ['id'])


def downgrade() -> None:
    op.drop_index('ix_iot_tracking_device', table_name='iot_tracking_points')
    op.drop_index('ix_iot_tracking_practice', table_name='iot_tracking_points')
    op.drop_index(op.f('ix_iot_tracking_points_id'), table_name='iot_tracking_points')
    op.drop_table('iot_tracking_points')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_id'), table_name='refresh_tokens')
    op.drop_index('ix_refresh_token_usuario', table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
