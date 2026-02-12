"""Add review_frequency to projects

Revision ID: 013_add_review_frequency
Revises: 012_weekly_review_completion
Create Date: 2026-02-11

Adds review_frequency field to projects table (daily/weekly/monthly).
Projects now use frequency-based review scheduling like areas,
instead of manually-set next_review_date.
"""

from datetime import date, timedelta
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "013_add_review_frequency"
down_revision: Union[str, None] = "012_weekly_review_completion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add review_frequency column with default 'weekly'
    op.add_column(
        "projects",
        sa.Column(
            "review_frequency",
            sa.String(20),
            nullable=False,
            server_default="weekly",
        ),
    )

    # Backfill: for projects with last_reviewed_at but no next_review_date,
    # set next_review_date = last_reviewed_at + 7 days (weekly default)
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE projects
            SET next_review_date = date(last_reviewed_at, '+7 days')
            WHERE last_reviewed_at IS NOT NULL
              AND next_review_date IS NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_column("projects", "review_frequency")
