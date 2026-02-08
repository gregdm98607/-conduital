"""
Intelligence service - Momentum calculation, stalled detection, AI features
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.db_utils import ensure_unique_file_marker, log_activity, update_project_activity
from app.models.activity_log import ActivityLog
from app.models.area import Area
from app.models.inbox import InboxItem
from app.models.project import Project
from app.models.task import Task


def _ensure_tz_aware(dt: datetime | None) -> datetime | None:
    """Ensure datetime is timezone-aware (assume UTC if naive)"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class IntelligenceService:
    """Service for intelligent project management features"""

    @staticmethod
    def calculate_momentum_score(db: Session, project: Project) -> float:
        """
        Calculate project momentum score (0.0 to 1.0)

        Factors:
        - Recent activity (40% weight): Days since last activity
        - Completion rate (30% weight): Recent task completions
        - Next action availability (20% weight): Has clear next action
        - Activity frequency (10% weight): Number of recent activities

        Args:
            db: Database session
            project: Project instance

        Returns:
            Momentum score (0.0-1.0)
        """
        now = datetime.now(timezone.utc)
        score = 0.0

        # Factor 1: Days since last activity (40% weight)
        if project.last_activity_at:
            last_activity = _ensure_tz_aware(project.last_activity_at)
            days_since = (now - last_activity).days
            # Decay over MOMENTUM_ACTIVITY_DECAY_DAYS (default 30)
            decay_days = settings.MOMENTUM_ACTIVITY_DECAY_DAYS
            activity_score = max(0, 1 - (days_since / decay_days))
            score += activity_score * 0.4
        else:
            # No activity yet
            score += 0.0

        # Factor 2: Recent completion rate (30% weight)
        # Tasks completed in last 7 days vs total recent tasks
        recent_date = now - timedelta(days=7)
        recent_tasks = (
            db.execute(
                select(Task)
                .where(
                    Task.project_id == project.id,
                    Task.created_at >= recent_date,
                )
            )
            .scalars()
            .all()
        )

        if recent_tasks:
            completed = sum(1 for t in recent_tasks if t.status == "completed")
            completion_rate = completed / len(recent_tasks)
            score += completion_rate * 0.3

        # Factor 3: Has clear next action (20% weight)
        has_next_action = (
            db.execute(
                select(Task)
                .where(
                    Task.project_id == project.id,
                    Task.is_next_action.is_(True),
                    Task.status == "pending",
                )
                .limit(1)
            )
            .scalar_one_or_none()
            is not None
        )

        if has_next_action:
            score += 0.2

        # Factor 4: Activity frequency (10% weight)
        # Count activities in last 14 days
        activity_count = db.execute(
            select(func.count(ActivityLog.id))
            .where(
                ActivityLog.entity_type == "project",
                ActivityLog.entity_id == project.id,
                ActivityLog.timestamp >= now - timedelta(days=14),
            )
        ).scalar_one()

        frequency_score = min(1.0, activity_count / 10)  # Cap at 10 activities
        score += frequency_score * 0.1

        return round(score, 2)

    @staticmethod
    def get_momentum_breakdown(db: Session, project: Project) -> dict:
        """
        Get detailed breakdown of momentum score factors.

        Returns individual factor scores, weights, and metadata
        so users can understand why their score is what it is.
        """
        now = datetime.now(timezone.utc)

        # Factor 1: Activity recency (40%)
        days_since_activity = None
        activity_raw = 0.0
        if project.last_activity_at:
            last_activity = _ensure_tz_aware(project.last_activity_at)
            days_since_activity = (now - last_activity).days
            decay_days = settings.MOMENTUM_ACTIVITY_DECAY_DAYS
            activity_raw = max(0, 1 - (days_since_activity / decay_days))

        # Factor 2: Completion rate (30%)
        recent_date = now - timedelta(days=7)
        recent_tasks = (
            db.execute(
                select(Task).where(
                    Task.project_id == project.id,
                    Task.created_at >= recent_date,
                )
            )
            .scalars()
            .all()
        )
        recent_total = len(recent_tasks)
        recent_completed = sum(1 for t in recent_tasks if t.status == "completed")
        completion_raw = (recent_completed / recent_total) if recent_total > 0 else 0.0

        # Factor 3: Next action (20%)
        has_next_action = (
            db.execute(
                select(Task)
                .where(
                    Task.project_id == project.id,
                    Task.is_next_action.is_(True),
                    Task.status == "pending",
                )
                .limit(1)
            )
            .scalar_one_or_none()
            is not None
        )
        next_action_raw = 1.0 if has_next_action else 0.0

        # Factor 4: Activity frequency (10%)
        activity_count = db.execute(
            select(func.count(ActivityLog.id)).where(
                ActivityLog.entity_type == "project",
                ActivityLog.entity_id == project.id,
                ActivityLog.timestamp >= now - timedelta(days=14),
            )
        ).scalar_one()
        frequency_raw = min(1.0, activity_count / 10)

        # Weighted scores
        activity_weighted = round(activity_raw * 0.4, 3)
        completion_weighted = round(completion_raw * 0.3, 3)
        next_action_weighted = round(next_action_raw * 0.2, 3)
        frequency_weighted = round(frequency_raw * 0.1, 3)
        total = round(activity_weighted + completion_weighted + next_action_weighted + frequency_weighted, 2)

        return {
            "total_score": total,
            "factors": [
                {
                    "name": "Recent Activity",
                    "weight": 0.4,
                    "raw_score": round(activity_raw, 3),
                    "weighted_score": activity_weighted,
                    "detail": f"{days_since_activity}d ago" if days_since_activity is not None else "No activity",
                },
                {
                    "name": "Completion Rate",
                    "weight": 0.3,
                    "raw_score": round(completion_raw, 3),
                    "weighted_score": completion_weighted,
                    "detail": f"{recent_completed}/{recent_total} tasks (7d)",
                },
                {
                    "name": "Next Action",
                    "weight": 0.2,
                    "raw_score": round(next_action_raw, 3),
                    "weighted_score": next_action_weighted,
                    "detail": "Defined" if has_next_action else "Missing",
                },
                {
                    "name": "Activity Frequency",
                    "weight": 0.1,
                    "raw_score": round(frequency_raw, 3),
                    "weighted_score": frequency_weighted,
                    "detail": f"{activity_count} actions (14d)",
                },
            ],
        }

    @staticmethod
    def update_all_momentum_scores(db: Session) -> dict:
        """
        Update momentum scores for all active projects.

        Batch-loads data to avoid N+1 queries:
        - 1 query for active projects
        - 1 query for all recent tasks across projects
        - 1 query for all next actions across projects
        - 1 query for all activity counts across projects

        Args:
            db: Database session

        Returns:
            Statistics dict
        """
        now = datetime.now(timezone.utc)

        projects = db.execute(
            select(Project).where(Project.status == "active")
        ).scalars().all()

        if not projects:
            return {"updated": 0, "stalled_detected": 0, "unstalled": 0}

        project_ids = [p.id for p in projects]

        # Batch: recent tasks (last 7 days) grouped by project
        recent_date = now - timedelta(days=7)
        recent_tasks = db.execute(
            select(Task).where(
                Task.project_id.in_(project_ids),
                Task.created_at >= recent_date,
            )
        ).scalars().all()

        recent_by_project: dict[int, list] = {pid: [] for pid in project_ids}
        for t in recent_tasks:
            recent_by_project[t.project_id].append(t)

        # Batch: projects that have a pending next action
        next_action_project_ids = set(
            row[0] for row in db.execute(
                select(Task.project_id).where(
                    Task.project_id.in_(project_ids),
                    Task.is_next_action.is_(True),
                    Task.status == "pending",
                ).distinct()
            ).all()
        )

        # Batch: activity counts per project (last 14 days)
        activity_date = now - timedelta(days=14)
        activity_rows = db.execute(
            select(ActivityLog.entity_id, func.count(ActivityLog.id))
            .where(
                ActivityLog.entity_type == "project",
                ActivityLog.entity_id.in_(project_ids),
                ActivityLog.timestamp >= activity_date,
            )
            .group_by(ActivityLog.entity_id)
        ).all()
        activity_counts: dict[int, int] = {row[0]: row[1] for row in activity_rows}

        # Calculate scores using pre-loaded data
        decay_days = settings.MOMENTUM_ACTIVITY_DECAY_DAYS
        threshold_days = settings.MOMENTUM_STALLED_THRESHOLD_DAYS
        stats = {"updated": 0, "stalled_detected": 0, "unstalled": 0}

        for project in projects:
            score = 0.0

            # Factor 1: Activity recency (40%)
            if project.last_activity_at:
                last_activity = _ensure_tz_aware(project.last_activity_at)
                days_since = (now - last_activity).days
                score += max(0, 1 - (days_since / decay_days)) * 0.4

            # Factor 2: Completion rate (30%)
            proj_recent = recent_by_project.get(project.id, [])
            if proj_recent:
                completed = sum(1 for t in proj_recent if t.status == "completed")
                score += (completed / len(proj_recent)) * 0.3

            # Factor 3: Next action (20%)
            if project.id in next_action_project_ids:
                score += 0.2

            # Factor 4: Activity frequency (10%)
            act_count = activity_counts.get(project.id, 0)
            score += min(1.0, act_count / 10) * 0.1

            project.momentum_score = round(score, 2)
            stats["updated"] += 1

            # Stalled detection
            if project.last_activity_at:
                last_activity = _ensure_tz_aware(project.last_activity_at)
                days_since = (now - last_activity).days

                if days_since >= threshold_days and not project.stalled_since:
                    project.stalled_since = now
                    stats["stalled_detected"] += 1
                    log_activity(
                        db,
                        entity_type="project",
                        entity_id=project.id,
                        action_type="stalled_detected",
                        details={"days_since_activity": days_since},
                        source="system",
                    )
                elif days_since < threshold_days and project.stalled_since:
                    project.stalled_since = None
                    stats["unstalled"] += 1
                    log_activity(
                        db,
                        entity_type="project",
                        entity_id=project.id,
                        action_type="unstalled",
                        source="system",
                    )

        db.commit()
        return stats

    @staticmethod
    def detect_stalled_projects(db: Session) -> list[Project]:
        """
        Detect stalled projects

        A project is stalled if:
        - No activity for MOMENTUM_STALLED_THRESHOLD_DAYS (default 14)
        - Momentum score < 0.2
        - Has pending tasks but no next action

        Args:
            db: Database session

        Returns:
            List of stalled projects
        """
        stalled = db.execute(
            select(Project).where(
                Project.status == "active",
                Project.stalled_since.is_not(None),
            )
        ).scalars().all()

        return list(stalled)

    @staticmethod
    def generate_unstuck_task_suggestion(db: Session, project: Project) -> str:
        """
        Generate suggestion for an unstuck task (without AI)

        Creates a minimal viable task suggestion based on project state

        Args:
            db: Database session
            project: Stalled project

        Returns:
            Task title suggestion
        """
        # Get recent activity to understand context
        recent_activity = db.execute(
            select(ActivityLog)
            .where(
                ActivityLog.entity_type == "project",
                ActivityLog.entity_id == project.id,
            )
            .order_by(ActivityLog.timestamp.desc())
            .limit(5)
        ).scalars().all()

        # Get pending tasks
        pending_tasks = db.execute(
            select(Task)
            .where(
                Task.project_id == project.id,
                Task.status == "pending",
            )
            .limit(3)
        ).scalars().all()

        # Generate suggestions based on state
        if not pending_tasks:
            return f"Review project status and define next steps for {project.title}"

        if not any(t.is_next_action for t in pending_tasks):
            return f"Choose the next action from {len(pending_tasks)} pending tasks"

        # Default: Review and update
        stalled_since = _ensure_tz_aware(project.stalled_since)
        days_stalled = (datetime.now(timezone.utc) - stalled_since).days if stalled_since else 0
        return f"Review project after {days_stalled} days and update status"

    @staticmethod
    def create_unstuck_task(
        db: Session, project: Project, title: Optional[str] = None, use_ai: bool = True
    ) -> Task:
        """
        Create an unstuck task for a stalled project

        Args:
            db: Database session
            project: Stalled project
            title: Optional custom title
            use_ai: Whether to use AI for task generation (default True)

        Returns:
            Created unstuck task
        """
        if not title:
            if use_ai:
                # Try AI generation first
                from app.core.config import settings

                if settings.AI_FEATURES_ENABLED and settings.ANTHROPIC_API_KEY:
                    try:
                        from app.services.ai_service import AIService

                        ai_service = AIService()
                        title = ai_service.generate_unstuck_task(db, project)
                    except Exception as e:
                        logger.warning(f"AI generation failed, using fallback: {e}")
                        title = IntelligenceService.generate_unstuck_task_suggestion(
                            db, project
                        )
                else:
                    # Fallback to non-AI
                    title = IntelligenceService.generate_unstuck_task_suggestion(
                        db, project
                    )
            else:
                # Use non-AI generation
                title = IntelligenceService.generate_unstuck_task_suggestion(db, project)

        task = Task(
            project_id=project.id,
            title=title,
            description=f"Minimal task to restart project momentum (auto-generated)",
            status="pending",
            is_next_action=True,
            is_unstuck_task=True,
            estimated_minutes=10,
            context="quick_win",
            energy_level="low",
            priority=1,
            file_marker=ensure_unique_file_marker(),
        )

        db.add(task)
        db.flush()

        # Update project activity
        update_project_activity(db, project.id, source="system")

        log_activity(
            db,
            entity_type="task",
            entity_id=task.id,
            action_type="created",
            details={"auto_generated": True, "unstuck_task": True, "ai_generated": use_ai},
            source="system",
        )

        db.commit()
        return task

    @staticmethod
    def get_project_health_summary(db: Session, project: Project) -> dict:
        """
        Get comprehensive health summary for a project

        Args:
            db: Database session
            project: Project instance

        Returns:
            Health summary dict
        """
        # Calculate momentum if not yet calculated
        if project.momentum_score is None:
            project.momentum_score = IntelligenceService.calculate_momentum_score(db, project)
            db.commit()

        # Get task statistics
        tasks = project.tasks
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        pending = sum(1 for t in tasks if t.status == "pending")
        in_progress = sum(1 for t in tasks if t.status == "in_progress")
        waiting = sum(1 for t in tasks if t.status == "waiting")
        next_actions = sum(1 for t in tasks if t.is_next_action and t.status != "completed")

        # Determine health status
        days_since_activity = None
        if project.last_activity_at:
            last_activity = _ensure_tz_aware(project.last_activity_at)
            days_since_activity = (datetime.now(timezone.utc) - last_activity).days

        if project.stalled_since:
            health_status = "stalled"
        elif days_since_activity and days_since_activity > settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS:
            health_status = "at_risk"
        elif project.momentum_score > 0.7:
            health_status = "strong"
        elif project.momentum_score > 0.4:
            health_status = "moderate"
        else:
            health_status = "weak"

        # Get recent activity count
        recent_activity_count = db.execute(
            select(func.count(ActivityLog.id))
            .where(
                ActivityLog.entity_type == "project",
                ActivityLog.entity_id == project.id,
                ActivityLog.timestamp >= datetime.now(timezone.utc) - timedelta(days=7),
            )
        ).scalar_one()

        return {
            "project_id": project.id,
            "title": project.title,
            "momentum_score": project.momentum_score,
            "health_status": health_status,
            "days_since_activity": days_since_activity,
            "is_stalled": bool(project.stalled_since),
            "stalled_since": project.stalled_since.isoformat() if project.stalled_since else None,
            "tasks": {
                "total": total_tasks,
                "completed": completed,
                "pending": pending,
                "in_progress": in_progress,
                "waiting": waiting,
                "completion_percentage": (completed / total_tasks * 100) if total_tasks > 0 else 0,
            },
            "next_actions_count": next_actions,
            "recent_activity_count": recent_activity_count,
            "recommendations": IntelligenceService._generate_recommendations(
                project, health_status, days_since_activity, next_actions
            ),
        }

    @staticmethod
    def _generate_recommendations(
        project: Project,
        health_status: str,
        days_since_activity: Optional[int],
        next_actions_count: int,
    ) -> list[str]:
        """Generate actionable recommendations"""
        recommendations = []

        if health_status == "stalled":
            recommendations.append("Project is stalled - create an unstuck task to restart momentum")
            recommendations.append(f"Review project goals and verify it's still active")

        elif health_status == "at_risk":
            recommendations.append(f"No activity for {days_since_activity} days - schedule review")
            recommendations.append("Create clear next action to maintain momentum")

        if next_actions_count == 0:
            recommendations.append("No next action defined - choose the very next physical action")

        if next_actions_count > 3:
            recommendations.append("Too many next actions - focus on one primary next action")

        if project.momentum_score < 0.3:
            recommendations.append("Low momentum - consider 15-minute quick win to build momentum")

        if not recommendations:
            recommendations.append("Project healthy - keep up the momentum!")

        return recommendations

    @staticmethod
    def calculate_area_health_score(db: Session, area: Area) -> float:
        """
        Calculate area health score (0.0 to 1.0)

        Factors:
        - Average project momentum (40%): Weighted avg of active project scores
        - Non-stalled ratio (25%): Ratio of active projects that are not stalled
        - Review freshness (20%): Decay since last review
        - Active project count (15%): Sweet spot is 3-7 projects

        Args:
            db: Database session
            area: Area instance (with projects loaded)

        Returns:
            Health score (0.0-1.0)
        """
        now = datetime.now(timezone.utc)
        score = 0.0

        active_projects = [p for p in area.projects if p.status == "active"]
        active_count = len(active_projects)

        # Factor 1: Average project momentum (40%)
        if active_projects:
            avg_momentum = sum(p.momentum_score for p in active_projects) / active_count
            score += avg_momentum * 0.4
        # No active projects = 0 for this factor

        # Factor 2: Non-stalled ratio (25%)
        if active_projects:
            non_stalled = sum(1 for p in active_projects if not p.stalled_since)
            stalled_ratio = non_stalled / active_count
            score += stalled_ratio * 0.25

        # Factor 3: Review freshness (20%)
        if area.last_reviewed_at:
            last_review = _ensure_tz_aware(area.last_reviewed_at)
            days_since_review = (now - last_review).days
            # Map review_frequency to expected interval
            freq_days = {"daily": 1, "weekly": 7, "monthly": 30}
            expected_interval = freq_days.get(area.review_frequency, 7)
            # Score decays as review becomes overdue
            freshness = max(0, 1 - (days_since_review / (expected_interval * 3)))
            score += freshness * 0.2
        # No review = 0 for this factor

        # Factor 4: Active project count sweet spot (15%)
        # Sweet spot: 3-7 projects gives full score
        # Too few (0-1) or too many (10+) reduces score
        if active_count == 0:
            count_score = 0.0
        elif 3 <= active_count <= 7:
            count_score = 1.0
        elif active_count < 3:
            count_score = active_count / 3.0
        else:
            count_score = max(0.3, 1.0 - ((active_count - 7) * 0.1))
        score += count_score * 0.15

        return round(score, 2)

    @staticmethod
    def get_area_health_breakdown(db: Session, area: Area) -> dict:
        """Get detailed breakdown of area health score factors."""
        now = datetime.now(timezone.utc)

        active_projects = [p for p in area.projects if p.status == "active"]
        active_count = len(active_projects)

        # Factor 1: Avg momentum
        avg_momentum = (sum(p.momentum_score for p in active_projects) / active_count) if active_count else 0.0
        momentum_weighted = round(avg_momentum * 0.4, 3)

        # Factor 2: Non-stalled ratio
        non_stalled = sum(1 for p in active_projects if not p.stalled_since) if active_count else 0
        stalled_ratio = (non_stalled / active_count) if active_count else 0.0
        stalled_weighted = round(stalled_ratio * 0.25, 3)
        stalled_count = active_count - non_stalled

        # Factor 3: Review freshness
        days_since_review = None
        freshness_raw = 0.0
        if area.last_reviewed_at:
            last_review = _ensure_tz_aware(area.last_reviewed_at)
            days_since_review = (now - last_review).days
            freq_days = {"daily": 1, "weekly": 7, "monthly": 30}
            expected_interval = freq_days.get(area.review_frequency, 7)
            freshness_raw = max(0, 1 - (days_since_review / (expected_interval * 3)))
        freshness_weighted = round(freshness_raw * 0.2, 3)

        # Factor 4: Active project count
        if active_count == 0:
            count_raw = 0.0
        elif 3 <= active_count <= 7:
            count_raw = 1.0
        elif active_count < 3:
            count_raw = active_count / 3.0
        else:
            count_raw = max(0.3, 1.0 - ((active_count - 7) * 0.1))
        count_weighted = round(count_raw * 0.15, 3)

        total = round(momentum_weighted + stalled_weighted + freshness_weighted + count_weighted, 2)

        return {
            "total_score": total,
            "factors": [
                {
                    "name": "Project Momentum",
                    "weight": 0.4,
                    "raw_score": round(avg_momentum, 3),
                    "weighted_score": momentum_weighted,
                    "detail": f"Avg {avg_momentum:.0%} across {active_count} projects",
                },
                {
                    "name": "Stalled Ratio",
                    "weight": 0.25,
                    "raw_score": round(stalled_ratio, 3),
                    "weighted_score": stalled_weighted,
                    "detail": f"{stalled_count} stalled of {active_count} active",
                },
                {
                    "name": "Review Freshness",
                    "weight": 0.2,
                    "raw_score": round(freshness_raw, 3),
                    "weighted_score": freshness_weighted,
                    "detail": f"{days_since_review}d since review" if days_since_review is not None else "Never reviewed",
                },
                {
                    "name": "Project Count",
                    "weight": 0.15,
                    "raw_score": round(count_raw, 3),
                    "weighted_score": count_weighted,
                    "detail": f"{active_count} active (sweet spot: 3-7)",
                },
            ],
        }

    @staticmethod
    def update_all_area_health_scores(db: Session) -> dict:
        """
        Update health scores for all areas.

        Args:
            db: Database session

        Returns:
            Statistics dict
        """
        areas = db.execute(
            select(Area)
            .where(Area.is_archived.is_(False))
            .options(joinedload(Area.projects))
        ).unique().scalars().all()

        stats = {"updated": 0}
        for area in areas:
            area.health_score = IntelligenceService.calculate_area_health_score(db, area)
            stats["updated"] += 1

        db.commit()
        return stats

    @staticmethod
    def get_weekly_review_data(db: Session) -> dict:
        """
        Generate data for GTD weekly review

        Returns:
            Weekly review summary
        """
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # Active projects (eagerly load tasks to avoid N+1)
        active_projects = db.execute(
            select(Project)
            .where(Project.status == "active")
            .options(joinedload(Project.tasks))
        ).unique().scalars().all()

        # Projects needing review (stalled or at risk)
        needs_review = [
            p for p in active_projects
            if p.stalled_since or (
                p.last_activity_at and
                (now - _ensure_tz_aware(p.last_activity_at)).days > settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS
            )
        ]

        # Completed this week
        completed_this_week = db.execute(
            select(func.count(Task.id))
            .where(
                Task.status == "completed",
                Task.completed_at >= week_ago,
            )
        ).scalar_one()

        # Projects without next actions (tasks already loaded above)
        projects_no_next_action = [
            p for p in active_projects
            if not any(t.is_next_action and t.status == "pending" for t in p.tasks)
        ]

        # Inbox count (unprocessed items)
        inbox_count = db.execute(
            select(func.count(InboxItem.id))
            .where(InboxItem.processed_at.is_(None))
        ).scalar_one()

        # Someday/Maybe count
        someday_maybe_count = db.execute(
            select(func.count(Project.id))
            .where(Project.status == "someday_maybe")
        ).scalar_one()

        return {
            "review_date": now.isoformat(),
            "active_projects_count": len(active_projects),
            "projects_needing_review": len(needs_review),
            "projects_without_next_action": len(projects_no_next_action),
            "tasks_completed_this_week": completed_this_week,
            "inbox_count": inbox_count,
            "someday_maybe_count": someday_maybe_count,
            "projects_needing_review_details": [
                {
                    "id": p.id,
                    "title": p.title,
                    "days_since_activity": (now - _ensure_tz_aware(p.last_activity_at)).days if p.last_activity_at else None,
                    "is_stalled": bool(p.stalled_since),
                }
                for p in needs_review
            ],
            "projects_without_next_action_details": [
                {"id": p.id, "title": p.title}
                for p in projects_no_next_action
            ],
        }
