# НОВОЕ
"""add rides table

Revision ID: 0002_add_rides
Revises: 0001_initial
Create Date: 2025-11-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_add_rides'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # Создаем тип ride_status, если его ещё нет (в некоторых схемах это уже делалось)
    ride_status = sa.Enum(
        'pending', 'driver_assigned', 'driver_arrived', 'passenger_onboard',
        'in_progress', 'completed', 'cancelled', name='ride_status'
    )
    ride_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'rides',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('passenger_user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('driver_user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', ride_status, nullable=False, server_default='pending'),
        sa.Column('start_x', sa.Integer(), nullable=False),
        sa.Column('start_y', sa.Integer(), nullable=False),
        sa.Column('end_x', sa.Integer(), nullable=False),
        sa.Column('end_y', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
    )


def downgrade():
    op.drop_table('rides')
    ride_status = sa.Enum(name='ride_status')
    ride_status.drop(op.get_bind(), checkfirst=True)
