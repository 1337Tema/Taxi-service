"""Initial migration with unique index for active rides."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Таблица users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Таблица drivers
    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="offline"),
        sa.Column("x", sa.Integer, nullable=False, server_default="0"),
        sa.Column("y", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_online", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint("chk_driver_x_range", "drivers", "x >= 0 AND x < 100")
    op.create_check_constraint("chk_driver_y_range", "drivers", "y >= 0 AND y < 100")

    # Таблица rides
    op.create_table(
        "rides",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("passenger_user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("start_x", sa.Integer, nullable=False),
        sa.Column("start_y", sa.Integer, nullable=False),
        sa.Column("end_x", sa.Integer, nullable=False),
        sa.Column("end_y", sa.Integer, nullable=False),
        sa.Column("price", sa.Numeric(10,2), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
    )

    # Частичный уникальный индекс: один водитель не может иметь несколько активных поездок
    op.create_index(
        "uq_driver_active_ride",
        "rides",
        ["driver_user_id"],
        unique=True,
        postgresql_where=sa.text("status NOT IN ('completed', 'cancelled')")
    )


def downgrade() -> None:
    op.drop_index("uq_driver_active_ride", table_name="rides")
    op.drop_table("rides")
    op.drop_table("drivers")
    op.drop_table("users")
