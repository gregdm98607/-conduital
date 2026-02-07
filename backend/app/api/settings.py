"""
Settings API endpoints

Provides read/write access to runtime-configurable settings,
including AI configuration. Settings are persisted to .env file.
"""

import re
import logging
import threading
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lock for concurrent .env file writes (DEBT-042)
_env_write_lock = threading.Lock()

router = APIRouter()


class ProviderModelInfo(BaseModel):
    """Model info for a provider."""
    id: str
    name: str


class AISettingsResponse(BaseModel):
    """AI settings response (API keys masked)"""
    ai_provider: str
    ai_features_enabled: bool
    ai_model: str
    ai_max_tokens: int
    api_key_configured: bool
    api_key_masked: Optional[str] = None
    openai_key_configured: bool = False
    openai_key_masked: Optional[str] = None
    google_key_configured: bool = False
    google_key_masked: Optional[str] = None
    available_providers: list[str] = ["anthropic", "openai", "google"]
    provider_models: dict[str, list[ProviderModelInfo]] = {}


class AISettingsUpdate(BaseModel):
    """AI settings update request"""
    ai_provider: Optional[str] = Field(None, pattern=r"^(anthropic|openai|google)$")
    ai_features_enabled: Optional[bool] = None
    ai_model: Optional[str] = Field(None, max_length=100)
    ai_max_tokens: Optional[int] = Field(None, ge=100, le=8000)
    api_key: Optional[str] = Field(None, max_length=500)
    openai_api_key: Optional[str] = Field(None, max_length=500)
    google_api_key: Optional[str] = Field(None, max_length=500)


class AITestResponse(BaseModel):
    """Response from AI connection test"""
    success: bool
    message: str
    model: Optional[str] = None


class MomentumSettingsResponse(BaseModel):
    """Momentum threshold settings"""
    stalled_threshold_days: int
    at_risk_threshold_days: int
    activity_decay_days: int
    recalculate_interval: int


def _mask_key(key: Optional[str]) -> tuple[bool, Optional[str]]:
    """Mask an API key. Returns (is_configured, masked_value)."""
    if not key:
        return False, None
    if len(key) > 8:
        return True, f"...{key[-4:]}"
    return True, "***"


def _get_env_file_path() -> Path:
    """Get the path to the .env file (next to the backend app)."""
    current = Path(__file__).resolve()
    backend_dir = current.parent.parent.parent  # backend/
    return backend_dir / ".env"


def _sanitize_env_value(value: str) -> str:
    """Sanitize a value for safe .env file storage (DEBT-043).

    Strips newlines and carriage returns to prevent env var injection.
    Quotes the value if it contains spaces or special characters.
    """
    # Strip newlines/carriage returns to prevent injection
    sanitized = value.replace("\n", "").replace("\r", "")
    # Quote if contains spaces, #, or quotes
    if " " in sanitized or "#" in sanitized or "'" in sanitized or '"' in sanitized:
        # Escape existing double quotes and wrap
        sanitized = '"' + sanitized.replace('"', '\\"') + '"'
    return sanitized


def _persist_to_env(updates: dict[str, str]) -> bool:
    """Persist key-value pairs to the .env file.

    Updates existing keys in-place. Appends new keys at the end.
    Creates .env if it doesn't exist.

    Thread-safe via _env_write_lock (DEBT-042).
    Values are sanitized to prevent injection (DEBT-043).

    Returns True on success, False on failure.
    """
    env_path = _get_env_file_path()

    with _env_write_lock:
        try:
            if env_path.exists():
                content = env_path.read_text(encoding="utf-8")
            else:
                content = ""

            for key, value in updates.items():
                sanitized_value = _sanitize_env_value(value)
                pattern = rf"^{re.escape(key)}\s*=.*$"
                replacement = f"{key}={sanitized_value}"
                if re.search(pattern, content, re.MULTILINE):
                    content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                else:
                    if content and not content.endswith("\n"):
                        content += "\n"
                    content += f"{replacement}\n"

            env_path.write_text(content, encoding="utf-8")
            logger.info(f"Persisted {len(updates)} setting(s) to {env_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to persist settings to .env: {e}")
            return False


