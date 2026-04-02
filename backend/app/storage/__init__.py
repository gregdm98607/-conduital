"""
Storage provider abstraction for data repo agnostic storage.

Supports pluggable backends (local folder, cloud, etc.) following
the same provider pattern as AIProvider in ai_service.py.
"""

from app.storage.base import Change, ChangeType, StorageProvider
from app.storage.factory import create_storage_provider, get_storage_provider
from app.storage.local_folder import LocalFolderProvider

__all__ = [
    "Change",
    "ChangeType",
    "StorageProvider",
    "LocalFolderProvider",
    "create_storage_provider",
    "get_storage_provider",
]
