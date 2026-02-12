"""
Project model
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.area import Area
    from app.models.goal import Goal
    from app.models.project_phase import ProjectPhase
    from app.models.task import Task
    from app.models.user import User
    from app.models.vision import Vision


class Project(Base, TimestampMixin):
    """
    Project model - represents a multi-step outcome with a clear endpoint

    Any desired result requiring more than one action step.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # User ownership (required for multi-user SaaS)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )  # nullable=True for migration compatibility, will be required in production

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome_statement: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # What does "done" look like?

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )  # active, someday_maybe, completed, archived, stalled

    # Relationships
    area_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("areas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    phase_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("phase_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    goal_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("goals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vision_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("visions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Priority and momentum
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=5, index=True)  # 1-10, 1 is highest
    momentum_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, index=True
    )  # 0.0-1.0
    previous_momentum_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None
    )  # Previous score for delta/trend calculation

    # Timestamps
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    stalled_since: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    target_completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Review tracking
    review_frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, default="weekly"
    )  # daily, weekly, monthly
    next_review_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, index=True
    )  # Auto-calculated from review_frequency + last_reviewed_at
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # When project was last reviewed

    # Natural Planning Model fields
    purpose: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # NPM Step 1: Why are we doing this?
    vision_statement: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # NPM Step 2: What does wild success look like?
    brainstorm_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # NPM Step 3: Raw ideas, no judgment
    organizing_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # NPM Step 4: How do pieces fit together?

    # File system integration
    file_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True, unique=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # SHA-256 hash

    # Non-persisted attributes populated by service layer queries (DEBT-061).
    # Defined here so the intent is explicit, IDE autocomplete works, and
    # Pydantic from_attributes can read them reliably.
    task_count: int = 0
    completed_task_count: int = 0

    # Relationships (defined with TYPE_CHECKING to avoid circular imports)
    user: Mapped[Optional["User"]] = relationship("User", backref="projects")
    area: Mapped[Optional["Area"]] = relationship("Area", back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )
    phases: Mapped[list["ProjectPhase"]] = relationship(
        "ProjectPhase", back_populates="project", cascade="all, delete-orphan"
    )
    goal: Mapped[Optional["Goal"]] = relationship("Goal", back_populates="projects")
    vision: Mapped[Optional["Vision"]] = relationship("Vision", back_populates="projects")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title='{self.title}', status='{self.status}', momentum={self.momentum_score})>"

    @property
    def is_stalled(self) -> bool:
        """Check if project is currently stalled"""
        return self.stalled_since is not None

    @property
    def days_since_activity(self) -> Optional[int]:
        """Calculate days since last activity"""
        if not self.last_activity_at:
            return None
        delta = datetime.now(timezone.utc) - self.last_activity_at
        return delta.days

    @property
    def completion_percentage(self) -> float:
        """Calculate percentage of completed tasks"""
        if not self.tasks:
            return 0.0
        completed = sum(1 for task in self.tasks if task.status == "completed")
        return (completed / len(self.tasks)) * 100

    @property
    def is_review_due(self) -> bool:
        """Check if project review is due (next_review_date <= today)"""
        if not self.next_review_date:
            return False
        return self.next_review_date <= date.today()

    @property
    def days_until_review(self) -> Optional[int]:
        """Calculate days until next review (negative if overdue)"""
        if not self.next_review_date:
            return None
        delta = self.next_review_date - date.today()
        return delta.days
