"""
Project service - business logic for projects
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.db_utils import ensure_tz_aware, log_activity, soft_delete, update_project_activity
from app.models.area import Area
from app.models.project import Project
from app.models.task import Task
from app.schemas.project import ProjectCreate, ProjectHealth, ProjectUpdate


REVIEW_FREQ_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def _calculate_next_review_date(frequency: str, base_date: date | None = None) -> date:
    """Calculate next review date from frequency and a base date (defaults to today)."""
    days = REVIEW_FREQ_DAYS.get(frequency, 7)
    return (base_date or date.today()) + timedelta(days=days)


class ProjectService:
    """Service for project operations"""

    @staticmethod
    def get_all(
        db: Session,
        status: Optional[str] = None,
        area_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Project], int]:
        """
        Get all projects with optional filtering

        Args:
            db: Database session
            status: Filter by status
            area_id: Filter by area
            skip: Offset for pagination
            limit: Limit for pagination

        Returns:
            Tuple of (projects, total_count)
        """
        # Base filter query (reused for count and main query)
        base = select(Project).where(Project.deleted_at.is_(None))
        if status:
            base = base.where(Project.status == status)
        if area_id:
            base = base.where(Project.area_id == area_id)

        # Get total count
        count_query = select(func.count()).select_from(base.subquery())
        total = db.execute(count_query).scalar_one()

        # Task count subqueries (avoid N+1 by annotating in SQL, exclude soft-deleted)
        task_count_sq = (
            select(func.count(Task.id))
            .where(Task.project_id == Project.id, Task.deleted_at.is_(None))
            .correlate(Project)
            .scalar_subquery()
            .label("task_count")
        )
        completed_task_count_sq = (
            select(func.count(Task.id))
            .where(Task.project_id == Project.id, Task.deleted_at.is_(None), Task.status == "completed")
            .correlate(Project)
            .scalar_subquery()
            .label("completed_task_count")
        )

        # Main query with task count annotations
        query = (
            base.add_columns(task_count_sq, completed_task_count_sq)
            .options(joinedload(Project.area))
            .order_by(Project.momentum_score.desc(), Project.priority)
            .offset(skip)
            .limit(limit)
        )

        rows = db.execute(query).unique().all()
        # Attach task counts as attributes on each project ORM object
        projects = []
        for project, task_count, completed_task_count in rows:
            project.task_count = task_count
            project.completed_task_count = completed_task_count
            projects.append(project)

        return projects, total

    @staticmethod
    def get_by_id(db: Session, project_id: int, include_tasks: bool = False) -> Optional[Project]:
        """
        Get project by ID

        Args:
            db: Database session
            project_id: Project ID
            include_tasks: Whether to include tasks

        Returns:
            Project or None
        """
        query = select(Project).where(Project.id == project_id, Project.deleted_at.is_(None))

        # Always load area relationship
        query = query.options(joinedload(Project.area))

        if include_tasks:
            query = query.options(joinedload(Project.tasks))

        project = db.execute(query).unique().scalar_one_or_none()

        if project is not None:
            if include_tasks and project.tasks is not None:
                # Compute from already-loaded tasks (no extra query)
                project.task_count = len(project.tasks)
                project.completed_task_count = sum(
                    1 for t in project.tasks if t.status == "completed"
                )
            else:
                # Use SQL count queries (exclude soft-deleted tasks)
                project.task_count = db.execute(
                    select(func.count(Task.id)).where(
                        Task.project_id == project_id, Task.deleted_at.is_(None)
                    )
                ).scalar_one()
                project.completed_task_count = db.execute(
                    select(func.count(Task.id)).where(
                        Task.project_id == project_id, Task.deleted_at.is_(None), Task.status == "completed"
                    )
                ).scalar_one()

        return project

    @staticmethod
    def create(db: Session, project_data: ProjectCreate) -> Project:
        """
        Create a new project

        Args:
            db: Database session
            project_data: Project creation data

        Returns:
            Created project
        """
        project = Project(**project_data.model_dump())
        project.last_activity_at = datetime.now(timezone.utc)
        # Auto-set initial next_review_date from review_frequency
        project.next_review_date = _calculate_next_review_date(project.review_frequency)

        db.add(project)
        db.flush()

        # Log activity
        log_activity(
            db,
            entity_type="project",
            entity_id=project.id,
            action_type="created",
            details={"title": project.title, "status": project.status},
        )

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def update(db: Session, project_id: int, project_data: ProjectUpdate) -> Optional[Project]:
        """
        Update a project

        Args:
            db: Database session
            project_id: Project ID
            project_data: Update data

        Returns:
            Updated project or None
        """
        project = db.get(Project, project_id)
        if not project or project.deleted_at is not None:
            return None

        # Track changes for activity log
        changes = {}
        update_dict = project_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            if getattr(project, field) != value:
                changes[field] = {"old": getattr(project, field), "new": value}
                setattr(project, field, value)

        # If review_frequency changed, recompute next_review_date
        if "review_frequency" in changes:
            base = project.last_reviewed_at.date() if project.last_reviewed_at else date.today()
            project.next_review_date = _calculate_next_review_date(project.review_frequency, base)

        if changes:
            # Update activity timestamp
            update_project_activity(db, project_id)

            # Log activity
            log_activity(
                db,
                entity_type="project",
                entity_id=project_id,
                action_type="updated",
                details=changes,
            )

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete(db: Session, project_id: int) -> bool:
        """
        Delete a project

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            True if deleted, False if not found
        """
        project = db.get(Project, project_id)
        if not project or project.deleted_at is not None:
            return False

        # Log activity before soft deletion
        log_activity(
            db,
            entity_type="project",
            entity_id=project_id,
            action_type="deleted",
            details={"title": project.title},
        )

        soft_delete(db, project)
        # Also soft-delete child tasks
        for task in project.tasks:
            if task.deleted_at is None:
                soft_delete(db, task)
        db.commit()
        return True

    @staticmethod
    def change_status(db: Session, project_id: int, new_status: str) -> Optional[Project]:
        """
        Change project status

        Args:
            db: Database session
            project_id: Project ID
            new_status: New status value

        Returns:
            Updated project or None
        """
        project = db.get(Project, project_id)
        if not project or project.deleted_at is not None:
            return None

        old_status = project.status
        project.status = new_status

        # Set completed_at if completing
        if new_status == "completed" and not project.completed_at:
            project.completed_at = datetime.now(timezone.utc)

        # Update activity
        update_project_activity(db, project_id)

        # Log activity
        log_activity(
            db,
            entity_type="project",
            entity_id=project_id,
            action_type="status_changed",
            details={"old_status": old_status, "new_status": new_status},
        )

        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_health(db: Session, project_id: int) -> Optional[ProjectHealth]:
        """
        Get project health metrics

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            ProjectHealth or None
        """
        project = ProjectService.get_by_id(db, project_id, include_tasks=True)
        if not project:
            return None

        # Calculate task statistics
        total_tasks = len(project.tasks)
        completed_tasks = sum(1 for t in project.tasks if t.status == "completed")
        pending_tasks = sum(1 for t in project.tasks if t.status == "pending")
        in_progress_tasks = sum(1 for t in project.tasks if t.status == "in_progress")
        waiting_tasks = sum(1 for t in project.tasks if t.status == "waiting")
        next_actions_count = sum(1 for t in project.tasks if t.is_next_action)

        # Calculate days since activity
        days_since_activity = None
        if project.last_activity_at:
            delta = datetime.now(timezone.utc) - ensure_tz_aware(project.last_activity_at)
            days_since_activity = delta.days

        # Determine health status
        if project.stalled_since:
            health_status = "stalled"
        elif days_since_activity and days_since_activity > 7:
            health_status = "at_risk"
        elif project.momentum_score > 0.7:
            health_status = "strong"
        elif project.momentum_score > 0.4:
            health_status = "moderate"
        else:
            health_status = "weak"

        # Calculate completion percentage
        completion_percentage = (
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        )

        return ProjectHealth(
            id=project.id,
            title=project.title,
            status=project.status,
            momentum_score=project.momentum_score,
            days_since_activity=days_since_activity,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            in_progress_tasks=in_progress_tasks,
            waiting_tasks=waiting_tasks,
            next_actions_count=next_actions_count,
            health_status=health_status,
            completion_percentage=completion_percentage,
        )

    @staticmethod
    def get_stalled_projects(db: Session) -> list[Project]:
        """
        Get all stalled projects

        Args:
            db: Database session

        Returns:
            List of stalled projects
        """
        query = select(Project).where(
            Project.deleted_at.is_(None),
            Project.status == "active",
            Project.stalled_since.is_not(None),
        )

        return list(db.execute(query).scalars().all())

    @staticmethod
    def search(db: Session, search_term: str, limit: int = 20) -> list[Project]:
        """
        Search projects by title or description

        Args:
            db: Database session
            search_term: Search term
            limit: Maximum results

        Returns:
            List of matching projects
        """
        search_pattern = f"%{search_term}%"
        query = (
            select(Project)
            .where(
                Project.deleted_at.is_(None),
                or_(
                    Project.title.ilike(search_pattern),
                    Project.description.ilike(search_pattern),
                ),
            )
            .limit(limit)
        )

        return list(db.execute(query).scalars().all())
