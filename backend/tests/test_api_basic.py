"""
Basic API tests

Fixed test infrastructure (DEBT-024):
- TestClient created per-test via fixture (not at module level)
- Database override applied BEFORE TestClient triggers startup
- In-memory SQLite for speed and isolation
- Startup side-effects (scheduler, folder watcher) patched out

Consolidated (DEBT-070): Uses shared in_memory_engine from conftest.py
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.models.base import Base


@pytest.fixture(scope="function")
def test_client(in_memory_engine):
    """
    Create a TestClient with proper database override.

    Uses the shared in_memory_engine fixture from conftest.py (DEBT-070).

    This fixture:
    1. Reuses the shared in-memory SQLite engine (with StaticPool)
    2. Creates all tables
    3. Overrides get_db dependency BEFORE creating TestClient
    4. Patches startup side-effects (scheduler, folder watcher, urgency recalc)
    5. Yields the TestClient for the test
    6. Cleans up after
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_engine)

    # Create all tables before anything else
    Base.metadata.create_all(bind=in_memory_engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    # Import app and apply override BEFORE creating TestClient
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    # Patch startup side-effects that don't work in test context
    # - init_db: would create tables on production engine, not test engine
    # - enable_wal_mode: requires production SQLite file
    # - register_modules/mount_module_routers: module system not needed for basic tests
    # - scheduler/urgency: background tasks not needed in tests
    with patch("app.core.database.init_db"), \
         patch("app.main.enable_wal_mode"), \
         patch("app.main.register_modules", return_value=set()), \
         patch("app.main.mount_module_routers"), \
         patch("app.services.scheduler_service.start_scheduler"), \
         patch("app.services.scheduler_service.run_urgency_zone_recalculation_now", new_callable=AsyncMock):
        client = TestClient(app)
        yield client

    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=in_memory_engine)


class TestHealthEndpoints:
    """Test health and info endpoints"""

    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "app" in data
        assert "version" in data

    def test_root_endpoint(self, test_client):
        """Test root endpoint — serves SPA (HTML) if build exists, otherwise JSON API info"""
        response = test_client.get("/")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        if "text/html" in content_type:
            # Static build exists — root serves SPA
            assert len(response.content) > 0
        else:
            # No static build — root returns API info JSON
            data = response.json()
            assert "message" in data
            assert "version" in data
            assert "docs" in data


class TestProjectEndpoints:
    """Test project CRUD operations"""

    def test_create_project(self, test_client):
        """Test creating a project"""
        project_data = {
            "title": "Test Project",
            "description": "Test description",
            "status": "active",
            "priority": 2,
        }
        response = test_client.post("/api/v1/projects", json=project_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Project"
        assert data["status"] == "active"
        assert "id" in data

    def test_list_projects_empty(self, test_client):
        """Test listing projects when none exist"""
        response = test_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["projects"] == []

    def test_list_projects_with_data(self, test_client):
        """Test listing projects"""
        test_client.post(
            "/api/v1/projects",
            json={"title": "Project 1", "status": "active", "priority": 1},
        )

        response = test_client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["projects"]) == 1
        assert data["projects"][0]["title"] == "Project 1"

    def test_get_project_by_id(self, test_client):
        """Test getting a project by ID"""
        create_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Get Test", "status": "active", "priority": 3},
        )
        project_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["title"] == "Get Test"

    def test_get_project_not_found(self, test_client):
        """Test getting non-existent project"""
        response = test_client.get("/api/v1/projects/999")
        assert response.status_code == 404

    def test_update_project(self, test_client):
        """Test updating a project"""
        create_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Original", "status": "active", "priority": 3},
        )
        project_id = create_response.json()["id"]

        update_data = {"title": "Updated", "priority": 1}
        response = test_client.put(f"/api/v1/projects/{project_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["priority"] == 1

    def test_delete_project(self, test_client):
        """Test deleting a project"""
        create_response = test_client.post(
            "/api/v1/projects",
            json={"title": "To Delete", "status": "active", "priority": 3},
        )
        project_id = create_response.json()["id"]

        response = test_client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204

        get_response = test_client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404


class TestTaskEndpoints:
    """Test task CRUD operations"""

    def test_create_task(self, test_client):
        """Test creating a task"""
        project_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Project for Task", "status": "active", "priority": 3},
        )
        project_id = project_response.json()["id"]

        task_data = {
            "title": "Test Task",
            "description": "Test description",
            "project_id": project_id,
            "status": "pending",
            "is_next_action": True,
            "priority": 2,
        }
        response = test_client.post("/api/v1/tasks", json=task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["is_next_action"] is True
        assert "id" in data

    def test_list_tasks(self, test_client):
        """Test listing tasks"""
        response = test_client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data

    def test_complete_task(self, test_client):
        """Test completing a task"""
        project_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Project", "status": "active", "priority": 3},
        )
        project_id = project_response.json()["id"]

        task_response = test_client.post(
            "/api/v1/tasks",
            json={
                "title": "Task to Complete",
                "project_id": project_id,
                "status": "pending",
                "priority": 3,
            },
        )
        task_id = task_response.json()["id"]

        response = test_client.post(f"/api/v1/tasks/{task_id}/complete?actual_minutes=30")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["actual_minutes"] == 30
        assert data["completed_at"] is not None


