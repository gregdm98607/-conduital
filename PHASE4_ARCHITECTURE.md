# Phase 4: Intelligence Layer — Architecture Document

**Created:** 2026-02-02  
**Author:** Alfred Tarski (OpenClaw) + Greg Maxfield  
**Status:** Planning → Implementation

---

## Executive Summary

Phase 4 (Intelligence Layer) is **~70% complete**. Core algorithms exist and work. This document identifies gaps and proposes enhancements.

---

## Current State Assessment

### ✅ Implemented & Working

| Component | Status | Notes |
|-----------|--------|-------|
| Momentum Score Algorithm | ✅ | 4-factor weighted score (0.0-1.0) |
| Stalled Project Detection | ✅ | Auto-detects based on inactivity threshold |
| Unstuck Task Generation | ✅ | Non-AI fallback + AI-powered version |
| AI Service (Claude API) | ✅ | Health analysis, next action suggestions |
| Weekly Review Data | ✅ | GTD-style review summary |
| Intelligence API | ✅ | 7 endpoints exposed |

### ⏳ Gaps Identified

| Gap | Priority | Effort | Description |
|-----|----------|--------|-------------|
| MYN Urgency Zones | High | Medium | Critical Now / Opportunity Now / Over Horizon |
| Momentum History | Medium | Low | Track momentum over time for trends |
| Proactive Alerts | Medium | Medium | Notify when project at risk (before stalled) |
| Smart Scheduling | Low | High | Energy/time-aware task suggestions |
| Learning Loop | Low | High | Track which unstuck tasks actually worked |

---

## Architecture Decisions

### Decision 1: MYN Urgency Zone Integration

**Context:** The backlog shows MYN urgency zones (BACKLOG-019, 020, 022) as high priority. Tasks have `defer_until` but no urgency classification.

**Decision:** Add `urgency_zone` computed property to Task model.

**Implementation:**
```python
# In task.py model
@property
def urgency_zone(self) -> str:
    """
    MYN Urgency Zone classification:
    - critical_now: Due today OR marked critical
    - opportunity_now: Available today, not critical
    - over_horizon: Future start date OR someday/maybe
    """
    today = date.today()
    
    # Over the Horizon: future start date
    if self.defer_until and self.defer_until > today:
        return "over_horizon"
    
    # Someday/Maybe tasks
    if self.task_type == "someday_maybe":
        return "over_horizon"
    
    # Critical Now: due today or marked critical
    if self.is_critical_now or (self.due_date and self.due_date <= today):
        return "critical_now"
    
    # Opportunity Now: available, not critical
    return "opportunity_now"
```

**API Changes:**
- Add `GET /api/v1/next-actions/by-zone` endpoint
- Add zone filter to existing endpoints
- Dashboard widget showing zone counts

---

### Decision 2: Momentum History Tracking

**Context:** Current momentum is point-in-time only. Can't see if project is improving or declining.

**Decision:** Add `MomentumSnapshot` model to track daily momentum.

**Implementation:**
```python
class MomentumSnapshot(Base, TimestampMixin):
    """Daily momentum snapshots for trend analysis"""
    __tablename__ = "momentum_snapshots"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    snapshot_date: Mapped[date]
    momentum_score: Mapped[float]
    factors: Mapped[dict]  # JSON breakdown of score components
    
    __table_args__ = (
        UniqueConstraint("project_id", "snapshot_date"),
    )
```

**Capture Strategy:**
- Cron job or scheduled task captures daily at midnight
- Keep 90 days of history (configurable)
- API endpoint: `GET /api/v1/intelligence/momentum/{project_id}/history`

---

### Decision 3: Proactive Alert System

**Context:** Currently, projects are flagged as "stalled" only after they've been inactive for 14 days. Need earlier warning.

**Decision:** Add "at risk" detection with configurable thresholds.

**Implementation:**
```python
# In config.py - already exists but let's use it better
MOMENTUM_AT_RISK_THRESHOLD_DAYS = 7  # Warning before stalled
MOMENTUM_STALLED_THRESHOLD_DAYS = 14  # Current stall threshold

# Health status progression:
# strong (>0.7) → moderate (0.4-0.7) → weak (<0.4) → at_risk (7+ days) → stalled (14+ days)
```

