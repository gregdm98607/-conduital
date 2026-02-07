"""Add memory layer tables

Revision ID: 006_memory_layer
Revises: (previous revision)
Create Date: 2026-02-02

Adds tables for the memory layer module:
- memory_namespaces: Namespace organization
- memory_objects: Core memory storage
- memory_index: Quick key routing
- prefetch_rules: Bundle prefetch configuration
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_memory_layer'
down_revision: Union[str, None] = "d4e5f6g7h8i9"  # Links to urgency_zone migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Memory Namespaces table
    op.create_table(
        'memory_namespaces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_namespace', sa.String(255), nullable=True),
        sa.Column('default_priority', sa.Integer(), default=50, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('idx_namespace_parent', 'memory_namespaces', ['parent_namespace'])

    # Memory Objects table
    op.create_table(
        'memory_objects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('object_id', sa.String(255), nullable=False),
        sa.Column('namespace', sa.String(255), sa.ForeignKey('memory_namespaces.name'), nullable=False),
        sa.Column('version', sa.String(20), default='1.0.0', nullable=False),
        sa.Column('priority', sa.Integer(), default=50, nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('checksum', sa.String(100), nullable=True),
        sa.Column('storage_type', sa.String(20), default='db', nullable=False),
        sa.Column('content', sa.JSON(), nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('priority >= 0 AND priority <= 100', name='check_priority_range'),
        sa.CheckConstraint("storage_type IN ('db', 'file')", name='check_storage_type'),
    )
    op.create_index('idx_memory_namespace', 'memory_objects', ['namespace'])
    op.create_index('idx_memory_priority', 'memory_objects', ['priority'])
    op.create_index('idx_memory_effective', 'memory_objects', ['effective_from', 'effective_to'])
    op.create_index('idx_memory_object_id', 'memory_objects', ['object_id'])
    op.create_index('idx_memory_user', 'memory_objects', ['user_id'])

    # Memory Index table (quick keys)
    op.create_table(
        'memory_index',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('target_type', sa.String(20), default='object', nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('target_path', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )

    # Prefetch Rules table
    op.create_table(
        'prefetch_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('trigger', sa.String(255), nullable=False),
        sa.Column('lookahead_minutes', sa.Integer(), default=120, nullable=False),
        sa.Column('bundle', sa.JSON(), nullable=False),
        sa.Column('false_prefetch_decay_minutes', sa.Integer(), default=30, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Seed default namespaces
    op.execute("""
        INSERT INTO memory_namespaces (name, description, default_priority)
        VALUES
            ('core', 'Core identity and preferences', 90),
            ('core.identity', 'User identity information', 92),
            ('core.preferences', 'User preferences and interaction style', 87),
            ('projects', 'Project-related memory', 70),
            ('knowledge', 'Knowledge domains and skills', 67),
            ('knowledge.domains', 'Areas of expertise', 67),
            ('workflows', 'Workflow and thread memory', 77),
            ('workflows.threads', 'Active conversation threads', 77),
            ('contexts', 'Contextual information', 82),
            ('system', 'System evolution and meta information', 62)
    """)


def downgrade() -> None:
    op.drop_table('prefetch_rules')
    op.drop_table('memory_index')
    op.drop_index('idx_memory_user', 'memory_objects')
    op.drop_index('idx_memory_object_id', 'memory_objects')
    op.drop_index('idx_memory_effective', 'memory_objects')
    op.drop_index('idx_memory_priority', 'memory_objects')
    op.drop_index('idx_memory_namespace', 'memory_objects')
    op.drop_table('memory_objects')
    op.drop_index('idx_namespace_parent', 'memory_namespaces')
    op.drop_table('memory_namespaces')
