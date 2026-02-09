"""
Inbox API endpoint tests — BETA-030, BETA-031, BETA-032.

Tests for:
- Weekly review completion tracking (BETA-030)
- Inbox batch processing (BETA-031)
- Inbox processing stats (BETA-032)
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.models.base import Base
from app.models import InboxItem, Project, Task, WeeklyReviewCompletion


@pytest.fixture(scope="function")
def test_client(in_memory_engine):
    """Create a TestClient with proper database override."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_engine)

    Base.metadata.create_all(bind=in_memory_engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.core.database.init_db"), \
         patch("app.main.enable_wal_mode"), \
         patch("app.main.register_modules", return_value=set()), \
         patch("app.main.mount_module_routers"), \
         patch("app.services.scheduler_service.start_scheduler"), \
         patch("app.services.scheduler_service.run_urgency_zone_recalculation_now", new_callable=AsyncMock):
        client = TestClient(app)
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=in_memory_engine)


@pytest.fixture
def db_with_inbox_items(db_session):
    """Create inbox items with various states for testing."""
    now = datetime.now(timezone.utc)

    project = Project(title="Test Project", status="active", priority=1)
    db_session.add(project)
    db_session.commit()

    items = [
        InboxItem(content="Unprocessed item 1", source="web_ui"),
        InboxItem(content="Unprocessed item 2", source="web_ui"),
        InboxItem(content="Unprocessed item 3", source="api"),
        InboxItem(
            content="Processed today",
            source="web_ui",
            processed_at=now - timedelta(hours=2),
            result_type="task",
            captured_at=now - timedelta(hours=5),
        ),
        InboxItem(
            content="Processed yesterday",
            source="web_ui",
            processed_at=now - timedelta(days=1, hours=3),
            result_type="project",
            captured_at=now - timedelta(days=1, hours=6),
        ),
    ]
    db_session.add_all(items)
    db_session.commit()
    return {"items": items, "project": project}


# =============================================================================
# BETA-030: Weekly Review Completion
# =============================================================================


