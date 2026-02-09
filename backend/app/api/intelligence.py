"""
Intelligence API endpoints - Momentum, stalled projects, AI features
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.database import get_db
from app.models.momentum_snapshot import MomentumSnapshot
from app.models.project import Project
from app.schemas.task import Task as TaskSchema
from app.services.intelligence_service import IntelligenceService

router = APIRouter()


class MomentumUpdateResponse(BaseModel):
    """Response for momentum update operations"""

    success: bool
    message: str
    stats: dict


class MomentumFactor(BaseModel):
    """Individual momentum factor"""

    name: str
    weight: float
    raw_score: float
    weighted_score: float
    detail: str


class MomentumBreakdownResponse(BaseModel):
    """Response for momentum score drill-down"""

    project_id: int
    title: str
    total_score: float
    factors: list[MomentumFactor]


class ProjectHealthResponse(BaseModel):
    """Response for project health analysis"""

    project_id: int
    title: str
    momentum_score: float
    health_status: str
    days_since_activity: int | None
    is_stalled: bool
    stalled_since: str | None
    tasks: dict
    next_actions_count: int
    recent_activity_count: int
    recommendations: list[str]


class WeeklyReviewResponse(BaseModel):
    """Response for weekly review data"""

    review_date: str
    active_projects_count: int
    projects_needing_review: int
    projects_without_next_action: int
    tasks_completed_this_week: int
    inbox_count: int = 0
    someday_maybe_count: int = 0
    projects_needing_review_details: list[dict]
    projects_without_next_action_details: list[dict]


class AIAnalysisResponse(BaseModel):
    """Response for AI analysis"""

    analysis: str
    recommendations: list[str]


class AITaskSuggestion(BaseModel):
    """Response for AI task suggestions"""

    suggestion: str
    ai_generated: bool


class DashboardStatsResponse(BaseModel):
    """Response for dashboard stats"""

    active_project_count: int
    pending_task_count: int
    avg_momentum: float
    orphan_project_count: int


class MomentumSnapshotItem(BaseModel):
    """Single momentum snapshot data point for sparkline charts"""

    score: float
    snapshot_at: str  # ISO datetime


class MomentumHistoryResponse(BaseModel):
    """Response for momentum history / sparkline data"""

    project_id: int
    title: str
    current_score: float
    previous_score: float | None
    trend: str  # "rising", "falling", "stable"
    snapshots: list[MomentumSnapshotItem]


class MomentumSummaryProject(BaseModel):
    """Per-project momentum summary for the dashboard"""

    id: int
    title: str
    score: float
    previous_score: float | None
    trend: str  # "rising", "falling", "stable"


class MomentumSummaryResponse(BaseModel):
    """Aggregate momentum summary across all active projects"""

    total_active: int
    gaining: int  # projects with rising trend
    steady: int  # projects with stable trend
    declining: int  # projects with falling trend
    avg_score: float
    projects: list[MomentumSummaryProject]


def _compute_trend(current: float, previous: float | None) -> str:
    """Compute trend string from current and previous momentum scores."""
    if previous is None:
        return "stable"
    delta = current - previous
    if delta > 0.05:
        return "rising"
    elif delta < -0.05:
        return "falling"
    return "stable"


@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get aggregated dashboard statistics.

    Returns pre-computed counts for the dashboard stats grid:
    - Active project count
    - Pending task count (tasks with status 'pending' or 'in_progress' in active projects)
    - Average momentum score across active projects
    - Orphan project count (active projects without an area)
    """
    from app.models.task import Task

    # Get active projects stats in one query
    active_projects = db.execute(
        select(Project).where(Project.status == "active")
    ).scalars().all()

    active_count = len(active_projects)
    avg_momentum = (
        sum(p.momentum_score or 0 for p in active_projects) / active_count
        if active_count > 0
        else 0.0
    )
    orphan_count = sum(1 for p in active_projects if not p.area_id)

    # Count pending/in_progress tasks across active projects
    pending_count = db.execute(
        select(func.count(Task.id))
        .join(Project, Task.project_id == Project.id)
        .where(
            Project.status == "active",
            Task.status.in_(["pending", "in_progress"]),
        )
    ).scalar() or 0

    return DashboardStatsResponse(
        active_project_count=active_count,
        pending_task_count=pending_count,
        avg_momentum=avg_momentum,
        orphan_project_count=orphan_count,
    )


