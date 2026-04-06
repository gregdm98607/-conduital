"""
Phase 5 — Integration tests for the storage provider abstraction.

Covers:
- Full round-trip: create via API-style → verify markdown → edit externally → verify reflects
- Migration: populate SQLite → export to folder → rebuild from folder → verify
- Concurrent access: external edit during API write
- Large dataset: 100+ projects, 500+ tasks — performance check
"""

import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.project import Project
from app.models.task import Task
from app.storage.local_folder import LocalFolderProvider
from app.services.storage_service import StorageService
from app.storage.factory import reset_storage_provider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session():
    """In-memory SQLite session with all tables."""
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
    """Temp folder with expected watch subdirectories."""
    (tmp_path / "10_Projects").mkdir()
    (tmp_path / "areas").mkdir()
    (tmp_path / "goals").mkdir()
    (tmp_path / "visions").mkdir()
    return tmp_path


@pytest.fixture()
def provider(storage_root: Path) -> LocalFolderProvider:
    return LocalFolderProvider(
        root_path=storage_root,
        watch_directories=["10_Projects"],
    )


def _patch_storage_first(monkeypatch, storage_root: Path):
    """Helper to set up storage-first mode in monkeypatch."""
    monkeypatch.setattr("app.core.config.settings.STORAGE_MODE", "storage_first")
    monkeypatch.setattr("app.core.config.settings.STORAGE_PROVIDER", "local_folder")
    monkeypatch.setattr("app.core.config.settings.STORAGE_PATH", str(storage_root))
    monkeypatch.setattr("app.core.config.settings.SECOND_BRAIN_ROOT", str(storage_root))
    monkeypatch.setattr("app.core.config.settings.WATCH_DIRECTORIES", "10_Projects")
    reset_storage_provider()


# ---------------------------------------------------------------------------
# 1. Full round-trip integration tests
# ---------------------------------------------------------------------------


class TestFullRoundTrip:
    """Create entity via StorageService → verify markdown → edit externally → verify API."""

    def test_create_project_roundtrip(
        self, db_session, provider, storage_root, monkeypatch
    ):
        """Create project via StorageService, verify markdown, edit file, verify changes."""
        _patch_storage_first(monkeypatch, storage_root)

        # Step 1: Create a project in SQLite
        project = Project(
            title="Round Trip Project",
            status="active",
            priority=2,
            momentum_score=0.6,
            last_activity_at=datetime.now(timezone.utc),
        )
        db_session.add(project)
        db_session.flush()

        # Step 2: Write to storage via StorageService
        service = StorageService(db_session)
        service._provider = provider
        service.persist_project(project)
        db_session.commit()

        # Step 3: Verify markdown file was created
        assert project.file_path is not None
        file_path = Path(project.file_path)
        assert file_path.exists()
        content = file_path.read_text(encoding="utf-8")
        assert "Round Trip Project" in content
        assert "project_status: active" in content

        # Step 4: Edit the markdown file externally (simulating Obsidian edit)
        new_content = content.replace("project_status: active", "project_status: completed")
        new_content = new_content.replace("priority: 2", "priority: 1")
        file_path.write_text(new_content, encoding="utf-8")

        # Step 5: Read back via provider and verify changes
        entity_id = provider._relative_id(file_path)
        result = provider.read_entity("project", entity_id)
        assert result["metadata"]["project_status"] == "completed"
        assert result["metadata"]["priority"] == 1

    def test_entity_handler_roundtrip_area(self, provider, storage_root):
        """Write an area, read it back, edit externally, read again."""
        from app.sync.entity_markdown import AreaMarkdown

        # Write via provider
        data = {
            "title": "Health & Fitness",
            "description": "Stay healthy.",
            "standard_of_excellence": "Exercise 4x/week.",
            "health_score": 0.8,
            "review_frequency": "weekly",
            "is_archived": False,
        }
        entity_id = provider.write_entity("area", "", data)
        assert (storage_root / entity_id).exists()

        # Read back
        result = provider.read_entity("area", entity_id)
        assert result["title"] == "Health & Fitness"
        assert result["health_score"] == 0.8

        # Edit externally
        fp = storage_root / entity_id
        text = fp.read_text(encoding="utf-8")
        fp.write_text(text.replace("health_score: 0.8", "health_score: 0.95"), encoding="utf-8")

        # Read again
        result2 = provider.read_entity("area", entity_id)
        assert result2["health_score"] == 0.95

    def test_entity_handler_roundtrip_goal(self, provider, storage_root):
        """Write a goal, read it back, verify all fields."""
        data = {
            "title": "Ship v2.0",
            "description": "Release version 2.0 by Q3.",
            "timeframe": "1_year",
            "status": "active",
        }
        entity_id = provider.write_entity("goal", "", data)
        result = provider.read_entity("goal", entity_id)
        assert result["title"] == "Ship v2.0"
        assert result["description"] == "Release version 2.0 by Q3."
        assert result["metadata"]["status"] == "active"


