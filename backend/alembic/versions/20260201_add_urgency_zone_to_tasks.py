"""Add urgency_zone to tasks

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-02-01

Adds urgency_zone field to tasks table for MYN (Manage Your Now)
urgency zone classification (BACKLOG-019).

Zones:
- critical_now: Must do today, non-negotiable commitments
- opportunity_now: Could do today, working inventory
- over_the_horizon: Not for today, future tasks
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add urgency_zone column to tasks table with default value
    op.add_column(
        "tasks",
        sa.Column(
            "urgency_zone",
            sa.String(30),
            nullable=True,
            server_default="opportunity_now",
        ),
    )
    # Create index for efficient filtering by urgency zone
    op.create_index(
        "ix_tasks_urgency_zone",
        "tasks",
        ["urgency_zone"],
    )


def downgrade() -> None:
    # Remove index and column
    op.drop_index("ix_tasks_urgency_zone", table_name="tasks")
    op.drop_column("tasks", "urgency_zone")
