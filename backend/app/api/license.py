"""
License API endpoints

Provides license activation and status checks for the Conduital commercial tier system.

Endpoints:
    POST /license/activate   — redeem a license key (Gumroad or Stripe)
    GET  /license/status     — current license state for this installation

Key dispatch by prefix:
    gr_*        → Gumroad /v2/licenses/verify  (sync, no webhook required)
    sk_live_*/sk_test_*  → Stripe  (wired in a later session; returns 503 until ready)

Single-user mode (AUTH_ENABLED=False):
    A local system user (local@conduital.local) is created on first call and
    its id is used for all license operations.  No login required.

Auth mode (AUTH_ENABLED=True):
    Uses the authenticated user from the JWT bearer token.
"""

import logging
from datetime import timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.license_service import LicenseService

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Gumroad variant name → Conduital tier
# Keep in sync with the Gumroad product version names in the dashboard.
# ---------------------------------------------------------------------------
GUMROAD_VARIANT_TO_TIER: dict[str, str] = {
    "GTD — Most Popular": "gtd",
    "GTD+": "full",
    # Fallback: any unrecognised paid variant maps to gtd (conservative).
}

GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"

# Synthetic email used when AUTH_ENABLED=False (single-user desktop mode).
LOCAL_USER_EMAIL = "local@conduital.local"


# ---------------------------------------------------------------------------
# Dependency: resolve user_id for license operations
# ---------------------------------------------------------------------------

def get_license_user_id(db: Session = Depends(get_db)) -> int:
    """
    Return the user_id to use for license operations.

    - AUTH_ENABLED=False (default desktop mode): get-or-create a local system
      user and return its id.  No credentials required.
    - AUTH_ENABLED=True: require a valid JWT bearer token.
    """
    if not settings.AUTH_ENABLED:
        return _get_or_create_local_user(db)

    # Auth mode: import dependency lazily to avoid circular imports.
    from app.core.auth.dependencies import get_current_user  # noqa: PLC0415
    # This path is only taken when AUTH_ENABLED=True.  We can't use
    # Depends() recursively here, so we re-implement the minimal lookup.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Auth-mode license activation is not yet wired.  "
            "Ensure AUTH_ENABLED=False for this release."
        ),
    )


def _get_or_create_local_user(db: Session) -> int:
    """
    Return the id of the single local user, creating it on first call.

    This is the correct user record to bind the license to in single-user
    desktop mode.
    """
    user = db.query(User).filter(User.email == LOCAL_USER_EMAIL).first()
    if user is None:
        user = User(
            email=LOCAL_USER_EMAIL,
            display_name="Local User",
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created local system user for license binding (id=%d)", user.id)
    return user.id


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LicenseActivateRequest(BaseModel):
    license_key: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description=(
            "License key delivered after purchase.  "
            "Gumroad keys begin with 'gr_'; Stripe keys begin with 'sk_live_' or 'sk_test_'."
        ),
    )


class LicenseStatusResponse(BaseModel):
    tier: str
    effective_tier: str
    is_paid: bool
    is_trial_active: bool
    trial_expires_at: Optional[str]  # ISO 8601 or None
    activated_at: Optional[str]      # ISO 8601 or None
    purchase_id: Optional[str]


class LicenseActivateResponse(BaseModel):
    success: bool
    tier: str
    effective_tier: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/status", response_model=LicenseStatusResponse, summary="Get license status")
def get_license_status(
    user_id: int = Depends(get_license_user_id),
    db: Session = Depends(get_db),
):
    """
    Return the current license state for this installation.

    Always succeeds — creates a reverse-trial license record if none exists
    (e.g. on first launch before any key has been activated).
    """
    lic = LicenseService.get_or_create_license(db, user_id)

    trial_expires_str = None
    if lic.trial_expires_at is not None:
        ts = lic.trial_expires_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        trial_expires_str = ts.isoformat()

    activated_str = None
    if lic.activated_at is not None:
        ts = lic.activated_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        activated_str = ts.isoformat()

    return LicenseStatusResponse(
        tier=lic.tier,
        effective_tier=lic.effective_tier,
        is_paid=lic.is_paid,
        is_trial_active=lic.is_trial_active,
        trial_expires_at=trial_expires_str,
        activated_at=activated_str,
        purchase_id=lic.purchase_id,
    )


