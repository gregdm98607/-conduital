"""
Sync engine for bidirectional synchronization between database and files
"""

import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.db_utils import calculate_file_hash, ensure_unique_file_marker, log_activity
from app.models.project import Project
from app.models.sync_state import SyncState
from app.models.task import Task
from app.sync.markdown_parser import MarkdownParser
from app.sync.markdown_writer import MarkdownWriter


class SyncConflict(Exception):
    """Raised when a sync conflict is detected"""

    def __init__(self, message: str, file_path: str, db_version: dict, file_version: dict):
        super().__init__(message)
        self.file_path = file_path
        self.db_version = db_version
        self.file_version = file_version


class SyncEngine:
    """
    Bidirectional sync engine

    Handles synchronization between database and Second Brain markdown files
    """

    def __init__(self, db: Session, root_path: Optional[Path] = None):
        """
        Initialize sync engine

        Args:
            db: Database session
            root_path: Second Brain root path (default from settings)
        """
        self.db = db
        self.root_path = Path(root_path) if root_path else settings.SECOND_BRAIN_PATH

    def sync_file_to_database(self, file_path: Path) -> Optional[Project]:
        """
        Sync a file to the database (File → DB)

        Args:
            file_path: Path to markdown file

        Returns:
            Updated/created project or None
        """
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return None

        logger.info(f"Syncing file to database: {file_path.name}")

        try:
            # Parse file
            parsed = MarkdownParser.parse_file(file_path)
            metadata = parsed["metadata"]
            tasks = parsed["tasks"]

            # Calculate file hash
            file_hash = calculate_file_hash(str(file_path))

            # Check sync state
            sync_state = self.get_or_create_sync_state(str(file_path))

            # Detect conflicts (both file and DB changed since last sync)
            if self._has_conflict(sync_state, file_hash):
                # Handle conflict based on strategy
                if settings.CONFLICT_STRATEGY == "file_wins":
                    pass  # Proceed with file update
                elif settings.CONFLICT_STRATEGY == "db_wins":
                    return None  # Skip file update
                else:  # prompt
                    raise SyncConflict(
                        f"Conflict detected for {file_path}",
                        str(file_path),
                        {},  # Would include DB data
                        metadata,
                    )

            # Get or create project
            project = None
            if "id" in metadata:
                project = self.db.get(Project, metadata["id"])

            if not project:
                # Create new project
                project = Project()

            # Update project fields
            if "title" in metadata:
                project.title = metadata["title"]
            if "description" in metadata:
                project.description = metadata["description"]
            if "status" in metadata:
                project.status = metadata["status"]
            if "priority" in metadata:
                project.priority = metadata["priority"]
            if "momentum_score" in metadata:
                project.momentum_score = metadata["momentum_score"]
            if "target_completion_date" in metadata:
                project.target_completion_date = metadata["target_completion_date"]

            project.file_path = str(file_path)
            project.file_hash = file_hash
            project.last_activity_at = datetime.now(timezone.utc)

            # Save project
            if not project.id:
                self.db.add(project)
                self.db.flush()
                log_activity(
                    self.db,
                    entity_type="project",
                    entity_id=project.id,
                    action_type="created",
                    source="file_sync",
                )

            # Sync tasks
            self._sync_tasks_from_file(project, tasks)

            # Update sync state
            sync_state.last_synced_at = datetime.now(timezone.utc)
            sync_state.file_hash = file_hash
            sync_state.sync_status = "synced"
            sync_state.entity_type = "project"
            sync_state.entity_id = project.id

            self.db.commit()

            logger.info(f"Synced to database: {project.title}")
            return project

        except SyncConflict:
            raise
        except Exception as e:
            logger.error(f"Error syncing file {file_path}: {e}")
            sync_state = self.get_or_create_sync_state(str(file_path))
            sync_state.sync_status = "error"
            sync_state.error_message = str(e)
            self.db.commit()
            return None

    def sync_database_to_file(self, project: Project) -> bool:
        """
        Sync database to file (DB → File)

        Args:
            project: Project to sync

        Returns:
            True if successful
        """
        logger.info(f"Syncing database to file: {project.title}")

        try:
            # Determine file path
            if project.file_path:
                file_path = Path(project.file_path)
            else:
                file_path = MarkdownWriter.create_project_file_path(project, self.root_path)
                project.file_path = str(file_path)

            # Write file
            MarkdownWriter.write_project_file(project, file_path, preserve_content=True)

            # Calculate new hash
            file_hash = calculate_file_hash(str(file_path))
            project.file_hash = file_hash

            # Update sync state
            sync_state = self.get_or_create_sync_state(str(file_path))
            sync_state.last_synced_at = datetime.now(timezone.utc)
            sync_state.file_hash = file_hash
            sync_state.sync_status = "synced"
            sync_state.entity_type = "project"
            sync_state.entity_id = project.id

            log_activity(
                self.db,
                entity_type="project",
                entity_id=project.id,
                action_type="file_synced",
                source="file_sync",
            )

            self.db.commit()

            logger.info(f"Synced to file: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Error syncing to file for project {project.title}: {e}")
            return False

    def _sync_tasks_from_file(self, project: Project, file_tasks: list[dict]):
        """
        Sync tasks from file to database

        Args:
            project: Project instance
            file_tasks: List of task dicts from file
        """
        # Build marker-to-task map from database
        db_tasks = {task.file_marker: task for task in project.tasks if task.file_marker}

        for task_data in file_tasks:
            marker = task_data.get("marker")

            if marker and marker in db_tasks:
                # Update existing task
                task = db_tasks[marker]
                task.title = task_data["title"]
                task.status = "completed" if task_data["checked"] else "pending"
                task.file_line_number = task_data["line_number"]

                # Update task type if specified
                if task_data["task_type"] == "waiting":
                    task.task_type = "waiting_for"
                    task.status = "waiting"
                elif task_data["task_type"] == "someday":
                    task.task_type = "someday_maybe"

            elif marker:
                # Task has marker but not in DB - shouldn't happen, but create it
                self._create_task_from_file_data(project, task_data)

            else:
                # New task without marker - create with new marker
                task_data["marker"] = ensure_unique_file_marker()
                self._create_task_from_file_data(project, task_data)

    def _create_task_from_file_data(self, project: Project, task_data: dict) -> Task:
        """Create a task from file data"""
        task = Task(
            project_id=project.id,
            title=task_data["title"],
            status="completed" if task_data["checked"] else "pending",
            file_marker=task_data["marker"],
            file_line_number=task_data["line_number"],
        )

        if task_data.get("task_type") == "waiting":
            task.task_type = "waiting_for"
            task.status = "waiting"
        elif task_data.get("task_type") == "someday":
            task.task_type = "someday_maybe"

        self.db.add(task)
        return task

    def get_or_create_sync_state(self, file_path: str) -> SyncState:
        """Get or create sync state record"""
        sync_state = (
            self.db.execute(select(SyncState).where(SyncState.file_path == file_path))
            .scalar_one_or_none()
        )

        if not sync_state:
            sync_state = SyncState(file_path=file_path, sync_status="pending")
            self.db.add(sync_state)
            self.db.flush()

        return sync_state

    def _has_conflict(self, sync_state: SyncState, file_hash: str) -> bool:
        """
        Detect if there's a sync conflict

        A conflict occurs when:
        1. File has changed since last sync (hash different)
        2. Database has changed since last sync (updated_at different)
        3. Both changed

        Args:
            sync_state: Sync state record
            file_hash: Current file hash

        Returns:
            True if conflict detected
        """
        # If no previous sync, no conflict
        if not sync_state.last_synced_at:
            return False

        # Check if file changed
        file_changed = sync_state.file_hash != file_hash

        # Check if database changed
        db_changed = False
        if sync_state.entity_id:
            project = self.db.get(Project, sync_state.entity_id)
            if project and project.updated_at > sync_state.last_synced_at:
                db_changed = True

        # Conflict if both changed
        return file_changed and db_changed

    def scan_and_sync(self) -> dict:
        """
        Scan Second Brain and sync all markdown files

        Returns:
            Statistics dict
        """
        logger.info(f"Scanning Second Brain: {self.root_path}")

        stats = {
            "scanned": 0,
            "synced": 0,
            "errors": 0,
            "skipped": 0,
        }

        for watch_dir in settings.WATCH_DIRECTORIES:
            dir_path = self.root_path / watch_dir

            if not dir_path.exists():
                continue

            # Find all markdown files
            for md_file in dir_path.rglob("*.md"):
                stats["scanned"] += 1

                try:
                    project = self.sync_file_to_database(md_file)
                    if project:
                        stats["synced"] += 1
                    else:
                        stats["skipped"] += 1
                except SyncConflict as e:
                    logger.warning(f"Conflict detected: {e.file_path}")
                    stats["errors"] += 1
                except Exception as e:
                    logger.error(f"Error syncing {md_file}: {e}")
                    stats["errors"] += 1

        logger.info(f"Scan complete: {stats}")
        return stats

    def sync_project_to_file(self, project_id: int) -> bool:
        """
        Sync a specific project to its file

        Args:
            project_id: Project ID

        Returns:
            True if successful
        """
        project = (
            self.db.execute(
                select(Project)
                .where(Project.id == project_id)
                .options(joinedload(Project.tasks))
            )
            .scalar_one_or_none()
        )

        if not project:
            return False

        return self.sync_database_to_file(project)
