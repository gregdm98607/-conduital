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
    auto_discovery_enabled: bool


class SyncSettingsUpdate(BaseModel):
    """Schema for updating file sync settings"""
    sync_folder_root: Optional[str] = Field(None, max_length=1000)
    watch_directories: Optional[list[str]] = None
    sync_interval: Optional[int] = Field(None, ge=5, le=600)
    conflict_strategy: Optional[str] = Field(None, pattern=r"^(prompt|file_wins|db_wins|merge)$")
    auto_discovery_enabled: Optional[bool] = None

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


def _persist_to_env(updates: dict[str, str]) -> None:
    """Persist key-value pairs to the .env file.

    Updates existing keys in-place. Appends new keys at the end.
    Creates .env if it doesn't exist.

    Thread-safe via _env_write_lock (DEBT-042).
    Values are sanitized to prevent injection (DEBT-043).

    Raises OSError on failure (callers should NOT mutate in-memory
    settings until this succeeds — see DEBT-075).
    """
    env_path = _get_env_file_path()

    with _env_write_lock:
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

    Persist-first: writes to .env before mutating in-memory settings,
    so a disk failure never leaves the singleton in a diverged state.
    """
    env_updates: dict[str, str] = {}
    memory_updates: list[tuple[str, object]] = []

    if update.ai_provider is not None:
        env_updates["AI_PROVIDER"] = update.ai_provider
        memory_updates.append(("AI_PROVIDER", update.ai_provider))

    if update.ai_features_enabled is not None:
        env_updates["AI_FEATURES_ENABLED"] = str(update.ai_features_enabled).lower()
        memory_updates.append(("AI_FEATURES_ENABLED", update.ai_features_enabled))

    if update.ai_model is not None:
        env_updates["AI_MODEL"] = update.ai_model
        memory_updates.append(("AI_MODEL", update.ai_model))

    if update.ai_max_tokens is not None:
        env_updates["AI_MAX_TOKENS"] = str(update.ai_max_tokens)
        memory_updates.append(("AI_MAX_TOKENS", update.ai_max_tokens))

    if update.api_key is not None and update.api_key.strip():
        env_updates["ANTHROPIC_API_KEY"] = update.api_key.strip()
        memory_updates.append(("ANTHROPIC_API_KEY", update.api_key.strip()))

    if update.openai_api_key is not None and update.openai_api_key.strip():
        env_updates["OPENAI_API_KEY"] = update.openai_api_key.strip()
        memory_updates.append(("OPENAI_API_KEY", update.openai_api_key.strip()))

    if update.google_api_key is not None and update.google_api_key.strip():
        env_updates["GOOGLE_API_KEY"] = update.google_api_key.strip()
        memory_updates.append(("GOOGLE_API_KEY", update.google_api_key.strip()))

    # Persist to disk FIRST — only mutate in-memory if this succeeds
    if env_updates:
        try:
            _persist_to_env(env_updates)
        except OSError as e:
            logger.error(f"Failed to persist AI settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to save settings to disk")
        for attr, value in memory_updates:
            setattr(settings, attr, value)

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
    """Update momentum threshold settings.

    Persist-first: writes to .env before mutating in-memory settings.
    """
    env_updates: dict[str, str] = {}
    memory_updates: list[tuple[str, object]] = []

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

    if update.stalled_threshold_days is not None:
        env_updates["MOMENTUM_STALLED_THRESHOLD_DAYS"] = str(update.stalled_threshold_days)
        memory_updates.append(("MOMENTUM_STALLED_THRESHOLD_DAYS", update.stalled_threshold_days))
    if update.at_risk_threshold_days is not None:
        env_updates["MOMENTUM_AT_RISK_THRESHOLD_DAYS"] = str(update.at_risk_threshold_days)
        memory_updates.append(("MOMENTUM_AT_RISK_THRESHOLD_DAYS", update.at_risk_threshold_days))
    if update.activity_decay_days is not None:
        env_updates["MOMENTUM_ACTIVITY_DECAY_DAYS"] = str(update.activity_decay_days)
        memory_updates.append(("MOMENTUM_ACTIVITY_DECAY_DAYS", update.activity_decay_days))
    if update.recalculate_interval is not None:
        env_updates["MOMENTUM_RECALCULATE_INTERVAL"] = str(update.recalculate_interval)
        memory_updates.append(("MOMENTUM_RECALCULATE_INTERVAL", update.recalculate_interval))

    # Persist to disk FIRST — only mutate in-memory if this succeeds
    if env_updates:
        try:
            _persist_to_env(env_updates)
        except OSError as e:
            logger.error(f"Failed to persist momentum settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to save settings to disk")
        for attr, value in memory_updates:
            setattr(settings, attr, value)

    return MomentumSettingsResponse(
        stalled_threshold_days=settings.MOMENTUM_STALLED_THRESHOLD_DAYS,
        at_risk_threshold_days=settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS,
        activity_decay_days=settings.MOMENTUM_ACTIVITY_DECAY_DAYS,
        recalculate_interval=settings.MOMENTUM_RECALCULATE_INTERVAL,
    )


def _apply_auto_discovery(enabled: bool) -> None:
    """Start or stop the folder watcher based on the auto_discovery_enabled setting."""
    if enabled and settings.SECOND_BRAIN_ROOT:
        from app.sync.folder_watcher import get_folder_watcher, start_folder_watcher
        watcher = get_folder_watcher()
        if not watcher.is_running:
            from app.services.auto_discovery_service import (
                on_new_folder_created,
                on_folder_renamed,
                on_folder_moved,
                on_area_created,
                on_area_renamed,
                on_area_moved,
            )
            start_folder_watcher(
                on_folder_created=on_new_folder_created,
                on_folder_renamed=on_folder_renamed,
                on_folder_moved=on_folder_moved,
                on_area_created=on_area_created,
                on_area_renamed=on_area_renamed,
                on_area_moved=on_area_moved,
            )
            logger.info("Auto-discovery started via Settings toggle")
    else:
        from app.sync.folder_watcher import get_folder_watcher
        watcher = get_folder_watcher()
        if watcher.is_running:
            from app.sync.folder_watcher import stop_folder_watcher
            stop_folder_watcher()
            logger.info("Auto-discovery stopped via Settings toggle")


@router.get("/sync", response_model=SyncSettingsResponse)
def get_sync_settings():
    """Get current file sync settings"""
    return SyncSettingsResponse(
        sync_folder_root=settings.SECOND_BRAIN_ROOT,
        watch_directories=settings.watch_directories,
        sync_interval=settings.SYNC_INTERVAL,
        conflict_strategy=settings.CONFLICT_STRATEGY,
        auto_discovery_enabled=settings.AUTO_DISCOVERY_ENABLED,
    )


@router.put("/sync", response_model=SyncSettingsResponse)
def update_sync_settings(update: SyncSettingsUpdate):
    """Update file sync settings.

    Persist-first: writes to .env before mutating in-memory settings.
    """
    env_updates: dict[str, str] = {}
    memory_updates: list[tuple[str, object]] = []

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
            env_updates["SECOND_BRAIN_ROOT"] = str(resolved)
            memory_updates.append(("SECOND_BRAIN_ROOT", str(resolved)))
        else:
            env_updates["SECOND_BRAIN_ROOT"] = ""
            memory_updates.append(("SECOND_BRAIN_ROOT", None))

    if update.watch_directories is not None:
        cleaned = [d.strip() for d in update.watch_directories if d.strip()]
        env_updates["WATCH_DIRECTORIES"] = ",".join(cleaned)
        memory_updates.append(("WATCH_DIRECTORIES", ",".join(cleaned)))

    if update.sync_interval is not None:
        env_updates["SYNC_INTERVAL"] = str(update.sync_interval)
        memory_updates.append(("SYNC_INTERVAL", update.sync_interval))

    if update.conflict_strategy is not None:
        env_updates["CONFLICT_STRATEGY"] = update.conflict_strategy
        memory_updates.append(("CONFLICT_STRATEGY", update.conflict_strategy))

    if update.auto_discovery_enabled is not None:
        env_updates["AUTO_DISCOVERY_ENABLED"] = str(update.auto_discovery_enabled).lower()
        memory_updates.append(("AUTO_DISCOVERY_ENABLED", update.auto_discovery_enabled))

    # Persist to disk FIRST — only mutate in-memory if this succeeds
    if env_updates:
        try:
            _persist_to_env(env_updates)
        except OSError as e:
            logger.error(f"Failed to persist sync settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to save settings to disk")
        for attr, value in memory_updates:
            setattr(settings, attr, value)

    # Start/stop folder watcher based on new auto_discovery_enabled value
    if update.auto_discovery_enabled is not None:
        _apply_auto_discovery(settings.AUTO_DISCOVERY_ENABLED)

    return get_sync_settings()
