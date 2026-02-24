"""
Memory Layer API routes

REST endpoints for memory object management and context hydration.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.modules.memory_layer.models import MemoryObject, MemoryNamespace, MemoryIndex, PrefetchRule
from app.modules.memory_layer.schemas import (
    MemoryObjectCreate,
    MemoryObjectUpdate,
    MemoryObjectResponse,
    MemoryObjectBrief,
    NamespaceCreate,
    NamespaceUpdate,
    NamespaceResponse,
    HydrationRequest,
    HydrationResponse,
    QuickKeyCreate,
    QuickKeyResponse,
    PrefetchRuleCreate,
    PrefetchRuleUpdate,
    PrefetchRuleResponse,
    MemoryExport,
    MemoryImportRequest,
    MemoryStats,
    MemoryStatsTotals,
    MemoryStatsObjects,
    MemoryStatsNamespaceCount,
    MemoryStatsActivity,
    SessionCaptureRequest,
)
from app.modules.memory_layer.services import MemoryService, HydrationService

router = APIRouter()


# =============================================================================
# Stats Endpoint
# =============================================================================

@router.get("/stats", response_model=MemoryStats)
def get_memory_stats(db: Session = Depends(get_db)):
    """Return aggregated health metrics for the memory layer."""
    from sqlalchemy import func, case, or_
    from datetime import datetime, timedelta, timezone

    today = date.today()
    cutoff_7d = datetime.now(timezone.utc) - timedelta(days=7)
    cutoff_30d = datetime.now(timezone.utc) - timedelta(days=30)

    # Query 1: All MemoryObject aggregates in a single pass
    is_active = case(
        (
            (MemoryObject.effective_from <= today)
            & or_(MemoryObject.effective_to.is_(None), MemoryObject.effective_to >= today),
            1,
        ),
        else_=0,
    )
    row = db.query(
        func.count(MemoryObject.id),
        func.sum(is_active),
        func.count(case((MemoryObject.storage_type == "db", 1))),
        func.count(case((MemoryObject.storage_type == "file", 1))),
        func.avg(MemoryObject.priority),
        func.count(case((MemoryObject.priority >= 80, 1))),
        func.count(case(((MemoryObject.priority >= 40) & (MemoryObject.priority < 80), 1))),
        func.count(case((MemoryObject.priority < 40, 1))),
        func.count(case((MemoryObject.created_at >= cutoff_7d, 1))),
        func.count(case((MemoryObject.updated_at >= cutoff_7d, 1))),
        func.count(case((MemoryObject.created_at >= cutoff_30d, 1))),
        func.count(case((MemoryObject.updated_at >= cutoff_30d, 1))),
    ).one()

    total_objects = row[0] or 0
    active_objects = int(row[1] or 0)
    db_storage = row[2] or 0
    file_storage = row[3] or 0
    avg_priority = round(float(row[4]), 1) if row[4] is not None else 0.0
    high_priority = row[5] or 0
    medium_priority = row[6] or 0
    low_priority = row[7] or 0
    created_7d = row[8] or 0
    updated_7d = row[9] or 0
    created_30d = row[10] or 0
    updated_30d = row[11] or 0

    # Query 2: Counts from other tables (namespaces, quick keys, prefetch rules)
    total_namespaces = db.query(func.count(MemoryNamespace.id)).scalar() or 0
    total_quick_keys = db.query(func.count(MemoryIndex.id)).scalar() or 0
    prefetch_row = db.query(
        func.count(PrefetchRule.id),
        func.count(case((PrefetchRule.is_active.is_(True), 1))),
    ).one()
    total_prefetch = prefetch_row[0] or 0
    active_prefetch = prefetch_row[1] or 0

    # Query 3: Top namespaces by object count
    ns_rows = (
        db.query(MemoryObject.namespace, func.count(MemoryObject.id).label("cnt"))
        .group_by(MemoryObject.namespace)
        .order_by(func.count(MemoryObject.id).desc())
        .limit(8)
        .all()
    )

    return MemoryStats(
        totals=MemoryStatsTotals(
            objects=total_objects,
            namespaces=total_namespaces,
            quick_keys=total_quick_keys,
            prefetch_rules=total_prefetch,
            active_prefetch_rules=active_prefetch,
        ),
        objects=MemoryStatsObjects(
            active=active_objects,
            inactive=total_objects - active_objects,
            db_storage=db_storage,
            file_storage=file_storage,
            avg_priority=avg_priority,
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
        ),
        namespaces_by_count=[
            MemoryStatsNamespaceCount(name=name, count=cnt) for name, cnt in ns_rows
        ],
        recent_activity=MemoryStatsActivity(
            created_last_7d=created_7d,
            updated_last_7d=updated_7d,
            created_last_30d=created_30d,
            updated_last_30d=updated_30d,
        ),
    )


# =============================================================================
# Memory Object Endpoints
# =============================================================================

@router.get("/objects", response_model=list[MemoryObjectBrief])
def list_memory_objects(
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    min_priority: int = Query(0, ge=0, le=100),
    active_only: bool = Query(True),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List memory objects with optional filters"""
    objects = MemoryService.list_objects(
        db,
        namespace=namespace,
        min_priority=min_priority,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return [MemoryObjectBrief.model_validate(obj) for obj in objects]


@router.get("/objects/search", response_model=list[MemoryObjectBrief])
def search_memory_objects(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    namespace: Optional[str] = Query(None, description="Filter by namespace"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    Search memory objects across object_id, namespace, tags, and content.

    Performs case-insensitive substring matching across all text fields.
    """
    objects = MemoryService.search_objects(
        db,
        query_text=q,
        namespace=namespace,
        limit=limit,
    )
    return [MemoryObjectBrief.model_validate(obj) for obj in objects]


@router.post("/objects", response_model=MemoryObjectResponse, status_code=status.HTTP_201_CREATED)
def create_memory_object(
    data: MemoryObjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new memory object"""
    # Check if object_id already exists
    existing = MemoryService.get_object(db, data.object_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Memory object with ID '{data.object_id}' already exists"
        )

    obj = MemoryService.create_object(db, data)
    return MemoryObjectResponse.model_validate(obj)


@router.get("/objects/{object_id}", response_model=MemoryObjectResponse)
def get_memory_object(
    object_id: str,
    db: Session = Depends(get_db),
):
    """Get a memory object by ID"""
    obj = MemoryService.get_object(db, object_id)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory object '{object_id}' not found"
        )
    return MemoryObjectResponse.model_validate(obj)


@router.patch("/objects/{object_id}", response_model=MemoryObjectResponse)
def update_memory_object(
    object_id: str,
    data: MemoryObjectUpdate,
    db: Session = Depends(get_db),
):
    """Update a memory object"""
    obj = MemoryService.update_object(db, object_id, data)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory object '{object_id}' not found"
        )
    return MemoryObjectResponse.model_validate(obj)


@router.delete("/objects/{object_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory_object(
    object_id: str,
    db: Session = Depends(get_db),
):
    """Delete a memory object"""
    success = MemoryService.delete_object(db, object_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memory object '{object_id}' not found"
        )


# =============================================================================
# Namespace Endpoints
# =============================================================================

@router.get("/namespaces", response_model=list[NamespaceResponse])
def list_namespaces(db: Session = Depends(get_db)):
    """List all namespaces with object counts"""
    from sqlalchemy import func
    namespaces = db.query(MemoryNamespace).order_by(MemoryNamespace.name).all()
    counts = dict(
        db.query(MemoryObject.namespace, func.count(MemoryObject.id))
        .group_by(MemoryObject.namespace)
        .all()
    )
    result = []
    for ns in namespaces:
        data = NamespaceResponse.model_validate(ns)
        data.object_count = counts.get(ns.name, 0)
        result.append(data)
    return result


@router.post("/namespaces", response_model=NamespaceResponse, status_code=status.HTTP_201_CREATED)
def create_namespace(
    data: NamespaceCreate,
    db: Session = Depends(get_db),
):
    """Create a new namespace"""
    existing = db.query(MemoryNamespace).filter(MemoryNamespace.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Namespace '{data.name}' already exists"
        )

    namespace = MemoryService.create_namespace(
        db,
        data.name,
        data.description,
        data.default_priority
    )
    ns_response = NamespaceResponse.model_validate(namespace)
    ns_response.object_count = 0
    return ns_response


@router.patch("/namespaces/{name}", response_model=NamespaceResponse)
def update_namespace(
    name: str,
    data: NamespaceUpdate,
    db: Session = Depends(get_db),
):
    """Update a namespace's description or default priority (name is immutable)"""
    from sqlalchemy import func
    ns = db.query(MemoryNamespace).filter(MemoryNamespace.name == name).first()
    if not ns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Namespace '{name}' not found"
        )

    if data.description is not None:
        ns.description = data.description
    if data.default_priority is not None:
        ns.default_priority = data.default_priority

    db.commit()
    db.refresh(ns)

    count = db.query(func.count(MemoryObject.id)).filter(MemoryObject.namespace == name).scalar() or 0
    ns_response = NamespaceResponse.model_validate(ns)
    ns_response.object_count = count
    return ns_response


