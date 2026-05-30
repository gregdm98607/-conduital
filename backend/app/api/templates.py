"""
Starter Template API endpoints (BACKLOG-087).

Read-only gallery (`GET`) plus a one-click `apply` that scaffolds Areas,
Projects (with phases) and starter Tasks for a new user. Mirrors the thin
router → service pattern used by ``projects.py``.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.template import TemplateApplyResult, TemplateDetail, TemplateList
from app.services.template_service import TemplateService

router = APIRouter()


@router.get("", response_model=TemplateList)
def list_templates():
    """List available starter templates with preview counts."""
    return TemplateList(templates=TemplateService.list_templates())


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str):
    """Get a single template's full preview (areas, projects, phases, tasks)."""
    detail = TemplateService.get_template(template_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return detail


@router.post("/{template_id}/apply", response_model=TemplateApplyResult, status_code=201)
def apply_template(template_id: str, db: Session = Depends(get_db)):
    """Apply a template, creating its areas, projects, phases and tasks."""
    result = TemplateService.apply_template(db, template_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return result