# ---------------------------------------------------------------------------
# 2. Migration test: SQLite → folder → rebuild → verify
# ---------------------------------------------------------------------------


class TestMigrationRoundTrip:
    """Populate SQLite, export to markdown, delete SQLite, rebuild from folder."""

    def test_full_migration_cycle(
        self, db_session, provider, storage_root, monkeypatch
    ):
        _patch_storage_first(monkeypatch, storage_root)

        # Step 1: Create projects and tasks in SQLite
        for i in range(5):
            project = Project(
                title=f"Migration Project {i}",
                status="active",
                priority=i + 1,
                momentum_score=0.1 * (i + 1),
                last_activity_at=datetime.now(timezone.utc),
            )
            db_session.add(project)
            db_session.flush()

            for j in range(3):
                task = Task(
                    title=f"Task {j} for project {i}",
                    project_id=project.id,
                    status="pending" if j < 2 else "completed",
                    file_marker=f"tracker:task:mig-{i}-{j}",
                )
                db_session.add(task)

            # Write to storage
            service = StorageService(db_session)
            service._provider = provider
            service.persist_project(project)

        db_session.commit()

        # Step 2: Verify all 5 markdown files exist
        md_files = list((storage_root / "10_Projects").rglob("*.md"))
        assert len(md_files) == 5

        # Step 3: Wipe SQLite (simulate fresh start)
        db_session.close()
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        Session_ = sessionmaker(bind=engine)
        fresh_session = Session_()

        # Step 4: Rebuild cache from markdown files
        reset_storage_provider()
        stats = StorageService.rebuild_cache(fresh_session)

        assert stats["scanned"] == 5
        assert stats["created"] == 5
        assert stats["errors"] == 0

        # Step 5: Verify all projects are restored
        projects = fresh_session.execute(select(Project)).scalars().all()
        assert len(projects) == 5

        # Verify tasks were also restored
        all_tasks = fresh_session.execute(select(Task)).scalars().all()
        assert len(all_tasks) == 15  # 5 projects * 3 tasks each

        fresh_session.close()
        reset_storage_provider()


# ---------------------------------------------------------------------------
# 3. Concurrent access: external edit during API write
# ---------------------------------------------------------------------------


class TestConcurrentAccess:
    """Simulate external edits happening alongside API writes."""

    def test_external_edit_then_api_write_preserves_external_content(
        self, db_session, provider, storage_root, monkeypatch
    ):
        """
        External user adds a line to markdown body.
        API then writes metadata update — the external body edit should survive.
        """
        _patch_storage_first(monkeypatch, storage_root)

        # Create initial project via service
        project = Project(
            title="Concurrent Test",
            status="active",
            priority=3,
            momentum_score=0.5,
            last_activity_at=datetime.now(timezone.utc),
        )
        db_session.add(project)
        db_session.flush()

        service = StorageService(db_session)
        service._provider = provider
        service.persist_project(project)
        db_session.commit()

        # External user edits the markdown body (e.g., in Obsidian)
        file_path = Path(project.file_path)
        content = file_path.read_text(encoding="utf-8")
        external_edit = content + "\n\n## External Notes\n\nAdded by Obsidian user.\n"
        file_path.write_text(external_edit, encoding="utf-8")

        # API updates only metadata (status change)
        project.status = "completed"
        project.momentum_score = 1.0
        service.persist_project(project)
        db_session.commit()

        # Verify the external content is preserved
        final_content = file_path.read_text(encoding="utf-8")
        assert "Added by Obsidian user." in final_content
        assert "project_status: completed" in final_content

    def test_watch_detects_external_changes_between_writes(
        self, db_session, provider, storage_root, monkeypatch
    ):
        """
        Provider write → external edit → watch_for_changes → detect modification.
        """
        _patch_storage_first(monkeypatch, storage_root)

        # Write a project
        data = {
            "title": "Watch Test",
            "status": "active",
            "priority": 5,
            "momentum_score": 0.3,
        }
        entity_id = provider.write_entity("project", "", data)

        # Initialize watch baseline
        provider.watch_for_changes()

        # External edit
        fp = storage_root / entity_id
        text = fp.read_text(encoding="utf-8")
        fp.write_text(text + "\n<!-- external note -->\n", encoding="utf-8")

        # Watch should detect the change
        changes = provider.watch_for_changes()
        assert len(changes) == 1
        assert changes[0].entity_id == entity_id


