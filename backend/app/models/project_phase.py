"""
Project Phase model
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.task import Task


class ProjectPhase(Base):
    """
    Project Phase model - represents a stage in a multi-phase project

    Example phases:
    - Manuscript: Research, Outline, Draft, Revision, Editing, Submission
    - Genealogy: Collection, Digitization, Analysis, Writing, Review
    """

    __tablename__ = "project_phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Relationships
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Phase details
    phase_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phase_order: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1, 2, 3, etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, active, completed

    # Timestamps
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="phases")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="phase")

    def __repr__(self) -> str:
        return f"<ProjectPhase(id={self.id}, name='{self.phase_name}', order={self.phase_order}, status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if this phase is currently active"""
        return self.status == "active"

    @property
    def is_completed(self) -> bool:
        """Check if this phase is completed"""
        return self.status == "completed"
