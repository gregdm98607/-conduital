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
    mistral_key_configured: bool = False
    mistral_key_masked: Optional[str] = None
    groq_key_configured: bool = False
    groq_key_masked: Optional[str] = None
    deepseek_key_configured: bool = False
    deepseek_key_masked: Optional[str] = None
    ollama_key_configured: bool = False
    ollama_key_masked: Optional[str] = None
    ollama_base_url: Optional[str] = "http://localhost:11434/v1"
    openai_compatible_key_configured: bool = False
    openai_compatible_key_masked: Optional[str] = None
    openai_compatible_base_url: Optional[str] = None
    available_providers: list[str] = [
        "anthropic", "openai", "google", "mistral", "groq",
        "deepseek", "ollama", "openai_compatible",
    ]
    provider_models: dict[str, list[ProviderModelInfo]] = {}


class AISettingsUpdate(BaseModel):
    """AI settings update request"""
    ai_provider: Optional[str] = Field(
        None,
        pattern=r"^(anthropic|openai|google|mistral|groq|deepseek|ollama|openai_compatible)$",
    )
    ai_features_enabled: Optional[bool] = None
    ai_model: Optional[str] = Field(None, max_length=100)
    ai_max_tokens: Optional[int] = Field(None, ge=100, le=8000)
    api_key: Optional[str] = Field(None, max_length=500)
    openai_api_key: Optional[str] = Field(None, max_length=500)
    google_api_key: Optional[str] = Field(None, max_length=500)
    mistral_api_key: Optional[str] = Field(None, max_length=500)
    groq_api_key: Optional[str] = Field(None, max_length=500)
    deepseek_api_key: Optional[str] = Field(None, max_length=500)
    ollama_api_key: Optional[str] = Field(None, max_length=500)
    ollama_base_url: Optional[str] = Field(None, max_length=500)
    openai_compatible_api_key: Optional[str] = Field(None, max_length=500)
    openai_compatible_base_url: Optional[str] = Field(None, max_length=500)


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
    from app.services.ai_service import PROVIDER_MODELS, VALID_PROVIDERS

    anthropic_configured, anthropic_masked = _mask_key(settings.ANTHROPIC_API_KEY)
    openai_configured, openai_masked = _mask_key(settings.OPENAI_API_KEY)
    google_configured, google_masked = _mask_key(settings.GOOGLE_API_KEY)
    mistral_configured, mistral_masked = _mask_key(settings.MISTRAL_API_KEY)
    groq_configured, groq_masked = _mask_key(settings.GROQ_API_KEY)
    deepseek_configured, deepseek_masked = _mask_key(settings.DEEPSEEK_API_KEY)
    ollama_configured, ollama_masked = _mask_key(settings.OLLAMA_API_KEY)
    compat_configured, compat_masked = _mask_key(settings.OPENAI_COMPATIBLE_API_KEY)

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
        mistral_key_configured=mistral_configured,
        mistral_key_masked=mistral_masked,
        groq_key_configured=groq_configured,
        groq_key_masked=groq_masked,
        deepseek_key_configured=deepseek_configured,
        deepseek_key_masked=deepseek_masked,
        ollama_key_configured=ollama_configured,
        ollama_key_masked=ollama_masked,
        ollama_base_url=settings.OLLAMA_BASE_URL,
        openai_compatible_key_configured=compat_configured,
        openai_compatible_key_masked=compat_masked,
        openai_compatible_base_url=settings.OPENAI_COMPATIBLE_BASE_URL,
        available_providers=VALID_PROVIDERS,
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

    if update.mistral_api_key is not None and update.mistral_api_key.strip():
        env_updates["MISTRAL_API_KEY"] = update.mistral_api_key.strip()
        memory_updates.append(("MISTRAL_API_KEY", update.mistral_api_key.strip()))

    if update.groq_api_key is not None and update.groq_api_key.strip():
        env_updates["GROQ_API_KEY"] = update.groq_api_key.strip()
        memory_updates.append(("GROQ_API_KEY", update.groq_api_key.strip()))

    if update.deepseek_api_key is not None and update.deepseek_api_key.strip():
        env_updates["DEEPSEEK_API_KEY"] = update.deepseek_api_key.strip()
        memory_updates.append(("DEEPSEEK_API_KEY", update.deepseek_api_key.strip()))

    if update.ollama_api_key is not None and update.ollama_api_key.strip():
        env_updates["OLLAMA_API_KEY"] = update.ollama_api_key.strip()
        memory_updates.append(("OLLAMA_API_KEY", update.ollama_api_key.strip()))

    if update.ollama_base_url is not None and update.ollama_base_url.strip():
        env_updates["OLLAMA_BASE_URL"] = update.ollama_base_url.strip()
        memory_updates.append(("OLLAMA_BASE_URL", update.ollama_base_url.strip()))

    if update.openai_compatible_api_key is not None and update.openai_compatible_api_key.strip():
        env_updates["OPENAI_COMPATIBLE_API_KEY"] = update.openai_compatible_api_key.strip()
        memory_updates.append(("OPENAI_COMPATIBLE_API_KEY", update.openai_compatible_api_key.strip()))

    if update.openai_compatible_base_url is not None and update.openai_compatible_base_url.strip():
        env_updates["OPENAI_COMPATIBLE_BASE_URL"] = update.openai_compatible_base_url.strip()
        memory_updates.append(("OPENAI_COMPATIBLE_BASE_URL", update.openai_compatible_base_url.strip()))

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
            "mistral": "openai",
            "groq": "openai",
            "deepseek": "openai",
            "ollama": "openai",
            "openai_compatible": "openai",
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


