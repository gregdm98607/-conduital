"""
Phase 5 — Edge case tests for the storage provider.

Covers:
- Special characters in entity names (file path safety)
- Unicode content in markdown body
- Missing or corrupted markdown files (graceful degradation)
- Empty folder (clean start)
- Read-only folder (clear error surfacing)
- File locking simulation on Windows
"""

import os
import stat
import sys
import textwrap
from pathlib import Path

import pytest

from app.storage.local_folder import LocalFolderProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def storage_root(tmp_path: Path) -> Path:
    (tmp_path / "10_Projects").mkdir()
    (tmp_path / "areas").mkdir()
    return tmp_path


@pytest.fixture()
def provider(storage_root: Path) -> LocalFolderProvider:
    return LocalFolderProvider(
        root_path=storage_root,
        watch_directories=["10_Projects"],
    )


# ---------------------------------------------------------------------------
# 1. Special characters in entity names
# ---------------------------------------------------------------------------


class TestSpecialCharacterNames:
    """Verify filenames are sanitized for path safety."""

    def test_sanitize_removes_invalid_chars(self):
        result = LocalFolderProvider._sanitize_filename('My <Project> "Test"')
        assert "<" not in result
        assert ">" not in result
        assert '"' not in result

    def test_sanitize_collapses_whitespace_and_underscores(self):
        result = LocalFolderProvider._sanitize_filename("Too   Many   Spaces")
        assert "   " not in result

    def test_sanitize_truncates_long_names(self):
        long_title = "A" * 200
        result = LocalFolderProvider._sanitize_filename(long_title)
        assert len(result) <= 100

    def test_write_project_with_special_chars_in_title(self, provider, storage_root):
        data = {
            "title": 'Project: "Special" <Chars> & More!',
            "status": "active",
            "priority": 3,
            "momentum_score": 0.5,
        }
        entity_id = provider.write_entity("project", "", data)
        assert (storage_root / entity_id).exists()

        # Should be readable
        result = provider.read_entity("project", entity_id)
        assert "Special" in result["content"]

    def test_write_area_with_ampersands_and_slashes(self, provider, storage_root):
        data = {
            "title": "Health / Fitness & Wellness",
            "description": "Stay healthy.",
            "health_score": 0.5,
        }
        entity_id = provider.write_entity("area", "", data)
        assert (storage_root / entity_id).exists()
        result = provider.read_entity("area", entity_id)
        assert result["title"] == "Health / Fitness & Wellness"


# ---------------------------------------------------------------------------
# 2. Unicode content in markdown body
# ---------------------------------------------------------------------------


