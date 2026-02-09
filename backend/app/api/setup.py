"""
First-run setup wizard API endpoints.

Provides status check, path validation, and configuration persistence
for the first-run setup experience.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.paths import (
    get_config_path,
    get_data_dir,
    is_first_run,
    is_packaged,
    check_legacy_migration,
)
from app.api.settings import _persist_to_env

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================


class SetupStatus(BaseModel):
    """Response from setup status check."""
    setup_complete: bool
    is_first_run: bool
    is_packaged: bool
    data_directory: str
    config_path: str
    legacy_migration: dict
    current_settings: dict


class SetupRequest(BaseModel):
    """Request to complete first-run setup."""
    sync_folder: Optional[str] = Field(None, description="Path to sync folder")
    anthropic_api_key: Optional[str] = Field(None, max_length=500)
    ai_features_enabled: bool = False
    migrate_legacy_data: bool = False


class SetupResponse(BaseModel):
    """Response after completing setup."""
    success: bool
    message: str
    data_directory: str


class PathValidation(BaseModel):
    """Response from path validation."""
    valid: bool
    exists: bool
    is_directory: bool
    path: str


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/status", response_model=SetupStatus)
def get_setup_status():
    """Check if first-run setup is needed."""
    data_dir = get_data_dir()

    return SetupStatus(
        setup_complete=not is_first_run(),
        is_first_run=is_first_run(),
        is_packaged=is_packaged(),
        data_directory=str(data_dir) if data_dir else "development mode",
        config_path=str(get_config_path()),
        legacy_migration=check_legacy_migration(),
        current_settings={
            "sync_folder_configured": bool(settings.SECOND_BRAIN_ROOT),
            "sync_folder": settings.SECOND_BRAIN_ROOT or "",
            "ai_key_configured": bool(settings.ANTHROPIC_API_KEY),
            "ai_features_enabled": settings.AI_FEATURES_ENABLED,
            "database_path": settings.DATABASE_PATH,
        },
    )


@router.post("/complete", response_model=SetupResponse)
def complete_setup(request: SetupRequest):
    """Save first-run configuration and mark setup as complete."""
    data_dir = get_data_dir()
    data_dir_str = str(data_dir) if data_dir else "development mode"
    env_updates: dict[str, str] = {}

    # Validate sync folder if provided
    if request.sync_folder and request.sync_folder.strip():
        folder = Path(request.sync_folder.strip())
        if not folder.is_dir():
            return SetupResponse(
                success=False,
                message=f"Sync folder does not exist: {request.sync_folder}",
                data_directory=data_dir_str,
            )
        settings.SECOND_BRAIN_ROOT = str(folder)
        env_updates["SECOND_BRAIN_ROOT"] = str(folder)
        logger.info(f"Setup: sync folder set to {folder}")

    # AI API key
    if request.anthropic_api_key and request.anthropic_api_key.strip():
        key = request.anthropic_api_key.strip()
        settings.ANTHROPIC_API_KEY = key
        env_updates["ANTHROPIC_API_KEY"] = key
        logger.info("Setup: Anthropic API key configured")

    # AI features toggle
    settings.AI_FEATURES_ENABLED = request.ai_features_enabled
    env_updates["AI_FEATURES_ENABLED"] = str(request.ai_features_enabled).lower()

    # Handle legacy data migration
    if request.migrate_legacy_data:
        migration = check_legacy_migration()
        if migration["needs_migration"]:
            try:
                shutil.copy2(migration["legacy_path"], migration["target_path"])
                logger.info(
                    f"Setup: migrated database from {migration['legacy_path']} "
                    f"to {migration['target_path']}"
                )
            except Exception as e:
                logger.error(f"Setup: migration failed: {e}")
                return SetupResponse(
                    success=False,
                    message=f"Failed to migrate database: {e}",
                    data_directory=data_dir_str,
                )

    # Mark setup as complete
    env_updates["SETUP_COMPLETE"] = "true"
    settings.SETUP_COMPLETE = True

    # Persist everything to config file
    success = _persist_to_env(env_updates)
    if not success:
        return SetupResponse(
            success=False,
            message="Failed to save configuration. Check file permissions.",
            data_directory=data_dir_str,
        )

    logger.info("Setup: first-run configuration complete")
    return SetupResponse(
        success=True,
        message="Setup complete! Conduital is ready to use.",
        data_directory=data_dir_str,
    )


@router.post("/validate-path", response_model=PathValidation)
def validate_sync_path(path: str):
    """Validate a sync folder path exists and is accessible."""
    folder = Path(path)
    exists = folder.exists()
    return PathValidation(
        valid=folder.is_dir() if exists else False,
        exists=exists,
        is_directory=folder.is_dir() if exists else False,
        path=str(folder.resolve()) if exists else path,
    )