@router.delete("/namespaces/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_namespace(
    name: str,
    force: bool = Query(False, description="Delete even if namespace contains objects"),
    db: Session = Depends(get_db),
):
    """
    Delete a namespace.

    By default, returns 409 if the namespace contains objects.
    Use force=true to delete the namespace and all its objects.
    """
    from sqlalchemy import func
    ns = db.query(MemoryNamespace).filter(MemoryNamespace.name == name).first()
    if not ns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Namespace '{name}' not found"
        )

    count = db.query(func.count(MemoryObject.id)).filter(MemoryObject.namespace == name).scalar() or 0
    if count > 0 and not force:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Namespace '{name}' contains {count} object(s). Delete them first or use force=true."
        )

    if force and count > 0:
        db.query(MemoryObject).filter(MemoryObject.namespace == name).delete()

    db.delete(ns)
    db.commit()


# =============================================================================
# Hydration Endpoints
# =============================================================================

@router.post("/hydrate", response_model=HydrationResponse)
def hydrate_context(
    request: HydrationRequest,
    db: Session = Depends(get_db),
):
    """
    Hydrate memory context for AI consumption.

    Returns memory objects based on priority and namespace filters.

    Hydration modes:
    - full: All active objects above min_priority
    - thin: High priority only (set min_priority >= 70)
    - targeted: Specific namespaces only (provide namespaces list)
    """
    return HydrationService.hydrate(db, request)


