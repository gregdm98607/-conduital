"""
File system watcher for monitoring markdown file changes
"""

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from app.core.config import settings

logger = logging.getLogger(__name__)


class DebounceHandler(FileSystemEventHandler):
    """
    File system event handler with debouncing

    Prevents multiple events for the same file within a short time window
    """

    def __init__(self, callback: Callable[[Path], None], debounce_seconds: float = 1.0):
        """
        Initialize debounce handler

        Args:
            callback: Function to call with file path when change detected
            debounce_seconds: Time to wait before processing (default 1.0)
        """
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.timers: dict[str, threading.Timer] = {}
        self.lock = threading.Lock()

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only watch markdown files
        if file_path.suffix.lower() not in [".md", ".markdown"]:
            return

        self._debounce_event(file_path)

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.suffix.lower() not in [".md", ".markdown"]:
            return

        self._debounce_event(file_path)

    def _debounce_event(self, file_path: Path):
        """
        Debounce file events

        Args:
            file_path: Path to file that changed
        """
        file_str = str(file_path)

        with self.lock:
            # Cancel existing timer for this file
            if file_str in self.timers:
                self.timers[file_str].cancel()

            # Create new timer
            timer = threading.Timer(
                self.debounce_seconds,
                self._process_file,
                args=[file_path],
            )
            self.timers[file_str] = timer
            timer.start()

    def _process_file(self, file_path: Path):
        """
        Process file after debounce period

        Args:
            file_path: Path to file
        """
        file_str = str(file_path)

        # Remove timer
        with self.lock:
            if file_str in self.timers:
                del self.timers[file_str]

        # Call callback
        try:
            self.callback(file_path)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")


class FileWatcher:
    """
    Watch synced notes directories for changes

    Monitors specified directories and triggers sync when files change
    """

    def __init__(
        self,
        root_path: Optional[Path] = None,
        watch_dirs: Optional[list[str]] = None,
        debounce_seconds: float = 1.0,
    ):
        """
        Initialize file watcher

        Args:
            root_path: Synced notes root path (default from settings)
            watch_dirs: List of subdirectories to watch (default from settings)
            debounce_seconds: Debounce time in seconds
        """
        self.root_path = Path(root_path) if root_path else settings.SECOND_BRAIN_PATH
        self.watch_dirs = watch_dirs or settings.WATCH_DIRECTORIES
        self.debounce_seconds = debounce_seconds

        self.observer: Optional[Observer] = None
        self.callback: Optional[Callable[[Path], None]] = None
        self.is_running = False

    def start(self, callback: Callable[[Path], None]):
        """
        Start watching files

        Args:
            callback: Function to call when file changes (receives Path)
        """
        if self.is_running:
            logger.info("File watcher already running")
            return

        self.callback = callback

        # Create observer
        self.observer = Observer()

        # Create handler
        handler = DebounceHandler(callback, self.debounce_seconds)

        # Schedule watching for each directory
        for watch_dir in self.watch_dirs:
            dir_path = self.root_path / watch_dir

            if not dir_path.exists():
                logger.warning(f"Watch directory does not exist: {dir_path}")
                continue

            self.observer.schedule(handler, str(dir_path), recursive=True)
            logger.info(f"Watching directory: {dir_path}")

        # Start observer
        self.observer.start()
        self.is_running = True
        logger.info("File watcher started")

    def stop(self):
        """Stop watching files"""
        if not self.is_running or not self.observer:
            return

        self.observer.stop()
        self.observer.join(timeout=5)
        self.is_running = False
        logger.info("File watcher stopped")

    def is_watched_file(self, file_path: Path) -> bool:
        """
        Check if a file is in a watched directory

        Args:
            file_path: Path to check

        Returns:
            True if file should be watched
        """
        try:
            # Convert to absolute path
            if not file_path.is_absolute():
                file_path = file_path.resolve()

            # Check if it's under root path
            if self.root_path not in file_path.parents and file_path.parent != self.root_path:
                return False

            # Check if it's in a watched directory
            relative_path = file_path.relative_to(self.root_path)
            first_part = relative_path.parts[0] if relative_path.parts else ""

            return first_part in self.watch_dirs

        except (ValueError, OSError):
            return False


# Global watcher instance
_watcher: Optional[FileWatcher] = None


def get_watcher() -> FileWatcher:
    """
    Get global file watcher instance

    Returns:
        FileWatcher instance
    """
    global _watcher
    if _watcher is None:
        _watcher = FileWatcher()
    return _watcher


def start_file_watcher(callback: Callable[[Path], None]):
    """
    Start the global file watcher

    Args:
        callback: Function to call when files change
    """
    watcher = get_watcher()
    if not watcher.is_running:
        watcher.start(callback)


def stop_file_watcher():
    """Stop the global file watcher"""
    watcher = get_watcher()
    watcher.stop()
