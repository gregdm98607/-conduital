"""
Tests for the feedback API endpoints (F-001 / MON-011).

Covers:
- POST /feedback              — create entries
- GET  /feedback              — list with category + resolved filters, pagination
- GET  /feedback/{id}         — fetch one
- PATCH /feedback/{id}        — toggle resolved flag
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base


@pytest.fixture(autouse=True)
def reset_module_registry():
    """Clear the module registry before each test so lifespan re-registration works."""
    from app.modules.registry import registry
    registry._modules.clear()
    registry._initialized.clear()
    yield
    registry._modules.clear()
    registry._initialized.clear()


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


def _submit(client, **overrides):
    payload = {
        "category": "bug",
        "message": "Something broke",
        "page": "/projects",
    }
    payload.update(overrides)
    resp = client.post("/api/v1/feedback", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCreate:
    def test_creates_with_defaults_and_returns_unresolved(self, client):
        """New entries should default to resolved=False (visible via list)."""
        created = _submit(client)
        assert created["category"] == "bug"

        listing = client.get("/api/v1/feedback").json()
        assert len(listing) == 1
        assert listing[0]["resolved"] is False
        assert listing[0]["message"] == "Something broke"

    def test_strips_whitespace_only_messages(self, client):
        resp = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "   "},
        )
        assert resp.status_code == 422


class TestList:
    def test_filter_by_category(self, client):
        _submit(client, category="bug", message="bug one")
        _submit(client, category="feature", message="feature one")
        _submit(client, category="general", message="general one")

        bugs = client.get("/api/v1/feedback?category=bug").json()
        assert len(bugs) == 1
        assert bugs[0]["category"] == "bug"

    def test_filter_by_resolved(self, client):
        _submit(client, message="open")
        second = _submit(client, message="closed")

        # Mark second resolved
        client.patch(
            f"/api/v1/feedback/{second['id']}", json={"resolved": True}
        )

        unresolved = client.get("/api/v1/feedback?resolved=false").json()
        assert [e["message"] for e in unresolved] == ["open"]

        resolved = client.get("/api/v1/feedback?resolved=true").json()
        assert [e["message"] for e in resolved] == ["closed"]

    def test_pagination(self, client):
        for i in range(5):
            _submit(client, message=f"msg-{i}")
        page1 = client.get("/api/v1/feedback?page=1&page_size=2").json()
        page2 = client.get("/api/v1/feedback?page=2&page_size=2").json()
        assert len(page1) == 2
        assert len(page2) == 2
        # Newest first → page 1 starts with the last submitted
        assert page1[0]["message"] == "msg-4"

    def test_returns_resolved_field(self, client):
        _submit(client)
        listing = client.get("/api/v1/feedback").json()
        assert "resolved" in listing[0]


class TestPatch:
    def test_toggle_resolved_flag(self, client):
        created = _submit(client)
        fid = created["id"]

        resp = client.patch(f"/api/v1/feedback/{fid}", json={"resolved": True})
        assert resp.status_code == 200
        assert resp.json()["resolved"] is True

        # Toggle back
        resp = client.patch(f"/api/v1/feedback/{fid}", json={"resolved": False})
        assert resp.status_code == 200
        assert resp.json()["resolved"] is False

    def test_404_for_unknown_id(self, client):
        resp = client.patch("/api/v1/feedback/9999", json={"resolved": True})
        assert resp.status_code == 404

    def test_resolved_field_required(self, client):
        created = _submit(client)
        resp = client.patch(f"/api/v1/feedback/{created['id']}", json={})
        assert resp.status_code == 422