@router.get("/hydrate/quick/{key}")
def hydrate_quick_key(
    key: str,
    db: Session = Depends(get_db),
):
    """Get memory object by quick key"""
    obj = HydrationService.get_quick_key(db, key)
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quick key '{key}' not found or not mapped"
        )
    return MemoryObjectResponse.model_validate(obj)


@router.get("/hydrate/bundle/{trigger}")
def get_prefetch_bundle(
    trigger: str,
    db: Session = Depends(get_db),
):
    """Get bundle of objects for a prefetch trigger"""
    objects = HydrationService.get_prefetch_bundle(db, trigger)
    return {
        "trigger": trigger,
        "objects": [MemoryObjectResponse.model_validate(obj) for obj in objects],
        "count": len(objects),
    }


# =============================================================================
# Quick Key Endpoints
# =============================================================================

@router.get("/index/keys", response_model=list[QuickKeyResponse])
def list_quick_keys(db: Session = Depends(get_db)):
    """List all quick keys"""
    keys = db.query(MemoryIndex).order_by(MemoryIndex.key).all()
    return [QuickKeyResponse.model_validate(k) for k in keys]


@router.post("/index/keys", response_model=QuickKeyResponse, status_code=status.HTTP_201_CREATED)
def create_quick_key(
    data: QuickKeyCreate,
    db: Session = Depends(get_db),
):
    """Create a quick key mapping"""
    existing = db.query(MemoryIndex).filter(MemoryIndex.key == data.key).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Quick key '{data.key}' already exists"
        )

    key = MemoryIndex(
        key=data.key,
        target_type=data.target_type,
        target_id=data.target_id,
        target_path=data.target_path,
        description=data.description,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return QuickKeyResponse.model_validate(key)


# =============================================================================
# Prefetch Rule Endpoints
# =============================================================================

@router.get("/index/prefetch", response_model=list[PrefetchRuleResponse])
def list_prefetch_rules(db: Session = Depends(get_db)):
    """List all prefetch rules"""
    rules = db.query(PrefetchRule).order_by(PrefetchRule.name).all()
    return [PrefetchRuleResponse.model_validate(r) for r in rules]


@router.post("/index/prefetch", response_model=PrefetchRuleResponse, status_code=status.HTTP_201_CREATED)
def create_prefetch_rule(
    data: PrefetchRuleCreate,
    db: Session = Depends(get_db),
):
    """Create a prefetch rule"""
    existing = db.query(PrefetchRule).filter(PrefetchRule.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Prefetch rule '{data.name}' already exists"
        )

    rule = PrefetchRule(
        name=data.name,
        trigger=data.trigger,
        lookahead_minutes=data.lookahead_minutes,
        bundle=data.bundle,
        false_prefetch_decay_minutes=data.false_prefetch_decay_minutes,
        is_active=data.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return PrefetchRuleResponse.model_validate(rule)


@router.patch("/index/prefetch/{name}", response_model=PrefetchRuleResponse)
def update_prefetch_rule(
    name: str,
    data: PrefetchRuleUpdate,
    db: Session = Depends(get_db),
):
    """Update a prefetch rule (name is immutable)"""
    rule = db.query(PrefetchRule).filter(PrefetchRule.name == name).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prefetch rule '{name}' not found"
        )

    if data.trigger is not None:
        rule.trigger = data.trigger
    if data.lookahead_minutes is not None:
        rule.lookahead_minutes = data.lookahead_minutes
    if data.bundle is not None:
        rule.bundle = data.bundle
    if data.false_prefetch_decay_minutes is not None:
        rule.false_prefetch_decay_minutes = data.false_prefetch_decay_minutes
    if data.is_active is not None:
        rule.is_active = data.is_active

    db.commit()
    db.refresh(rule)
    return PrefetchRuleResponse.model_validate(rule)


@router.delete("/index/prefetch/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prefetch_rule(
    name: str,
    db: Session = Depends(get_db),
):
    """Delete a prefetch rule"""
    rule = db.query(PrefetchRule).filter(PrefetchRule.name == name).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prefetch rule '{name}' not found"
        )
    db.delete(rule)
    db.commit()


