"""
Folder Watcher for Project and Area Discovery

Monitors 10_Projects and 20_Areas directories for folder changes (create, rename, move)
and triggers automatic discovery.
"""

import re
import threading
import time
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    DirCreatedEvent,
    DirModifiedEvent,
    DirMovedEvent,
)
from watchdog.observers import Observer

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class FolderEventHandler(FileSystemEventHandler):
    """
    Handler for folder-level events in monitored directories.

    Detects:
    - New folders created (projects or areas)
    - Folders renamed
    - Folders moved
    """

    def __init__(
        self,
        on_folder_created: Callable[[Path], None],
        on_folder_renamed: Callable[[Path, Path], None],
        on_folder_moved: Callable[[Path, Path], None],
        monitored_parent: str,  # "10_Projects" or "20_Areas"
        debounce_seconds: float = 2.0,
    ):
        """
        Initialize folder event handler.

        Args:
            on_folder_created: Callback for new folders
            on_folder_renamed: Callback for renamed folders (old_path, new_path)
            on_folder_moved: Callback for moved folders (old_path, new_path)
            monitored_parent: Parent directory name ("10_Projects" or "20_Areas")
            debounce_seconds: Time to wait before processing
        """
        self.on_folder_created = on_folder_created
        self.on_folder_renamed = on_folder_renamed
        self.on_folder_moved = on_folder_moved
        self.monitored_parent = monitored_parent
        self.debounce_seconds = debounce_seconds

        self.pattern = re.compile(settings.PROJECT_FOLDER_PATTERN)
        self.timers: dict[str, threading.Timer] = {}
        self.lock = threading.Lock()

    def on_created(self, event: FileSystemEvent):
        """Handle directory creation"""
        if not isinstance(event, DirCreatedEvent):
            return

        folder_path = Path(event.src_path)

        # Check if it's a project folder (matches pattern)
        if not self._is_project_folder(folder_path):
            return

        logger.info(f"New project folder detected: {folder_path.name}")
        self._debounce_event("created", folder_path)

    def on_moved(self, event: FileSystemEvent):
        """Handle directory moves and renames"""
        if not isinstance(event, DirMovedEvent):
            return

        old_path = Path(event.src_path)
        new_path = Path(event.dest_path)

        # Check if source or destination is a project folder
        old_is_project = self._is_project_folder(old_path)
        new_is_project = self._is_project_folder(new_path)

        if not (old_is_project or new_is_project):
            return

        # Determine if it's a rename or move
        if old_path.parent == new_path.parent:
            # Rename (same parent directory)
            logger.info(f"Project folder renamed: {old_path.name} → {new_path.name}")
            self._debounce_event("renamed", new_path, old_path)
        else:
            # Move (different parent)
            logger.info(f"Project folder moved: {old_path} → {new_path}")
            self._debounce_event("moved", new_path, old_path)

    def _is_project_folder(self, folder_path: Path) -> bool:
        """
        Check if folder matches naming pattern for monitored directory.

        Args:
            folder_path: Path to folder

        Returns:
            True if folder matches xx.xx Name pattern and is in monitored parent
        """
        # Must be direct child of monitored directory
        if folder_path.parent.name != self.monitored_parent:
            return False

        # Must match pattern
        return self.pattern.match(folder_path.name) is not None

    def _debounce_event(
        self,
        event_type: str,
        folder_path: Path,
        old_path: Optional[Path] = None
    ):
        """
        Debounce folder events to avoid duplicate processing.

        Args:
            event_type: Type of event ('created', 'renamed', 'moved')
            folder_path: New/current path
            old_path: Old path (for rename/move events)
        """
        folder_str = str(folder_path)

        with self.lock:
            # Cancel existing timer
            if folder_str in self.timers:
                self.timers[folder_str].cancel()

            # Create new timer
            timer = threading.Timer(
                self.debounce_seconds,
                self._process_event,
                args=[event_type, folder_path, old_path],
            )
            self.timers[folder_str] = timer
            timer.start()

    def _process_event(
        self,
        event_type: str,
        folder_path: Path,
        old_path: Optional[Path] = None
    ):
        """
        Process folder event after debounce period.

        Args:
            event_type: Type of event
            folder_path: Current folder path
            old_path: Old folder path (if applicable)
        """
        folder_str = str(folder_path)

        # Remove timer
        with self.lock:
            if folder_str in self.timers:
                del self.timers[folder_str]

        # Call appropriate callback
        try:
            if event_type == "created":
                self.on_folder_created(folder_path)
            elif event_type == "renamed":
                self.on_folder_renamed(old_path, folder_path)
            elif event_type == "moved":
                self.on_folder_moved(old_path, folder_path)
        except Exception as e:
            logger.error(f"Error processing {event_type} event for {folder_path}: {e}")


