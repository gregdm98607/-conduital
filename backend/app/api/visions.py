"""
Vision API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.vision import Vision as VisionModel
from app.schemas.vision import Vision, VisionCreate, VisionUpdate

router = APIRouter()


@router.get("", response_model=list[Vision])
def list_visions(db: Session = Depends(get_db)):
    """List all visions"""
    visions = db.execute(select(VisionModel)).scalars().all()
    return list(visions)


@router.get("/{vision_id}", response_model=Vision)
def get_vision(vision_id: int, db: Session = Depends(get_db)):
    """Get a single vision by ID"""
    vision = db.get(VisionModel, vision_id)
    if not vision:
        raise HTTPException(status_code=404, detail="Vision not found")
    return vision


@router.post("", response_model=Vision, status_code=201)
def create_vision(vision: VisionCreate, db: Session = Depends(get_db)):
    """Create a new vision"""
    new_vision = VisionModel(**vision.model_dump())
    db.add(new_vision)
    db.commit()
    db.refresh(new_vision)
    return new_vision


@router.put("/{vision_id}", response_model=Vision)
def update_vision(vision_id: int, vision: VisionUpdate, db: Session = Depends(get_db)):
    """Update a vision"""
    existing_vision = db.get(VisionModel, vision_id)
    if not existing_vision:
        raise HTTPException(status_code=404, detail="Vision not found")

    update_dict = vision.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(existing_vision, field, value)

    db.commit()
    db.refresh(existing_vision)
    return existing_vision


@router.delete("/{vision_id}", status_code=204)
def delete_vision(vision_id: int, db: Session = Depends(get_db)):
    """Delete a vision"""
    vision = db.get(VisionModel, vision_id)
    if not vision:
        raise HTTPException(status_code=404, detail="Vision not found")

    db.delete(vision)
    db.commit()
    return None