@router.get("/momentum-history/{project_id}", response_model=MomentumHistoryResponse)
def get_momentum_history(
    project_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history to return"),
    db: Session = Depends(get_db),
):
    """
    Get momentum snapshot history for a project.

    Returns time-series data suitable for sparkline charts, including
    the current score, previous score, computed trend, and daily snapshots.
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    snapshots = (
        db.execute(
            select(MomentumSnapshot)
            .where(
                MomentumSnapshot.project_id == project_id,
                MomentumSnapshot.snapshot_at >= cutoff,
            )
            .order_by(MomentumSnapshot.snapshot_at.desc())
        )
        .scalars()
        .all()
    )

    trend = _compute_trend(project.momentum_score or 0.0, project.previous_momentum_score)

    snapshot_items = [
        MomentumSnapshotItem(
            score=s.score,
            snapshot_at=s.snapshot_at.isoformat(),
        )
        for s in snapshots
    ]

    return MomentumHistoryResponse(
        project_id=project.id,
        title=project.title,
        current_score=project.momentum_score or 0.0,
        previous_score=project.previous_momentum_score,
        trend=trend,
        snapshots=snapshot_items,
    )


@router.get("/dashboard/momentum-summary", response_model=MomentumSummaryResponse)
def get_momentum_summary(db: Session = Depends(get_db)):
    """
    Get aggregate momentum summary across all active projects.

    Returns counts of gaining/steady/declining projects, the average
    momentum score, and per-project details with trend indicators.
    """
    active_projects = (
        db.execute(select(Project).where(Project.status == "active"))
        .scalars()
        .all()
    )

    project_summaries: list[MomentumSummaryProject] = []
    gaining = 0
    steady = 0
    declining = 0

    for p in active_projects:
        trend = _compute_trend(p.momentum_score or 0.0, p.previous_momentum_score)
        if trend == "rising":
            gaining += 1
        elif trend == "falling":
            declining += 1
        else:
            steady += 1

        project_summaries.append(
            MomentumSummaryProject(
                id=p.id,
                title=p.title,
                score=p.momentum_score or 0.0,
                previous_score=p.previous_momentum_score,
                trend=trend,
            )
        )

    total_active = len(active_projects)
    avg_score = (
        sum(p.momentum_score or 0.0 for p in active_projects) / total_active
        if total_active > 0
        else 0.0
    )

    return MomentumSummaryResponse(
        total_active=total_active,
        gaining=gaining,
        steady=steady,
        declining=declining,
        avg_score=avg_score,
        projects=project_summaries,
    )


@router.post("/momentum/update", response_model=MomentumUpdateResponse)
def update_momentum_scores(db: Session = Depends(get_db)):
    """
    Update momentum scores for all active projects

    This will:
    1. Calculate new momentum scores
    2. Detect newly stalled projects
    3. Unstall projects that have resumed activity
    4. Log all changes
    """
    try:
        stats = IntelligenceService.update_all_momentum_scores(db)

        return MomentumUpdateResponse(
            success=True,
            message=f"Updated {stats['updated']} projects",
            stats=stats,
        )
    except Exception as e:
        logger.error(f"Momentum update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Momentum update failed: {str(e)}")


@router.get("/momentum/{project_id}", response_model=float)
def calculate_project_momentum(project_id: int, db: Session = Depends(get_db)):
    """
    Calculate momentum score for a specific project

    Returns a score from 0.0 to 1.0 based on:
    - Recent activity (40% weight)
    - Completion rate (30% weight)
    - Next action availability (20% weight)
    - Activity frequency (10% weight)
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    score = IntelligenceService.calculate_momentum_score(db, project)
    return score