class FolderWatcher:
    """
    Watches 10_Projects and 20_Areas directories for folder changes.

    Enables automatic discovery when:
    - New folders are created
    - Folders are renamed
    - Folders are moved
    """

    def __init__(
        self,
        root_path: Optional[Path] = None,
        debounce_seconds: float = 2.0,
    ):
        """
        Initialize folder watcher.

        Args:
            root_path: Synced notes root path
            debounce_seconds: Debounce time in seconds
        """
        self.root_path = Path(root_path) if root_path else settings.SECOND_BRAIN_PATH
        self.projects_dir = self.root_path / "10_Projects"
        self.areas_dir = self.root_path / "20_Areas"
        self.debounce_seconds = debounce_seconds

        self.observer: Optional[Observer] = None
        self.is_running = False

        # Callbacks for projects
        self.on_project_created: Optional[Callable[[Path], None]] = None
        self.on_project_renamed: Optional[Callable[[Path, Path], None]] = None
        self.on_project_moved: Optional[Callable[[Path, Path], None]] = None

        # Callbacks for areas
        self.on_area_created: Optional[Callable[[Path], None]] = None
        self.on_area_renamed: Optional[Callable[[Path, Path], None]] = None
        self.on_area_moved: Optional[Callable[[Path, Path], None]] = None

    def start(
        self,
        on_folder_created: Callable[[Path], None],
        on_folder_renamed: Optional[Callable[[Path, Path], None]] = None,
        on_folder_moved: Optional[Callable[[Path, Path], None]] = None,
        on_area_created: Optional[Callable[[Path], None]] = None,
        on_area_renamed: Optional[Callable[[Path, Path], None]] = None,
        on_area_moved: Optional[Callable[[Path, Path], None]] = None,
    ):
        """
        Start watching for folder changes in projects and areas.

        Args:
            on_folder_created: Callback when new project folder created
            on_folder_renamed: Callback when project folder renamed (old_path, new_path)
            on_folder_moved: Callback when project folder moved (old_path, new_path)
            on_area_created: Callback when new area folder created
            on_area_renamed: Callback when area folder renamed (old_path, new_path)
            on_area_moved: Callback when area folder moved (old_path, new_path)
        """
        if self.is_running:
            logger.warning("Folder watcher already running")
            return

        if not self.projects_dir.exists():
            logger.error(f"Projects directory not found: {self.projects_dir}")
            return

        # Store project callbacks
        self.on_project_created = on_folder_created
        self.on_project_renamed = on_folder_renamed or self._default_rename_handler
        self.on_project_moved = on_folder_moved or self._default_move_handler

        # Store area callbacks
        self.on_area_created = on_area_created
        self.on_area_renamed = on_area_renamed
        self.on_area_moved = on_area_moved

        # Create observer
        self.observer = Observer()

        # Create handler for projects
        project_handler = FolderEventHandler(
            on_folder_created=self.on_project_created,
            on_folder_renamed=self.on_project_renamed,
            on_folder_moved=self.on_project_moved,
            monitored_parent="10_Projects",
            debounce_seconds=self.debounce_seconds,
        )

        # Schedule watching for projects
        self.observer.schedule(project_handler, str(self.projects_dir), recursive=False)

        # Create handler for areas if callbacks provided and directory exists
        if self.on_area_created and self.areas_dir.exists():
            area_handler = FolderEventHandler(
                on_folder_created=self.on_area_created,
                on_folder_renamed=self.on_area_renamed or self._default_area_rename_handler,
                on_folder_moved=self.on_area_moved or self._default_area_move_handler,
                monitored_parent="20_Areas",
                debounce_seconds=self.debounce_seconds,
            )

            # Schedule watching for areas
            self.observer.schedule(area_handler, str(self.areas_dir), recursive=False)
            logger.info(f"Monitoring areas: {self.areas_dir}")

        # Start observer
        self.observer.start()
        self.is_running = True

        logger.info("Folder watcher started")
        print(f"Watching for new project folders in: {self.projects_dir}")
        if self.on_area_created and self.areas_dir.exists():
            print(f"Watching for new area folders in: {self.areas_dir}")

    def stop(self):
        """Stop watching folders"""
        if not self.is_running or not self.observer:
            return

        self.observer.stop()
        self.observer.join(timeout=5)
        self.is_running = False

        logger.info("Folder watcher stopped")
        print("Folder watcher stopped")

    def _default_rename_handler(self, old_path: Path, new_path: Path):
        """Default handler for project folder renames - imports new folder"""
        logger.info(f"Using default rename handler: {old_path.name} → {new_path.name}")
        # Just import the renamed folder as if it's new
        if self.on_project_created:
            self.on_project_created(new_path)

    def _default_move_handler(self, old_path: Path, new_path: Path):
        """Default handler for project folder moves - imports new location"""
        logger.info(f"Using default move handler: {old_path} → {new_path}")
        # Import from new location
        if self.on_project_created:
            self.on_project_created(new_path)

    def _default_area_rename_handler(self, old_path: Path, new_path: Path):
        """Default handler for area folder renames - imports new folder"""
        logger.info(f"Using default area rename handler: {old_path.name} → {new_path.name}")
        # Import the renamed folder as if it's new
        if self.on_area_created:
            self.on_area_created(new_path)

    def _default_area_move_handler(self, old_path: Path, new_path: Path):
        """Default handler for area folder moves - imports new location"""
        logger.info(f"Using default area move handler: {old_path} → {new_path}")
        # Import from new location
        if self.on_area_created:
            self.on_area_created(new_path)


