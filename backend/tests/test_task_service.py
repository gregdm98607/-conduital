"""
TaskService unit tests.

DEBT-005: Test coverage improvement for R1 release.
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import Project, Task, Area
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService, calculate_urgency_zone


class TestCalculateUrgencyZone:
    """Test the urgency zone calculation function."""

    def test_over_the_horizon_with_future_defer(self):
        """Test that tasks deferred to the future are Over the Horizon."""
        tomorrow = date.today() + timedelta(days=1)
        zone = calculate_urgency_zone(
            defer_until=tomorrow,
            due_date=None,
            priority=5,
        )
        assert zone == "over_the_horizon"

    def test_critical_now_due_today_high_priority(self):
        """Test that high priority tasks due today are Critical Now."""
        today = date.today()
        zone = calculate_urgency_zone(
            defer_until=None,
            due_date=today,
            priority=2,  # High priority (1-3)
        )
        assert zone == "critical_now"

    def test_critical_now_due_today_low_priority(self):
        """Test that all tasks due today are Critical Now regardless of priority."""
        today = date.today()
        zone = calculate_urgency_zone(
            defer_until=None,
            due_date=today,
            priority=5,  # Low priority (4+)
        )
        assert zone == "critical_now"

    def test_critical_now_overdue(self):
        """Test that overdue tasks are Critical Now regardless of priority."""
        yesterday = date.today() - timedelta(days=1)
        zone = calculate_urgency_zone(
            defer_until=None,
            due_date=yesterday,
            priority=8,  # Low priority
        )
        assert zone == "critical_now"

    def test_critical_now_overdue_multiple_days(self):
        """Test that tasks overdue by many days are Critical Now."""
        long_overdue = date.today() - timedelta(days=10)
        zone = calculate_urgency_zone(
            defer_until=None,
            due_date=long_overdue,
            priority=5,
        )
        assert zone == "critical_now"

    def test_critical_now_due_tomorrow_high_priority(self):
        """Test that high priority tasks due tomorrow are Critical Now."""
        tomorrow = date.today() + timedelta(days=1)
        zone = calculate_urgency_zone(
            defer_until=None,
            due_date=tomorrow,
            priority=2,  # High priority
        )
        assert zone == "critical_now"

    def test_opportunity_now_due_tomorrow_low_priority(self):
        """Test that low priority tasks due tomorrow are Opportunity Now."""
        tomorrow = date.today() + timedelta(days=1)
        zone = calculate_urgency_zone(
            defer_until=None,
            due_date=tomorrow,
            priority=5,  # Low priority
        )
        assert zone == "opportunity_now"

    def test_opportunity_now_default(self):
        """Test that default zone is Opportunity Now."""
        zone = calculate_urgency_zone(
            defer_until=None,
            due_date=None,
            priority=5,
        )
        assert zone == "opportunity_now"

    def test_opportunity_now_past_defer_date(self):
        """Test that tasks with past defer date are Opportunity Now."""
        yesterday = date.today() - timedelta(days=1)
        zone = calculate_urgency_zone(
            defer_until=yesterday,
            due_date=None,
            priority=5,
        )
        assert zone == "opportunity_now"

    def test_critical_now_threshold_due_today(self):
        """Test that all tasks due today are Critical Now regardless of priority."""
        today = date.today()
        # Priority 3 should be Critical Now
        zone3 = calculate_urgency_zone(defer_until=None, due_date=today, priority=3)
        assert zone3 == "critical_now"

        # Priority 4 should also be Critical Now (due today)
        zone4 = calculate_urgency_zone(defer_until=None, due_date=today, priority=4)
        assert zone4 == "critical_now"


class TestTaskServiceCRUD:
    """Test TaskService CRUD operations."""

    def test_create_task(self, db_session: Session, sample_project: Project):
        """Test creating a new task."""
        task_data = TaskCreate(
            title="New Task",
            description="A test task description",
            status="pending",
            priority=3,
            project_id=sample_project.id,
        )

        task = TaskService.create(db_session, task_data)

        assert task.id is not None
        assert task.title == "New Task"
        assert task.description == "A test task description"
        assert task.status == "pending"
        assert task.priority == 3
        assert task.project_id == sample_project.id
        assert task.file_marker is not None  # Should have file marker for sync

    def test_create_task_auto_calculates_urgency_zone(self, db_session: Session, sample_project: Project):
        """Test that creating a task auto-calculates urgency zone."""
        tomorrow = date.today() + timedelta(days=1)
        task_data = TaskCreate(
            title="Deferred Task",
            status="pending",
            priority=5,
            project_id=sample_project.id,
            defer_until=tomorrow,
        )

        task = TaskService.create(db_session, task_data)

        assert task.urgency_zone == "over_the_horizon"

    def test_create_task_with_all_fields(self, db_session: Session, sample_project: Project):
        """Test creating a task with all optional fields."""
        due_date = date.today() + timedelta(days=7)
        task_data = TaskCreate(
            title="Full Task",
            description="Complete description",
            status="pending",
            priority=2,
            project_id=sample_project.id,
            context="@computer",
            energy_level="high",
            estimated_minutes=30,
            is_next_action=True,
            is_two_minute_task=False,
            due_date=due_date,
        )

        task = TaskService.create(db_session, task_data)

        assert task.context == "@computer"
        assert task.energy_level == "high"
        assert task.estimated_minutes == 30
        assert task.is_next_action is True
        assert task.is_two_minute_task is False
        assert task.due_date == due_date

    def test_get_by_id_found(self, db_session: Session, sample_task: Task):
        """Test getting a task by ID when it exists."""
        task = TaskService.get_by_id(db_session, sample_task.id)

        assert task is not None
        assert task.id == sample_task.id
        assert task.title == sample_task.title

    def test_get_by_id_not_found(self, db_session: Session):
        """Test getting a task by ID when it doesn't exist."""
        task = TaskService.get_by_id(db_session, 99999)

        assert task is None

    def test_get_by_id_with_project(self, db_session: Session, sample_task: Task):
        """Test getting a task with project eagerly loaded."""
        task = TaskService.get_by_id(db_session, sample_task.id, include_project=True)

        assert task is not None
        assert task.project is not None
        assert task.project.title == "Test Project"

    def test_update_task(self, db_session: Session, sample_task: Task):
        """Test updating a task."""
        update_data = TaskUpdate(
            title="Updated Title",
            priority=1,
        )

        updated = TaskService.update(db_session, sample_task.id, update_data)

        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.priority == 1
        # Original fields unchanged
        assert updated.status == sample_task.status

    def test_update_task_recalculates_urgency_zone(self, db_session: Session, sample_task: Task):
        """Test that updating defer_until recalculates urgency zone."""
        tomorrow = date.today() + timedelta(days=1)
        update_data = TaskUpdate(defer_until=tomorrow)

        updated = TaskService.update(db_session, sample_task.id, update_data)

        assert updated.urgency_zone == "over_the_horizon"

    def test_update_task_not_found(self, db_session: Session):
        """Test updating a non-existent task."""
        update_data = TaskUpdate(title="New Title")

        result = TaskService.update(db_session, 99999, update_data)

        assert result is None

    def test_delete_task(self, db_session: Session, sample_task: Task):
        """Test deleting a task."""
        task_id = sample_task.id

        result = TaskService.delete(db_session, task_id)

        assert result is True
        # Verify deletion
        deleted = TaskService.get_by_id(db_session, task_id)
        assert deleted is None

    def test_delete_task_not_found(self, db_session: Session):
        """Test deleting a non-existent task."""
        result = TaskService.delete(db_session, 99999)

        assert result is False


