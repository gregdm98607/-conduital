"""
Task API endpoints
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.task import Task, TaskCreate, TaskList, TaskListWithProjects, TaskUpdate, TaskWithProject
from app.services.task_service import TaskService

router = APIRouter()


@router.get("")
def list_tasks(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    context: Optional[str] = Query(None, description="Filter by context"),
    energy_level: Optional[str] = Query(None, description="Filter by energy level (high, medium, low)"),
    is_next_action: Optional[bool] = Query(None, description="Filter by next action flag"),
    priority_min: Optional[int] = Query(None, ge=1, le=10, description="Minimum priority (1-10)"),
    priority_max: Optional[int] = Query(None, ge=1, le=10, description="Maximum priority (1-10)"),
    include_project: bool = Query(False, description="Include project details for each task"),
    show_completed: bool = Query(False, description="Include completed tasks"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all tasks with optional filtering and pagination.
    Use include_project=true to get project details for each task.
    """
    skip = (page - 1) * page_size
    tasks, total = TaskService.get_all(
        db,
        project_id=project_id,
        status=status,
        context=context,
        energy_level=energy_level,
        is_next_action=is_next_action,
        priority_min=priority_min,
        priority_max=priority_max,
        include_project=include_project,
        show_completed=show_completed,
        skip=skip,
        limit=page_size,
    )

    has_more = (skip + len(tasks)) < total

    if include_project:
        return TaskListWithProjects(
            tasks=tasks,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
    return TaskList(
        tasks=tasks,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/overdue", response_model=list[Task])
def list_overdue_tasks(
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
):
    """
    Get all overdue tasks
    """
    return TaskService.get_overdue(db, limit=limit)


@router.get("/quick-wins", response_model=list[Task])
def list_quick_wins(
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
):
    """
    Get quick tasks (2 minutes or less)
    """
    return TaskService.get_two_minute_tasks(db, limit=limit)


@router.get("/by-context/{context}", response_model=list[Task])
def list_tasks_by_context(
    context: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
):
    """
    Get tasks filtered by specific context
    """
    return TaskService.get_by_context(db, context, limit=limit)


@router.get("/search", response_model=list[Task])
def search_tasks(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
):
    """
    Search tasks by title or description
    """
    return TaskService.search(db, search_term=q, limit=limit)


@router.get("/{task_id}", response_model=TaskWithProject)
def get_task(
    task_id: int,
    include_project: bool = Query(True, description="Include project details"),
    db: Session = Depends(get_db),
):
    """
    Get a single task by ID
    """
    task = TaskService.get_by_id(db, task_id, include_project=include_project)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("", response_model=Task, status_code=201)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new task
    """
    return TaskService.create(db, task)


@router.put("/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    task: TaskUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a task
    """
    updated_task = TaskService.update(db, task_id, task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@router.post("/{task_id}/complete", response_model=Task)
def complete_task(
    task_id: int,
    actual_minutes: Optional[int] = Query(None, description="Actual time taken (minutes)"),
    db: Session = Depends(get_db),
):
    """
    Mark a task as complete
    """
    completed_task = TaskService.complete(db, task_id, actual_minutes=actual_minutes)
    if not completed_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return completed_task


@router.post("/{task_id}/start", response_model=Task)
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Start a task (mark as in progress)
    """
    started_task = TaskService.start(db, task_id)
    if not started_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return started_task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a task
    """
    deleted = TaskService.delete(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return None
