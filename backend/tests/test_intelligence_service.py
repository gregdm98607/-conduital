"""
IntelligenceService unit tests.

DEBT-005: Test coverage improvement for R1 release.
Updated for beta momentum formula (BETA-001 through BETA-004).
"""

import pytest
import math
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from unittest.mock import patch

from app.models import Project, Task, Area, MomentumSnapshot
from app.models.activity_log import ActivityLog
from app.services.intelligence_service import (
    IntelligenceService,
    _ensure_tz_aware,
    _calc_graduated_next_action,
    _calc_sliding_completion,
    _calc_sliding_completion_from_tasks,
    _next_action_detail_string,
)


class TestEnsureTzAware:
    """Test the _ensure_tz_aware helper function."""

    def test_returns_none_for_none(self):
        """Test that None input returns None."""
        assert _ensure_tz_aware(None) is None

    def test_preserves_tz_aware_datetime(self):
        """Test that timezone-aware datetime is preserved."""
        dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = _ensure_tz_aware(dt)
        assert result == dt
        assert result.tzinfo == timezone.utc

    def test_adds_utc_to_naive_datetime(self):
        """Test that naive datetime gets UTC timezone added."""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)
        result = _ensure_tz_aware(naive_dt)
        assert result.tzinfo == timezone.utc
        assert result.year == 2024
        assert result.month == 1


