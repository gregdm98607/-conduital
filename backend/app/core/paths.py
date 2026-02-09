"""
Path resolution for Conduital.

Development mode: paths relative to source tree (existing behavior).
Packaged mode (PyInstaller): paths in %LOCALAPPDATA%\\Conduital\\.

This module has NO imports from app.core.config to avoid circular imports.
All other modules should import path functions from here.
"""

import os
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def is_packaged() -> bool:
    """Detect if running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


@lru_cache(maxsize=1)
def get_bundle_dir() -> Path:
    """Get the directory where bundled data files live (PyInstaller _MEIPASS).

    In development, this is the backend/ directory.
    """
    if is_packaged():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent.parent


@lru_cache(maxsize=1)
def get_data_dir():
    """Get the user data directory.

    Packaged: %LOCALAPPDATA%\\Conduital\\
    Development: None (callers use existing dev paths)

    Override: set CONDUITAL_DATA_DIR environment variable.

    Returns:
        Path or None. None signals "use existing dev paths".
    """
    override = os.environ.get("CONDUITAL_DATA_DIR")
    if override:
        return Path(override)

    if is_packaged():
        base = Path(
            os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        )
        return base / "Conduital"

    return None


def get_config_path() -> Path:
    """Get path to the config/env file."""
    data_dir = get_data_dir()
    if data_dir:
        return data_dir / "config.env"
    # Development: backend/.env
    return Path(__file__).resolve().parent.parent.parent / ".env"


def get_database_path() -> str:
    """Get default path to the SQLite database."""
    data_dir = get_data_dir()
    if data_dir:
        return str(data_dir / "tracker.db")
    # Development default
    return str(Path.home() / ".conduital" / "tracker.db")


def get_log_dir() -> Path:
    """Get log directory."""
    data_dir = get_data_dir()
    if data_dir:
        return data_dir / "logs"
    # Development: backend/logs/
    return Path(__file__).resolve().parent.parent.parent / "logs"


def get_alembic_ini_path() -> Path:
    """Get path to alembic.ini."""
    if is_packaged():
        return get_bundle_dir() / "alembic.ini"
    return Path(__file__).resolve().parent.parent.parent / "alembic.ini"


def get_alembic_dir() -> Path:
    """Get path to alembic migrations directory."""
    if is_packaged():
        return get_bundle_dir() / "alembic"
    return Path(__file__).resolve().parent.parent.parent / "alembic"


def get_frontend_dist() -> Path:
    """Get path to frontend/dist."""
    if is_packaged():
        return get_bundle_dir() / "frontend_dist"
    return Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"


def ensure_data_dir() -> None:
    """Create the data directory and subdirectories if needed.

    In development mode this is a no-op.
    """
    data_dir = get_data_dir()
    if data_dir:
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "logs").mkdir(exist_ok=True)


def is_first_run() -> bool:
    """Check if first-run setup has been completed.

    Returns True if the config file doesn't exist or SETUP_COMPLETE is not set.
    """
    config_path = get_config_path()
    if not config_path.exists():
        return True
    try:
        for line in config_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("SETUP_COMPLETE=") and not stripped.startswith("#"):
                value = stripped.split("=", 1)[1].strip().lower().strip('"').strip("'")
                return value not in ("true", "1", "yes")
    except Exception:
        pass
    return True


def check_legacy_migration() -> dict:
    """Check if legacy data exists that should be migrated.

    Looks for a database at ~/.conduital/tracker.db that could be
    migrated to the new data directory.

    Returns:
        Dict with migration info: needs_migration, legacy_path, target_path.
    """
    data_dir = get_data_dir()
    if not data_dir:
        return {"needs_migration": False}

    legacy_db = Path.home() / ".conduital" / "tracker.db"
    target_db = data_dir / "tracker.db"

    if legacy_db.exists() and not target_db.exists():
        return {
            "needs_migration": True,
            "legacy_path": str(legacy_db),
            "target_path": str(target_db),
        }
    return {"needs_migration": False}
