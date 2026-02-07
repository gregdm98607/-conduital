"""
Export schemas for data export/backup API

BACKLOG-074: Data portability promise for R1 release.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class EntityCounts(BaseModel):
    """Counts of exported entities"""

    projects: int = Field(0, description="Number of projects")
    tasks: int = Field(0, description="Number of tasks")
    areas: int = Field(0, description="Number of areas")
    goals: int = Field(0, description="Number of goals")
    visions: int = Field(0, description="Number of visions")
    contexts: int = Field(0, description="Number of contexts")
    inbox_items: int = Field(0, description="Number of inbox items")


class ExportMetadata(BaseModel):
    """Metadata about the export"""

    export_version: str = Field("1.0.0", description="Export format version")
    app_version: str = Field(..., description="Application version")
    exported_at: datetime = Field(..., description="Export timestamp (UTC)")
    commercial_mode: str = Field(..., description="Commercial mode at time of export")
    entity_counts: EntityCounts = Field(..., description="Counts of exported entities")
    database_path: Optional[str] = Field(None, description="Original database path (for reference)")


class ExportData(BaseModel):
    """Complete export data structure"""

    model_config = ConfigDict(from_attributes=True)

    metadata: ExportMetadata = Field(..., description="Export metadata")
    areas: list[dict[str, Any]] = Field(default_factory=list, description="Areas of responsibility")
    goals: list[dict[str, Any]] = Field(default_factory=list, description="Goals (1-3 year)")
    visions: list[dict[str, Any]] = Field(default_factory=list, description="Visions (3-5 year)")
    contexts: list[dict[str, Any]] = Field(default_factory=list, description="GTD contexts")
    projects: list[dict[str, Any]] = Field(default_factory=list, description="Projects with tasks")
    inbox_items: list[dict[str, Any]] = Field(default_factory=list, description="Inbox items")


class ExportPreview(BaseModel):
    """Preview of export without actual data (for UI)"""

    entity_counts: EntityCounts = Field(..., description="Counts of entities to export")
    estimated_size_bytes: int = Field(..., description="Estimated export size in bytes")
    estimated_size_display: str = Field(..., description="Human-readable size (e.g., '1.5 MB')")
    available_formats: list[str] = Field(..., description="Available export formats")
