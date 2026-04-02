"""
Factory for creating the configured StorageProvider instance.

Mirrors the ``create_provider()`` pattern in ``ai_service.py``.
"""

import logging
from pathlib import Path
from typing import Optional

from app.storage.base import StorageProvider

logger = logging.getLogger(__name__)

# Module-level singleton (lazily initialised by get_storage_provider)
_provider_instance: Optional[StorageProvider] = None


def create_storage_provider(
    provider_type: Optional[str] = None,
    storage_path: Optional[str] = None,
) -> StorageProvider:
    """
    Factory: build a StorageProvider from explicit args or settings.

    Args:
        provider_type: "local_folder" (default from settings.STORAGE_PROVIDER).
        storage_path:  Root path (default from settings.STORAGE_PATH).

    Returns:
        Configured StorageProvider instance.

    Raises:
        ValueError: Unknown provider type or missing path.
    """
    from app.core.config import settings

    provider_type = provider_type or getattr(settings, "STORAGE_PROVIDER", "local_folder")
    storage_path = storage_path or getattr(settings, "STORAGE_PATH", None) or settings.SECOND_BRAIN_ROOT

    if not storage_path:
        raise ValueError(
            "No storage path configured. Set STORAGE_PATH or SECOND_BRAIN_ROOT."
        )

    if provider_type == "local_folder":
        from app.storage.local_folder import LocalFolderProvider

        watch_dirs = settings.watch_directories
        return LocalFolderProvider(
            root_path=Path(storage_path),
            watch_directories=watch_dirs,
        )
    else:
        raise ValueError(
            f"Unknown storage provider: '{provider_type}'. "
            f"Supported: local_folder"
        )


def get_storage_provider() -> StorageProvider:
    """
    Return (or create) the module-level singleton provider.

    Safe to call repeatedly — the instance is cached after first creation.
    """
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = create_storage_provider()
    return _provider_instance


def reset_storage_provider() -> None:
    """Clear the cached singleton (useful in tests)."""
    global _provider_instance
    _provider_instance = None