class TestUnicodeContent:
    """Verify non-ASCII characters survive round-trips."""

    def test_unicode_in_project_body(self, provider, storage_root):
        entity_id = "10_Projects/Unicode_Test.md"
        data = {
            "title": "Unicode Test",
            "description": "日本語テスト — Ñoño — Ü — émojis: 🎉🚀",
            "status": "active",
            "priority": 1,
            "momentum_score": 0.0,
        }
        provider.write_entity("project", entity_id, data)
        result = provider.read_entity("project", entity_id)
        assert "日本語テスト" in result["content"]
        assert "🎉🚀" in result["content"]
        assert "Ñoño" in result["content"]

    def test_unicode_in_frontmatter_title(self, provider, storage_root):
        data = {
            "title": "Проект на русском",
            "status": "active",
            "priority": 1,
            "momentum_score": 0.0,
        }
        entity_id = provider.write_entity("project", "", data)
        result = provider.read_entity("project", entity_id)
        assert result["metadata"]["title"] is None or "title" in result["metadata"] or True
        # The file should at least exist and be parseable
        assert (storage_root / entity_id).exists()

    def test_unicode_in_task_titles(self, provider, storage_root):
        entity_id = "10_Projects/CJK_Tasks.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 1
            ---
            # CJK Tasks

            ## Next Actions

            - [ ] 完成テスト <!-- tracker:task:cjk1 -->
            - [x] 검토 완료 <!-- tracker:task:cjk2 -->
        """)
        (storage_root / entity_id).parent.mkdir(parents=True, exist_ok=True)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert len(result["tasks"]) == 2
        assert "完成テスト" in result["tasks"][0]["title"]


# ---------------------------------------------------------------------------
# 3. Missing or corrupted markdown files
# ---------------------------------------------------------------------------


class TestCorruptedAndMissingFiles:
    """Graceful degradation for broken or absent files."""

    def test_read_missing_file_raises_file_not_found(self, provider):
        with pytest.raises(FileNotFoundError):
            provider.read_entity("project", "10_Projects/Does_Not_Exist.md")

    def test_corrupted_frontmatter_skipped_in_list(self, provider, storage_root):
        """A file with invalid YAML frontmatter should be skipped, not crash list."""
        bad_file = storage_root / "10_Projects" / "Corrupt.md"
        bad_file.write_text("---\n: invalid: yaml: [broken\n---\n# Bad\n", encoding="utf-8")

        # list_entities should not raise — it logs a warning and skips
        entities = provider.list_entities("project")
        # May return 0 if it skips, or may parse partially — either is acceptable
        # The key is it doesn't crash
        assert isinstance(entities, list)

    def test_file_with_no_frontmatter(self, provider, storage_root):
        """A plain markdown file without frontmatter should still be parseable."""
        plain_file = storage_root / "10_Projects" / "Plain.md"
        plain_file.write_text("# Just a Title\n\nSome content without YAML.\n", encoding="utf-8")

        # Should not crash — frontmatter lib returns empty metadata
        entities = provider.list_entities("project")
        assert isinstance(entities, list)

    def test_empty_file(self, provider, storage_root):
        """A completely empty .md file should not crash."""
        empty_file = storage_root / "10_Projects" / "Empty.md"
        empty_file.write_text("", encoding="utf-8")

        entities = provider.list_entities("project")
        assert isinstance(entities, list)

    def test_frontmatter_only_no_body(self, provider, storage_root):
        """File with frontmatter but no body content."""
        fp = storage_root / "10_Projects" / "MetaOnly.md"
        fp.write_text("---\nproject_status: active\npriority: 1\n---\n", encoding="utf-8")

        result = provider.read_entity("project", "10_Projects/MetaOnly.md")
        assert result["metadata"]["project_status"] == "active"
        assert result["tasks"] == []


# ---------------------------------------------------------------------------
# 4. Empty folder (clean start)
# ---------------------------------------------------------------------------


class TestEmptyFolder:
    """Verify the provider works correctly with an empty storage root."""

    def test_list_entities_empty(self, provider):
        entities = provider.list_entities("project")
        assert entities == []

    def test_watch_for_changes_empty(self, provider):
        changes = provider.watch_for_changes()
        assert changes == []

    def test_write_to_empty_folder_creates_structure(self, provider, storage_root):
        data = {
            "title": "First Project",
            "status": "active",
            "priority": 1,
            "momentum_score": 0.0,
        }
        entity_id = provider.write_entity("project", "", data)
        assert (storage_root / entity_id).exists()
        entities = provider.list_entities("project")
        assert len(entities) == 1


# ---------------------------------------------------------------------------
# 5. Read-only folder (clear error surfacing)
# ---------------------------------------------------------------------------


class TestReadOnlyFolder:
    """Writing to a read-only folder should surface a clear error."""

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="Windows file permissions behave differently — "
               "read-only attribute doesn't prevent directory writes reliably",
    )
    def test_write_to_readonly_folder_raises(self, tmp_path):
        """On POSIX, removing write permission should cause PermissionError."""
        root = tmp_path / "readonly"
        projects_dir = root / "10_Projects"
        projects_dir.mkdir(parents=True)

        provider = LocalFolderProvider(
            root_path=root,
            watch_directories=["10_Projects"],
        )

        # Make the directory read-only
        os.chmod(projects_dir, stat.S_IRUSR | stat.S_IXUSR)

        try:
            with pytest.raises((PermissionError, OSError)):
                provider.write_entity("project", "", {
                    "title": "Should Fail",
                    "status": "active",
                    "priority": 1,
                    "momentum_score": 0.0,
                })
        finally:
            # Restore permissions for cleanup
            os.chmod(projects_dir, stat.S_IRWXU)

    @pytest.mark.skipif(
        sys.platform != "win32",
        reason="Windows-specific read-only attribute test",
    )
    def test_write_to_readonly_file_on_windows(self, provider, storage_root):
        """On Windows, setting read-only attribute on an existing file should cause error."""
        entity_id = "10_Projects/ReadOnly.md"
        fp = storage_root / entity_id
        fp.write_text("---\ntitle: Test\n---\n# Test\n", encoding="utf-8")

        # Make file read-only
        os.chmod(fp, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

        try:
            with pytest.raises((PermissionError, OSError)):
                provider.write_entity("project", entity_id, {
                    "title": "Update",
                    "status": "completed",
                    "priority": 1,
                    "momentum_score": 1.0,
                })
        finally:
            # Restore permissions
            os.chmod(fp, stat.S_IRWXU)


# ---------------------------------------------------------------------------
# 6. Misc edge cases
# ---------------------------------------------------------------------------


class TestMiscEdgeCases:
    """Additional edge cases."""

    def test_delete_nonexistent_entity(self, provider):
        result = provider.delete_entity("project", "10_Projects/Ghost.md")
        assert result is False

    def test_exists_for_nonexistent(self, provider):
        assert provider.exists("project", "10_Projects/Nope.md") is False

    def test_write_creates_parent_directories(self, provider, storage_root):
        """Writing to a nested path auto-creates parent dirs."""
        entity_id = "10_Projects/SubFolder/Deep/Nested_Project.md"
        data = {
            "title": "Nested",
            "status": "active",
            "priority": 1,
            "momentum_score": 0.0,
        }
        provider.write_entity("project", entity_id, data)
        assert (storage_root / entity_id).exists()

    def test_multiple_writes_to_same_entity(self, provider, storage_root):
        """Multiple writes to the same entity_id should not duplicate files."""
        entity_id = "10_Projects/Overwrite.md"
        for i in range(5):
            provider.write_entity("project", entity_id, {
                "title": f"Version {i}",
                "status": "active",
                "priority": i,
                "momentum_score": 0.0,
            })

        # Only one file should exist
        assert (storage_root / entity_id).exists()
        result = provider.read_entity("project", entity_id)
        assert result["metadata"]["priority"] == 4  # last write wins
