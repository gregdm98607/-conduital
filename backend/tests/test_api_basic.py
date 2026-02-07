"""
Basic API tests

Fixed test infrastructure (DEBT-024):
- TestClient created per-test via fixture (not at module level)
- Database override applied BEFORE TestClient triggers startup
- In-memory SQLite for speed and isolation
- Startup side-effects (scheduler, folder watcher) patched out
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.models.base import Base


# Test database (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_client():
    """
    Create a TestClient with proper database override.

    This fixture:
    1. Creates an in-memory SQLite engine
    2. Creates all tables
    3. Overrides get_db dependency BEFORE creating TestClient
    4. Patches startup side-effects (scheduler, folder watcher, urgency recalc)
    5. Yields the TestClient for the test
    6. Cleans up after
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Share single connection for in-memory SQLite
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables before anything else
    Base.metadata.create_all(bind=engine)

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
    Base.metadata.drop_all(bind=engine)


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
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
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
