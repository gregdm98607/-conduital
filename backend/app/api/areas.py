"""
Area API endpoints
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.db_utils import get_or_create, soft_delete
from app.models.area import Area as AreaModel
from app.models.project import Project as ProjectModel
from app.schemas.area import Area, AreaCreate, AreaUpdate, AreaWithCounts, AreaWithProjects
from app.services.intelligence_service import IntelligenceService

router = APIRouter()


@router.get("", response_model=list[AreaWithCounts])
def list_areas(include_archived: bool = False, db: Session = Depends(get_db)):
    """List all areas with project counts"""
    from sqlalchemy import select, func, case

    # Get all areas (filter archived and soft-deleted by default)
    query = select(AreaModel).where(AreaModel.deleted_at.is_(None))
    if not include_archived:
        query = query.where(AreaModel.is_archived.is_(False))
    areas = db.execute(query).scalars().all()

    # Get total project counts per area (exclude soft-deleted projects)
    total_counts = db.execute(
        select(
            ProjectModel.area_id,
            func.count(ProjectModel.id).label('total')
        )
        .where(ProjectModel.area_id.isnot(None), ProjectModel.deleted_at.is_(None))
        .group_by(ProjectModel.area_id)
    ).all()

    # Get active project counts per area (exclude soft-deleted projects)
    active_counts = db.execute(
        select(
            ProjectModel.area_id,
            func.count(ProjectModel.id).label('active')
        )
        .where(ProjectModel.area_id.isnot(None), ProjectModel.deleted_at.is_(None))
        .where(ProjectModel.status == 'active')
        .group_by(ProjectModel.area_id)
    ).all()

    # Create lookup dicts for counts
    total_by_area = {row.area_id: row.total for row in total_counts}
    active_by_area = {row.area_id: row.active for row in active_counts}

    # Build response with counts
    result = []
    for area in areas:
        area_dict = {
            'id': area.id,
            'title': area.title,
            'description': area.description,
            'folder_path': area.folder_path,
            'standard_of_excellence': area.standard_of_excellence,
            'review_frequency': area.review_frequency,
            'last_reviewed_at': area.last_reviewed_at,
            'health_score': area.health_score,
            'is_archived': area.is_archived,
            'archived_at': area.archived_at,
            'created_at': area.created_at,
            'updated_at': area.updated_at,
            'project_count': total_by_area.get(area.id, 0),
            'active_project_count': active_by_area.get(area.id, 0),
        }
        result.append(area_dict)

    return result


@router.get("/{area_id}", response_model=AreaWithProjects)
def get_area(area_id: int, db: Session = Depends(get_db)):
    """Get a single area by ID with projects and computed counts"""
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    area = db.execute(
        select(AreaModel).where(AreaModel.id == area_id).options(joinedload(AreaModel.projects))
    ).unique().scalar_one_or_none()

    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    # Compute project counts
    projects = area.projects or []
    active_count = sum(1 for p in projects if p.status == "active")
    stalled_count = sum(1 for p in projects if p.stalled_since is not None)
    completed_count = sum(1 for p in projects if p.status == "completed")

    # Return area with computed fields
    return {
        "id": area.id,
        "title": area.title,
        "description": area.description,
        "folder_path": area.folder_path,
        "standard_of_excellence": area.standard_of_excellence,
        "review_frequency": area.review_frequency,
        "health_score": area.health_score,
        "is_archived": area.is_archived,
        "archived_at": area.archived_at,
        "last_reviewed_at": area.last_reviewed_at,
        "created_at": area.created_at,
        "updated_at": area.updated_at,
        "projects": projects,
        "active_projects_count": active_count,
        "stalled_projects_count": stalled_count,
        "completed_projects_count": completed_count,
    }


@router.post("", response_model=Area, status_code=201)
def create_area(area: AreaCreate, db: Session = Depends(get_db)):
    """Create a new area"""
    new_area = AreaModel(**area.model_dump())
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area


@router.put("/{area_id}", response_model=Area)
def update_area(area_id: int, area: AreaUpdate, db: Session = Depends(get_db)):
    """Update an area"""
    existing_area = db.get(AreaModel, area_id)
    if not existing_area:
        raise HTTPException(status_code=404, detail="Area not found")

    update_dict = area.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(existing_area, field, value)

    db.commit()
    db.refresh(existing_area)
    return existing_area


@router.delete("/{area_id}", status_code=204)
def delete_area(area_id: int, db: Session = Depends(get_db)):
    """Delete an area"""
    area = db.get(AreaModel, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    soft_delete(db, area)
    db.commit()
    return None


@router.post("/{area_id}/mark-reviewed", response_model=Area)
def mark_area_reviewed(area_id: int, db: Session = Depends(get_db)):
    """Mark an area as reviewed, updating last_reviewed_at timestamp"""
    area = db.get(AreaModel, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    area.last_reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(area)
    return area


@router.get("/{area_id}/health")
def get_area_health(area_id: int, db: Session = Depends(get_db)):
    """Get area health score breakdown"""
    from sqlalchemy import select
    from sqlalchemy.orm import joinedload

    area = db.execute(
        select(AreaModel).where(AreaModel.id == area_id).options(joinedload(AreaModel.projects))
    ).unique().scalar_one_or_none()

    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    breakdown = IntelligenceService.get_area_health_breakdown(db, area)
    breakdown["area_id"] = area.id
    breakdown["title"] = area.title
    return breakdown


@router.post("/{area_id}/archive", response_model=Area)
def archive_area(
    area_id: int,
    force: bool = False,
    db: Session = Depends(get_db),
):
    """Archive an area (soft delete).

    If the area has active projects, returns 409 unless force=True.
    When forced, active projects are set to on_hold status.
    """
    from sqlalchemy import select, func

    area = db.get(AreaModel, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    if area.is_archived:
        raise HTTPException(status_code=400, detail="Area is already archived")

    # Check for active projects belonging to this area
    active_count = db.execute(
        select(func.count(ProjectModel.id)).where(
            ProjectModel.area_id == area_id,
            ProjectModel.status == "active",
        )
    ).scalar_one()

    if active_count > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail=f"Area has {active_count} active project(s). Use force=true to archive anyway (projects will be set to on_hold).",
        )

    if active_count > 0 and force:
        # Set active projects to on_hold to prevent orphaning
        active_projects = db.execute(
            select(ProjectModel).where(
                ProjectModel.area_id == area_id,
                ProjectModel.status == "active",
            )
        ).scalars().all()
        for project in active_projects:
            project.status = "on_hold"
        logger.info(f"Set {active_count} active projects to on_hold for archived area {area_id}")

    area.is_archived = True
    area.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(area)
    return area


@router.post("/{area_id}/unarchive", response_model=Area)
def unarchive_area(area_id: int, db: Session = Depends(get_db)):
    """Unarchive an area"""
    area = db.get(AreaModel, area_id)
    if not area:
        raise HTTPException(status_code=404, detail="Area not found")

    if not area.is_archived:
        raise HTTPException(status_code=400, detail="Area is not archived")

    area.is_archived = False
    area.archived_at = None
    db.commit()
    db.refresh(area)
    return area
