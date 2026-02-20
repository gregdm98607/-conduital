"""
Tests for BACKLOG-082: Session Summary Capture endpoint.

Tests the POST /intelligence/session-summary endpoint including:
- Empty session (no activity)
- Session with task completions
- Session with momentum changes
- Memory layer persistence (persist=True)
- Idempotent session-latest upsert
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.models.base import Base
from app.models.project import Project
from app.models.task import Task
from app.models.activity_log import ActivityLog
from app.models.momentum_snapshot import MomentumSnapshot
# Import memory layer models so their tables are registered with Base.metadata
from app.modules.memory_layer.models import MemoryObject, MemoryNamespace  # noqa: F401


@pytest.fixture(scope="function")
def test_client(in_memory_engine):
    """Create a TestClient with proper database override for session summary tests."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=in_memory_engine
    )

    Base.metadata.create_all(bind=in_memory_engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("app.core.database.init_db"),
        patch("app.main.enable_wal_mode"),
        patch("app.main.register_modules", return_value=set()),
        patch("app.main.mount_module_routers"),
        patch("app.services.scheduler_service.start_scheduler"),
        patch(
            "app.services.scheduler_service.run_urgency_zone_recalculation_now",
            new_callable=AsyncMock,
        ),
    ):
        client = TestClient(app)
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=in_memory_engine)


