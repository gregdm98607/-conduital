"""
Sync State model - tracks file synchronization status
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SyncState(Base):
    """
    Sync State model - tracks synchronization between files and database

    Used for:
    - Change detection (file hash comparison)
    - Conflict resolution
    - Sync status monitoring
    - Error tracking
    """

    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # File reference
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)

    # Sync tracking
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_file_modified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Change detection
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )  # SHA-256 hash

    # Status
    sync_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # synced, pending, conflict, error

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Entity mapping
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # project, area, resource
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<SyncState(id={self.id}, file='{self.file_path}', status='{self.sync_status}')>"

    @property
    def has_conflict(self) -> bool:
        """Check if sync has a conflict"""
        return self.sync_status == "conflict"

    @property
    def has_error(self) -> bool:
        """Check if sync has an error"""
        return self.sync_status == "error"