class TestTaskServiceGetAll:
    """Test TaskService get_all with filtering and pagination."""

    def test_get_all_empty(self, db_session: Session):
        """Test get_all with no tasks."""
        tasks, total = TaskService.get_all(db_session)

        assert tasks == []
        assert total == 0

    def test_get_all_returns_tasks(self, db_session: Session, sample_project_with_tasks: Project):
        """Test get_all returns all non-completed tasks."""
        tasks, total = TaskService.get_all(db_session)

        # sample_project_with_tasks has 4 tasks: pending, in_progress, completed, waiting
        # Default excludes completed
        assert total == 3
        assert len(tasks) == 3

    def test_get_all_show_completed(self, db_session: Session, sample_project_with_tasks: Project):
        """Test get_all with show_completed=True."""
        tasks, total = TaskService.get_all(db_session, show_completed=True)

        assert total == 4
        assert len(tasks) == 4

    def test_get_all_filter_by_project(self, db_session: Session, sample_project_with_tasks: Project, sample_area: Area):
        """Test get_all with project filter."""
        # Create another project with a task
        other_project = Project(
            title="Other Project",
            status="active",
            priority=5,
            area_id=sample_area.id,
        )
        db_session.add(other_project)
        db_session.commit()

        other_task = Task(
            title="Other Task",
            project_id=other_project.id,
            status="pending",
            priority=5,
        )
        db_session.add(other_task)
        db_session.commit()

        # Filter by original project
        tasks, total = TaskService.get_all(db_session, project_id=sample_project_with_tasks.id)

        # Should only return tasks from sample_project_with_tasks (3 non-completed)
        assert total == 3
        assert all(t.project_id == sample_project_with_tasks.id for t in tasks)

    def test_get_all_filter_by_status(self, db_session: Session, sample_project_with_tasks: Project):
        """Test get_all with status filter."""
        tasks, total = TaskService.get_all(db_session, status="pending")

        assert total == 1
        assert all(t.status == "pending" for t in tasks)

    def test_get_all_filter_by_context(self, db_session: Session, sample_project: Project):
        """Test get_all with context filter."""
        # Create tasks with different contexts
        task1 = Task(
            title="Computer Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            context="@computer",
        )
        task2 = Task(
            title="Phone Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            context="@phone",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        tasks, total = TaskService.get_all(db_session, context="@computer")

        assert total == 1
        assert tasks[0].context == "@computer"

    def test_get_all_filter_by_energy_level(self, db_session: Session, sample_project: Project):
        """Test get_all with energy level filter."""
        task1 = Task(
            title="High Energy Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            energy_level="high",
        )
        task2 = Task(
            title="Low Energy Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            energy_level="low",
        )
        db_session.add_all([task1, task2])
        db_session.commit()

        tasks, total = TaskService.get_all(db_session, energy_level="high")

        assert total == 1
        assert tasks[0].energy_level == "high"

    def test_get_all_filter_by_next_action(self, db_session: Session, sample_project_with_tasks: Project):
        """Test get_all with is_next_action filter."""
        tasks, total = TaskService.get_all(db_session, is_next_action=True)

        assert total == 1
        assert tasks[0].is_next_action is True

    def test_get_all_filter_by_priority_range(self, db_session: Session, sample_project: Project):
        """Test get_all with priority range filter."""
        # Create tasks with various priorities
        for i in range(1, 6):
            task = Task(
                title=f"Priority {i} Task",
                project_id=sample_project.id,
                status="pending",
                priority=i,
            )
            db_session.add(task)
        db_session.commit()

        # Get priorities 2-4
        tasks, total = TaskService.get_all(db_session, priority_min=2, priority_max=4)

        assert total == 3
        priorities = [t.priority for t in tasks]
        assert all(2 <= p <= 4 for p in priorities)

    def test_get_all_pagination(self, db_session: Session, sample_project: Project):
        """Test get_all with pagination."""
        # Create 5 tasks
        for i in range(5):
            task = Task(
                title=f"Task {i}",
                project_id=sample_project.id,
                status="pending",
                priority=5,
            )
            db_session.add(task)
        db_session.commit()

        tasks_page1, total = TaskService.get_all(db_session, skip=0, limit=2)
        tasks_page2, _ = TaskService.get_all(db_session, skip=2, limit=2)

        assert total == 5
        assert len(tasks_page1) == 2
        assert len(tasks_page2) == 2
        # Different tasks on each page
        page1_ids = {t.id for t in tasks_page1}
        page2_ids = {t.id for t in tasks_page2}
        assert page1_ids.isdisjoint(page2_ids)


class TestTaskServiceComplete:
    """Test TaskService complete and start operations."""

    def test_complete_task(self, db_session: Session, sample_task: Task):
        """Test marking a task as complete."""
        result = TaskService.complete(db_session, sample_task.id)

        assert result is not None
        assert result.status == "completed"
        assert result.completed_at is not None

    def test_complete_task_with_actual_minutes(self, db_session: Session, sample_task: Task):
        """Test completing a task with actual time."""
        result = TaskService.complete(db_session, sample_task.id, actual_minutes=45)

        assert result is not None
        assert result.status == "completed"
        assert result.actual_minutes == 45

    def test_complete_task_not_found(self, db_session: Session):
        """Test completing a non-existent task."""
        result = TaskService.complete(db_session, 99999)

        assert result is None

    def test_start_task(self, db_session: Session, sample_task: Task):
        """Test starting a task."""
        result = TaskService.start(db_session, sample_task.id)

        assert result is not None
        assert result.status == "in_progress"
        assert result.started_at is not None

    def test_start_task_not_found(self, db_session: Session):
        """Test starting a non-existent task."""
        result = TaskService.start(db_session, 99999)

        assert result is None


class TestTaskServiceQueries:
    """Test TaskService specialized query methods."""

    def test_get_by_context(self, db_session: Session, sample_project: Project):
        """Test getting tasks by context."""
        # Create tasks with context
        task1 = Task(
            title="Computer Task 1",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            context="@computer",
        )
        task2 = Task(
            title="Computer Task 2",
            project_id=sample_project.id,
            status="in_progress",
            priority=3,
            context="@computer",
        )
        task3 = Task(
            title="Phone Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            context="@phone",
        )
        task4 = Task(
            title="Completed Computer Task",
            project_id=sample_project.id,
            status="completed",
            priority=5,
            context="@computer",
        )
        db_session.add_all([task1, task2, task3, task4])
        db_session.commit()

        results = TaskService.get_by_context(db_session, "@computer")

        # Should return 2 (excludes completed)
        assert len(results) == 2
        assert all(t.context == "@computer" for t in results)
        assert all(t.status in ["pending", "in_progress"] for t in results)

    def test_get_overdue(self, db_session: Session, sample_project: Project):
        """Test getting overdue tasks."""
        yesterday = date.today() - timedelta(days=1)
        tomorrow = date.today() + timedelta(days=1)

        # Create overdue task
        overdue_task = Task(
            title="Overdue Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            due_date=yesterday,
        )
        # Create future task
        future_task = Task(
            title="Future Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            due_date=tomorrow,
        )
        # Create completed overdue task (should not be returned)
        completed_overdue = Task(
            title="Completed Overdue",
            project_id=sample_project.id,
            status="completed",
            priority=5,
            due_date=yesterday,
        )
        db_session.add_all([overdue_task, future_task, completed_overdue])
        db_session.commit()

        results = TaskService.get_overdue(db_session)

        assert len(results) == 1
        assert results[0].title == "Overdue Task"

    def test_get_two_minute_tasks(self, db_session: Session, sample_project: Project):
        """Test getting two-minute tasks."""
        # Create two-minute task
        quick_task = Task(
            title="Quick Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            is_two_minute_task=True,
        )
        # Create normal task
        normal_task = Task(
            title="Normal Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
            is_two_minute_task=False,
        )
        # Create completed two-minute task (should not be returned)
        completed_quick = Task(
            title="Completed Quick",
            project_id=sample_project.id,
            status="completed",
            priority=5,
            is_two_minute_task=True,
        )
        db_session.add_all([quick_task, normal_task, completed_quick])
        db_session.commit()

        results = TaskService.get_two_minute_tasks(db_session)

        assert len(results) == 1
        assert results[0].title == "Quick Task"


class TestTaskServiceSearch:
    """Test TaskService search functionality."""

    def test_search_by_title(self, db_session: Session, sample_project: Project):
        """Test searching tasks by title."""
        task1 = Task(
            title="Important Meeting Prep",
            project_id=sample_project.id,
            status="pending",
            priority=5,
        )
        task2 = Task(
            title="Meeting Follow Up",
            project_id=sample_project.id,
            status="pending",
            priority=5,
        )
        task3 = Task(
            title="Email Inbox Zero",
            project_id=sample_project.id,
            status="pending",
            priority=5,
        )
        db_session.add_all([task1, task2, task3])
        db_session.commit()

        results = TaskService.search(db_session, "Meeting")

        assert len(results) == 2
        titles = [t.title for t in results]
        assert "Important Meeting Prep" in titles
        assert "Meeting Follow Up" in titles

    def test_search_by_description(self, db_session: Session, sample_project: Project):
        """Test searching tasks by description."""
        task = Task(
            title="Generic Task",
            description="This involves machine learning algorithms",
            project_id=sample_project.id,
            status="pending",
            priority=5,
        )
        db_session.add(task)
        db_session.commit()

        results = TaskService.search(db_session, "machine learning")

        assert len(results) == 1
        assert results[0].title == "Generic Task"

    def test_search_case_insensitive(self, db_session: Session, sample_project: Project):
        """Test that search is case-insensitive."""
        task = Task(
            title="IMPORTANT Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
        )
        db_session.add(task)
        db_session.commit()

        results = TaskService.search(db_session, "important")

        assert len(results) == 1

    def test_search_no_results(self, db_session: Session, sample_project: Project):
        """Test search with no matching results."""
        task = Task(
            title="Some Task",
            project_id=sample_project.id,
            status="pending",
            priority=5,
        )
        db_session.add(task)
        db_session.commit()

        results = TaskService.search(db_session, "nonexistent")

        assert results == []

    def test_search_limit(self, db_session: Session, sample_project: Project):
        """Test search respects limit parameter."""
        # Create many tasks
        for i in range(10):
            task = Task(
                title=f"Search Test Task {i}",
                project_id=sample_project.id,
                status="pending",
                priority=5,
            )
            db_session.add(task)
        db_session.commit()

        results = TaskService.search(db_session, "Search Test", limit=3)

        assert len(results) == 3
