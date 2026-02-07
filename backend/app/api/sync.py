"""
Sync API endpoints
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.models.sync_state import SyncState
from app.sync.sync_engine import SyncEngine, SyncConflict

router = APIRouter()


class SyncResponse(BaseModel):
    """Response model for sync operations"""

    success: bool
    message: str
    stats: dict = {}


class SyncStatusResponse(BaseModel):
    """Response model for sync status"""

    total_files: int
    synced: int
    pending: int
    conflicts: int
    errors: int
    files: list[dict] = []


@router.post("/scan", response_model=SyncResponse)
def scan_and_sync(
    discover_projects: bool = Query(
        False,
        description="Run project discovery before sync (finds projects by folder structure)"
    ),
    db: Session = Depends(get_db),
):
    """
    Scan Second Brain and sync all markdown files

    This will:
    1. (Optional) Discover projects by folder structure (xx.xx Project_Name)
    2. Find all markdown files in watched directories
    3. Parse and sync each file to database
    4. Create projects and tasks as needed
    5. Update sync state

    Args:
        discover_projects: If True, run project discovery first
    """
    try:
        stats = {}

        # Optional: Run discovery first
        if discover_projects:
            from app.services.discovery_service import ProjectDiscoveryService
            discovery = ProjectDiscoveryService(db)
            discovery_stats = discovery.discover_all_projects()
            stats["discovery"] = discovery_stats

        # Run regular sync
        engine = SyncEngine(db)
        sync_stats = engine.scan_and_sync()
        stats.update(sync_stats)

        message_parts = [f"Scanned {sync_stats['scanned']} files, synced {sync_stats['synced']}"]
        if discover_projects:
            message_parts.append(
                f"Discovered {discovery_stats['discovered']} folders, "
                f"imported {discovery_stats['imported']} projects"
            )

        return SyncResponse(
            success=True,
            message="; ".join(message_parts),
            stats=stats,
        )
    except Exception as e:
        logger.error(f"Scan and sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/project/{project_id}", response_model=SyncResponse)
def sync_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Sync a specific project to its file (Database → File)

    Updates the markdown file with current database state
    """
    try:
        engine = SyncEngine(db)
        success = engine.sync_project_to_file(project_id)

        if success:
            return SyncResponse(
                success=True,
                message=f"Project {project_id} synced to file",
            )
        else:
            raise HTTPException(status_code=404, detail="Project not found")

    except Exception as e:
        logger.error(f"Sync project {project_id} to file failed: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/file", response_model=SyncResponse)
def sync_file(
    file_path: str = Query(..., description="Path to file to sync"),
    db: Session = Depends(get_db),
):
    """
    Sync a specific file to database (File → Database)

    Parses the markdown file and updates/creates project in database
    """
    try:
        engine = SyncEngine(db)
        path = Path(file_path)

        project = engine.sync_file_to_database(path)

        if project:
            return SyncResponse(
                success=True,
                message=f"File synced: {project.title}",
                stats={"project_id": project.id},
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to sync file")

    except SyncConflict as e:
        logger.warning(f"Sync conflict detected for file {e.file_path}: {e}")
        raise HTTPException(
            status_code=409,
            detail={
                "error": "Sync conflict detected",
                "file_path": e.file_path,
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"Sync file failed for {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status", response_model=SyncStatusResponse)
def get_sync_status(
    limit: int = Query(100, ge=1, le=500, description="Maximum files to return"),
    db: Session = Depends(get_db),
):
    """
    Get sync status for all tracked files

    Shows:
    - Total files tracked
    - Sync status breakdown
    - Recent sync activity
    """
    # Get all sync states
    query = select(SyncState).order_by(SyncState.last_synced_at.desc()).limit(limit)
    sync_states = list(db.execute(query).scalars().all())

    # Calculate stats
    total = len(sync_states)
    synced = sum(1 for s in sync_states if s.sync_status == "synced")
    pending = sum(1 for s in sync_states if s.sync_status == "pending")
    conflicts = sum(1 for s in sync_states if s.sync_status == "conflict")
    errors = sum(1 for s in sync_states if s.sync_status == "error")

    # Format file list
    files = [
        {
            "file_path": s.file_path,
            "status": s.sync_status,
            "last_synced": s.last_synced_at.isoformat() if s.last_synced_at else None,
            "entity_type": s.entity_type,
            "entity_id": s.entity_id,
            "error_message": s.error_message,
        }
        for s in sync_states
    ]

    return SyncStatusResponse(
        total_files=total,
        synced=synced,
        pending=pending,
        conflicts=conflicts,
        errors=errors,
        files=files,
    )


@router.get("/conflicts", response_model=list[dict])
def get_conflicts(
    db: Session = Depends(get_db),
):
    """
    Get all files with sync conflicts

    Returns list of files that need manual conflict resolution
    """
    query = select(SyncState).where(SyncState.sync_status == "conflict")
    conflicts = list(db.execute(query).scalars().all())

    return [
        {
            "file_path": s.file_path,
            "last_synced": s.last_synced_at.isoformat() if s.last_synced_at else None,
            "entity_type": s.entity_type,
            "entity_id": s.entity_id,
        }
        for s in conflicts
    ]


@router.post("/resolve/{sync_id}", response_model=SyncResponse)
def resolve_conflict(
    sync_id: int,
    use_file: bool = Query(..., description="True to use file version, False for database version"),
    db: Session = Depends(get_db),
):
    """
    Resolve a sync conflict

    Args:
        sync_id: Sync state ID
        use_file: True to keep file version, False to keep database version
    """
    sync_state = db.get(SyncState, sync_id)
    if not sync_state:
        raise HTTPException(status_code=404, detail="Sync state not found")

    if sync_state.sync_status != "conflict":
        raise HTTPException(status_code=400, detail="No conflict to resolve")

    try:
        engine = SyncEngine(db)

        if use_file:
            # File wins - sync file to database
            path = Path(sync_state.file_path)
            project = engine.sync_file_to_database(path)
            message = f"Conflict resolved: using file version for {project.title}"
        else:
            # Database wins - sync database to file
            if not sync_state.entity_id:
                raise HTTPException(status_code=400, detail="No database entity linked")

            success = engine.sync_project_to_file(sync_state.entity_id)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to sync to file")

            message = f"Conflict resolved: using database version"

        return SyncResponse(success=True, message=message)

    except Exception as e:
        logger.error(f"Conflict resolution failed for sync_id {sync_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Resolution failed: {str(e)}")
