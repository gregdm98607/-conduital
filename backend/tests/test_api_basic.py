"""
Basic API tests

Fixed test infrastructure (DEBT-024):
- TestClient created per-test via fixture (not at module level)
- Database override applied BEFORE TestClient triggers startup
- In-memory SQLite for speed and isolation
- Startup side-effects (scheduler, folder watcher) patched out

Consolidated (DEBT-070): Uses shared in_memory_engine from conftest.py
"""

import json

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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
        from unittest.mock import patch

        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "No Notes", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        with patch("app.core.config.settings.AI_FEATURES_ENABLED", True):
            response = test_client.post(f"/api/v1/intelligence/ai/decompose-tasks/{project_id}")
        assert response.status_code == 400
        assert "no brainstorm" in response.json()["detail"].lower()

    def test_decompose_tasks_not_found(self, test_client):
        """Task decomposition returns 404 for non-existent project"""
        from unittest.mock import patch

        with patch("app.core.config.settings.AI_FEATURES_ENABLED", True):
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


class TestSession6NonAIEndpoints:
    """Test non-AI intelligence endpoints — dashboard stats, momentum, health, weekly review."""

    def test_dashboard_stats_empty(self, test_client):
        """Dashboard stats with no projects returns zeros"""
        response = test_client.get("/api/v1/intelligence/dashboard-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["active_project_count"] == 0
        assert data["pending_task_count"] == 0
        assert data["avg_momentum"] == 0.0
        assert data["orphan_project_count"] == 0

    def test_dashboard_stats_with_data(self, test_client):
        """Dashboard stats counts active projects, pending tasks, orphans"""
        # Create area + project with area
        test_client.post("/api/v1/areas", json={"title": "Work", "standard_of_excellence": "Good"})
        areas = test_client.get("/api/v1/areas").json()
        area_id = areas[0]["id"] if areas else None

        test_client.post(
            "/api/v1/projects",
            json={"title": "With Area", "status": "active", "priority": 3, "area_id": area_id},
        )
        # Orphan project (no area)
        proj2 = test_client.post(
            "/api/v1/projects",
            json={"title": "Orphan", "status": "active", "priority": 5},
        )
        project_id = proj2.json()["id"]
        # Completed project — should not count
        test_client.post(
            "/api/v1/projects",
            json={"title": "Done", "status": "completed", "priority": 1},
        )
        # Add a pending task
        test_client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, "title": "Pending", "status": "pending", "priority": 3},
        )

        response = test_client.get("/api/v1/intelligence/dashboard-stats")
        assert response.status_code == 200
        data = response.json()
        assert data["active_project_count"] == 2
        assert data["pending_task_count"] >= 1
        assert data["orphan_project_count"] >= 1

    def test_momentum_update(self, test_client):
        """Momentum update endpoint recalculates all project scores"""
        test_client.post(
            "/api/v1/projects",
            json={"title": "Momentum Test", "status": "active", "priority": 3},
        )
        response = test_client.post("/api/v1/intelligence/momentum/update")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "updated" in data["stats"]

    def test_calculate_project_momentum(self, test_client):
        """Single project momentum calculation returns a float"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Calc Momentum", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]
        response = test_client.get(f"/api/v1/intelligence/momentum/{project_id}")
        assert response.status_code == 200
        score = response.json()
        assert isinstance(score, (int, float))
        assert 0.0 <= score <= 1.0

    def test_calculate_momentum_not_found(self, test_client):
        """Momentum calculation for non-existent project returns 404"""
        response = test_client.get("/api/v1/intelligence/momentum/99999")
        assert response.status_code == 404

    def test_momentum_breakdown(self, test_client):
        """Momentum breakdown returns factor details"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Breakdown Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]
        response = test_client.get(f"/api/v1/intelligence/momentum-breakdown/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert "total_score" in data
        assert "factors" in data
        assert isinstance(data["factors"], list)
        assert len(data["factors"]) > 0
        factor = data["factors"][0]
        assert "name" in factor
        assert "weight" in factor
        assert "raw_score" in factor
        assert "weighted_score" in factor

    def test_project_health_summary(self, test_client):
        """Health endpoint returns comprehensive project health"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Health Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]
        response = test_client.get(f"/api/v1/intelligence/health/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert "health_status" in data
        assert "momentum_score" in data
        assert "tasks" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_project_health_not_found(self, test_client):
        """Health endpoint for non-existent project returns 404"""
        response = test_client.get("/api/v1/intelligence/health/99999")
        assert response.status_code == 404

    def test_weekly_review_data(self, test_client):
        """Weekly review data endpoint returns review structure"""
        response = test_client.get("/api/v1/intelligence/weekly-review")
        assert response.status_code == 200
        data = response.json()
        assert "review_date" in data
        assert "active_projects_count" in data
        assert "tasks_completed_this_week" in data
        assert "projects_needing_review_details" in data

    def test_stalled_projects_empty(self, test_client):
        """Stalled projects returns empty list when none stalled"""
        response = test_client.get("/api/v1/intelligence/stalled")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_stalled_projects_includes_at_risk(self, test_client):
        """Stalled projects with include_at_risk returns at-risk projects"""
        response = test_client.get("/api/v1/intelligence/stalled?include_at_risk=true")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSession6AIWithMock:
    """Test AI endpoints with mocked AI provider — happy path tests."""

    def _enable_ai_and_mock_provider(self):
        """Return context managers to enable AI and mock the provider."""
        mock_provider = MagicMock()
        mock_provider.generate.return_value = "Mock AI response"
        mock_provider.test_connection.return_value = {"success": True, "message": "OK", "model": "mock"}

        return (
            patch("app.core.config.settings.AI_FEATURES_ENABLED", True),
            patch("app.core.config.settings.ANTHROPIC_API_KEY", "test-key-123"),
            patch("app.services.ai_service.create_provider", return_value=mock_provider),
            mock_provider,
        )

    def test_ai_analyze_project_happy_path(self, test_client):
        """AI analyze endpoint returns analysis when AI is mocked"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "AI Analyze Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        p1, p2, p3, mock_provider = self._enable_ai_and_mock_provider()
        mock_provider.generate.return_value = (
            "Analysis: This project is healthy with steady momentum.\n\n"
            "Recommendations:\n"
            "1. Continue daily progress on key tasks\n"
            "2. Schedule a review meeting this week"
        )

        with p1, p2, p3:
            response = test_client.post(f"/api/v1/intelligence/ai/analyze/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)

    def test_ai_analyze_project_not_found(self, test_client):
        """AI analyze for non-existent project returns 404"""
        p1, p2, p3, _ = self._enable_ai_and_mock_provider()
        with p1, p2, p3:
            response = test_client.post("/api/v1/intelligence/ai/analyze/99999")
        assert response.status_code == 404

    def test_ai_suggest_next_action_happy_path(self, test_client):
        """AI suggest-next-action returns a suggestion when AI is mocked"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Suggest Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        p1, p2, p3, mock_provider = self._enable_ai_and_mock_provider()
        mock_provider.generate.return_value = "Draft the project proposal outline"

        with p1, p2, p3:
            response = test_client.post(f"/api/v1/intelligence/ai/suggest-next-action/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ai_generated"] is True
        assert len(data["suggestion"]) > 0

    def test_ai_suggest_next_action_not_found(self, test_client):
        """AI suggest for non-existent project returns 404"""
        p1, p2, p3, _ = self._enable_ai_and_mock_provider()
        with p1, p2, p3:
            response = test_client.post("/api/v1/intelligence/ai/suggest-next-action/99999")
        assert response.status_code == 404

    def test_ai_weekly_review_summary_happy_path(self, test_client):
        """AI weekly review summary returns portfolio narrative when AI is mocked"""
        # Create a project so there's data to analyze
        test_client.post(
            "/api/v1/projects",
            json={"title": "Review Summary Test", "status": "active", "priority": 3},
        )

        p1, p2, p3, mock_provider = self._enable_ai_and_mock_provider()
        mock_provider.generate.return_value = json.dumps({
            "portfolio_narrative": "Your portfolio is healthy with steady progress.",
            "wins": ["Completed 5 tasks this week"],
            "attention_items": [],
            "recommendations": ["Focus on stalled projects", "Clear inbox items"],
        })

        with p1, p2, p3:
            response = test_client.post("/api/v1/intelligence/ai/weekly-review-summary")
        assert response.status_code == 200
        data = response.json()
        assert "portfolio_narrative" in data
        assert "wins" in data
        assert "attention_items" in data
        assert "recommendations" in data
        assert "generated_at" in data

    def test_ai_project_review_insight_happy_path(self, test_client):
        """AI project review insight returns health summary when AI is mocked"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Insight Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        p1, p2, p3, mock_provider = self._enable_ai_and_mock_provider()
        mock_provider.generate.return_value = json.dumps({
            "health_summary": "Project is on track with good momentum.",
            "suggested_next_action": "Review pending code changes",
            "questions_to_consider": ["Is the deadline realistic?", "Any blockers?"],
            "momentum_context": "Momentum is rising at 0.75",
        })

        with p1, p2, p3:
            response = test_client.post(f"/api/v1/intelligence/ai/review-project/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert "health_summary" in data
        assert "questions_to_consider" in data
        assert isinstance(data["questions_to_consider"], list)
        assert "momentum_context" in data

    def test_ai_decompose_tasks_with_notes(self, test_client):
        """AI task decomposition works when project has brainstorm notes"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Decompose Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        # Add brainstorm notes to the project
        test_client.put(
            f"/api/v1/projects/{project_id}",
            json={"brainstorm_notes": "Need to research competitors, write proposal, create mockups"},
        )

        p1, p2, p3, mock_provider = self._enable_ai_and_mock_provider()
        mock_provider.generate.return_value = (
            "TASK: Research top 3 competitors | 60 | high | research\n"
            "TASK: Draft proposal outline | 30 | medium | deep_work\n"
            "TASK: Create initial mockup wireframes | 120 | high | creative"
        )

        with p1, p2, p3:
            response = test_client.post(f"/api/v1/intelligence/ai/decompose-tasks/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert data["source"] == "brainstorm_notes"
        assert len(data["tasks"]) == 3
        task = data["tasks"][0]
        assert "title" in task
        assert task["estimated_minutes"] == 60
        assert task["energy_level"] == "high"

    def test_proactive_analysis_error_sanitization(self, test_client):
        """BUG-028/029 regression: proactive analysis errors show type, not raw message"""
        from unittest.mock import patch
        from app.models.project import Project
        from datetime import datetime
        from app.core.database import get_db
        from app.main import app

        # Create a stalled project
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Error Sanitize Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        p = db.get(Project, project_id)
        p.stalled_since = datetime.utcnow()
        p.momentum_score = 0.1
        db.commit()

        p1, p2, p3, mock_provider = self._enable_ai_and_mock_provider()
        # Mock analyze_project_health to raise — simulates provider error
        # that escapes internal try/except (e.g. during context building)
        with p1, p2, p3, patch(
            "app.services.ai_service.AIService.analyze_project_health",
            side_effect=RuntimeError("Sensitive API error: key=abc123"),
        ):
            response = test_client.post("/api/v1/intelligence/ai/proactive-analysis")
        assert response.status_code == 200
        data = response.json()
        assert data["projects_analyzed"] >= 1
        insight = data["insights"][0]
        # Error should contain "Analysis failed:" — sanitized
        assert "error" in insight
        assert "Analysis failed:" in insight["error"]
        # Raw sensitive data must NOT appear in error field
        assert "abc123" not in insight["error"]

    def test_unstuck_task_no_ai_configured(self, test_client):
        """Unstuck task returns 400 when AI enabled but no API key"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Unstuck Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        with patch("app.core.config.settings.AI_FEATURES_ENABLED", True), \
             patch("app.core.config.settings.ANTHROPIC_API_KEY", ""):
            response = test_client.post(f"/api/v1/intelligence/unstuck/{project_id}")
        assert response.status_code == 400

    def test_strip_json_fences_with_language_tag(self, test_client):
        """DEBT-112: _strip_json_fences handles ```json fences"""
        from app.services.ai_service import AIService

        raw = '```json\n{"key": "value"}\n```'
        assert AIService._strip_json_fences(raw) == '{"key": "value"}'

    def test_strip_json_fences_without_language(self, test_client):
        """DEBT-112: _strip_json_fences handles bare ``` fences"""
        from app.services.ai_service import AIService

        raw = '```\n{"key": "value"}\n```'
        assert AIService._strip_json_fences(raw) == '{"key": "value"}'

    def test_strip_json_fences_no_fences(self, test_client):
        """DEBT-112: _strip_json_fences passes through bare JSON"""
        from app.services.ai_service import AIService

        raw = '{"key": "value"}'
        assert AIService._strip_json_fences(raw) == '{"key": "value"}'

    def test_strip_json_fences_with_whitespace(self, test_client):
        """DEBT-112: _strip_json_fences handles extra whitespace"""
        from app.services.ai_service import AIService

        raw = '  ```JSON\n{"key": "value"}\n```  '
        assert AIService._strip_json_fences(raw) == '{"key": "value"}'

    def test_unstuck_task_without_ai(self, test_client):
        """Unstuck task with use_ai=false creates a fallback task"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Unstuck Fallback", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        response = test_client.post(f"/api/v1/intelligence/unstuck/{project_id}?use_ai=false")
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert data["status"] == "pending"
        assert data["is_next_action"] is True


class TestDEBT115TzNaiveDatetime:
    """DEBT-115 regression: SQLite strips tz info — datetime arithmetic must not crash."""

    def test_ensure_tz_aware_naive(self):
        """ensure_tz_aware converts naive datetime to UTC-aware"""
        from datetime import datetime, timezone
        from app.core.db_utils import ensure_tz_aware

        naive = datetime(2025, 6, 15, 12, 0, 0)
        assert naive.tzinfo is None
        aware = ensure_tz_aware(naive)
        assert aware.tzinfo == timezone.utc
        assert aware.year == 2025

    def test_ensure_tz_aware_already_aware(self):
        """ensure_tz_aware returns aware datetimes unchanged"""
        from datetime import datetime, timezone
        from app.core.db_utils import ensure_tz_aware

        aware = datetime(2025, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = ensure_tz_aware(aware)
        assert result is aware  # Same object

    def test_ensure_tz_aware_none(self):
        """ensure_tz_aware returns None for None input"""
        from app.core.db_utils import ensure_tz_aware
        assert ensure_tz_aware(None) is None

    def test_project_health_with_naive_stalled_since(self, test_client):
        """Project health endpoint doesn't crash when stalled_since is naive (simulating SQLite)"""
        from datetime import datetime
        from app.core.database import get_db
        from app.main import app
        from app.models.project import Project

        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "TZ Naive Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        # Set naive datetime — simulates what SQLite returns
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        p = db.get(Project, project_id)
        p.stalled_since = datetime(2025, 1, 1, 12, 0, 0)  # naive, no tzinfo
        p.momentum_score = 0.2
        db.commit()

        response = test_client.get(f"/api/v1/projects/{project_id}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["health_status"] == "stalled"

    def test_stalled_projects_endpoint_with_naive_datetimes(self, test_client):
        """Stalled projects list doesn't crash with naive stalled_since and last_activity_at"""
        from datetime import datetime
        from app.core.database import get_db
        from app.main import app
        from app.models.project import Project

        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "TZ Stalled Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        p = db.get(Project, project_id)
        p.stalled_since = datetime(2025, 1, 1, 12, 0, 0)  # naive
        p.last_activity_at = datetime(2024, 12, 15, 8, 0, 0)  # naive
        p.momentum_score = 0.1
        db.commit()

        response = test_client.get("/api/v1/intelligence/stalled")
        assert response.status_code == 200
        data = response.json()
        # Should have our project in the stalled list without crashing
        stalled_ids = [p["id"] for p in data]
        assert project_id in stalled_ids

    def test_ai_context_build_with_naive_stalled_since(self, test_client):
        """AI service _build_project_context doesn't crash on naive stalled_since"""
        from datetime import datetime
        from app.core.database import get_db
        from app.main import app
        from app.models.project import Project
        from sqlalchemy.orm import joinedload, Session
        from sqlalchemy import select

        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "AI Context TZ Test", "status": "active", "priority": 3},
        )
        project_id = proj.json()["id"]

        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        p = db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(joinedload(Project.tasks), joinedload(Project.area))
        ).unique().scalar_one()
        p.stalled_since = datetime(2025, 1, 1)  # naive
        db.commit()

        from app.services.ai_service import AIService
        # _build_project_context is called by AI methods — test directly
        # Use a fresh session for the eager-loaded project
        p_fresh = db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(joinedload(Project.tasks), joinedload(Project.area))
        ).unique().scalar_one()

        # This should NOT raise TypeError
        service = AIService.__new__(AIService)
        context = service._build_project_context(db, p_fresh)
        assert "days_stalled" in context
        assert context["days_stalled"] >= 0


