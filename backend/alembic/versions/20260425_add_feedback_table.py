"""Add feedback table for in-app feedback widget (F-001)

Revision ID: 017_add_feedback_table
Revises: 016_add_license_table
Create Date: 2026-04-25

Adds the feedback table to support the F-001 in-app feedback widget.
Feedback is stored locally in SQLite and is never sent to a remote server
without explicit user action. Fields:
  - category  : bug | feature | general
  - message   : free-text feedback body (max 2000 chars)
  - page      : window.location.pathname at submission time (for triage)
  - email     : optional user-provided reply-to address
  - app_version : version string captured at submission time
  - submitted_at : UTC timestamp
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = "017_add_feedback_table"
down_revision: Union[str, None] = "016_add_license_table"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("page", sa.String(200), nullable=True),
        sa.Column("email", sa.String(254), nullable=True),
        sa.Column("app_version", sa.String(20), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_feedback_category", "feedback", ["category"])
    op.create_index("ix_feedback_submitted_at", "feedback", ["submitted_at"])


def downgrade() -> None:
    op.drop_index("ix_feedback_submitted_at")
    op.drop_index("ix_feedback_category")
    op.drop_table("feedback")
