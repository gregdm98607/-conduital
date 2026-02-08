"""
Project Discovery API

Endpoints for discovering projects from folder structure and managing area mappings.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.services.discovery_service import ProjectDiscoveryService
from app.services.area_discovery_service import AreaDiscoveryService

router = APIRouter(prefix="/discovery", tags=["discovery"])


class DiscoveryStats(BaseModel):
    """Statistics from project discovery"""
    success: bool
    discovered: int = Field(..., description="Number of folders discovered")
    imported: int = Field(..., description="Number of projects imported")
    skipped: int = Field(..., description="Number of projects skipped")
    errors: list[dict] = Field(default_factory=list, description="List of errors encountered")


class AreaMapping(BaseModel):
    """Area prefix mapping"""
    prefix: str = Field(..., description="Two-digit prefix (e.g., '01')")
    area_name: str = Field(..., description="Area name (e.g., 'Literary Projects')")


class AreaMappingUpdate(BaseModel):
    """Update area prefix mappings"""
    mappings: dict[str, str] = Field(
        ...,
        description="Dictionary of prefix to area name",
        examples=[{"01": "Literary Projects", "10": "Tech Projects"}]
    )


class SuggestionResult(BaseModel):
    """Suggested area mappings for unmapped prefixes"""
    unmapped_prefixes: dict[str, dict]


@router.post("/scan", response_model=DiscoveryStats)
def discover_projects(db: Session = Depends(get_db)):
    """
    Scan 10_Projects directory and discover all projects.

    This will:
    1. Find all folders matching pattern: xx.xx Project_Name
    2. Map prefixes to areas using configured mappings
    3. Create/update projects in database
    4. Sync markdown files if present

    Returns:
        DiscoveryStats: Statistics about discovery process
    """
    service = ProjectDiscoveryService(db)
    stats = service.discover_all_projects()

    if not stats["success"]:
        raise HTTPException(status_code=500, detail=stats.get("error", "Discovery failed"))

    return stats


@router.get("/mappings", response_model=dict[str, str])
def get_area_mappings(db: Session = Depends(get_db)):
    """
    Get current area prefix mappings.

    Returns:
        dict: Mapping of prefix to area name
    """
    service = ProjectDiscoveryService(db)
    return service.get_area_mappings()


@router.post("/mappings")
def update_area_mappings(
    mappings: dict[str, str] = Body(..., examples=[{"01": "Literary Projects"}]),
    db: Session = Depends(get_db)
):
    """
    Update area prefix mappings.

    Note: This currently updates runtime configuration only.
    To persist changes, update the .env file or Settings.

    Args:
        mappings: Dictionary of prefix to area name

    Returns:
        dict: Success message with updated mappings
    """
    from app.core.config import settings

    # Validate prefixes are 2 digits
    for prefix in mappings.keys():
        if not prefix.isdigit() or len(prefix) != 2:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid prefix '{prefix}'. Must be 2 digits (e.g., '01', '10')"
            )

    # Update runtime settings
    settings.AREA_PREFIX_MAP = mappings

    return {
        "success": True,
        "message": "Area mappings updated (runtime only - update .env to persist)",
        "mappings": mappings,
        "note": "Run /discovery/scan to apply new mappings to projects"
    }


@router.get("/suggestions", response_model=SuggestionResult)
def suggest_area_mappings(db: Session = Depends(get_db)):
    """
    Analyze project folders and suggest area mappings for unmapped prefixes.

    Returns:
        SuggestionResult: Unmapped prefixes with project samples
    """
    service = ProjectDiscoveryService(db)
    suggestions = service.suggest_area_mappings()

    return {
        "unmapped_prefixes": suggestions
    }


@router.post("/scan-folder")
def scan_specific_folder(
    folder_name: str = Body(..., embed=True, examples=["01.01 The_Lund_Covenant"]),
    db: Session = Depends(get_db)
):
    """
    Scan a specific project folder and import it.

    Args:
        folder_name: Name of the folder to scan (e.g., "01.01 The_Lund_Covenant")

    Returns:
        dict: Import result
    """
    from pathlib import Path
    from app.core.config import settings

    service = ProjectDiscoveryService(db)
    folder_path = settings.SECOND_BRAIN_PATH / "10_Projects" / folder_name

    if not folder_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Folder not found: {folder_name}"
        )

    try:
        result = service._process_project_folder(folder_path)
        return {
            "success": True,
            "folder": folder_name,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing project folder {folder_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing folder: {str(e)}"
        )


# Area Discovery Endpoints

@router.post("/scan-areas", response_model=DiscoveryStats)
def discover_areas(db: Session = Depends(get_db)):
    """
    Scan 20_Areas directory and discover all areas.

    This will:
    1. Find all folders matching pattern: xx.xx Area_Name
    2. Parse area markdown files for metadata
    3. Create/update areas in database

    Returns:
        DiscoveryStats: Statistics about discovery process
    """
    service = AreaDiscoveryService(db)
    stats = service.discover_all_areas()

    if not stats["success"]:
        raise HTTPException(status_code=500, detail=stats.get("error", "Area discovery failed"))

    return stats


@router.post("/scan-area-folder")
def scan_specific_area_folder(
    folder_name: str = Body(..., embed=True, examples=["20.05 AI_Systems"]),
    db: Session = Depends(get_db)
):
    """
    Scan a specific area folder and import it.

    Args:
        folder_name: Name of the folder to scan (e.g., "20.05 AI_Systems")

    Returns:
        dict: Import result
    """
    from pathlib import Path
    from app.core.config import settings

    service = AreaDiscoveryService(db)
    folder_path = settings.SECOND_BRAIN_PATH / "20_Areas" / folder_name

    if not folder_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Folder not found: {folder_name}"
        )

    try:
        result = service._process_area_folder(folder_path)
        return {
            "success": True,
            "folder": folder_name,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error processing area folder {folder_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing folder: {str(e)}"
        )


@router.get("/area-suggestions", response_model=SuggestionResult)
def suggest_unmapped_areas(db: Session = Depends(get_db)):
    """
    Analyze area folders and suggest areas that are not yet in the database.

    Returns:
        SuggestionResult: Unmapped area folders with details
    """
    service = AreaDiscoveryService(db)
    suggestions = service.suggest_area_mappings()

    return {
        "unmapped_prefixes": suggestions
    }
