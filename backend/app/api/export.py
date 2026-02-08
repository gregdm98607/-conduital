"""
Export API endpoints for data export and backup

BACKLOG-074: Data portability promise for R1 release.
BACKLOG-081: Context export for AI sessions.

Endpoints:
- GET /export/preview - Get export preview (counts, size estimate)
- GET /export/json - Download full JSON export
- GET /export/backup - Download SQLite database backup
- GET /export/ai-context - Generate AI session context (markdown)
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.project import Project
from app.models.area import Area
from app.models.goal import Goal
from app.models.vision import Vision
from app.schemas.export import ExportData, ExportPreview
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/preview", response_model=ExportPreview)
def get_export_preview(db: Session = Depends(get_db)):
    """
    Get a preview of what would be exported.

    Returns entity counts and estimated export size without
    performing the actual export. Use this to show the user
    what will be exported before they initiate the download.
    """
    return ExportService.get_export_preview(db)


@router.get("/json")
def export_json(db: Session = Depends(get_db)):
    """
    Export all data as JSON.

    Returns a downloadable JSON file containing:
    - Export metadata (version, timestamp, entity counts)
    - All areas
    - All goals
    - All visions
    - All contexts
    - All projects with nested tasks
    - All inbox items

    The export format is versioned for future import compatibility.
    """
    try:
        export_data = ExportService.export_full_json(db)

        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"conduital_export_{timestamp}.json"

        # Convert to dict for JSON response
        # Using model_dump() instead of .dict() (Pydantic v2)
        data_dict = export_data.model_dump(mode="json")

        return JSONResponse(
            content=data_dict,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Export-Version": ExportService.EXPORT_VERSION,
            },
        )

    except Exception as e:
        logger.exception("Failed to export JSON")
        raise HTTPException(
            status_code=500,
            detail=f"Export failed: {str(e)}",
        )


@router.get("/backup")
def export_database_backup():
    """
    Download a backup copy of the SQLite database.

    Creates a point-in-time copy of the database file.
    This is the most complete backup option as it includes
    the exact database state including any data not covered
    by the JSON export.

    Note: The backup file is temporary and will be deleted
    after download.
    """
    try:
        backup_path = ExportService.create_database_backup()

        # Generate filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"conduital_backup_{timestamp}.db"

        # Return file for download
        # background=BackgroundTask will delete file after response is sent
        from starlette.background import BackgroundTask

        def cleanup_backup(path):
            """Remove temporary backup files after download"""
            try:
                os.unlink(path)
                # Also clean up WAL/SHM if they exist
                wal_path = str(path) + "-wal"
                shm_path = str(path) + "-shm"
                if os.path.exists(wal_path):
                    os.unlink(wal_path)
                if os.path.exists(shm_path):
                    os.unlink(shm_path)
                logger.debug(f"Cleaned up backup files: {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup backup file {path}: {e}")

        return FileResponse(
            path=str(backup_path),
            filename=filename,
            media_type="application/x-sqlite3",
            background=BackgroundTask(cleanup_backup, backup_path),
        )

    except FileNotFoundError as e:
        logger.error(f"Database file not found: {e}")
        raise HTTPException(
            status_code=404,
            detail="Database file not found",
        )
    except Exception as e:
        logger.exception("Failed to create database backup")
        raise HTTPException(
            status_code=500,
            detail=f"Backup failed: {str(e)}",
        )


class AIContextResponse(BaseModel):
    """AI context export response"""
    context: str
    project_count: int
    task_count: int
    area_count: int


@router.get("/ai-context", response_model=AIContextResponse)
def export_ai_context(
    project_id: Optional[int] = Query(None, description="Export context for a specific project"),
    area_id: Optional[int] = Query(None, description="Export context for a specific area"),
    db: Session = Depends(get_db),
):
    """
    Generate structured markdown context for AI chat sessions.

    Collects active projects, tasks, areas, goals, and visions into
    a concise markdown format optimized for pasting into AI conversations.

    Optional filters:
    - project_id: Focus on a single project with full detail
    - area_id: Focus on all projects within an area
    """
    try:
        lines: list[str] = []
        now = datetime.now(timezone.utc)
        p_count = 0
        t_count = 0
        a_count = 0

        if project_id:
            # Single project export
            project = db.execute(
                select(Project)
                .options(joinedload(Project.tasks))
                .where(Project.id == project_id)
            ).unique().scalar_one_or_none()

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            lines.append(f"# AI Context: {project.title}")
            lines.append(f"**Exported:** {now.strftime('%Y-%m-%d %H:%M UTC')}")
            lines.append("")
            lines.extend(_format_project_detail(project))
            p_count = 1
            t_count = len(project.tasks) if project.tasks else 0

        elif area_id:
            # Area-focused export
            area = db.execute(
                select(Area)
                .options(joinedload(Area.projects).joinedload(Project.tasks))
                .where(Area.id == area_id)
            ).unique().scalar_one_or_none()

            if not area:
                raise HTTPException(status_code=404, detail="Area not found")

            lines.append(f"# AI Context: {area.title} (Area)")
            lines.append(f"**Exported:** {now.strftime('%Y-%m-%d %H:%M UTC')}")
            lines.append("")
            lines.extend(_format_area_detail(area))
            a_count = 1
            active_projects = [p for p in (area.projects or []) if p.status == "active"]
            p_count = len(active_projects)
            t_count = sum(len(p.tasks or []) for p in active_projects)

        else:
            # Full overview export
            lines.append("# Conduital AI Context")
            lines.append(f"**Exported:** {now.strftime('%Y-%m-%d %H:%M UTC')}")
            lines.append("")

            # Fetch all active projects once (reused for counts and stalled section)
            all_active = db.execute(
                select(Project)
                .options(joinedload(Project.tasks))
                .where(Project.status == "active")
            ).unique().scalars().all()

            active_count = len(all_active)
            stalled_count = len([p for p in all_active if p.stalled_since])

            lines.append(f"**Active Projects:** {active_count} | **Stalled:** {stalled_count}")
            lines.append("")

            # Visions
            visions = db.execute(
                select(Vision).order_by(Vision.title)
            ).scalars().all()
            if visions:
                lines.append("## Visions")
                for v in visions:
                    lines.append(f"- **{v.title}**" + (f" ({v.timeframe})" if v.timeframe else ""))
                    if v.description:
                        lines.append(f"  {v.description[:200]}")
                lines.append("")

            # Goals
            goals = db.execute(
                select(Goal).where(Goal.status == "active").order_by(Goal.title)
            ).scalars().all()
            if goals:
                lines.append("## Active Goals")
                for g in goals:
                    line = f"- **{g.title}**"
                    if g.target_date:
                        line += f" (target: {g.target_date})"
                    lines.append(line)
                    if g.description:
                        lines.append(f"  {g.description[:200]}")
                lines.append("")

            # Areas with projects
            areas = db.execute(
                select(Area)
                .options(joinedload(Area.projects).joinedload(Project.tasks))
                .where(Area.is_archived.is_(False))
                .order_by(Area.title)
            ).unique().scalars().all()

            if areas:
                lines.append("## Areas of Responsibility")
                for area in areas:
                    lines.extend(_format_area_summary(area))
                lines.append("")
                a_count = len(areas)

            # Orphan projects (no area)
            orphan_projects = db.execute(
                select(Project)
                .options(joinedload(Project.tasks))
                .where(Project.status == "active", Project.area_id.is_(None))
                .order_by(Project.title)
            ).unique().scalars().all()

            if orphan_projects:
                lines.append("## Unassigned Projects")
                for p in orphan_projects:
                    lines.extend(_format_project_summary(p))
                lines.append("")

            # Stalled projects highlight (derived from all_active)
            stalled = sorted(
                [p for p in all_active if p.stalled_since],
                key=lambda p: p.stalled_since,
            )

            if stalled:
                lines.append("## Stalled Projects (Need Attention)")
                for p in stalled:
                    days = (now - p.stalled_since).days if p.stalled_since else 0
                    total = len(p.tasks or [])
                    done = len([t for t in (p.tasks or []) if t.status == "completed"])
                    next_actions = len([t for t in (p.tasks or []) if t.is_next_action and t.status != "completed"])
                    lines.append(f"- **{p.title}** - stalled {days}d | momentum: {p.momentum_score or 0:.2f} | tasks: {done}/{total} | next actions: {next_actions}")
                lines.append("")

            # Count totals (from all_active fetched above)
            p_count = len(all_active)
            t_count = sum(len(p.tasks or []) for p in all_active)

        context_text = "\n".join(lines)

        return AIContextResponse(
            context=context_text,
            project_count=p_count,
            task_count=t_count,
            area_count=a_count,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate AI context export")
        raise HTTPException(status_code=500, detail=f"Context export failed: {str(e)}")


def _format_project_detail(project: Project) -> list[str]:
    """Format a single project with full detail for AI context."""
    lines: list[str] = []
    lines.append(f"## {project.title}")
    lines.append(f"**Status:** {project.status} | **Momentum:** {project.momentum_score or 0:.2f}")

    if project.purpose:
        lines.append(f"**Purpose:** {project.purpose}")
    if project.outcome_statement:
        lines.append(f"**Outcome:** {project.outcome_statement}")
    if project.vision_statement:
        lines.append(f"**Vision:** {project.vision_statement}")
    lines.append("")

    if project.brainstorm_notes:
        lines.append("### Brainstorm Notes")
        lines.append(project.brainstorm_notes[:500])
        lines.append("")

    if project.organizing_notes:
        lines.append("### Organizing Notes")
        lines.append(project.organizing_notes[:500])
        lines.append("")

    tasks = project.tasks or []
    active_tasks = [t for t in tasks if t.status != "completed"]
    completed_tasks = [t for t in tasks if t.status == "completed"]
    next_actions = [t for t in active_tasks if t.is_next_action]

    lines.append(f"### Tasks ({len(completed_tasks)}/{len(tasks)} completed)")

    if next_actions:
        lines.append("**Next Actions:**")
        for t in next_actions:
            due = f" (due: {t.due_date})" if t.due_date else ""
            lines.append(f"- [ ] {t.title}{due}")

    remaining = [t for t in active_tasks if not t.is_next_action]
    if remaining:
        lines.append("**Pending:**")
        for t in remaining[:10]:  # Limit to 10
            lines.append(f"- [ ] {t.title}")
        if len(remaining) > 10:
            lines.append(f"- ... and {len(remaining) - 10} more")

    if completed_tasks:
        lines.append(f"**Completed:** {len(completed_tasks)} tasks")

    lines.append("")
    return lines


def _format_area_detail(area: Area) -> list[str]:
    """Format an area with all projects for AI context."""
    lines: list[str] = []
    lines.append(f"## {area.title}")
    if area.health_score is not None:
        lines.append(f"**Health Score:** {area.health_score:.2f}")
    if area.standard_of_excellence:
        lines.append(f"**Standard of Excellence:** {area.standard_of_excellence}")
    if area.description:
        lines.append(f"**Description:** {area.description}")
    lines.append("")

    active_projects = [p for p in (area.projects or []) if p.status == "active"]
    if active_projects:
        lines.append(f"### Active Projects ({len(active_projects)})")
        for p in sorted(active_projects, key=lambda x: x.momentum_score or 0, reverse=True):
            lines.extend(_format_project_detail(p))
    else:
        lines.append("*No active projects*")

    return lines


def _format_area_summary(area: Area) -> list[str]:
    """Format an area summary for the overview export."""
    lines: list[str] = []
    active = [p for p in (area.projects or []) if p.status == "active"]
    health = f" | health: {area.health_score:.2f}" if area.health_score is not None else ""
    lines.append(f"### {area.title} ({len(active)} active projects{health})")
    if area.standard_of_excellence:
        lines.append(f"*Standard:* {area.standard_of_excellence[:150]}")

    for p in sorted(active, key=lambda x: x.momentum_score or 0, reverse=True):
        lines.extend(_format_project_summary(p))

    return lines


def _format_project_summary(project: Project) -> list[str]:
    """Format a project summary line for the overview export."""
    lines: list[str] = []
    tasks = project.tasks or []
    total = len(tasks)
    done = len([t for t in tasks if t.status == "completed"])
    next_actions = len([t for t in tasks if t.is_next_action and t.status != "completed"])
    momentum = project.momentum_score or 0

    status_icon = "!" if project.stalled_since else ""
    lines.append(f"- {status_icon}**{project.title}** | momentum: {momentum:.2f} | tasks: {done}/{total} | next actions: {next_actions}")
    if project.outcome_statement:
        lines.append(f"  *Outcome: {project.outcome_statement[:120]}*")

    return lines