# =========================================================================
# Storage Settings (Phase 4 — Data Storage UI)
# =========================================================================


class StorageSettingsResponse(BaseModel):
    """Current data-storage configuration."""
    storage_provider: str
    storage_path: Optional[str] = None
    storage_mode: str
    sync_health: str  # "healthy", "degraded", "not_configured"
    entity_counts: dict[str, int] = {}


class StorageSettingsUpdate(BaseModel):
    """Schema for updating storage settings."""
    storage_provider: Optional[str] = Field(
        None, pattern=r"^(local_folder)$",
    )
    storage_path: Optional[str] = Field(None, max_length=2000)
    storage_mode: Optional[str] = Field(
        None, pattern=r"^(legacy|storage_first)$",
    )


class StorageTestResponse(BaseModel):
    """Response from storage folder validation."""
    valid: bool
    exists: bool
    is_directory: bool
    is_writable: bool
    path: str
    message: str


class StorageRebuildResponse(BaseModel):
    """Response from cache rebuild."""
    success: bool
    message: str
    stats: dict = {}


class StorageMigrationRequest(BaseModel):
    """Request to export existing SQLite data to a storage folder."""
    action: str = Field(
        ..., pattern=r"^(export_to_folder|import_from_folder|start_fresh)$",
    )
    folder_path: str = Field(..., max_length=2000)


class StorageMigrationResponse(BaseModel):
    """Response from migration action."""
    success: bool
    message: str
    stats: dict = {}


def _get_entity_counts() -> dict[str, int]:
    """Count entities in the current storage folder."""
    try:
        from app.storage.factory import get_storage_provider
        provider = get_storage_provider()
        counts: dict[str, int] = {}
        for entity_type in ["project", "task", "area", "goal", "vision"]:
            try:
                entities = provider.list_entities(entity_type)
                counts[entity_type + "s"] = len(entities)
            except (ValueError, Exception):
                pass
        return counts
    except Exception:
        return {}


def _check_sync_health() -> str:
    """Check overall sync/storage health."""
    storage_path = getattr(settings, "STORAGE_PATH", None) or settings.SECOND_BRAIN_ROOT
    if not storage_path:
        return "not_configured"
    p = Path(storage_path)
    if not p.exists() or not p.is_dir():
        return "degraded"
    # Quick write test
    try:
        test_file = p / ".conduital_health_check"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink()
        return "healthy"
    except Exception:
        return "degraded"


@router.get("/storage", response_model=StorageSettingsResponse)
def get_storage_settings():
    """Get current data storage configuration."""
    storage_path = getattr(settings, "STORAGE_PATH", None) or settings.SECOND_BRAIN_ROOT
    health = _check_sync_health()
    counts = _get_entity_counts() if health == "healthy" else {}

    return StorageSettingsResponse(
        storage_provider=getattr(settings, "STORAGE_PROVIDER", "local_folder"),
        storage_path=storage_path,
        storage_mode=getattr(settings, "STORAGE_MODE", "legacy"),
        sync_health=health,
        entity_counts=counts,
    )


