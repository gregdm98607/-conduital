"""
Intelligence API endpoints - Momentum, stalled projects, AI features
"""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

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
from app.core.db_utils import ensure_tz_aware
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


class WeeklyReviewCompleteRequest(BaseModel):
    """Request for completing a weekly review (BETA-030)"""

    notes: str | None = None
    ai_summary: str | None = None


class WeeklyReviewCompletionItem(BaseModel):
    """Single weekly review completion record"""

    id: int
    completed_at: str
    notes: str | None = None
    ai_summary: str | None = None


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
    completion_streak_days: int


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


class MomentumHeatmapDay(BaseModel):
    """Single day in the momentum heatmap"""

    date: str  # YYYY-MM-DD
    avg_momentum: float  # 0.0-1.0 average across projects
    completions: int  # tasks completed that day


class MomentumHeatmapResponse(BaseModel):
    """Response for the daily momentum heatmap (BACKLOG-139)"""

    days: int
    data: list[MomentumHeatmapDay]


class ProjectAttentionItem(BaseModel):
    """A project flagged for attention during weekly review"""

    project_id: int
    project_title: str
    momentum_score: float
    trend: str
    reason: str
    suggested_action: str | None = None


class WeeklyReviewAISummary(BaseModel):
    """AI-generated weekly review summary"""

    portfolio_narrative: str
    wins: list[str]
    attention_items: list[ProjectAttentionItem]
    recommendations: list[str]
    generated_at: str


class ProjectReviewInsight(BaseModel):
    """AI-generated per-project review insight"""

    project_id: int
    project_title: str
    health_summary: str
    suggested_next_action: str | None = None
    questions_to_consider: list[str]
    momentum_context: str


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
        select(Project).where(Project.status == "active", Project.deleted_at.is_(None))
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
            Task.deleted_at.is_(None),
            Project.deleted_at.is_(None),
        )
    ).scalar() or 0

    # Calculate completion streak: consecutive days with at least 1 completed task
    from datetime import datetime, timezone, timedelta

    today = datetime.now(timezone.utc).date()
    streak = 0
    for days_ago in range(0, 90):  # Check up to 90 days back
        check_date = today - timedelta(days=days_ago)
        day_start = datetime(check_date.year, check_date.month, check_date.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        completed_count = db.execute(
            select(func.count(Task.id)).where(
                Task.status == "completed",
                Task.completed_at >= day_start,
                Task.completed_at < day_end,
                Task.deleted_at.is_(None),
            )
        ).scalar() or 0

        if completed_count > 0:
            streak += 1
        else:
            # If today has no completions, skip it (streak still counts from yesterday)
            if days_ago == 0:
                continue
            break

    return DashboardStatsResponse(
        active_project_count=active_count,
        pending_task_count=pending_count,
        avg_momentum=avg_momentum,
        orphan_project_count=orphan_count,
        completion_streak_days=streak,
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
    if not project or project.deleted_at is not None:
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
        db.execute(select(Project).where(Project.status == "active", Project.deleted_at.is_(None)))
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


@router.get("/momentum-heatmap", response_model=MomentumHeatmapResponse)
def get_momentum_heatmap(
    days: int = Query(90, ge=7, le=365, description="Number of days to show"),
    db: Session = Depends(get_db),
):
    """
    Get daily momentum heatmap data (BACKLOG-139).

    Returns an array of daily data points with:
    - avg_momentum: average momentum score across all active projects that day
    - completions: count of tasks completed that day
    """
    from collections import defaultdict
    from app.models.task import Task as TaskModel

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    # Get active project IDs (for filtering snapshots to non-deleted projects)
    active_project_ids = [
        row[0]
        for row in db.execute(
            select(Project.id).where(
                Project.status == "active", Project.deleted_at.is_(None)
            )
        ).all()
    ]

    # 1) Momentum snapshots grouped by date
    daily_scores: dict[str, list[float]] = defaultdict(list)
    if active_project_ids:
        snapshots = (
            db.execute(
                select(MomentumSnapshot)
                .where(
                    MomentumSnapshot.project_id.in_(active_project_ids),
                    MomentumSnapshot.snapshot_at >= cutoff,
                )
                .order_by(MomentumSnapshot.snapshot_at)
            )
            .scalars()
            .all()
        )
        for snap in snapshots:
            dt = ensure_tz_aware(snap.snapshot_at)
            date_str = dt.date().isoformat()
            daily_scores[date_str].append(snap.score)

    # 2) Task completions grouped by date (only from active, non-deleted projects)
    daily_completions: dict[str, int] = defaultdict(int)
    completion_query = select(TaskModel.completed_at).where(
        TaskModel.completed_at.is_not(None),
        TaskModel.completed_at >= cutoff,
        TaskModel.deleted_at.is_(None),
    )
    if active_project_ids:
        completion_query = completion_query.where(
            TaskModel.project_id.in_(active_project_ids)
        )
    else:
        # No active projects → no completions to count
        completion_query = completion_query.where(False)
    completion_rows = db.execute(completion_query).all()
    for (completed_at,) in completion_rows:
        dt = ensure_tz_aware(completed_at)
        date_str = dt.date().isoformat()
        daily_completions[date_str] += 1

    # 3) Build response — fill all days in range (sparse → dense)
    all_dates: set[str] = set()
    for d in range(days):
        all_dates.add((now - timedelta(days=d)).date().isoformat())

    data = []
    for date_str in sorted(all_dates):
        scores = daily_scores.get(date_str, [])
        avg = sum(scores) / len(scores) if scores else 0.0
        data.append(
            MomentumHeatmapDay(
                date=date_str,
                avg_momentum=round(avg, 3),
                completions=daily_completions.get(date_str, 0),
            )
        )

    return MomentumHeatmapResponse(days=days, data=data)


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
    if not project or project.deleted_at is not None:
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
    if not project or project.deleted_at is not None:
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
        .where(Project.id == project_id, Project.deleted_at.is_(None))
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
    now = datetime.now(timezone.utc)
    stalled = IntelligenceService.detect_stalled_projects(db)
    stalled_ids = {p.id for p in stalled}

    results = [
        {
            "id": p.id,
            "title": p.title,
            "momentum_score": p.momentum_score,
            "stalled_since": p.stalled_since.isoformat() if p.stalled_since else None,
            "days_stalled": (now - ensure_tz_aware(p.stalled_since)).days if p.stalled_since else None,
            "days_since_activity": (
                (now - ensure_tz_aware(p.last_activity_at)).days if p.last_activity_at else None
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
                Project.deleted_at.is_(None),
            )
        ).scalars().all()

        threshold = settings.MOMENTUM_AT_RISK_THRESHOLD_DAYS
        for p in active_projects:
            if p.id in stalled_ids:
                continue
            if p.last_activity_at:
                days_since = (now - ensure_tz_aware(p.last_activity_at)).days
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
    if not project or project.deleted_at is not None:
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
        db.commit()
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
        ai_summary=body.ai_summary if body else None,
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)

    return WeeklyReviewCompletionItem(
        id=completion.id,
        completed_at=completion.completed_at.isoformat(),
        notes=completion.notes,
        ai_summary=completion.ai_summary,
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
                ai_summary=c.ai_summary,
            )
            for c in completions
        ],
        last_completed_at=last_completed_at,
        days_since_last_review=days_since,
    )


