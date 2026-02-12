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
from app.services.intelligence_service import IntelligenceService, _ensure_tz_aware

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


class WeeklyReviewCompleteRequest(BaseModel):
    """Request for completing a weekly review (BETA-030)"""

    notes: str | None = None


class WeeklyReviewCompletionItem(BaseModel):
    """Single weekly review completion record"""

    id: int
    completed_at: str
    notes: str | None = None


class WeeklyReviewHistoryResponse(BaseModel):
    """Response for weekly review completion history (BETA-030)"""

    completions: list[WeeklyReviewCompletionItem]
    last_completed_at: str | None = None
    days_since_last_review: int | None = None


class AIAnalysisResponse(BaseModel):
    """Response for AI analysis"""

    analysis: str
    recommendations: list[str]


class AITaskSuggestion(BaseModel):
    """Response for AI task suggestions"""

    suggestion: str
    ai_generated: bool


class ProactiveInsight(BaseModel):
    """Single project proactive insight"""

    project_id: int
    project_title: str
    momentum_score: float
    trend: str
    analysis: str | None = None
    recommended_action: str | None = None
    error: str | None = None


class ProactiveAnalysisResponse(BaseModel):
    """Response for proactive stalled/declining analysis"""

    projects_analyzed: int
    insights: list[ProactiveInsight]


class DecomposedTask(BaseModel):
    """A task decomposed from brainstorm notes"""

    title: str
    estimated_minutes: int | None = None
    energy_level: str | None = None
    context: str | None = None


class TaskDecompositionResponse(BaseModel):
    """Response for AI task decomposition from brainstorm notes"""

    project_id: int
    tasks: list[DecomposedTask]
    source: str  # "brainstorm_notes" or "organizing_notes"


class RebalanceSuggestion(BaseModel):
    """Single rebalancing suggestion"""

    task_id: int
    task_title: str
    project_title: str
    current_zone: str | None
    suggested_zone: str
    reason: str


class RebalanceResponse(BaseModel):
    """Response for priority rebalancing suggestions"""

    opportunity_now_count: int
    threshold: int
    suggestions: list[RebalanceSuggestion]


class EnergyTask(BaseModel):
    """Task matched by energy level"""

    task_id: int
    task_title: str
    project_id: int
    project_title: str
    energy_level: str | None
    estimated_minutes: int | None
    context: str | None
    urgency_zone: str | None


class EnergyRecommendationResponse(BaseModel):
    """Response for energy-matched task recommendations"""

    energy_level: str
    tasks: list[EnergyTask]
    total_available: int


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


@router.post("/weekly-review/complete", response_model=WeeklyReviewCompletionItem)
def complete_weekly_review(
    body: WeeklyReviewCompleteRequest | None = None,
    db: Session = Depends(get_db),
):
    """
    Mark weekly review as complete. Persists a completion record.

    BETA-030: Weekly review completion tracking.
    """
    from app.models.weekly_review import WeeklyReviewCompletion

    completion = WeeklyReviewCompletion(
        completed_at=datetime.now(timezone.utc),
        notes=body.notes if body else None,
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)

    return WeeklyReviewCompletionItem(
        id=completion.id,
        completed_at=completion.completed_at.isoformat(),
        notes=completion.notes,
    )


@router.get("/weekly-review/history", response_model=WeeklyReviewHistoryResponse)
def get_weekly_review_history(
    limit: int = Query(10, ge=1, le=52, description="Number of completions to return"),
    db: Session = Depends(get_db),
):
    """
    Get weekly review completion history.

    Returns recent completions and days since last review.
    BETA-030.
    """
    from app.models.weekly_review import WeeklyReviewCompletion

    completions = db.execute(
        select(WeeklyReviewCompletion)
        .order_by(WeeklyReviewCompletion.completed_at.desc())
        .limit(limit)
    ).scalars().all()

    last_completed_at = None
    days_since = None
    if completions:
        last_dt = completions[0].completed_at
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=timezone.utc)
        last_completed_at = last_dt.isoformat()
        days_since = (datetime.now(timezone.utc) - last_dt).days

    return WeeklyReviewHistoryResponse(
        completions=[
            WeeklyReviewCompletionItem(
                id=c.id,
                completed_at=c.completed_at.isoformat() if c.completed_at else "",
                notes=c.notes,
            )
            for c in completions
        ],
        last_completed_at=last_completed_at,
        days_since_last_review=days_since,
    )


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


