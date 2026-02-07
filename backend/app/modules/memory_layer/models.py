"""
Memory Layer database models

These models port the proactive-assistant memory schema to SQLAlchemy,
enabling database-backed memory storage with optional JSON file export.
"""

from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Boolean,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class MemoryNamespace(Base, TimestampMixin):
    """
    Namespace for organizing memory objects.

    Namespaces follow dot notation: core.identity, projects.active, etc.
    """
    __tablename__ = "memory_namespaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_namespace: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Default priority for objects in this namespace
    default_priority: Mapped[int] = mapped_column(Integer, default=50)

    # Relationships
    memory_objects: Mapped[list["MemoryObject"]] = relationship(
        "MemoryObject",
        back_populates="namespace_ref",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_namespace_parent", "parent_namespace"),
    )


class MemoryObject(Base, TimestampMixin):
    """
    A memory object representing a piece of persistent context.

    Ported from proactive-assistant JSON schema.

    Memory objects have:
    - Unique ID within namespace
    - Priority score (0-100) for retrieval ordering
    - Effective dates for temporal validity
    - Versioning for schema evolution
    - Content stored as JSON (or reference to external file)
    """
    __tablename__ = "memory_objects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Unique identifier (e.g., "user-profile-001")
    object_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Namespace (e.g., "core.identity")
    namespace: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("memory_namespaces.name"),
        nullable=False
    )

    # Version (semver format)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    # Priority for retrieval ordering (0=lowest, 100=highest)
    priority: Mapped[int] = mapped_column(Integer, default=50)

    # Effective date range
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Tags for filtering
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Content checksum for integrity verification
    checksum: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Storage type: "db" for inline JSON, "file" for external JSON file
    storage_type: Mapped[str] = mapped_column(String(20), default="db")

    # Content - stored inline as JSON when storage_type="db"
    content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # File path - used when storage_type="file"
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Owner (when auth is enabled)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True
    )

    # Relationships
    namespace_ref: Mapped["MemoryNamespace"] = relationship(
        "MemoryNamespace",
        back_populates="memory_objects"
    )

    __table_args__ = (
        Index("idx_memory_namespace", "namespace"),
        Index("idx_memory_priority", "priority"),
        Index("idx_memory_effective", "effective_from", "effective_to"),
        Index("idx_memory_object_id", "object_id"),
        Index("idx_memory_user", "user_id"),
        CheckConstraint("priority >= 0 AND priority <= 100", name="check_priority_range"),
        CheckConstraint(
            "storage_type IN ('db', 'file')",
            name="check_storage_type"
        ),
    )

    def is_active(self, as_of: Optional[date] = None) -> bool:
        """Check if memory object is active (within effective date range)"""
        check_date = as_of or date.today()
        if self.effective_from > check_date:
            return False
        if self.effective_to and self.effective_to < check_date:
            return False
        return True


class MemoryIndex(Base, TimestampMixin):
    """
    Quick key routing for fast memory access.

    Ported from proactive-assistant index.json quick_keys.
    """
    __tablename__ = "memory_index"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Quick key name (e.g., "user_profile", "macro_gmb")
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Target: either memory_object_id or file path
    target_type: Mapped[str] = mapped_column(String(20), default="object")  # object, file
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PrefetchRule(Base, TimestampMixin):
    """
    Prefetch rules for bundle loading.

    Ported from proactive-assistant index.json prefetch_rules.
    """
    __tablename__ = "prefetch_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Rule name (e.g., "gmb_boot")
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Trigger condition (e.g., "macro_gmb")
    trigger: Mapped[str] = mapped_column(String(255), nullable=False)

    # Lookahead time in minutes
    lookahead_minutes: Mapped[int] = mapped_column(Integer, default=120)

    # Bundle of memory objects to preload (list of object_ids)
    bundle: Mapped[list] = mapped_column(JSON, nullable=False)

    # Decay time for false prefetch (minutes)
    false_prefetch_decay_minutes: Mapped[int] = mapped_column(Integer, default=30)

    # Is this rule active?
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