@pytest.fixture
def session_db(in_memory_engine, test_client):
    """Get a DB session that shares the same engine as the test client."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=in_memory_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()


class TestSessionSummaryEmpty:
    """Test session summary with no activity."""

    def test_empty_session_returns_zero_counts(self, test_client):
        """Empty session should return all zeros with a 'No activity' message."""
        response = test_client.post("/api/v1/intelligence/session-summary")
        assert response.status_code == 200

        data = response.json()
        assert data["tasks_completed"] == 0
        assert data["tasks_created"] == 0
        assert data["tasks_updated"] == 0
        assert data["projects_touched"] == []
        assert data["momentum_changes"] == []
        assert data["activity_count"] == 0
        assert "No activity" in data["summary_text"]
        assert data["persisted"] is False
        assert data["memory_object_id"] is None


class TestSessionSummaryWithData:
    """Test session summary with task completions and momentum."""

    def test_session_with_completions(self, test_client, session_db):
        """Session with completed tasks returns correct counts and summary."""
        now = datetime.now(timezone.utc)

        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            momentum_score=0.65,
        )
        session_db.add(project)
        session_db.commit()

        # 2 completed tasks, 1 new task
        t1 = Task(
            title="Completed Task 1",
            project_id=project.id,
            status="completed",
            priority=1,
            completed_at=now - timedelta(minutes=30),
        )
        t2 = Task(
            title="Completed Task 2",
            project_id=project.id,
            status="completed",
            priority=2,
            completed_at=now - timedelta(minutes=15),
        )
        t3 = Task(
            title="New Task",
            project_id=project.id,
            status="pending",
            priority=3,
        )
        session_db.add_all([t1, t2, t3])
        session_db.commit()

        # Set created_at: t1/t2 created before session, t3 created during session
        t1.created_at = now - timedelta(hours=3)
        t2.created_at = now - timedelta(hours=3)
        t3.created_at = now - timedelta(minutes=10)
        session_db.commit()

        # Activity log entries
        a1 = ActivityLog(
            entity_type="task",
            entity_id=t1.id,
            action_type="completed",
            timestamp=now - timedelta(minutes=30),
            source="user",
        )
        a2 = ActivityLog(
            entity_type="task",
            entity_id=t2.id,
            action_type="completed",
            timestamp=now - timedelta(minutes=15),
            source="user",
        )
        session_db.add_all([a1, a2])
        session_db.commit()

        session_start = (now - timedelta(hours=2)).isoformat()
        response = test_client.post(
            "/api/v1/intelligence/session-summary",
            params={"session_start": session_start},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["tasks_completed"] == 2
        assert data["tasks_created"] == 1
        assert "Test Project" in data["projects_touched"]
        assert data["activity_count"] == 2
        assert "Completed 2 tasks" in data["summary_text"]
        assert "Created 1 new task" in data["summary_text"]

    def test_session_with_momentum_changes(self, test_client, session_db):
        """Session shows momentum deltas for touched projects."""
        now = datetime.now(timezone.utc)

        project = Project(
            title="Momentum Project",
            status="active",
            priority=1,
            momentum_score=0.75,
        )
        session_db.add(project)
        session_db.commit()

        # Pre-session snapshot
        old_snapshot = MomentumSnapshot(
            project_id=project.id,
            score=0.50,
            factors_json="{}",
            snapshot_at=now - timedelta(hours=5),
        )
        session_db.add(old_snapshot)

        # Completed task to touch the project
        task = Task(
            title="Done Task",
            project_id=project.id,
            status="completed",
            priority=1,
            completed_at=now - timedelta(minutes=20),
        )
        session_db.add(task)
        session_db.commit()

        session_start = (now - timedelta(hours=2)).isoformat()
        response = test_client.post(
            "/api/v1/intelligence/session-summary",
            params={"session_start": session_start},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["momentum_changes"]) == 1
        mc = data["momentum_changes"][0]
        assert mc["project_name"] == "Momentum Project"
        assert mc["old_score"] == 0.50
        assert mc["new_score"] == 0.75
        assert "+0.25" in data["summary_text"]


class TestSessionSummaryPersist:
    """Test memory layer persistence."""

    def test_persist_creates_memory_objects(self, test_client, session_db):
        """persist=True creates session summary and session-latest memory objects."""
        from app.modules.memory_layer.models import MemoryObject

        response = test_client.post(
            "/api/v1/intelligence/session-summary?persist=true&notes=Great%20session"
        )
        assert response.status_code == 200

        data = response.json()
        assert data["persisted"] is True
        assert data["memory_object_id"] is not None
        assert data["memory_object_id"].startswith("session-summary-")

        # Verify summary object in DB
        summary_obj = (
            session_db.query(MemoryObject)
            .filter(MemoryObject.object_id == data["memory_object_id"])
            .first()
        )
        assert summary_obj is not None
        assert summary_obj.namespace == "sessions.history"
        assert summary_obj.priority == 60
        assert "session" in (summary_obj.tags or [])
        assert summary_obj.content["user_notes"] == "Great session"

        # Verify session-latest was created
        latest_obj = (
            session_db.query(MemoryObject)
            .filter(MemoryObject.object_id == "session-latest")
            .first()
        )
        assert latest_obj is not None
        assert latest_obj.namespace == "sessions.history"
        assert latest_obj.priority == 80
        assert "latest" in (latest_obj.tags or [])

    def test_persist_updates_existing_latest(self, test_client, session_db):
        """Calling persist=True twice updates (not duplicates) session-latest."""
        from app.modules.memory_layer.models import MemoryObject

        response1 = test_client.post(
            "/api/v1/intelligence/session-summary?persist=true&notes=First"
        )
        assert response1.status_code == 200
        assert response1.json()["persisted"] is True

        response2 = test_client.post(
            "/api/v1/intelligence/session-summary?persist=true&notes=Second"
        )
        assert response2.status_code == 200
        assert response2.json()["persisted"] is True

        # Only one session-latest should exist
        latest_count = (
            session_db.query(MemoryObject)
            .filter(MemoryObject.object_id == "session-latest")
            .count()
        )
        assert latest_count == 1

        latest = (
            session_db.query(MemoryObject)
            .filter(MemoryObject.object_id == "session-latest")
            .first()
        )
        assert latest.content["user_notes"] == "Second"


class TestSessionSummaryValidation:
    """Test input validation."""

    def test_invalid_session_start_returns_400(self, test_client):
        """Invalid session_start format returns 400."""
        response = test_client.post(
            "/api/v1/intelligence/session-summary?session_start=not-a-date"
        )
        assert response.status_code == 400
        assert "Invalid session_start" in response.json()["detail"]
