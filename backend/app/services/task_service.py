"""
Task service - business logic for tasks
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.db_utils import ensure_unique_file_marker, log_activity, soft_delete, update_project_activity
from app.models.task import Task
from app.schemas.common import UrgencyZoneEnum
from app.schemas.task import TaskCreate, TaskUpdate

# Default priority threshold for Critical Now auto-designation
# Priority 1-3 are high priority (CRITICAL, VERY_HIGH, HIGH)
CRITICAL_NOW_PRIORITY_THRESHOLD = 3


def calculate_urgency_zone(
    defer_until: Optional[date],
    due_date: Optional[date],
    priority: int,
    current_zone: Optional[str] = None,
) -> str:
    """
    Calculate the appropriate MYN urgency zone based on task attributes.

    MYN Urgency Zone Rules:
    1. OVER_THE_HORIZON: Tasks with defer_until date in the future (not ready to work on)
    2. CRITICAL_NOW: Tasks that are overdue, or due today/tomorrow with high priority (1-3)
    3. OPPORTUNITY_NOW: Default zone for all other actionable tasks

    Args:
        defer_until: Task's defer/start date
        due_date: Task's due date
        priority: Task priority (1-10, lower is higher priority)
        current_zone: Current zone if updating (for future zone_locked support)

    Returns:
        Calculated urgency zone value
    """
    today = date.today()

    # Rule 1: Over the Horizon - tasks deferred to the future
    if defer_until and defer_until > today:
        return UrgencyZoneEnum.OVER_THE_HORIZON.value

    if due_date:
        days_until_due = (due_date - today).days

        # Rule 2a: Critical Now - overdue tasks (any priority)
        if days_until_due < 0:
            return UrgencyZoneEnum.CRITICAL_NOW.value

        # Rule 2b: Critical Now - due today or tomorrow with high priority
        if days_until_due <= 1 and priority <= CRITICAL_NOW_PRIORITY_THRESHOLD:
            return UrgencyZoneEnum.CRITICAL_NOW.value

        # Rule 2c: Critical Now - due today (any priority)
        if days_until_due == 0:
            return UrgencyZoneEnum.CRITICAL_NOW.value

    # Default: Opportunity Now - working inventory
    return UrgencyZoneEnum.OPPORTUNITY_NOW.value


def recalculate_all_urgency_zones(db: Session) -> int:
    """
    Recalculate urgency zones for all active (non-completed, non-cancelled) tasks.

    This should run daily (and on startup) so that tasks whose due dates have
    arrived or passed get promoted to Critical Now automatically.

    Returns:
        Number of tasks whose urgency zone changed.
    """
    # Only recalculate for tasks that are still actionable
    active_statuses = ("pending", "in_progress", "waiting")
    query = select(Task).where(Task.deleted_at.is_(None), Task.status.in_(active_statuses))
    tasks = db.execute(query).scalars().all()

    updated_count = 0
    for task in tasks:
        new_zone = calculate_urgency_zone(
            defer_until=task.defer_until,
            due_date=task.due_date,
            priority=task.priority,
            current_zone=task.urgency_zone,
        )
        if task.urgency_zone != new_zone:
            task.urgency_zone = new_zone
            updated_count += 1

    if updated_count > 0:
        db.commit()

    return updated_count


class TaskService:
    """Service for task operations"""

    @staticmethod
    def get_all(
        db: Session,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        context: Optional[str] = None,
        energy_level: Optional[str] = None,
        is_next_action: Optional[bool] = None,
        priority_min: Optional[int] = None,
        priority_max: Optional[int] = None,
        include_project: bool = False,
        show_completed: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        """
        Get all tasks with optional filtering

        Args:
            db: Database session
            project_id: Filter by project
            status: Filter by status
            context: Filter by context
            energy_level: Filter by energy level (high, medium, low)
            is_next_action: Filter by next action flag
            priority_min: Minimum priority (1-10)
            priority_max: Maximum priority (1-10)
            include_project: Whether to include project details
            show_completed: Whether to include completed tasks
            skip: Offset for pagination
            limit: Limit for pagination

        Returns:
            Tuple of (tasks, total_count)
        """
        query = select(Task).where(Task.deleted_at.is_(None))

        # Include project relationship if requested
        if include_project:
            query = query.options(joinedload(Task.project))

        # Apply filters
        if project_id:
            query = query.where(Task.project_id == project_id)
        if status:
            query = query.where(Task.status == status)
        elif not show_completed:
            # By default, exclude completed and cancelled tasks
            query = query.where(Task.status.notin_(["completed", "cancelled"]))
        if context:
            query = query.where(Task.context == context)
        if energy_level:
            query = query.where(Task.energy_level == energy_level)
        if is_next_action is not None:
            query = query.where(Task.is_next_action == is_next_action)
        if priority_min is not None:
            query = query.where(Task.priority >= priority_min)
        if priority_max is not None:
            query = query.where(Task.priority <= priority_max)

        # Get total count (need subquery without joinedload for count)
        count_subquery = select(Task.id).where(Task.deleted_at.is_(None))
        if project_id:
            count_subquery = count_subquery.where(Task.project_id == project_id)
        if status:
            count_subquery = count_subquery.where(Task.status == status)
        elif not show_completed:
            count_subquery = count_subquery.where(Task.status.notin_(["completed", "cancelled"]))
        if context:
            count_subquery = count_subquery.where(Task.context == context)
        if energy_level:
            count_subquery = count_subquery.where(Task.energy_level == energy_level)
        if is_next_action is not None:
            count_subquery = count_subquery.where(Task.is_next_action == is_next_action)
        if priority_min is not None:
            count_subquery = count_subquery.where(Task.priority >= priority_min)
        if priority_max is not None:
            count_subquery = count_subquery.where(Task.priority <= priority_max)

        count_query = select(func.count()).select_from(count_subquery.subquery())
        total = db.execute(count_query).scalar_one()

        # Apply pagination and order
        query = (
            query.order_by(
                Task.is_next_action.desc(),
                Task.priority.desc(),
                Task.due_date.nullslast(),
            )
            .offset(skip)
            .limit(limit)
        )

        result = db.execute(query)
        if include_project:
            tasks = result.unique().scalars().all()
        else:
            tasks = result.scalars().all()
        return list(tasks), total

    @staticmethod
    def get_by_id(db: Session, task_id: int, include_project: bool = False) -> Optional[Task]:
        """
        Get task by ID

        Args:
            db: Database session
            task_id: Task ID
            include_project: Whether to include project

        Returns:
            Task or None
        """
        query = select(Task).where(Task.id == task_id, Task.deleted_at.is_(None))

        if include_project:
            query = query.options(joinedload(Task.project))

        return db.execute(query).scalar_one_or_none()

    @staticmethod
    def create(db: Session, task_data: TaskCreate) -> Task:
        """
        Create a new task

        Args:
            db: Database session
            task_data: Task creation data

        Returns:
            Created task
        """
        task_dict = task_data.model_dump()

        # Auto-calculate urgency zone based on task attributes
        calculated_zone = calculate_urgency_zone(
            defer_until=task_dict.get("defer_until"),
            due_date=task_dict.get("due_date"),
            priority=task_dict.get("priority", 5),
        )
        task_dict["urgency_zone"] = calculated_zone

        task = Task(**task_dict)

        # Generate file marker for sync
        task.file_marker = ensure_unique_file_marker()

        db.add(task)
        db.flush()

        # Update project activity
        update_project_activity(db, task.project_id)

        # Log activity
        log_activity(
            db,
            entity_type="task",
            entity_id=task.id,
            action_type="created",
            details={"title": task.title, "project_id": task.project_id},
        )

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update(db: Session, task_id: int, task_data: TaskUpdate) -> Optional[Task]:
        """
        Update a task

        Args:
            db: Database session
            task_id: Task ID
            task_data: Update data

        Returns:
            Updated task or None
        """
        task = db.get(Task, task_id)
        if not task:
            return None

        # Track changes
        changes = {}
        update_dict = task_data.model_dump(exclude_unset=True)

        # Apply updates first
        for field, value in update_dict.items():
            if getattr(task, field) != value:
                changes[field] = {"old": getattr(task, field), "new": value}
                setattr(task, field, value)

        # Auto-recalculate urgency zone if relevant fields changed
        # (defer_until, due_date, or priority)
        zone_affecting_fields = {"defer_until", "due_date", "priority"}
        if zone_affecting_fields & set(update_dict.keys()):
            calculated_zone = calculate_urgency_zone(
                defer_until=task.defer_until,
                due_date=task.due_date,
                priority=task.priority,
                current_zone=task.urgency_zone,
            )
            if task.urgency_zone != calculated_zone:
                changes["urgency_zone"] = {"old": task.urgency_zone, "new": calculated_zone}
                task.urgency_zone = calculated_zone

        if changes:
            # Update project activity
            update_project_activity(db, task.project_id)

            # Log activity
            log_activity(
                db,
                entity_type="task",
                entity_id=task_id,
                action_type="updated",
                details=changes,
            )

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete(db: Session, task_id: int) -> bool:
        """
        Delete a task

        Args:
            db: Database session
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        task = db.get(Task, task_id)
        if not task or task.deleted_at is not None:
            return False

        project_id = task.project_id

        # Log activity
        log_activity(
            db,
            entity_type="task",
            entity_id=task_id,
            action_type="deleted",
            details={"title": task.title, "project_id": project_id},
        )

        soft_delete(db, task)

        # Update project activity
        update_project_activity(db, project_id)

        db.commit()
        return True

    @staticmethod
    def complete(db: Session, task_id: int, actual_minutes: Optional[int] = None) -> Optional[Task]:
        """
        Mark a task as complete

        Args:
            db: Database session
            task_id: Task ID
            actual_minutes: Actual time taken

        Returns:
            Updated task or None
        """
        task = db.get(Task, task_id)
        if not task:
            return None

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)

        if actual_minutes is not None:
            task.actual_minutes = actual_minutes

        # Update project activity
        update_project_activity(db, task.project_id)

        # Log activity
        log_activity(
            db,
            entity_type="task",
            entity_id=task_id,
            action_type="completed",
            details={
                "title": task.title,
                "actual_minutes": actual_minutes,
            },
        )

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def start(db: Session, task_id: int) -> Optional[Task]:
        """
        Start a task (begin work)

        Args:
            db: Database session
            task_id: Task ID

        Returns:
            Updated task or None
        """
        task = db.get(Task, task_id)
        if not task:
            return None

        task.status = "in_progress"
        task.started_at = datetime.now(timezone.utc)

        # Update project activity
        update_project_activity(db, task.project_id)

        # Log activity
        log_activity(
            db,
            entity_type="task",
            entity_id=task_id,
            action_type="started",
            details={"title": task.title},
        )

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_by_context(db: Session, context: str, limit: int = 20) -> list[Task]:
        """
        Get tasks by context

        Args:
            db: Database session
            context: Context to filter by
            limit: Maximum results

        Returns:
            List of tasks
        """
        query = (
            select(Task)
            .where(
                Task.deleted_at.is_(None),
                Task.context == context,
                Task.status.in_(["pending", "in_progress"]),
            )
            .order_by(Task.is_next_action.desc(), Task.priority)
            .limit(limit)
        )

        return list(db.execute(query).scalars().all())

    @staticmethod
    def get_overdue(db: Session, limit: int = 50) -> list[Task]:
        """
        Get overdue tasks

        Args:
            db: Database session
            limit: Maximum results

        Returns:
            List of overdue tasks
        """
        from datetime import date

        query = (
            select(Task)
            .where(
                Task.deleted_at.is_(None),
                Task.due_date < date.today(),
                Task.status.in_(["pending", "in_progress"]),
            )
            .order_by(Task.due_date)
            .limit(limit)
        )

        return list(db.execute(query).scalars().all())

    @staticmethod
    def get_two_minute_tasks(db: Session, limit: int = 20) -> list[Task]:
        """
        Get quick tasks (2 minutes or less)

        Args:
            db: Database session
            limit: Maximum results

        Returns:
            List of quick tasks
        """
        query = (
            select(Task)
            .where(
                Task.deleted_at.is_(None),
                Task.is_two_minute_task.is_(True),
                Task.status == "pending",
            )
            .order_by(Task.priority)
            .limit(limit)
        )

        return list(db.execute(query).scalars().all())

    @staticmethod
    def search(db: Session, search_term: str, limit: int = 20) -> list[Task]:
        """
        Search tasks by title or description

        Args:
            db: Database session
            search_term: Search term
            limit: Maximum results

        Returns:
            List of matching tasks
        """
        search_pattern = f"%{search_term}%"
        query = (
            select(Task)
            .where(
                Task.deleted_at.is_(None),
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern),
                ),
            )
            .limit(limit)
        )

        return list(db.execute(query).scalars().all())