@router.get("/ai", response_model=AISettingsResponse)
def get_ai_settings():
    """Get current AI settings (API keys masked)"""
    from app.services.ai_service import PROVIDER_MODELS

    anthropic_configured, anthropic_masked = _mask_key(settings.ANTHROPIC_API_KEY)
    openai_configured, openai_masked = _mask_key(settings.OPENAI_API_KEY)
    google_configured, google_masked = _mask_key(settings.GOOGLE_API_KEY)

    return AISettingsResponse(
        ai_provider=settings.AI_PROVIDER,
        ai_features_enabled=settings.AI_FEATURES_ENABLED,
        ai_model=settings.AI_MODEL,
        ai_max_tokens=settings.AI_MAX_TOKENS,
        api_key_configured=anthropic_configured,
        api_key_masked=anthropic_masked,
        openai_key_configured=openai_configured,
        openai_key_masked=openai_masked,
        google_key_configured=google_configured,
        google_key_masked=google_masked,
        available_providers=["anthropic", "openai", "google"],
        provider_models={
            provider: [ProviderModelInfo(**m) for m in models]
            for provider, models in PROVIDER_MODELS.items()
        },
    )


@router.put("/ai", response_model=AISettingsResponse)
def update_ai_settings(update: AISettingsUpdate):
    """Update AI settings and persist to .env file.

    Changes are applied immediately to runtime AND written to .env
    so they survive server restarts.
    """
    env_updates: dict[str, str] = {}

    if update.ai_provider is not None:
        settings.AI_PROVIDER = update.ai_provider
        env_updates["AI_PROVIDER"] = update.ai_provider

    if update.ai_features_enabled is not None:
        settings.AI_FEATURES_ENABLED = update.ai_features_enabled
        env_updates["AI_FEATURES_ENABLED"] = str(update.ai_features_enabled).lower()

    if update.ai_model is not None:
        settings.AI_MODEL = update.ai_model
        env_updates["AI_MODEL"] = update.ai_model

    if update.ai_max_tokens is not None:
        settings.AI_MAX_TOKENS = update.ai_max_tokens
        env_updates["AI_MAX_TOKENS"] = str(update.ai_max_tokens)

    # Anthropic key
    if update.api_key is not None and update.api_key.strip():
        settings.ANTHROPIC_API_KEY = update.api_key.strip()
        env_updates["ANTHROPIC_API_KEY"] = update.api_key.strip()

    # OpenAI key
    if update.openai_api_key is not None and update.openai_api_key.strip():
        settings.OPENAI_API_KEY = update.openai_api_key.strip()
        env_updates["OPENAI_API_KEY"] = update.openai_api_key.strip()

    # Google key
    if update.google_api_key is not None and update.google_api_key.strip():
        settings.GOOGLE_API_KEY = update.google_api_key.strip()
        env_updates["GOOGLE_API_KEY"] = update.google_api_key.strip()

    # Persist all changes to .env
    if env_updates:
        _persist_to_env(env_updates)

    return get_ai_settings()


@router.post("/ai/test", response_model=AITestResponse)
def test_ai_connection():
    """Test the AI connection with current settings.

    Makes a minimal API call to verify the key is valid
    and the model is accessible. Uses the currently selected provider.
    """
    from app.services.ai_service import create_provider, get_api_key_for_provider

    provider_name = settings.AI_PROVIDER
    api_key = get_api_key_for_provider(provider_name)

    if not api_key:
        return AITestResponse(
            success=False,
            message=f"No API key configured for {provider_name}",
        )

    try:
        provider = create_provider(provider_name, api_key, settings.AI_MODEL)
        result = provider.test_connection()
        return AITestResponse(**result)
    except ImportError as e:
        package_map = {
            "anthropic": "anthropic",
            "openai": "openai",
            "google": "google-generativeai",
        }
        pkg = package_map.get(provider_name, provider_name)
        return AITestResponse(
            success=False,
            message=f"Package not installed: pip install {pkg}",
        )
    except Exception as e:
        return AITestResponse(success=False, message=str(e))


@router.get("/momentum", response_model=MomentumSettingsResponse)
def get_momentum_settings():
    """Get current momentum threshold settings"""
    return MomentumSettingsResponse(
        stalled_threshold_days=settings.MOMENTUM_STALLED_THRESHOLD_DAYS,
        at_risk_threshold_days=settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS,
        activity_decay_days=settings.MOMENTUM_ACTIVITY_DECAY_DAYS,
        recalculate_interval=settings.MOMENTUM_RECALCULATE_INTERVAL,
    )
