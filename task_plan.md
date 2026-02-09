# Task Plan: v1.0.0-beta Preparation

**Status:** in-progress
**Date:** 2026-02-09
**Goal:** Incremental beta release over v1.0.0-alpha — three pillars: Momentum Intelligence, GTD Inbox Enhancements, Distribution & Infrastructure.

---

## Current State

- **v1.0.0-alpha**: Shipped and distributed (2026-02-08)
- **Commits**: `4a69e62` (alpha + post-release), `fd5af5f` (cleanup + beta planning)
- **Tests**: 192/192 passing (100%)
- **Root directory**: Cleaned — historical docs archived to `archive/`
- **Tracking**: backlog.md, CHANGELOG.md, progress.md all current

---

## Pillar 1: Momentum Intelligence

### Phase 1A — Granularity Improvements

**Problem:** 70-80% of projects cluster into 4-5 indistinguishable momentum scores due to:
- Binary next-action gate (0 or 0.20 — cliff effect)
- Linear activity decay over 30 days (no nuance for recent vs stale)
- Hard 7-day window for completion ratio (cliff at boundary)
- Frequency capped at 10 actions / 14 days (saturation too easy)

**Current Formula:** `(Activity × 0.4) + (Completion × 0.3) + (NextAction × 0.2) + (Frequency × 0.1)`
**Location:** `backend/app/services/intelligence_service.py`

| ID | Task | Priority |
|----|------|----------|
| BETA-001 | **Graduated next-action scoring** — replace binary 0/1 with graduated scale: 0 (none), 0.3 (has next action but stale >7d), 0.7 (recent next action 1-7d), 1.0 (fresh <24h). Eliminates cliff effect. | ✅ Done |
| BETA-002 | **Exponential activity decay** — replace linear `1 - (days/30)` with exponential `e^(-days/7)`. Recent activity matters more; old activity fades faster. | ✅ Done |
| BETA-003 | **Sliding completion window** — replace hard 7-day window with weighted 30-day window: last 7d × 1.0, 8-14d × 0.5, 15-30d × 0.25. Prevents cliff at day 8. | ✅ Done |
| BETA-004 | **Logarithmic frequency scaling** — replace `min(1.0, count/10)` with `log(1 + count) / log(11)`. Makes each additional action worth less, harder to saturate. | ✅ Done |
| BETA-005 | **Task age weighting** — weight completed tasks by recency (completing old lingering tasks worth more). | Nice |

### Phase 1B — Motivation Signals (Psychology-Backed)

**Design Principle:** Subtle, informational, never gamified. No points, badges, streaks, or celebrations. Intrinsic motivation only.

**Psychology Foundations:**
- Progress Principle (Amabile & Kramer) — seeing progress is the #1 motivator
- Goal Gradient Effect (Hull) — effort accelerates as you approach completion
- Self-Determination Theory (Deci & Ryan) — autonomy, competence, relatedness
- Zeigarnik Effect — incomplete tasks create psychological tension
- Loss Aversion (Kahneman & Tversky) — protecting gains motivates more than seeking new ones

| ID | Task | Priority | Principle |
|----|------|----------|-----------|
| BETA-010 | **Momentum trend indicator** — small up/down/stable arrow next to score, based on delta. | ✅ Done | Progress Principle |
| BETA-011 | **Momentum sparkline** — inline SVG trend line on ProjectCard. | ✅ Done | Progress Principle |
| BETA-012 | **Project completion progress bar** — thin gradient bar on ProjectCard: `completed / total` tasks. | ✅ Done | Goal Gradient |
| BETA-013 | **"Almost there" nudge** — when >80% tasks complete, subtle text: "N tasks to finish line". | ✅ Done | Goal Gradient + Zeigarnik |
| BETA-014 | **Dashboard momentum summary** — "5 gaining, 2 steady, 1 declining" aggregate view. | ✅ Done | Progress Principle |
| BETA-015 | **Momentum history chart** — Settings or Dashboard widget: line chart of average momentum over 30/60/90 days. | Nice | Progress Principle |
| BETA-016 | **Streak-free activity heatmap** — GitHub-style contribution grid showing activity density. No streak counter — just the visual pattern. | Nice | Variable Ratio |
| BETA-017 | **Momentum protection framing** — when momentum is high, frame as "maintaining your progress" rather than "keep going". Loss aversion subtle cue. | Nice | Loss Aversion |

