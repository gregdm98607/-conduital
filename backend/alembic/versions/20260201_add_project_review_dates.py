"""Add project review dates

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-01

Adds next_review_date and last_reviewed_at fields to projects table.
Part of BACKLOG-042: Project Review Date for GTD review compliance.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add next_review_date column to projects table
    op.add_column(
        "projects",
        sa.Column("next_review_date", sa.Date(), nullable=True),
    )
    op.create_index("ix_projects_next_review_date", "projects", ["next_review_date"])

    # Add last_reviewed_at column to projects table
    op.add_column(
        "projects",
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # Remove last_reviewed_at column from projects table
    op.drop_column("projects", "last_reviewed_at")

    # Remove next_review_date column and index from projects table
    op.drop_index("ix_projects_next_review_date", "projects")
    op.drop_column("projects", "next_review_date")
