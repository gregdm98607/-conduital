"""
Memory Layer Pydantic schemas

Request/response models for the memory layer API.
"""

from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Namespace Schemas
# =============================================================================

class NamespaceBase(BaseModel):
    """Base namespace schema"""
    name: str = Field(..., description="Namespace name (dot notation)", examples=["core.identity"])
    description: Optional[str] = Field(None, description="Namespace description")
    parent_namespace: Optional[str] = Field(None, description="Parent namespace name")
    default_priority: int = Field(50, ge=0, le=100, description="Default priority for objects")


class NamespaceCreate(NamespaceBase):
    """Schema for creating a namespace"""
    pass


class NamespaceResponse(NamespaceBase):
    """Schema for namespace response"""
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime


# =============================================================================
# Memory Object Schemas
# =============================================================================

class MemoryObjectBase(BaseModel):
    """Base memory object schema"""
    object_id: str = Field(..., description="Unique object identifier", examples=["user-profile-001"])
    namespace: str = Field(..., description="Namespace", examples=["core.identity"])
    version: str = Field("1.0.0", description="Version (semver)")
    priority: int = Field(50, ge=0, le=100, description="Priority for retrieval (0-100)")
    effective_from: date = Field(..., description="Start of effective period")
    effective_to: Optional[date] = Field(None, description="End of effective period (null=current)")
    tags: Optional[list[str]] = Field(None, description="Tags for filtering")


class MemoryObjectCreate(MemoryObjectBase):
    """Schema for creating a memory object"""
    content: dict[str, Any] = Field(..., description="Memory content as JSON")
    storage_type: str = Field("db", description="Storage type: db or file")
    file_path: Optional[str] = Field(None, description="File path if storage_type=file")


class MemoryObjectUpdate(BaseModel):
    """Schema for updating a memory object"""
    version: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    effective_to: Optional[date] = None
    tags: Optional[list[str]] = None
    content: Optional[dict[str, Any]] = None


class MemoryObjectResponse(MemoryObjectBase):
    """Schema for memory object response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    checksum: Optional[str]
    storage_type: str
    content: Optional[dict[str, Any]]
    file_path: Optional[str]
    created_at: datetime
    updated_at: datetime


class MemoryObjectBrief(BaseModel):
    """Brief memory object for list views"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    object_id: str
    namespace: str
    priority: int
    version: str
    is_active: bool = True


# =============================================================================
# Hydration Schemas
# =============================================================================

class HydrationRequest(BaseModel):
    """Request for context hydration"""
    namespaces: Optional[list[str]] = Field(
        None,
        description="Namespaces to include (null=all)"
    )
    min_priority: int = Field(0, ge=0, le=100, description="Minimum priority to include")
    max_objects: int = Field(50, ge=1, le=200, description="Maximum objects to return")
    include_content: bool = Field(True, description="Include full content in response")
    as_of_date: Optional[date] = Field(None, description="Effective date filter (default=today)")
    persona: Optional[str] = Field(None, description="Persona for routing preferences")


class HydrationResponse(BaseModel):
    """Response from context hydration"""
    objects: list[MemoryObjectResponse]
    total_count: int
    included_count: int
    namespaces_included: list[str]
    hydration_mode: str = Field(..., description="full, thin, or targeted")


# =============================================================================
# Index Schemas
# =============================================================================

class QuickKeyCreate(BaseModel):
    """Schema for creating a quick key"""
    key: str = Field(..., description="Quick key name")
    target_type: str = Field("object", description="Target type: object or file")
    target_id: Optional[int] = Field(None, description="Target memory object ID")
    target_path: Optional[str] = Field(None, description="Target file path")
    description: Optional[str] = None


class QuickKeyResponse(QuickKeyCreate):
    """Schema for quick key response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# =============================================================================
# Prefetch Rule Schemas
# =============================================================================

class PrefetchRuleCreate(BaseModel):
    """Schema for creating a prefetch rule"""
    name: str = Field(..., description="Rule name")
    trigger: str = Field(..., description="Trigger condition")
    lookahead_minutes: int = Field(120, description="Lookahead time in minutes")
    bundle: list[str] = Field(..., description="Object IDs to prefetch")
    false_prefetch_decay_minutes: int = Field(30)
    is_active: bool = Field(True)


class PrefetchRuleResponse(PrefetchRuleCreate):
    """Schema for prefetch rule response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Import/Export Schemas
# =============================================================================

class MemoryExport(BaseModel):
    """Schema for exporting memory to PA-compatible JSON format"""
    version: str = "1.0.0"
    exported_at: datetime
    namespaces: list[NamespaceResponse]
    objects: list[MemoryObjectResponse]
    quick_keys: list[QuickKeyResponse]
    prefetch_rules: list[PrefetchRuleResponse]


class MemoryImportRequest(BaseModel):
    """Schema for importing memory from PA-compatible JSON"""
    overwrite_existing: bool = Field(False, description="Overwrite existing objects with same ID")
    namespaces: Optional[list[NamespaceCreate]] = None
    objects: list[MemoryObjectCreate]
