"""Add previous_momentum_score column and momentum_snapshots table

Revision ID: 011_momentum_snapshots
Revises: 010_repair_user_id
Create Date: 2026-02-09

BETA-020: previous_momentum_score on projects (for trend/delta calculation)
BETA-021: momentum_snapshots table (for sparkline history)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "011_momentum_snapshots"
down_revision: Union[str, None] = "010_repair_user_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table using PRAGMA table_info."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns


def _table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    # BETA-020: Add previous_momentum_score to projects
    if not _column_exists("projects", "previous_momentum_score"):
        with op.batch_alter_table("projects") as batch_op:
            batch_op.add_column(
                sa.Column("previous_momentum_score", sa.Float(), nullable=True)
            )

    # BETA-021: Create momentum_snapshots table
    if not _table_exists("momentum_snapshots"):
        op.create_table(
            "momentum_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "project_id",
                sa.Integer(),
                sa.ForeignKey("projects.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("factors_json", sa.Text(), nullable=False),
            sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index(
            "ix_momentum_snapshots_project_id",
            "momentum_snapshots",
            ["project_id"],
        )
        op.create_index(
            "ix_momentum_snapshots_snapshot_at",
            "momentum_snapshots",
            ["snapshot_at"],
        )


def downgrade() -> None:
    # Drop momentum_snapshots table
    if _table_exists("momentum_snapshots"):
        op.drop_index("ix_momentum_snapshots_snapshot_at", table_name="momentum_snapshots")
        op.drop_index("ix_momentum_snapshots_project_id", table_name="momentum_snapshots")
        op.drop_table("momentum_snapshots")

    # Remove previous_momentum_score from projects
    if _column_exists("projects", "previous_momentum_score"):
        with op.batch_alter_table("projects") as batch_op:
            batch_op.drop_column("previous_momentum_score")