@router.post("/ai/proactive-analysis", response_model=ProactiveAnalysisResponse)
def proactive_stalled_analysis(
    limit: int = Query(5, ge=1, le=10, description="Max projects to analyze"),
    db: Session = Depends(get_db),
):
    """
    Proactively analyze declining and stalled projects with AI.

    Finds projects that are stalled or declining in momentum and generates
    AI-powered insights and recommended actions for each.

    ROADMAP-002: Proactive stalled project analysis.
    """
    if not settings.AI_FEATURES_ENABLED:
        raise HTTPException(status_code=400, detail="AI features not enabled")

    # Find stalled + declining projects
    active_projects = (
        db.execute(select(Project).where(Project.status == "active"))
        .scalars()
        .all()
    )

    # Prioritize: stalled first, then declining trend, then low momentum
    candidates = []
    for p in active_projects:
        trend = _compute_trend(p.momentum_score or 0.0, p.previous_momentum_score)
        priority = 0
        if p.stalled_since:
            priority = 3  # Stalled — highest priority
        elif trend == "falling":
            priority = 2  # Declining
        elif (p.momentum_score or 0.0) < 0.3:
            priority = 1  # Low momentum
        else:
            continue  # Skip healthy projects
        candidates.append((priority, p, trend))

    # Sort by priority descending, take top N
    candidates.sort(key=lambda x: x[0], reverse=True)
    targets = candidates[:limit]

    if not targets:
        return ProactiveAnalysisResponse(projects_analyzed=0, insights=[])

    from app.services.ai_service import AIService

    try:
        ai_service = AIService()
    except Exception:
        # AI not configured — return insights without AI analysis
        insights = [
            ProactiveInsight(
                project_id=p.id,
                project_title=p.title,
                momentum_score=p.momentum_score or 0.0,
                trend=trend,
                error="AI not configured",
            )
            for _, p, trend in targets
        ]
        return ProactiveAnalysisResponse(
            projects_analyzed=len(insights), insights=insights
        )

    insights: list[ProactiveInsight] = []
    for _, project, trend in targets:
        try:
            result = ai_service.analyze_project_health(db, project)
            suggestion = ai_service.suggest_next_action(db, project)
            insights.append(
                ProactiveInsight(
                    project_id=project.id,
                    project_title=project.title,
                    momentum_score=project.momentum_score or 0.0,
                    trend=trend,
                    analysis=result.get("analysis", ""),
                    recommended_action=suggestion,
                )
            )
        except Exception as e:
            logger.warning(f"Proactive analysis failed for project {project.id}: {e}")
            insights.append(
                ProactiveInsight(
                    project_id=project.id,
                    project_title=project.title,
                    momentum_score=project.momentum_score or 0.0,
                    trend=trend,
                    error=str(e),
                )
            )

    return ProactiveAnalysisResponse(
        projects_analyzed=len(insights), insights=insights
    )


