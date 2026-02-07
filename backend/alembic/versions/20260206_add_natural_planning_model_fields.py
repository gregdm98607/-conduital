"""Add Natural Planning Model fields to projects

Revision ID: 007_npm_fields
Revises: 006_memory_layer
Create Date: 2026-02-06

Adds GTD Natural Planning Model fields to projects table:
- purpose: Why are we doing this? (NPM Step 1)
- vision_statement: What does wild success look like? (NPM Step 2)
- brainstorm_notes: Raw ideas, no judgment (NPM Step 3)
- organizing_notes: How do pieces fit together? (NPM Step 4)
- Next Actions (Step 5) already handled by tasks with is_next_action flag
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007_npm_fields"
down_revision: Union[str, None] = "006_memory_layer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(sa.Column("purpose", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("vision_statement", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("brainstorm_notes", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("organizing_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("organizing_notes")
        batch_op.drop_column("brainstorm_notes")
        batch_op.drop_column("vision_statement")
        batch_op.drop_column("purpose")