@router.put("/storage", response_model=StorageSettingsResponse)
def update_storage_settings(update: StorageSettingsUpdate):
    """Update data storage configuration.

    Persist-first: writes to .env before mutating in-memory settings.
    """
    env_updates: dict[str, str] = {}
    memory_updates: list[tuple[str, object]] = []

    if update.storage_provider is not None:
        env_updates["STORAGE_PROVIDER"] = update.storage_provider
        memory_updates.append(("STORAGE_PROVIDER", update.storage_provider))

    if update.storage_path is not None:
        path_value = update.storage_path.strip()
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
            env_updates["STORAGE_PATH"] = str(resolved)
            memory_updates.append(("STORAGE_PATH", str(resolved)))
            # Also update SECOND_BRAIN_ROOT for backward compat
            env_updates["SECOND_BRAIN_ROOT"] = str(resolved)
            memory_updates.append(("SECOND_BRAIN_ROOT", str(resolved)))
        else:
            env_updates["STORAGE_PATH"] = ""
            memory_updates.append(("STORAGE_PATH", None))

    if update.storage_mode is not None:
        env_updates["STORAGE_MODE"] = update.storage_mode
        memory_updates.append(("STORAGE_MODE", update.storage_mode))

    if env_updates:
        try:
            _persist_to_env(env_updates)
        except OSError as e:
            logger.error(f"Failed to persist storage settings: {e}")
            raise HTTPException(status_code=500, detail="Failed to save settings to disk")
        for attr, value in memory_updates:
            setattr(settings, attr, value)
        # Reset the cached storage provider so it picks up new settings
        from app.storage.factory import reset_storage_provider
        reset_storage_provider()

    return get_storage_settings()


@router.post("/storage/test", response_model=StorageTestResponse)
def test_storage_folder(path: str):
    """Validate a storage folder path exists, is a directory, and is writable."""
    folder = Path(path)
    exists = folder.exists()
    is_dir = folder.is_dir() if exists else False
    is_writable = False
    message = ""

    if not exists:
        message = "Path does not exist"
    elif not is_dir:
        message = "Path is not a directory"
    else:
        try:
            test_file = folder / ".conduital_write_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
            is_writable = True
            message = "Folder is valid and writable"
        except PermissionError:
            message = "Folder exists but is not writable (permission denied)"
        except Exception as e:
            message = f"Folder exists but write test failed: {e}"

    return StorageTestResponse(
        valid=is_dir and is_writable,
        exists=exists,
        is_directory=is_dir,
        is_writable=is_writable,
        path=str(folder.resolve()) if exists else path,
        message=message,
    )


@router.post("/storage/rebuild", response_model=StorageRebuildResponse)
def rebuild_cache():
    """Force rebuild the SQLite cache from markdown files in the storage folder."""
    storage_path = getattr(settings, "STORAGE_PATH", None) or settings.SECOND_BRAIN_ROOT
    if not storage_path:
        return StorageRebuildResponse(
            success=False,
            message="No storage folder configured. Set a storage path first.",
        )

    try:
        from app.core.database import get_db
        from app.services.storage_service import StorageService
        from app.storage.factory import reset_storage_provider

        # Reset provider to pick up any config changes
        reset_storage_provider()

        db_gen = get_db()
        db = next(db_gen)
        try:
            stats = StorageService.rebuild_cache(db)
            return StorageRebuildResponse(
                success=True,
                message=(
                    f"Cache rebuilt: {stats.get('scanned', 0)} files scanned, "
                    f"{stats.get('created', 0)} created, "
                    f"{stats.get('updated', 0)} updated, "
                    f"{stats.get('errors', 0)} errors."
                ),
                stats=stats,
            )
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
    except Exception as e:
        logger.exception("Cache rebuild failed")
        return StorageRebuildResponse(
            success=False,
            message=f"Cache rebuild failed: {e}",
        )