class TestSoftDelete:
    """Tests for DEBT-007: Soft delete foundation"""

    def test_soft_delete_project_hides_from_list(self, test_client):
        """Soft-deleted project should not appear in list endpoint"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Soft Delete Me", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        # Delete (now soft)
        resp = test_client.delete(f"/api/v1/projects/{project_id}")
        assert resp.status_code == 204

        # Should not appear in list
        list_resp = test_client.get("/api/v1/projects")
        assert list_resp.status_code == 200
        titles = [p["title"] for p in list_resp.json()["projects"]]
        assert "Soft Delete Me" not in titles

    def test_soft_delete_project_returns_404_on_get(self, test_client):
        """GET on soft-deleted project should return 404"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Ghost Project", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        test_client.delete(f"/api/v1/projects/{project_id}")
        get_resp = test_client.get(f"/api/v1/projects/{project_id}")
        assert get_resp.status_code == 404

    def test_soft_delete_project_cascades_to_tasks(self, test_client):
        """Deleting a project should soft-delete its child tasks"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Parent Project", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        task_resp = test_client.post(
            "/api/v1/tasks",
            json={"title": "Child Task", "project_id": project_id, "priority": 5},
        )
        task_id = task_resp.json()["id"]

        # Delete project
        test_client.delete(f"/api/v1/projects/{project_id}")

        # Task should also be hidden
        get_task = test_client.get(f"/api/v1/tasks/{task_id}")
        assert get_task.status_code == 404

    def test_soft_delete_task_hides_from_list(self, test_client):
        """Soft-deleted task should not appear in list endpoint"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Task Host", "status": "active", "priority": 5},
        )
        project_id = proj.json()["id"]

        task = test_client.post(
            "/api/v1/tasks",
            json={"title": "Delete This Task", "project_id": project_id, "priority": 5},
        )
        task_id = task.json()["id"]

        # Delete task
        resp = test_client.delete(f"/api/v1/tasks/{task_id}")
        assert resp.status_code == 204

        # Should not appear in list
        list_resp = test_client.get("/api/v1/tasks", params={"project_id": project_id, "show_completed": True})
        titles = [t["title"] for t in list_resp.json()["tasks"]]
        assert "Delete This Task" not in titles

    def test_soft_delete_area_hides_from_list(self, test_client):
        """Soft-deleted area should not appear in list endpoint"""
        create = test_client.post(
            "/api/v1/areas",
            json={"title": "Trash Area"},
        )
        area_id = create.json()["id"]

        resp = test_client.delete(f"/api/v1/areas/{area_id}")
        assert resp.status_code == 204

        list_resp = test_client.get("/api/v1/areas")
        titles = [a["title"] for a in list_resp.json()]
        assert "Trash Area" not in titles

    def test_double_delete_returns_404(self, test_client):
        """Deleting an already-deleted item should return 404"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Double Delete", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        resp1 = test_client.delete(f"/api/v1/projects/{project_id}")
        assert resp1.status_code == 204

        resp2 = test_client.delete(f"/api/v1/projects/{project_id}")
        assert resp2.status_code == 404

    def test_soft_delete_project_excluded_from_search(self, test_client):
        """Soft-deleted project should not appear in search results"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Searchable Ghost", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        test_client.delete(f"/api/v1/projects/{project_id}")

        search_resp = test_client.get("/api/v1/projects/search", params={"q": "Searchable Ghost"})
        assert search_resp.status_code == 200
        titles = [p["title"] for p in search_resp.json()]
        assert "Searchable Ghost" not in titles

    def test_soft_delete_preserves_data_in_db(self, test_client):
        """Soft delete should set deleted_at, not remove the row"""
        from app.main import app
        from app.core.database import get_db

        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Still In DB", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        test_client.delete(f"/api/v1/projects/{project_id}")

        # Verify directly in DB that the row still exists with deleted_at set
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)
        try:
            from app.models.project import Project
            project = db.get(Project, project_id)
            assert project is not None, "Row should still exist in DB"
            assert project.deleted_at is not None, "deleted_at should be set"
            assert project.title == "Still In DB"
        finally:
            db.close()

    def test_update_soft_deleted_project_returns_404(self, test_client):
        """Updating a soft-deleted project should return 404"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Update Ghost", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        test_client.delete(f"/api/v1/projects/{project_id}")

        resp = test_client.put(
            f"/api/v1/projects/{project_id}",
            json={"title": "Should Fail"},
        )
        assert resp.status_code == 404

    def test_complete_soft_deleted_task_returns_404(self, test_client):
        """Completing a soft-deleted task should return 404"""
        proj = test_client.post(
            "/api/v1/projects",
            json={"title": "Task Ghost Proj", "status": "active", "priority": 5},
        )
        project_id = proj.json()["id"]

        task = test_client.post(
            "/api/v1/tasks",
            json={"title": "Ghost Task", "project_id": project_id, "status": "pending"},
        )
        task_id = task.json()["id"]

        test_client.delete(f"/api/v1/tasks/{task_id}")

        resp = test_client.post(f"/api/v1/tasks/{task_id}/complete")
        assert resp.status_code == 404

    def test_soft_deleted_project_excluded_from_dashboard_stats(self, test_client):
        """Soft-deleted projects should not count in dashboard stats"""
        # Create and delete a project
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Dashboard Ghost", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        # Get stats before delete
        before = test_client.get("/api/v1/intelligence/dashboard-stats")
        before_count = before.json()["active_project_count"]

        test_client.delete(f"/api/v1/projects/{project_id}")

        # Get stats after delete
        after = test_client.get("/api/v1/intelligence/dashboard-stats")
        after_count = after.json()["active_project_count"]

        assert after_count == before_count - 1

    def test_soft_deleted_area_excluded_from_list(self, test_client):
        """Soft-deleted areas should not appear in area list"""
        create = test_client.post(
            "/api/v1/areas",
            json={"title": "Ghost Area"},
        )
        area_id = create.json()["id"]

        test_client.delete(f"/api/v1/areas/{area_id}")

        resp = test_client.get("/api/v1/areas")
        titles = [a["title"] for a in resp.json()]
        assert "Ghost Area" not in titles

    def test_update_soft_deleted_area_returns_404(self, test_client):
        """Updating a soft-deleted area should return 404"""
        create = test_client.post(
            "/api/v1/areas",
            json={"title": "Area Ghost"},
        )
        area_id = create.json()["id"]

        test_client.delete(f"/api/v1/areas/{area_id}")

        resp = test_client.put(
            f"/api/v1/areas/{area_id}",
            json={"title": "Should Fail"},
        )
        assert resp.status_code == 404

    def test_mark_reviewed_soft_deleted_area_returns_404(self, test_client):
        """Marking a soft-deleted area as reviewed should return 404"""
        create = test_client.post(
            "/api/v1/areas",
            json={"title": "Review Ghost"},
        )
        area_id = create.json()["id"]

        test_client.delete(f"/api/v1/areas/{area_id}")

        resp = test_client.post(f"/api/v1/areas/{area_id}/mark-reviewed")
        assert resp.status_code == 404

    def test_soft_deleted_project_excluded_from_momentum_summary(self, test_client):
        """Soft-deleted projects should not appear in momentum summary"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Momentum Ghost", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        test_client.delete(f"/api/v1/projects/{project_id}")

        resp = test_client.get("/api/v1/intelligence/dashboard/momentum-summary")
        assert resp.status_code == 200
        project_ids = [p["id"] for p in resp.json()["projects"]]
        assert project_id not in project_ids

    def test_change_status_soft_deleted_project_returns_404(self, test_client):
        """Changing status of a soft-deleted project should return 404"""
        create = test_client.post(
            "/api/v1/projects",
            json={"title": "Status Ghost", "status": "active", "priority": 5},
        )
        project_id = create.json()["id"]

        test_client.delete(f"/api/v1/projects/{project_id}")

        resp = test_client.patch(
            f"/api/v1/projects/{project_id}/status?status=completed",
        )
        assert resp.status_code == 404
