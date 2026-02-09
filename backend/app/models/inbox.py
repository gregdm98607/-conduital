"""
Inbox model - quick capture
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class InboxItem(TimestampMixin, Base):
    """
    Inbox model - captures ideas, tasks, and items for later processing.

    Principle: Capture everything, process later.
    """

    __tablename__ = "inbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User ownership (required for multi-user SaaS)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Capture source
    source: Mapped[str] = mapped_column(
        String(50), nullable=False, default="web_ui"
    )  # web_ui, api, voice, email, file

    # Processing result
    result_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # task, project, reference, trash
    result_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # ID of created entity

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", backref="inbox_items")

    def __repr__(self) -> str:
        status = "processed" if self.processed_at else "pending"
        return f"<InboxItem(id={self.id}, status='{status}', content='{self.content[:50]}...')>"

    @property
    def is_processed(self) -> bool:
        """Check if item has been processed"""
        return self.processed_at is not None

    @property
    def preview(self) -> str:
        """Get preview of content (first 100 chars)"""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."
