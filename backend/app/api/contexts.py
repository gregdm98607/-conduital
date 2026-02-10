"""
Context API endpoints
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.context import Context as ContextModel
from app.schemas.context import Context, ContextCreate, ContextUpdate

logger = logging.getLogger(__name__)

router = APIRouter()

# Default contexts seeded on first startup (matches task context pick list)
_DEFAULT_CONTEXTS = [
    {"name": "work", "context_type": "location", "description": "Work environment tasks"},
    {"name": "home", "context_type": "location", "description": "Tasks to do at home"},
    {"name": "computer", "context_type": "tool", "description": "Tasks requiring a computer"},
    {"name": "phone", "context_type": "tool", "description": "Tasks requiring a phone"},
    {"name": "errands", "context_type": "location", "description": "Tasks requiring going out"},
    {"name": "reading", "context_type": "energy", "description": "Reading and review tasks"},
]


def seed_default_contexts(db: Session) -> None:
    """Seed the contexts table with defaults if empty. Runs once on first startup."""
    count = db.scalar(select(func.count()).select_from(ContextModel))
    if count and count > 0:
        return
    for ctx_data in _DEFAULT_CONTEXTS:
        db.add(ContextModel(**ctx_data))
    db.commit()
    logger.info("Seeded %d default contexts", len(_DEFAULT_CONTEXTS))


@router.get("", response_model=list[Context])
def list_contexts(db: Session = Depends(get_db)):
    """List all contexts"""
    contexts = db.execute(select(ContextModel).order_by(ContextModel.name)).scalars().all()
    return list(contexts)


@router.get("/{context_id}", response_model=Context)
def get_context(context_id: int, db: Session = Depends(get_db)):
    """Get a single context by ID"""
    context = db.get(ContextModel, context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    return context


@router.post("", response_model=Context, status_code=201)
def create_context(context: ContextCreate, db: Session = Depends(get_db)):
    """Create a new context"""
    new_context = ContextModel(**context.model_dump())
    db.add(new_context)
    db.commit()
    db.refresh(new_context)
    return new_context


@router.put("/{context_id}", response_model=Context)
def update_context(context_id: int, context: ContextUpdate, db: Session = Depends(get_db)):
    """Update a context"""
    existing_context = db.get(ContextModel, context_id)
    if not existing_context:
        raise HTTPException(status_code=404, detail="Context not found")

    update_dict = context.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(existing_context, field, value)

    db.commit()
    db.refresh(existing_context)
    return existing_context


@router.delete("/{context_id}", status_code=204)
def delete_context(context_id: int, db: Session = Depends(get_db)):
    """Delete a context"""
    context = db.get(ContextModel, context_id)
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")

    db.delete(context)
    db.commit()
    return None
