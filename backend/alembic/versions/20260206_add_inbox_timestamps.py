"""Add created_at and updated_at to inbox table

Revision ID: 009_inbox_timestamps
Revises: 008_area_health_archive
Create Date: 2026-02-06

Adds TimestampMixin columns (created_at, updated_at) to inbox table
for consistency with other models. Existing rows get current timestamp.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "009_inbox_timestamps"
down_revision: Union[str, None] = "008_area_health_archive"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("inbox") as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("inbox") as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