@router.post("/storage/migrate", response_model=StorageMigrationResponse)
def migrate_storage(request: StorageMigrationRequest):
    """Execute a migration action: export to folder, import from folder, or start fresh."""
    folder = Path(request.folder_path)

    if request.action == "start_fresh":
        # Just validate the folder exists / create it
        try:
            folder.mkdir(parents=True, exist_ok=True)
            return StorageMigrationResponse(
                success=True,
                message=f"Fresh start: folder ready at {folder}",
            )
        except Exception as e:
            return StorageMigrationResponse(
                success=False,
                message=f"Failed to create folder: {e}",
            )

    if request.action == "export_to_folder":
        # Export all SQLite data as markdown files to the chosen folder
        try:
            from app.core.database import get_db
            from app.storage.local_folder import LocalFolderProvider

            folder.mkdir(parents=True, exist_ok=True)
            provider = LocalFolderProvider(root_path=folder)

            db_gen = get_db()
            db = next(db_gen)
            try:
                from app.models.project import Project as ProjectModel
                from app.models.task import Task as TaskModel
                from sqlalchemy import select

                projects = db.execute(
                    select(ProjectModel).where(ProjectModel.deleted_at.is_(None))
                ).scalars().all()

                exported = 0
                errors = 0
                for project in projects:
                    try:
                        tasks = db.execute(
                            select(TaskModel).where(
                                TaskModel.project_id == project.id,
                                TaskModel.deleted_at.is_(None),
                            )
                        ).scalars().all()

                        task_dicts = [
                            {
                                "title": t.title,
                                "checked": t.status == "completed",
                                "marker": t.file_marker,
                                "file_marker": t.file_marker,
                                "task_type": t.task_type,
                            }
                            for t in tasks
                        ]

                        data = {
                            "title": project.title,
                            "description": project.description,
                            "status": project.status,
                            "priority": project.priority,
                            "momentum_score": project.momentum_score or 0.0,
                            "metadata": {
                                "tracker_id": project.id,
                                "project_status": project.status,
                                "priority": project.priority,
                                "momentum_score": project.momentum_score or 0.0,
                                "title": project.title,
                                "description": project.description,
                            },
                            "tasks": task_dicts,
                        }
                        provider.write_entity("project", "", data)
                        exported += 1
                    except Exception as exc:
                        logger.warning("Failed to export project '%s': %s", project.title, exc)
                        errors += 1

                return StorageMigrationResponse(
                    success=True,
                    message=f"Exported {exported} projects to {folder} ({errors} errors)",
                    stats={"exported": exported, "errors": errors},
                )
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass
        except Exception as e:
            logger.exception("Export to folder failed")
            return StorageMigrationResponse(
                success=False,
                message=f"Export failed: {e}",
            )

    if request.action == "import_from_folder":
        # Import markdown files from the folder into SQLite
        try:
            if not folder.is_dir():
                return StorageMigrationResponse(
                    success=False,
                    message=f"Folder does not exist: {folder}",
                )

            from app.core.database import get_db
            from app.services.storage_service import StorageService
            from app.storage.factory import create_storage_provider

            # Temporarily create a provider pointing at the chosen folder
            provider = create_storage_provider(
                provider_type="local_folder",
                storage_path=str(folder),
            )

            db_gen = get_db()
            db = next(db_gen)
            try:
                # Use the existing rebuild mechanism
                entities = provider.list_entities("project")
                created = 0
                errors = 0
                for entity_summary in entities:
                    try:
                        full_data = provider.read_entity("project", entity_summary["entity_id"])
                        StorageService._upsert_project_from_storage(
                            db, entity_summary["entity_id"], full_data, provider=provider
                        )
                        created += 1
                    except Exception as exc:
                        logger.warning("Failed to import %s: %s", entity_summary["entity_id"], exc)
                        errors += 1
                db.commit()

                return StorageMigrationResponse(
                    success=True,
                    message=f"Imported {created} projects from {folder} ({errors} errors)",
                    stats={"imported": created, "errors": errors},
                )
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass
        except Exception as e:
            logger.exception("Import from folder failed")
            return StorageMigrationResponse(
                success=False,
                message=f"Import failed: {e}",
            )

    return StorageMigrationResponse(
        success=False,
        message=f"Unknown action: {request.action}",
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
