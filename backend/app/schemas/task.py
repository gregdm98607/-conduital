"""
Task schemas for API validation
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import EnergyLevelEnum, TaskStatusEnum, TaskTypeEnum, UrgencyZoneEnum, strip_whitespace

if TYPE_CHECKING:
    from app.schemas.project import Project


class TaskBase(BaseModel):
    """Base task schema with common fields"""

    title: str = Field(..., min_length=1, max_length=500, description="Task title")

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return strip_whitespace(v)
    description: Optional[str] = Field(None, max_length=5000, description="Task description")
    status: TaskStatusEnum = Field(TaskStatusEnum.PENDING, description="Task status")
    task_type: TaskTypeEnum = Field(TaskTypeEnum.ACTION, description="Task type")

    # Context and scheduling
    context: Optional[str] = Field(None, max_length=50, description="Context (@creative, @administrative, etc.)")
    energy_level: Optional[EnergyLevelEnum] = Field(None, description="Required energy level")
    location: Optional[str] = Field(None, max_length=100, description="Location requirement")

    # Time estimates
    estimated_minutes: Optional[int] = Field(None, ge=0, description="Estimated duration (minutes)")
    due_date: Optional[date] = Field(None, description="Due date")
    defer_until: Optional[date] = Field(None, description="Defer until this date")

    # Priority and flags
    priority: int = Field(5, ge=1, le=10, description="Task priority (1-10, 1 is highest)")
    is_next_action: bool = Field(False, description="Is this the next action for the project?")
    is_two_minute_task: bool = Field(False, description="Can be done in 2 minutes or less")

    # MYN Urgency Zone
    urgency_zone: Optional[UrgencyZoneEnum] = Field(
        UrgencyZoneEnum.OPPORTUNITY_NOW,
        description="MYN urgency zone (critical_now, opportunity_now, over_the_horizon)"
    )

    # Dependencies
    waiting_for: Optional[str] = Field(None, max_length=500, description="Person/thing waiting for")
    resource_requirements: Optional[str] = Field(None, max_length=2000, description="Required resources (JSON)")

    # Relationships
    project_id: int = Field(..., description="Parent project ID")
    parent_task_id: Optional[int] = Field(None, description="Parent task ID (for subtasks)")
    phase_id: Optional[int] = Field(None, description="Project phase ID")


class TaskCreate(TaskBase):
    """Schema for creating a new task"""

    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task (all fields optional)"""

    title: Optional[str] = Field(None, min_length=1, max_length=500)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        return strip_whitespace(v)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatusEnum] = None
    task_type: Optional[TaskTypeEnum] = None
    context: Optional[str] = Field(None, max_length=50)
    energy_level: Optional[EnergyLevelEnum] = None
    location: Optional[str] = Field(None, max_length=100)
    estimated_minutes: Optional[int] = Field(None, ge=0)
    due_date: Optional[date] = None
    defer_until: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    is_next_action: Optional[bool] = None
    is_two_minute_task: Optional[bool] = None
    urgency_zone: Optional[UrgencyZoneEnum] = None
    waiting_for: Optional[str] = Field(None, max_length=500)
    resource_requirements: Optional[str] = Field(None, max_length=2000)
    parent_task_id: Optional[int] = None
    phase_id: Optional[int] = None


class Task(TaskBase):
    """Schema for task response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sequence_order: Optional[int] = None
    actual_minutes: Optional[int] = Field(None, ge=0)
    is_unstuck_task: bool = Field(False, description="Minimal task for stalled project")
    file_line_number: Optional[int] = None
    file_marker: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

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
        """Human-readable duration"""
        if not self.estimated_minutes:
            return "Unknown"
        if self.estimated_minutes < 60:
            return f"{self.estimated_minutes}min"
        hours = self.estimated_minutes // 60
        minutes = self.estimated_minutes % 60
        if minutes == 0:
            return f"{hours}h"
        return f"{hours}h {minutes}min"


class TaskWithProject(Task):
    """Task with embedded project information"""

    project: Optional["Project"] = Field(None, description="Parent project")


class TaskList(BaseModel):
    """Paginated list of tasks"""

    tasks: list[Task]
    total: int
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    has_more: bool


class TaskListWithProjects(BaseModel):
    """Paginated list of tasks with project info"""

    tasks: list[TaskWithProject]
    total: int
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
    has_more: bool


class NextActionResponse(BaseModel):
    """Response for next actions query"""

    tasks: list[TaskWithProject]
    stalled_projects_count: int = Field(0, description="Number of stalled projects")
    context_filter: Optional[str] = None
    energy_filter: Optional[str] = None
    time_available: Optional[int] = None


class DailyDashboardResponse(BaseModel):
    """Response for daily dashboard endpoint"""

    model_config = ConfigDict(from_attributes=True)

    top_3_priorities: list[TaskWithProject] = Field(
        default_factory=list, description="Top 3 priority tasks for today"
    )
    quick_wins: list[TaskWithProject] = Field(
        default_factory=list, description="Quick tasks (< 15 min)"
    )
    due_today: list[TaskWithProject] = Field(
        default_factory=list, description="Tasks due today"
    )
    stalled_projects_count: int = Field(0, description="Number of stalled projects")
    top_momentum_projects: list["Project"] = Field(
        default_factory=list, description="Projects with highest momentum"
    )