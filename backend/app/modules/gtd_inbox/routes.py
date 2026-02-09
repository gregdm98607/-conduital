"""
Inbox module routes

Provides workflow endpoints:
- Inbox processing
- Weekly review
- Waiting-for management
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db

# Import the existing inbox router to re-expose
from app.api import inbox

# Create module router
router = APIRouter()

# Include the existing inbox endpoints under this module
# The inbox router is now gated by the gtd_inbox module being enabled
router.include_router(inbox.router, prefix="/inbox", tags=["Inbox"])


# --- Weekly Review Schemas ---

class WeeklyReviewCompleteRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=5000, description="Optional notes about the review")


class WeeklyReviewCompletionResponse(BaseModel):
    id: int
    completed_at: str
    notes: Optional[str] = None


class WeeklyReviewHistoryResponse(BaseModel):
    completions: list[WeeklyReviewCompletionResponse]
    last_completed_at: Optional[str] = None
    days_since_last_review: Optional[int] = None


# --- Weekly Review Endpoints ---

@router.get("/weekly-review")
async def get_weekly_review_data(db: Session = Depends(get_db)):
    """
    Get data for weekly review.

    This aggregates:
    - Projects without next actions
    - Stalled projects
    - Waiting-for items due for follow-up
    - Someday/maybe items to review
    - Completed items this week
    """
    from app.services.intelligence_service import IntelligenceService

    review_data = IntelligenceService.get_weekly_review_data(db)
    return review_data


@router.post("/weekly-review/complete", response_model=WeeklyReviewCompletionResponse)
async def mark_weekly_review_complete(
    body: Optional[WeeklyReviewCompleteRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Mark weekly review as complete.

    Persists a completion timestamp. BETA-030.
    """
    from app.models.weekly_review import WeeklyReviewCompletion

    completion = WeeklyReviewCompletion(
        completed_at=datetime.now(timezone.utc),
        notes=body.notes if body else None,
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)

    return WeeklyReviewCompletionResponse(
        id=completion.id,
        completed_at=completion.completed_at.isoformat(),
        notes=completion.notes,
    )


@router.get("/weekly-review/history", response_model=WeeklyReviewHistoryResponse)
async def get_weekly_review_history(
    limit: int = Query(10, ge=1, le=52, description="Number of completions to return"),
    db: Session = Depends(get_db),
):
    """
    Get weekly review completion history.

    Returns recent completions and days since last review.
    """
    from app.models.weekly_review import WeeklyReviewCompletion

    completions = db.execute(
        select(WeeklyReviewCompletion)
        .order_by(WeeklyReviewCompletion.completed_at.desc())
        .limit(limit)
    ).scalars().all()

    last_completed_at = None
    days_since = None
    if completions:
        last_dt = completions[0].completed_at
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        last_completed_at = last_dt.isoformat()
        days_since = (datetime.now(timezone.utc) - last_dt).days

    return WeeklyReviewHistoryResponse(
        completions=[
            WeeklyReviewCompletionResponse(
                id=c.id,
                completed_at=c.completed_at.isoformat() if c.completed_at else "",
                notes=c.notes,
            )
            for c in completions
        ],
        last_completed_at=last_completed_at,
        days_since_last_review=days_since,
    )


@router.get("/waiting-for")
async def get_waiting_for_items(
    include_overdue: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all waiting-for items.

    Waiting-for items are tasks delegated to others or dependent
    on external events.
    """
    from app.services.task_service import TaskService

    tasks = TaskService.get_waiting_for_tasks(db, include_overdue=include_overdue)
    return {"items": tasks, "count": len(tasks)}


@router.get("/someday-maybe")
async def get_someday_maybe_items(db: Session = Depends(get_db)):
    """
    Get someday/maybe projects and tasks.

    These are items not committed to but worth reviewing periodically.
    """
    from app.models.project import Project
    from app.models.task import Task
    from app.schemas.project import ProjectResponse
    from app.schemas.task import TaskResponse

    # Get someday/maybe projects
    projects = db.query(Project).filter(
        Project.status == "someday_maybe"
    ).all()

    # Get someday/maybe tasks (standalone, not in projects)
    tasks = db.query(Task).filter(
        Task.task_type == "someday_maybe"
    ).all()

    return {
        "projects": [ProjectResponse.model_validate(p) for p in projects],
        "tasks": [TaskResponse.model_validate(t) for t in tasks],
    }
