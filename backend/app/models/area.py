"""
Area model - Areas of Responsibility
"""

from typing import TYPE_CHECKING, Optional

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Area(Base, TimestampMixin):
    """
    Area of Responsibility model

    A sphere of activity with a standard to maintain.
    Represents ongoing domains of responsibility (work, health, finance, etc.)
    """

    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User ownership (required for multi-user SaaS)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # File system integration
    folder_path: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, unique=True
    )  # e.g., 20_Areas/20.05_AI_Systems

    # What does "good" look like?
    standard_of_excellence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Review cadence
    review_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="weekly"
    )  # daily, weekly, monthly

    # Last reviewed timestamp (for tracking review compliance)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Health score (0.0-1.0, calculated from constituent project momentum)
    health_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Archival
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", backref="areas")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="area")

    def __repr__(self) -> str:
        return f"<Area(id={self.id}, title='{self.title}')>"

    @property
    def active_projects_count(self) -> int:
        """Count active projects in this area"""
        return sum(1 for p in self.projects if p.status == "active")