### Phase 1C — Data Model Additions

| ID | Task | Priority |
|----|------|----------|
| BETA-020 | Add `previous_momentum_score` column to projects table (for delta calculation) | ✅ Done |
| BETA-021 | Create `MomentumSnapshot` table (project_id, score, factors_json, timestamp) — daily snapshots for sparklines | ✅ Done |
| BETA-022 | Migration for both new tables/columns | ✅ Done |
| BETA-023 | Snapshot creation in scheduled recalculation job | ✅ Done |
| BETA-024 | API endpoints: `GET /intelligence/momentum-history/{id}`, `GET /intelligence/dashboard/momentum-summary` | ✅ Done |

---

## Pillar 2: GTD Inbox Enhancements

**Context:** GTD inbox is feature-complete for basic capture/clarify/process. R2 backlog items are marked complete. But there are meaningful enhancements for beta quality.

| ID | Task | Priority | Status |
|----|------|----------|--------|
| BETA-030 | **Weekly review completion tracking** — `POST /weekly-review/complete` stub → persist completion, track history, show on Dashboard | Must | ✅ Done |
| BETA-031 | **Inbox batch processing** — multi-select + bulk actions (assign, delete, convert) | Should | ✅ Done |
| BETA-032 | **Inbox processing stats endpoint** — `GET /inbox/stats` replaces client-side calc (DEBT-064) | Should | ✅ Done |
| BETA-033 | **Quick capture keyboard shortcut** — global `Ctrl+N` to open capture modal | Nice | Deferred |
| BETA-034 | **Inbox item age indicator** — subtle visual aging on unprocessed items (24h/3d/7d) | Nice | ✅ Done |

### Phase 2A: BETA-030 — Weekly Review Completion Tracking

**Backend:**
1. New model `WeeklyReviewCompletion` → `backend/app/models/weekly_review.py`
   - Fields: `id`, `user_id` (nullable FK), `completed_at` (DateTime tz), `notes` (Text optional)
   - Inherits `Base` only (completed_at IS the timestamp)
2. Register in `models/__init__.py` + `alembic/env.py`
3. Alembic migration `012_weekly_review_completion` (down_revision=`011_momentum_snapshots`)
4. Implement stub at `modules/gtd_inbox/routes.py:46-55` → persist to DB
5. Add `GET /weekly-review/history` endpoint (last N completions + days_since)
6. Tests: POST creates record, GET returns ordered history, days calculation

**Frontend:**
7. New API methods + hook: `completeWeeklyReview()`, `getWeeklyReviewHistory()`, `useWeeklyReviewHistory()`
8. Dashboard.tsx: "Last completed: X days ago" in review section

### Phase 2B: BETA-032 — Inbox Stats Endpoint

**Backend:**
1. `GET /inbox/stats` → `unprocessed_count`, `processed_today`, `avg_processing_time_hours`
2. Schema: `InboxStats` in `schemas/inbox.py`
3. Tests for stats calculation

**Frontend:**
4. `useInboxStats()` hook, `getInboxStats()` API method
5. InboxPage: replace client-side stats with API data

### Phase 2C: BETA-031 — Inbox Batch Processing

**Backend:**
1. `POST /inbox/batch-process` → `{ item_ids, action, project_id? }`
2. Actions: `assign_to_project`, `delete`, `convert_to_task`
3. Schema: `InboxBatchProcess` request, `InboxBatchResult` response
4. Tests: batch assign, batch delete, error cases

**Frontend:**
5. Multi-select checkboxes on inbox items
6. Bulk action toolbar: "Assign to Project", "Delete", "Convert to Tasks"
7. Selection state management

