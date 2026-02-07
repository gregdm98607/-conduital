"""
Goal model - 1-3 year objectives (GTD Horizon 3)
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Goal(Base, TimestampMixin):
    """
    Goal model - GTD Horizon of Focus Level 3 (1-3 year goals)
    """

    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User ownership (required for multi-user SaaS)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timeframe
    timeframe: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 1_year, 2_year, 3_year
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active"
    )  # active, completed, archived, cancelled

    # Completion
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", backref="goals")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="goal")

    def __repr__(self) -> str:
        return f"<Goal(id={self.id}, title='{self.title}', timeframe='{self.timeframe}')>"