@router.post("/ai/weekly-review-summary", response_model=WeeklyReviewAISummary)
def get_weekly_review_ai_summary(db: Session = Depends(get_db)):
    """
    Generate AI-powered weekly review summary.

    Analyzes portfolio health, identifies wins, flags projects needing attention,
    and provides actionable recommendations for the weekly review.

    Requires AI_FEATURES_ENABLED=true and a configured AI provider.
    """
    if not settings.AI_FEATURES_ENABLED:
        raise HTTPException(status_code=400, detail="AI features are not enabled")

    from app.services.ai_service import AIService
    from app.services.intelligence_service import IntelligenceService

    try:
        ai_service = AIService()
    except Exception:
        raise HTTPException(status_code=400, detail="AI service not configured")

    # Gather review data
    review_data = IntelligenceService.get_weekly_review_data(db)

    # Gather momentum data for all active projects
    active_projects = (
        db.execute(
            select(Project)
            .where(Project.status == "active", Project.deleted_at.is_(None))
            .options(joinedload(Project.tasks))
        )
        .unique()
        .scalars()
        .all()
    )

    now = datetime.now(timezone.utc)

    # Batch query: latest MomentumSnapshot per project (avoids N+1)
    project_ids = [p.id for p in active_projects]
    latest_snapshots: dict[int, float | None] = {}
    if project_ids:
        latest_snap_subq = (
            select(
                MomentumSnapshot.project_id,
                func.max(MomentumSnapshot.snapshot_at).label("max_at"),
            )
            .where(MomentumSnapshot.project_id.in_(project_ids))
            .group_by(MomentumSnapshot.project_id)
            .subquery()
        )
        snap_rows = db.execute(
            select(MomentumSnapshot.project_id, MomentumSnapshot.score)
            .join(
                latest_snap_subq,
                (MomentumSnapshot.project_id == latest_snap_subq.c.project_id)
                & (MomentumSnapshot.snapshot_at == latest_snap_subq.c.max_at),
            )
        ).all()
        for row in snap_rows:
            latest_snapshots[row[0]] = row[1]

    project_momentum_data = []
    for p in active_projects:
        days_since = None
        if p.last_activity_at:
            la = p.last_activity_at
            if la.tzinfo is None:
                la = la.replace(tzinfo=timezone.utc)
            days_since = (now - la).days

        prev_score = latest_snapshots.get(p.id)

        project_momentum_data.append({
            "id": p.id,
            "title": p.title,
            "score": p.momentum_score,
            "trend": _compute_trend(p.momentum_score, prev_score),
            "days_since_activity": days_since,
            "is_stalled": bool(p.stalled_since),
        })

    try:
        result = ai_service.generate_weekly_review_summary(review_data, project_momentum_data)
    except Exception as e:
        logger.error(f"AI weekly review summary failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI review summary")

    return WeeklyReviewAISummary(
        portfolio_narrative=result["portfolio_narrative"],
        wins=result["wins"],
        attention_items=[
            ProjectAttentionItem(**item) for item in result["attention_items"]
        ],
        recommendations=result["recommendations"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.post("/ai/review-project/{project_id}", response_model=ProjectReviewInsight)
def get_project_review_insight(project_id: int, db: Session = Depends(get_db)):
    """
    Generate AI-powered insight for a single project during weekly review.

    Provides health summary, suggested next action, and questions to consider.

    Requires AI_FEATURES_ENABLED=true and a configured AI provider.
    """
    if not settings.AI_FEATURES_ENABLED:
        raise HTTPException(status_code=400, detail="AI features are not enabled")

    project = db.execute(
        select(Project)
        .where(Project.id == project_id, Project.deleted_at.is_(None))
        .options(joinedload(Project.tasks), joinedload(Project.area))
    ).unique().scalars().first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.services.ai_service import AIService

    try:
        ai_service = AIService()
    except Exception:
        raise HTTPException(status_code=400, detail="AI service not configured")

    try:
        result = ai_service.generate_project_review_insight(db, project)
    except Exception as e:
        logger.error(f"AI project review insight failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate project insight")

    return ProjectReviewInsight(
        project_id=project.id,
        project_title=project.title,
        health_summary=result["health_summary"],
        suggested_next_action=result["suggested_next_action"],
        questions_to_consider=result["questions_to_consider"],
        momentum_context=result["momentum_context"],
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

    project = db.execute(
        select(Project)
        .where(Project.id == project_id, Project.deleted_at.is_(None))
        .options(joinedload(Project.tasks), joinedload(Project.area))
    ).unique().scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        from app.services.ai_service import AIService

        ai_service = AIService()
        result = ai_service.analyze_project_health(db, project)
        return AIAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"AI analysis failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail="AI analysis failed. Check server logs for details.")


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

    project = db.execute(
        select(Project)
        .where(Project.id == project_id, Project.deleted_at.is_(None))
        .options(joinedload(Project.tasks), joinedload(Project.area))
    ).unique().scalars().first()
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
            status_code=500, detail="AI suggestion failed. Check server logs for details."
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

    # Find stalled + declining projects (eager-load tasks+area for AI context)
    active_projects = (
        db.execute(
            select(Project)
            .where(Project.status == "active", Project.deleted_at.is_(None))
            .options(joinedload(Project.tasks), joinedload(Project.area))
        )
        .unique()
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
                    error=f"Analysis failed: {type(e).__name__}",
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
    if not project or project.deleted_at is not None:
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
        logger.warning("AI service init failed in decompose-tasks: %s", e)
        raise HTTPException(status_code=400, detail="AI features not configured. Add your Anthropic API key in Settings.")

    # Get existing tasks to avoid duplicates
    from app.models.task import Task as TaskModel

    existing_tasks = (
        db.execute(
            select(TaskModel)
            .where(TaskModel.project_id == project_id, TaskModel.status != "cancelled", TaskModel.deleted_at.is_(None))
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
            status_code=500, detail="Task decomposition failed due to an internal error."
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
                TaskModel.deleted_at.is_(None),
                Project.deleted_at.is_(None),
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
        created = ensure_tz_aware(t.created_at) if t.created_at else None
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
    today = date.today()
    for _, t in scored:
        if t.due_date:
            days_until = (t.due_date - today).days
            if days_until <= 3:
                suggestions.append(
                    RebalanceSuggestion(
                        task_id=t.id,
                        task_title=t.title,
                        project_title=t.project.title if t.project else "Unknown",
                        current_zone="opportunity_now",
                        suggested_zone="critical_now",
                        reason=f"Due in {days_until} day{'s' if days_until != 1 else ''}",
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
            created = ensure_tz_aware(t.created_at) if t.created_at else None
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
            TaskModel.deleted_at.is_(None),
            Project.deleted_at.is_(None),
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


# =============================================================================
# BACKLOG-082: Session Summary Capture
# =============================================================================


class MomentumDelta(BaseModel):
    """Momentum change for a project during a session"""

    project_name: str
    old_score: Optional[float] = None
    new_score: float


class SessionSummaryResponse(BaseModel):
    """Response for session summary endpoint"""

    session_start: str  # ISO datetime
    session_end: str  # ISO datetime
    tasks_completed: int
    tasks_created: int
    tasks_updated: int
    projects_touched: list[str]
    momentum_changes: list[MomentumDelta]
    activity_count: int
    summary_text: str
    persisted: bool = False
    memory_object_id: Optional[str] = None


@router.post("/session-summary", response_model=SessionSummaryResponse)
def capture_session_summary(
    session_start: Optional[str] = Query(None, description="Session start ISO timestamp (default: 4 hours ago)"),
    persist: bool = Query(False, description="Persist summary to memory layer"),
    notes: Optional[str] = Query(None, description="Optional user notes about the session"),
    db: Session = Depends(get_db),
):
    """
    Generate a session summary of what changed during a work session.

    Queries ActivityLog, completed tasks, created tasks, and momentum changes
    to build a template-based narrative summary. No AI dependency.

    When persist=True, stores the summary in the memory layer under the
    sessions.history namespace for cross-session continuity.

    BACKLOG-082: Session Summary Capture.
    """
    from app.models.activity_log import ActivityLog
    from app.models.task import Task as TaskModel

    now = datetime.now(timezone.utc)

    # Parse session_start or default to 4 hours ago
    if session_start:
        try:
            # Normalize timezone: "Z" -> "+00:00"
            normalized = session_start.strip().replace("Z", "+00:00")
            start = datetime.fromisoformat(normalized)
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid session_start format. Use ISO 8601.")
    else:
        start = now - timedelta(hours=4)

    # 1. Query ActivityLog for all entries since session_start
    activities = (
        db.execute(
            select(ActivityLog)
            .where(ActivityLog.timestamp >= start)
            .order_by(ActivityLog.timestamp)
        )
        .scalars()
        .all()
    )
    activity_count = len(activities)

    # Group by entity_type + action_type for summary
    action_groups: dict[str, int] = {}
    for a in activities:
        key = f"{a.entity_type}:{a.action_type}"
        action_groups[key] = action_groups.get(key, 0) + 1

    # 2. Tasks completed during session
    completed_tasks = (
        db.execute(
            select(TaskModel)
            .where(
                TaskModel.completed_at >= start,
                TaskModel.completed_at.is_not(None),
                TaskModel.deleted_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    tasks_completed = len(completed_tasks)

    # 3. Tasks created during session
    created_tasks = (
        db.execute(
            select(TaskModel)
            .where(
                TaskModel.created_at >= start,
                TaskModel.deleted_at.is_(None),
            )
        )
        .scalars()
        .all()
    )
    tasks_created = len(created_tasks)

    # Count updated tasks (from activity log)
    tasks_updated = action_groups.get("task:updated", 0)

    # 4. Projects touched during session
    touched_project_ids: set[int] = set()
    for t in completed_tasks:
        if t.project_id:
            touched_project_ids.add(t.project_id)
    for t in created_tasks:
        if t.project_id:
            touched_project_ids.add(t.project_id)

    # Also gather project IDs from activity log
    for a in activities:
        if a.entity_type == "project":
            touched_project_ids.add(a.entity_id)
        elif a.entity_type == "task":
            # Look up the task's project
            task = db.get(TaskModel, a.entity_id)
            if task and task.project_id:
                touched_project_ids.add(task.project_id)

    # Get project names
    projects_touched: list[str] = []
    if touched_project_ids:
        touched_projects = (
            db.execute(
                select(Project)
                .where(Project.id.in_(touched_project_ids))
            )
            .scalars()
            .all()
        )
        projects_touched = [p.title for p in touched_projects]

    # 5. Momentum deltas
    momentum_changes: list[MomentumDelta] = []
    if touched_project_ids:
        for pid in touched_project_ids:
            project = db.get(Project, pid)
            if not project:
                continue

            current_score = project.momentum_score or 0.0

            # Find snapshot closest to (but before) session_start
            old_snapshot = (
                db.execute(
                    select(MomentumSnapshot)
                    .where(
                        MomentumSnapshot.project_id == pid,
                        MomentumSnapshot.snapshot_at < start,
                    )
                    .order_by(MomentumSnapshot.snapshot_at.desc())
                    .limit(1)
                )
                .scalars()
                .first()
            )
            old_score = old_snapshot.score if old_snapshot else None

            # Only include if there's a meaningful change or no baseline
            if old_score is None or abs(current_score - old_score) > 0.001:
                momentum_changes.append(
                    MomentumDelta(
                        project_name=project.title,
                        old_score=old_score,
                        new_score=current_score,
                    )
                )

    # 6. Build summary text
    parts = []
    if tasks_completed > 0:
        project_count = len(projects_touched)
        parts.append(
            f"Completed {tasks_completed} task{'s' if tasks_completed != 1 else ''}"
            + (f" across {project_count} project{'s' if project_count != 1 else ''}" if project_count > 0 else "")
        )
    if tasks_created > 0:
        parts.append(f"Created {tasks_created} new task{'s' if tasks_created != 1 else ''}")
    for mc in momentum_changes:
        if mc.old_score is not None:
            delta = mc.new_score - mc.old_score
            direction = "+" if delta >= 0 else ""
            parts.append(f"Project '{mc.project_name}' momentum {direction}{delta:.2f}")

    if not parts:
        if activity_count > 0:
            parts.append(f"{activity_count} activity log entries recorded")
        else:
            parts.append("No activity recorded during this session")

    summary_text = ". ".join(parts) + "."

    # 7. Optionally persist to memory layer
    persisted = False
    memory_object_id = None

    if persist:
        try:
            from app.modules.memory_layer.services import MemoryService
            from app.modules.memory_layer.schemas import MemoryObjectCreate, MemoryObjectUpdate

            today = date.today()
            timestamp_str = now.strftime("%Y%m%d-%H%M")
            object_id = f"session-summary-{timestamp_str}"

            content = {
                "session_start": start.isoformat(),
                "session_end": now.isoformat(),
                "tasks_completed": tasks_completed,
                "tasks_created": tasks_created,
                "tasks_updated": tasks_updated,
                "projects_touched": projects_touched,
                "momentum_changes": [mc.model_dump() for mc in momentum_changes],
                "activity_count": activity_count,
                "summary_text": summary_text,
            }
            if notes:
                content["user_notes"] = notes

            # Create the session-specific memory object
            MemoryService.create_object(
                db,
                MemoryObjectCreate(
                    object_id=object_id,
                    namespace="sessions.history",
                    priority=60,
                    effective_from=today,
                    content=content,
                    tags=["session", "auto-generated"],
                ),
            )
            memory_object_id = object_id

            # Upsert session-latest (always holds most recent session)
            latest_id = "session-latest"
            existing_latest = MemoryService.get_object(db, latest_id)
            if existing_latest:
                MemoryService.update_object(
                    db,
                    latest_id,
                    MemoryObjectUpdate(
                        content=content,
                        priority=80,
                        tags=["session", "auto-generated", "latest"],
                    ),
                )
            else:
                MemoryService.create_object(
                    db,
                    MemoryObjectCreate(
                        object_id=latest_id,
                        namespace="sessions.history",
                        priority=80,
                        effective_from=today,
                        content=content,
                        tags=["session", "auto-generated", "latest"],
                    ),
                )

            persisted = True
        except Exception as e:
            logger.error(f"Failed to persist session summary to memory layer: {e}")
            # Don't fail the response — summary is still returned

    return SessionSummaryResponse(
        session_start=start.isoformat(),
        session_end=now.isoformat(),
        tasks_completed=tasks_completed,
        tasks_created=tasks_created,
        tasks_updated=tasks_updated,
        projects_touched=projects_touched,
        momentum_changes=momentum_changes,
        activity_count=activity_count,
        summary_text=summary_text,
        persisted=persisted,
        memory_object_id=memory_object_id,
    )