# ---------------------------------------------------------------------------
# 4. Large dataset performance test
# ---------------------------------------------------------------------------


class TestLargeDataset:
    """Verify 100+ projects and 500+ tasks perform acceptably."""

    def test_100_projects_500_tasks(self, provider, storage_root, monkeypatch):
        """
        Create 100 projects with 5 tasks each (500 tasks total).
        Verify list_entities and watch_for_changes complete in reasonable time.
        """
        _patch_storage_first(monkeypatch, storage_root)

        # Create 100 project markdown files
        projects_dir = storage_root / "10_Projects"
        for i in range(100):
            task_lines = []
            for j in range(5):
                checked = "x" if j == 0 else " "
                task_lines.append(
                    f"- [{checked}] Task {j} for project {i} "
                    f"<!-- tracker:task:large-{i}-{j} -->"
                )
            tasks_block = "\n".join(task_lines)

            md = textwrap.dedent(f"""\
                ---
                tracker_id: {1000 + i}
                project_status: active
                priority: {(i % 5) + 1}
                momentum_score: {round(i / 100, 2)}
                title: Large Project {i}
                ---
                # Large Project {i}

                Project number {i} for performance testing.

                ## Next Actions

                {tasks_block}
            """)
            fp = projects_dir / f"Large_Project_{i:03d}.md"
            fp.write_text(md, encoding="utf-8")

        # Verify list_entities returns all 100 projects within 10s
        start = time.time()
        entities = provider.list_entities("project")
        elapsed_list = time.time() - start

        assert len(entities) == 100
        assert elapsed_list < 10.0, f"list_entities took {elapsed_list:.2f}s (>10s)"

        # Verify watch_for_changes baseline within 10s
        start = time.time()
        changes = provider.watch_for_changes()  # baseline — returns empty
        elapsed_watch = time.time() - start

        assert changes == []
        assert elapsed_watch < 10.0, f"watch_for_changes took {elapsed_watch:.2f}s (>10s)"

        # Modify 10 files and verify change detection
        for i in range(10):
            fp = projects_dir / f"Large_Project_{i:03d}.md"
            text = fp.read_text(encoding="utf-8")
            fp.write_text(text + f"\n<!-- bulk edit {i} -->\n", encoding="utf-8")

        start = time.time()
        changes = provider.watch_for_changes()
        elapsed_detect = time.time() - start

        assert len(changes) == 10
        assert elapsed_detect < 10.0, f"change detection took {elapsed_detect:.2f}s (>10s)"

    def test_cache_rebuild_100_projects(
        self, provider, storage_root, monkeypatch
    ):
        """Rebuild SQLite cache from 100 markdown files."""
        _patch_storage_first(monkeypatch, storage_root)

        # Create 100 projects
        projects_dir = storage_root / "10_Projects"
        for i in range(100):
            md = textwrap.dedent(f"""\
                ---
                project_status: active
                priority: {(i % 5) + 1}
                title: Rebuild Project {i}
                ---
                # Rebuild Project {i}

                - [ ] Task A <!-- tracker:task:rebuild-{i}-a -->
                - [x] Task B <!-- tracker:task:rebuild-{i}-b -->
            """)
            fp = projects_dir / f"Rebuild_Project_{i:03d}.md"
            fp.write_text(md, encoding="utf-8")

        reset_storage_provider()

        # Create a fresh SQLite and rebuild
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        Session_ = sessionmaker(bind=engine)
        session = Session_()

        start = time.time()
        stats = StorageService.rebuild_cache(session)
        elapsed = time.time() - start

        assert stats["scanned"] == 100
        assert stats["errors"] == 0
        assert elapsed < 30.0, f"Cache rebuild took {elapsed:.2f}s (>30s)"

        projects = session.execute(select(Project)).scalars().all()
        assert len(projects) == 100

        tasks = session.execute(select(Task)).scalars().all()
        assert len(tasks) == 200  # 2 tasks per project

        session.close()
        reset_storage_provider()
