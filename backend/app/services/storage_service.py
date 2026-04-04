"""
StorageService — Phase 3: Invert SQLite's role from source of truth to query cache.

This service wraps the StorageProvider abstraction and provides write-through
semantics: when STORAGE_MODE is "storage_first", writes go to the
StorageProvider (markdown files) FIRST, then SQLite is updated as a cache.

When STORAGE_MODE is "legacy" (the default), the old SQLite-first behavior
is preserved for full backward compatibility.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.core.config import settings
from app.models.project import Project
from app.models.task import Task

logger = logging.getLogger(__name__)


def _is_storage_first() -> bool:
    """Check if the system is configured for storage-first mode."""
    mode = getattr(settings, "STORAGE_MODE", "legacy")
    return mode == "storage_first"


class StorageService:
    """
    Write-through service that keeps StorageProvider and SQLite in sync.

    In *storage_first* mode every project/task mutation is written to
    the StorageProvider (markdown) first, then the SQLite cache is updated.

    In *legacy* mode (default) the service is a no-op passthrough — the
    caller's existing SQLAlchemy workflow is unchanged.
    """

    def __init__(self, db: Session):
        self.db = db
        self.storage_first = _is_storage_first()
        self._provider = None

    @property
    def provider(self):
        """Lazy-load the StorageProvider singleton."""
        if self._provider is None:
            from app.storage.factory import get_storage_provider
            self._provider = get_storage_provider()
        return self._provider

    # ------------------------------------------------------------------
    # Project write-through
    # ------------------------------------------------------------------

    def persist_project(self, project: Project) -> None:
        """
        Write a project to the StorageProvider (if storage_first).

        Call this BEFORE db.commit() in service-layer write paths.
        In legacy mode this is a no-op.
        """
        if not self.storage_first:
            return

        try:
            data = self._project_to_dict(project)
            entity_id = self._entity_id_for_project(project)
            written_id = self.provider.write_entity("project", entity_id, data)

            # Store the entity_id back on the project so we can find it later
            if not project.file_path:
                abs_path = self.provider._resolve_path(written_id)
                project.file_path = str(abs_path)
            logger.debug("Wrote project '%s' to storage: %s", project.title, written_id)
        except Exception:
            logger.exception("Failed to write project '%s' to storage", project.title)
            raise

    def delete_project_from_storage(self, project: Project) -> None:
        """Remove a project from the StorageProvider."""
        if not self.storage_first:
            return

        entity_id = self._entity_id_for_project(project)
        if entity_id:
            try:
                self.provider.delete_entity("project", entity_id)
                logger.debug("Deleted project '%s' from storage", project.title)
            except Exception:
                logger.exception("Failed to delete project '%s' from storage", project.title)

    # ------------------------------------------------------------------
    # Task write-through (tasks live inside project markdown files)
    # ------------------------------------------------------------------

    def persist_task(self, task: Task) -> None:
        """
        After a task is created/updated, re-write the parent project to storage.

        Tasks are embedded as checkbox lines inside the parent project's
        markdown file, so any task mutation means re-writing the project.
        """
        if not self.storage_first:
            return

        project = task.project or self.db.get(Project, task.project_id)
        if project:
            self.persist_project(project)

    # ------------------------------------------------------------------
    # Cache rebuild (startup)
    # ------------------------------------------------------------------

    @classmethod
    def rebuild_cache(cls, db: Session) -> dict:
        """
        Scan all markdown files via the StorageProvider and upsert into SQLite.

        This is the authoritative cache rebuild — markdown files win over
        any stale SQLite data. Called on startup when storage_first mode
        is active.

        Returns:
            Stats dict with counts of created / updated / errors.
        """
        from app.storage.factory import get_storage_provider
        from app.core.db_utils import ensure_unique_file_marker

        provider = get_storage_provider()
        stats = {"created": 0, "updated": 0, "errors": 0, "scanned": 0}

        try:
            entities = provider.list_entities("project")
        except Exception:
            logger.exception("Failed to list entities from storage provider")
            return stats

        for entity_summary in entities:
            stats["scanned"] += 1
            entity_id = entity_summary["entity_id"]
            try:
                full_data = provider.read_entity("project", entity_id)
                cls._upsert_project_from_storage(db, entity_id, full_data, provider=provider)
                stats["updated" if cls._was_update else "created"] += 1
            except Exception:
                logger.exception("Error rebuilding cache for %s", entity_id)
                stats["errors"] += 1

        db.commit()
        logger.info(
            "Cache rebuild complete: scanned=%d created=%d updated=%d errors=%d",
            stats["scanned"], stats["created"], stats["updated"], stats["errors"],
        )
        return stats

    # Class-level flag used by rebuild_cache to track create vs update
    _was_update: bool = False

    @classmethod
    def _upsert_project_from_storage(
        cls, db: Session, entity_id: str, data: dict, *, provider=None
    ) -> Project:
        """
        Create or update a SQLite project row from StorageProvider data.

        Markdown is the source of truth — if the file exists, its data wins.
        """
        from app.core.db_utils import ensure_unique_file_marker

        if provider is None:
            from app.storage.factory import get_storage_provider
            provider = get_storage_provider()
        abs_path = str(provider._resolve_path(entity_id))
        metadata = data.get("metadata", {})
        tasks_data = data.get("tasks", [])

        # Try to find existing project by file_path
        project = db.execute(
            select(Project).where(Project.file_path == abs_path)
        ).scalar_one_or_none()

        cls._was_update = project is not None

        if project is None:
            project = Project()
            project.file_path = abs_path

        # Map metadata fields to project columns
        if "title" in metadata:
            project.title = metadata["title"]
        elif not project.title:
            # Derive from entity_id (filename)
            import os
            project.title = os.path.splitext(os.path.basename(entity_id))[0].replace("_", " ")

        if "project_status" in metadata:
            project.status = metadata["project_status"]
        elif "status" in metadata:
            project.status = metadata["status"]
        elif not project.status:
            project.status = "active"

        if "priority" in metadata:
            project.priority = int(metadata["priority"])
        if "momentum_score" in metadata:
            project.momentum_score = float(metadata["momentum_score"])
        if "description" in metadata:
            project.description = metadata["description"]

        project.file_hash = data.get("file_hash")
        if not project.last_activity_at:
            project.last_activity_at = datetime.now(timezone.utc)

        if project.id is None:
            db.add(project)
            db.flush()  # Get auto-generated ID

        # Upsert tasks
        cls._upsert_tasks_from_storage(db, project, tasks_data)

        return project

    @classmethod
    def _upsert_tasks_from_storage(
        cls, db: Session, project: Project, tasks_data: list[dict]
    ) -> None:
        """Sync task checkbox data from markdown into SQLite."""
        from app.core.db_utils import ensure_unique_file_marker

        # Build marker → existing task map
        existing_tasks = {
            t.file_marker: t
            for t in db.execute(
                select(Task).where(
                    Task.project_id == project.id,
                    Task.file_marker.isnot(None),
                    Task.deleted_at.is_(None),
                )
            ).scalars().all()
        }

        seen_markers = set()
        for td in tasks_data:
            marker = td.get("marker")
            if not marker:
                marker = ensure_unique_file_marker()

            seen_markers.add(marker)

            if marker in existing_tasks:
                task = existing_tasks[marker]
                task.title = td["title"]
                new_status = "completed" if td.get("checked") else "pending"
                task.status = new_status
                task.file_line_number = td.get("line_number")
            else:
                task = Task(
                    project_id=project.id,
                    title=td["title"],
                    status="completed" if td.get("checked") else "pending",
                    file_marker=marker,
                    file_line_number=td.get("line_number"),
                )
                if td.get("task_type") == "waiting":
                    task.task_type = "waiting_for"
                    task.status = "waiting"
                elif td.get("task_type") == "someday":
                    task.task_type = "someday_maybe"
                db.add(task)

    # ------------------------------------------------------------------
    # Change detection (external edits — e.g. user edited in Obsidian)
    # ------------------------------------------------------------------

    def sync_external_changes(self) -> dict:
        """
        Poll the StorageProvider for external file changes and update SQLite.

        Returns:
            Stats dict with counts of changes processed.
        """
        if not self.storage_first:
            return {"changes": 0}

        changes = self.provider.watch_for_changes()
        stats = {"changes": len(changes), "created": 0, "updated": 0, "deleted": 0, "errors": 0}

        for change in changes:
            try:
                from app.storage.base import ChangeType

                if change.change_type == ChangeType.DELETED:
                    self._handle_deleted_entity(change.entity_id)
                    stats["deleted"] += 1
                elif change.change_type == ChangeType.CREATED:
                    full_data = self.provider.read_entity(
                        change.entity_type, change.entity_id
                    )
                    self._upsert_project_from_storage(
                        self.db, change.entity_id, full_data,
                        provider=self.provider,
                    )
                    stats["created"] += 1
                elif change.change_type == ChangeType.MODIFIED:
                    full_data = self.provider.read_entity(
                        change.entity_type, change.entity_id
                    )
                    self._upsert_project_from_storage(
                        self.db, change.entity_id, full_data,
                        provider=self.provider,
                    )
                    stats["updated"] += 1
            except Exception:
                logger.exception(
                    "Error processing external change for %s", change.entity_id
                )
                stats["errors"] += 1

        if stats["changes"] > 0:
            self.db.commit()
            logger.info("Processed %d external changes", stats["changes"])

        return stats

    def _handle_deleted_entity(self, entity_id: str) -> None:
        """Soft-delete the SQLite project whose file was removed."""
        from app.core.db_utils import soft_delete

        abs_path = str(self.provider._resolve_path(entity_id))
        project = self.db.execute(
            select(Project).where(Project.file_path == abs_path)
        ).scalar_one_or_none()

        if project and project.deleted_at is None:
            soft_delete(self.db, project)
            # Also soft-delete child tasks
            for task in project.tasks:
                if task.deleted_at is None:
                    soft_delete(self.db, task)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _project_to_dict(self, project: Project) -> dict:
        """Convert a Project ORM instance to a dict for StorageProvider."""
        # Load tasks if not already loaded
        tasks = project.tasks if project.tasks else []

        task_dicts = []
        for t in tasks:
            if t.deleted_at is not None:
                continue
            task_dicts.append({
                "title": t.title,
                "checked": t.status == "completed",
                "marker": t.file_marker,
                "file_marker": t.file_marker,
                "task_type": t.task_type,
                "type": t.task_type,
            })

        return {
            "title": project.title,
            "description": project.description,
            "status": project.status,
            "priority": project.priority,
            "momentum_score": project.momentum_score or 0.0,
            "metadata": {
                "tracker_id": project.id,
                "project_status": project.status,
                "priority": project.priority,
                "momentum_score": project.momentum_score or 0.0,
                "title": project.title,
                "description": project.description,
            },
            "tasks": task_dicts,
        }

    def _entity_id_for_project(self, project: Project) -> str:
        """
        Derive the StorageProvider entity_id for a project.

        If the project already has a file_path, convert it to a relative
        entity_id. Otherwise return empty string to let the provider
        auto-generate one from the title.
        """
        if not project.file_path:
            return ""

        try:
            from pathlib import Path
            abs_path = Path(project.file_path)
            return self.provider._relative_id(abs_path)
        except (ValueError, AttributeError):
            # file_path isn't under the provider root — use empty to auto-generate
            return ""


# ---------------------------------------------------------------------------
# Module-level convenience for startup
# ---------------------------------------------------------------------------

def rebuild_sqlite_cache_on_startup(db: Session) -> dict:
    """
    Called during application startup when STORAGE_MODE == "storage_first".

    Scans the configured storage folder and populates SQLite as a cache.
    """
    if not _is_storage_first():
        logger.info("Storage mode is 'legacy' — skipping cache rebuild")
        return {}

    logger.info("Storage-first mode active — rebuilding SQLite cache from storage")
    return StorageService.rebuild_cache(db)
