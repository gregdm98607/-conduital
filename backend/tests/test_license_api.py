"""
Tests for the license API endpoints.

Covers:
- GET /license/status  — fresh install, trial active, paid, expired
- POST /license/activate — Gumroad path (mocked), Stripe stub, bad key format
- Trial expiry job (process_expired_trials integration)
- Single-user (AUTH_ENABLED=False) local-user creation
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models.base import Base
from app.models.license import License
from app.models.user import User
from app.services.license_service import LicenseService


# ---------------------------------------------------------------------------
# Module registry reset (prevents "already registered" errors across TestClient instances)
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_module_registry():
    """Clear the module registry before each test so lifespan re-registration works."""
    from app.modules.registry import registry
    registry._modules.clear()
    registry._initialized.clear()
    yield
    registry._modules.clear()
    registry._initialized.clear()


# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        TEST_DB_URL,
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
    """TestClient with the in-memory DB injected via dependency override."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db, email="local@conduital.local") -> User:
    user = User(email=email, display_name="Test User", is_active=True, is_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_license(db, user_id: int, **kwargs) -> License:
    lic = LicenseService.get_or_create_license(db, user_id)
    for k, v in kwargs.items():
        setattr(lic, k, v)
    db.commit()
    db.refresh(lic)
    return lic


# ---------------------------------------------------------------------------
# GET /license/status
# ---------------------------------------------------------------------------

class TestLicenseStatus:
    def test_fresh_install_creates_trial(self, client):
        """First call to /status bootstraps a reverse-trial license."""
        resp = client.get("/api/v1/license/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_trial_active"] is True
        assert data["effective_tier"] == "full"
        assert data["is_paid"] is False
        assert data["trial_expires_at"] is not None

    def test_status_idempotent(self, client):
        """Calling /status twice returns the same record."""
        r1 = client.get("/api/v1/license/status").json()
        r2 = client.get("/api/v1/license/status").json()
        assert r1["trial_expires_at"] == r2["trial_expires_at"]

    def test_expired_trial_shows_free(self, client, db):
        """After trial expiry, effective_tier is 'free'."""
        user = _make_user(db)
        _make_license(
            db,
            user.id,
            tier="full",
            trial_expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        resp = client.get("/api/v1/license/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_trial_active"] is False
        assert data["effective_tier"] == "free"

    def test_paid_license_shows_correct_tier(self, client, db):
        """A paid activation overrides trial state."""
        user = _make_user(db)
        lic = _make_license(db, user.id)
        LicenseService.activate_license(db, user.id, tier="gtd", purchase_id="gr_abc123")
        resp = client.get("/api/v1/license/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_paid"] is True
        assert data["tier"] == "gtd"
        assert data["effective_tier"] == "gtd"


# ---------------------------------------------------------------------------
# POST /license/activate — Gumroad path
# ---------------------------------------------------------------------------

GUMROAD_SUCCESS_GTD = {
    "success": True,
    "purchase": {
        "sale_id": "sale_gtd_001",
        "variants": "GTD — Most Popular",
        "email": "buyer@example.com",
    },
}

GUMROAD_SUCCESS_FULL = {
    "success": True,
    "purchase": {
        "sale_id": "sale_full_001",
        "variants": "GTD+",
        "email": "buyer@example.com",
    },
}

GUMROAD_FAILURE = {"success": False, "message": "That license does not exist."}


class TestActivateGumroad:
    def _post(self, client, key: str):
        return client.post("/api/v1/license/activate", json={"license_key": key})

    @patch("app.api.license.settings")
    @patch("app.api.license.httpx.post")
    def test_gtd_variant_activates_gtd_tier(self, mock_post, mock_settings, client):
        mock_settings.AUTH_ENABLED = False
        mock_settings.GUMROAD_PRODUCT_ID = "conduital"
        mock_resp = MagicMock()
        mock_resp.json.return_value = GUMROAD_SUCCESS_GTD
        mock_post.return_value = mock_resp

        resp = self._post(client, "gr_gtd_abc123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["tier"] == "gtd"
        assert data["effective_tier"] == "gtd"

    @patch("app.api.license.settings")
    @patch("app.api.license.httpx.post")
    def test_full_variant_activates_full_tier(self, mock_post, mock_settings, client):
        mock_settings.AUTH_ENABLED = False
        mock_settings.GUMROAD_PRODUCT_ID = "conduital"
        mock_resp = MagicMock()
        mock_resp.json.return_value = GUMROAD_SUCCESS_FULL
        mock_post.return_value = mock_resp

        resp = self._post(client, "gr_full_abc123")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "full"
        assert data["effective_tier"] == "full"

    @patch("app.api.license.settings")
    @patch("app.api.license.httpx.post")
    def test_gumroad_rejection_returns_422(self, mock_post, mock_settings, client):
        mock_settings.AUTH_ENABLED = False
        mock_settings.GUMROAD_PRODUCT_ID = "conduital"
        mock_resp = MagicMock()
        mock_resp.json.return_value = GUMROAD_FAILURE
        mock_post.return_value = mock_resp

        resp = self._post(client, "gr_invalid_key")
        assert resp.status_code == 422
        assert "does not exist" in resp.json()["detail"]

    @patch("app.api.license.settings")
    @patch("app.api.license.httpx.post")
    def test_network_error_returns_502(self, mock_post, mock_settings, client):
        import httpx as _httpx
        mock_settings.AUTH_ENABLED = False
        mock_settings.GUMROAD_PRODUCT_ID = "conduital"
        mock_post.side_effect = _httpx.ConnectError("timeout")

        resp = self._post(client, "gr_network_fail")
        assert resp.status_code == 502

    @patch("app.api.license.settings")
    def test_no_product_id_accepts_key_unverified(self, mock_settings, client):
        """When GUMROAD_PRODUCT_ID is blank, key is accepted without remote call."""
        mock_settings.AUTH_ENABLED = False
        mock_settings.GUMROAD_PRODUCT_ID = ""

        resp = self._post(client, "gr_unverified_key")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "unverified" in data["message"]

    @patch("app.api.license.settings")
    @patch("app.api.license.httpx.post")
    def test_activate_is_idempotent(self, mock_post, mock_settings, client):
        """Activating the same key twice succeeds both times."""
        mock_settings.AUTH_ENABLED = False
        mock_settings.GUMROAD_PRODUCT_ID = "conduital"
        mock_resp = MagicMock()
        mock_resp.json.return_value = GUMROAD_SUCCESS_GTD
        mock_post.return_value = mock_resp

        r1 = self._post(client, "gr_idempotent_key")
        r2 = self._post(client, "gr_idempotent_key")
        assert r1.status_code == 200
        assert r2.status_code == 200


# ---------------------------------------------------------------------------
# POST /license/activate — other key formats
# ---------------------------------------------------------------------------

class TestActivateOtherFormats:
    def test_stripe_live_key_returns_503(self, client):
        resp = client.post(
            "/api/v1/license/activate",
            json={"license_key": "sk_live_abc123"},
        )
        assert resp.status_code == 503
        assert "Stripe" in resp.json()["detail"]

    def test_stripe_test_key_returns_503(self, client):
        resp = client.post(
            "/api/v1/license/activate",
            json={"license_key": "sk_test_abc123"},
        )
        assert resp.status_code == 503

    def test_unknown_prefix_returns_400(self, client):
        resp = client.post(
            "/api/v1/license/activate",
            json={"license_key": "xx_garbage"},
        )
        assert resp.status_code == 400
        assert "Unrecognised" in resp.json()["detail"]

    def test_empty_key_rejected(self, client):
        resp = client.post("/api/v1/license/activate", json={"license_key": ""})
        assert resp.status_code == 422  # Pydantic validation


# ---------------------------------------------------------------------------
# Trial expiry job (unit-level, no HTTP)
# ---------------------------------------------------------------------------

class TestTrialExpiry:
    def test_expired_trial_downgraded(self, db):
        user = _make_user(db, email="expiry@conduital.local")
        _make_license(
            db,
            user.id,
            tier="full",
            trial_expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        affected = LicenseService.process_expired_trials(db)
        assert user.id in affected
        db.refresh(user.license)
        assert user.license.tier == "free"

    def test_active_trial_not_downgraded(self, db):
        user = _make_user(db, email="active@conduital.local")
        _make_license(
            db,
            user.id,
            tier="full",
            trial_expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        affected = LicenseService.process_expired_trials(db)
        assert user.id not in affected
        db.refresh(user.license)
        assert user.license.tier == "full"

    def test_paid_license_not_touched(self, db):
        """A paid license is never downgraded even if trial_expires_at has passed."""
        user = _make_user(db, email="paid@conduital.local")
        LicenseService.activate_license(
            db, user.id, tier="gtd", purchase_id="gr_paid_test"
        )
        # Manually push trial expiry into the past
        lic = user.license
        db.refresh(lic)
        lic.trial_expires_at = datetime.now(timezone.utc) - timedelta(days=30)
        db.commit()

        affected = LicenseService.process_expired_trials(db)
        assert user.id not in affected
        db.refresh(lic)
        assert lic.tier == "gtd"

    def test_no_licenses_returns_empty_list(self, db):
        affected = LicenseService.process_expired_trials(db)
        assert affected == []
