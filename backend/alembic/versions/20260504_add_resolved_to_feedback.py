"""Add resolved column to feedback table (MON-011)

Revision ID: 018_add_resolved_to_feedback
Revises: 017_add_feedback_table
Create Date: 2026-05-04

Adds a boolean ``resolved`` flag to the feedback table so the in-app
admin view (Settings → Feedback) can triage submissions. Defaults to 0
for existing rows.
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = "018_add_resolved_to_feedback"
down_revision: Union[str, None] = "017_add_feedback_table"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "feedback",
        sa.Column(
            "resolved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_index("ix_feedback_resolved", "feedback", ["resolved"])


def downgrade() -> None:
    op.drop_index("ix_feedback_resolved")
    op.drop_column("feedback", "resolved")
