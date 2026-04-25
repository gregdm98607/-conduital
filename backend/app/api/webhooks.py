"""
Stripe Webhook Handler

Handles incoming Stripe webhook events for Conduital purchase fulfillment.

Flow on checkout.session.completed:
  1. Verify Stripe webhook signature (STRIPE_WEBHOOK_SECRET)
  2. Extract buyer email + tier from session metadata
  3. Generate a 32-byte hex license key
  4. Activate/upsert the local license record
  5. Send transactional fulfillment email via Resend (key + download URL)

Endpoints:
    POST /api/v1/webhooks/stripe   — Stripe signed webhook delivery

Configuration (.env):
    STRIPE_SECRET_KEY        — sk_live_* or sk_test_*
    STRIPE_WEBHOOK_SECRET    — whsec_* (from Stripe Dashboard → Webhooks)
    RESEND_API_KEY           — re_* (from resend.com dashboard)
    CONDUITAL_DOWNLOAD_URL   — https://conduital.com/download/v1.3.0
    STRIPE_GTD_PRICE_ID      — price_* for the GTD tier
    STRIPE_FULL_PRICE_ID     — price_* for the Full tier
"""

import hashlib
import hmac
import logging
import secrets
import time
from typing import Any

import httpx
from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.license_service import LicenseService

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Tier mapping: Stripe price ID → Conduital tier
# Populated from config so the dashboard can change prices without redeploy.
# ---------------------------------------------------------------------------

def _get_tier_for_price(price_id: str) -> str:
    """Map a Stripe Price ID to a Conduital tier string."""
    mapping: dict[str, str] = {}
    if settings.STRIPE_GTD_PRICE_ID:
        mapping[settings.STRIPE_GTD_PRICE_ID] = "gtd"
    if settings.STRIPE_FULL_PRICE_ID:
        mapping[settings.STRIPE_FULL_PRICE_ID] = "full"
    return mapping.get(price_id, "gtd")  # Conservative default


# ---------------------------------------------------------------------------
# Signature verification
# ---------------------------------------------------------------------------

def _verify_stripe_signature(payload: bytes, sig_header: str, secret: str) -> bool:
    """
    Verify a Stripe webhook signature.

    Stripe uses HMAC-SHA256 over "timestamp.payload" with the webhook signing
    secret. The signature header has the form:
        t=<timestamp>,v1=<hex_digest>[,v1=<hex_digest>...]

    Rejects events with a timestamp older than 5 minutes to prevent replay.
    """
    parts: dict[str, list[str]] = {}
    for part in sig_header.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            parts.setdefault(k.strip(), []).append(v.strip())

    timestamps = parts.get("t", [])
    signatures = parts.get("v1", [])

    if not timestamps or not signatures:
        return False

    try:
        ts = int(timestamps[0])
    except ValueError:
        return False

    # Replay protection: reject if older than 5 minutes
    if abs(time.time() - ts) > 300:
        logger.warning("Stripe webhook timestamp out of tolerance: %d", ts)
        return False

    signed_payload = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()

    return any(hmac.compare_digest(expected, sig) for sig in signatures)


# ---------------------------------------------------------------------------
# Email fulfillment via Resend
# ---------------------------------------------------------------------------

def _send_fulfillment_email(buyer_email: str, tier: str, license_key: str) -> bool:
    """
    Send a post-purchase fulfillment email with the license key and download URL.

    Returns True on success, False on any delivery failure (non-fatal — the
    license is already activated; Greg can re-send manually if needed).
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured — skipping fulfillment email to %s", buyer_email)
        return False

    tier_label = {"gtd": "GTD", "full": "GTD+"}.get(tier, tier.upper())
    download_url = settings.CONDUITAL_DOWNLOAD_URL or "https://conduital.com/download/v1.3.0"

    subject = f"Your Conduital {tier_label} license key is ready"
    html_body = f"""
<p>Hi there,</p>

<p>Thank you for purchasing <strong>Conduital {tier_label}</strong>. Your license key is below.</p>

<p style="font-size:18px; font-family:monospace; background:#f4f4f4; padding:12px; border-radius:4px;">
  {license_key}
</p>

<p>
  <a href="{download_url}" style="display:inline-block;background:#0070f3;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;">
    Download Conduital
  </a>
</p>

<ol>
  <li>Download and install Conduital from the link above.</li>
  <li>Open <strong>Settings → License</strong>.</li>
  <li>Paste your key and click <strong>Activate</strong>.</li>
</ol>

<p>Your {tier_label} features will unlock immediately. Keep this email — your key is permanent.</p>

<p>Questions? Reply to this email or visit <a href="https://conduital.com">conduital.com</a>.</p>

