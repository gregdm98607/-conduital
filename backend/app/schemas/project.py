"""
Project schemas for API validation
"""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import StatusEnum, strip_whitespace

if TYPE_CHECKING:
    from app.schemas.task import Task


class AreaSummary(BaseModel):
    """Minimal area schema for embedding in project responses"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str


class ProjectBase(BaseModel):
    """Base project schema with common fields"""

    title: str = Field(..., min_length=1, max_length=500, description="Project title")

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return strip_whitespace(v)
    description: Optional[str] = Field(None, max_length=5000, description="Project description")
    outcome_statement: Optional[str] = Field(
        None, max_length=2000, description="What does successful completion look like?"
    )
    # Natural Planning Model fields
    purpose: Optional[str] = Field(
        None, max_length=2000, description="NPM Step 1: Why are we doing this?"
    )
    vision_statement: Optional[str] = Field(
        None, max_length=2000, description="NPM Step 2: What does wild success look like?"
    )
    brainstorm_notes: Optional[str] = Field(
        None, max_length=5000, description="NPM Step 3: Raw ideas, no judgment"
    )
    organizing_notes: Optional[str] = Field(
        None, max_length=5000, description="NPM Step 4: How do pieces fit together?"
    )
    status: StatusEnum = Field(StatusEnum.ACTIVE, description="Project status")
    priority: int = Field(5, ge=1, le=10, description="Project priority (1-10, 1 is highest)")
    target_completion_date: Optional[date] = Field(None, description="Target completion date")
    next_review_date: Optional[date] = Field(None, description="When to review this project")
    area_id: Optional[int] = Field(None, description="Area of responsibility ID")
    goal_id: Optional[int] = Field(None, description="Goal ID (1-3 year)")
    vision_id: Optional[int] = Field(None, description="Vision ID (3-5 year)")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)"""

    title: Optional[str] = Field(None, min_length=1, max_length=500)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        return strip_whitespace(v)
    description: Optional[str] = Field(None, max_length=5000)
    outcome_statement: Optional[str] = Field(None, max_length=2000)
    purpose: Optional[str] = Field(None, max_length=2000)
    vision_statement: Optional[str] = Field(None, max_length=2000)
    brainstorm_notes: Optional[str] = Field(None, max_length=5000)
    organizing_notes: Optional[str] = Field(None, max_length=5000)
    status: Optional[StatusEnum] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    target_completion_date: Optional[date] = None
    next_review_date: Optional[date] = None
    area_id: Optional[int] = None
    goal_id: Optional[int] = None
    vision_id: Optional[int] = None


class Project(ProjectBase):
    """Schema for project response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    outcome_statement: Optional[str] = Field(
        None, description="What does successful completion look like?"
    )
    momentum_score: float = Field(..., ge=0.0, le=1.0, description="Momentum score (0.0-1.0)")
    last_activity_at: Optional[datetime] = Field(None, description="Last activity timestamp")
    stalled_since: Optional[datetime] = Field(None, description="When project became stalled")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    last_reviewed_at: Optional[datetime] = Field(None, description="When project was last reviewed")
    file_path: Optional[str] = Field(None, description="Path to project file in synced notes")
    created_at: datetime
    updated_at: datetime
    area: Optional[AreaSummary] = Field(None, description="Associated area of responsibility")
    task_count: int = Field(0, description="Total number of tasks")
    completed_task_count: int = Field(0, description="Number of completed tasks")

    @property
    def is_stalled(self) -> bool:
        """Check if project is stalled"""
        return self.stalled_since is not None

    @property
    def days_since_activity(self) -> Optional[int]:
        """Days since last activity"""
        if not self.last_activity_at:
            return None
        delta = datetime.now(timezone.utc) - self.last_activity_at
        return delta.days


class ProjectWithTasks(Project):
    """Project with embedded tasks"""

    tasks: list["Task"] = Field(default_factory=list, description="Project tasks")

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if not self.tasks:
            return 0.0
        completed = sum(1 for task in self.tasks if task.status == "completed")
        return (completed / len(self.tasks)) * 100


class ProjectHealth(BaseModel):
    """Project health metrics"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: StatusEnum
    momentum_score: float
    days_since_activity: Optional[int]
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    waiting_tasks: int
    next_actions_count: int
    health_status: str = Field(
        ..., description="Health status: strong, moderate, weak, at_risk, stalled"
    )
    completion_percentage: float


class ProjectList(BaseModel):
    """Paginated list of projects"""

    projects: list[Project]
    total: int
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    has_more: bool


# Note: model_rebuild() is called in __init__.py to avoid circular imports