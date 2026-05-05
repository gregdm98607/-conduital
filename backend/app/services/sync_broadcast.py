"""
Sync event broadcaster (BACKLOG-153, S33).

Mirrors `discovery_broadcast.py` but for file-sync events. The sync engine
publishes coarse-grained events (`sync_started`, `file_synced`, `sync_error`,
`conflict_detected`, `sync_completed`) so the frontend can render a live
"Synced 2m ago" indicator + recent-activity panel.

Publishers (sync engine, scan endpoints) call `record_sync_event(...)`, which
appends to the in-memory ring buffer and pushes to all WebSocket subscribers.

The broadcaster is process-local. In a future multi-process deploy this would
need to move to Redis pub/sub, but the desktop app is single-process.
"""

from __future__ import annotations

import asyncio
import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


# ---------- In-memory event log ----------
_MAX_EVENTS = 50
_event_log: deque[dict] = deque(maxlen=_MAX_EVENTS)
_event_lock = threading.Lock()

# Latest "completed" timestamp for the sidebar indicator (cheap to read).
_last_synced_at: Optional[str] = None
_last_synced_lock = threading.Lock()


class SyncBroadcaster:
    """In-process pub/sub for sync events.

    Identical contract to `DiscoveryBroadcaster` — see that module's docstring
    for thread-safety notes.
    """

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self, maxsize: int = 100) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers.discard(queue)

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def publish(self, event: dict) -> None:
        loop = self._loop
        if loop is None or not loop.is_running():
            return

        with self._lock:
            subscribers = list(self._subscribers)

        if not subscribers:
            return

        def _deliver() -> None:
            for queue in subscribers:
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    try:
                        queue.get_nowait()
                        queue.put_nowait(event)
                    except (asyncio.QueueEmpty, asyncio.QueueFull):
                        pass

        try:
            loop.call_soon_threadsafe(_deliver)
        except RuntimeError:
            logger.debug("Event loop closed during sync publish; dropping event")


broadcaster = SyncBroadcaster()


def record_sync_event(
    action: str,
    file_path: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
    detail: Optional[str] = None,
    stats: Optional[dict] = None,
) -> dict:
    """Append a sync event to the in-memory log and broadcast it.

    Returns the event dict (useful for tests).

    Actions used by callers:
      - `scan_started` / `scan_completed` (scan-and-sync run boundaries)
      - `file_synced` (single file → DB)
      - `project_synced` (single project → file)
      - `conflict_detected`
      - `sync_error`
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    event: dict = {
        "timestamp": timestamp,
        "action": action,
        "success": success,
    }
    if file_path:
        event["file_path"] = file_path
    if error:
        event["error"] = error
    if detail:
        event["detail"] = detail
    if stats:
        event["stats"] = stats

    with _event_lock:
        _event_log.append(event)

    # Track last successful completion for the sidebar indicator.
    if success and action in ("scan_completed", "file_synced", "project_synced"):
        global _last_synced_at
        with _last_synced_lock:
            _last_synced_at = timestamp

    broadcaster.publish(event)
    return event


def get_recent_sync_events(limit: int = 20) -> list[dict]:
    """Return the most recent sync events (newest first)."""
    with _event_lock:
        events = list(_event_log)
    return list(reversed(events[-limit:]))


def get_last_synced_at() -> Optional[str]:
    """Return ISO timestamp of the last successful sync completion, or None."""
    with _last_synced_lock:
        return _last_synced_at


def reset_for_tests() -> None:
    """Test helper: wipe state so tests start from a clean log."""
    global _last_synced_at
    with _event_lock:
        _event_log.clear()
    with _last_synced_lock:
        _last_synced_at = None
