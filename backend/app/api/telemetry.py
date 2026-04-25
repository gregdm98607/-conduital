"""
Telemetry API endpoint

Receives batched analytics events from the Conduital frontend and forwards
them to PostHog via the TelemetryService singleton.

All app events (install, session, trial, conversion funnel, feature gates)
route through this endpoint. This keeps PostHog as a swappable backend
rather than a hard frontend dependency.

Design (per CPO Analytics Instrumentation Plan 2026-04-23):
- Frontend sends JSON array of events to POST /api/v1/telemetry/events
- Backend checks opt-out flag, sanitises properties, forwards to PostHog
- Non-blocking: PostHog SDK calls fire in background threads
- Distinct ID is a device UUID stored in SQLite settings (no email/name)

Endpoints:
    POST /api/v1/telemetry/events     — ingest batch of app events
    GET  /api/v1/telemetry/distinct-id — get or generate installation UUID
    POST /api/v1/telemetry/opt-out    — toggle analytics opt-out
    GET  /api/v1/telemetry/status     — health / configuration check
"""

import logging
import uuid as _uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.telemetry_service import telemetry

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Known launch-blocking event names (CPO plan §5)
# Used for schema validation — unknown events are accepted but logged.
# ---------------------------------------------------------------------------
KNOWN_EVENTS: set[str] = {
    # App lifecycle
    "app_first_launch", "app_launched", "app_uninstalled",
    # Activation
    "first_project_created", "first_task_created",
    "onboarding_step_completed", "onboarding_completed",
    # Engagement
    "returned_day_3", "weekly_review_completed", "task_completed", "session_started",
    # Conversion funnel — gate hits
    "gate_hit_inbox", "gate_hit_review", "gate_hit_waiting",
    "gate_hit_scale", "gate_hit_ai", "gate_hit_proactive",
    # Conversion funnel — upgrade flow
    "upgrade_prompt_shown", "upgrade_prompt_clicked", "upgrade_prompt_dismissed",
    "checkout_started", "purchase_completed", "license_activated",
    # Trial events
    "trial_started", "trial_day_7_banner_shown", "trial_day_11_banner_shown",
    "trial_day_13_modal_shown", "trial_day_13_modal_dismissed",
    "trial_expired", "trial_extension_requested",
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class TelemetryEvent(BaseModel):
    """A single analytics event from the app."""
    event: str = Field(..., min_length=1, max_length=100)
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event")
    @classmethod
    def event_name_safe(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError("Event name must be snake_case alphanumeric")
        if v not in KNOWN_EVENTS:
            logger.debug("Unknown telemetry event: %s (accepted but logged)", v)
        return v


class TelemetryBatch(BaseModel):
    """Batch payload from the frontend."""
    distinct_id: str = Field(..., min_length=1, max_length=64)
    events: list[TelemetryEvent] = Field(..., min_length=1, max_length=100)
    opt_out: bool = Field(default=False)

    @field_validator("distinct_id")
    @classmethod
    def distinct_id_is_uuid(cls, v: str) -> str:
        # Accept any non-empty string; UUID format is strongly preferred but
        # we don't reject legacy IDs during the rollout window.
        v = v.strip()
        if not v:
            raise ValueError("distinct_id must not be empty")
        return v


class TelemetryStatusResponse(BaseModel):
    enabled: bool
    posthog_configured: bool
    opt_out: bool


class OptOutRequest(BaseModel):
    opt_out: bool


class DistinctIdResponse(BaseModel):
    distinct_id: str
    is_new: bool


# ---------------------------------------------------------------------------
# Helpers — persistent distinct_id storage
# ---------------------------------------------------------------------------

_SETTINGS_KEY_DISTINCT_ID = "analytics_distinct_id"
_SETTINGS_KEY_OPT_OUT = "analytics_opt_out"


def _get_analytics_setting(db: Session, key: str) -> Optional[str]:
    """Read a single analytics setting from the app_settings table."""
    try:
        from app.models.app_settings import AppSetting  # type: ignore[import]
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        return row.value if row else None
    except Exception:
        return None


def _set_analytics_setting(db: Session, key: str, value: str) -> None:
    """Upsert a single analytics setting in the app_settings table."""
    try:
        from app.models.app_settings import AppSetting  # type: ignore[import]
        row = db.query(AppSetting).filter(AppSetting.key == key).first()
        if row:
            row.value = value
        else:
            db.add(AppSetting(key=key, value=value))
        db.commit()
    except Exception as exc:
        logger.debug("Could not persist analytics setting %s: %s", key, exc)


def _get_or_create_distinct_id(db: Session) -> tuple[str, bool]:
    """
    Return the installation distinct_id, generating a new UUID if none exists.

    Returns (distinct_id, is_new).
    """
    existing = _get_analytics_setting(db, _SETTINGS_KEY_DISTINCT_ID)
    if existing:
        return existing, False
    new_id = str(_uuid.uuid4())
    _set_analytics_setting(db, _SETTINGS_KEY_DISTINCT_ID, new_id)
    return new_id, True


def _get_opt_out(db: Session) -> bool:
    """Return the current opt-out state."""
    val = _get_analytics_setting(db, _SETTINGS_KEY_OPT_OUT)
    return val == "true"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/events",
    status_code=status.HTTP_200_OK,
    summary="Ingest batched telemetry events",
)
def ingest_events(
    payload: TelemetryBatch,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Accept a batch of analytics events from the app frontend.

    The endpoint always returns 200 so that telemetry failures never disrupt
    the user experience. Opt-out is checked here AND in TelemetryService.capture()
    for defence in depth.
    """
    db_opt_out = _get_opt_out(db)
    effective_opt_out = payload.opt_out or db_opt_out

    if effective_opt_out:
        return {"status": "ok", "accepted": 0, "reason": "opt_out"}

    accepted = 0
    for evt in payload.events:
        telemetry.capture(
            distinct_id=payload.distinct_id,
            event=evt.event,
            properties=evt.properties,
            opt_out=False,  # Already checked above
        )
        accepted += 1

    return {"status": "ok", "accepted": accepted}


@router.get(
    "/distinct-id",
    response_model=DistinctIdResponse,
    summary="Get or generate installation distinct_id",
)
def get_distinct_id(db: Session = Depends(get_db)) -> DistinctIdResponse:
    """
    Return the persistent analytics UUID for this installation.

    The frontend calls this once at startup to obtain its distinct_id.
    If no ID exists yet, a new UUID v4 is generated and persisted.
    """
    distinct_id, is_new = _get_or_create_distinct_id(db)
    return DistinctIdResponse(distinct_id=distinct_id, is_new=is_new)


@router.post(
    "/opt-out",
    status_code=status.HTTP_200_OK,
    summary="Set analytics opt-out preference",
)
def set_opt_out(
    body: OptOutRequest,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Toggle the analytics opt-out setting.

    When opt_out=True, all subsequent calls to /events return immediately
    with 0 events accepted. The PostHog client stops calling capture().
    """
    _set_analytics_setting(db, _SETTINGS_KEY_OPT_OUT, "true" if body.opt_out else "false")
    logger.info("Analytics opt-out set to: %s", body.opt_out)
    return {"status": "ok", "opt_out": body.opt_out}


@router.get(
    "/status",
    response_model=TelemetryStatusResponse,
    summary="Telemetry configuration status",
)
def telemetry_status(db: Session = Depends(get_db)) -> TelemetryStatusResponse:
    """Return current telemetry configuration (for Settings panel debug view)."""
    return TelemetryStatusResponse(
        enabled=telemetry.is_enabled,
        posthog_configured=bool(settings.POSTHOG_WRITE_KEY or settings.POSTHOG_DEV_WRITE_KEY),
        opt_out=_get_opt_out(db),
    )
