"""
Vision model - 3-5 year vision and life purpose
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


class Vision(Base, TimestampMixin):
    """
    Vision model - long-term vision and life purpose (3-5 year horizon).
    """

    __tablename__ = "visions"

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
    )  # 3_year, 5_year, life_purpose

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", backref="visions")
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="vision")

    def __repr__(self) -> str:
        return f"<Vision(id={self.id}, title='{self.title}', timeframe='{self.timeframe}')>"
