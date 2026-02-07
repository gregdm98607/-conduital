"""
Activity Log model - tracks all changes for momentum calculation
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ActivityLog(Base):
    """
    Activity Log model - tracks all entity changes

    Used for:
    - Momentum calculation
    - Audit trail
    - Undo functionality (future)
    - Analytics
    """

    __tablename__ = "activity_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Entity reference
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # project, task, area
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Action details
    action_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # created, updated, completed, status_changed, file_synced
    details: Mapped[str] = mapped_column(
        Text, nullable=True
    )  # JSON with specific changes

    # Metadata
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="user"
    )  # user, file_sync, ai_assistant, system

    def __repr__(self) -> str:
        return f"<ActivityLog(id={self.id}, entity='{self.entity_type}:{self.entity_id}', action='{self.action_type}')>"
