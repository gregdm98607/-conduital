"""
Discovery event broadcaster (DEBT-016).

Thread-safe asyncio-based pub/sub so WebSocket clients can receive
auto-discovery events in real time without polling /discovery/status.

Usage
-----
Backend (on startup):
    from app.services.discovery_broadcast import broadcaster
    broadcaster.attach_loop(asyncio.get_running_loop())

Event emitters (may run in any thread):
    broadcaster.publish({"action": "project_created", ...})

WebSocket handler:
    queue = broadcaster.subscribe()
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    finally:
        broadcaster.unsubscribe(queue)
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class DiscoveryBroadcaster:
    """In-process pub/sub for discovery events.

    `subscribe` / `unsubscribe` are async-only (called from WS handlers on the
    event loop). `publish` is thread-safe and is called from both async and
    threaded contexts (folder watcher callbacks run on worker threads).
    """

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind the broadcaster to the running event loop (called at startup)."""
        self._loop = loop

    def subscribe(self, maxsize: int = 100) -> asyncio.Queue:
        """Register a new subscriber and return its queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Remove a subscriber queue."""
        with self._lock:
            self._subscribers.discard(queue)

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def publish(self, event: dict) -> None:
        """Publish an event to all subscribers. Thread-safe.

        Dropped silently if no event loop is attached (e.g., startup race or
        tests without an async runtime). A full queue drops the oldest event
        for that subscriber rather than blocking the publisher.
        """
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
                    # Drop oldest, put newest — slow subscribers lose history, not liveness.
                    try:
                        queue.get_nowait()
                        queue.put_nowait(event)
                    except (asyncio.QueueEmpty, asyncio.QueueFull):
                        pass

        try:
            loop.call_soon_threadsafe(_deliver)
        except RuntimeError:
            # Loop closed between the is_running check and the scheduling call.
            logger.debug("Event loop closed during publish; dropping event")


broadcaster = DiscoveryBroadcaster()
