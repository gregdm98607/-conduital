"""
AI Context API routes

Endpoints for AI-specific context aggregation and macro execution.
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.modules import is_module_enabled

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================

class ContextRequest(BaseModel):
    """Request for AI context aggregation"""
    persona: Optional[str] = Field(None, description="Persona for routing (default, project_focused, creative)")
    include_projects: bool = Field(True, description="Include project summaries")
    include_memory: bool = Field(True, description="Include memory objects (if memory_layer enabled)")
    include_next_actions: bool = Field(True, description="Include prioritized next actions")
    max_projects: int = Field(10, ge=1, le=50)
    max_actions: int = Field(10, ge=1, le=50)
    max_memory_objects: int = Field(20, ge=1, le=100)


class MacroRequest(BaseModel):
    """Request for macro execution"""
    macro_name: str = Field(..., description="Macro to execute (gmb, wrap_up, weekly_review)")
    parameters: Optional[dict] = Field(None, description="Optional parameters")


class PersonaConfig(BaseModel):
    """Persona configuration"""
    name: str
    description: str
    prefer_namespaces: list[str] = Field(default_factory=list)
    fallback_namespaces: list[str] = Field(default_factory=list)
    project_filter: Optional[str] = None  # area, status filter


# =============================================================================
# Persona Definitions
# =============================================================================

PERSONAS = {
    "default": PersonaConfig(
        name="default",
        description="General-purpose context",
        prefer_namespaces=["core.identity", "core.preferences", "contexts"],
        fallback_namespaces=["knowledge.domains", "projects"],
    ),
    "project_focused": PersonaConfig(
        name="project_focused",
        description="Project and task focused context",
        prefer_namespaces=["projects", "workflows.threads"],
        fallback_namespaces=["core.identity"],
        project_filter="active",
    ),
    "creative": PersonaConfig(
        name="creative",
        description="Creative work context",
        prefer_namespaces=["contexts.creative", "projects"],
        fallback_namespaces=["knowledge.domains"],
        project_filter="active",
    ),
    "weekly_review": PersonaConfig(
        name="weekly_review",
        description="Weekly review context",
        prefer_namespaces=["core.identity", "projects", "workflows.threads", "system"],
        fallback_namespaces=[],
    ),
}


# =============================================================================
# Context Aggregation
# =============================================================================

@router.post("/context")
async def get_ai_context(
    request: ContextRequest,
    db: Session = Depends(get_db),
):
    """
    Get aggregated context for AI consumption.

    This combines:
    - Project summaries with momentum
    - Prioritized next actions
    - Memory objects (if memory_layer enabled)
    - User profile and preferences

    The response is optimized for AI context windows.
    """
    context = {
        "generated_at": datetime.utcnow().isoformat(),
        "persona": request.persona or "default",
    }

    persona = PERSONAS.get(request.persona or "default", PERSONAS["default"])

    # Get project summaries
    if request.include_projects:
        from app.services.project_service import ProjectService

        projects = ProjectService.list_projects(
            db,
            status=persona.project_filter,
            page=1,
            page_size=request.max_projects,
        )

        context["projects"] = {
            "count": len(projects),
            "items": [
                {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status,
                    "momentum": p.momentum_score,
                    "area": p.area.title if p.area else None,
                    "is_stalled": p.stalled_since is not None,
                }
                for p in projects
            ],
        }

    # Get next actions
    if request.include_next_actions:
        from app.services.next_actions_service import NextActionsService

        actions = NextActionsService.get_prioritized_next_actions(
            db,
            limit=request.max_actions,
        )

        context["next_actions"] = {
            "count": len(actions),
            "items": [
                {
                    "id": a.id,
                    "title": a.title,
                    "project": a.project.title if a.project else None,
                    "context": a.context,
                    "energy": a.energy_level,
                    "estimated_minutes": a.estimated_minutes,
                    "is_unstuck": a.is_unstuck_task,
                }
                for a in actions
            ],
        }

    # Get memory objects (if module enabled)
    if request.include_memory and is_module_enabled("memory_layer"):
        from app.modules.memory_layer.services import HydrationService
        from app.modules.memory_layer.schemas import HydrationRequest

        hydration_request = HydrationRequest(
            namespaces=persona.prefer_namespaces or None,
            min_priority=50,
            max_objects=request.max_memory_objects,
            include_content=True,
        )

        hydration = HydrationService.hydrate(db, hydration_request)

        context["memory"] = {
            "mode": hydration.hydration_mode,
            "count": hydration.included_count,
            "namespaces": hydration.namespaces_included,
            "objects": [
                {
                    "id": obj.object_id,
                    "namespace": obj.namespace,
                    "priority": obj.priority,
                    "content": obj.content,
                }
                for obj in hydration.objects
            ],
        }
    elif request.include_memory:
        context["memory"] = {
            "status": "memory_layer_not_enabled",
            "message": "Enable memory_layer module for persistent AI context",
        }

    return context


# =============================================================================
# Macro Execution
# =============================================================================

@router.post("/macros/{macro_name}")
async def execute_macro(
    macro_name: str,
    request: Optional[MacroRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Execute a macro for structured AI interactions.

    Available macros:
    - gmb: Good Morning Board - daily startup context
    - wrap_up: End of day wrap-up
    - weekly_review: Weekly review context
    """
    if macro_name not in ["gmb", "wrap_up", "weekly_review"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown macro: {macro_name}. Available: gmb, wrap_up, weekly_review"
        )

    macro_context = {
        "macro": macro_name,
        "executed_at": datetime.utcnow().isoformat(),
    }

    if macro_name == "gmb":
        # Good Morning Board
        macro_context.update(await _execute_gmb_macro(db))

    elif macro_name == "wrap_up":
        # Wrap Up
        macro_context.update(await _execute_wrap_up_macro(db))

    elif macro_name == "weekly_review":
        # Weekly Review
        macro_context.update(await _execute_weekly_review_macro(db))

    return macro_context


