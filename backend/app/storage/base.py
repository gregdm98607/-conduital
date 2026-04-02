"""
StorageProvider abstract base class.

Defines the interface for pluggable data-repo backends.
Follows the same ABC pattern as AIProvider in ai_service.py.
"""

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


class ChangeType(enum.Enum):
    """Types of changes detected by watch_for_changes."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class Change:
    """Represents a single detected change in the storage backend."""

    change_type: ChangeType
    entity_type: str
    entity_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


class StorageProvider(ABC):
    """
    Abstract base class for storage providers.

    Each provider implements reading/writing entity data to a specific
    backend (local markdown folder, cloud storage, API, etc.).

    Entity types mirror the domain model: "project", "task", etc.
    Entity IDs are strings — the provider decides the format
    (e.g. relative file paths for local folder, UUIDs for cloud).

    All data is exchanged as plain dicts so the provider layer
    stays decoupled from SQLAlchemy ORM models.
    """

    @abstractmethod
    def read_entity(self, entity_type: str, entity_id: str) -> dict:
        """
        Read a single entity from storage.

        Args:
            entity_type: Kind of entity ("project", "task", etc.)
            entity_id: Provider-specific identifier

        Returns:
            Dict with at least 'metadata', 'content', and (for projects)
            'tasks'. Exact keys depend on entity_type.

        Raises:
            FileNotFoundError: If the entity does not exist.
            ValueError: If entity_type is unsupported.
        """
        ...

    @abstractmethod
    def write_entity(
        self, entity_type: str, entity_id: str, data: dict
    ) -> str:
        """
        Write (create or update) an entity to storage.

        Args:
            entity_type: Kind of entity ("project", "task", etc.)
            entity_id: Provider-specific identifier. If empty/None the
                       provider may auto-generate one (e.g. from title).
            data: Dict containing entity fields. Expected shape varies
                  by entity_type (see LocalFolderProvider for the
                  canonical project schema).

        Returns:
            The canonical entity_id that was written (may differ from
            input if auto-generated).

        Raises:
            ValueError: If entity_type is unsupported or data is invalid.
        """
        ...

    @abstractmethod
    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        Delete an entity from storage.

        Args:
            entity_type: Kind of entity
            entity_id: Provider-specific identifier

        Returns:
            True if the entity was deleted, False if it did not exist.
        """
        ...

    @abstractmethod
    def list_entities(self, entity_type: str) -> list[dict]:
        """
        List all entities of the given type.

        Args:
            entity_type: Kind of entity

        Returns:
            List of dicts, each with at least 'entity_id' and 'metadata'.
        """
        ...

    @abstractmethod
    def exists(self, entity_type: str, entity_id: str) -> bool:
        """
        Check whether an entity exists in storage.

        Args:
            entity_type: Kind of entity
            entity_id: Provider-specific identifier

        Returns:
            True if the entity exists.
        """
        ...

    @abstractmethod
    def watch_for_changes(self) -> list[Change]:
        """
        Detect changes since the last call (or since provider init).

        Providers that don't support watching may return an empty list.

        Returns:
            List of Change objects describing what changed.
        """
        ...
