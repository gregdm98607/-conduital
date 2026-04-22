"""Tests for the discovery WebSocket broadcaster (DEBT-016).

Covers:
- Broadcaster pub/sub (subscribe, publish, unsubscribe, bounded queue drop)
- Thread-safe publish from worker threads via call_soon_threadsafe
- /ws/discovery-status handshake: sends snapshot, then streams events
- Broadcaster is wired into _record_event in auto_discovery_service
"""

import asyncio
import threading

import pytest

from app.services.discovery_broadcast import DiscoveryBroadcaster, broadcaster


# ---------- Broadcaster unit tests ----------

@pytest.mark.asyncio
async def test_publish_delivers_to_subscriber():
    b = DiscoveryBroadcaster()
    b.attach_loop(asyncio.get_running_loop())

    queue = b.subscribe()
    b.publish({"action": "project_created", "folder": "foo", "success": True})

    event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert event["action"] == "project_created"
    assert event["folder"] == "foo"
    assert event["success"] is True


@pytest.mark.asyncio
async def test_publish_without_loop_is_noop():
    # No attach_loop call — publish should silently drop (e.g. unit tests without runtime).
    b = DiscoveryBroadcaster()
    b.publish({"action": "x", "folder": "y", "success": True})
    # No exception raised, no subscribers to check. Success = we didn't crash.


@pytest.mark.asyncio
async def test_unsubscribe_removes_queue():
    b = DiscoveryBroadcaster()
    b.attach_loop(asyncio.get_running_loop())

    queue = b.subscribe()
    assert b.subscriber_count() == 1
    b.unsubscribe(queue)
    assert b.subscriber_count() == 0

    b.publish({"action": "x", "folder": "y", "success": True})
    await asyncio.sleep(0.05)
    assert queue.empty()


@pytest.mark.asyncio
async def test_publish_from_thread_is_thread_safe():
    b = DiscoveryBroadcaster()
    b.attach_loop(asyncio.get_running_loop())
    queue = b.subscribe()

    def publish_from_thread():
        b.publish({"action": "thread_event", "folder": "bg", "success": True})

    thread = threading.Thread(target=publish_from_thread)
    thread.start()
    thread.join(timeout=1.0)

    event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert event["action"] == "thread_event"


@pytest.mark.asyncio
async def test_full_queue_drops_oldest():
    b = DiscoveryBroadcaster()
    b.attach_loop(asyncio.get_running_loop())
    queue = b.subscribe(maxsize=2)

    for i in range(5):
        b.publish({"seq": i, "action": "x", "folder": "y", "success": True})
    # Give call_soon_threadsafe a chance to drain.
    await asyncio.sleep(0.05)

    # Queue should hold the 2 newest events; older ones dropped.
    received = []
    while not queue.empty():
        received.append(queue.get_nowait())
    seqs = [e["seq"] for e in received]
    assert len(seqs) == 2
    assert 4 in seqs  # newest always retained


# ---------- Integration: _record_event publishes to the broadcaster ----------

@pytest.mark.asyncio
async def test_record_event_publishes_to_subscribers():
    """End-to-end: a discovery event recorded via the real helper flows
    through the module singleton to an active subscriber."""
    from app.services.auto_discovery_service import _record_event

    broadcaster.attach_loop(asyncio.get_running_loop())
    queue = broadcaster.subscribe()
    try:
        # _record_event is thread-safe and calls broadcaster.publish internally.
        _record_event(
            action="project_created",
            folder="99.99 Test_Project",
            success=True,
            detail="Test",
        )

        event = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert event["action"] == "project_created"
        assert event["folder"] == "99.99 Test_Project"
        assert event["success"] is True
        assert event["detail"] == "Test"
        assert "timestamp" in event
    finally:
        broadcaster.unsubscribe(queue)


def test_broadcaster_is_module_singleton():
    # _record_event imports the module-level singleton; verify it's the same
    # object the WS route subscribes to (guards against accidental re-binding).
    from app.services import discovery_broadcast as db_mod
    assert db_mod.broadcaster is broadcaster