**Alert Types:**
1. **At Risk Alert:** Project inactive 7+ days
2. **No Next Action Alert:** Active project without defined next action
3. **Overdue Alert:** Tasks past due date
4. **Momentum Decline Alert:** Score dropped >0.2 in a week

**Delivery Options (Future):**
- In-app dashboard widget
- Email digest (daily/weekly)
- Integration with external systems (OpenClaw, etc.)

---

### Decision 4: Next Action Prioritization Enhancement

**Context:** `NextActionsService` exists but prioritization could be smarter.

**Decision:** Enhance prioritization with MYN + GTD hybrid approach.

**Current Tiers:**
1. Tier 0: Unstuck tasks (stalled projects)
2. Tier 1: Due within 3 days
3. Tier 2: Marked as next action
4. Tier 3: Two-minute tasks
5. Tier 4: Context-matched

**Enhanced Tiers:**
1. **Critical Now:** Due today + critical flag
2. **Unstuck:** Stalled project restarters
3. **Overdue:** Past due date
4. **Due Soon:** Due within 3 days
5. **Opportunity Now:** Available today, context-matched
6. **Quick Wins:** Two-minute + low energy
7. **Deep Work:** High energy, focus required

---

### Decision 5: AI Enhancement Strategy

**Context:** AI service exists but could be more helpful.

**Enhancements:**
1. **Batch Analysis:** Analyze all projects in one call (cost-effective)
2. **Pattern Recognition:** "You tend to stall on research phases"
3. **Personalized Suggestions:** Learn from completed tasks
4. **Natural Language Queries:** "What should I work on if I have 30 minutes and low energy?"

**Deferred (Future):**
- These are valuable but complex
- Focus on MYN zones and alerts first
- AI enhancements in Phase 4.5 or 5

---

## Implementation Priority

### Sprint 1: MYN Zones (High Impact, Medium Effort)
- [ ] Add `urgency_zone` computed property to Task
- [ ] Add `is_critical_now` field to Task model (migration)
- [ ] Create `/next-actions/by-zone` endpoint
- [ ] Update dashboard to show zone breakdown
- [ ] Add zone filter to task list UI

### Sprint 2: Proactive Alerts (Medium Impact, Medium Effort)
- [ ] Implement "at risk" detection in intelligence service
- [ ] Create alerts summary endpoint
- [ ] Add dashboard alerts widget
- [ ] Add "Projects Needing Attention" view

### Sprint 3: Momentum History (Medium Impact, Low Effort)
- [ ] Create `MomentumSnapshot` model + migration
- [ ] Implement daily snapshot capture
- [ ] Create history API endpoint
- [ ] Add momentum trend chart to project detail

### Sprint 4: Polish & Integration (Ongoing)
- [ ] Write tests for all new features
- [ ] Documentation updates
- [ ] Performance optimization
- [ ] UI polish

---

## Testing Strategy

### Unit Tests
- Urgency zone calculation edge cases
- Momentum calculation accuracy
- Alert threshold triggers

### Integration Tests
- API endpoint responses
- Database operations
- AI service mocking

### E2E Tests (Phase 5)
- Full workflow: create project → add tasks → track momentum → receive alerts

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Stalled projects detected early | 80% caught at "at risk" | Compare at_risk → stalled transitions |
| Critical Now accuracy | <5 tasks/day | User feedback on zone assignments |
| Momentum trend visibility | 90% of projects | Projects with 7+ day history |
| AI suggestion acceptance | >50% | Track unstuck task completion rates |

---

## Open Questions

1. **Q:** Should momentum snapshots be per-project or global summary?
   **A:** Per-project (enables trend analysis per project)

2. **Q:** How to handle timezone for "today" in urgency zones?
   **A:** Use user's configured timezone (stored in settings)

3. **Q:** Should alerts be persistent (dismissible) or regenerated each view?
   **A:** Regenerated - simpler, always current

---

## Appendix: Existing Code Locations

| Component | File |
|-----------|------|
| Intelligence Service | `backend/app/services/intelligence_service.py` |
| AI Service | `backend/app/services/ai_service.py` |
| Intelligence API | `backend/app/api/intelligence.py` |
| Next Actions Service | `backend/app/services/next_actions_service.py` |
| Task Model | `backend/app/models/task.py` |
| Project Model | `backend/app/models/project.py` |
| Config (thresholds) | `backend/app/core/config.py` |

---

**Next Step:** Review this document, make decisions on open questions, then update `backlog.md` with prioritized implementation items.