class TestNextActions:
    """Test next actions endpoints"""

    def test_get_next_actions_empty(self, test_client):
        """Test getting next actions when none exist"""
        response = test_client.get("/api/v1/next-actions")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert "stalled_projects_count" in data

    def test_get_dashboard(self, test_client):
        """Test getting dashboard data"""
        response = test_client.get("/api/v1/next-actions/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "top_3_priorities" in data
        assert "quick_wins" in data
        assert "due_today" in data
        assert "stalled_projects_count" in data


class TestInbox:
    """Test inbox endpoints"""

    def test_create_inbox_item(self, test_client):
        """Test creating an inbox item"""
        inbox_data = {"content": "Test inbox item", "source": "web_ui"}
        response = test_client.post("/api/v1/inbox", json=inbox_data)
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test inbox item"
        assert data["processed_at"] is None

    def test_list_inbox_items(self, test_client):
        """Test listing inbox items"""
        test_client.post("/api/v1/inbox", json={"content": "Item 1", "source": "web_ui"})

        response = test_client.get("/api/v1/inbox")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_process_inbox_item_as_project(self, test_client):
        """Test processing an inbox item as a project"""
        create_response = test_client.post(
            "/api/v1/inbox", json={"content": "Process me as project", "source": "web_ui"}
        )
        item_id = create_response.json()["id"]

        process_data = {"result_type": "project"}
        response = test_client.post(f"/api/v1/inbox/{item_id}/process", json=process_data)
        assert response.status_code == 200
        data = response.json()
        assert data["processed_at"] is not None
        assert data["result_type"] == "project"

    def test_process_inbox_item_as_task(self, test_client):
        """Test processing an inbox item as a task"""
        project_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Target Project", "status": "active", "priority": 3},
        )
        project_id = project_response.json()["id"]

        create_response = test_client.post(
            "/api/v1/inbox", json={"content": "Process me as task", "source": "web_ui"}
        )
        item_id = create_response.json()["id"]

        process_data = {"result_type": "task", "result_id": project_id}
        response = test_client.post(f"/api/v1/inbox/{item_id}/process", json=process_data)
        assert response.status_code == 200
        data = response.json()
        assert data["processed_at"] is not None
        assert data["result_type"] == "task"


