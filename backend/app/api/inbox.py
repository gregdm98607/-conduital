"""
Inbox API endpoints - Quick Capture
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.inbox import InboxItem as InboxItemModel
from app.models.project import Project
from app.models.task import Task
from app.schemas.inbox import (
    InboxBatchAction,
    InboxBatchResponse,
    InboxBatchResultItem,
    InboxItem,
    InboxItemCreate,
    InboxItemProcess,
    InboxItemUpdate,
    InboxStatsResponse,
)

logger = logging.getLogger(__name__)

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


# --- Collection-level routes (must come before /{item_id} to avoid conflict) ---

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


# --- BETA-032: Inbox Stats ---

@router.get("/stats", response_model=InboxStatsResponse)
def get_inbox_stats(db: Session = Depends(get_db)):
    """
    Get inbox processing statistics.

    Returns unprocessed count, processed today, and average processing time.
    BETA-032: Replaces client-side calculation (DEBT-064).
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Unprocessed count
    unprocessed_count = db.execute(
        select(func.count(InboxItemModel.id))
        .where(InboxItemModel.processed_at.is_(None))
    ).scalar_one()

    # Processed today
    processed_today = db.execute(
        select(func.count(InboxItemModel.id))
        .where(InboxItemModel.processed_at >= today_start)
    ).scalar_one()

    # Average processing time (last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    processed_items = db.execute(
        select(InboxItemModel.captured_at, InboxItemModel.processed_at)
        .where(
            InboxItemModel.processed_at.is_not(None),
            InboxItemModel.processed_at >= thirty_days_ago,
        )
    ).all()

    avg_time = None
    if processed_items:
        total_seconds = 0
        count = 0
        for captured_at, processed_at in processed_items:
            if captured_at and processed_at:
                # Handle naive datetimes
                cap = captured_at if captured_at.tzinfo else captured_at.replace(tzinfo=timezone.utc)
                proc = processed_at if processed_at.tzinfo else processed_at.replace(tzinfo=timezone.utc)
                delta = (proc - cap).total_seconds()
                if delta >= 0:
                    total_seconds += delta
                    count += 1
        if count > 0:
            avg_time = round(total_seconds / count / 3600, 1)

    return InboxStatsResponse(
        unprocessed_count=unprocessed_count,
        processed_today=processed_today,
        avg_processing_time_hours=avg_time,
    )


# --- BETA-031: Inbox Batch Processing ---

@router.post("/batch-process", response_model=InboxBatchResponse)
def batch_process_inbox_items(
    batch: InboxBatchAction,
    db: Session = Depends(get_db),
):
    """
    Process multiple inbox items at once.

    Actions:
    - assign_to_project: Create tasks in a project from selected items
    - convert_to_task: Same as assign_to_project (alias)
    - delete: Delete selected items

    BETA-031: Batch processing for inbox efficiency.
    """
    now = datetime.now(timezone.utc)
    results: list[InboxBatchResultItem] = []

    # Validate project exists for assign/convert actions
    project = None
    if batch.action in ("assign_to_project", "convert_to_task"):
        if not batch.project_id:
            raise HTTPException(
                status_code=400,
                detail="project_id is required for assign_to_project/convert_to_task",
            )
        project = db.get(Project, batch.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Target project not found")

    for item_id in batch.item_ids:
        try:
            item = db.get(InboxItemModel, item_id)
            if not item:
                results.append(InboxBatchResultItem(
                    item_id=item_id, success=False, error="Item not found"
                ))
                continue

            if batch.action == "delete":
                db.delete(item)
                results.append(InboxBatchResultItem(item_id=item_id, success=True))

            elif batch.action in ("assign_to_project", "convert_to_task"):
                if item.processed_at:
                    results.append(InboxBatchResultItem(
                        item_id=item_id, success=False, error="Already processed"
                    ))
                    continue

                entity_title = batch.title_override or item.content[:500]
                new_task = Task(
                    title=entity_title,
                    project_id=batch.project_id,
                    status="pending",
                    is_next_action=True,
                    urgency_zone="opportunity_now",
                )
                db.add(new_task)
                db.flush()

                item.processed_at = now
                item.result_type = "task"
                item.result_id = new_task.id
                results.append(InboxBatchResultItem(item_id=item_id, success=True))

        except Exception as e:
            logger.error(f"Batch process error for item {item_id}: {e}")
            results.append(InboxBatchResultItem(
                item_id=item_id, success=False, error=str(e)
            ))

    # Update project activity timestamp if we created tasks
    if project and batch.action in ("assign_to_project", "convert_to_task"):
        project.last_activity_at = now

    db.commit()

    succeeded = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)

    return InboxBatchResponse(
        processed=succeeded,
        failed=failed,
        results=results,
    )


# --- Item-level routes (/{item_id} pattern must come AFTER fixed paths) ---

@router.get("/{item_id}", response_model=InboxItem)
def get_inbox_item(item_id: int, db: Session = Depends(get_db)):
    """Get a single inbox item by ID"""
    item = db.get(InboxItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Inbox item not found")
    return _to_response(item, db)


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
