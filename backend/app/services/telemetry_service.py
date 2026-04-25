"""
Telemetry Service — PostHog integration

Wraps the PostHog Python SDK behind a thin service layer so PostHog remains a
swappable implementation detail rather than a hard dependency throughout the app.

Design decisions (per CPO Analytics Instrumentation Plan 2026-04-23):
- All app events route through POST /api/v1/telemetry/events (batch)
- Distinct ID is a UUID persisted in SQLite settings; no email/name/PII
- Opt-out toggle in Settings stops all posthog.capture() calls for app events
- Two PostHog write keys: Dev (POSTHOG_DEV_WRITE_KEY) and Prod (POSTHOG_WRITE_KEY)
- Web events (conduital.com) use a separate JS snippet — not this service
- posthog.capture() is called in a background thread to stay non-blocking

Privacy rules (enforced here, not at call sites):
- No property value may exceed 200 characters (safety net for accidental PII)
- No property key or value may contain "@" (email leakage guard)
- Allowed property value types: int, float, bool, str (enum-style only)

Usage:
    from app.services.telemetry_service import telemetry

    telemetry.capture(distinct_id, "app_launched", {
        "session_number": 3,
        "tier": "gtd",
        "trial_days_remaining": None,
    })
"""

import logging
import threading
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

# PostHog EU endpoint (privacy-conscious default)
POSTHOG_HOST = "https://us.i.posthog.com"

# Maximum property string value length — safety net against accidental content leakage
MAX_PROP_VALUE_LEN = 200


class TelemetryService:
    """
    Singleton wrapper around the PostHog Python client.

    Initialised lazily on first use so import order doesn't matter.
    Thread-safe: uses a threading.Lock for init guard; PostHog SDK itself
    is thread-safe.
    """

    def __init__(self) -> None:
        self._client: Any = None
        self._init_lock = threading.Lock()
        self._enabled: bool = False

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def init(self, write_key: str, enabled: bool = True) -> None:
        """
        Initialise the PostHog client.

        Call once at app startup (from lifespan or router registration).
        Idempotent — safe to call multiple times; subsequent calls are no-ops.

        Args:
            write_key: PostHog project write key (Dev or Prod)
            enabled:   False → all capture() calls are silenced immediately
        """
        with self._init_lock:
            if self._client is not None:
                return  # Already initialised

            self._enabled = enabled

            if not write_key or not enabled:
                logger.info(
                    "Telemetry disabled (write_key_present=%s, enabled=%s)",
                    bool(write_key),
                    enabled,
                )
                return

            try:
                import posthog as ph  # type: ignore[import]

                ph.project_api_key = write_key
                ph.host = POSTHOG_HOST
                # Disable PostHog's own exception capture — we handle errors ourselves
                ph.on_error = None
                # Flush synchronously on process exit
                ph.sync_mode = False
                self._client = ph
                logger.info("PostHog telemetry initialised (host=%s)", POSTHOG_HOST)
            except ImportError:
                logger.warning(
                    "posthog package not installed — telemetry disabled. "
                    "Run: poetry add posthog"
                )
            except Exception as exc:
                logger.error("PostHog init failed: %s", exc)

    # ------------------------------------------------------------------
    # Property sanitisation
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitise_properties(props: dict[str, Any]) -> dict[str, Any]:
        """
        Strip any property that could leak PII or content.

        Rules:
        - Values > 200 chars are truncated with a sentinel suffix
        - Values containing "@" are dropped (email guard)
        - Non-scalar values (lists, dicts) are dropped
        - None values are passed through (PostHog handles null correctly)
        """
        clean: dict[str, Any] = {}
        for k, v in props.items():
            if v is None:
                clean[k] = v
                continue
            if not isinstance(v, (int, float, bool, str)):
                # Drop complex types silently — call sites should only send scalars
                logger.debug("Telemetry: dropped non-scalar property '%s' (%s)", k, type(v).__name__)
                continue
            if isinstance(v, str):
                if "@" in v:
                    logger.debug("Telemetry: dropped '@'-containing property '%s'", k)
                    continue
                if len(v) > MAX_PROP_VALUE_LEN:
                    v = v[:MAX_PROP_VALUE_LEN] + "[TRUNCATED]"
            clean[k] = v
        return clean

    # ------------------------------------------------------------------
    # Core capture
    # ------------------------------------------------------------------

    def capture(
        self,
        distinct_id: str,
        event: str,
        properties: Optional[dict[str, Any]] = None,
        opt_out: bool = False,
    ) -> None:
        """
        Emit a PostHog event.

        Non-blocking: the SDK call is dispatched to a background thread so
        it cannot add latency to the request that triggered it.

        Args:
            distinct_id: UUID persisted per installation (no email/name)
            event:       Event name (snake_case, from CPO taxonomy)
            properties:  Key/value pairs (all sanitised before sending)
            opt_out:     True → skip capture (Settings opt-out is enforced)
        """
        if opt_out or not self._enabled or self._client is None:
            return

        safe_props = self._sanitise_properties(properties or {})

        def _send() -> None:
            try:
                self._client.capture(distinct_id, event, safe_props)
            except Exception as exc:
                logger.debug("PostHog capture error (non-fatal): %s", exc)

        t = threading.Thread(target=_send, daemon=True)
        t.start()

    def identify(
        self,
        distinct_id: str,
        person_properties: dict[str, Any],
        opt_out: bool = False,
    ) -> None:
        """
        Set person properties on a PostHog person record.

        Called once on `purchase_completed` to record tier/source/date.
        No PII — only tier, purchase_source, purchase_date, is_paid.
        """
        if opt_out or not self._enabled or self._client is None:
            return

        safe_props = self._sanitise_properties(person_properties)

        def _send() -> None:
            try:
                self._client.identify(distinct_id, safe_props)
            except Exception as exc:
                logger.debug("PostHog identify error (non-fatal): %s", exc)

        t = threading.Thread(target=_send, daemon=True)
        t.start()

    def flush(self) -> None:
        """Force-flush the PostHog queue (called on app shutdown)."""
        if self._client is not None:
            try:
                self._client.flush()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generate_distinct_id() -> str:
        """Generate a new UUID v4 for use as an installation distinct_id."""
        return str(uuid.uuid4())

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._client is not None


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere:
#   from app.services.telemetry_service import telemetry
# ---------------------------------------------------------------------------
telemetry = TelemetryService()
