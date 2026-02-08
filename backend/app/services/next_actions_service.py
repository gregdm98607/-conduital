"""
Next Actions service - smart prioritization of next actions
"""

from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.project import Project
from app.models.task import Task


class NextActionsService:
    """Service for next action prioritization"""

    @staticmethod
    def get_prioritized_next_actions(
        db: Session,
        context: Optional[str] = None,
        energy_level: Optional[str] = None,
        time_available: Optional[int] = None,
        include_stalled: bool = True,
        limit: int = 20,
    ) -> list[Task]:
        """
        Get prioritized list of next actions

        Prioritization logic:
        1. Stalled projects with unstuck tasks (if include_stalled)
        2. High momentum projects with due dates
        3. Medium momentum projects
        4. Recently started tasks (minimize context switching)

        Args:
            db: Database session
            context: Filter by context
            energy_level: Filter by energy level
            time_available: Filter by estimated time (minutes)
            include_stalled: Include unstuck tasks from stalled projects
            limit: Maximum results

        Returns:
            List of prioritized tasks
        """
        # Build query for next actions
        # Exclude deferred tasks (defer_until in the future) — they aren't actionable yet.
        # Over the Horizon display is handled by the urgency_zone field on tasks.
        today = date.today()
        query = (
            select(Task)
            .join(Project)
            .where(
                Task.is_next_action.is_(True),
                Task.status.in_(["pending", "in_progress"]),
                Project.status == "active",
                (Task.defer_until.is_(None)) | (Task.defer_until <= today),
            )
        )

        # Apply filters
        if context:
            query = query.where(Task.context == context)
        if energy_level:
            query = query.where(Task.energy_level == energy_level)
        if time_available:
            query = query.where(
                (Task.estimated_minutes.is_(None)) | (Task.estimated_minutes <= time_available)
            )

        # Load project relationship for sorting
        query = query.options(joinedload(Task.project))

        # Execute query
        tasks = list(db.execute(query).unique().scalars().all())

        # Sort by priority (using custom logic)

        def priority_key(task: Task) -> tuple:
            project = task.project

            # Priority tier 0: Unstuck tasks for stalled projects
            if include_stalled and project.stalled_since and task.is_unstuck_task:
                return (0, -project.momentum_score, task.priority, task.due_date or date.max)

            # Priority tier 1: Tasks due soon (within 3 days)
            if task.due_date and task.due_date <= today + timedelta(days=3):
                return (1, task.due_date, task.priority, -project.momentum_score)

            # Priority tier 2: High momentum projects
            if project.momentum_score > 0.7:
                return (2, -project.momentum_score, task.priority, task.due_date or date.max)

            # Priority tier 3: Tasks already in progress
            if task.started_at:
                return (3, task.started_at, task.priority, -project.momentum_score)

            # Priority tier 4: Medium momentum projects
            if project.momentum_score > 0.4:
                return (4, -project.momentum_score, task.priority, task.due_date or date.max)

            # Priority tier 5: Low momentum projects
            return (5, -project.momentum_score, task.priority, task.due_date or date.max)

        tasks.sort(key=priority_key)

        return tasks[:limit]

    @staticmethod
    def get_next_actions_by_context(db: Session, limit_per_context: int = 10) -> dict[str, list[Task]]:
        """
        Get next actions grouped by context

        Args:
            db: Database session
            limit_per_context: Tasks per context

        Returns:
            Dictionary mapping context to tasks
        """
        # Get all next actions
        query = (
            select(Task)
            .join(Project)
            .where(
                Task.is_next_action.is_(True),
                Task.status.in_(["pending", "in_progress"]),
                Task.context.is_not(None),
                Project.status == "active",
            )
            .options(joinedload(Task.project))
        )

        tasks = list(db.execute(query).unique().scalars().all())

        # Group by context
        by_context: dict[str, list[Task]] = {}
        for task in tasks:
            if task.context not in by_context:
                by_context[task.context] = []
            by_context[task.context].append(task)

        # Sort and limit each context group
        for context, context_tasks in by_context.items():
            context_tasks.sort(
                key=lambda t: (
                    -t.project.momentum_score,
                    t.priority,
                    t.due_date or date.max,
                )
            )
            by_context[context] = context_tasks[:limit_per_context]

        return by_context

    @staticmethod
    def get_stalled_projects_count(db: Session) -> int:
        """
        Get count of stalled projects

        Args:
            db: Database session

        Returns:
            Count of stalled projects
        """
        query = select(Project).where(
            Project.status == "active",
            Project.stalled_since.is_not(None),
        )

        count = len(list(db.execute(query).scalars().all()))
        return count

    @staticmethod
    def get_daily_dashboard(db: Session) -> dict:
        """
        Get daily dashboard data

        Returns:
            Dashboard data dictionary
        """
        # Get top 3 priority tasks
        top_3 = NextActionsService.get_prioritized_next_actions(
            db, include_stalled=True, limit=3
        )

        # Get quick wins (< 15 min)
        quick_wins_query = (
            select(Task)
            .join(Project)
            .where(
                Task.is_next_action.is_(True),
                Task.status == "pending",
                Task.estimated_minutes.is_not(None),
                Task.estimated_minutes <= 15,
                Project.status == "active",
            )
            .options(joinedload(Task.project))
            .order_by(Task.estimated_minutes, Task.priority)
            .limit(5)
        )
        quick_wins = list(db.execute(quick_wins_query).unique().scalars().all())

        # Get tasks due today
        due_today_query = (
            select(Task)
            .join(Project)
            .where(
                Task.due_date == date.today(),
                Task.status.in_(["pending", "in_progress"]),
                Project.status == "active",
            )
            .options(joinedload(Task.project))
            .order_by(Task.priority)
        )
        due_today = list(db.execute(due_today_query).unique().scalars().all())

        # Get stalled projects count
        stalled_count = NextActionsService.get_stalled_projects_count(db)

        # Get project momentum summary
        momentum_query = (
            select(Project)
            .where(Project.status == "active")
            .order_by(Project.momentum_score.desc())
            .limit(10)
        )
        top_projects = list(db.execute(momentum_query).scalars().all())

        return {
            "top_3_priorities": top_3,
            "quick_wins": quick_wins,
            "due_today": due_today,
            "stalled_projects_count": stalled_count,
            "top_momentum_projects": top_projects,
        }
