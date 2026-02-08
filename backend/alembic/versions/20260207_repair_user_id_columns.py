"""Repair missing user_id columns on goals and visions

Revision ID: 010_repair_user_id
Revises: 009_inbox_timestamps
Create Date: 2026-02-07

The authentication migration (b2c3d4e5f6g7) was partially applied on some
databases: projects, areas, and inbox received user_id columns, but goals and
visions did not. This repair migration adds the missing columns only if they
don't already exist (safe to run on both fresh and partially-migrated databases).

Fixes BUG-022: /export/ai-context crashes with 'no such column: visions.user_id'
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "010_repair_user_id"
down_revision: Union[str, None] = "009_inbox_timestamps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using PRAGMA table_info."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns


def upgrade() -> None:
    # Add user_id to goals table only if missing (may already exist from auth migration)
    if not _column_exists("goals", "user_id"):
        with op.batch_alter_table("goals") as batch_op:
            batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
            batch_op.create_index("ix_goals_user_id", ["user_id"])
            batch_op.create_foreign_key(
                "fk_goals_user_id",
                "users",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )

    # Add user_id to visions table only if missing (may already exist from auth migration)
    if not _column_exists("visions", "user_id"):
        with op.batch_alter_table("visions") as batch_op:
            batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
            batch_op.create_index("ix_visions_user_id", ["user_id"])
            batch_op.create_foreign_key(
                "fk_visions_user_id",
                "users",
                ["user_id"],
                ["id"],
                ondelete="CASCADE",
            )


def downgrade() -> None:
    # Only drop if column exists (safe downgrade)
    if _column_exists("visions", "user_id"):
        with op.batch_alter_table("visions") as batch_op:
            batch_op.drop_constraint("fk_visions_user_id", type_="foreignkey")
            batch_op.drop_index("ix_visions_user_id")
            batch_op.drop_column("user_id")

    if _column_exists("goals", "user_id"):
        with op.batch_alter_table("goals") as batch_op:
            batch_op.drop_constraint("fk_goals_user_id", type_="foreignkey")
            batch_op.drop_index("ix_goals_user_id")
            batch_op.drop_column("user_id")
