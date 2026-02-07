"""
Goal schemas for API validation
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import GoalStatusEnum, GoalTimeframeEnum


class GoalBase(BaseModel):
    """Base goal schema"""

    title: str = Field(..., min_length=1, max_length=500, description="Goal title")
    description: Optional[str] = Field(None, max_length=5000, description="Goal description")
    timeframe: Optional[GoalTimeframeEnum] = Field(None, description="1_year, 2_year, 3_year")
    target_date: Optional[date] = Field(None, description="Target completion date")
    status: GoalStatusEnum = Field(GoalStatusEnum.ACTIVE, description="Goal status")


class GoalCreate(GoalBase):
    """Schema for creating a new goal"""

    pass


class GoalUpdate(BaseModel):
    """Schema for updating a goal"""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    timeframe: Optional[GoalTimeframeEnum] = None
    target_date: Optional[date] = None
    status: Optional[GoalStatusEnum] = None


class Goal(GoalBase):
    """Schema for goal response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
