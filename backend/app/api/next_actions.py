"""
Next Actions API endpoints - Smart prioritization
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.task import DailyDashboardResponse, NextActionResponse, Task, TaskWithProject
from app.services.next_actions_service import NextActionsService

router = APIRouter()


@router.get("", response_model=NextActionResponse)
def get_next_actions(
    context: Optional[str] = Query(None, description="Filter by context"),
    energy_level: Optional[str] = Query(None, description="Filter by energy level"),
    time_available: Optional[int] = Query(None, ge=1, description="Available time (minutes)"),
    include_stalled: bool = Query(True, description="Include unstuck tasks from stalled projects"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
):
    """
    Get prioritized next actions based on momentum and context

    Prioritization logic:
    1. Stalled projects with unstuck tasks
    2. High momentum projects with approaching due dates
    3. Medium momentum projects
    4. Tasks already in progress (minimize context switching)
    5. Lower momentum projects

    Filters:
    - context: @creative, @administrative, @research, etc.
    - energy_level: high, medium, low
    - time_available: Show only tasks that fit in available time
    """
    tasks = NextActionsService.get_prioritized_next_actions(
        db,
        context=context,
        energy_level=energy_level,
        time_available=time_available,
        include_stalled=include_stalled,
        limit=limit,
    )

    stalled_count = NextActionsService.get_stalled_projects_count(db)

    return NextActionResponse(
        tasks=tasks,
        stalled_projects_count=stalled_count,
        context_filter=context,
        energy_filter=energy_level,
        time_available=time_available,
    )


@router.get("/by-context", response_model=dict[str, list[TaskWithProject]])
def get_next_actions_by_context(
    limit_per_context: int = Query(10, ge=1, le=50, description="Tasks per context"),
    db: Session = Depends(get_db),
):
    """
    Get next actions grouped by context

    Returns a dictionary mapping context names to lists of tasks
    Example: {"creative": [...], "administrative": [...]}
    """
    return NextActionsService.get_next_actions_by_context(db, limit_per_context=limit_per_context)


@router.get("/dashboard", response_model=DailyDashboardResponse)
def get_daily_dashboard(db: Session = Depends(get_db)):
    """
    Get daily dashboard data

    Returns:
    - top_3_priorities: Top 3 priority tasks for today
    - quick_wins: Quick tasks (< 15 min)
    - due_today: Tasks due today
    - stalled_projects_count: Number of stalled projects
    - top_momentum_projects: Projects with highest momentum
    """
    return NextActionsService.get_daily_dashboard(db)
