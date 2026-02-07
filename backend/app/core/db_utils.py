"""
Database utility functions
"""

from datetime import datetime, timezone
from typing import Any, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog

T = TypeVar("T")


def log_activity(
    db: Session,
    entity_type: str,
    entity_id: int,
    action_type: str,
    details: Optional[dict[str, Any]] = None,
    source: str = "user",
) -> ActivityLog:
    """
    Log an activity for audit trail and momentum calculation

    Args:
        db: Database session
        entity_type: Type of entity (project, task, area)
        entity_id: ID of the entity
        action_type: Type of action (created, updated, completed, etc.)
        details: Optional dictionary of change details (will be JSON serialized)
        source: Source of the change (user, file_sync, ai_assistant, system)

    Returns:
        Created ActivityLog instance
    """
    import json
    from datetime import date

    def json_serializer(obj):
        """Custom JSON serializer for objects not serializable by default."""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    activity = ActivityLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action_type=action_type,
        details=json.dumps(details, default=json_serializer) if details else None,
        source=source,
    )
    db.add(activity)
    db.flush()
    return activity


def update_project_activity(db: Session, project_id: int, source: str = "user") -> None:
    """
    Update project's last_activity_at timestamp

    Args:
        db: Database session
        project_id: Project ID
        source: Source of the activity
    """
    from app.models.project import Project

    project = db.get(Project, project_id)
    if project:
        project.last_activity_at = datetime.now(timezone.utc)
        # Clear stalled status if activity occurs
        if project.stalled_since:
            project.stalled_since = None
        db.flush()


def get_or_create(
    db: Session, model: Type[T], defaults: Optional[dict[str, Any]] = None, **kwargs: Any
) -> tuple[T, bool]:
    """
    Get an existing instance or create a new one

    Args:
        db: Database session
        model: Model class
        defaults: Default values for creation
        **kwargs: Filter criteria

    Returns:
        Tuple of (instance, created)
    """
    instance = db.execute(select(model).filter_by(**kwargs)).scalar_one_or_none()

    if instance:
        return instance, False

    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance, True


def soft_delete(db: Session, instance: Any) -> None:
    """
    Soft delete an instance by marking as archived/deleted

    Note: Currently we use hard deletes. This is a placeholder for future soft delete support.
    """
    # TODO: Implement soft delete when we add deleted_at/archived_at columns
    raise NotImplementedError("Soft delete not yet implemented")


def bulk_create(db: Session, instances: list[Any]) -> None:
    """
    Bulk create instances efficiently

    Args:
        db: Database session
        instances: List of model instances
    """
    db.add_all(instances)
    db.flush()


def count_by_status(db: Session, model: Type[T], status_field: str = "status") -> dict[str, int]:
    """
    Count instances by status

    Args:
        db: Database session
        model: Model class
        status_field: Name of the status field

    Returns:
        Dictionary mapping status to count
    """
    from sqlalchemy import func

    status_column = getattr(model, status_field)
    results = db.execute(
        select(status_column, func.count()).group_by(status_column)
    ).all()

    return {status: count for status, count in results}


def get_recent_activity(
    db: Session, entity_type: str, entity_id: int, limit: int = 50
) -> list[ActivityLog]:
    """
    Get recent activity for an entity

    Args:
        db: Database session
        entity_type: Type of entity
        entity_id: Entity ID
        limit: Maximum number of records

    Returns:
        List of ActivityLog instances
    """
    return (
        db.execute(
            select(ActivityLog)
            .filter_by(entity_type=entity_type, entity_id=entity_id)
            .order_by(ActivityLog.timestamp.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def ensure_unique_file_marker() -> str:
    """
    Generate a unique file marker for task sync

    Returns:
        Unique marker string (UUID-based)
    """
    import uuid

    return f"task:{uuid.uuid4().hex[:12]}"


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file

    Args:
        file_path: Path to file

    Returns:
        Hex digest of file hash
    """
    import hashlib
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        return ""

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()
