"""Storage-settings tests + regression for the .env backslash-path bug.

Bug: saving Storage Settings persisted a Windows path (e.g.
``G:\\My Drive\\999_SECOND_BRAIN``) to an EXISTING ``.env`` key. ``_persist_to_env``
used ``re.sub`` with a replacement *string*, so backslash sequences in the
value were interpreted as regex escapes ("bad escape \\M", "invalid group
reference 9") and raised ``re.error`` — which is not an ``OSError`` and so
surfaced as an unhandled HTTP 500 ("Failed to save storage settings" on the
client). Fixed by passing a replacement *function* to ``re.sub``.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api.settings as settings_api
from app.core.database import get_db
from app.main import app
from app.models.base import Base

WIN_PATH = r"G:\My Drive\999_SECOND_BRAIN"


@pytest.fixture(autouse=True)
def reset_module_registry():
    from app.modules.registry import registry
    registry._modules.clear()
    registry._initialized.clear()
    yield
    registry._modules.clear()
    registry._initialized.clear()


class TestPersistToEnvBackslashValues:
    """Direct unit tests of the root cause in _persist_to_env."""

    def test_update_existing_key_with_windows_path_does_not_raise(self, tmp_path, monkeypatch):
        env_file = tmp_path / "config.env"
        # Pre-existing key forces the in-place update (re.sub) branch.
        env_file.write_text('SECOND_BRAIN_ROOT="C:\\old\\path"\n', encoding="utf-8")
        monkeypatch.setattr(settings_api, "_get_env_file_path", lambda: env_file)

        # Previously raised re.error ("bad escape \\M"); must now succeed.
        settings_api._persist_to_env({"SECOND_BRAIN_ROOT": WIN_PATH})

        content = env_file.read_text(encoding="utf-8")
        assert WIN_PATH in content
        assert "old" not in content
        # Updated in place, not appended.
        assert sum(1 for ln in content.splitlines() if ln.startswith("SECOND_BRAIN_ROOT=")) == 1

    def test_append_new_key_with_windows_path(self, tmp_path, monkeypatch):
        env_file = tmp_path / "config.env"
        env_file.write_text("EXISTING=1\n", encoding="utf-8")
        monkeypatch.setattr(settings_api, "_get_env_file_path", lambda: env_file)
        settings_api._persist_to_env({"STORAGE_PATH": WIN_PATH})
        assert WIN_PATH in env_file.read_text(encoding="utf-8")


@pytest.fixture
def client(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: session

    env_file = tmp_path / "config.env"
    # Pre-populate keys so the endpoint exercises the update-in-place branch.
    env_file.write_text('STORAGE_PATH="C:\\old"\nSECOND_BRAIN_ROOT="C:\\old"\n', encoding="utf-8")
    monkeypatch.setattr(settings_api, "_get_env_file_path", lambda: env_file)

    # Isolate settings-singleton mutations (monkeypatch auto-restores after).
    from app.core.config import settings as cfg
    for attr in ("STORAGE_PATH", "SECOND_BRAIN_ROOT", "STORAGE_PROVIDER", "STORAGE_MODE"):
        monkeypatch.setattr(cfg, attr, getattr(cfg, attr), raising=False)

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, env_file
    app.dependency_overrides.clear()
    session.close()


class TestStorageSettingsEndpoint:
    def test_put_storage_with_windows_path_returns_200(self, client, tmp_path):
        c, env_file = client
        vault = tmp_path / "vault"
        vault.mkdir()
        resp = c.put(
            "/api/v1/settings/storage",
            json={
                "storage_provider": "local_folder",
                "storage_path": str(vault),  # real Windows path with backslashes
                "storage_mode": "legacy",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["storage_mode"] == "legacy"
        # Path persisted to the pre-existing key without error.
        assert str(vault) in env_file.read_text(encoding="utf-8")

    def test_put_storage_rejects_nonexistent_path(self, client):
        c, _ = client
        resp = c.put(
            "/api/v1/settings/storage",
            json={"storage_path": r"G:\definitely\does\not\exist\zzz999"},
        )
        assert resp.status_code == 422

    def test_get_storage_settings_ok(self, client):
        c, _ = client
        resp = c.get("/api/v1/settings/storage")
        assert resp.status_code == 200
        assert "storage_mode" in resp.json()
