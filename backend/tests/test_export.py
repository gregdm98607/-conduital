"""
Export API tests

BACKLOG-074: Data Export/Backup feature tests

Note: These tests use direct database access to avoid startup event issues.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models import Project, Task, Area, Goal, Vision, InboxItem
from app.services.export_service import ExportService


# Test database (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


class TestExportService:
    """Test ExportService methods directly"""

    def test_get_entity_counts_empty(self, db_session: Session):
        """Test entity counts with empty database"""
        counts = ExportService.get_entity_counts(db_session)

        assert counts.projects == 0
        assert counts.tasks == 0
        assert counts.areas == 0
        assert counts.goals == 0
        assert counts.visions == 0
        assert counts.inbox_items == 0

    def test_get_entity_counts_with_data(self, db_session: Session):
        """Test entity counts with data"""
        # Add projects
        p1 = Project(title="Project 1", status="active", priority=1)
        p2 = Project(title="Project 2", status="active", priority=2)
        db_session.add_all([p1, p2])
        db_session.commit()

        # Add tasks
        t1 = Task(title="Task 1", project_id=p1.id, status="pending", priority=1)
        t2 = Task(title="Task 2", project_id=p1.id, status="completed", priority=2)
        db_session.add_all([t1, t2])

        # Add area
        a1 = Area(title="Health")
        db_session.add(a1)

        # Add goal
        g1 = Goal(title="Run marathon", timeframe="1_year")
        db_session.add(g1)

        db_session.commit()

        counts = ExportService.get_entity_counts(db_session)

        assert counts.projects == 2
        assert counts.tasks == 2
        assert counts.areas == 1
        assert counts.goals == 1

    def test_export_preview_structure(self, db_session: Session):
        """Test export preview returns correct structure"""
        preview = ExportService.get_export_preview(db_session)

        assert preview.entity_counts is not None
        assert preview.estimated_size_bytes >= 0
        assert preview.estimated_size_display is not None
        assert "json" in preview.available_formats
        assert "sqlite" in preview.available_formats

    def test_export_full_json_empty(self, db_session: Session):
        """Test full JSON export with empty database"""
        export_data = ExportService.export_full_json(db_session)

        # Check metadata
        assert export_data.metadata is not None
        assert export_data.metadata.export_version == "1.0.0"
        assert export_data.metadata.exported_at is not None

        # Check empty data sections
        assert export_data.areas == []
        assert export_data.goals == []
        assert export_data.visions == []
        assert export_data.contexts == []
        assert export_data.projects == []
        assert export_data.inbox_items == []

    def test_export_full_json_with_project_and_tasks(self, db_session: Session):
        """Test full JSON export with project and tasks"""
        # Create project
        project = Project(
            title="Test Project",
            description="Export test",
            status="active",
            priority=1,
        )
        db_session.add(project)
        db_session.commit()

        # Create tasks
        task1 = Task(
            title="Task 1",
            project_id=project.id,
            status="pending",
            priority=1,
        )
        task2 = Task(
            title="Task 2",
            project_id=project.id,
            status="completed",
            priority=2,
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        # Export
        export_data = ExportService.export_full_json(db_session)

        # Check counts
        assert export_data.metadata.entity_counts.projects == 1
        assert export_data.metadata.entity_counts.tasks == 2

        # Check project data
        assert len(export_data.projects) == 1
        exported_project = export_data.projects[0]
        assert exported_project["title"] == "Test Project"
        assert exported_project["description"] == "Export test"

        # Check nested tasks
        assert "tasks" in exported_project
        assert len(exported_project["tasks"]) == 2
        task_titles = [t["title"] for t in exported_project["tasks"]]
        assert "Task 1" in task_titles
        assert "Task 2" in task_titles

    def test_export_full_json_with_areas_and_goals(self, db_session: Session):
        """Test full JSON export includes areas and goals"""
        # Create area
        area = Area(title="Health", description="Health area")
        db_session.add(area)

        # Create goal
        goal = Goal(title="Run marathon", timeframe="1_year")
        db_session.add(goal)

        # Create vision
        vision = Vision(title="Be healthy", timeframe="5_year")
        db_session.add(vision)

        db_session.commit()

        # Export
        export_data = ExportService.export_full_json(db_session)

        # Check areas
        assert len(export_data.areas) == 1
        assert export_data.areas[0]["title"] == "Health"

        # Check goals
        assert len(export_data.goals) == 1
        assert export_data.goals[0]["title"] == "Run marathon"

        # Check visions
        assert len(export_data.visions) == 1
        assert export_data.visions[0]["title"] == "Be healthy"

    def test_export_includes_timestamps(self, db_session: Session):
        """Test that exported data includes timestamp fields"""
        # Create project
        project = Project(title="Timestamp Test", status="active", priority=1)
        db_session.add(project)
        db_session.commit()

        # Export
        export_data = ExportService.export_full_json(db_session)

        # Check timestamps in metadata
        assert export_data.metadata.exported_at is not None

        # Check timestamps in project
        exported_project = export_data.projects[0]
        assert "created_at" in exported_project
        assert "updated_at" in exported_project
        assert exported_project["created_at"] is not None

    def test_export_inbox_items(self, db_session: Session):
        """Test JSON export includes inbox items"""
        # Create inbox item
        inbox_item = InboxItem(content="Quick capture test", source="web_ui")
        db_session.add(inbox_item)
        db_session.commit()

        # Export
        export_data = ExportService.export_full_json(db_session)

        # Check inbox items
        assert len(export_data.inbox_items) == 1
        assert export_data.inbox_items[0]["content"] == "Quick capture test"

    def test_export_preserves_relationships(self, db_session: Session):
        """Test that export preserves entity relationships"""
        # Create area
        area = Area(title="Work")
        db_session.add(area)
        db_session.commit()

        # Create goal
        goal = Goal(title="Get promoted", timeframe="1_year")
        db_session.add(goal)
        db_session.commit()

        # Create project linked to area and goal
        project = Project(
            title="Performance Review",
            status="active",
            priority=1,
            area_id=area.id,
            goal_id=goal.id,
        )
        db_session.add(project)
        db_session.commit()

        # Export
        export_data = ExportService.export_full_json(db_session)

        # Check relationships are preserved
        exported_project = export_data.projects[0]
        assert exported_project["area_id"] == area.id
        assert exported_project["goal_id"] == goal.id


class TestFormatBytes:
    """Test the byte formatting helper"""

    def test_format_bytes(self):
        assert ExportService._format_bytes(500) == "500 B"
        assert ExportService._format_bytes(1024) == "1.0 KB"
        assert ExportService._format_bytes(1536) == "1.5 KB"
        assert ExportService._format_bytes(1024 * 1024) == "1.0 MB"
        assert ExportService._format_bytes(1024 * 1024 * 1024) == "1.0 GB"