@router.post(
    "/activate",
    response_model=LicenseActivateResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate a license key",
)
def activate_license(
    body: LicenseActivateRequest,
    user_id: int = Depends(get_license_user_id),
    db: Session = Depends(get_db),
):
    """
    Redeem a license key and upgrade the installation to the purchased tier.

    Dispatches by key prefix:
    - ``gr_*``       — Gumroad: verified synchronously via /v2/licenses/verify.
    - ``sk_live_*``  — Stripe live key: not yet implemented (503).
    - ``sk_test_*``  — Stripe test key: not yet implemented (503).

    On success the license record is updated immediately and the new effective
    tier is returned.  Calling activate again with the same key is idempotent.
    """
    key = body.license_key.strip()

    if key.startswith("gr_"):
        return _activate_gumroad(key, user_id, db)

    if key.startswith(("sk_live_", "sk_test_")):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Stripe key activation is not yet available in this release.  "
                "Use your Gumroad license key instead, or wait for the next update."
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            f"Unrecognised license key format.  "
            f"Gumroad keys start with 'gr_'.  "
            f"Received key starts with: '{key[:8]}…'"
        ),
    )


# ---------------------------------------------------------------------------
# Gumroad verification
# ---------------------------------------------------------------------------

def _activate_gumroad(key: str, user_id: int, db: Session) -> LicenseActivateResponse:
    """
    Verify a Gumroad license key and activate the matching tier.

    Calls POST https://api.gumroad.com/v2/licenses/verify with:
        product_id   — from settings.GUMROAD_PRODUCT_ID
        license_key  — the raw key from the buyer

    The Gumroad response includes a ``purchase`` object whose ``variants``
    field contains the product-version name chosen at checkout.  That name
    is mapped to a Conduital tier via GUMROAD_VARIANT_TO_TIER.

    If GUMROAD_PRODUCT_ID is not configured the key is accepted but marked
    "unverified" and defaults to the gtd tier.  This allows Greg to hand out
    keys during the pre-configuration window without a hard failure.
    """
    product_id = settings.GUMROAD_PRODUCT_ID

    if not product_id:
        logger.warning(
            "GUMROAD_PRODUCT_ID not configured — accepting key without remote verification"
        )
        tier = _tier_from_key_prefix(key)
        lic = LicenseService.activate_license(
            db,
            user_id=user_id,
            tier=tier,
            purchase_id=key,
        )
        return LicenseActivateResponse(
            success=True,
            tier=lic.tier,
            effective_tier=lic.effective_tier,
            message=(
                f"License accepted (unverified — GUMROAD_PRODUCT_ID not set).  "
                f"Tier: {lic.effective_tier}"
            ),
        )

    # --- Remote verification ---
    try:
        resp = httpx.post(
            GUMROAD_VERIFY_URL,
            data={"product_id": product_id, "license_key": key},
            timeout=10.0,
        )
    except httpx.RequestError as exc:
        logger.error("Gumroad verification network error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Gumroad to verify this license key.  Check your internet connection and try again.",
        )

    payload = resp.json()

    if not payload.get("success"):
        gumroad_msg = payload.get("message", "unknown error")
        logger.warning("Gumroad rejected key %s…: %s", key[:12], gumroad_msg)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Gumroad could not verify this key: {gumroad_msg}",
        )

    purchase = payload.get("purchase", {})
    variant_name: str = purchase.get("variants", "") or ""
    sale_id: str = purchase.get("sale_id", key)
    tier = GUMROAD_VARIANT_TO_TIER.get(variant_name.strip(), "gtd")

    logger.info(
        "Gumroad key verified — sale_id=%s variant='%s' → tier=%s",
        sale_id,
        variant_name,
        tier,
    )

    lic = LicenseService.activate_license(
        db,
        user_id=user_id,
        tier=tier,
        purchase_id=sale_id,
    )

    return LicenseActivateResponse(
        success=True,
        tier=lic.tier,
        effective_tier=lic.effective_tier,
        message=f"License activated.  Tier: {lic.effective_tier}",
    )


def _tier_from_key_prefix(key: str) -> str:
    """
    Heuristic tier detection when we cannot call the Gumroad API.

    Gumroad's own key generator doesn't encode tier in the key itself,
    so we default conservatively to 'gtd' for any paid gr_ key.
    """
    return "gtd"
