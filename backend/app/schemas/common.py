"""
Common schemas and enums
"""

from enum import Enum


def strip_whitespace(v: str | None) -> str | None:
    """Strip leading/trailing whitespace from string values.

    Used as a Pydantic field_validator to reject whitespace-only strings.
    When combined with min_length=1 on the Field, this ensures "   " is
    rejected (strips to "" which fails min_length).
    """
    if v is not None:
        return v.strip()
    return v


class StatusEnum(str, Enum):
    """Project status values"""

    ACTIVE = "active"
    ON_HOLD = "on_hold"
    SOMEDAY_MAYBE = "someday_maybe"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    STALLED = "stalled"


class TaskStatusEnum(str, Enum):
    """Task status values"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskTypeEnum(str, Enum):
    """Task type values"""

    ACTION = "action"
    MILESTONE = "milestone"
    WAITING_FOR = "waiting_for"
    SOMEDAY_MAYBE = "someday_maybe"


class PriorityEnum(int, Enum):
    """Priority values (1 is highest, 10 is lowest)"""

    CRITICAL = 1
    VERY_HIGH = 2
    HIGH = 3
    MEDIUM_HIGH = 4
    MEDIUM = 5
    MEDIUM_LOW = 6
    LOW = 7
    VERY_LOW = 8
    MINIMAL = 9
    NONE = 10


class EnergyLevelEnum(str, Enum):
    """Energy level values"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContextTypeEnum(str, Enum):
    """Context type values"""

    LOCATION = "location"
    ENERGY = "energy"
    WORK_TYPE = "work_type"
    TIME = "time"
    TOOL = "tool"


class SyncStatusEnum(str, Enum):
    """Sync status values"""

    SYNCED = "synced"
    PENDING = "pending"
    CONFLICT = "conflict"
    ERROR = "error"


class InboxResultTypeEnum(str, Enum):
    """Inbox processing result types"""

    TASK = "task"
    PROJECT = "project"
    REFERENCE = "reference"
    TRASH = "trash"


class UrgencyZoneEnum(str, Enum):
    """MYN Urgency Zone values

    Manage Your Now (MYN) methodology zones:
    - Critical Now: Must do today, non-negotiable commitments
    - Opportunity Now: Could do today, working inventory
    - Over the Horizon: Not for today, future tasks
    """

    CRITICAL_NOW = "critical_now"
    OPPORTUNITY_NOW = "opportunity_now"
    OVER_THE_HORIZON = "over_the_horizon"


class ReviewFrequencyEnum(str, Enum):
    """Review frequency values for areas"""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class GoalTimeframeEnum(str, Enum):
    """Goal timeframe values"""

    ONE_YEAR = "1_year"
    TWO_YEAR = "2_year"
    THREE_YEAR = "3_year"


class VisionTimeframeEnum(str, Enum):
    """Vision timeframe values"""

    THREE_YEAR = "3_year"
    FIVE_YEAR = "5_year"
    LIFE_PURPOSE = "life_purpose"


class GoalStatusEnum(str, Enum):
    """Goal status values"""

    ACTIVE = "active"
    ACHIEVED = "achieved"
    DEFERRED = "deferred"
    ABANDONED = "abandoned"
