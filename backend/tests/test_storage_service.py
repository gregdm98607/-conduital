"""
Tests for StorageService — Phase 3: write-through and cache rebuild.

Tests cover:
- Legacy mode (no-op passthrough)
- Storage-first mode (write-through to StorageProvider)
- Cache rebuild from markdown files
- External change detection
"""

import textwrap
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.project import Project
from app.models.task import Task
from app.storage.local_folder import LocalFolderProvider
from app.services.storage_service import StorageService, _is_storage_first


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session():
    """In-memory SQLite session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session_ = sessionmaker(bind=engine)
    session = Session_()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def storage_root(tmp_path: Path) -> Path:
    """Temp folder with expected watch subdirectory."""
    (tmp_path / "10_Projects").mkdir()
    return tmp_path


@pytest.fixture()
def provider(storage_root: Path) -> LocalFolderProvider:
    return LocalFolderProvider(root_path=storage_root, watch_directories=["10_Projects"])


@pytest.fixture()
def sample_project(db_session) -> Project:
    """A project row in SQLite (no file yet)."""
    project = Project(
        title="Test Project",
        status="active",
        priority=3,
        momentum_score=0.5,
        last_activity_at=datetime.now(timezone.utc),
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture()
def sample_md(storage_root: Path) -> str:
    """Write a sample markdown file and return its entity_id."""
    md = textwrap.dedent("""\
        ---
        tracker_id: 99
        project_status: active
        priority: 2
        momentum_score: 0.8
        title: Markdown Project
        ---
        # Markdown Project

        Body text.

        ## Next Actions

        - [ ] Task A <!-- tracker:task:aaa111 -->
        - [x] Task B <!-- tracker:task:bbb222 -->
    """)
    fp = storage_root / "10_Projects" / "Markdown_Project.md"
    fp.write_text(md, encoding="utf-8")
    return "10_Projects/Markdown_Project.md"


# ---------------------------------------------------------------------------
# Legacy mode tests (default — StorageService is a no-op)
# ---------------------------------------------------------------------------

class TestLegacyMode:
    def test_is_storage_first_defaults_to_false(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "legacy")
        assert _is_storage_first() is False

    def test_persist_project_is_noop_in_legacy(self, db_session, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "legacy")
        service = StorageService(db_session)
        project = Project(title="X", status="active", priority=5)
        # Should not raise and should not touch any provider
        service.persist_project(project)

    def test_persist_task_is_noop_in_legacy(self, db_session, sample_project, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "legacy")
        task = Task(title="T", project_id=sample_project.id, status="pending")
        db_session.add(task)
        db_session.flush()
        service = StorageService(db_session)
        service.persist_task(task)  # no-op

    def test_delete_project_is_noop_in_legacy(self, db_session, sample_project, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "legacy")
        service = StorageService(db_session)
        service.delete_project_from_storage(sample_project)  # no-op

    def test_sync_external_changes_returns_zero_in_legacy(self, db_session, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "legacy")
        service = StorageService(db_session)
        result = service.sync_external_changes()
        assert result == {"changes": 0}


# ---------------------------------------------------------------------------
# Storage-first mode tests
# ---------------------------------------------------------------------------

class TestStorageFirstMode:
    def test_is_storage_first_true(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")
        assert _is_storage_first() is True

    def test_persist_project_creates_file(
        self, db_session, sample_project, provider, storage_root, monkeypatch
    ):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")
        service = StorageService(db_session)
        service._provider = provider

        service.persist_project(sample_project)

        # File should be created
        assert sample_project.file_path is not None
        assert Path(sample_project.file_path).exists()

    def test_persist_project_updates_existing_file(
        self, db_session, provider, storage_root, sample_md, monkeypatch
    ):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")

        abs_path = str(storage_root / sample_md)
        project = Project(
            title="Markdown Project",
            status="completed",
            priority=1,
            momentum_score=1.0,
            file_path=abs_path,
            last_activity_at=datetime.now(timezone.utc),
        )
        db_session.add(project)
        db_session.commit()

        service = StorageService(db_session)
        service._provider = provider

        service.persist_project(project)

        # Read back and verify status was updated
        result = provider.read_entity("project", sample_md)
        assert result["metadata"]["project_status"] == "completed"

    def test_delete_project_removes_file(
        self, db_session, provider, storage_root, sample_md, monkeypatch
    ):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")

        abs_path = str(storage_root / sample_md)
        project = Project(
            title="Markdown Project",
            status="active",
            priority=2,
            file_path=abs_path,
        )
        db_session.add(project)
        db_session.commit()

        service = StorageService(db_session)
        service._provider = provider

        assert (storage_root / sample_md).exists()
        service.delete_project_from_storage(project)
        assert not (storage_root / sample_md).exists()


# ---------------------------------------------------------------------------
# Cache rebuild tests
# ---------------------------------------------------------------------------

class TestCacheRebuild:
    def test_rebuild_creates_project_from_markdown(
        self, db_session, provider, storage_root, sample_md, monkeypatch
    ):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")
        monkeypatch.setattr("app.core.config.settings.STORAGE_PROVIDER", "local_folder")
        monkeypatch.setattr("app.core.config.settings.STORAGE_PATH", str(storage_root))
        monkeypatch.setattr("app.core.config.settings.SECOND_BRAIN_ROOT", str(storage_root))
        monkeypatch.setattr("app.core.config.settings.WATCH_DIRECTORIES", "10_Projects")

        from app.storage.factory import reset_storage_provider
        reset_storage_provider()

        stats = StorageService.rebuild_cache(db_session)

        assert stats["scanned"] >= 1
        assert stats["created"] >= 1
        assert stats["errors"] == 0

        # Project should exist in SQLite
        project = db_session.execute(
            select(Project).where(Project.title == "Markdown Project")
        ).scalar_one_or_none()
        assert project is not None
        assert project.status == "active"
        assert project.priority == 2

        # Tasks should be created
        tasks = db_session.execute(
            select(Task).where(Task.project_id == project.id)
        ).scalars().all()
        assert len(tasks) == 2

        reset_storage_provider()

    def test_rebuild_updates_existing_project(
        self, db_session, provider, storage_root, sample_md, monkeypatch
    ):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")
        monkeypatch.setattr("app.core.config.settings.STORAGE_PROVIDER", "local_folder")
        monkeypatch.setattr("app.core.config.settings.STORAGE_PATH", str(storage_root))
        monkeypatch.setattr("app.core.config.settings.SECOND_BRAIN_ROOT", str(storage_root))
        monkeypatch.setattr("app.core.config.settings.WATCH_DIRECTORIES", "10_Projects")

        from app.storage.factory import reset_storage_provider
        reset_storage_provider()

        # Pre-create project with old data
        abs_path = str(storage_root / sample_md)
        project = Project(
            title="Old Title",
            status="someday_maybe",
            priority=9,
            file_path=abs_path,
        )
        db_session.add(project)
        db_session.commit()
        project_id = project.id

        stats = StorageService.rebuild_cache(db_session)
        assert stats["updated"] >= 1

        # Project should be updated from markdown (markdown wins)
        db_session.expire_all()
        updated = db_session.get(Project, project_id)
        assert updated.title == "Markdown Project"
        assert updated.status == "active"
        assert updated.priority == 2

        reset_storage_provider()

    def test_rebuild_noop_when_legacy(self, db_session, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "legacy")
        from app.services.storage_service import rebuild_sqlite_cache_on_startup
        result = rebuild_sqlite_cache_on_startup(db_session)
        assert result == {}


# ---------------------------------------------------------------------------
# External change detection tests
# ---------------------------------------------------------------------------

class TestExternalChangeDetection:
    def test_detects_modified_file(
        self, db_session, provider, storage_root, sample_md, monkeypatch
    ):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")

        service = StorageService(db_session)
        service._provider = provider

        # Build baseline snapshot
        provider.watch_for_changes()

        # Pre-create matching project in SQLite
        abs_path = str(storage_root / sample_md)
        project = Project(
            title="Markdown Project",
            status="active",
            priority=2,
            file_path=abs_path,
        )
        db_session.add(project)
        db_session.commit()

        # Modify file externally
        fp = storage_root / sample_md
        fp.write_text(
            fp.read_text(encoding="utf-8").replace("priority: 2", "priority: 1"),
            encoding="utf-8",
        )

        stats = service.sync_external_changes()
        assert stats["changes"] >= 1
        assert stats["updated"] >= 1

    def test_detects_deleted_file(
        self, db_session, provider, storage_root, sample_md, monkeypatch
    ):
        monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")

        service = StorageService(db_session)
        service._provider = provider

        # Build baseline
        provider.watch_for_changes()

        # Pre-create matching project
        abs_path = str(storage_root / sample_md)
        project = Project(
            title="Markdown Project",
            status="active",
            priority=2,
            file_path=abs_path,
        )
        db_session.add(project)
        db_session.commit()
        pid = project.id

        # Delete file
        (storage_root / sample_md).unlink()

        stats = service.sync_external_changes()
        assert stats["deleted"] >= 1

        # Project should be soft-deleted
        db_session.expire_all()
        proj = db_session.get(Project, pid)
        assert proj.deleted_at is not None