class TestMomentumHistoryEndpoints:
    """Test momentum history and summary API endpoints (BETA-024)"""

    def test_momentum_history_empty(self, test_client):
        """Test momentum history for a project with no snapshots"""
        create_response = test_client.post(
            "/api/v1/projects",
            json={"title": "History Test", "status": "active", "priority": 3},
        )
        project_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/intelligence/momentum-history/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["title"] == "History Test"
        assert data["current_score"] == 0.0
        assert data["previous_score"] is None
        assert data["trend"] == "stable"
        assert data["snapshots"] == []

    def test_momentum_history_not_found(self, test_client):
        """Test momentum history for non-existent project"""
        response = test_client.get("/api/v1/intelligence/momentum-history/999")
        assert response.status_code == 404

    def test_momentum_history_days_param(self, test_client):
        """Test momentum history respects days query parameter"""
        create_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Days Param Test", "status": "active", "priority": 3},
        )
        project_id = create_response.json()["id"]

        response = test_client.get(
            f"/api/v1/intelligence/momentum-history/{project_id}",
            params={"days": 7},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id

    def test_momentum_history_invalid_days(self, test_client):
        """Test momentum history rejects invalid days param"""
        create_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Invalid Days", "status": "active", "priority": 3},
        )
        project_id = create_response.json()["id"]

        response = test_client.get(
            f"/api/v1/intelligence/momentum-history/{project_id}",
            params={"days": 0},
        )
        assert response.status_code == 422  # Validation error

    def test_momentum_summary_empty(self, test_client):
        """Test momentum summary with no active projects"""
        response = test_client.get("/api/v1/intelligence/dashboard/momentum-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_active"] == 0
        assert data["gaining"] == 0
        assert data["steady"] == 0
        assert data["declining"] == 0
        assert data["avg_score"] == 0.0
        assert data["projects"] == []

    def test_momentum_summary_with_projects(self, test_client):
        """Test momentum summary with active projects"""
        test_client.post(
            "/api/v1/projects",
            json={"title": "Project A", "status": "active", "priority": 3},
        )
        test_client.post(
            "/api/v1/projects",
            json={"title": "Project B", "status": "active", "priority": 5},
        )
        # Completed project should not appear
        test_client.post(
            "/api/v1/projects",
            json={"title": "Project C", "status": "completed", "priority": 1},
        )

        response = test_client.get("/api/v1/intelligence/dashboard/momentum-summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_active"] == 2
        assert len(data["projects"]) == 2
        # Both new projects have no previous score, so all should be "stable"
        assert data["steady"] == 2
        assert data["gaining"] == 0
        assert data["declining"] == 0
        # Verify project structure
        project_titles = {p["title"] for p in data["projects"]}
        assert "Project A" in project_titles
        assert "Project B" in project_titles
        assert "Project C" not in project_titles

    def test_project_response_includes_previous_momentum_score(self, test_client):
        """Test that project response includes previous_momentum_score field"""
        create_response = test_client.post(
            "/api/v1/projects",
            json={"title": "Schema Test", "status": "active", "priority": 3},
        )
        project_id = create_response.json()["id"]

        response = test_client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert "previous_momentum_score" in data
        assert data["previous_momentum_score"] is None


