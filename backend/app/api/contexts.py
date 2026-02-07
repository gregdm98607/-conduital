"""
Context API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.context import Context as ContextModel
from app.schemas.context import Context, ContextCreate, ContextUpdate

router = APIRouter()


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
