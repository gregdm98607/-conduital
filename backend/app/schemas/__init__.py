"""
Pydantic schemas for API request/response validation
"""

from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectUpdate,
    ProjectWithTasks,
    ProjectHealth,
)
from app.schemas.task import Task, TaskCreate, TaskUpdate, TaskWithProject, TaskListWithProjects, NextActionResponse, DailyDashboardResponse
from app.schemas.area import Area, AreaCreate, AreaUpdate, AreaWithProjects
from app.schemas.goal import Goal, GoalCreate, GoalUpdate
from app.schemas.vision import Vision, VisionCreate, VisionUpdate
from app.schemas.context import Context, ContextCreate, ContextUpdate
from app.schemas.inbox import InboxItem, InboxItemCreate, InboxItemProcess
from app.schemas.common import StatusEnum, TaskStatusEnum, PriorityEnum
from app.schemas.export import EntityCounts, ExportMetadata, ExportData, ExportPreview

# Rebuild models to resolve forward references between schemas
# This must happen after all imports are complete to avoid circular import issues
ProjectWithTasks.model_rebuild()
TaskWithProject.model_rebuild()
DailyDashboardResponse.model_rebuild()
AreaWithProjects.model_rebuild()

__all__ = [
    # Project schemas
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectWithTasks",
    "ProjectHealth",
    # Task schemas
    "Task",
    "TaskCreate",
    "TaskUpdate",
    "TaskWithProject",
    "TaskListWithProjects",
    "NextActionResponse",
    "DailyDashboardResponse",
    # Area schemas
    "Area",
    "AreaCreate",
    "AreaUpdate",
    "AreaWithProjects",
    # Goal schemas
    "Goal",
    "GoalCreate",
    "GoalUpdate",
    # Vision schemas
    "Vision",
    "VisionCreate",
    "VisionUpdate",
    # Context schemas
    "Context",
    "ContextCreate",
    "ContextUpdate",
    # Inbox schemas
    "InboxItem",
    "InboxItemCreate",
    "InboxItemProcess",
    # Common enums
    "StatusEnum",
    "TaskStatusEnum",
    "PriorityEnum",
    # Export schemas
    "EntityCounts",
    "ExportMetadata",
    "ExportData",
    "ExportPreview",
]
