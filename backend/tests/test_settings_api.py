"""
Settings API endpoint tests

Tests the persist-first pattern (DEBT-075) and settings CRUD:
- GET/PUT momentum settings round-trip
- Momentum threshold validation (at_risk >= stalled rejected)
- GET AI settings returns masked keys
- PUT AI settings persist-first behavior
- GET/PUT sync settings round-trip
- Persist failure rolls back (no in-memory mutation)
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.models.base import Base


@pytest.fixture(scope="function")
def test_client(in_memory_engine):
    """Create a TestClient with proper database override for settings tests."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=in_memory_engine
    )
    Base.metadata.create_all(bind=in_memory_engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("app.core.database.init_db"),
        patch("app.main.enable_wal_mode"),
        patch("app.main.register_modules", return_value=set()),
        patch("app.main.mount_module_routers"),
        patch("app.services.scheduler_service.start_scheduler"),
        patch(
            "app.services.scheduler_service.run_urgency_zone_recalculation_now",
            new_callable=AsyncMock,
        ),
    ):
        client = TestClient(app)
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=in_memory_engine)


class TestMomentumSettings:
    """Tests for GET/PUT /api/v1/settings/momentum"""

    def test_get_momentum_settings(self, test_client):
        resp = test_client.get("/api/v1/settings/momentum")
        assert resp.status_code == 200
        data = resp.json()
        assert "stalled_threshold_days" in data
        assert "at_risk_threshold_days" in data
        assert "activity_decay_days" in data
        assert "recalculate_interval" in data

    @patch("app.api.settings._persist_to_env")
    def test_put_momentum_round_trip(self, mock_persist, test_client):
        resp = test_client.put(
            "/api/v1/settings/momentum",
            json={"stalled_threshold_days": 21, "at_risk_threshold_days": 10},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stalled_threshold_days"] == 21
        assert data["at_risk_threshold_days"] == 10
        mock_persist.assert_called_once()

        # GET should reflect the change
        resp2 = test_client.get("/api/v1/settings/momentum")
        assert resp2.json()["stalled_threshold_days"] == 21

    def test_put_momentum_rejects_invalid_relationship(self, test_client):
        """at_risk must be strictly less than stalled"""
        resp = test_client.put(
            "/api/v1/settings/momentum",
            json={"stalled_threshold_days": 10, "at_risk_threshold_days": 10},
        )
        assert resp.status_code == 422

    def test_put_momentum_rejects_at_risk_greater_than_stalled(self, test_client):
        resp = test_client.put(
            "/api/v1/settings/momentum",
            json={"stalled_threshold_days": 5, "at_risk_threshold_days": 8},
        )
        assert resp.status_code == 422

    @patch("app.api.settings._persist_to_env", side_effect=OSError("disk full"))
    def test_put_momentum_persist_failure_no_memory_mutation(
        self, mock_persist, test_client
    ):
        """If .env write fails, in-memory settings must NOT change (DEBT-075)."""
        # Get current values
        before = test_client.get("/api/v1/settings/momentum").json()

        resp = test_client.put(
            "/api/v1/settings/momentum",
            json={"stalled_threshold_days": 30, "at_risk_threshold_days": 5},
        )
        assert resp.status_code == 500

        # Verify in-memory settings unchanged
        after = test_client.get("/api/v1/settings/momentum").json()
        assert after["stalled_threshold_days"] == before["stalled_threshold_days"]
        assert after["at_risk_threshold_days"] == before["at_risk_threshold_days"]

    @patch("app.api.settings._persist_to_env")
    def test_put_momentum_partial_update(self, mock_persist, test_client):
        """Only provided fields should be updated."""
        resp = test_client.put(
            "/api/v1/settings/momentum",
            json={"activity_decay_days": 60},
        )
        assert resp.status_code == 200
        assert resp.json()["activity_decay_days"] == 60
        mock_persist.assert_called_once()


class TestAISettings:
    """Tests for GET/PUT /api/v1/settings/ai"""

    def test_get_ai_settings_masks_keys(self, test_client):
        resp = test_client.get("/api/v1/settings/ai")
        assert resp.status_code == 200
        data = resp.json()
        assert "ai_provider" in data
        assert "ai_features_enabled" in data
        assert "available_providers" in data
        # Key should be masked or None, never raw
        if data["api_key_configured"]:
            assert data["api_key_masked"].startswith("...")

    @patch("app.api.settings._persist_to_env")
    def test_put_ai_settings_updates_provider(self, mock_persist, test_client):
        resp = test_client.put(
            "/api/v1/settings/ai",
            json={"ai_provider": "openai", "ai_model": "gpt-4"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ai_provider"] == "openai"
        assert data["ai_model"] == "gpt-4"
        mock_persist.assert_called_once()

    @patch("app.api.settings._persist_to_env", side_effect=OSError("disk full"))
    def test_put_ai_persist_failure_no_memory_mutation(
        self, mock_persist, test_client
    ):
        """If .env write fails, in-memory AI settings must NOT change (DEBT-075)."""
        before = test_client.get("/api/v1/settings/ai").json()

        resp = test_client.put(
            "/api/v1/settings/ai",
            json={"ai_provider": "google"},
        )
        assert resp.status_code == 500

        after = test_client.get("/api/v1/settings/ai").json()
        assert after["ai_provider"] == before["ai_provider"]

    @patch("app.api.settings._persist_to_env")
    def test_put_ai_settings_empty_body_is_noop(self, mock_persist, test_client):
        resp = test_client.put("/api/v1/settings/ai", json={})
        assert resp.status_code == 200
        mock_persist.assert_not_called()


class TestSyncSettings:
    """Tests for GET/PUT /api/v1/settings/sync"""

    def test_get_sync_settings(self, test_client):
        resp = test_client.get("/api/v1/settings/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert "sync_folder_root" in data
        assert "watch_directories" in data
        assert "sync_interval" in data
        assert "conflict_strategy" in data

    @patch("app.api.settings._persist_to_env")
    def test_put_sync_settings_interval(self, mock_persist, test_client):
        resp = test_client.put(
            "/api/v1/settings/sync",
            json={"sync_interval": 30, "conflict_strategy": "file_wins"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["sync_interval"] == 30
        assert data["conflict_strategy"] == "file_wins"
        mock_persist.assert_called_once()

    def test_put_sync_settings_rejects_nonexistent_path(self, test_client):
        resp = test_client.put(
            "/api/v1/settings/sync",
            json={"sync_folder_root": "/definitely/not/a/real/path"},
        )
        assert resp.status_code == 422

    @patch("app.api.settings._persist_to_env", side_effect=OSError("disk full"))
    def test_put_sync_persist_failure_no_memory_mutation(
        self, mock_persist, test_client
    ):
        """If .env write fails, in-memory sync settings must NOT change (DEBT-075)."""
        before = test_client.get("/api/v1/settings/sync").json()

        resp = test_client.put(
            "/api/v1/settings/sync",
            json={"sync_interval": 120},
        )
        assert resp.status_code == 500

        after = test_client.get("/api/v1/settings/sync").json()
        assert after["sync_interval"] == before["sync_interval"]

    @patch("app.api.settings._persist_to_env")
    def test_put_sync_clear_folder_root(self, mock_persist, test_client):
        """Empty string should clear the sync folder root."""
        resp = test_client.put(
            "/api/v1/settings/sync",
            json={"sync_folder_root": ""},
        )
        assert resp.status_code == 200
        assert resp.json()["sync_folder_root"] is None
        mock_persist.assert_called_once()


class TestPersistToEnv:
    """Tests for _persist_to_env utility function."""

    def test_persist_creates_env_file(self, tmp_path):
        """_persist_to_env should create .env if it doesn't exist."""
        env_file = tmp_path / "config.env"

        with patch("app.api.settings._get_env_file_path", return_value=env_file):
            from app.api.settings import _persist_to_env

            _persist_to_env({"TEST_KEY": "test_value"})

        content = env_file.read_text()
        assert "TEST_KEY=test_value" in content

    def test_persist_updates_existing_key(self, tmp_path):
        """_persist_to_env should update existing keys in place."""
        env_file = tmp_path / "config.env"
        env_file.write_text("EXISTING_KEY=old_value\nOTHER=keep\n")

        with patch("app.api.settings._get_env_file_path", return_value=env_file):
            from app.api.settings import _persist_to_env

            _persist_to_env({"EXISTING_KEY": "new_value"})

        content = env_file.read_text()
        assert "EXISTING_KEY=new_value" in content
        assert "OTHER=keep" in content
        assert "old_value" not in content

    def test_persist_appends_new_key(self, tmp_path):
        env_file = tmp_path / "config.env"
        env_file.write_text("EXISTING=value\n")

        with patch("app.api.settings._get_env_file_path", return_value=env_file):
            from app.api.settings import _persist_to_env

            _persist_to_env({"NEW_KEY": "new_value"})

        content = env_file.read_text()
        assert "EXISTING=value" in content
        assert "NEW_KEY=new_value" in content

    def test_persist_raises_on_write_failure(self, tmp_path):
        """_persist_to_env must raise OSError on failure, not swallow it."""
        env_file = tmp_path / "nonexistent_dir" / "config.env"

        with patch("app.api.settings._get_env_file_path", return_value=env_file):
            from app.api.settings import _persist_to_env

            with pytest.raises(OSError):
                _persist_to_env({"KEY": "value"})