# Global folder watcher instance
_folder_watcher: Optional[FolderWatcher] = None


def get_folder_watcher() -> FolderWatcher:
    """
    Get global folder watcher instance.

    Returns:
        FolderWatcher instance
    """
    global _folder_watcher
    if _folder_watcher is None:
        _folder_watcher = FolderWatcher()
    return _folder_watcher


def start_folder_watcher(
    on_folder_created: Callable[[Path], None],
    on_folder_renamed: Optional[Callable[[Path, Path], None]] = None,
    on_folder_moved: Optional[Callable[[Path, Path], None]] = None,
    on_area_created: Optional[Callable[[Path], None]] = None,
    on_area_renamed: Optional[Callable[[Path, Path], None]] = None,
    on_area_moved: Optional[Callable[[Path, Path], None]] = None,
):
    """
    Start the global folder watcher for both projects and areas.

    Args:
        on_folder_created: Callback for new project folders
        on_folder_renamed: Optional callback for renamed project folders
        on_folder_moved: Optional callback for moved project folders
        on_area_created: Optional callback for new area folders
        on_area_renamed: Optional callback for renamed area folders
        on_area_moved: Optional callback for moved area folders
    """
    watcher = get_folder_watcher()
    if not watcher.is_running:
        watcher.start(
            on_folder_created,
            on_folder_renamed,
            on_folder_moved,
            on_area_created,
            on_area_renamed,
            on_area_moved,
        )


def stop_folder_watcher():
    """Stop the global folder watcher"""
    watcher = get_folder_watcher()
    watcher.stop()