@router.get("/momentum-breakdown/{project_id}", response_model=MomentumBreakdownResponse)
def get_momentum_breakdown(project_id: int, db: Session = Depends(get_db)):
    """
    Get detailed momentum score breakdown for a project.

    Shows each factor's contribution to the total score:
    - Recent Activity (40%): Decay over 30 days since last activity
    - Completion Rate (30%): Tasks completed in last 7 days
    - Next Action (20%): Whether a clear next action is defined
    - Activity Frequency (10%): Actions logged in last 14 days
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    breakdown = IntelligenceService.get_momentum_breakdown(db, project)
    return MomentumBreakdownResponse(
        project_id=project.id,
        title=project.title,
        **breakdown,
    )


@router.get("/health/{project_id}", response_model=ProjectHealthResponse)
def get_project_health(project_id: int, db: Session = Depends(get_db)):
    """
    Get comprehensive health summary for a project

    Includes:
    - Momentum score
    - Health status (stalled, at_risk, weak, moderate, strong)
    - Task statistics
    - Recent activity count
    - Actionable recommendations
    """
    # Eagerly load tasks to avoid N+1 in health summary
    project = db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(joinedload(Project.tasks))
    ).unique().scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    health = IntelligenceService.get_project_health_summary(db, project)
    return ProjectHealthResponse(**health)


@router.get("/stalled", response_model=list[dict])
def get_stalled_projects(
    include_at_risk: bool = Query(False, description="Include at-risk projects (7+ days inactive)"),
    db: Session = Depends(get_db),
):
    """
    Get stalled and optionally at-risk projects.

    Stalled: no activity for 14+ days (stalled_since set).
    At-risk: 7-13 days inactive (not yet stalled but needs attention).
    """
    from datetime import datetime, timezone
    from app.services.intelligence_service import _ensure_tz_aware

    now = datetime.now(timezone.utc)
    stalled = IntelligenceService.detect_stalled_projects(db)
    stalled_ids = {p.id for p in stalled}

    results = [
        {
            "id": p.id,
            "title": p.title,
            "momentum_score": p.momentum_score,
            "stalled_since": p.stalled_since.isoformat() if p.stalled_since else None,
            "days_stalled": (now - p.stalled_since).days if p.stalled_since else None,
            "days_since_activity": (
                (now - p.last_activity_at).days if p.last_activity_at else None
            ),
            "is_stalled": True,
        }
        for p in stalled
    ]

    if include_at_risk:
        # Find at-risk projects: active, not stalled, but inactive > threshold
        active_projects = db.execute(
            select(Project).where(
                Project.status == "active",
                Project.stalled_since.is_(None),
            )
        ).scalars().all()

        threshold = settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS
        for p in active_projects:
            if p.id in stalled_ids:
                continue
            if p.last_activity_at:
                days_since = (now - _ensure_tz_aware(p.last_activity_at)).days
                if days_since > threshold:
                    results.append({
                        "id": p.id,
                        "title": p.title,
                        "momentum_score": p.momentum_score,
                        "stalled_since": None,
                        "days_stalled": None,
                        "days_since_activity": days_since,
                        "is_stalled": False,
                    })

    return results


@router.post("/unstuck/{project_id}", response_model=TaskSchema)
def create_unstuck_task(
    project_id: int,
    use_ai: bool = Query(True, description="Use AI for task generation"),
    db: Session = Depends(get_db),
):
    """
    Create an unstuck task for a stalled project

    Generates a minimal viable task (5-15 minutes) to restart momentum.

    Args:
        project_id: Project ID
        use_ai: Whether to use AI for generation (default True)

    The task will be:
    - Marked as next action
    - Set to 10 minutes estimated time
    - Assigned to "quick_win" context
    - Set to "low" energy level
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if AI is enabled
    if use_ai and not settings.AI_FEATURES_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="AI features not enabled. Set AI_FEATURES_ENABLED=true in .env",
        )

    if use_ai and not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env",
        )

    try:
        task = IntelligenceService.create_unstuck_task(db, project, use_ai=use_ai)
        return TaskSchema.model_validate(task)
    except Exception as e:
        logger.error(f"Unstuck task creation failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


@router.get("/weekly-review", response_model=WeeklyReviewResponse)
def get_weekly_review(db: Session = Depends(get_db)):
    """
    Generate weekly review data

    Returns:
    - Active project count
    - Projects needing review (stalled or at risk)
    - Projects without next actions
    - Tasks completed this week
    - Detailed lists for review
    """
    review_data = IntelligenceService.get_weekly_review_data(db)
    return WeeklyReviewResponse(**review_data)


@router.post("/ai/analyze/{project_id}", response_model=AIAnalysisResponse)
def analyze_project_with_ai(project_id: int, db: Session = Depends(get_db)):
    """
    Generate AI-powered project health analysis

    Requires:
    - AI_FEATURES_ENABLED=true
    - ANTHROPIC_API_KEY configured

    Returns:
    - Written analysis of project health
    - 2-3 specific actionable recommendations
    """
    if not settings.AI_FEATURES_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="AI features not enabled. Set AI_FEATURES_ENABLED=true in .env",
        )

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env",
        )

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        from app.services.ai_service import AIService

        ai_service = AIService()
        result = ai_service.analyze_project_health(db, project)
        return AIAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"AI analysis failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


@router.post("/ai/suggest-next-action/{project_id}", response_model=AITaskSuggestion)
def suggest_next_action_with_ai(project_id: int, db: Session = Depends(get_db)):
    """
    Generate AI-powered next action suggestion

    For active (non-stalled) projects, suggests the most important
    next action based on project context, pending tasks, and recent activity.

    Requires:
    - AI_FEATURES_ENABLED=true
    - ANTHROPIC_API_KEY configured
    """
    if not settings.AI_FEATURES_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="AI features not enabled. Set AI_FEATURES_ENABLED=true in .env",
        )

    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env",
        )

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        from app.services.ai_service import AIService

        ai_service = AIService()
        suggestion = ai_service.suggest_next_action(db, project)
        return AITaskSuggestion(suggestion=suggestion, ai_generated=True)
    except Exception as e:
        logger.error(f"AI suggestion failed for project {project_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"AI suggestion failed: {str(e)}"
        )