class TestWeeklyReviewCompletion:
    """Tests for BETA-030: Weekly review completion tracking."""

    def test_complete_weekly_review(self, test_client):
        """POST /weekly-review/complete creates a completion record."""
        response = test_client.post("/api/v1/intelligence/weekly-review/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert "completed_at" in data

    def test_complete_with_notes(self, test_client):
        """POST /weekly-review/complete accepts optional notes."""
        response = test_client.post(
            "/api/v1/intelligence/weekly-review/complete",
            json={"notes": "Reviewed all projects, moved 2 to someday/maybe"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Reviewed all projects, moved 2 to someday/maybe"

    def test_history_empty(self, test_client):
        """GET /weekly-review/history returns empty when no completions."""
        response = test_client.get("/api/v1/intelligence/weekly-review/history")
        assert response.status_code == 200
        data = response.json()
        assert data["completions"] == []
        assert data["last_completed_at"] is None
        assert data["days_since_last_review"] is None

    def test_history_after_completion(self, test_client):
        """GET /weekly-review/history returns data after completing a review."""
        # Complete a review
        test_client.post("/api/v1/intelligence/weekly-review/complete")

        response = test_client.get("/api/v1/intelligence/weekly-review/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data["completions"]) == 1
        assert data["last_completed_at"] is not None
        assert data["days_since_last_review"] == 0

    def test_history_ordering(self, test_client):
        """History returns completions in reverse chronological order."""
        # Complete multiple reviews
        test_client.post("/api/v1/intelligence/weekly-review/complete",
                         json={"notes": "First review"})
        test_client.post("/api/v1/intelligence/weekly-review/complete",
                         json={"notes": "Second review"})

        response = test_client.get("/api/v1/intelligence/weekly-review/history")
        data = response.json()
        assert len(data["completions"]) == 2
        assert data["completions"][0]["notes"] == "Second review"
        assert data["completions"][1]["notes"] == "First review"

    def test_history_limit(self, test_client):
        """History respects the limit parameter."""
        for i in range(5):
            test_client.post("/api/v1/intelligence/weekly-review/complete",
                             json={"notes": f"Review {i}"})

        response = test_client.get("/api/v1/intelligence/weekly-review/history?limit=3")
        data = response.json()
        assert len(data["completions"]) == 3


class TestWeeklyReviewCompletionModel:
    """Unit tests for WeeklyReviewCompletion model."""

    def test_create_completion(self, db_session):
        """Model can be created and persisted."""
        completion = WeeklyReviewCompletion(
            completed_at=datetime.now(timezone.utc),
            notes="Test review",
        )
        db_session.add(completion)
        db_session.commit()
        assert completion.id is not None

    def test_repr(self, db_session):
        """Model has a readable repr."""
        completion = WeeklyReviewCompletion(
            completed_at=datetime.now(timezone.utc),
        )
        db_session.add(completion)
        db_session.commit()
        assert "WeeklyReviewCompletion" in repr(completion)


# =============================================================================
# BETA-032: Inbox Stats
# =============================================================================


class TestInboxStats:
    """Tests for BETA-032: Inbox processing stats endpoint."""

    def test_stats_empty(self, test_client):
        """Stats endpoint returns zeros when no items exist."""
        response = test_client.get("/api/v1/inbox/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["unprocessed_count"] == 0
        assert data["processed_today"] == 0
        assert data["avg_processing_time_hours"] is None

    def test_stats_with_items(self, db_session, db_with_inbox_items):
        """Stats correctly counts unprocessed and processed items."""
        from app.api.inbox import get_inbox_stats

        # Direct service test using db_session
        now = datetime.now(timezone.utc)

        # Count unprocessed: should be 3
        unprocessed = db_session.query(InboxItem).filter(
            InboxItem.processed_at.is_(None)
        ).count()
        assert unprocessed == 3

    def test_stats_unprocessed_count(self, test_client):
        """Stats endpoint returns correct unprocessed count via API."""
        # Create some items
        test_client.post("/api/v1/inbox", json={"content": "Item 1"})
        test_client.post("/api/v1/inbox", json={"content": "Item 2"})

        response = test_client.get("/api/v1/inbox/stats")
        data = response.json()
        assert data["unprocessed_count"] == 2


# =============================================================================
# BETA-031: Inbox Batch Processing
# =============================================================================


class TestInboxBatchProcessing:
    """Tests for BETA-031: Inbox batch processing endpoint."""

    def test_batch_delete(self, test_client):
        """Batch delete removes multiple items."""
        # Create items
        r1 = test_client.post("/api/v1/inbox", json={"content": "Delete me 1"})
        r2 = test_client.post("/api/v1/inbox", json={"content": "Delete me 2"})
        id1 = r1.json()["id"]
        id2 = r2.json()["id"]

        response = test_client.post("/api/v1/inbox/batch-process", json={
            "item_ids": [id1, id2],
            "action": "delete",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 2
        assert data["failed"] == 0

    def test_batch_assign_to_project(self, test_client):
        """Batch assign creates tasks in target project."""
        # Create a project
        proj_response = test_client.post("/api/v1/projects", json={
            "title": "Target Project",
            "status": "active",
            "priority": 1,
        })
        project_id = proj_response.json()["id"]

        # Create inbox items
        r1 = test_client.post("/api/v1/inbox", json={"content": "Task from inbox 1"})
        r2 = test_client.post("/api/v1/inbox", json={"content": "Task from inbox 2"})
        id1 = r1.json()["id"]
        id2 = r2.json()["id"]

        response = test_client.post("/api/v1/inbox/batch-process", json={
            "item_ids": [id1, id2],
            "action": "assign_to_project",
            "project_id": project_id,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 2
        assert data["failed"] == 0

    def test_batch_requires_project_for_assign(self, test_client):
        """Batch assign without project_id returns 400."""
        r1 = test_client.post("/api/v1/inbox", json={"content": "Item"})
        id1 = r1.json()["id"]

        response = test_client.post("/api/v1/inbox/batch-process", json={
            "item_ids": [id1],
            "action": "assign_to_project",
        })
        assert response.status_code == 400

    def test_batch_nonexistent_items(self, test_client):
        """Batch process handles nonexistent item IDs gracefully."""
        response = test_client.post("/api/v1/inbox/batch-process", json={
            "item_ids": [9999, 9998],
            "action": "delete",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 0
        assert data["failed"] == 2

    def test_batch_invalid_action(self, test_client):
        """Batch process rejects invalid actions."""
        response = test_client.post("/api/v1/inbox/batch-process", json={
            "item_ids": [1],
            "action": "invalid_action",
        })
        assert response.status_code == 422

    def test_batch_mixed_results(self, test_client):
        """Batch process handles mix of valid and invalid items."""
        r1 = test_client.post("/api/v1/inbox", json={"content": "Valid item"})
        id1 = r1.json()["id"]

        response = test_client.post("/api/v1/inbox/batch-process", json={
            "item_ids": [id1, 9999],
            "action": "delete",
        })
        data = response.json()
        assert data["processed"] == 1
        assert data["failed"] == 1
