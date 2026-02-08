"""
Inbox API endpoints - Quick Capture
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.inbox import InboxItem as InboxItemModel
from app.models.project import Project
from app.models.task import Task
from app.schemas.inbox import InboxItem, InboxItemCreate, InboxItemProcess, InboxItemUpdate

router = APIRouter()


def _resolve_result_title(item: InboxItemModel, db: Session) -> Optional[str]:
    """Resolve the title of the entity created from an inbox item."""
    if not item.result_id or not item.result_type:
        return None
    if item.result_type == "task":
        task = db.get(Task, item.result_id)
        return task.title if task else None
    elif item.result_type == "project":
        project = db.get(Project, item.result_id)
        return project.title if project else None
    return None


def _to_response(item: InboxItemModel, db: Session) -> dict:
    """Convert an inbox item model to a response dict with result_title."""
    result_project_id = None
    if item.result_type == "task" and item.result_id:
        task = db.get(Task, item.result_id)
        if task:
            result_project_id = task.project_id

    data = {
        "id": item.id,
        "content": item.content,
        "source": item.source,
        "captured_at": item.captured_at,
        "processed_at": item.processed_at,
        "result_type": item.result_type,
        "result_id": item.result_id,
        "result_title": _resolve_result_title(item, db) if item.processed_at else None,
        "result_project_id": result_project_id,
    }
    return data


@router.get("", response_model=list[InboxItem])
def list_inbox_items(
    processed: bool = Query(False, description="Show processed items"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    db: Session = Depends(get_db),
):
    """
    List inbox items

    By default shows only unprocessed items
    """
    query = select(InboxItemModel).order_by(InboxItemModel.captured_at.desc()).limit(limit)

    if not processed:
        query = query.where(InboxItemModel.processed_at.is_(None))

    items = db.execute(query).scalars().all()
    return [_to_response(item, db) for item in items]


@router.get("/{item_id}", response_model=InboxItem)
def get_inbox_item(item_id: int, db: Session = Depends(get_db)):
    """Get a single inbox item by ID"""
    item = db.get(InboxItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return _to_response(item, db)


@router.post("", response_model=InboxItem, status_code=201)
def create_inbox_item(item: InboxItemCreate, db: Session = Depends(get_db)):
    """
    Quick capture to inbox

    Capture anything that has your attention - process later
    """
    new_item = InboxItemModel(**item.model_dump())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


@router.put("/{item_id}", response_model=InboxItem)
def update_inbox_item(
    item_id: int,
    update: InboxItemUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an unprocessed inbox item (edit content before processing)
    """
    item = db.get(InboxItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    if item.processed_at:
        raise HTTPException(status_code=400, detail="Cannot edit a processed inbox item")

    if update.content is not None:
        item.content = update.content

    db.commit()
    db.refresh(item)
    return _to_response(item, db)


@router.post("/{item_id}/process", response_model=InboxItem)
def process_inbox_item(
    item_id: int,
    processing: InboxItemProcess,
    db: Session = Depends(get_db),
):
    """
    Process an inbox item (Clarify phase)

    Creates the appropriate entity (project, task) and links back to the inbox item.
    Supports optional title and description overrides for the created entity.
    """
    item = db.get(InboxItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    now = datetime.now(timezone.utc)
    result_id = processing.result_id
    entity_title = processing.title or item.content[:500]

    if processing.result_type == "project":
        new_project = Project(
            title=entity_title,
            description=processing.description or f"Created from inbox item #{item.id}",
            status="active",
            last_activity_at=now,
        )
        db.add(new_project)
        db.flush()
        result_id = new_project.id

    elif processing.result_type == "task":
        project_id = processing.result_id
        if not project_id:
            raise HTTPException(
                status_code=400,
                detail="A project must be selected when processing as task",
            )
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Selected project not found")

        new_task = Task(
            title=entity_title,
            description=processing.description,
            project_id=project_id,
            status="pending",
            is_next_action=True,
            urgency_zone="opportunity_now",
        )
        db.add(new_task)
        db.flush()
        result_id = new_task.id

        project.last_activity_at = now

    # Mark the inbox item as processed
    item.processed_at = now
    item.result_type = processing.result_type
    item.result_id = result_id

    db.commit()
    db.refresh(item)
    return _to_response(item, db)


@router.delete("/{item_id}", status_code=204)
def delete_inbox_item(item_id: int, db: Session = Depends(get_db)):
    """Delete an inbox item"""
    item = db.get(InboxItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    db.delete(item)
    db.commit()
    return None
