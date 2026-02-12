"""
Export service - data export and backup functionality

BACKLOG-074: Data portability promise for R1 release.
"""

import logging
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models import Area, Context, Goal, InboxItem, Project, Task, Vision
from app.schemas.export import EntityCounts, ExportData, ExportMetadata, ExportPreview

logger = logging.getLogger(__name__)


class ExportService:
    """Service for data export and backup operations"""

    EXPORT_VERSION = "1.0.0"
    AVAILABLE_FORMATS = ["json", "sqlite"]

    @classmethod
    def get_entity_counts(cls, db: Session) -> EntityCounts:
        """
        Get counts of all exportable entities.

        Args:
            db: Database session

        Returns:
            EntityCounts with counts for each entity type
        """
        return EntityCounts(
            projects=db.execute(select(func.count(Project.id))).scalar_one(),
            tasks=db.execute(select(func.count(Task.id))).scalar_one(),
            areas=db.execute(select(func.count(Area.id))).scalar_one(),
            goals=db.execute(select(func.count(Goal.id))).scalar_one(),
            visions=db.execute(select(func.count(Vision.id))).scalar_one(),
            contexts=db.execute(select(func.count(Context.id))).scalar_one(),
            inbox_items=db.execute(select(func.count(InboxItem.id))).scalar_one(),
        )

    @classmethod
    def get_export_preview(cls, db: Session) -> ExportPreview:
        """
        Get a preview of what would be exported (for UI display).

        Args:
            db: Database session

        Returns:
            ExportPreview with counts and size estimate
        """
        counts = cls.get_entity_counts(db)

        # Rough size estimate: ~500 bytes per entity on average
        total_entities = (
            counts.projects
            + counts.tasks
            + counts.areas
            + counts.goals
            + counts.visions
            + counts.contexts
            + counts.inbox_items
        )
        estimated_bytes = total_entities * 500 + 1000  # Add 1KB for metadata

        return ExportPreview(
            entity_counts=counts,
            estimated_size_bytes=estimated_bytes,
            estimated_size_display=cls._format_bytes(estimated_bytes),
            available_formats=cls.AVAILABLE_FORMATS,
        )

    @classmethod
    def export_full_json(cls, db: Session) -> ExportData:
        """
        Export all user data as structured JSON.

        Exports:
        - Areas (with project counts)
        - Goals
        - Visions
        - Contexts
        - Projects (with nested tasks)
        - Inbox items

        Args:
            db: Database session

        Returns:
            ExportData containing all exportable data
        """
        logger.info("Starting full JSON export")

        # Get entity counts first
        counts = cls.get_entity_counts(db)

        # Build metadata
        metadata = ExportMetadata(
            export_version=cls.EXPORT_VERSION,
            app_version=settings.VERSION,
            exported_at=datetime.now(timezone.utc),
            commercial_mode=settings.COMMERCIAL_MODE,
            entity_counts=counts,
            database_path=settings.DATABASE_PATH,
        )

        # Export each entity type
        areas = cls._export_areas(db)
        goals = cls._export_goals(db)
        visions = cls._export_visions(db)
        contexts = cls._export_contexts(db)
        projects = cls._export_projects_with_tasks(db)
        inbox_items = cls._export_inbox_items(db)

        logger.info(
            f"Export complete: {counts.projects} projects, {counts.tasks} tasks, "
            f"{counts.areas} areas, {counts.goals} goals, {counts.visions} visions, "
            f"{counts.contexts} contexts, {counts.inbox_items} inbox items"
        )

        return ExportData(
            metadata=metadata,
            areas=areas,
            goals=goals,
            visions=visions,
            contexts=contexts,
            projects=projects,
            inbox_items=inbox_items,
        )

    @classmethod
    def create_database_backup(cls) -> Path:
        """
        Create a backup copy of the SQLite database file.

        Returns:
            Path to the temporary backup file

        Raises:
            FileNotFoundError: If database file doesn't exist
            IOError: If backup fails
        """
        db_path = Path(settings.DATABASE_PATH)

        if not db_path.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        # Create temp file with .db extension
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".db",
            prefix="conduital_backup_",
        )
        temp_path = Path(temp_file.name)
        temp_file.close()

        # Copy database file
        logger.info(f"Creating database backup: {db_path} -> {temp_path}")
        shutil.copy2(db_path, temp_path)

        # Also copy WAL and SHM files if they exist (for consistency)
        wal_path = db_path.with_suffix(".db-wal")
        shm_path = db_path.with_suffix(".db-shm")

        if wal_path.exists():
            shutil.copy2(wal_path, temp_path.with_suffix(".db-wal"))
        if shm_path.exists():
            shutil.copy2(shm_path, temp_path.with_suffix(".db-shm"))

        logger.info(f"Database backup created: {temp_path}")
        return temp_path

    @classmethod
    def _export_areas(cls, db: Session) -> list[dict[str, Any]]:
        """Export all areas"""
        query = select(Area).order_by(Area.title)
        areas = db.execute(query).scalars().all()

        return [
            {
                "id": area.id,
                "title": area.title,
                "description": area.description,
                "folder_path": area.folder_path,
                "standard_of_excellence": area.standard_of_excellence,
                "review_frequency": area.review_frequency,
                "last_reviewed_at": cls._serialize_datetime(area.last_reviewed_at),
                "created_at": cls._serialize_datetime(area.created_at),
                "updated_at": cls._serialize_datetime(area.updated_at),
            }
            for area in areas
        ]

    @classmethod
    def _export_goals(cls, db: Session) -> list[dict[str, Any]]:
        """Export all goals"""
        query = select(Goal).order_by(Goal.title)
        goals = db.execute(query).scalars().all()

        return [
            {
                "id": goal.id,
                "title": goal.title,
                "description": goal.description,
                "timeframe": goal.timeframe,
                "target_date": cls._serialize_date(goal.target_date),
                "status": goal.status,
                "completed_at": cls._serialize_datetime(goal.completed_at),
                "created_at": cls._serialize_datetime(goal.created_at),
                "updated_at": cls._serialize_datetime(goal.updated_at),
            }
            for goal in goals
        ]

    @classmethod
    def _export_visions(cls, db: Session) -> list[dict[str, Any]]:
        """Export all visions"""
        query = select(Vision).order_by(Vision.title)
        visions = db.execute(query).scalars().all()

        return [
            {
                "id": vision.id,
                "title": vision.title,
                "description": vision.description,
                "timeframe": vision.timeframe,
                "created_at": cls._serialize_datetime(vision.created_at),
                "updated_at": cls._serialize_datetime(vision.updated_at),
            }
            for vision in visions
        ]

    @classmethod
    def _export_contexts(cls, db: Session) -> list[dict[str, Any]]:
        """Export all contexts"""
        query = select(Context).order_by(Context.name)
        contexts = db.execute(query).scalars().all()

        return [
            {
                "id": context.id,
                "name": context.name,
                "context_type": context.context_type,
                "description": context.description,
                "icon": context.icon,
                "created_at": cls._serialize_datetime(context.created_at),
                "updated_at": cls._serialize_datetime(context.updated_at),
            }
            for context in contexts
        ]

    @classmethod
    def _export_projects_with_tasks(cls, db: Session) -> list[dict[str, Any]]:
        """Export all projects with their tasks nested"""
        query = (
            select(Project)
            .options(joinedload(Project.tasks))
            .order_by(Project.title)
        )
        projects = db.execute(query).unique().scalars().all()

        return [cls._serialize_project(project) for project in projects]

    @classmethod
    def _serialize_project(cls, project: Project) -> dict[str, Any]:
        """Serialize a project with its tasks"""
        return {
            "id": project.id,
            "title": project.title,
            "description": project.description,
            "outcome_statement": project.outcome_statement,
            "status": project.status,
            "priority": project.priority,
            "momentum_score": project.momentum_score,
            "area_id": project.area_id,
            "goal_id": project.goal_id,
            "vision_id": project.vision_id,
            "target_completion_date": cls._serialize_date(project.target_completion_date),
            "review_frequency": project.review_frequency,
            "next_review_date": cls._serialize_date(project.next_review_date),
            "last_reviewed_at": cls._serialize_datetime(project.last_reviewed_at),
            "last_activity_at": cls._serialize_datetime(project.last_activity_at),
            "completed_at": cls._serialize_datetime(project.completed_at),
            "stalled_since": cls._serialize_datetime(project.stalled_since),
            "file_path": project.file_path,
            "file_hash": project.file_hash,
            "created_at": cls._serialize_datetime(project.created_at),
            "updated_at": cls._serialize_datetime(project.updated_at),
            "tasks": [cls._serialize_task(task) for task in project.tasks],
        }

    @classmethod
    def _serialize_task(cls, task: Task) -> dict[str, Any]:
        """Serialize a task"""
        return {
            "id": task.id,
            "project_id": task.project_id,
            "parent_task_id": task.parent_task_id,
            "phase_id": task.phase_id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "task_type": task.task_type,
            "priority": task.priority,
            "context": task.context,
            "energy_level": task.energy_level,
            "location": task.location,
            "estimated_minutes": task.estimated_minutes,
            "actual_minutes": task.actual_minutes,
            "due_date": cls._serialize_date(task.due_date),
            "defer_until": cls._serialize_date(task.defer_until),
            "is_next_action": task.is_next_action,
            "is_two_minute_task": task.is_two_minute_task,
            "is_unstuck_task": task.is_unstuck_task,
            "urgency_zone": task.urgency_zone,
            "waiting_for": task.waiting_for,
            "resource_requirements": task.resource_requirements,
            "sequence_order": task.sequence_order,
            "file_line_number": task.file_line_number,
            "file_marker": task.file_marker,
            "started_at": cls._serialize_datetime(task.started_at),
            "completed_at": cls._serialize_datetime(task.completed_at),
            "created_at": cls._serialize_datetime(task.created_at),
            "updated_at": cls._serialize_datetime(task.updated_at),
        }

    @classmethod
    def _export_inbox_items(cls, db: Session) -> list[dict[str, Any]]:
        """Export all inbox items"""
        query = select(InboxItem).order_by(InboxItem.captured_at.desc())
        items = db.execute(query).scalars().all()

        return [
            {
                "id": item.id,
                "content": item.content,
                "source": item.source,
                "captured_at": cls._serialize_datetime(item.captured_at),
                "processed_at": cls._serialize_datetime(item.processed_at),
                "result_type": item.result_type,
                "result_id": item.result_id,
            }
            for item in items
        ]

    @staticmethod
    def _serialize_datetime(dt: datetime | None) -> str | None:
        """Serialize datetime to ISO format string"""
        if dt is None:
            return None
        return dt.isoformat()

    @staticmethod
    def _serialize_date(d) -> str | None:
        """Serialize date to ISO format string"""
        if d is None:
            return None
        return d.isoformat()

    @staticmethod
    def _format_bytes(size_bytes: int) -> str:
        """Format bytes as human-readable string"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