### Phase 2D: BETA-034 — Inbox Item Age Indicator

**Frontend only:**
1. Age tiers: <24h (none), 24h-3d (gray clock), 3d-7d (amber clock), >7d (red clock)
2. Subtle badge on unprocessed items only. Informational, not gamified.

---

## Pillar 3: Distribution & Infrastructure

### From distribution-checklist.md

| Phase | Item | Status |
|-------|------|--------|
| 4.3 | Privacy Policy draft | Not started |
| 5.1 | App icon (.ico, multiple sizes) | Not started |
| 5.1 | Screenshots (5-8 polished) | Not started |
| 5.1 | Product description | Not started |
| 5.2 | Pricing research & decision | Not started |
| 5.3 | Gumroad listing setup | Not started |
| 5.4 | Support infrastructure (FAQ, email) | Not started |
| 5.5 | Update mechanism | Not started |

### Testing

| Item | Status |
|------|--------|
| BACKLOG-118: Clean Windows 10 VM testing | Not started |
| BACKLOG-118: Clean Windows 11 VM testing | Not started |
| BACKLOG-117: Upgrade-in-place testing | Not started |

### Tech Debt (from backlog.md)

| ID | Description | Priority |
|----|-------------|----------|
| DEBT-007 | Soft delete for entities | Medium |
| DEBT-080 | Installer version not SSoT | Medium |
| DEBT-083 | Installer kills without graceful shutdown attempt | Medium |
| BACKLOG-116 | Version single source of truth | Medium |

### Code Quality & Polish

| ID | Description | Priority |
|----|-------------|----------|
| DEBT-013 | Mobile views not optimized | Low |
| DEBT-016 | WebSocket updates not integrated | Low |
| DEBT-039 | MemoryPage priority input out-of-range | Low |
| DEBT-061 | Dynamic attribute assignment fragility | Low |

---

## What's NOT in Beta Scope

- License key system (Phase 4.1) — shipping free, deferred to paid transition
- Code signing (Phase 3.1) — deferred, saves $200-500/year
- Multi-user/teams
- SaaS/cloud deployment
- Full R3/R4 features (memory layer improvements, AI weekly review advisors)

---

## Implementation Order (Suggested Sessions)

### Session 1: Momentum Granularity (Backend)
- BETA-001: Graduated next-action scoring
- BETA-002: Exponential activity decay
- BETA-003: Sliding completion window
- BETA-004: Logarithmic frequency scaling
- BETA-020/021/022/023: Data model additions + migration + snapshot job
- Run all 174+ tests, verify no regressions

### Session 2: Motivation Signals (Frontend + API)
- BETA-010: Trend indicator (up/down/stable arrow)
- BETA-011: Sparkline on ProjectCard
- BETA-012: Completion progress bar
- BETA-013: "Almost there" nudge
- BETA-014: Dashboard momentum summary
- BETA-024: History + summary API endpoints

### Session 3: GTD Inbox + Polish ← **CURRENT SESSION**
- BETA-030: Weekly review completion tracking
- BETA-031: Batch processing
- BETA-032: Processed Today stats endpoint
- BETA-034: Inbox item age indicator

### Session 4: Distribution & Testing
- Privacy policy, app icon, screenshots
- VM testing (Windows 10/11)
- Upgrade-in-place testing
- Installer graceful shutdown (DEBT-083)
- Version SSoT (BACKLOG-116)

---

## Anti-Patterns to Avoid

Per research on psychology-backed motivation:

- **No points/XP systems** — extrinsic reward undermines intrinsic motivation
- **No badges/achievements** — creates "achievement hunting" behavior
- **No streak counters** — creates anxiety about breaking streaks
- **No leaderboards** — single-user app, comparison is irrelevant
- **No celebration modals** — interrupts flow, feels patronizing
- **No daily login rewards** — creates obligation, not motivation
- **No loss penalties** — never punish the user for taking a break

The goal is to make the data *informative and visible*, not to gamify the experience.

---

*Last updated: 2026-02-09*