async def _execute_gmb_macro(db: Session) -> dict:
    """Good Morning Board macro"""
    from app.services.project_service import ProjectService
    from app.services.next_actions_service import NextActionsService
    from app.services.intelligence_service import IntelligenceService

    # Get stalled projects
    stalled = IntelligenceService.get_stalled_projects(db)

    # Get top next actions
    actions = NextActionsService.get_prioritized_next_actions(db, limit=5)

    # Get active project count
    active_projects = ProjectService.list_projects(db, status="active", page=1, page_size=100)

    return {
        "greeting": f"Good morning! Today is {date.today().strftime('%A, %B %d, %Y')}",
        "summary": {
            "active_projects": len(active_projects),
            "stalled_projects": len(stalled),
            "top_actions": len(actions),
        },
        "stalled_projects": [
            {
                "title": p.title,
                "stalled_days": (date.today() - p.stalled_since.date()).days if p.stalled_since else 0,
            }
            for p in stalled[:3]
        ],
        "top_actions": [
            {
                "title": a.title,
                "project": a.project.title if a.project else None,
                "context": a.context,
            }
            for a in actions
        ],
    }


async def _execute_wrap_up_macro(db: Session) -> dict:
    """Wrap Up macro"""
    from app.models.activity_log import ActivityLog
    from datetime import timedelta

    today_start = datetime.combine(date.today(), datetime.min.time())

    # Get today's activity
    today_activity = db.query(ActivityLog).filter(
        ActivityLog.timestamp >= today_start
    ).order_by(ActivityLog.timestamp.desc()).limit(20).all()

    completed_tasks = [
        a for a in today_activity
        if a.entity_type == "task" and a.action_type == "completed"
    ]

    return {
        "day_summary": {
            "total_activities": len(today_activity),
            "tasks_completed": len(completed_tasks),
        },
        "completed_tasks": [
            {
                "entity_id": a.entity_id,
                "timestamp": a.timestamp.isoformat(),
            }
            for a in completed_tasks[:10]
        ],
        "prompt": "What progress did you make today? Any blockers for tomorrow?",
    }


async def _execute_weekly_review_macro(db: Session) -> dict:
    """Weekly Review macro"""
    from app.services.intelligence_service import IntelligenceService

    review_data = IntelligenceService.get_weekly_review_data(db)

    return {
        "review_data": review_data,
        "checklist": [
            "Clear inbox to zero",
            "Review each active project",
            "Ensure every project has a next action",
            "Review waiting-for items",
            "Review someday/maybe list",
            "Look at calendar (next 2 weeks)",
            "Update project statuses",
        ],
    }


# =============================================================================
# Persona Endpoints
# =============================================================================

@router.get("/personas")
async def list_personas():
    """List available personas"""
    return {
        "personas": [
            {
                "name": p.name,
                "description": p.description,
            }
            for p in PERSONAS.values()
        ]
    }


@router.get("/personas/{persona_name}")
async def get_persona(persona_name: str):
    """Get persona configuration"""
    if persona_name not in PERSONAS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown persona: {persona_name}"
        )
    return PERSONAS[persona_name]
