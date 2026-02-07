"""Add outcome_statement to projects

Revision ID: a1b2c3d4e5f6
Revises: 05cc64c204e2
Create Date: 2026-01-29

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "05cc64c204e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add outcome_statement column to projects table
    op.add_column(
        "projects",
        sa.Column("outcome_statement", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    # Remove outcome_statement column from projects table
    op.drop_column("projects", "outcome_statement")
