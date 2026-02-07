"""
Inbox schemas for API validation
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import InboxResultTypeEnum, strip_whitespace


class InboxItemBase(BaseModel):
    """Base inbox item schema"""

    content: str = Field(..., min_length=1, max_length=10000, description="Captured content")

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, v: str) -> str:
        return strip_whitespace(v)
    source: str = Field("web_ui", max_length=50, description="Capture source")


class InboxItemCreate(InboxItemBase):
    """Schema for creating a new inbox item"""

    pass


class InboxItemUpdate(BaseModel):
    """Schema for updating an inbox item before processing"""

    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="Updated content")

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, v: str | None) -> str | None:
        return strip_whitespace(v)


class InboxItemProcess(BaseModel):
    """Schema for processing an inbox item"""

    result_type: InboxResultTypeEnum = Field(..., description="Processing result type")
    result_id: Optional[int] = Field(None, description="ID of created entity (if applicable)")
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Custom title for created entity")

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, v: str | None) -> str | None:
        return strip_whitespace(v)
    description: Optional[str] = Field(None, max_length=5000, description="Description for created entity")


class InboxItem(InboxItemBase):
    """Schema for inbox item response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    captured_at: datetime
    processed_at: Optional[datetime] = None
    result_type: Optional[InboxResultTypeEnum] = None
    result_id: Optional[int] = None
    result_title: Optional[str] = Field(None, description="Title of created entity")
    result_project_id: Optional[int] = Field(None, description="Project ID (for task results)")

    @property
    def is_processed(self) -> bool:
        """Check if processed"""
        return self.processed_at is not None

    @property
    def preview(self) -> str:
        """Preview of content"""
        if len(self.content) <= 100:
            return self.content
        return self.content[:97] + "..."
