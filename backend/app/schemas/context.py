"""
Context schemas for API validation
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ContextTypeEnum


class ContextBase(BaseModel):
    """Base context schema"""

    name: str = Field(..., min_length=1, max_length=100, description="Context name (@home, etc.)")
    context_type: Optional[ContextTypeEnum] = Field(None, description="Context type")
    description: Optional[str] = Field(None, max_length=1000, description="Context description")
    icon: Optional[str] = Field(None, max_length=50, description="Icon for UI")


class ContextCreate(ContextBase):
    """Schema for creating a new context"""

    pass


class ContextUpdate(BaseModel):
    """Schema for updating a context"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    context_type: Optional[ContextTypeEnum] = None
    description: Optional[str] = Field(None, max_length=1000)
    icon: Optional[str] = Field(None, max_length=50)


class Context(ContextBase):
    """Schema for context response"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