@router.post("/ai/decompose-tasks/{project_id}", response_model=TaskDecompositionResponse)
def decompose_brainstorm_to_tasks(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Use AI to decompose brainstorm/organizing notes into concrete tasks.

    Reads the project's brainstorm_notes and organizing_notes, then uses AI
    to generate a list of actionable tasks with estimated effort and energy levels.

    ROADMAP-002: AI task decomposition from brainstorm notes (NPM Step 3 → tasks).
    """
    if not settings.AI_FEATURES_ENABLED:
        raise HTTPException(status_code=400, detail="AI features not enabled")

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    notes = (project.brainstorm_notes or "").strip()
    organizing = (project.organizing_notes or "").strip()

    if not notes and not organizing:
        raise HTTPException(
            status_code=400,
            detail="Project has no brainstorm or organizing notes to decompose",
        )

    source_text = ""
    source_label = "brainstorm_notes"
    if notes:
        source_text += f"Brainstorm Notes:\n{notes}\n\n"
    if organizing:
        source_text += f"Organizing Notes:\n{organizing}\n\n"
        if not notes:
            source_label = "organizing_notes"

    from app.services.ai_service import AIService

    try:
        ai_service = AIService()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AI not configured: {e}")

    # Get existing tasks to avoid duplicates
    from app.models.task import Task as TaskModel

    existing_tasks = (
        db.execute(
            select(TaskModel)
            .where(TaskModel.project_id == project_id, TaskModel.status != "cancelled")
            .limit(20)
        )
        .scalars()
        .all()
    )
    existing_titles = [t.title for t in existing_tasks]

    prompt = f"""Decompose the following project notes into concrete, actionable tasks.

Project: {project.title}
Purpose: {project.purpose or 'Not specified'}
Vision: {project.vision_statement or 'Not specified'}

{source_text}

Existing tasks (avoid duplicates):
{chr(10).join(f'- {t}' for t in existing_titles[:10]) if existing_titles else '- None'}

Generate 3-8 concrete tasks from these notes. For each task, provide:
- title: A clear, actionable task title (max 80 chars, start with a verb)
- estimated_minutes: Estimated time (15, 30, 60, 120, or 240)
- energy_level: Required energy (high, medium, or low)
- context: Best context (deep_work, creative, administrative, communication, research, or quick_win)

Format each task as exactly one line:
TASK: [title] | [minutes] | [energy] | [context]

Example:
TASK: Draft initial outline for chapter 3 | 60 | high | deep_work
TASK: Send follow-up email to reviewer | 15 | low | communication

Return ONLY TASK lines, nothing else."""

    try:
        response = ai_service.provider.generate(prompt, max_tokens=800, temperature=0.7)
        tasks: list[DecomposedTask] = []
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line.startswith("TASK:"):
                continue
            parts = line[5:].strip().split("|")
            title = parts[0].strip() if len(parts) > 0 else ""
            if not title:
                continue
            minutes = None
            energy = None
            context = None
            if len(parts) > 1:
                try:
                    minutes = int(parts[1].strip())
                except (ValueError, IndexError):
                    pass
            if len(parts) > 2:
                e = parts[2].strip().lower()
                if e in ("high", "medium", "low"):
                    energy = e
            if len(parts) > 3:
                c = parts[3].strip().lower()
                if c in ("deep_work", "creative", "administrative", "communication", "research", "quick_win"):
                    context = c
            tasks.append(
                DecomposedTask(
                    title=title[:80],
                    estimated_minutes=minutes,
                    energy_level=energy,
                    context=context,
                )
            )

        return TaskDecompositionResponse(
            project_id=project_id,
            tasks=tasks,
            source=source_label,
        )
    except Exception as e:
        logger.error(f"Task decomposition failed for project {project_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Task decomposition failed: {str(e)}"
        )


@router.get("/ai/rebalance-suggestions", response_model=RebalanceResponse)
def get_rebalance_suggestions(
    threshold: int = Query(7, ge=3, le=20, description="Max items before Opportunity Now overflows"),
    db: Session = Depends(get_db),
):
    """
    Suggest priority rebalancing when Opportunity Now zone overflows.

    Analyzes tasks in the Opportunity Now urgency zone across all active projects.
    When the count exceeds the threshold, suggests which tasks to demote to
    Over the Horizon or promote to Critical Now.

    ROADMAP-002: Priority rebalancing suggestions.
    """
    from app.models.task import Task as TaskModel

    # Count Opportunity Now tasks across active projects
    opportunity_tasks = (
        db.execute(
            select(TaskModel)
            .join(Project, TaskModel.project_id == Project.id)
            .where(
                Project.status == "active",
                TaskModel.status == "pending",
                TaskModel.is_next_action.is_(True),
                TaskModel.urgency_zone == "opportunity_now",
            )
            .options(joinedload(TaskModel.project))
        )
        .unique()
        .scalars()
        .all()
    )

    on_count = len(opportunity_tasks)
    if on_count <= threshold:
        return RebalanceResponse(
            opportunity_now_count=on_count,
            threshold=threshold,
            suggestions=[],
        )

    # Generate suggestions — rank tasks by staleness/priority
    now = datetime.now(timezone.utc)
    scored: list[tuple[float, TaskModel]] = []
    for t in opportunity_tasks:
        score = 0.0
        # Older tasks should be demoted first
        created = _ensure_tz_aware(t.created_at) if t.created_at else None
        if created:
            age_days = (now - created).total_seconds() / 86400
            score += min(age_days / 30, 1.0) * 0.4  # Older → more demotable

        # Lower priority tasks demoted first
        score += (t.priority or 5) / 10 * 0.3

        # Tasks from low-momentum projects demoted first
        if t.project and t.project.momentum_score is not None:
            score += (1.0 - t.project.momentum_score) * 0.3

        scored.append((score, t))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Suggest demoting the excess tasks
    excess = on_count - threshold
    suggestions: list[RebalanceSuggestion] = []

    # Tasks with due dates coming up should be promoted to Critical Now
    for _, t in scored:
        if t.due_date:
            due = _ensure_tz_aware(t.due_date) if isinstance(t.due_date, datetime) else None
            if due and (due - now).days <= 3:
                suggestions.append(
                    RebalanceSuggestion(
                        task_id=t.id,
                        task_title=t.title,
                        project_title=t.project.title if t.project else "Unknown",
                        current_zone="opportunity_now",
                        suggested_zone="critical_now",
                        reason=f"Due in {(due - now).days} days",
                    )
                )
                excess -= 1
        if excess <= 0:
            break

    # Remaining excess: demote to Over the Horizon
    if excess > 0:
        already_suggested = {s.task_id for s in suggestions}
        for _, t in scored:
            if t.id in already_suggested:
                continue
            if excess <= 0:
                break
            reason_parts = []
            created = _ensure_tz_aware(t.created_at) if t.created_at else None
            if created:
                age = (now - created).days
                if age > 7:
                    reason_parts.append(f"Created {age}d ago")
            if t.project and (t.project.momentum_score or 0) < 0.3:
                reason_parts.append("Low project momentum")
            if not reason_parts:
                reason_parts.append("Lower priority")
            suggestions.append(
                RebalanceSuggestion(
                    task_id=t.id,
                    task_title=t.title,
                    project_title=t.project.title if t.project else "Unknown",
                    current_zone="opportunity_now",
                    suggested_zone="over_the_horizon",
                    reason="; ".join(reason_parts),
                )
            )
            excess -= 1

    return RebalanceResponse(
        opportunity_now_count=on_count,
        threshold=threshold,
        suggestions=suggestions,
    )


@router.get("/ai/energy-recommendations", response_model=EnergyRecommendationResponse)
def get_energy_recommendations(
    energy_level: str = Query("low", description="Current energy level: high, medium, or low"),
    limit: int = Query(5, ge=1, le=15, description="Max tasks to return"),
    db: Session = Depends(get_db),
):
    """
    Get task recommendations matched to current energy level.

    Returns actionable tasks filtered and sorted by energy compatibility.
    Low energy → quick wins, administrative tasks
    Medium energy → standard tasks, communication
    High energy → deep work, creative tasks

    ROADMAP-002: Energy-matched task recommendations.
    """
    from app.models.task import Task as TaskModel

    if energy_level not in ("high", "medium", "low"):
        raise HTTPException(status_code=400, detail="energy_level must be high, medium, or low")

    now = datetime.now(timezone.utc)
    today = now.date()

    # Base query: pending next actions from active projects, not deferred
    base_query = (
        select(TaskModel)
        .join(Project, TaskModel.project_id == Project.id)
        .where(
            Project.status == "active",
            TaskModel.status == "pending",
            TaskModel.is_next_action.is_(True),
        )
        .options(joinedload(TaskModel.project))
    )

    # Exclude deferred tasks
    base_query = base_query.where(
        (TaskModel.defer_until.is_(None)) | (TaskModel.defer_until <= today)
    )

    all_tasks = db.execute(base_query).unique().scalars().all()

    # Score tasks by energy match
    scored: list[tuple[float, TaskModel]] = []
    for t in all_tasks:
        score = 0.0
        t_energy = (t.energy_level or "medium").lower()
        t_context = (t.context or "").lower()
        t_minutes = t.estimated_minutes or 30

        if energy_level == "low":
            # Prefer: low energy, quick tasks, admin/quick_win
            if t_energy == "low":
                score += 1.0
            elif t_energy == "medium":
                score += 0.4
            else:
                score += 0.1
            if t_minutes <= 15:
                score += 0.5
            elif t_minutes <= 30:
                score += 0.3
            if t_context in ("quick_win", "administrative", "communication"):
                score += 0.3

        elif energy_level == "medium":
            # Prefer: medium energy, moderate tasks
            if t_energy == "medium":
                score += 1.0
            elif t_energy == "low":
                score += 0.6
            else:
                score += 0.3
            if 15 <= t_minutes <= 60:
                score += 0.3
            if t_context in ("communication", "research", "administrative"):
                score += 0.2

        else:  # high
            # Prefer: high energy, deep work, longer tasks
            if t_energy == "high":
                score += 1.0
            elif t_energy == "medium":
                score += 0.5
            else:
                score += 0.1
            if t_minutes >= 60:
                score += 0.4
            elif t_minutes >= 30:
                score += 0.2
            if t_context in ("deep_work", "creative", "research"):
                score += 0.3

        # Boost tasks from higher-momentum projects
        if t.project and t.project.momentum_score:
            score += t.project.momentum_score * 0.2

        scored.append((score, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_tasks = scored[:limit]

    return EnergyRecommendationResponse(
        energy_level=energy_level,
        tasks=[
            EnergyTask(
                task_id=t.id,
                task_title=t.title,
                project_id=t.project_id,
                project_title=t.project.title if t.project else "Unknown",
                energy_level=t.energy_level,
                estimated_minutes=t.estimated_minutes,
                context=t.context,
                urgency_zone=t.urgency_zone,
            )
            for _, t in top_tasks
        ],
        total_available=len(all_tasks),
    )
