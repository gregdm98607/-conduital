"""
Tests for the StorageProvider abstraction and LocalFolderProvider.

Covers basic CRUD operations with markdown files, the watch_for_changes
snapshot-diff mechanism, and the factory function.
"""

import textwrap
from pathlib import Path

import pytest

from app.storage.base import Change, ChangeType, StorageProvider
from app.storage.local_folder import LocalFolderProvider
from app.storage.factory import create_storage_provider, reset_storage_provider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def storage_root(tmp_path: Path) -> Path:
    """Create a temp folder with the expected watch subdirectory."""
    projects_dir = tmp_path / "10_Projects"
    projects_dir.mkdir()
    return tmp_path


@pytest.fixture()
def provider(storage_root: Path) -> LocalFolderProvider:
    """A LocalFolderProvider pointed at the temp root."""
    return LocalFolderProvider(
        root_path=storage_root,
        watch_directories=["10_Projects"],
    )


@pytest.fixture()
def sample_md(storage_root: Path) -> str:
    """Write a sample markdown file and return its entity_id."""
    md_content = textwrap.dedent("""\
        ---
        tracker_id: 42
        project_status: active
        priority: 3
        momentum_score: 0.75
        ---
        # Test Project

        A project for testing.

        ## Next Actions

        - [ ] Write unit tests <!-- tracker:task:abc123 -->
        - [x] Set up CI <!-- tracker:task:def456 -->
    """)
    file_path = storage_root / "10_Projects" / "Test_Project.md"
    file_path.write_text(md_content, encoding="utf-8")
    return "10_Projects/Test_Project.md"


# ---------------------------------------------------------------------------
# ABC contract
# ---------------------------------------------------------------------------

class TestStorageProviderABC:
    def test_local_folder_is_subclass(self):
        assert issubclass(LocalFolderProvider, StorageProvider)

    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            StorageProvider()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class TestReadEntity:
    def test_read_existing_project(self, provider: LocalFolderProvider, sample_md: str):
        result = provider.read_entity("project", sample_md)

        assert result["entity_id"] == sample_md
        assert result["metadata"]["tracker_id"] == 42
        assert result["metadata"]["project_status"] == "active"
        assert result["metadata"]["priority"] == 3
        assert result["metadata"]["momentum_score"] == 0.75
        assert "file_hash" in result
        assert len(result["tasks"]) == 2

    def test_read_parses_tasks(self, provider: LocalFolderProvider, sample_md: str):
        result = provider.read_entity("project", sample_md)
        tasks = result["tasks"]

        unchecked = [t for t in tasks if not t["checked"]]
        checked = [t for t in tasks if t["checked"]]
        assert len(unchecked) == 1
        assert unchecked[0]["title"] == "Write unit tests"
        assert unchecked[0]["marker"] == "tracker:task:abc123"
        assert len(checked) == 1
        assert checked[0]["title"] == "Set up CI"

    def test_read_nonexistent_raises(self, provider: LocalFolderProvider):
        with pytest.raises(FileNotFoundError):
            provider.read_entity("project", "10_Projects/Nope.md")

    def test_read_unsupported_type_raises(self, provider: LocalFolderProvider):
        with pytest.raises(ValueError, match="Unsupported entity type"):
            provider.read_entity("unknown_type", "x.md")


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

class TestWriteEntity:
    def test_write_new_project(self, provider: LocalFolderProvider, storage_root: Path):
        data = {
            "title": "Brand New Project",
            "description": "Created via provider",
            "status": "active",
            "priority": 2,
            "momentum_score": 0.5,
            "tasks": [
                {"title": "First task", "checked": False, "marker": "tracker:task:t1"},
                {"title": "Done task", "checked": True, "marker": "tracker:task:t2"},
            ],
        }
        entity_id = provider.write_entity("project", "", data)

        # File was created
        assert (storage_root / entity_id).exists()

        # Round-trip: read it back
        result = provider.read_entity("project", entity_id)
        assert result["metadata"]["project_status"] == "active"
        assert result["metadata"]["priority"] == 2
        assert len(result["tasks"]) == 2

    def test_write_to_explicit_path(self, provider: LocalFolderProvider, storage_root: Path):
        entity_id = "10_Projects/Explicit.md"
        data = {"title": "Explicit Path", "status": "active", "priority": 5, "momentum_score": 0.0}
        returned_id = provider.write_entity("project", entity_id, data)

        assert returned_id == entity_id
        assert (storage_root / entity_id).exists()

    def test_write_preserves_existing_content(
        self, provider: LocalFolderProvider, sample_md: str, storage_root: Path
    ):
        """Updating metadata should not clobber the markdown body."""
        original = provider.read_entity("project", sample_md)
        original_content = original["content"]

        provider.write_entity("project", sample_md, {"status": "completed", "priority": 1, "momentum_score": 1.0})

        updated = provider.read_entity("project", sample_md)
        # Body text preserved
        assert "A project for testing." in updated["content"]
        # Metadata updated
        assert updated["metadata"]["project_status"] == "completed"

    def test_write_updates_task_checkboxes(
        self, provider: LocalFolderProvider, sample_md: str
    ):
        """Writing with tasks should flip checkbox states."""
        provider.write_entity("project", sample_md, {
            "tasks": [
                {"marker": "tracker:task:abc123", "checked": True},  # was unchecked
                {"marker": "tracker:task:def456", "checked": False},  # was checked
            ],
        })

        result = provider.read_entity("project", sample_md)
        task_map = {t["marker"]: t for t in result["tasks"]}
        assert task_map["tracker:task:abc123"]["checked"] is True
        assert task_map["tracker:task:def456"]["checked"] is False


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class TestDeleteEntity:
    def test_delete_existing(self, provider: LocalFolderProvider, sample_md: str, storage_root: Path):
        assert (storage_root / sample_md).exists()
        assert provider.delete_entity("project", sample_md) is True
        assert not (storage_root / sample_md).exists()

    def test_delete_nonexistent_returns_false(self, provider: LocalFolderProvider):
        assert provider.delete_entity("project", "10_Projects/Ghost.md") is False


