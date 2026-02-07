"""
Vision schemas for API validation
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import VisionTimeframeEnum


class VisionBase(BaseModel):
    """Base vision schema"""

    title: str = Field(..., min_length=1, max_length=500, description="Vision title")
    description: Optional[str] = Field(None, max_length=5000, description="Vision description")
    timeframe: Optional[VisionTimeframeEnum] = Field(None, description="3_year, 5_year, life_purpose")


class VisionCreate(VisionBase):
    """Schema for creating a new vision"""

    pass


class VisionUpdate(BaseModel):
    """Schema for updating a vision"""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    timeframe: Optional[VisionTimeframeEnum] = None


class Vision(VisionBase):
    """Schema for vision response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