# =============================================================================
# Import/Export Endpoints
# =============================================================================

@router.get("/export", response_model=MemoryExport)
def export_memory(db: Session = Depends(get_db)):
    """
    Export all memory data in PA-compatible format.

    This can be used to backup memory or migrate to file-based storage.
    """
    from datetime import datetime

    namespaces = db.query(MemoryNamespace).all()
    objects = db.query(MemoryObject).all()
    quick_keys = db.query(MemoryIndex).all()
    prefetch_rules = db.query(PrefetchRule).all()

    return MemoryExport(
        version="1.0.0",
        exported_at=datetime.utcnow(),
        namespaces=[NamespaceResponse.model_validate(ns) for ns in namespaces],
        objects=[MemoryObjectResponse.model_validate(obj) for obj in objects],
        quick_keys=[QuickKeyResponse.model_validate(k) for k in quick_keys],
        prefetch_rules=[PrefetchRuleResponse.model_validate(r) for r in prefetch_rules],
    )


@router.post("/import", status_code=status.HTTP_201_CREATED)
def import_memory(
    data: MemoryImportRequest,
    db: Session = Depends(get_db),
):
    """
    Import memory data from PA-compatible format.

    Use this to migrate from file-based PA to database-backed memory.
    """
    imported = {"namespaces": 0, "objects": 0, "skipped": 0}

    # Import namespaces first
    if data.namespaces:
        for ns_data in data.namespaces:
            existing = db.query(MemoryNamespace).filter(
                MemoryNamespace.name == ns_data.name
            ).first()
            if not existing:
                MemoryService.create_namespace(
                    db, ns_data.name, ns_data.description, ns_data.default_priority
                )
                imported["namespaces"] += 1

    # Import objects
    for obj_data in data.objects:
        existing = MemoryService.get_object(db, obj_data.object_id)
        if existing:
            if data.overwrite_existing:
                MemoryService.update_object(
                    db,
                    obj_data.object_id,
                    MemoryObjectUpdate(
                        content=obj_data.content,
                        priority=obj_data.priority,
                        tags=obj_data.tags,
                    )
                )
                imported["objects"] += 1
            else:
                imported["skipped"] += 1
        else:
            MemoryService.create_object(db, obj_data)
            imported["objects"] += 1

    return {
        "status": "success",
        "imported": imported,
    }


