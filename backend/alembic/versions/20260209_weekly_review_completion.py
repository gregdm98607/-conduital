"""Add weekly_review_completions table

Revision ID: 012_weekly_review_completion
Revises: 011_momentum_snapshots
Create Date: 2026-02-09

BETA-030: Weekly review completion tracking — persist when user completes review.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "012_weekly_review_completion"
down_revision: Union[str, None] = "011_momentum_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not _table_exists("weekly_review_completions"):
        op.create_table(
            "weekly_review_completions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=True,
            ),
            sa.Column(
                "completed_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("notes", sa.Text(), nullable=True),
        )
        op.create_index(
            "ix_weekly_review_completions_user_id",
            "weekly_review_completions",
            ["user_id"],
        )
        op.create_index(
            "ix_weekly_review_completions_completed_at",
            "weekly_review_completions",
            ["completed_at"],
        )


def downgrade() -> None:
    if _table_exists("weekly_review_completions"):
        op.drop_index(
            "ix_weekly_review_completions_completed_at",
            table_name="weekly_review_completions",
        )
        op.drop_index(
            "ix_weekly_review_completions_user_id",
            table_name="weekly_review_completions",
        )
        op.drop_table("weekly_review_completions")
