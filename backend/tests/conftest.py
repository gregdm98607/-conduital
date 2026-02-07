"""
Shared pytest fixtures for all backend tests.

This conftest.py provides common fixtures for database access,
test data creation, and service testing.

Usage:
    def test_something(db_session):
        # db_session is a fresh SQLAlchemy session with all tables created
        project = Project(title="Test", status="active", priority=1)
        db_session.add(project)
        db_session.commit()
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models import Project, Task, Area, Goal, Vision, Context, InboxItem


# Test database URL - in-memory SQLite for speed and isolation
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def in_memory_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    return engine


@pytest.fixture(scope="function")
def db_session(in_memory_engine):
    """
    Create a fresh database session for each test.

    - Creates all tables before yielding
    - Provides a session for the test
    - Cleans up (closes session, drops tables) after test

    Usage:
        def test_create_project(db_session):
            project = Project(title="Test", status="active", priority=1)
            db_session.add(project)
            db_session.commit()
            assert project.id is not None
    """
    # Create all tables
    Base.metadata.create_all(bind=in_memory_engine)

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=in_memory_engine)
    session = SessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=in_memory_engine)


# =============================================================================
# Test Data Factory Fixtures
# =============================================================================


@pytest.fixture
def sample_area(db_session) -> Area:
    """Create a sample area for testing."""
    area = Area(
        title="Test Area",
        description="A test area of responsibility",
        standard_of_excellence="Maintain high standards",
        review_frequency="weekly",
    )
    db_session.add(area)
    db_session.commit()
    return area


@pytest.fixture
def sample_goal(db_session) -> Goal:
    """Create a sample goal for testing."""
    goal = Goal(
        title="Test Goal",
        description="A test 1-year goal",
        timeframe="1_year",
        status="active",
    )
    db_session.add(goal)
    db_session.commit()
    return goal


@pytest.fixture
def sample_vision(db_session) -> Vision:
    """Create a sample vision for testing."""
    vision = Vision(
        title="Test Vision",
        description="A test 3-5 year vision",
        timeframe="3_year",
    )
    db_session.add(vision)
    db_session.commit()
    return vision


@pytest.fixture
def sample_project(db_session, sample_area) -> Project:
    """Create a sample project for testing."""
    project = Project(
        title="Test Project",
        description="A test project",
        outcome_statement="Successfully complete the test",
        status="active",
        priority=3,
        area_id=sample_area.id,
    )
    db_session.add(project)
    db_session.commit()
    return project


@pytest.fixture
def sample_project_with_tasks(db_session, sample_area) -> Project:
    """Create a sample project with multiple tasks."""
    project = Project(
        title="Project With Tasks",
        description="A project with tasks for testing",
        status="active",
        priority=2,
        area_id=sample_area.id,
    )
    db_session.add(project)
    db_session.commit()

    # Add tasks
    tasks = [
        Task(
            title="Task 1 - Next Action",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
        ),
        Task(
            title="Task 2 - In Progress",
            project_id=project.id,
            status="in_progress",
            priority=2,
        ),
        Task(
            title="Task 3 - Completed",
            project_id=project.id,
            status="completed",
            priority=3,
        ),
        Task(
            title="Task 4 - Waiting",
            project_id=project.id,
            status="waiting",
            priority=4,
            waiting_for="External review",
        ),
    ]
    db_session.add_all(tasks)
    db_session.commit()

    # Refresh to load tasks relationship
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_task(db_session, sample_project) -> Task:
    """Create a sample task for testing."""
    task = Task(
        title="Test Task",
        description="A test task",
        project_id=sample_project.id,
        status="pending",
        priority=3,
        is_next_action=True,
        urgency_zone="opportunity_now",
    )
    db_session.add(task)
    db_session.commit()
    return task


@pytest.fixture
def sample_inbox_item(db_session) -> InboxItem:
    """Create a sample inbox item for testing."""
    item = InboxItem(
        content="Quick capture: remember to test this",
        source="web_ui",
    )
    db_session.add(item)
    db_session.commit()
    return item


@pytest.fixture
def multiple_projects(db_session, sample_area) -> list[Project]:
    """Create multiple projects with varying states for testing."""
    from datetime import datetime, timedelta, timezone

    projects = [
        Project(
            title="Active High Priority",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.8,
            last_activity_at=datetime.now(timezone.utc),
        ),
        Project(
            title="Active Low Priority",
            status="active",
            priority=8,
            area_id=sample_area.id,
            momentum_score=0.5,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=5),
        ),
        Project(
            title="Stalled Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.1,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=20),
            stalled_since=datetime.now(timezone.utc) - timedelta(days=6),
        ),
        Project(
            title="Completed Project",
            status="completed",
            priority=5,
            area_id=sample_area.id,
            momentum_score=1.0,
            completed_at=datetime.now(timezone.utc) - timedelta(days=2),
        ),
        Project(
            title="Someday Maybe",
            status="someday_maybe",
            priority=10,
            momentum_score=0.0,
        ),
    ]
    db_session.add_all(projects)
    db_session.commit()
    return projects
