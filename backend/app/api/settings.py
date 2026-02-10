"""
Settings API endpoints

Provides read/write access to runtime-configurable settings,
including AI configuration. Settings are persisted to .env file.
"""

import re
import logging
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
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


class SyncSettingsResponse(BaseModel):
    """File sync settings response"""
    sync_folder_root: Optional[str] = None
    watch_directories: list[str]
    sync_interval: int
    conflict_strategy: str


class SyncSettingsUpdate(BaseModel):
    """Schema for updating file sync settings"""
    sync_folder_root: Optional[str] = Field(None, max_length=1000)
    watch_directories: Optional[list[str]] = None
    sync_interval: Optional[int] = Field(None, ge=5, le=600)
    conflict_strategy: Optional[str] = Field(None, pattern=r"^(prompt|file_wins|db_wins|merge)$")

    @model_validator(mode="after")
    def validate_watch_dirs(self) -> "SyncSettingsUpdate":
        if self.watch_directories is not None:
            if len(self.watch_directories) == 0:
                raise ValueError("At least one watch directory is required")
            for d in self.watch_directories:
                if not d.strip():
                    raise ValueError("Watch directory names cannot be empty")
        return self


class MomentumSettingsResponse(BaseModel):
    """Momentum threshold settings"""
    stalled_threshold_days: int
    at_risk_threshold_days: int
    activity_decay_days: int
    recalculate_interval: int


class MomentumSettingsUpdate(BaseModel):
    """Schema for updating momentum settings"""
    stalled_threshold_days: Optional[int] = Field(None, ge=1, le=90)
    at_risk_threshold_days: Optional[int] = Field(None, ge=1, le=90)
    activity_decay_days: Optional[int] = Field(None, ge=7, le=365)
    recalculate_interval: Optional[int] = Field(None, ge=60, le=86400)

    @model_validator(mode="after")
    def validate_threshold_relationship(self) -> "MomentumSettingsUpdate":
        """When both thresholds are provided in the same request, validate their relationship."""
        if self.stalled_threshold_days is not None and self.at_risk_threshold_days is not None:
            if self.at_risk_threshold_days >= self.stalled_threshold_days:
                raise ValueError(
                    f"At-risk threshold ({self.at_risk_threshold_days} days) "
                    f"must be less than stalled threshold ({self.stalled_threshold_days} days)"
                )
        return self


def _mask_key(key: Optional[str]) -> tuple[bool, Optional[str]]:
    """Mask an API key. Returns (is_configured, masked_value)."""
    if not key:
        return False, None
    if len(key) > 8:
        return True, f"...{key[-4:]}"
    return True, "***"


def _get_env_file_path() -> Path:
    """Get the path to the config/env file (resolved by paths module)."""
    from app.core.paths import get_config_path
    return get_config_path()


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


@router.put("/momentum", response_model=MomentumSettingsResponse)
def update_momentum_settings(update: MomentumSettingsUpdate):
    """Update momentum threshold settings and persist to .env"""
    env_updates: dict[str, str] = {}

    # Compute effective values (new value if provided, else current setting)
    effective_stalled = (
        update.stalled_threshold_days
        if update.stalled_threshold_days is not None
        else settings.MOMENTUM_STALLED_THRESHOLD_DAYS
    )
    effective_at_risk = (
        update.at_risk_threshold_days
        if update.at_risk_threshold_days is not None
        else settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS
    )

    # Validate relationship: at_risk must be strictly less than stalled
    if effective_at_risk >= effective_stalled:
        raise HTTPException(
            status_code=422,
            detail=(
                f"At-risk threshold ({effective_at_risk} days) must be less than "
                f"stalled threshold ({effective_stalled} days)"
            ),
        )

    # Apply mutations only after validation passes
    if update.stalled_threshold_days is not None:
        settings.MOMENTUM_STALLED_THRESHOLD_DAYS = update.stalled_threshold_days
        env_updates["MOMENTUM_STALLED_THRESHOLD_DAYS"] = str(update.stalled_threshold_days)
    if update.at_risk_threshold_days is not None:
        settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS = update.at_risk_threshold_days
        env_updates["MOMENTUM_AT_RISK_THRESHOLD_DAYS"] = str(update.at_risk_threshold_days)
    if update.activity_decay_days is not None:
        settings.MOMENTUM_ACTIVITY_DECAY_DAYS = update.activity_decay_days
        env_updates["MOMENTUM_ACTIVITY_DECAY_DAYS"] = str(update.activity_decay_days)
    if update.recalculate_interval is not None:
        settings.MOMENTUM_RECALCULATE_INTERVAL = update.recalculate_interval
        env_updates["MOMENTUM_RECALCULATE_INTERVAL"] = str(update.recalculate_interval)

    if env_updates:
        _persist_to_env(env_updates)

    return MomentumSettingsResponse(
        stalled_threshold_days=settings.MOMENTUM_STALLED_THRESHOLD_DAYS,
        at_risk_threshold_days=settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS,
        activity_decay_days=settings.MOMENTUM_ACTIVITY_DECAY_DAYS,
        recalculate_interval=settings.MOMENTUM_RECALCULATE_INTERVAL,
    )


@router.get("/sync", response_model=SyncSettingsResponse)
def get_sync_settings():
    """Get current file sync settings"""
    return SyncSettingsResponse(
        sync_folder_root=settings.SECOND_BRAIN_ROOT,
        watch_directories=settings.WATCH_DIRECTORIES,
        sync_interval=settings.SYNC_INTERVAL,
        conflict_strategy=settings.CONFLICT_STRATEGY,
    )


@router.put("/sync", response_model=SyncSettingsResponse)
def update_sync_settings(update: SyncSettingsUpdate):
    """Update file sync settings and persist to .env"""
    env_updates: dict[str, str] = {}

    if update.sync_folder_root is not None:
        path_value = update.sync_folder_root.strip()
        if path_value:
            resolved = Path(path_value).resolve()
            if not resolved.exists():
                raise HTTPException(
                    status_code=422,
                    detail=f"Path does not exist: {path_value}",
                )
            if not resolved.is_dir():
                raise HTTPException(
                    status_code=422,
                    detail=f"Path is not a directory: {path_value}",
                )
            settings.SECOND_BRAIN_ROOT = str(resolved)
            env_updates["SECOND_BRAIN_ROOT"] = str(resolved)
        else:
            settings.SECOND_BRAIN_ROOT = None
            env_updates["SECOND_BRAIN_ROOT"] = ""

    if update.watch_directories is not None:
        cleaned = [d.strip() for d in update.watch_directories if d.strip()]
        settings.WATCH_DIRECTORIES = cleaned
        env_updates["WATCH_DIRECTORIES"] = ",".join(cleaned)

    if update.sync_interval is not None:
        settings.SYNC_INTERVAL = update.sync_interval
        env_updates["SYNC_INTERVAL"] = str(update.sync_interval)

    if update.conflict_strategy is not None:
        settings.CONFLICT_STRATEGY = update.conflict_strategy
        env_updates["CONFLICT_STRATEGY"] = update.conflict_strategy

    if env_updates:
        _persist_to_env(env_updates)

    return get_sync_settings()
