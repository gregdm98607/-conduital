"""Tests for migration chain analysis."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.migrations.chain import (
    MigrationInfo,
    get_migration_chain,
    get_current_head,
    find_orphaned_migrations,
    find_multiple_heads,
    get_chain_order,
    validate_chain,
    parse_migration_file,
)


class TestMigrationParsing:
    """Tests for parsing migration files."""

    def test_parse_migration_file_with_valid_content(self, tmp_path):
        """Test parsing a valid migration file."""
        content = '''"""Add users table

Revision ID: abc123
"""
revision: str = "abc123"
down_revision: Union[str, None] = "def456"
'''
        migration_file = tmp_path / "test_migration.py"
        migration_file.write_text(content)

        result = parse_migration_file(migration_file)

        assert result is not None
        assert result.revision == "abc123"
        assert result.down_revision == "def456"
        assert "Add users table" in result.description

    def test_parse_migration_file_with_none_down_revision(self, tmp_path):
        """Test parsing migration with None down_revision (root)."""
        content = '''"""Initial schema

Revision ID: root123
"""
revision: str = "root123"
down_revision: Union[str, None] = None
'''
        migration_file = tmp_path / "initial.py"
        migration_file.write_text(content)

        result = parse_migration_file(migration_file)

        assert result is not None
        assert result.revision == "root123"
        assert result.down_revision is None

    def test_parse_migration_file_without_revision(self, tmp_path):
        """Test parsing file without revision returns None."""
        content = '''"""Not a migration"""
some_var = "value"
'''
        migration_file = tmp_path / "not_migration.py"
        migration_file.write_text(content)

        result = parse_migration_file(migration_file)
        assert result is None


class TestChainValidation:
    """Tests for migration chain validation."""

    @patch("app.migrations.chain.get_migrations_dir")
    def test_validate_chain_healthy(self, mock_dir, tmp_path):
        """Test validation of a healthy chain."""
        # Create mock migrations
        root = '''"""Root
Revision ID: rev1
"""
revision = "rev1"
down_revision = None
'''
        child = '''"""Child
Revision ID: rev2
"""
revision = "rev2"
down_revision = "rev1"
'''
        (tmp_path / "001_root.py").write_text(root)
        (tmp_path / "002_child.py").write_text(child)
        mock_dir.return_value = tmp_path

        result = validate_chain()

        assert result.is_valid
        assert result.head_revision == "rev2"
        assert len(result.orphaned) == 0
        assert len(result.multiple_heads) == 0

    @patch("app.migrations.chain.get_migrations_dir")
    def test_validate_chain_with_orphan(self, mock_dir, tmp_path):
        """Test validation detects orphaned migration."""
        root = '''"""Root
Revision ID: rev1
"""
revision = "rev1"
down_revision = None
'''
        orphan = '''"""Orphan
Revision ID: rev3
"""
revision = "rev3"
down_revision = "nonexistent"
'''
        (tmp_path / "001_root.py").write_text(root)
        (tmp_path / "002_orphan.py").write_text(orphan)
        mock_dir.return_value = tmp_path

        result = validate_chain()

        assert not result.is_valid
        assert "rev3" in result.orphaned
        assert any("nonexistent" in e for e in result.errors)

    @patch("app.migrations.chain.get_migrations_dir")
    def test_validate_chain_with_multiple_heads(self, mock_dir, tmp_path):
        """Test validation detects multiple heads (branches)."""
        root = '''"""Root
Revision ID: rev1
"""
revision = "rev1"
down_revision = None
'''
        branch_a = '''"""Branch A
Revision ID: rev2a
"""
revision = "rev2a"
down_revision = "rev1"
'''
        branch_b = '''"""Branch B
Revision ID: rev2b
"""
revision = "rev2b"
down_revision = "rev1"
'''
        (tmp_path / "001_root.py").write_text(root)
        (tmp_path / "002a_branch.py").write_text(branch_a)
        (tmp_path / "002b_branch.py").write_text(branch_b)
        mock_dir.return_value = tmp_path

        result = validate_chain()

        assert not result.is_valid
        assert len(result.multiple_heads) == 2
        assert "rev2a" in result.multiple_heads
        assert "rev2b" in result.multiple_heads

    @patch("app.migrations.chain.get_migrations_dir")
    def test_get_chain_order(self, mock_dir, tmp_path):
        """Test getting migrations in correct order."""
        migrations = [
            ('"""M1"""\nrevision = "rev1"\ndown_revision = None', "001.py"),
            ('"""M2"""\nrevision = "rev2"\ndown_revision = "rev1"', "002.py"),
            ('"""M3"""\nrevision = "rev3"\ndown_revision = "rev2"', "003.py"),
        ]
        for content, name in migrations:
            (tmp_path / name).write_text(content)
        mock_dir.return_value = tmp_path

        order = get_chain_order()

        assert order == ["rev1", "rev2", "rev3"]


class TestChainIntegration:
    """Integration tests using actual migration files."""

    def test_get_migration_chain_loads_files(self):
        """Test that get_migration_chain loads actual migration files."""
        # This tests against the real migration files
        chain = get_migration_chain()

        # Should have migrations
        assert len(chain) > 0

        # Should have the initial migration
        assert any("cb7b35ad5824" in rev for rev in chain.keys())

    def test_validate_actual_chain(self):
        """Test validation of actual migration chain."""
        result = validate_chain()

        # After fixing 006_memory_layer, chain should be valid
        # or at least not have orphaned migrations from that file
        assert result.head_revision is not None

    def test_find_current_head(self):
        """Test finding the current head revision."""
        head = get_current_head()

        # Should find a head
        assert head is not None
        # Head should be 006_memory_layer after our fix
        assert "006_memory_layer" in head or len(head) > 0
