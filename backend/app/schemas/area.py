"""
Area schemas for API validation
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import ReviewFrequencyEnum, strip_whitespace

if TYPE_CHECKING:
    from app.schemas.project import Project


class AreaBase(BaseModel):
    """Base area schema"""

    title: str = Field(..., min_length=1, max_length=200, description="Area title")

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str) -> str:
        return strip_whitespace(v)
    description: Optional[str] = Field(None, max_length=5000, description="Area description")
    folder_path: Optional[str] = Field(None, max_length=1000, description="Folder path in Second Brain")
    standard_of_excellence: Optional[str] = Field(
        None, max_length=2000, description="GTD: What does good look like?"
    )
    review_frequency: ReviewFrequencyEnum = Field(
        ReviewFrequencyEnum.WEEKLY, description="Review frequency: daily, weekly, monthly"
    )


class AreaCreate(AreaBase):
    """Schema for creating a new area"""

    pass


class AreaUpdate(BaseModel):
    """Schema for updating an area"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        return strip_whitespace(v)
    description: Optional[str] = Field(None, max_length=5000)
    folder_path: Optional[str] = Field(None, max_length=1000)
    standard_of_excellence: Optional[str] = Field(None, max_length=2000)
    review_frequency: Optional[ReviewFrequencyEnum] = None


class Area(AreaBase):
    """Schema for area response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    health_score: float = Field(0.0, ge=0.0, le=1.0, description="Area health score (0.0-1.0)")
    is_archived: bool = Field(False, description="Whether area is archived")
    archived_at: Optional[datetime] = Field(None, description="When area was archived")
    last_reviewed_at: Optional[datetime] = Field(None, description="When area was last reviewed")
    created_at: datetime
    updated_at: datetime


class AreaWithCounts(Area):
    """Area with project counts (for list views)"""

    project_count: int = Field(0, description="Total number of projects in this area")
    active_project_count: int = Field(0, description="Number of active projects in this area")


class AreaWithProjects(Area):
    """Area with embedded projects"""

    projects: list["Project"] = Field(default_factory=list, description="Projects in this area")

    # Computed fields serialized in response
    active_projects_count: int = Field(0, description="Count of active projects")
    stalled_projects_count: int = Field(0, description="Count of stalled projects")
    completed_projects_count: int = Field(0, description="Count of completed projects")