<p>— The Conduital Team</p>
""".strip()

    text_body = (
        f"Your Conduital {tier_label} license key:\n\n{license_key}\n\n"
        f"Download: {download_url}\n\n"
        "To activate: open Settings → License, paste your key, click Activate.\n\n"
        "Questions? Visit conduital.com"
    )

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": "Conduital <licenses@conduital.com>",
                "to": [buyer_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
            },
            timeout=10.0,
        )
        if resp.status_code in (200, 201):
            logger.info("Fulfillment email sent to %s (tier=%s)", buyer_email, tier)
            return True
        else:
            logger.error(
                "Resend returned %d for fulfillment email to %s: %s",
                resp.status_code,
                buyer_email,
                resp.text[:300],
            )
            return False
    except httpx.RequestError as exc:
        logger.error("Network error sending fulfillment email to %s: %s", buyer_email, exc)
        return False


# ---------------------------------------------------------------------------
# License key generation
# ---------------------------------------------------------------------------

def _generate_license_key() -> str:
    """
    Generate a 32-byte (64-char hex) cryptographically secure license key.

    Format: XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX (8 groups of 4 hex chars)
    so it reads cleanly in the activation UI.
    """
    raw = secrets.token_hex(32).upper()
    # Group into 8 × 4-character segments separated by dashes
    return "-".join(raw[i : i + 8] for i in range(0, 64, 8))


# ---------------------------------------------------------------------------
# Local user resolution for license binding
# ---------------------------------------------------------------------------

LOCAL_USER_EMAIL = "local@conduital.local"


def _get_or_create_local_user(db: Session) -> int:
    """Return the id of the single local desktop user, creating it on first call."""
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
    return user.id


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/stripe",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook receiver",
    include_in_schema=False,  # Hide from public API docs
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
) -> dict[str, str]:
    """
    Receive and process Stripe webhook events.

    Only `checkout.session.completed` triggers fulfillment.
    All other event types return 200 immediately (Stripe requires this).

    Stripe retries on non-200 responses, so we return 200 even when the
    webhook secret is unconfigured — this avoids infinite retry loops in
    dev/staging environments where the secret isn't wired yet.
    """
    payload = await request.body()

    # --- Signature verification ---
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if webhook_secret:
        if not stripe_signature:
            logger.warning("Stripe webhook received with no signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header",
            )
        if not _verify_stripe_signature(payload, stripe_signature, webhook_secret):
            logger.warning("Stripe webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook signature verification failed",
            )
    else:
        logger.warning(
            "STRIPE_WEBHOOK_SECRET not configured — processing webhook without verification "
            "(acceptable in dev; set secret before production)"
        )

    # --- Parse event ---
    import json
    try:
        event: dict[str, Any] = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type: str = event.get("type", "")
    logger.info("Received Stripe event: %s (id=%s)", event_type, event.get("id", "?"))

    # --- Only handle checkout completion ---
    if event_type != "checkout.session.completed":
        return {"status": "ignored", "event": event_type}

    session_data: dict[str, Any] = event.get("data", {}).get("object", {})
    return await _handle_checkout_completed(session_data)


async def _handle_checkout_completed(session: dict[str, Any]) -> dict[str, str]:
    """
    Fulfillment logic for checkout.session.completed.

    Steps:
    1. Extract buyer email + price metadata
    2. Determine tier from price ID (or metadata)
    3. Generate license key
    4. Activate local license record
    5. Send fulfillment email
    """
    buyer_email: str = (
        session.get("customer_details", {}).get("email")
        or session.get("customer_email")
        or ""
    )
    stripe_customer_id: str = session.get("customer", "") or ""
    payment_intent: str = session.get("payment_intent", "") or session.get("id", "")

    # Resolve tier from session metadata (preferred) or line items price ID
    metadata = session.get("metadata", {}) or {}
    tier = metadata.get("conduital_tier", "")
    if not tier:
        # Fall back to price-based mapping if metadata not set
        line_items_url = session.get("url", "")  # not reliable — prefer metadata
        price_id = metadata.get("price_id", "")
        tier = _get_tier_for_price(price_id) if price_id else "gtd"

    # Generate license key
    license_key = _generate_license_key()

    # Activate license in local SQLite — use purchase_id = generated key
    from app.core.database import SessionLocal
    with SessionLocal() as db:
        user_id = _get_or_create_local_user(db)
        LicenseService.activate_license(
            db,
            user_id=user_id,
            tier=tier,
            purchase_id=license_key,
            stripe_customer_id=stripe_customer_id or None,
        )
        logger.info(
            "License activated via Stripe webhook — tier=%s payment_intent=%s",
            tier,
            payment_intent,
        )

    # Send fulfillment email (best-effort; non-fatal on failure)
    email_sent = False
    if buyer_email:
        email_sent = _send_fulfillment_email(buyer_email, tier, license_key)
    else:
        logger.warning(
            "No buyer email in checkout.session.completed (payment_intent=%s) — "
            "cannot send fulfillment email",
            payment_intent,
        )

    return {
        "status": "fulfilled",
        "tier": tier,
        "email_sent": str(email_sent),
    }
