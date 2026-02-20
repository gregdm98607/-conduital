"""
Import service and API tests

BACKLOG-090: Data import from JSON backup.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models import Project, Task, Area, Goal, Vision, Context, InboxItem
from app.services.import_service import ImportService, ImportResult


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Minimal valid export fixture
# ---------------------------------------------------------------------------

def make_export(areas=None, goals=None, visions=None, contexts=None,
                projects=None, inbox_items=None):
    return {
        "metadata": {"export_version": "1.0.0", "app_version": "1.1.0",
                     "exported_at": "2026-01-01T00:00:00+00:00",
                     "commercial_mode": "basic",
                     "entity_counts": {"projects": 0, "tasks": 0, "areas": 0,
                                       "goals": 0, "visions": 0, "contexts": 0,
                                       "inbox_items": 0}},
        "areas": areas or [],
        "goals": goals or [],
        "visions": visions or [],
        "contexts": contexts or [],
        "projects": projects or [],
        "inbox_items": inbox_items or [],
    }


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidateExport:

    def test_valid_export_passes(self):
        errors = ImportService.validate_export(make_export())
        assert errors == []

    def test_not_a_dict_fails(self):
        errors = ImportService.validate_export([1, 2, 3])
        assert any("JSON object" in e for e in errors)

    def test_missing_metadata_fails(self):
        errors = ImportService.validate_export({"projects": []})
        assert any("metadata" in e for e in errors)

    def test_unsupported_version_fails(self):
        data = make_export()
        data["metadata"]["export_version"] = "9.9.9"
        errors = ImportService.validate_export(data)
        assert any("Unsupported" in e for e in errors)

    def test_projects_not_list_fails(self):
        data = make_export()
        data["projects"] = {"bad": "value"}
        errors = ImportService.validate_export(data)
        assert any("projects" in e for e in errors)


# ---------------------------------------------------------------------------
# Import service unit tests
# ---------------------------------------------------------------------------

class TestImportAreas:

    def test_imports_new_area(self, db_session: Session):
        data = make_export(areas=[{"id": 1, "title": "Health", "description": "Stay healthy"}])
        result = ImportService.import_from_json(data, db_session)
        assert result.areas_imported == 1
        assert result.areas_skipped == 0
        area = db_session.query(Area).filter_by(title="Health").first()
        assert area is not None
        assert area.description == "Stay healthy"

    def test_skips_existing_area_by_title(self, db_session: Session):
        db_session.add(Area(title="Health"))
        db_session.commit()
        data = make_export(areas=[{"id": 1, "title": "Health"}])
        result = ImportService.import_from_json(data, db_session)
        assert result.areas_imported == 0
        assert result.areas_skipped == 1
        assert db_session.query(Area).count() == 1

    def test_title_match_is_case_insensitive(self, db_session: Session):
        db_session.add(Area(title="health"))
        db_session.commit()
        data = make_export(areas=[{"id": 1, "title": "Health"}])
        result = ImportService.import_from_json(data, db_session)
        assert result.areas_skipped == 1

    def test_skips_area_with_empty_title(self, db_session: Session):
        data = make_export(areas=[{"id": 1, "title": ""}])
        result = ImportService.import_from_json(data, db_session)
        assert result.areas_skipped == 1
        assert len(result.warnings) == 1


class TestImportGoals:

    def test_imports_new_goal(self, db_session: Session):
        data = make_export(goals=[{"id": 1, "title": "Run a marathon",
                                   "timeframe": "1_year", "status": "active"}])
        result = ImportService.import_from_json(data, db_session)
        assert result.goals_imported == 1
        goal = db_session.query(Goal).first()
        assert goal.title == "Run a marathon"

    def test_skips_duplicate_goal(self, db_session: Session):
        db_session.add(Goal(title="Run a marathon", timeframe="1_year"))
        db_session.commit()
        data = make_export(goals=[{"id": 1, "title": "Run a marathon"}])
        result = ImportService.import_from_json(data, db_session)
        assert result.goals_skipped == 1


class TestImportProjects:

    def test_imports_project_with_tasks(self, db_session: Session):
        data = make_export(projects=[{
            "id": 10,
            "title": "Write book",
            "status": "active",
            "priority": 3,
            "tasks": [
                {"title": "Draft outline", "status": "pending", "priority": 5},
                {"title": "Write chapter 1", "status": "pending", "priority": 4},
            ],
        }])
        result = ImportService.import_from_json(data, db_session)
        assert result.projects_imported == 1
        assert result.tasks_imported == 2
        project = db_session.query(Project).filter_by(title="Write book").first()
        assert project is not None
        tasks = db_session.query(Task).filter_by(project_id=project.id).all()
        assert len(tasks) == 2

    def test_skips_duplicate_project_and_its_tasks(self, db_session: Session):
        db_session.add(Project(title="Write book", status="active", priority=3))
        db_session.commit()
        data = make_export(projects=[{
            "id": 10, "title": "Write book", "status": "active", "priority": 3,
            "tasks": [{"title": "Draft outline", "status": "pending", "priority": 5}],
        }])
        result = ImportService.import_from_json(data, db_session)
        assert result.projects_skipped == 1
        assert result.tasks_skipped == 1
        assert db_session.query(Task).count() == 0

    def test_area_fk_remapped_correctly(self, db_session: Session):
        # Area exists already (old_id=5, new_id will be different)
        existing_area = Area(title="Work")
        db_session.add(existing_area)
        db_session.commit()
        new_area_id = existing_area.id

        data = make_export(
            areas=[{"id": 5, "title": "Work"}],  # skipped but id_map populated
            projects=[{"id": 20, "title": "Launch product", "status": "active",
                       "priority": 1, "area_id": 5, "tasks": []}],
        )
        result = ImportService.import_from_json(data, db_session)
        assert result.projects_imported == 1
        project = db_session.query(Project).filter_by(title="Launch product").first()
        assert project.area_id == new_area_id

    def test_skips_task_with_empty_title(self, db_session: Session):
        data = make_export(projects=[{
            "id": 1, "title": "My project", "status": "active", "priority": 3,
            "tasks": [{"title": "", "status": "pending", "priority": 1}],
        }])
        result = ImportService.import_from_json(data, db_session)
        assert result.tasks_skipped == 1
        assert len(result.warnings) >= 1


class TestImportInboxItems:

    def test_imports_inbox_item(self, db_session: Session):
        data = make_export(inbox_items=[{"content": "Call dentist", "source": "web_ui"}])
        result = ImportService.import_from_json(data, db_session)
        assert result.inbox_items_imported == 1
        item = db_session.query(InboxItem).first()
        assert item.content == "Call dentist"

    def test_skips_inbox_item_with_empty_content(self, db_session: Session):
        data = make_export(inbox_items=[{"content": "", "source": "web_ui"}])
        result = ImportService.import_from_json(data, db_session)
        assert result.inbox_items_skipped == 1


class TestRoundTrip:

    def test_export_then_import_round_trip(self, db_session: Session):
        """Export data then re-import it — totals should match on second import."""
        from app.services.export_service import ExportService

        # Seed data
        area = Area(title="Health")
        db_session.add(area)
        db_session.commit()
        project = Project(title="Exercise daily", status="active",
                          priority=2, area_id=area.id)
        db_session.add(project)
        db_session.commit()
        db_session.add(Task(title="Morning run", project_id=project.id,
                            status="pending", priority=3))
        db_session.commit()

        # Export
        export_data = ExportService.export_full_json(db_session)
        data_dict = export_data.model_dump(mode="json")

        # First import: everything should be skipped (data already present)
        result1 = ImportService.import_from_json(data_dict, db_session)
        assert result1.projects_skipped == 1
        assert result1.tasks_skipped == 1
        assert result1.areas_skipped == 1

        # Second DB (fresh) — full import should succeed
        engine2 = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False},
                                poolclass=StaticPool)
        Base.metadata.create_all(bind=engine2)
        Session2 = sessionmaker(bind=engine2)
        db2 = Session2()
        result2 = ImportService.import_from_json(data_dict, db2)
        assert result2.projects_imported == 1
        assert result2.tasks_imported == 1
        assert result2.areas_imported == 1
        db2.close()
        Base.metadata.drop_all(bind=engine2)


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

class TestImportEndpoint:

    @pytest.fixture
    def test_client(self, in_memory_engine):
        from unittest.mock import patch, AsyncMock
        from fastapi.testclient import TestClient
        from sqlalchemy.orm import sessionmaker
        from app.core.database import get_db
        from app.models.base import Base

        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False,
                                           bind=in_memory_engine)
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
             patch("app.services.scheduler_service.run_urgency_zone_recalculation_now",
                   new_callable=AsyncMock):
            client = TestClient(app)
            yield client

        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=in_memory_engine)

    def test_import_valid_export_returns_200(self, test_client):
        data = make_export(projects=[{
            "id": 1, "title": "Test project", "status": "active", "priority": 3,
            "tasks": [{"title": "First task", "status": "pending", "priority": 5}],
        }])
        response = test_client.post("/api/v1/export/import", json=data)
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["projects_imported"] == 1
        assert body["tasks_imported"] == 1

    def test_import_invalid_json_returns_400(self, test_client):
        response = test_client.post(
            "/api/v1/export/import",
            content=b"not json at all",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_import_wrong_version_returns_422(self, test_client):
        data = make_export()
        data["metadata"]["export_version"] = "99.0.0"
        response = test_client.post("/api/v1/export/import", json=data)
        assert response.status_code == 422

    def test_import_skips_duplicates(self, test_client):
        data = make_export(projects=[{
            "id": 1, "title": "Dedup project", "status": "active", "priority": 3,
            "tasks": [],
        }])
        # First import
        r1 = test_client.post("/api/v1/export/import", json=data)
        assert r1.status_code == 200
        assert r1.json()["projects_imported"] == 1

        # Second import — same data
        r2 = test_client.post("/api/v1/export/import", json=data)
        assert r2.status_code == 200
        assert r2.json()["projects_imported"] == 0
        assert r2.json()["projects_skipped"] == 1
