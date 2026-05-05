"""Tests for the sync WebSocket broadcaster (BACKLOG-153, S33).

Covers:
- Broadcaster pub/sub (subscribe, publish, unsubscribe)
- record_sync_event populates the ring buffer + last_synced_at on success
- Conflict / error events do NOT advance last_synced_at
- /api/v1/sync/events returns the recent buffer
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base
from app.services.sync_broadcast import (
    SyncBroadcaster,
    broadcaster,
    record_sync_event,
    get_recent_sync_events,
    get_last_synced_at,
    reset_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_registry_and_log():
    from app.modules.registry import registry
    registry._modules.clear()
    registry._initialized.clear()
    reset_for_tests()
    yield
    registry._modules.clear()
    registry._initialized.clear()
    reset_for_tests()


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(test_engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_publish_delivers_to_subscriber():
    b = SyncBroadcaster()
    b.attach_loop(asyncio.get_running_loop())

    queue = b.subscribe()
    b.publish({"action": "file_synced", "success": True})

    event = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert event["action"] == "file_synced"


def test_record_event_appends_and_advances_last_synced_at():
    record_sync_event("scan_started", success=True)
    record_sync_event("file_synced", file_path="/x.md", success=True, detail="Project X")
    record_sync_event("scan_completed", success=True, stats={"scanned": 1, "synced": 1})

    events = get_recent_sync_events()
    actions = [e["action"] for e in events]
    # newest-first ordering
    assert actions == ["scan_completed", "file_synced", "scan_started"]

    # Successful completion advanced the timestamp.
    assert get_last_synced_at() is not None


def test_conflict_event_does_not_advance_last_synced_at():
    record_sync_event("conflict_detected", file_path="/c.md", success=False, error="hash mismatch")
    record_sync_event("sync_error", file_path="/c.md", success=False, error="boom")

    events = get_recent_sync_events()
    assert len(events) == 2
    # No success → last_synced_at stays unset.
    assert get_last_synced_at() is None


def test_get_recent_sync_events_respects_limit():
    for i in range(10):
        record_sync_event("file_synced", file_path=f"/f{i}.md", success=True)

    assert len(get_recent_sync_events(limit=3)) == 3
    assert len(get_recent_sync_events(limit=20)) == 10


def test_events_endpoint(client):
    record_sync_event("file_synced", file_path="/x.md", success=True, detail="Hello")

    resp = client.get("/api/v1/sync/events")
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_synced_at"] is not None
    assert body["events"][0]["action"] == "file_synced"
    assert body["events"][0]["detail"] == "Hello"


def test_broadcaster_is_module_singleton():
    from app.services import sync_broadcast as sb_mod
    assert sb_mod.broadcaster is broadcaster
