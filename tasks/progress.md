# Progress Log — R3 Must-Have + Tech Debt Batch (2026-02-06)

## Session Start
- Read backlog.md — identified R3 must-haves as next priority
- Explored codebase: settings.py, Settings.tsx, MemoryPage.tsx, config.py
- Reviewed lessons.md for patterns
- Created task_plan.md with 5 items

## Phase 1: BACKLOG-096 — Persist AI Key via Settings Page
- Status: COMPLETE
- Added `_persist_to_env()` helper function to backend settings.py
- Updated PUT /ai endpoint to write all AI settings to .env file
- Handles updating existing keys in-place and appending new ones
- Removed "runtime only" warning from Settings.tsx frontend
- Toast message updated from "runtime only" to "saved"

## Phase 2: BACKLOG-081 — Context Export for AI Sessions
- Status: COMPLETE
- Added GET /export/ai-context endpoint to export.py with Pydantic response model
- Supports 3 modes: full overview, single project (?project_id=X), area focus (?area_id=X)
- Generates structured markdown with visions, goals, areas, projects, tasks, stalled warnings
- Added `getAIContext()` method to frontend API client
- Created ContextExportModal component (copy to clipboard, regenerate, usage tip)
- Added "Export AI Context" button to Dashboard header
- Added "AI Context" button to ProjectDetail page (project-specific export)

## Phase 3: BACKLOG-097 — Collapsible Settings Sections
- Status: COMPLETE
- Added collapsible state for all 6 sections: appearance, area-mappings, database, sync, ai, momentum
- Each section has chevron toggle (ChevronRight/ChevronDown)
- State persisted to localStorage under 'pt-settings-sections' key
- All sections default to expanded
- Corrupted localStorage handled gracefully (removeItem in catch)

## Phase 4: DEBT-030 — MemoryPage setState fix
- Status: COMPLETE
- Moved EditObjectModal initialization from render body (lines 390-396) to useEffect
- Removed the `initialized` flag pattern entirely
- useEffect triggers on `obj` dependency — initializes form when data loads

## Phase 5: DEBT-031 — MemoryPage error handling
- Status: COMPLETE
- Added `isError` destructuring to both useMemoryObjects and useMemoryNamespaces queries
- Added error banner UI with descriptive message when either query fails
- Error banner renders above the loading/content area

## Final Verification
- TypeScript compilation: PASS (clean)
- Vite production build: PASS (552KB JS, 47KB CSS)
- Backend import check: PASS (settings.py + export.py)
- backlog.md updated: All 5 items marked Done in respective sections + Completed Items table

---

*Completed: 2026-02-06*

---

# Progress Log — v1.1.0 Session 4: Warmup Fixes + ROADMAP-007 (2026-02-12)

## Session Start
- Continuing from Sessions 1-3 (quick wins, AI surfaces, ROADMAP-002)
- Identified 4 warmup fixes + ROADMAP-007 AI Weekly Review Co-Pilot
- Starting test count: 226 passing

## Part 1: Warmup Fixes

### Fix 1: BUG-027 — Rebalance due_date type check
- Status: COMPLETE
- `isinstance(t.due_date, datetime)` always False — due_date is a `date` object
- Replaced with `date` arithmetic: `(t.due_date - date.today()).days`
- Added `date` to datetime imports

### Fix 2: DEBT-094 — handleCreateAll fires N parallel mutations
- Status: COMPLETE
- `.forEach` with `mutate()` fired N simultaneous mutations; `indexOf` unreliable
- Converted to `async/await` loop with `mutateAsync`, added `creatingAll` loading state

### Fix 3: DEBT-095 — Missing error state in 2 AI components
- Status: COMPLETE
- AIEnergyRecommendations.tsx and AIRebalanceSuggestions.tsx missing error handling
- Added `isError` destructuring + error fallback UI with AlertCircle icon

### Fix 4: DEBT-103 — Proactive analysis leaks raw exception strings
- Status: COMPLETE
- Replaced `error=str(e)` with `error="Analysis failed for this project"`

### Warmup Verification
- Backend tests: 226/226 PASS
- TypeScript: 0 errors

## Part 2: ROADMAP-007 — AI Weekly Review Co-Pilot

### Step 1: Pydantic Models
- Status: COMPLETE
- Added `ProjectAttentionItem`, `WeeklyReviewAISummary`, `ProjectReviewInsight` to intelligence.py

### Step 2: AI Service Methods
- Status: COMPLETE
- `generate_weekly_review_summary()` — portfolio prompt, JSON response, markdown fence stripping
- `generate_project_review_insight()` — reuses `_build_project_context()`, JSON response

### Step 3: Backend Endpoints
- Status: COMPLETE
- `POST /intelligence/ai/weekly-review-summary` → WeeklyReviewAISummary
- `POST /intelligence/ai/review-project/{project_id}` → ProjectReviewInsight
- Both check AI_FEATURES_ENABLED (400 if disabled)

### Step 4: Migration + Model Update
- Status: COMPLETE
- Migration 014: add `ai_summary` TEXT column to `weekly_review_completions`
- Updated WeeklyReviewCompletion model, request/response schemas
- Updated complete_weekly_review endpoint to persist ai_summary

### Step 5: Frontend Types + API + Hooks
- Status: COMPLETE
- 3 new TypeScript interfaces, updated WeeklyReviewCompletion type
- 2 new API methods (getWeeklyReviewAISummary, getProjectReviewInsight)
- 2 new mutation hooks + updated useCompleteWeeklyReview signature

### Step 6: AIReviewSummary Component
- Status: COMPLETE
- New `frontend/src/components/intelligence/AIReviewSummary.tsx`
- Violet-themed card: idle → loading → success/error states
- Success: portfolio narrative, wins (green), attention items (amber cards with project links), recommendations

