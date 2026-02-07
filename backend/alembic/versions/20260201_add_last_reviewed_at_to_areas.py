"""Add last_reviewed_at to areas

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-02-01

Adds last_reviewed_at timestamp field to areas table for tracking
when an area was last reviewed (BACKLOG-028).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_reviewed_at column to areas table
    op.add_column(
        "areas",
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    # Remove last_reviewed_at column from areas table
    op.drop_column("areas", "last_reviewed_at")
