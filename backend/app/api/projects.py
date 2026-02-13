"""
Project API endpoints
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.project import Project as ProjectModel
from app.schemas.project import (
    Project,
    ProjectCreate,
    ProjectHealth,
    ProjectList,
    ProjectUpdate,
    ProjectWithTasks,
)
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("", response_model=ProjectList)
def list_projects(
    status: Optional[str] = Query(None, description="Filter by status"),
    area_id: Optional[int] = Query(None, description="Filter by area ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    List all projects with optional filtering and pagination
    """
    skip = (page - 1) * page_size
    projects, total = ProjectService.get_all(
        db, status=status, area_id=area_id, skip=skip, limit=page_size
    )

    has_more = (skip + len(projects)) < total

    return ProjectList(
        projects=projects,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.get("/stalled", response_model=list[Project])
def list_stalled_projects(db: Session = Depends(get_db)):
    """
    Get all stalled projects (no activity for 14+ days)
    """
    return ProjectService.get_stalled_projects(db)


@router.get("/search", response_model=list[Project])
def search_projects(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db),
):
    """
    Search projects by title or description
    """
    return ProjectService.search(db, search_term=q, limit=limit)


@router.get("/{project_id}", response_model=ProjectWithTasks)
def get_project(
    project_id: int,
    include_tasks: bool = Query(True, description="Include tasks"),
    db: Session = Depends(get_db),
):
    """
    Get a single project by ID
    """
    project = ProjectService.get_by_id(db, project_id, include_tasks=include_tasks)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", response_model=Project, status_code=201)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new project
    """
    return ProjectService.create(db, project)


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a project
    """
    updated_project = ProjectService.update(db, project_id, project)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project


@router.patch("/{project_id}/status", response_model=Project)
def change_project_status(
    project_id: int,
    status: str = Query(..., description="New status"),
    db: Session = Depends(get_db),
):
    """
    Change project status
    """
    updated_project = ProjectService.change_status(db, project_id, status)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project


@router.get("/{project_id}/health", response_model=ProjectHealth)
def get_project_health(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get project health metrics
    """
    health = ProjectService.get_health(db, project_id)
    if not health:
        raise HTTPException(status_code=404, detail="Project not found")
    return health


@router.post("/{project_id}/mark-reviewed", response_model=Project)
def mark_project_reviewed(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Mark a project as reviewed, updating last_reviewed_at timestamp
    """
    project = db.get(ProjectModel, project_id)
    if not project or project.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Project not found")

    project.last_reviewed_at = datetime.now(timezone.utc)

    # Auto-calculate next review date from review_frequency
    freq_days = {"daily": 1, "weekly": 7, "monthly": 30}
    days = freq_days.get(project.review_frequency, 7)
    project.next_review_date = date.today() + timedelta(days=days)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a project
    """
    deleted = ProjectService.delete(db, project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
    return None