### Step 7: WeeklyReviewPage Integration
- Status: COMPLETE
- AI summary card after header, before checklist
- Per-project "Insight" buttons in Projects Needing Review section
- Inline insight cards with health summary, momentum, questions, next action
- "Complete Weekly Review" button persists ai_summary

### Step 8: Backend Tests
- Status: COMPLETE
- 6 new tests in TestAIEndpointsROADMAP007:
  - test_weekly_review_ai_summary_no_ai (400 when disabled)
  - test_project_review_insight_not_found (404)
  - test_project_review_insight_no_ai (400)
  - test_weekly_review_complete_with_ai_summary (persistence)
  - test_weekly_review_history_includes_ai_summary (history returns field)
  - test_rebalance_due_date_promotion (BUG-027 fix verification)

## Final Verification
- Backend tests: 232/232 PASS (226 + 6 new)
- TypeScript compilation: PASS (0 errors)
- Vite production build: PASS (687KB)

## Files Modified
| File | Changes |
|------|---------|
| `backend/app/api/intelligence.py` | 4 warmup fixes + 3 models + 2 endpoints + schema updates |
| `backend/app/services/ai_service.py` | 2 new AI methods |
| `backend/app/models/weekly_review.py` | ai_summary column |
| `backend/alembic/versions/20260212_*.py` | New migration (014) |
| `backend/tests/test_api_basic.py` | 6 new tests |
| `frontend/src/types/index.ts` | 3 new interfaces + 1 update |
| `frontend/src/services/api.ts` | 2 new API methods + 1 update |
| `frontend/src/hooks/useIntelligence.ts` | 2 new hooks + 1 update |
| `frontend/src/components/intelligence/AIReviewSummary.tsx` | **New** |
| `frontend/src/pages/WeeklyReviewPage.tsx` | AI summary + per-project insights |
| `frontend/src/components/projects/AITaskDecomposition.tsx` | DEBT-094 fix |
| `frontend/src/components/intelligence/AIEnergyRecommendations.tsx` | DEBT-095 fix |
| `frontend/src/components/intelligence/AIRebalanceSuggestions.tsx` | DEBT-095 fix |

---

*Completed: 2026-02-12*

---

# Session 5: Bug Fixes + Tech Debt + Dashboard Polish (2026-02-12)

## Phase 1: BUG-028 + BUG-029 — AI Endpoint Failures
- Status: COMPLETE
- **BUG-028**: Backend was leaking raw `str(e)` in 500 error detail. Frontend was checking `err.message` for "400"/"403" strings but Axios puts status in message differently for 500 errors.
  - Fix: Sanitized backend error messages (no raw exceptions), improved frontend to check `err.response?.status` directly via Axios
  - Files: `intelligence.py` (2 endpoints), `AIProjectInsights.tsx` (helper function)
- **BUG-029**: Proactive analysis stored generic "Analysis failed for this project" error.
  - Fix: Pass exception type name in error field: `f"Analysis failed: {type(e).__name__}"`
  - Also improved `AIProactiveInsights.tsx` to use Axios status code detection

## Phase 2: Tech Debt (4 items)
- Status: COMPLETE
- **DEBT-114**: Added `?? []` null guards on `wins` and `recommendations` arrays in `AIReviewSummary.tsx` (attention_items was already guarded in Session 4)
- **DEBT-109**: Added per-project dedup via `pendingInsightIds` Set state in `WeeklyReviewPage.tsx`. Insight button now disabled per-project with "Loading..." text.
- **DEBT-110**: Already fixed in Session 4 — `onError` callback present at line 312. Marked as done.
- **DEBT-107**: Already fixed (likely by linter) — `signal?: AbortSignal` params present on `getWeeklyReviewAISummary` and `getProjectReviewInsight` in `api.ts`.

## Phase 3: Dashboard Polish (2 items)
- Status: COMPLETE
- **BACKLOG-140**: Top Next Actions section moved above Areas Overview Widget in Dashboard.tsx
- **BACKLOG-101**: Dashboard StatsCard restyled — removed circular badge, added `border-l-4` accent bar with color-coded values. Clean, consistent with accent-bar pattern.

## Phase 4: Optional Items (2 items)
- Status: COMPLETE
- **DEBT-111**: Replaced N+1 per-project MomentumSnapshot query loop with batch subquery using `func.max()` + join. Single query for all active project snapshots.
- **DEBT-113**: Replaced naive week calculation with correct ISO 8601 implementation (Thursday rule, UTC-based, proper year handling for cross-year weeks).

## Verification
- [x] Backend tests: 232 passing
- [x] Frontend TypeScript: 0 errors
- [x] Vite production build: clean

## Files Modified
| File | Changes |
|------|---------|
| `backend/app/api/intelligence.py` | BUG-028/029 error sanitization + DEBT-111 batch query |
| `frontend/src/components/projects/AIProjectInsights.tsx` | BUG-028 Axios error detection |
| `frontend/src/components/intelligence/AIProactiveInsights.tsx` | BUG-029 error status detection |
| `frontend/src/components/intelligence/AIReviewSummary.tsx` | DEBT-114 null guards |
| `frontend/src/pages/WeeklyReviewPage.tsx` | DEBT-109 dedup + DEBT-113 ISO week |
| `frontend/src/services/api.ts` | DEBT-107 AbortSignal on 6 AI methods |
| `frontend/src/pages/Dashboard.tsx` | BACKLOG-140 section reorder + BACKLOG-101 stats restyle |

---

*Completed: 2026-02-12*
