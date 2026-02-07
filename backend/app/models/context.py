"""
Context model - GTD contexts for task filtering
"""

from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Context(Base, TimestampMixin):
    """
    Context model - GTD contexts for organizing next actions

    Examples:
    - Location: @home, @office, @errands
    - Tool: @computer, @phone, @tablet
    - Energy: @creative, @administrative, @deep_work
    - Time: @quick_win (< 15min), @focus_block (60+ min)
    """

    __tablename__ = "contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    # Context categorization
    context_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # location, energy, work_type, time, tool

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # For UI display

    def __repr__(self) -> str:
        return f"<Context(id={self.id}, name='{self.name}', type='{self.context_type}')>"
