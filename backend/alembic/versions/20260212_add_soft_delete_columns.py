"""Add deleted_at column to projects, tasks, areas for soft delete

Revision ID: 015_add_soft_delete
Revises: 014_add_ai_summary
Create Date: 2026-02-12

DEBT-007: Soft delete foundation — mark records as deleted instead of hard delete.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "015_add_soft_delete"
down_revision: Union[str, None] = "014_add_ai_summary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade() -> None:
    for table in ("projects", "tasks", "areas"):
        if not _column_exists(table, "deleted_at"):
            op.add_column(
                table,
                sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            )
            op.create_index(f"ix_{table}_deleted_at", table, ["deleted_at"])


def downgrade() -> None:
    for table in ("projects", "tasks", "areas"):
        if _column_exists(table, "deleted_at"):
            op.drop_index(f"ix_{table}_deleted_at", table_name=table)
            op.drop_column(table, "deleted_at")