# ---------------------------------------------------------------------------
# Exists / List
# ---------------------------------------------------------------------------

class TestExistsAndList:
    def test_exists_true(self, provider: LocalFolderProvider, sample_md: str):
        assert provider.exists("project", sample_md) is True

    def test_exists_false(self, provider: LocalFolderProvider):
        assert provider.exists("project", "10_Projects/Nope.md") is False

    def test_list_entities(self, provider: LocalFolderProvider, sample_md: str):
        entities = provider.list_entities("project")
        assert len(entities) == 1
        assert entities[0]["entity_id"] == sample_md
        assert entities[0]["metadata"]["tracker_id"] == 42

    def test_list_entities_empty_dir(self, provider: LocalFolderProvider):
        entities = provider.list_entities("project")
        assert entities == []


# ---------------------------------------------------------------------------
# Watch for changes
# ---------------------------------------------------------------------------

class TestWatchForChanges:
    def test_first_call_returns_empty(self, provider: LocalFolderProvider, sample_md: str):
        """First watch call builds baseline — no changes reported."""
        changes = provider.watch_for_changes()
        assert changes == []

    def test_detects_modification(self, provider: LocalFolderProvider, sample_md: str, storage_root: Path):
        provider.watch_for_changes()  # baseline

        # Modify the file
        path = storage_root / sample_md
        path.write_text(path.read_text(encoding="utf-8") + "\n<!-- edited -->", encoding="utf-8")

        changes = provider.watch_for_changes()
        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.MODIFIED
        assert changes[0].entity_id == sample_md

    def test_detects_creation(self, provider: LocalFolderProvider, sample_md: str, storage_root: Path):
        provider.watch_for_changes()  # baseline

        # Create a new file
        new_file = storage_root / "10_Projects" / "New_File.md"
        new_file.write_text("---\ntitle: New\n---\n# New\n", encoding="utf-8")

        changes = provider.watch_for_changes()
        created = [c for c in changes if c.change_type == ChangeType.CREATED]
        assert len(created) == 1
        assert "New_File.md" in created[0].entity_id

    def test_detects_deletion(self, provider: LocalFolderProvider, sample_md: str, storage_root: Path):
        provider.watch_for_changes()  # baseline

        (storage_root / sample_md).unlink()

        changes = provider.watch_for_changes()
        deleted = [c for c in changes if c.change_type == ChangeType.DELETED]
        assert len(deleted) == 1
        assert deleted[0].entity_id == sample_md


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestFactory:
    def test_create_local_folder_provider(self, storage_root: Path, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_PROVIDER", "local_folder")
        monkeypatch.setattr("app.core.config.settings.STORAGE_PATH", str(storage_root))

        reset_storage_provider()
        p = create_storage_provider()
        assert isinstance(p, LocalFolderProvider)

    def test_unknown_provider_raises(self, storage_root: Path, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_PROVIDER", "s3_bucket")
        monkeypatch.setattr("app.core.config.settings.STORAGE_PATH", str(storage_root))

        with pytest.raises(ValueError, match="Unknown storage provider"):
            create_storage_provider()

    def test_missing_path_raises(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_PROVIDER", "local_folder")
        monkeypatch.setattr("app.core.config.settings.STORAGE_PATH", None)
        monkeypatch.setattr("app.core.config.settings.SECOND_BRAIN_ROOT", None)

        with pytest.raises(ValueError, match="No storage path configured"):
            create_storage_provider()
