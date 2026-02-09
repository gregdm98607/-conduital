"""
Inbox module routes

Provides workflow endpoints:
- Inbox processing
- Weekly review
- Waiting-for management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

# Import the existing inbox router to re-expose
from app.api import inbox

# Create module router
router = APIRouter()

# Include the existing inbox endpoints under this module
# The inbox router is now gated by the gtd_inbox module being enabled
router.include_router(inbox.router, prefix="/inbox", tags=["Inbox"])


# Additional workflow endpoints can be added here

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


@router.post("/weekly-review/complete")
async def mark_weekly_review_complete(db: Session = Depends(get_db)):
    """
    Mark weekly review as complete.

    This updates the last review timestamp and can trigger
    any post-review automation.
    """
    # TODO: Implement review completion tracking
    return {"status": "completed", "message": "Weekly review marked complete"}


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
