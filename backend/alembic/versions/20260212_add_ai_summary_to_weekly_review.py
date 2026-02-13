"""Add ai_summary column to weekly_review_completions

Revision ID: 014_add_ai_summary
Revises: 013_add_review_frequency
Create Date: 2026-02-12

ROADMAP-007: Persist AI-generated weekly review summaries.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "014_add_ai_summary"
down_revision: Union[str, None] = "013_add_review_frequency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    conn = op.get_bind()
    result = conn.execute(sa.text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def upgrade() -> None:
    if not _column_exists("weekly_review_completions", "ai_summary"):
        op.add_column(
            "weekly_review_completions",
            sa.Column("ai_summary", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    if _column_exists("weekly_review_completions", "ai_summary"):
        op.drop_column("weekly_review_completions", "ai_summary")
