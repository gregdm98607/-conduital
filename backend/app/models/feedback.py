"""
Feedback model — stores in-app user feedback submissions.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Feedback(Base):
    """
    User feedback submitted via the in-app feedback widget (F-001).

    Stored locally in SQLite. No PII required — email is optional.
    The `page` field captures window.location.pathname so feedback
    can be triaged by the screen that generated it.
    """

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Feedback content
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # bug | feature | general
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional context
    page: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    app_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Metadata
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, category='{self.category}', page='{self.page}')>"
