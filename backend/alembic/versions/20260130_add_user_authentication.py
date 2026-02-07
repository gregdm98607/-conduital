"""Add user authentication

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-30

Adds User table and user_id foreign keys to all user-owned entities.
Part of ROADMAP-009: Shared Authentication Architecture.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(1000), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("google_refresh_token", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("login_count", sa.Integer(), nullable=False, server_default="0"),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes on users table
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    # Add user_id to projects table using batch mode for SQLite compatibility
    with op.batch_alter_table("projects") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_projects_user_id", ["user_id"])
        batch_op.create_foreign_key(
            "fk_projects_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Add user_id to areas table using batch mode for SQLite compatibility
    with op.batch_alter_table("areas") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_areas_user_id", ["user_id"])
        batch_op.create_foreign_key(
            "fk_areas_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Add user_id to goals table using batch mode for SQLite compatibility
    with op.batch_alter_table("goals") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_goals_user_id", ["user_id"])
        batch_op.create_foreign_key(
            "fk_goals_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Add user_id to visions table using batch mode for SQLite compatibility
    with op.batch_alter_table("visions") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_visions_user_id", ["user_id"])
        batch_op.create_foreign_key(
            "fk_visions_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )

    # Add user_id to inbox table using batch mode for SQLite compatibility
    with op.batch_alter_table("inbox") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_inbox_user_id", ["user_id"])
        batch_op.create_foreign_key(
            "fk_inbox_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    # Remove foreign keys and user_id columns (reverse order) using batch mode for SQLite

    # inbox
    with op.batch_alter_table("inbox") as batch_op:
        batch_op.drop_constraint("fk_inbox_user_id", type_="foreignkey")
        batch_op.drop_index("ix_inbox_user_id")
        batch_op.drop_column("user_id")

    # visions
    with op.batch_alter_table("visions") as batch_op:
        batch_op.drop_constraint("fk_visions_user_id", type_="foreignkey")
        batch_op.drop_index("ix_visions_user_id")
        batch_op.drop_column("user_id")

    # goals
    with op.batch_alter_table("goals") as batch_op:
        batch_op.drop_constraint("fk_goals_user_id", type_="foreignkey")
        batch_op.drop_index("ix_goals_user_id")
        batch_op.drop_column("user_id")

    # areas
    with op.batch_alter_table("areas") as batch_op:
        batch_op.drop_constraint("fk_areas_user_id", type_="foreignkey")
        batch_op.drop_index("ix_areas_user_id")
        batch_op.drop_column("user_id")

    # projects
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint("fk_projects_user_id", type_="foreignkey")
        batch_op.drop_index("ix_projects_user_id")
        batch_op.drop_column("user_id")

    # Drop users table and indexes
    op.drop_index("ix_users_google_id", "users")
    op.drop_index("ix_users_email", "users")
    op.drop_table("users")