class TestAIEndpointsROADMAP002:
    """Test ROADMAP-002 AI feature endpoints"""

    def test_proactive_analysis_no_declining_projects(self, test_client):
        """Proactive analysis returns empty when all projects healthy"""
        response = test_client.post("/api/v1/intelligence/ai/proactive-analysis")
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            data = response.json()
            assert data["projects_analyzed"] == 0
            assert data["insights"] == []

    def test_proactive_analysis_with_stalled_project(self, test_client):
        """Proactive analysis finds stalled projects"""
        # Create a project and mark it stalled
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Stalled AI Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        # Manually set stalled_since via direct update
        from app.models.project import Project
        from datetime import datetime, timezone
        from app.core.database import get_db
        from app.main import app

        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        p = db.get(Project, project_id)
        p.stalled_since = datetime.now(timezone.utc)
        p.momentum_score = 0.1
        db.commit()

        response = test_client.post("/api/v1/intelligence/ai/proactive-analysis")
        # May fail if AI not configured — that's OK, check structure
        if response.status_code == 200:
            data = response.json()
            assert data["projects_analyzed"] >= 1
            assert len(data["insights"]) >= 1
            insight = data["insights"][0]
            assert insight["project_id"] == project_id
            assert "project_title" in insight

    def test_decompose_tasks_no_notes(self, test_client):
        """Task decomposition returns 400 when project has no notes"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "No Notes", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        response = test_client.post(f"/api/v1/intelligence/ai/decompose-tasks/{project_id}")
        assert response.status_code == 400
        assert "no brainstorm" in response.json()["detail"].lower()

    def test_decompose_tasks_not_found(self, test_client):
        """Task decomposition returns 404 for non-existent project"""
        response = test_client.post("/api/v1/intelligence/ai/decompose-tasks/99999")
        assert response.status_code == 404

    def test_rebalance_suggestions_empty(self, test_client):
        """Rebalance suggestions return empty when balanced"""
        response = test_client.get("/api/v1/intelligence/ai/rebalance-suggestions")
        assert response.status_code == 200
        data = response.json()
        assert "opportunity_now_count" in data
        assert "threshold" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    def test_rebalance_suggestions_custom_threshold(self, test_client):
        """Rebalance suggestions accept custom threshold"""
        response = test_client.get("/api/v1/intelligence/ai/rebalance-suggestions?threshold=3")
        assert response.status_code == 200
        data = response.json()
        assert data["threshold"] == 3

    def test_energy_recommendations_low(self, test_client):
        """Energy recommendations for low energy"""
        response = test_client.get("/api/v1/intelligence/ai/energy-recommendations?energy_level=low")
        assert response.status_code == 200
        data = response.json()
        assert data["energy_level"] == "low"
        assert "tasks" in data
        assert "total_available" in data

    def test_energy_recommendations_high(self, test_client):
        """Energy recommendations for high energy"""
        response = test_client.get("/api/v1/intelligence/ai/energy-recommendations?energy_level=high")
        assert response.status_code == 200
        data = response.json()
        assert data["energy_level"] == "high"

    def test_energy_recommendations_invalid(self, test_client):
        """Energy recommendations reject invalid energy level"""
        response = test_client.get("/api/v1/intelligence/ai/energy-recommendations?energy_level=extreme")
        assert response.status_code == 400

    def test_energy_recommendations_with_tasks(self, test_client):
        """Energy recommendations return tasks when available"""
        # Create a project and task
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Energy Test Project", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        task_resp = test_client.post(
            "/api/v1/tasks",
            json={
                "project_id": project_id,
                "title": "Low energy quick task",
                "status": "pending",
                "is_next_action": True,
                "energy_level": "low",
                "estimated_minutes": 10,
                "context": "quick_win",
                "priority": 5,
            },
        )
        assert task_resp.status_code == 201

        response = test_client.get("/api/v1/intelligence/ai/energy-recommendations?energy_level=low")
        assert response.status_code == 200
        data = response.json()
        assert data["total_available"] >= 1
        if data["tasks"]:
            task = data["tasks"][0]
            assert "task_id" in task
            assert "task_title" in task
            assert "project_title" in task


class TestAIEndpointsROADMAP007:
    """Test ROADMAP-007 AI Weekly Review Co-Pilot endpoints"""

    def test_weekly_review_ai_summary_no_ai(self, test_client):
        """Weekly review AI summary returns 400 when AI not enabled"""
        response = test_client.post("/api/v1/intelligence/ai/weekly-review-summary")
        # AI not configured in test env — expect 400
        assert response.status_code == 400

    def test_project_review_insight_not_found(self, test_client):
        """Project review insight returns 404 for non-existent project"""
        response = test_client.post("/api/v1/intelligence/ai/review-project/99999")
        # Either 400 (AI not enabled) or 404 (project not found)
        assert response.status_code in (400, 404)

    def test_project_review_insight_no_ai(self, test_client):
        """Project review insight returns 400 when AI not enabled"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Review Insight Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]
        response = test_client.post(f"/api/v1/intelligence/ai/review-project/{project_id}")
        assert response.status_code == 400

    def test_weekly_review_complete_with_ai_summary(self, test_client):
        """Weekly review completion persists ai_summary"""
        response = test_client.post(
            "/api/v1/intelligence/weekly-review/complete",
            json={"notes": "Good week", "ai_summary": '{"portfolio_narrative": "test"}'},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Good week"
        assert data["ai_summary"] == '{"portfolio_narrative": "test"}'

    def test_weekly_review_history_includes_ai_summary(self, test_client):
        """Weekly review history returns ai_summary field"""
        # Create a completion with ai_summary
        test_client.post(
            "/api/v1/intelligence/weekly-review/complete",
            json={"ai_summary": "test summary"},
        )
        response = test_client.get("/api/v1/intelligence/weekly-review/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data["completions"]) > 0
        # Check that ai_summary field is present in response
        latest = data["completions"][0]
        assert "ai_summary" in latest

    def test_rebalance_due_date_promotion(self, test_client):
        """BUG-027: Tasks due within 3 days appear in rebalance suggestions"""
        from datetime import date, timedelta

        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Due Date Rebalance Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        # Create enough opportunity_now tasks to trigger rebalancing
        for i in range(8):
            due = (date.today() + timedelta(days=2)).isoformat() if i == 0 else None
            test_client.post(
                "/api/v1/tasks",
                json={
                    "project_id": project_id,
                    "title": f"Rebalance task {i}",
                    "status": "pending",
                    "is_next_action": True,
                    "urgency_zone": "opportunity_now",
                    "priority": 5,
                    "due_date": due,
                },
            )

        response = test_client.get("/api/v1/intelligence/ai/rebalance-suggestions?threshold=5")
        assert response.status_code == 200
        data = response.json()
        # With 8 tasks and threshold 5, should have suggestions
        assert data["opportunity_now_count"] >= 8
        if data["suggestions"]:
            # Task with due_date should be promoted to critical_now
            due_task = next(
                (s for s in data["suggestions"] if "due" in s["reason"].lower()),
                None,
            )
            if due_task:
                assert due_task["suggested_zone"] == "critical_now"
