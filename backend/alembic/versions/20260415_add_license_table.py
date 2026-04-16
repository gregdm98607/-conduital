"""Add license table for feature gating

Revision ID: 016_add_license_table
Revises: 015_add_soft_delete
Create Date: 2026-04-15

Adds the licenses table to support commercial tier management:
- Reverse trial (14-day full access on first launch)
- Tier-based module enforcement (free/gtd/full)
- Stripe purchase tracking
"""

from typing import Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers
revision: str = "016_add_license_table"
down_revision: Union[str, None] = "015_add_soft_delete"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "licenses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("tier", sa.String(50), nullable=False, server_default="full"),
        sa.Column("trial_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True, unique=True),
        sa.Column("purchase_id", sa.String(255), nullable=True, unique=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_licenses_user_id", "licenses", ["user_id"])
    op.create_index("ix_licenses_stripe_customer_id", "licenses", ["stripe_customer_id"])


def downgrade() -> None:
    op.drop_index("ix_licenses_stripe_customer_id")
    op.drop_index("ix_licenses_user_id")
    op.drop_table("licenses")
