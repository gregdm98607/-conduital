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


class InboxStatsResponse(BaseModel):
    """BETA-032: Inbox processing statistics"""

    unprocessed_count: int = Field(..., description="Total unprocessed inbox items")
    processed_today: int = Field(..., description="Items processed today (UTC)")
    avg_processing_time_hours: Optional[float] = Field(None, description="Average hours from capture to processing (last 30 days)")


class InboxBatchAction(BaseModel):
    """BETA-031: Batch processing request"""

    item_ids: list[int] = Field(..., min_length=1, max_length=100, description="IDs of inbox items to process")
    action: str = Field(..., description="Batch action: assign_to_project, delete, convert_to_task")
    project_id: Optional[int] = Field(None, description="Target project ID (required for assign/convert)")
    title_override: Optional[str] = Field(None, max_length=500, description="Title override for created tasks")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"assign_to_project", "delete", "convert_to_task"}
        if v not in allowed:
            raise ValueError(f"action must be one of: {', '.join(sorted(allowed))}")
        return v


class InboxBatchResultItem(BaseModel):
    """Result for a single batch-processed item"""

    item_id: int
    success: bool
    error: Optional[str] = None


class InboxBatchResponse(BaseModel):
    """BETA-031: Batch processing response"""

    processed: int = Field(..., description="Number of successfully processed items")
    failed: int = Field(0, description="Number of failed items")
    results: list[InboxBatchResultItem]


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