class TestGraduatedNextAction:
    """Test BETA-001: Graduated next-action scoring helper."""

    def test_no_next_action_returns_zero(self, db_session: Session, sample_area: Area):
        """No pending next action → 0.0."""
        project = Project(
            title="No NA", status="active", priority=3, area_id=sample_area.id
        )
        db_session.add(project)
        db_session.commit()

        now = datetime.now(timezone.utc)
        score = _calc_graduated_next_action(db_session, project.id, now)
        assert score == 0.0

    def test_fresh_next_action_returns_one(self, db_session: Session, sample_area: Area):
        """Next action created <24h ago → 1.0."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Fresh NA", status="active", priority=3, area_id=sample_area.id
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="Fresh NA",
            project_id=project.id,
            status="pending",
            priority=3,
            is_next_action=True,
            created_at=now - timedelta(hours=6),
        )
        db_session.add(task)
        db_session.commit()

        score = _calc_graduated_next_action(db_session, project.id, now)
        assert score == 1.0

    def test_recent_next_action_returns_0_7(self, db_session: Session, sample_area: Area):
        """Next action created 1-7 days ago → 0.7."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Recent NA", status="active", priority=3, area_id=sample_area.id
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="Recent NA",
            project_id=project.id,
            status="pending",
            priority=3,
            is_next_action=True,
            created_at=now - timedelta(days=3),
        )
        db_session.add(task)
        db_session.commit()

        score = _calc_graduated_next_action(db_session, project.id, now)
        assert score == 0.7

    def test_stale_next_action_returns_0_3(self, db_session: Session, sample_area: Area):
        """Next action created >7 days ago → 0.3."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Stale NA", status="active", priority=3, area_id=sample_area.id
        )
        db_session.add(project)
        db_session.commit()

        task = Task(
            title="Stale NA",
            project_id=project.id,
            status="pending",
            priority=3,
            is_next_action=True,
            created_at=now - timedelta(days=10),
        )
        db_session.add(task)
        db_session.commit()

        score = _calc_graduated_next_action(db_session, project.id, now)
        assert score == 0.3


class TestSlidingCompletion:
    """Test BETA-003: Sliding completion window helper."""

    def test_no_tasks_returns_zero(self, db_session: Session, sample_area: Area):
        """No tasks → 0.0."""
        project = Project(
            title="Empty", status="active", priority=3, area_id=sample_area.id
        )
        db_session.add(project)
        db_session.commit()

        now = datetime.now(timezone.utc)
        score = _calc_sliding_completion(db_session, project.id, now)
        assert score == 0.0

    def test_recent_completions_weighted_higher(self, db_session: Session, sample_area: Area):
        """Tasks completed in last 7 days have higher weight than older ones."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Weighted", status="active", priority=3, area_id=sample_area.id
        )
        db_session.add(project)
        db_session.commit()

        # 1 completed in recent window (weight 1.0)
        t1 = Task(
            title="Recent Complete",
            project_id=project.id,
            status="completed",
            priority=3,
            created_at=now - timedelta(days=2),
        )
        # 1 pending in recent window (weight 1.0)
        t2 = Task(
            title="Recent Pending",
            project_id=project.id,
            status="pending",
            priority=3,
            created_at=now - timedelta(days=3),
        )
        # 1 completed in old window (weight 0.25)
        t3 = Task(
            title="Old Complete",
            project_id=project.id,
            status="completed",
            priority=3,
            created_at=now - timedelta(days=20),
        )
        db_session.add_all([t1, t2, t3])
        db_session.commit()

        score = _calc_sliding_completion(db_session, project.id, now)
        # weighted_completed = 1.0 + 0.25 = 1.25
        # weighted_total = 1.0 + 1.0 + 0.25 = 2.25
        # score = 1.25 / 2.25 ≈ 0.556
        assert 0.5 < score < 0.6

    def test_all_completed_returns_one(self, db_session: Session, sample_area: Area):
        """All tasks completed → 1.0."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="All Done", status="active", priority=3, area_id=sample_area.id
        )
        db_session.add(project)
        db_session.commit()

        for i in range(3):
            task = Task(
                title=f"Task {i}",
                project_id=project.id,
                status="completed",
                priority=3,
                created_at=now - timedelta(days=i + 1),
            )
            db_session.add(task)
        db_session.commit()

        score = _calc_sliding_completion(db_session, project.id, now)
        assert score == 1.0


class TestNextActionDetailString:
    """Test _next_action_detail_string helper."""

    def test_fresh(self):
        assert _next_action_detail_string(1.0) == "Fresh (<24h)"

    def test_recent(self):
        assert _next_action_detail_string(0.7) == "Recent (1-7d)"

    def test_stale(self):
        assert _next_action_detail_string(0.3) == "Stale (>7d)"

    def test_missing(self):
        assert _next_action_detail_string(0.0) == "Missing"


class TestCalculateMomentumScore:
    """Test IntelligenceService calculate_momentum_score with beta formula."""

    def test_zero_score_no_activity(self, db_session: Session, sample_area: Area):
        """Test that project with no activity has low score."""
        project = Project(
            title="No Activity Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=None,
        )
        db_session.add(project)
        db_session.commit()

        score = IntelligenceService.calculate_momentum_score(db_session, project)

        # Should be 0 (no activity, no tasks, no next action)
        assert score == 0.0

    def test_score_with_recent_activity(self, db_session: Session, sample_area: Area):
        """Test that recent activity increases score via exponential decay."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Recent Activity Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=now - timedelta(days=1),
        )
        db_session.add(project)
        db_session.commit()

        score = IntelligenceService.calculate_momentum_score(db_session, project)

        # BETA-002: e^(-1/7) * 0.4 ≈ 0.867 * 0.4 ≈ 0.347
        assert score > 0.3

    def test_score_with_next_action(self, db_session: Session, sample_area: Area):
        """Test that having next action increases score."""
        project = Project(
            title="Project with Next Action",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add(project)
        db_session.commit()

        # Add next action (created now — will be "stale" since created_at is auto-set)
        next_action = Task(
            title="Next Action",
            project_id=project.id,
            status="pending",
            priority=3,
            is_next_action=True,
        )
        db_session.add(next_action)
        db_session.commit()

        score = IntelligenceService.calculate_momentum_score(db_session, project)

        # BETA-001: graduated scoring — at minimum 0.3 * 0.2 = 0.06
        assert score >= 0.06

    def test_score_with_completed_tasks(self, db_session: Session, sample_area: Area):
        """Test that recent completions increase score via sliding window."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Project with Completions",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add(project)
        db_session.commit()

        # Add recent tasks, some completed
        for i in range(4):
            task = Task(
                title=f"Task {i}",
                project_id=project.id,
                status="completed" if i < 2 else "pending",
                priority=3,
                created_at=now - timedelta(days=2),
            )
            db_session.add(task)
        db_session.commit()

        score = IntelligenceService.calculate_momentum_score(db_session, project)

        # BETA-003: 50% completion in 7d window (weight 1.0) → 0.5 * 0.3 = 0.15
        assert score >= 0.15

    def test_score_decays_over_time(self, db_session: Session, sample_area: Area):
        """Test that momentum score decays with time since activity."""
        now = datetime.now(timezone.utc)

        # Project with activity 15 days ago
        old_project = Project(
            title="Old Activity",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=now - timedelta(days=15),
        )
        # Project with activity 1 day ago
        recent_project = Project(
            title="Recent Activity",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=now - timedelta(days=1),
        )
        db_session.add_all([old_project, recent_project])
        db_session.commit()

        old_score = IntelligenceService.calculate_momentum_score(db_session, old_project)
        recent_score = IntelligenceService.calculate_momentum_score(db_session, recent_project)

        # Recent project should have higher score
        assert recent_score > old_score

    def test_exponential_decay_is_steeper_than_linear(self, db_session: Session, sample_area: Area):
        """BETA-002: Exponential decay drops faster for stale activity."""
        now = datetime.now(timezone.utc)
        # Activity 20 days ago — linear would give 1-20/30 = 0.33,
        # exponential gives e^(-20/7) ≈ 0.057
        project = Project(
            title="Stale Activity",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=now - timedelta(days=20),
        )
        db_session.add(project)
        db_session.commit()

        score = IntelligenceService.calculate_momentum_score(db_session, project)
        # e^(-20/7) * 0.4 ≈ 0.057 * 0.4 ≈ 0.023
        assert score < 0.1  # Much lower than old linear would give (~0.13)

    def test_logarithmic_frequency_diminishing_returns(self, db_session: Session, sample_area: Area):
        """BETA-004: Each additional action is worth less."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Freq Test",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add(project)
        db_session.commit()

        # Add 10 activities in last 14 days
        for i in range(10):
            activity = ActivityLog(
                entity_type="project",
                entity_id=project.id,
                action_type="test",
                timestamp=now - timedelta(days=i),
            )
            db_session.add(activity)
        db_session.commit()

        score = IntelligenceService.calculate_momentum_score(db_session, project)

        # log(1+10)/log(11) = log(11)/log(11) = 1.0 — fully saturated at 10
        # So frequency contribution = 1.0 * 0.1 = 0.1
        # Total includes frequency component
        assert score >= 0.1


class TestUpdateAllMomentumScores:
    """Test IntelligenceService update_all_momentum_scores."""

    def test_updates_all_active_projects(self, db_session: Session, sample_area: Area):
        """Test that all active projects get updated."""
        project1 = Project(
            title="Project 1",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.0,
        )
        project2 = Project(
            title="Project 2",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.0,
        )
        completed_project = Project(
            title="Completed",
            status="completed",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add_all([project1, project2, completed_project])
        db_session.commit()

        stats = IntelligenceService.update_all_momentum_scores(db_session)

        assert stats["updated"] == 2  # Only active projects

    def test_saves_previous_momentum_score(self, db_session: Session, sample_area: Area):
        """BETA-020: Previous score is preserved for delta calculation."""
        project = Project(
            title="Delta Test",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.75,
        )
        db_session.add(project)
        db_session.commit()

        IntelligenceService.update_all_momentum_scores(db_session)

        db_session.refresh(project)
        assert project.previous_momentum_score == 0.75

    def test_detects_stalled_projects(self, db_session: Session, sample_area: Area):
        """Test that stalled projects are detected."""
        now = datetime.now(timezone.utc)
        stalled_project = Project(
            title="Stalled",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=now - timedelta(days=20),  # Over threshold
            stalled_since=None,
        )
        db_session.add(stalled_project)
        db_session.commit()

        stats = IntelligenceService.update_all_momentum_scores(db_session)

        assert stats["stalled_detected"] >= 1
        db_session.refresh(stalled_project)
        assert stalled_project.stalled_since is not None

    def test_unstalls_recovered_projects(self, db_session: Session, sample_area: Area):
        """Test that projects with recent activity are unstalled."""
        now = datetime.now(timezone.utc)
        recovered_project = Project(
            title="Recovered",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=now - timedelta(days=2),  # Recent
            stalled_since=now - timedelta(days=10),  # Was stalled
        )
        db_session.add(recovered_project)
        db_session.commit()

        stats = IntelligenceService.update_all_momentum_scores(db_session)

        assert stats["unstalled"] >= 1
        db_session.refresh(recovered_project)
        assert recovered_project.stalled_since is None


class TestCreateMomentumSnapshots:
    """Test BETA-021/023: MomentumSnapshot creation."""

    def test_creates_snapshots_for_active_projects(self, db_session: Session, sample_area: Area):
        """Snapshots are created for each active project."""
        p1 = Project(
            title="P1", status="active", priority=3,
            area_id=sample_area.id, momentum_score=0.5,
        )
        p2 = Project(
            title="P2", status="active", priority=3,
            area_id=sample_area.id, momentum_score=0.8,
        )
        p3 = Project(
            title="P3 (completed)", status="completed", priority=3,
            area_id=sample_area.id, momentum_score=1.0,
        )
        db_session.add_all([p1, p2, p3])
        db_session.commit()

        count = IntelligenceService.create_momentum_snapshots(db_session)

        assert count == 2  # Only active projects

        snapshots = db_session.query(MomentumSnapshot).all()
        assert len(snapshots) == 2
        scores = {s.project_id: s.score for s in snapshots}
        assert scores[p1.id] == 0.5
        assert scores[p2.id] == 0.8

    def test_snapshot_contains_factors_json(self, db_session: Session, sample_area: Area):
        """Snapshot factors_json contains score data."""
        project = Project(
            title="Snapshot Test", status="active", priority=3,
            area_id=sample_area.id, momentum_score=0.6,
            previous_momentum_score=0.55,
        )
        db_session.add(project)
        db_session.commit()

        IntelligenceService.create_momentum_snapshots(db_session)

        import json
        snapshot = db_session.query(MomentumSnapshot).first()
        factors = json.loads(snapshot.factors_json)
        assert factors["score"] == 0.6
        assert factors["previous"] == 0.55


class TestDetectStalledProjects:
    """Test IntelligenceService detect_stalled_projects."""

    def test_returns_empty_when_none_stalled(self, db_session: Session, sample_area: Area):
        """Test returns empty list when no projects are stalled."""
        project = Project(
            title="Active Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            stalled_since=None,
        )
        db_session.add(project)
        db_session.commit()

        stalled = IntelligenceService.detect_stalled_projects(db_session)

        assert stalled == []

    def test_returns_stalled_projects(self, db_session: Session, sample_area: Area):
        """Test returns projects marked as stalled."""
        now = datetime.now(timezone.utc)
        stalled_project = Project(
            title="Stalled Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            stalled_since=now - timedelta(days=5),
        )
        active_project = Project(
            title="Active Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            stalled_since=None,
        )
        db_session.add_all([stalled_project, active_project])
        db_session.commit()

        stalled = IntelligenceService.detect_stalled_projects(db_session)

        assert len(stalled) == 1
        assert stalled[0].title == "Stalled Project"


class TestGenerateUnstuckTaskSuggestion:
    """Test IntelligenceService generate_unstuck_task_suggestion."""

    def test_no_pending_tasks(self, db_session: Session, sample_area: Area):
        """Test suggestion when project has no pending tasks."""
        project = Project(
            title="Empty Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add(project)
        db_session.commit()

        suggestion = IntelligenceService.generate_unstuck_task_suggestion(db_session, project)

        assert "Review project status" in suggestion
        assert "Empty Project" in suggestion

    def test_no_next_action_defined(self, db_session: Session, sample_area: Area):
        """Test suggestion when no next action is defined."""
        project = Project(
            title="No Next Action Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add(project)
        db_session.commit()

        # Add pending tasks without next action
        task = Task(
            title="Pending Task",
            project_id=project.id,
            status="pending",
            priority=3,
            is_next_action=False,
        )
        db_session.add(task)
        db_session.commit()

        suggestion = IntelligenceService.generate_unstuck_task_suggestion(db_session, project)

        assert "Choose the next action" in suggestion

    def test_default_suggestion_with_stalled_time(self, db_session: Session, sample_area: Area):
        """Test suggestion includes stalled duration."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Stalled Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            stalled_since=now - timedelta(days=10),
        )
        db_session.add(project)
        db_session.commit()

        # Add a next action
        task = Task(
            title="Next Action",
            project_id=project.id,
            status="pending",
            priority=3,
            is_next_action=True,
        )
        db_session.add(task)
        db_session.commit()

        suggestion = IntelligenceService.generate_unstuck_task_suggestion(db_session, project)

        assert "10 days" in suggestion


class TestCreateUnstuckTask:
    """Test IntelligenceService create_unstuck_task."""

    def test_creates_task_with_custom_title(self, db_session: Session, sample_area: Area):
        """Test creating unstuck task with custom title."""
        project = Project(
            title="Test Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            stalled_since=datetime.now(timezone.utc) - timedelta(days=5),
        )
        db_session.add(project)
        db_session.commit()

        task = IntelligenceService.create_unstuck_task(
            db_session, project, title="Custom unstuck task", use_ai=False
        )

        assert task.title == "Custom unstuck task"
        assert task.is_unstuck_task is True
        assert task.is_next_action is True
        assert task.priority == 1
        assert task.estimated_minutes == 10

    def test_creates_task_with_generated_title(self, db_session: Session, sample_area: Area):
        """Test creating unstuck task with generated title."""
        project = Project(
            title="Stalled Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            stalled_since=datetime.now(timezone.utc) - timedelta(days=5),
        )
        db_session.add(project)
        db_session.commit()

        task = IntelligenceService.create_unstuck_task(db_session, project, use_ai=False)

        assert task.title is not None
        assert task.is_unstuck_task is True


class TestGetProjectHealthSummary:
    """Test IntelligenceService get_project_health_summary."""

    def test_health_summary_structure(self, db_session: Session, sample_area: Area):
        """Test health summary returns correct structure."""
        project = Project(
            title="Test Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        summary = IntelligenceService.get_project_health_summary(db_session, project)

        assert "project_id" in summary
        assert "title" in summary
        assert "momentum_score" in summary
        assert "health_status" in summary
        assert "tasks" in summary
        assert "recommendations" in summary
        assert summary["project_id"] == project.id

    def test_health_status_stalled(self, db_session: Session, sample_area: Area):
        """Test health status is stalled when project is stalled."""
        project = Project(
            title="Stalled Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.1,
            stalled_since=datetime.now(timezone.utc) - timedelta(days=10),
        )
        db_session.add(project)
        db_session.commit()

        summary = IntelligenceService.get_project_health_summary(db_session, project)

        assert summary["health_status"] == "stalled"
        assert summary["is_stalled"] is True

    def test_health_status_strong(self, db_session: Session, sample_area: Area):
        """Test health status is strong for high momentum."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Strong Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.85,
            last_activity_at=now - timedelta(days=1),
        )
        db_session.add(project)
        db_session.commit()

        summary = IntelligenceService.get_project_health_summary(db_session, project)

        assert summary["health_status"] == "strong"

    def test_health_summary_task_counts(self, db_session: Session, sample_area: Area):
        """Test health summary includes correct task counts."""
        project = Project(
            title="Project with Tasks",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        # Add tasks with various statuses
        tasks = [
            Task(title="Pending 1", project_id=project.id, status="pending", priority=3),
            Task(title="Pending 2", project_id=project.id, status="pending", priority=3),
            Task(title="Completed", project_id=project.id, status="completed", priority=3),
            Task(title="In Progress", project_id=project.id, status="in_progress", priority=3),
        ]
        db_session.add_all(tasks)
        db_session.commit()

        # Refresh to load tasks
        db_session.refresh(project)

        summary = IntelligenceService.get_project_health_summary(db_session, project)

        assert summary["tasks"]["total"] == 4
        assert summary["tasks"]["completed"] == 1
        assert summary["tasks"]["pending"] == 2
        assert summary["tasks"]["in_progress"] == 1
        assert summary["tasks"]["completion_percentage"] == 25.0


class TestGenerateRecommendations:
    """Test IntelligenceService _generate_recommendations."""

    def test_stalled_recommendations(self, db_session: Session, sample_area: Area):
        """Test recommendations for stalled project."""
        project = Project(
            title="Stalled",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.1,
        )

        recommendations = IntelligenceService._generate_recommendations(
            project, "stalled", 20, 0
        )

        assert any("stalled" in r.lower() for r in recommendations)

    def test_no_next_action_recommendation(self, db_session: Session, sample_area: Area):
        """Test recommendation when no next action defined."""
        project = Project(
            title="No Next Action",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.5,
        )

        recommendations = IntelligenceService._generate_recommendations(
            project, "moderate", 5, 0
        )

        assert any("next action" in r.lower() for r in recommendations)

    def test_too_many_next_actions_recommendation(self, db_session: Session, sample_area: Area):
        """Test recommendation when too many next actions."""
        project = Project(
            title="Many Next Actions",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.5,
        )

        recommendations = IntelligenceService._generate_recommendations(
            project, "moderate", 5, 5
        )

        assert any("too many" in r.lower() for r in recommendations)


class TestGetMomentumBreakdown:
    """Test IntelligenceService get_momentum_breakdown with beta formula."""

    def test_breakdown_structure(self, db_session: Session, sample_area: Area):
        """Test breakdown returns correct structure with updated factor names."""
        project = Project(
            title="Breakdown Test",
            status="active",
            priority=3,
            area_id=sample_area.id,
            momentum_score=0.5,
        )
        db_session.add(project)
        db_session.commit()

        breakdown = IntelligenceService.get_momentum_breakdown(db_session, project)

        assert "total_score" in breakdown
        assert "factors" in breakdown
        assert len(breakdown["factors"]) == 4
        factor_names = [f["name"] for f in breakdown["factors"]]
        assert "Recent Activity" in factor_names
        assert "Completion Rate" in factor_names
        assert "Next Action" in factor_names
        assert "Activity Frequency" in factor_names

    def test_breakdown_next_action_detail_graduated(self, db_session: Session, sample_area: Area):
        """BETA-001: Breakdown shows graduated next-action detail."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="NA Detail Test",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add(project)
        db_session.commit()

        # No next action → "Missing"
        breakdown = IntelligenceService.get_momentum_breakdown(db_session, project)
        na_factor = [f for f in breakdown["factors"] if f["name"] == "Next Action"][0]
        assert na_factor["detail"] == "Missing"
        assert na_factor["raw_score"] == 0.0


class TestGetWeeklyReviewData:
    """Test IntelligenceService get_weekly_review_data."""

    def test_weekly_review_structure(self, db_session: Session):
        """Test weekly review returns correct structure."""
        review = IntelligenceService.get_weekly_review_data(db_session)

        assert "review_date" in review
        assert "active_projects_count" in review
        assert "projects_needing_review" in review
        assert "tasks_completed_this_week" in review
        assert "projects_without_next_action" in review

    def test_weekly_review_counts_active_projects(self, db_session: Session, sample_area: Area):
        """Test weekly review counts active projects correctly."""
        active = Project(
            title="Active",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        completed = Project(
            title="Completed",
            status="completed",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add_all([active, completed])
        db_session.commit()

        review = IntelligenceService.get_weekly_review_data(db_session)

        assert review["active_projects_count"] == 1

    def test_weekly_review_finds_projects_needing_review(self, db_session: Session, sample_area: Area):
        """Test weekly review identifies projects needing review."""
        now = datetime.now(timezone.utc)
        stalled = Project(
            title="Stalled",
            status="active",
            priority=3,
            area_id=sample_area.id,
            stalled_since=now - timedelta(days=10),
        )
        healthy = Project(
            title="Healthy",
            status="active",
            priority=3,
            area_id=sample_area.id,
            last_activity_at=now - timedelta(days=1),
        )
        db_session.add_all([stalled, healthy])
        db_session.commit()

        review = IntelligenceService.get_weekly_review_data(db_session)

        assert review["projects_needing_review"] >= 1
        stalled_ids = [p["id"] for p in review["projects_needing_review_details"]]
        assert stalled.id in stalled_ids

    def test_weekly_review_counts_completions(self, db_session: Session, sample_area: Area):
        """Test weekly review counts completions this week."""
        now = datetime.now(timezone.utc)
        project = Project(
            title="Test Project",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add(project)
        db_session.commit()

        # Recent completion
        recent_task = Task(
            title="Recent Completion",
            project_id=project.id,
            status="completed",
            priority=3,
            completed_at=now - timedelta(days=2),
        )
        # Old completion
        old_task = Task(
            title="Old Completion",
            project_id=project.id,
            status="completed",
            priority=3,
            completed_at=now - timedelta(days=10),
        )
        db_session.add_all([recent_task, old_task])
        db_session.commit()

        review = IntelligenceService.get_weekly_review_data(db_session)

        assert review["tasks_completed_this_week"] == 1

    def test_weekly_review_finds_projects_without_next_action(self, db_session: Session, sample_area: Area):
        """Test weekly review identifies projects without next actions."""
        project_no_na = Project(
            title="No Next Action",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        project_with_na = Project(
            title="Has Next Action",
            status="active",
            priority=3,
            area_id=sample_area.id,
        )
        db_session.add_all([project_no_na, project_with_na])
        db_session.commit()

        # Add next action to one project
        next_action = Task(
            title="Next Action",
            project_id=project_with_na.id,
            status="pending",
            priority=3,
            is_next_action=True,
        )
        db_session.add(next_action)
        db_session.commit()

        # Refresh to load tasks
        db_session.refresh(project_no_na)
        db_session.refresh(project_with_na)

        review = IntelligenceService.get_weekly_review_data(db_session)

        assert review["projects_without_next_action"] >= 1
        no_na_ids = [p["id"] for p in review["projects_without_next_action_details"]]
        assert project_no_na.id in no_na_ids
