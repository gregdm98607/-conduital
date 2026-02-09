"""
Task model
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.project_phase import ProjectPhase


class Task(Base, TimestampMixin):
    """
    Task model - represents a single action item

    A physical, visible activity that moves something forward.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status and type
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )  # pending, in_progress, waiting, completed, cancelled
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="action"
    )  # action, milestone, waiting_for, someday_maybe

    # Relationships
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_task_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True, index=True
    )
    phase_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("project_phases.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Sequencing
    sequence_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Scheduling
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    defer_until: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Context and filtering
    context: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )  # creative, administrative, research, communication, deep_work, quick_win
    energy_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )  # high, medium, low
    location: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # home, office, anywhere, errand

    # Priority and flags
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5, index=True)  # 1-10, 1 is highest
    is_next_action: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_two_minute_task: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_unstuck_task: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )  # Minimal task for stalled projects

    # MYN Urgency Zone
    urgency_zone: Mapped[Optional[str]] = mapped_column(
        String(30), nullable=True, default="opportunity_now", index=True
    )  # critical_now, opportunity_now, over_the_horizon

    # Tracking
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Resources and dependencies
    waiting_for: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Person/thing waiting on
    resource_requirements: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON: files, tools, people

    # File sync
    file_line_number: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # Line in project file
    file_marker: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # Unique marker for sync

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    phase: Mapped[Optional["ProjectPhase"]] = relationship(
        "ProjectPhase", back_populates="tasks"
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
        cascade="all, delete-orphan",
        foreign_keys=[parent_task_id],
    )
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task", back_populates="subtasks", foreign_keys=[parent_task_id], remote_side=[id]
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}', next_action={self.is_next_action})>"

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if not self.due_date or self.status in ["completed", "cancelled"]:
            return False
        return self.due_date < date.today()

    @property
    def is_due_soon(self) -> bool:
        """Check if task is due within 3 days"""
        if not self.due_date or self.status in ["completed", "cancelled"]:
            return False
        from datetime import timedelta

        return date.today() <= self.due_date <= date.today() + timedelta(days=3)

    @property
    def duration_display(self) -> str:
        """Human-readable duration estimate"""
        if not self.estimated_minutes:
            return "Unknown"
        if self.estimated_minutes < 60:
            return f"{self.estimated_minutes}min"
        hours = self.estimated_minutes // 60
        minutes = self.estimated_minutes % 60
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}min"