# =============================================================================
# Onboarding Endpoint
# =============================================================================

class OnboardingRequest(BaseModel):
    """User onboarding data that generates initial memory objects."""
    # Step 1: Identity
    name: str = Field(..., min_length=1, max_length=100)
    preferred_name: Optional[str] = None
    role: Optional[str] = None
    timezone: Optional[str] = None
    # Step 2: Preferences
    communication_style: Optional[str] = None  # concise, detailed, balanced
    work_methodology: Optional[str] = None  # gtd, eisenhower, timeblocking, other
    planning_horizon: Optional[str] = None  # daily, weekly, monthly
    peak_hours: Optional[list[str]] = None  # e.g. ["09:00-12:00", "14:00-17:00"]
    # Step 3: Contexts
    primary_contexts: Optional[list[str]] = None  # e.g. ["@computer", "@desk"]
    locations: Optional[list[str]] = None
    # Step 4: Skills (optional)
    primary_skills: Optional[list[str]] = None
    learning_goals: Optional[list[str]] = None


class OnboardingResponse(BaseModel):
    """Response from onboarding."""
    status: str
    objects_created: int
    object_ids: list[str]


@router.post("/onboarding", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
def complete_onboarding(
    data: OnboardingRequest,
    db: Session = Depends(get_db),
):
    """
    Complete user onboarding by creating initial memory objects.

    Generates 2-4 memory objects based on user input:
    - core.identity: User profile
    - core.preferences: Work style and communication preferences
    - contexts: Available contexts and locations
    - knowledge.domains: Skills and learning goals (optional)
    """
    today = date.today()
    created_ids: list[str] = []

    # 1. Core Identity (always created)
    identity_data = MemoryObjectCreate(
        object_id="user-profile-001",
        namespace="core.identity",
        priority=92,
        effective_from=today,
        content={
            "name": data.name,
            "preferred_name": data.preferred_name or data.name,
            "role": data.role or "",
            "timezone": data.timezone or "",
        },
    )

    # Check if already exists (re-onboarding)
    existing = MemoryService.get_object(db, "user-profile-001")
    if existing:
        from app.modules.memory_layer.schemas import MemoryObjectUpdate
        MemoryService.update_object(db, "user-profile-001", MemoryObjectUpdate(
            content=identity_data.content
        ))
    else:
        MemoryService.create_object(db, identity_data)
    created_ids.append("user-profile-001")

    # 2. Core Preferences (if any preference data provided)
    if any([data.communication_style, data.work_methodology, data.planning_horizon, data.peak_hours]):
        prefs_content = {}
        if data.communication_style:
            prefs_content["communication_style"] = data.communication_style
        if data.work_methodology:
            prefs_content["work_methodology"] = data.work_methodology
        if data.planning_horizon:
            prefs_content["planning_horizon"] = data.planning_horizon
        if data.peak_hours:
            prefs_content["energy_patterns"] = {"peak_hours": data.peak_hours}

        prefs_data = MemoryObjectCreate(
            object_id="interaction-preferences-001",
            namespace="core.preferences",
            priority=87,
            effective_from=today,
            content=prefs_content,
        )

        existing = MemoryService.get_object(db, "interaction-preferences-001")
        if existing:
            MemoryService.update_object(db, "interaction-preferences-001", MemoryObjectUpdate(
                content=prefs_content
            ))
        else:
            MemoryService.create_object(db, prefs_data)
        created_ids.append("interaction-preferences-001")

    # 3. Contexts (if any context data provided)
    if any([data.primary_contexts, data.locations]):
        ctx_content = {}
        if data.primary_contexts:
            ctx_content["primary_contexts"] = data.primary_contexts
        if data.locations:
            ctx_content["locations"] = data.locations

        ctx_data = MemoryObjectCreate(
            object_id="work-context-001",
            namespace="contexts",
            priority=82,
            effective_from=today,
            content=ctx_content,
        )

        existing = MemoryService.get_object(db, "work-context-001")
        if existing:
            MemoryService.update_object(db, "work-context-001", MemoryObjectUpdate(
                content=ctx_content
            ))
        else:
            MemoryService.create_object(db, ctx_data)
        created_ids.append("work-context-001")

    # 4. Knowledge/Skills (optional, only if provided)
    if any([data.primary_skills, data.learning_goals]):
        knowledge_content = {}
        if data.primary_skills:
            knowledge_content["primary_skills"] = data.primary_skills
        if data.learning_goals:
            knowledge_content["learning_goals"] = data.learning_goals

        knowledge_data = MemoryObjectCreate(
            object_id="expertise-001",
            namespace="knowledge.domains",
            priority=67,
            effective_from=today,
            content=knowledge_content,
        )

        existing = MemoryService.get_object(db, "expertise-001")
        if existing:
            MemoryService.update_object(db, "expertise-001", MemoryObjectUpdate(
                content=knowledge_content
            ))
        else:
            MemoryService.create_object(db, knowledge_data)
        created_ids.append("expertise-001")

    return OnboardingResponse(
        status="success",
        objects_created=len(created_ids),
        object_ids=created_ids,
    )


# =============================================================================
# Session Capture Endpoints
# =============================================================================

_SESSIONS_NAMESPACE = "sessions"


@router.post("/sessions", response_model=MemoryObjectResponse, status_code=status.HTTP_201_CREATED)
def capture_session(
    data: SessionCaptureRequest,
    db: Session = Depends(get_db),
):
    """
    Capture an end-of-session summary.

    Creates a structured memory object in the 'sessions' namespace.
    Object IDs are auto-generated as session-YYYYMMDD-NNN.
    The sessions namespace is auto-created on first use.
    """
    session_date = data.session_date or date.today()
    date_str = session_date.strftime("%Y%m%d")

    # Auto-create sessions namespace if missing
    ns = db.query(MemoryNamespace).filter(MemoryNamespace.name == _SESSIONS_NAMESPACE).first()
    if not ns:
        MemoryService.create_namespace(
            db, _SESSIONS_NAMESPACE,
            "End-of-session summaries",
            default_priority=65,
        )

    # Determine next counter for this date
    prefix = f"session-{date_str}-"
    existing_count = (
        db.query(MemoryObject)
        .filter(
            MemoryObject.namespace == _SESSIONS_NAMESPACE,
            MemoryObject.object_id.like(f"{prefix}%"),
        )
        .count()
    )
    object_id = f"{prefix}{existing_count + 1:03d}"

    # Build structured content
    content: dict = {"date": str(session_date), "accomplishments": data.accomplishments}
    if data.blockers:
        content["blockers"] = data.blockers
    if data.next_focus:
        content["next_focus"] = data.next_focus
    if data.energy_level is not None:
        content["energy_level"] = data.energy_level
    if data.duration_minutes is not None:
        content["duration_minutes"] = data.duration_minutes
    if data.notes:
        content["notes"] = data.notes

    obj_data = MemoryObjectCreate(
        object_id=object_id,
        namespace=_SESSIONS_NAMESPACE,
        priority=65,
        effective_from=session_date,
        content=content,
        tags=data.tags or ["session"],
    )

    obj = MemoryService.create_object(db, obj_data)
    return MemoryObjectResponse.model_validate(obj)


@router.get("/sessions", response_model=list[MemoryObjectResponse])
def list_sessions(
    limit: int = Query(30, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List session summaries, newest first."""
    objects = (
        db.query(MemoryObject)
        .filter(MemoryObject.namespace == _SESSIONS_NAMESPACE)
        .order_by(MemoryObject.created_at.desc())
        .limit(limit)
        .all()
    )
    return [MemoryObjectResponse.model_validate(obj) for obj in objects]
