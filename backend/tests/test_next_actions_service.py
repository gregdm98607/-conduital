"""
NextActionsService unit tests.

DEBT-005: Test coverage improvement for R1 release.
"""

import pytest
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import Project, Task, Area
from app.services.next_actions_service import NextActionsService


class TestGetPrioritizedNextActions:
    """Test NextActionsService get_prioritized_next_actions."""

    def test_empty_database(self, db_session: Session):
        """Test with no tasks."""
        results = NextActionsService.get_prioritized_next_actions(db_session)
        assert results == []

    def test_returns_only_next_actions(self, db_session: Session, sample_area: Area):
        """Test that only is_next_action=True tasks are returned."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        # Create next action and regular task
        next_action = Task(
            title="Next Action",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
        )
        regular_task = Task(
            title="Regular Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=False,
        )
        db_session.add_all([next_action, regular_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(db_session)

        assert len(results) == 1
        assert results[0].title == "Next Action"

    def test_excludes_completed_tasks(self, db_session: Session, sample_area: Area):
        """Test that completed tasks are excluded."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        completed_task = Task(
            title="Completed Next Action",
            project_id=project.id,
            status="completed",
            priority=1,
            is_next_action=True,
        )
        pending_task = Task(
            title="Pending Next Action",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
        )
        db_session.add_all([completed_task, pending_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(db_session)

        assert len(results) == 1
        assert results[0].title == "Pending Next Action"

    def test_excludes_inactive_project_tasks(self, db_session: Session, sample_area: Area):
        """Test that tasks from inactive projects are excluded."""
        active_project = Project(
            title="Active Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        inactive_project = Project(
            title="Completed Project",
            status="completed",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add_all([active_project, inactive_project])
        db_session.commit()

        active_task = Task(
            title="Active Task",
            project_id=active_project.id,
            status="pending",
            priority=1,
            is_next_action=True,
        )
        inactive_task = Task(
            title="Inactive Task",
            project_id=inactive_project.id,
            status="pending",
            priority=1,
            is_next_action=True,
        )
        db_session.add_all([active_task, inactive_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(db_session)

        assert len(results) == 1
        assert results[0].title == "Active Task"

    def test_excludes_deferred_tasks(self, db_session: Session, sample_area: Area):
        """Test that deferred tasks (defer_until > today) are excluded."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        tomorrow = date.today() + timedelta(days=1)
        yesterday = date.today() - timedelta(days=1)

        deferred_task = Task(
            title="Deferred Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            defer_until=tomorrow,
        )
        ready_task = Task(
            title="Ready Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            defer_until=yesterday,
        )
        no_defer_task = Task(
            title="No Defer Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            defer_until=None,
        )
        db_session.add_all([deferred_task, ready_task, no_defer_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(db_session)

        assert len(results) == 2
        titles = [t.title for t in results]
        assert "Ready Task" in titles
        assert "No Defer Task" in titles
        assert "Deferred Task" not in titles

    def test_filter_by_context(self, db_session: Session, sample_area: Area):
        """Test filtering by context."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        computer_task = Task(
            title="Computer Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            context="@computer",
        )
        phone_task = Task(
            title="Phone Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            context="@phone",
        )
        db_session.add_all([computer_task, phone_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(
            db_session, context="@computer"
        )

        assert len(results) == 1
        assert results[0].context == "@computer"

    def test_filter_by_energy_level(self, db_session: Session, sample_area: Area):
        """Test filtering by energy level."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        high_energy_task = Task(
            title="High Energy Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            energy_level="high",
        )
        low_energy_task = Task(
            title="Low Energy Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            energy_level="low",
        )
        db_session.add_all([high_energy_task, low_energy_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(
            db_session, energy_level="low"
        )

        assert len(results) == 1
        assert results[0].energy_level == "low"

    def test_filter_by_time_available(self, db_session: Session, sample_area: Area):
        """Test filtering by time available."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        short_task = Task(
            title="Short Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            estimated_minutes=10,
        )
        long_task = Task(
            title="Long Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            estimated_minutes=60,
        )
        no_estimate_task = Task(
            title="No Estimate Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            estimated_minutes=None,
        )
        db_session.add_all([short_task, long_task, no_estimate_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(
            db_session, time_available=15
        )

        assert len(results) == 2
        titles = [t.title for t in results]
        assert "Short Task" in titles
        assert "No Estimate Task" in titles  # None passes the filter
        assert "Long Task" not in titles

    def test_respects_limit(self, db_session: Session, sample_area: Area):
        """Test that limit parameter is respected."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        # Create 10 tasks
        for i in range(10):
            task = Task(
                title=f"Task {i}",
                project_id=project.id,
                status="pending",
                priority=5,
                is_next_action=True,
            )
            db_session.add(task)
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(db_session, limit=3)

        assert len(results) == 3

    def test_prioritizes_due_soon_tasks(self, db_session: Session, sample_area: Area):
        """Test that tasks due soon are prioritized."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)

        due_tomorrow = Task(
            title="Due Tomorrow",
            project_id=project.id,
            status="pending",
            priority=5,
            is_next_action=True,
            due_date=tomorrow,
        )
        due_next_week = Task(
            title="Due Next Week",
            project_id=project.id,
            status="pending",
            priority=1,  # Higher priority
            is_next_action=True,
            due_date=next_week,
        )
        db_session.add_all([due_tomorrow, due_next_week])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(db_session)

        # Due tomorrow should come first (within 3 days)
        assert results[0].title == "Due Tomorrow"

    def test_prioritizes_high_momentum_projects(self, db_session: Session, sample_area: Area):
        """Test that high momentum project tasks are prioritized."""
        high_momentum = Project(
            title="High Momentum",
            status="active",
            priority=5,
            area_id=sample_area.id,
            momentum_score=0.9,
        )
        low_momentum = Project(
            title="Low Momentum",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.2,
        )
        db_session.add_all([high_momentum, low_momentum])
        db_session.commit()

        high_task = Task(
            title="High Momentum Task",
            project_id=high_momentum.id,
            status="pending",
            priority=5,
            is_next_action=True,
        )
        low_task = Task(
            title="Low Momentum Task",
            project_id=low_momentum.id,
            status="pending",
            priority=5,
            is_next_action=True,
        )
        db_session.add_all([high_task, low_task])
        db_session.commit()

        results = NextActionsService.get_prioritized_next_actions(db_session)

        # High momentum (>0.7) should be prioritized
        assert results[0].title == "High Momentum Task"


class TestGetNextActionsByContext:
    """Test NextActionsService get_next_actions_by_context."""

    def test_empty_database(self, db_session: Session):
        """Test with no tasks."""
        results = NextActionsService.get_next_actions_by_context(db_session)
        assert results == {}

    def test_groups_by_context(self, db_session: Session, sample_area: Area):
        """Test that tasks are grouped by context."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        computer_task = Task(
            title="Computer Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            context="@computer",
        )
        phone_task1 = Task(
            title="Phone Task 1",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            context="@phone",
        )
        phone_task2 = Task(
            title="Phone Task 2",
            project_id=project.id,
            status="pending",
            priority=2,
            is_next_action=True,
            context="@phone",
        )
        no_context_task = Task(
            title="No Context Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            context=None,
        )
        db_session.add_all([computer_task, phone_task1, phone_task2, no_context_task])
        db_session.commit()

        results = NextActionsService.get_next_actions_by_context(db_session)

        assert "@computer" in results
        assert "@phone" in results
        assert None not in results  # Tasks without context excluded
        assert len(results["@computer"]) == 1
        assert len(results["@phone"]) == 2

    def test_respects_limit_per_context(self, db_session: Session, sample_area: Area):
        """Test that limit_per_context is respected."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        # Create 5 tasks per context
        for i in range(5):
            task = Task(
                title=f"Computer Task {i}",
                project_id=project.id,
                status="pending",
                priority=5,
                is_next_action=True,
                context="@computer",
            )
            db_session.add(task)
        db_session.commit()

        results = NextActionsService.get_next_actions_by_context(
            db_session, limit_per_context=2
        )

        assert len(results["@computer"]) == 2


class TestGetStalledProjectsCount:
    """Test NextActionsService get_stalled_projects_count."""

    def test_empty_database(self, db_session: Session):
        """Test with no projects."""
        count = NextActionsService.get_stalled_projects_count(db_session)
        assert count == 0

    def test_counts_stalled_projects(self, db_session: Session, sample_area: Area):
        """Test counting stalled projects."""
        stalled_project = Project(
            title="Stalled Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            stalled_since=datetime.now(timezone.utc) - timedelta(days=10),
        )
        active_project = Project(
            title="Active Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            stalled_since=None,
        )
        completed_stalled = Project(
            title="Completed Stalled",
            status="completed",
            priority=1,
            area_id=sample_area.id,
            stalled_since=datetime.now(timezone.utc) - timedelta(days=10),
        )
        db_session.add_all([stalled_project, active_project, completed_stalled])
        db_session.commit()

        count = NextActionsService.get_stalled_projects_count(db_session)

        # Only active stalled projects counted
        assert count == 1


class TestGetDailyDashboard:
    """Test NextActionsService get_daily_dashboard."""

    def test_empty_database(self, db_session: Session):
        """Test dashboard with empty database."""
        dashboard = NextActionsService.get_daily_dashboard(db_session)

        assert "top_3_priorities" in dashboard
        assert "quick_wins" in dashboard
        assert "due_today" in dashboard
        assert "stalled_projects_count" in dashboard
        assert "top_momentum_projects" in dashboard
        assert dashboard["top_3_priorities"] == []
        assert dashboard["quick_wins"] == []
        assert dashboard["due_today"] == []
        assert dashboard["stalled_projects_count"] == 0

    def test_dashboard_with_data(self, db_session: Session, sample_area: Area):
        """Test dashboard returns proper data."""
        project = Project(
            title="Dashboard Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.8,
        )
        db_session.add(project)
        db_session.commit()

        # Create a next action (top priority)
        next_action = Task(
            title="Priority Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
        )
        # Create quick win
        quick_win = Task(
            title="Quick Win",
            project_id=project.id,
            status="pending",
            priority=3,
            is_next_action=True,
            estimated_minutes=10,
        )
        # Create due today task
        due_today_task = Task(
            title="Due Today",
            project_id=project.id,
            status="pending",
            priority=2,
            is_next_action=False,
            due_date=date.today(),
        )
        db_session.add_all([next_action, quick_win, due_today_task])
        db_session.commit()

        dashboard = NextActionsService.get_daily_dashboard(db_session)

        assert len(dashboard["top_3_priorities"]) == 2  # Both next actions
        assert len(dashboard["quick_wins"]) == 1
        assert len(dashboard["due_today"]) == 1  # Only task with due_date == today
        assert len(dashboard["top_momentum_projects"]) == 1

    def test_dashboard_quick_wins_limited_to_15_min(self, db_session: Session, sample_area: Area):
        """Test quick wins only includes tasks <= 15 min."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        short_task = Task(
            title="Quick Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            estimated_minutes=10,
        )
        long_task = Task(
            title="Long Task",
            project_id=project.id,
            status="pending",
            priority=1,
            is_next_action=True,
            estimated_minutes=30,
        )
        db_session.add_all([short_task, long_task])
        db_session.commit()

        dashboard = NextActionsService.get_daily_dashboard(db_session)

        assert len(dashboard["quick_wins"]) == 1
        assert dashboard["quick_wins"][0].title == "Quick Task"

    def test_dashboard_due_today_only(self, db_session: Session, sample_area: Area):
        """Test due_today only includes tasks due today."""
        project = Project(
            title="Test Project",
            status="active",
            priority=1,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        today = date.today()
        tomorrow = date.today() + timedelta(days=1)

        due_today = Task(
            title="Due Today",
            project_id=project.id,
            status="pending",
            priority=1,
            due_date=today,
        )
        due_tomorrow = Task(
            title="Due Tomorrow",
            project_id=project.id,
            status="pending",
            priority=1,
            due_date=tomorrow,
        )
        db_session.add_all([due_today, due_tomorrow])
        db_session.commit()

        dashboard = NextActionsService.get_daily_dashboard(db_session)

        assert len(dashboard["due_today"]) == 1
        assert dashboard["due_today"][0].title == "Due Today"
