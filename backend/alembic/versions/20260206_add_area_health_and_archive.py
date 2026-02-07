"""Add area health score and archival fields

Revision ID: 008_area_health_archive
Revises: 007_npm_fields
Create Date: 2026-02-06

Adds to areas table:
- health_score: Float (0.0-1.0) calculated from project momentum
- is_archived: Boolean for soft archive
- archived_at: DateTime for archive timestamp
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "008_area_health_archive"
down_revision: Union[str, None] = "007_npm_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("areas") as batch_op:
        batch_op.add_column(sa.Column("health_score", sa.Float(), nullable=False, server_default="0.0"))
        batch_op.add_column(sa.Column("is_archived", sa.Boolean(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("areas") as batch_op:
        batch_op.drop_column("archived_at")
        batch_op.drop_column("is_archived")
        batch_op.drop_column("health_score")
