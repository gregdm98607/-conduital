"""
Weekly review completion model — tracks when the user completes their GTD weekly review.

BETA-030: Quiet log, not a streak counter. Just records timestamps.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class WeeklyReviewCompletion(Base):
    """
    Records each weekly review completion.

    Design: Simple timestamp log. No streaks, no scoring, no gamification.
    """

    __tablename__ = "weekly_review_completions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User ownership (nullable for single-user compatibility)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # When the review was completed
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Optional notes about the review
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", backref="weekly_review_completions")

    def __repr__(self) -> str:
        return f"<WeeklyReviewCompletion(id={self.id}, completed_at='{self.completed_at}')>"
