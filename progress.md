# Progress Log

## Session: 2026-02-09 — Beta Session 4: Pillar 3 — Infrastructure & Polish

### Completed Items (9 items)

#### DEBT-083: Installer Graceful Shutdown
- `GracefulShutdown()` procedure in `installer/conduital.iss` replaces direct `taskkill /F`
- Step 1: Calls `POST http://127.0.0.1:52140/api/v1/shutdown` via PowerShell (5s timeout)
- Step 2: Waits up to 8 seconds for process to exit gracefully
- Step 3: Falls back to `taskkill /F` as safety net
- Both `InitializeSetup()` and `InitializeUninstall()` use the shared procedure

#### BACKLOG-116 / DEBT-080: Version Single Source of Truth
- `pyproject.toml` is the canonical version source
- `config.py` now reads version from `pyproject.toml` via `_read_version_from_pyproject()` at module load
- Falls back to `_FALLBACK_VERSION` constant for packaged builds (no pyproject.toml available)
- New `backend/scripts/sync_version.py` — propagates version to `package.json`, `conduital.iss`, `config.py` fallback
- Supports `--check` mode for CI validation (exit 1 if mismatch)

#### DEBT-039: MemoryPage Priority Input Out-of-Range
- All 3 priority input `onChange` handlers now clamp to `Math.min(100, Math.max(0, ...))`
- Locations: EditObjectModal, CreateObjectModal, CreateNamespaceModal
- Prevents users from typing values like -50 or 150

#### DEBT-061: Dynamic Attribute Assignment Fragility
- Added `task_count: int = 0` and `completed_task_count: int = 0` as explicit class attributes on `Project` model
- SQLAlchemy ignores these (not `Mapped[...]`), so no database impact
- Provides IDE autocomplete, prevents `AttributeError`, makes intent explicit
- Service layer still assigns values via query results — now overwrites defaults instead of creating dynamic attributes

#### DEBT-064: Marked Done
- Already fixed by BETA-032 (`GET /inbox/stats` endpoint replaces client-side calculation)
- Backlog updated to reflect completion

#### BACKLOG-120: "Make Next Action" Quick Action
- Added `handleBulkMakeNextAction` and `handleBulkDemoteToOther` handlers to ProjectDetail
- "→ Next Action" button shows when only Other Tasks are selected
- "→ Other" button shows when only Next Actions are selected
- Contextual buttons: appear/disappear based on selection composition

#### BACKLOG-119: Task Push/Defer Quick Action
- New `DeferPopover` component (`frontend/src/components/tasks/DeferPopover.tsx`)
  - "1 Week" and "1 Month" preset buttons with calculated dates
  - Custom date picker for arbitrary future dates
  - Compact mode for inline card usage
  - Click-outside-to-close behavior
- Integrated into ProjectDetail TaskItem (clock icon next to Edit button)
- Integrated into NextActions zones view and grid view action buttons
- Uses existing `PUT /tasks/{id}` with `{ defer_until }` — no new backend needed
- Deferred badge shown on tasks in ProjectDetail (shows defer date)

#### DEBT-062: Closed by Design
- Analyzed ProjectWithTasks schema — no actual redundancy
- task_count/completed_task_count are SQL-computed summaries
- tasks list provides full detail when needed
- Closed as "Works as Designed"

#### New Files
- `backend/scripts/sync_version.py`
- `frontend/src/components/tasks/DeferPopover.tsx`

#### Modified Files
- `installer/conduital.iss` — graceful shutdown procedure
- `backend/app/core/config.py` — version reads from pyproject.toml
- `backend/app/models/project.py` — explicit task_count/completed_task_count attributes
- `frontend/src/pages/MemoryPage.tsx` — priority input clamping (3 locations)
- `frontend/src/pages/ProjectDetail.tsx` — Make Next Action toolbar + DeferPopover integration
- `frontend/src/pages/NextActions.tsx` — DeferPopover integration (zones + grid views)

#### Tests
- Full suite: 216/216 passing (no regressions)
- TypeScript: 0 errors
- Python compile: PASS on all modified files

---

## Session: 2026-02-09 — Beta Session 3: GTD Inbox Enhancements (Pillar 2)

### Completed Items (4 BETA items)

#### BETA-030: Weekly Review Completion Tracking
- New `WeeklyReviewCompletion` model (`backend/app/models/weekly_review.py`) — simple timestamp + notes, no gamification
- Alembic migration `012_weekly_review_completion` — creates table with indexes on `user_id` and `completed_at`
- `POST /intelligence/weekly-review/complete` — persists completion record, optional notes
- `GET /intelligence/weekly-review/history` — returns last N completions, `days_since_last_review`, `last_completed_at`
- Module route stub replaced (was TODO in `modules/gtd_inbox/routes.py`)
- Dashboard: "Weekly Review" section shows "Last completed: X days ago" (or "Never completed")
- Frontend: `useWeeklyReviewHistory()` hook, `completeWeeklyReview()` + `getWeeklyReviewHistory()` API methods

#### BETA-032: Inbox Processing Stats Endpoint
- `GET /inbox/stats` endpoint returns `unprocessed_count`, `processed_today`, `avg_processing_time_hours`
- Replaces client-side stat calculation (fixes DEBT-064)
- Route ordering: `/stats` registered before `/{item_id}` to avoid path conflict
- Frontend: `useInboxStats()` hook, stats cards updated to use server data with fallback
- Third stat card now shows avg processing time when available

#### BETA-031: Inbox Batch Processing
- `POST /inbox/batch-process` endpoint — actions: `assign_to_project`, `convert_to_task`, `delete`
- Request validation: project_id required for assign/convert, action enum validated
- Per-item error handling: returns individual success/failure results
- Frontend: multi-select checkboxes on unprocessed items, select-all toggle
- Bulk action toolbar: project dropdown, "Assign to Project" button, "Delete" button, "Clear" selection
- Selection state clears on view switch (processed/unprocessed)

#### BETA-034: Inbox Item Age Indicator
- `getAgeIndicator()` function computes age tiers: <24h (hidden), 24h-3d (gray), 3d-7d (amber), >7d (red)
- Subtle `AlertCircle` icon + "Xd" text next to captured timestamp
- Only shown on unprocessed items — informational, not gamified

#### New Files
- `backend/app/models/weekly_review.py`
- `backend/alembic/versions/20260209_weekly_review_completion.py`
- `backend/tests/test_inbox_endpoints.py` (17 tests)

#### Modified Files
- `backend/app/models/__init__.py` — registered WeeklyReviewCompletion
- `backend/alembic/env.py` — added WeeklyReviewCompletion import
- `backend/app/api/intelligence.py` — added complete/history endpoints + schemas
- `backend/app/api/inbox.py` — added stats/batch-process endpoints, reordered routes
- `backend/app/schemas/inbox.py` — added InboxStats, InboxBatchAction/Response schemas
- `backend/app/modules/gtd_inbox/routes.py` — replaced TODO stub with full implementation
- `frontend/src/types/index.ts` — added InboxStats, InboxBatch*, WeeklyReviewCompletion types
- `frontend/src/services/api.ts` — added 5 new API methods
- `frontend/src/hooks/useIntelligence.ts` — added useWeeklyReviewHistory, useCompleteWeeklyReview
- `frontend/src/hooks/useInbox.ts` — added useInboxStats, useBatchProcessInbox
- `frontend/src/pages/InboxPage.tsx` — multi-select UI, stats from API, age indicators
- `frontend/src/pages/Dashboard.tsx` — weekly review status display

#### Tests
- 17 new tests in `test_inbox_endpoints.py`: weekly review (6), model (2), stats (3), batch processing (6)
- Full suite: 216/216 passing (17 new + 199 existing)
- TypeScript: 0 errors

---

## Session: 2026-02-09 — Beta Session 2: Motivation Signals (Frontend + API)

### Completed Items (7 BETA items)

#### API Endpoints (Phase 1C)
- BETA-024: Momentum history API — `GET /intelligence/momentum-history/{id}` returns sparkline data (snapshots, trend, previous score); `GET /intelligence/dashboard/momentum-summary` returns aggregate gaining/steady/declining counts with per-project details. Added `_compute_trend()` helper with ±5% threshold. **Done**
- Added `previous_momentum_score` to backend Project response schema (exposes trend data to frontend). **Done**

#### Frontend Motivation Signals (Phase 1B)
- BETA-010: Momentum trend indicator — up/down/stable arrow on ProjectCard. Uses `getTrendInfo()` helper comparing current vs previous momentum score (±0.05 threshold). Green TrendingUp, red TrendingDown, gray Minus. Dark mode support. **Done**
- BETA-011: Momentum sparkline — inline 40x16 SVG on ProjectCard. 2-point polyline from `previous_momentum_score` to `momentum_score` with color-coded stroke (green rising, red falling, gray stable). Flat line when no previous data. **Done**
- BETA-012: Project completion progress bar — thin h-1 gradient bar under stats grid. Blue gradient (`from-blue-400 to-blue-600`), dark mode variants. Only shown when totalTasks > 0. **Done**
- BETA-013: "Almost there" nudge — when completionPct > 80%, totalTasks > 0, project active: shows "{N} task(s) to finish line". Muted gray text (text-xs), singular/plural handling. Psychology: Goal Gradient + Zeigarnik Effect. **Done**
- BETA-014: Dashboard momentum summary — compact section after stats grid showing "N gaining momentum, N steady, N declining" with colored icons. Shows declining project links when any exist. Uses `useMomentumSummary()` hook. **Done**

#### Frontend Plumbing
- Added `MomentumSnapshotItem`, `MomentumHistory`, `MomentumSummaryProject`, `MomentumSummary` types to `types/index.ts`
- Added `previous_momentum_score` to `Project` interface
- Added `getMomentumHistory()` and `getMomentumSummary()` to API client
- Added `useMomentumHistory()` and `useMomentumSummary()` hooks to `useIntelligence.ts`

#### Tests
- 7 new API tests in `test_api_basic.py`: momentum history (empty, not found, days param, invalid days), momentum summary (empty, with projects), project schema includes previous_momentum_score
- TypeScript type check: PASS (0 errors)

#### Code Changes Summary
- `backend/app/api/intelligence.py`: 4 new schemas + `_compute_trend()` helper + 2 new endpoints
- `backend/app/schemas/project.py`: Added `previous_momentum_score` field to Project response
- `backend/tests/test_api_basic.py`: 7 new tests (TestMomentumHistoryEndpoints class)
- `frontend/src/types/index.ts`: 4 new interfaces + 1 field addition
- `frontend/src/services/api.ts`: 2 new methods + type imports
- `frontend/src/hooks/useIntelligence.ts`: 2 new hooks
- `frontend/src/components/projects/ProjectCard.tsx`: TrendingDown import, `getTrendInfo()` helper, trend arrow, sparkline SVG, progress bar, nudge
- `frontend/src/pages/Dashboard.tsx`: TrendingUp/TrendingDown/Minus imports, `useMomentumSummary` hook, momentum summary section

#### Test Results
- **199/199 backend tests pass (100%)** — 7 net new tests added (from 192 to 199)
- TypeScript: PASS (0 errors)

---

## Session: 2026-02-09 — Beta Session 1: Momentum Granularity (Backend)

### Completed Items (8 BETA items)

#### Formula Improvements (Phase 1A)
- BETA-001: Graduated next-action scoring — replaced binary 0/1 with 4-tier scale (0, 0.3, 0.7, 1.0) based on next-action age (<24h fresh, 1-7d recent, >7d stale, none). Implemented in `_calc_graduated_next_action()` helper. **Done**
- BETA-002: Exponential activity decay — replaced linear `1-(days/30)` with `e^(-days/7)`. Recent activity matters much more; 20-day-old activity drops to ~6% vs old ~33%. **Done**
- BETA-003: Sliding completion window — replaced hard 7-day window with weighted 30-day window: 0-7d×1.0, 8-14d×0.5, 15-30d×0.25. Implemented in `_calc_sliding_completion_from_tasks()` helper. **Done**
- BETA-004: Logarithmic frequency scaling — replaced `min(1, count/10)` with `log(1+count)/log(11)`. Diminishing returns per action, saturates at 10. **Done**

#### Data Model Additions (Phase 1C)
- BETA-020: Added `previous_momentum_score` column to projects table (nullable Float for delta/trend calculation) **Done**
- BETA-021: Created `MomentumSnapshot` model (project_id, score, factors_json, snapshot_at) — daily snapshots for sparklines **Done**
- BETA-022: Created Alembic migration `011_momentum_snapshots` (safe: checks column/table existence before creating) **Done**
- BETA-023: Added `create_momentum_snapshots()` to scheduled recalculation job in scheduler_service.py **Done**

#### Code Changes Summary
- `intelligence_service.py`: New helpers (`_calc_graduated_next_action`, `_calc_sliding_completion`, `_calc_sliding_completion_from_tasks`, `_calc_sliding_completion_detail`, `_next_action_detail_string`); updated `calculate_momentum_score`, `get_momentum_breakdown`, `update_all_momentum_scores`; added `create_momentum_snapshots`
- `models/momentum_snapshot.py`: NEW — MomentumSnapshot model
- `models/project.py`: Added `previous_momentum_score` column
- `models/__init__.py`: Registered MomentumSnapshot
- `scheduler_service.py`: Calls `create_momentum_snapshots` after score updates
- `alembic/versions/20260209_add_momentum_snapshots.py`: NEW — migration 011
- `tests/test_intelligence_service.py`: Added 13 new tests (graduated NA, sliding completion, snapshots, exponential decay, log frequency); updated existing tests for new formula

#### Test Results
- **192/192 tests pass (100%)** — 18 net new tests added (from 174 to 192)
- All existing tests updated for new formula (score thresholds adjusted)

---

## Session: 2026-02-07 — Batch 2 (5 items)

### Batch 2 Complete
- BACKLOG-106: List API uses Project schema without tasks. Need subquery annotations. **Done**
- BACKLOG-108: No ErrorBoundary exists anywhere. Need class component. **Done**
- BACKLOG-105: Sidebar nav items hardcoded. Backend has /modules endpoint, frontend doesn't use it. **Done**
- DEBT-056: Toaster has no dedup. Need toast IDs. **Done**
- DEBT-044: export.py has unused PlainTextResponse and Task imports. **Done**
- BaseModel import fix in memory_layer/routes.py (server startup crash) **Done**
- Integrity checker ENUM_DEFINITIONS fix **Done**

### Session Audit
- Logged 6 new DEBT items (DEBT-058 through DEBT-063)
- Updated lessons.md with 6 lessons from this session
- Marked DEBT-051 done (PydanticBaseModel alias removed)

### Batch 3 Complete (5 items)
- DEBT-058: `get_by_id` now computes task_count/completed_task_count **Done**
- DEBT-059: Layout.tsx `/modules` fetch replaced with API client + AbortController **Done**
- DEBT-060: ErrorBoundary retry loop prevention (max 2 resets, "Go Home" button) **Done**
- DEBT-027: Created `.eslintrc.cjs` with `no-console: warn` **Done**
- BACKLOG-107: Dashboard stalled/at-risk count reconciled with Weekly Review **Done**
- TypeScript: clean | Python syntax: clean | Backend tests: 2/3 pass (1 pre-existing)

### Batch 4 Complete (7 items) — 2026-02-07
- DIST-040: Git repository initialized + comprehensive .gitignore (awaiting git config for initial commit) **Done**
- DEBT-024: API test infrastructure fully fixed — fixture-based TestClient, StaticPool, startup patches → **18/18 tests pass** **Done**
- DEBT-028: Inbox "Processed Today" stat now filters by today's date only **Done**
- DEBT-046: ContextExportModal setState-in-render moved to useEffect **Done**
- DEBT-047: ContextExportModal stale data + memory leak fixed (reset on close, AbortController) **Done**
- DEBT-048: SQLAlchemy `== False` → `.is_(False)` fixed in 3 files (export.py, areas.py, intelligence_service.py) **Done**
- DEBT-055: Verified N/A — ContextExportModal already uses shared Modal with backdrop **Done**
- Also: DIST-043 unblocked (test suite now stable, ready for CI)
- TypeScript: clean | Vite build: clean | Python syntax: clean | Backend tests: **18/18 pass**

### Batch 5 Complete (5 items) — 2026-02-07
- BACKLOG-072: Unstuck Task Button on ProjectDetail — "Get Unstuck" button with Zap icon, wired to existing endpoint **Done**
- BACKLOG-084: Cross-Memory Search/Query — Backend `GET /memory/objects/search?q=` endpoint + `useSearchMemoryObjects` hook + MemoryPage server-side search **Done**
- DEBT-042/043: _persist_to_env safety — threading.Lock for concurrent writes + _sanitize_env_value() for newline/injection prevention **Done**
- BACKLOG-094: Whitespace-Only Content Validation — `strip_whitespace` validator in common.py applied to inbox, task, project, area schemas (title/content fields) **Done**
- BACKLOG-109: CORS Origins from Environment Variable — field_validator parses comma-separated or JSON array; .env.example updated **Done**
- TypeScript: clean | Vite build: clean | Python syntax: clean

### Batch 6 Complete (6 items) — 2026-02-07
- BACKLOG-091: Export UI in Frontend — Data Export section in Settings with preview, JSON download, DB backup download **Done**
- BACKLOG-098: Momentum Settings PUT Endpoint — `MomentumSettingsUpdate` schema + `PUT /settings/momentum` + editable stalled/at-risk/decay controls in Settings UI **Done**
- DEBT-066: SQLAlchemy `== True` → `.is_(True)` — Fixed 8 instances across intelligence_service.py (×3), next_actions_service.py (×3), task_service.py (×1), memory_layer/services.py (×1) **Done**
- DEBT-067: FastAPI `on_event` → lifespan — Converted startup/shutdown handlers to `asynccontextmanager` lifespan; moved helpers + lifespan above `app = FastAPI()` creation; `mount_module_routers` now takes `app` parameter **Done**
- DEBT-045: AI context export N+1 — Removed 2 redundant `func.count` queries + 1 redundant `all_active` query; single fetch at top, stalled/counts derived; removed unused `func` import **Done**
- DEBT-050: Unused `timedelta` import removed from ai_service.py **Done**
- Also: DIST-024 resolved (same as DEBT-067)
- TypeScript: clean | Vite build: clean | Python syntax: clean | Backend tests: **18/18 pass** (via venv python)

### Session Audit (Batches 5+6)
- Logged 8 new DEBT items (DEBT-071 through DEBT-078)
- Logged 2 new BACKLOG items (BACKLOG-111, BACKLOG-112)
- Updated lessons.md with 5 lessons from this session
- Root-caused test venv issue: `python` on PATH is system Python (no sqlalchemy), but `backend/venv/` has all deps. Must use explicit venv path.

### v1.0.0-alpha Release Prep — 2026-02-07
- Committed Batch 6 work (15 files, 660 insertions) **Done**
- Deleted `backend/Anthropic API Key.txt` from working tree (was already gitignored) **Done**
- Cleaned hardcoded `G:/My Drive/999_SECOND_BRAIN` paths from 22 documentation files **Done**
- Updated .env.example with generic path placeholders **Done**
- Bumped version to 1.0.0-alpha in pyproject.toml, package.json, config.py, .env.example **Done**
- Created annotated git tag `v1.0.0-alpha` **Done**
- Frontend build: CLEAN (576KB, 0 TS errors) | Working tree: CLEAN

### 0.6 Product Naming & Branding — 2026-02-07
- Researched 11 candidate names across web, app stores, Gumroad, domains, USPTO, GitHub, social media
- Used parallel subagents for efficient research (6 names in Round 1, 3+3 in Rounds 2+3)
- **Key finding:** User's #1 pick "Operaxis" is taken by OperAxis LLC (active US tech staffing company)
- Other eliminated names: Moventis (HIGH), Operant (HIGH), Axiomatic (HIGH), Vectis (HIGH), Kinetic (HIGH), Axionaut (MED-HIGH), Opivot (MEDIUM)
- **Final decision: Conduital** — complete blank slate, .com available ($5), zero USPTO filings, all namespace open
- Typography: Title case "Conduital"
- Tagline: "The Conduit for Intelligent Momentum"
- Logo: Wordmark only for now; icon mark deferred to pre-distribution
- Updated distribution-checklist.md section 0.6 with all decisions
- Updated findings.md with full research results and final decisions
- **Remaining:** Register domains, claim social handles

### v1.0.0 Release Prep Round 2 — Conduital Rebrand & Polish — 2026-02-07
- Rebranded all user-facing "Project Tracker" references to "Conduital" (56 occurrences across 25+ files) **Done**
- Cleaned 20+ remaining GTD references in backend schemas, API descriptions, module display names **Done**
- Cleaned "Second Brain" and "PARA" references in user-facing text (Settings, Layout, Projects, WeeklyReview, schemas) **Done**
- Updated index.html `<title>` to "Conduital — Intelligent Momentum" **Done**
- Renamed export/backup filenames from `project_tracker_*` to `conduital_*` **Done**
- Renamed log files from `project_tracker*.log` to `conduital*.log` **Done**
- Updated default database path from `~/.project-tracker/` to `~/.conduital/` **Done**
- Updated pyproject.toml package name to "conduital" **Done**
- Cleaned 1,603 lines of ChatGPT branding research from distribution-checklist.md **Done**
- Updated distribution-checklist.md title, completed items, trademark compliance section **Done**
- TypeScript: clean | Vite build: clean (576KB) | Python syntax: 88 files, 0 errors
- **Remaining:** Register domains (conduital.com/$5), claim social handles, design icon mark

### Namespace Claims — 2026-02-07
- conduital.com: PURCHASED ✅
- @conduital on Twitter/X: CLAIMED ✅
- conduital on Gumroad: CLAIMED ✅
- @conduital on GitHub (gregdm98607/conduital): CLAIMED ✅

### v1.0.0 Release Prep Round 3 — Deep Cleanup — 2026-02-07
- Cleaned 18 remaining "Project Tracker" references in internal docstrings/comments across 15 files **Done**
- Fixed FastAPI title override: local .env had stale APP_NAME="Project Tracker" (Pydantic BaseSettings precedence) **Done**
- Fixed alembic.ini database path: `.project-tracker/` → `.conduital/` **Done**
- Fixed package.json name: `project-tracker-frontend` → `conduital-frontend` **Done**
- Cleaned 8 stale "ProjectTracker" references in distribution-checklist.md future phases (installer paths, system tray, data directory) **Done**
- Cleaned 1 stale "Second Brain" reference in distribution-checklist.md (setup wizard step) **Done**
- Verified static file serving end-to-end: Vite build → FastAPI StaticFiles mount → catch-all SPA route (6/6 checks pass) **Done**
- TypeScript: clean | Vite build: clean (576KB) | Python syntax: PASS

### v1.0.0 Release Prep Round 4 — Tech Debt, Testing, Tracking Reconciliation — 2026-02-07

#### Code Changes
- DEBT-071: Removed unused `get_db` import from main.py (leftover from lifespan refactor) **Done**
- DEBT-068: Migrated 9 Pydantic V1 deprecations to V2 patterns **Done**
  - auth.py: `class Config: from_attributes = True` → `model_config = ConfigDict(from_attributes=True)`
  - memory_layer/schemas.py: 3× `Field(example=)` → `Field(examples=[])`
  - discovery.py: 4× `Field/Body(example=)` → `Field/Body(examples=[])`
- DEBT-072: Verified N/A — `Path` is actively used in 5 locations in main.py
- Fixed run.py: "Project Tracker" → "Conduital" in banner, docstring, argparser description
- Fixed run.py: Unicode `─` character → ASCII `-` (cp1252 encoding error on Windows console)

#### Static Build End-to-End Test (Phase 1.1 completion)
- Tested full app with Vite build only (no npm dev server): 6/6 checks pass **Done**
  - `/health`: 200, version `1.0.0-alpha`, app `Conduital`
  - `/` (root): Serves index.html (481 bytes, text/html) — fixed root endpoint to serve SPA when build exists
  - `/projects` (SPA route): Serves index.html — correct
  - `/assets/index-*.js`: 576KB static asset — correct
  - `/api/v1/projects`: Returns JSON — correct
  - `/docs`: Returns 200 — correct
- Fixed root `/` endpoint: now conditionally serves SPA (production) or API info JSON (development)
- Fixed local .env stale `VERSION=0.1.0` → `1.0.0-alpha` (Pydantic BaseSettings precedence)
- Updated test_api_basic.py `test_root_endpoint` to handle both SPA and JSON responses

#### Migrations from Empty State Test (Phase 1.2 completion)
- Tested Alembic `upgrade head` from empty database: 12 migrations, 17 tables **Done**
- Found and fixed migration 010 (repair_user_id): failed on fresh install because it unconditionally tried to add `user_id` to goals/visions (already added by auth migration 007)
- Fix: Added `_column_exists()` check using `PRAGMA table_info` before `batch_alter_table`
- Verified: goals.user_id PRESENT, visions.user_id PRESENT, projects.user_id PRESENT, areas.user_id PRESENT
- Also verified existing database migration still works (already at head, no-op)

#### Backlog Reconciliation
- Updated 11 DIST items from "Open" to "✅ Done" in backlog.md:
  - DIST-011 (static serving), DIST-020 (license audit), DIST-021 (lock deps), DIST-022 (semver)
  - DIST-050 (conduital.com), DIST-052 (@conduital X), DIST-053 (GitHub), DIST-054 (Gumroad)
  - DIST-055 (ChatGPT notes cleanup), DIST-056 (codebase rebrand)
- Added 13 items to Completed Items table
- Updated distribution-checklist.md Phase 1.1 and 1.2 test items

#### Build Verification
- TypeScript: clean (0 errors)
- Vite build: clean (576KB)
- Python compile: PASS (all backend files)
- Backend tests: 173/174 pass (1 pre-existing: deferred tasks filter test)

### v1.0.0 Release Prep Round 5 — Bug Fix, Accessibility, AI Degradation, Cleanup — 2026-02-07

#### Code Changes
- BUG-024: Fixed deferred tasks filter — added `(Task.defer_until.is_(None)) | (Task.defer_until <= today)` to SQL WHERE clause in `next_actions_service.py`. Removed dead sort tier 6 code (deferred tasks no longer reach sort phase). **Tests: 173/174 → 174/174 (100%)** **Done**
- DEBT-049: Added `type="button"` and `aria-expanded` attributes to 8 collapsible section toggle buttons (7 in Settings.tsx, 1 in NextActions.tsx) **Done**
- DEBT-077: Removed `asyncio_mode = "auto"` from pyproject.toml `[tool.pytest.ini_options]` — eliminates pytest-asyncio deprecation warning **Done**
- Branding: Cleaned last 4 code files with "Project Tracker" refs — diagnose.py, README.md, MODULE_SYSTEM.md, CLAUDE.md **Done**

#### Distribution Prep
- DIST-010: Added 32 dev-only files/directories to .gitignore (CLAUDE.md, MODULE_SYSTEM.md, distribution-checklist.md, tasks/, *.md dev docs, diagnose.py, .claude/) **Done**
- Phase 1.5 AI degradation: Verified graceful behavior with no API key — `AI_FEATURES_ENABLED=false`, `create_provider` raises clean ValueError, HTTP 400 responses. Marked checklist items complete **Done**

#### Build Verification
- TypeScript: clean (0 errors)
- Vite build: clean (576KB)
- Python compile: PASS (all backend files)
- Backend tests: **174/174 pass (100% — BUG-024 fixed the last failing test)**

#### Tracking Updates
- Updated backlog.md: BUG-024, DEBT-049, DEBT-077, DIST-010 marked Done; 4 items added to Completed Items table
- Updated distribution-checklist.md: Phase 1.5 AI degradation items marked complete
- Updated task_plan.md: Round 5 complete (7/7 items)

### v1.0.0 Release Prep Round 6 -- Docs Rebrand, Test Infra, Version SSoT -- 2026-02-07

#### Documentation Rebrand (DIST-056b)
- README.md: Complete rewrite -- outdated 413-line Phase 1 doc replaced with accurate 93-line product summary **Done**
- backlog.md: Rebranded header "Project Tracker" to "Conduital", section titles R1/R2, release overview table, STRAT-007 **Done**
- .gitignore: Rebranded header comment, added 8 backend dev docs to exclusion list, added conduital.db pattern **Done**
- backend/scripts/README.md: Rebranded "Project Tracker" to "Conduital" **Done**
- 5 Claude Code skill files: Rebranded 10 "Project Tracker" references across sync.md, test.md, db.md, capture.md, review.md **Done**

#### Test Infrastructure (DEBT-069, DEBT-070)
- DEBT-069: Added `StaticPool` import and usage to conftest.py `in_memory_engine` fixture -- ensures reliable in-memory SQLite connections **Done**
- DEBT-070: Refactored test_api_basic.py to use conftest.py's `in_memory_engine` fixture instead of duplicating engine creation -- removed 8 lines of duplicated setup code **Done**
- Backend tests: **174/174 pass** (verified after consolidation)

#### Version Single Source of Truth (DIST-022b)
- run.py: Replaced hardcoded `"Conduital v1.0.0-alpha"` with dynamic `settings.VERSION` from config.py **Done**

#### Backlog Hygiene
- Marked DEBT-069/070 Done in backlog.md medium priority table
- Removed stale "15 API integration tests failing" from Known Limitations
- Updated DIST-043 test count to 174/174
- Added 4 items to Completed Items table (DEBT-069, DEBT-070, DIST-056b, DIST-022b)
- Updated last-updated line with Round 6 summary

#### Build Verification
- TypeScript: clean (0 errors)
- Vite build: clean (576KB)
- Python compile: PASS (all changed files)
- Backend tests: **174/174 pass (100%)**

### v1.0.0 Release Prep Round 7 -- Deep Branding, Strategic Fix, Backlog Hygiene -- 2026-02-07

#### Strategic Consistency Fix
- STRAT-001 in backlog.md: Changed "Distribution: SaaS Web-Only" to "Distribution: Desktop-first" to match actual strategy in distribution-checklist.md **Done**

#### Deep Branding Cleanup
- Backend Python docstrings: 10 files cleaned -- "Second Brain" replaced with "synced notes folder" / "markdown files" in docstrings, comments, and logger messages across discovery_service.py, area_discovery_service.py, sync/ (6 files), config.py, main.py **Done**
- Skills directory: 17 replacements across 7 files -- "Project Tracker" / "Project-Tracker" → "Conduital", "Second Brain" → "synced notes folder" / "file sync" **Done**
- backlog.md: 4 "Second Brain" refs replaced (R1 target, R1 features x2, distribution model description), BACKLOG-113 condensed and cleaned **Done**
- .gitignore: Added 5 missing dev file exclusions (MODULE_SYSTEM.md, Skills/, backend/diagnose.py, frontend/FRONTEND_IMPLEMENTATION_GUIDE.md, frontend/SETUP_AND_TEST.md) **Done**
- frontend/package-lock.json: Regenerated with correct name "conduital-frontend" (was "project-tracker-frontend") **Done**

#### Backlog Hygiene
- Moved 14 Done items from Medium Priority debt table to Completed Items table (DEBT-024/027/028/042-048/053/055-057)
- Moved 8 Done items from Low Priority debt table to Completed Items table (DEBT-049-051/058-060/066-072/077)
- Removed 8 Done items from Parking Lot (BACKLOG-091/094/098/105-109)
- Condensed BACKLOG-104/113 descriptions for readability
- Cleaned DEBT-004 completed item description ("SECOND_BRAIN_ROOT" → "sync root")
- Updated last-updated line with Round 7 summary

#### Build Verification
- TypeScript: clean (0 errors)
- Vite build: clean (576KB)
- Python compile: PASS (all modified files)
- Backend tests: **174/174 pass (100%)**

### v1.0.0 Release Prep Round 8 -- Final Branding, Code Quality, CHANGELOG -- 2026-02-08

#### Branding Cleanup (Final Pass)
- create-test-data.ps1: 3 "Project Tracker" refs replaced with "Conduital" **Done**
- start-dev.bat: 1 "Project Tracker" ref replaced **Done**
- start-dev-enhanced.bat: 1 "Project Tracker" ref replaced **Done**
- THIRD_PARTY_LICENSES.txt: 1 "Project Tracker" ref replaced **Done**
- backend/.env.example: "Second Brain Integration" section rebranded to "File Sync Integration", "PARA-organized" removed, comments updated **Done**
- CLAUDE.md: "PARA-organized Second Brain folders" replaced with generic description **Done**
- .gitignore: removed stale `backend/project_tracker.db*` pattern **Done**

#### Code Quality
- auto_discovery_service.py: 33 print() statements converted to logger.info/warning/error; emojis removed for Windows encoding safety **Done**
- folder_watcher.py: 3 print() statements converted to logger.info **Done**

#### Release Documentation
- Created CHANGELOG.md with v1.0.0-alpha release notes (Added, Security, Infrastructure sections) **Done**

#### Build Verification
- TypeScript: clean (0 errors)
- Vite build: clean (576KB)
- Python compile: PASS (all modified files)
- Backend tests: **174/174 pass (100%)**

### v1.0.0 Release Prep Round 9 -- Production Route Fix, Deep Branding, Debt Documentation -- 2026-02-08

#### Bug Fix
- DEBT-063: SPA catch-all in main.py now excludes `/modules` and `/health` API routes — prevents JSON endpoints from being served as index.html in production builds **Done**

#### Branding Cleanup (Deep Pass)
- API_DOCUMENTATION.md: "Project Tracker" -> "Conduital" (title + health response), version updated to 1.0.0-alpha, 4 "GTD" refs cleaned (Inbox section, Capture/Clarify phase labels) **Done**
- backend/README.md: "GTD Next Actions" -> "next actions", "GTD Horizon 3/4-5" removed, "GTD contexts" -> "Contexts", "GTD inbox" -> "Inbox", "PARA-organized Second Brain" -> "synced notes folder" **Done**
- backend/scripts/discover_projects.py: "Second Brain" -> "synced notes folder" in docstring + print output **Done**
- backend/scripts/create_project_files.py: "Second Brain" -> "synced notes folder" in print output **Done**
- backend/scripts/README.md: "Second Brain" -> "synced notes folder" in purpose + output example **Done**
- backend/app/modules/projects/__init__.py: "GTD-style attributes" -> "next action attributes", "Second Brain" -> "markdown notes" **Done**
- backend/app/api/sync.py: "Second Brain" -> "synced notes folder" in docstring **Done**
- backend/.env: "Project Tracker" -> "Conduital" in header comment **Done**

#### Documentation
- DEBT-075: Added explanatory comment to config.py Settings class explaining why it's intentionally not frozen (runtime mutation by settings endpoints) **Done**
- CHANGELOG.md: Added [Unreleased] section with Round 9 changes **Done**

#### Build Verification (Round 9)
- TypeScript: clean (0 errors)
- Vite build: clean (576KB)
- Python compile: PASS (all modified files)
- Backend tests: **174/174 pass (100%)**

### v1.0.0 Release Prep Round 10 -- UI Polish, Code Quality, Defensive Routing -- 2026-02-08

#### UI Polish
- DEBT-073: Added `Activity` icon to Momentum section header in Settings.tsx — matches all other sections which have colored icons **Done**
- DEBT-074: Exposed `recalculateInterval` field in Momentum Settings UI — was loaded from API and saved back but had no input field (hidden from user) **Done**

#### Code Quality
- DEBT-076: Extracted `triggerBlobDownload()` private helper in api.ts — `downloadJSONExport` and `downloadDatabaseBackup` now delegate to shared helper instead of duplicating blob download logic **Done**

#### Defensive Routing
- DEBT-063b: SPA catch-all in main.py now also excludes `/openapi.json` route — defensive measure for production builds **Done**

#### Documentation
- CLAUDE.md: Removed stale references to `CLAUDE_CODE_PROMPTS.md` and `Project_Tracker_Technical_Spec.md` from Related Documentation section **Done**
- CHANGELOG.md: Updated [Unreleased] section with Round 10 changes **Done**

#### Build Verification (Round 10)
- TypeScript: clean (0 errors)
- Vite build: clean (577KB)
- Python compile: PASS (all modified files)
- Backend tests: **174/174 pass (100%)**

### v1.0.0 Release Prep Round 11 -- Trademark Cleanup, .gitignore Hygiene -- 2026-02-08

#### Trademark Cleanup (DIST-056e)
- Removed all GTD references from 7 model docstrings/comments: area.py, project.py, task.py, inbox.py, goal.py, vision.py, context.py **Done**
- Removed PARA reference from area.py docstring **Done**
- Cleaned GTD references from 5 module files: modules/__init__.py, modules/core/__init__.py, modules/registry.py, modules/gtd_inbox/__init__.py, modules/gtd_inbox/routes.py **Done**
- Cleaned GTD reference from intelligence_service.py weekly review docstring **Done**
- Cleaned GTD reference from ai_service.py unstuck task AI prompt **Done**
- Total: 30+ GTD/PARA references replaced with generic terminology across 13 source files

#### .gitignore Hygiene (DIST-010b)
- Restored backend/API_DOCUMENTATION.md — was incorrectly gitignored (it's user-facing API docs that should ship) **Done**
- Added frontend/INSTALL_TOAST.md to .gitignore (dev-only note with hardcoded paths) **Done**
- Added frontend/QUICK_FIX.md to .gitignore (dev-only troubleshooting doc) **Done**

#### Documentation
- CHANGELOG.md: Updated [Unreleased] section with Round 11 changes **Done**
- backlog.md: Added DIST-056e and DIST-010b to Completed Items; updated last-updated line **Done**

#### Build Verification (Round 11)
- TypeScript: clean (0 errors)
- Vite build: clean (577KB)
- Python compile: PASS (all modified files)
- Backend tests: **174/174 pass (100%)**

### v1.0.0 Release Prep Round 12 -- Final Release Readiness Audit -- 2026-02-08

#### Branding & Trademark Scan (Full Codebase)
- Scanned all source files for "Project Tracker", "Second Brain", "PARA", "GTD", "project-tracker", "project_tracker" **Done**
- Result: **CLEAN** — no stale references found; all remaining GTD/SECOND_BRAIN_ROOT occurrences are legitimate (trademark attribution in LICENSE, internal config variable names, module names) **Done**

#### Version Consistency Check
- Verified 1.0.0-alpha across 7 files: pyproject.toml, package.json, config.py, .env.example, run.py, CHANGELOG.md, API_DOCUMENTATION.md **Done**
- Result: **0 drift** — all files aligned on 1.0.0-alpha **Done**

#### .gitignore Hardening (DIST-010c)
- Added `~$*` pattern for Microsoft Office temporary files (was leaking `~$nduitalDesignBrief.docx`) **Done**
- Added root-level design asset exclusions: `/*.docx`, `/*.png`, `/*.jpg`, `/*.jpeg` **Done**

#### CHANGELOG Finalization
- Merged [Unreleased] section into v1.0.0-alpha entry — all changes are pre-release, no need for separate unreleased section **Done**
- Updated release date to 2026-02-08 **Done**
- Consolidated Fixed and Changed subsections into v1.0.0-alpha **Done**

#### Build Verification (Round 12)
- TypeScript: clean (0 errors)
- Vite build: clean (577KB)
- Python compile: PASS
- Backend tests: **174/174 pass (100%) in 4.69s**

### Phase 2.4: Packaged Exe Runtime Testing -- 2026-02-08

#### Test Results (13/13 PASS)
- Launch: exe starts, no console window, logging to `%LOCALAPPDATA%\Conduital\logs\` **PASS**
- Migrations: All 12 migrations from empty state, 17 tables in `%LOCALAPPDATA%\Conduital\tracker.db` **PASS**
- Server health: `GET /health` returns correct app name, version, commercial mode **PASS**
- Browser auto-open: Opens to `http://127.0.0.1:52140` **PASS**
- Setup wizard: `is_packaged: true`, `is_first_run: true`; 4-step wizard completes; `SETUP_COMPLETE=true` persisted **PASS**
- Frontend SPA: All routes (/, /projects, /areas, /next-actions, /weekly-review, /settings, /setup) return 200 **PASS**
- Static assets: JS (591KB) and CSS served from `_internal/frontend_dist/assets/` **PASS**
- API endpoints: /health, /api/v1/projects, /api/v1/setup/status, /modules, /docs all functional **PASS**
- Data directory: `%LOCALAPPDATA%\Conduital\` with tracker.db (253KB), config.env, logs/ **PASS**
- Log files: conduital.log + conduital_errors.log created; error log empty **PASS**
- System tray: Process runs with tray icon (139MB memory) **PASS**
- Shutdown: `taskkill /F` terminates cleanly; tray Quit is the clean shutdown path **PASS**
- Setup persistence: `setup_complete: true`, `is_first_run: false` after wizard **PASS**

**Issues found:** None blocking. All 13 tests pass.

### Phase 3: Inno Setup Installer Script -- 2026-02-08

#### Created `installer/conduital.iss`
- Full Inno Setup 6.x installer script **Done**
- EULA screen using LICENSE file **Done**
- Default install to `{autopf}\Conduital` (Program Files) **Done**
- Start Menu shortcuts (app + uninstaller) **Done**
- Optional Desktop shortcut **Done**
- "Launch Conduital" checkbox on final install screen **Done**
- Uninstaller in Windows Apps & Features **Done**
- Custom uninstall: prompts to remove `%LOCALAPPDATA%\Conduital\` user data (default: keep) **Done**
- Pre-uninstall: force-kills running Conduital.exe **Done**
- LZMA2/ultra64 compression **Done**
- x64 only, Windows 10+ minimum **Done**
- Version info embedded (1.0.0.0) **Done**
- `.gitignore`: Added `installer/Output/` exclusion **Done**

### Phase 3: Installer Build & Test -- 2026-02-08

#### Bug Fix: Uvicorn Logging in PyInstaller
- **Bug:** `ValueError: Unable to configure formatter 'default'` when launching installed exe
- **Root cause:** Uvicorn's default `LOGGING_CONFIG` uses `DefaultFormatter` which calls `sys.stderr.isatty()` — fails in PyInstaller `console=False` bundles
- **Fix:** Added `log_config=None` to `uvicorn.Config()` in `run_packaged()` — app's own `logging_config.py` handles all logging instead
- Rebuilt PyInstaller package and installer after fix **Done**

#### Inno Setup Installation
- Installed Inno Setup 6.7.0 via winget **Done**
- Fixed `#13#10` in Pascal Script → `Chr(13) + Chr(10)` (ISPP preprocessor conflict) **Done**
- Fixed `VersionInfoProductVersion` — Windows requires x.x.x.x format, not semver with prerelease tag **Done**
- Simplified `InitializeSetup()` — kills running Conduital.exe before install/upgrade **Done**

#### Installer Build
- Compiled with ISCC: 14.2s build time, 29 MB output **Done**
- Output: `installer/Output/ConduitalSetup-1.0.0-alpha.exe` **Done**

#### Full Install → Launch → Use → Uninstall Cycle (Dev Machine)
- Install: Inno Setup wizard with EULA, directory choice, shortcuts **PASS**
- Files installed to `C:\Program Files\Conduital\` (exe, _internal, LICENSE, THIRD_PARTY, uninstaller) **PASS**
- Launch: App starts from Program Files, server healthy on port 52140 **PASS**
- Setup wizard: `is_packaged: true`, `is_first_run: true`, 4-step wizard renders correctly **PASS**
- Uninstall: Files removed from Program Files; user data prompt works **PASS**

### Post-Release Batch — Tech Debt, Validation, Accessibility, Infrastructure — 2026-02-08

#### Code Changes (5 items)
- DEBT-082: Fixed `build.bat` size reporting — corrected `findstr` parsing with `usebackq tokens`, now shows bytes alongside MB **Done**
- BACKLOG-111: Momentum Settings stalled > at_risk validation — server-side effective-value validation with HTTP 422, client-side guard + inline warning banner in Settings UI **Done**
- BACKLOG-115: `/api/v1/shutdown` graceful shutdown endpoint — shared `shutdown_event` in `app.core.shutdown`, localhost-only POST endpoint, cooperative with system tray via `run.py` integration **Done**
- DEBT-014: ARIA accessibility improvements — Modal (`role="dialog"`, `aria-modal`, `aria-labelledby`), UserMenu (`aria-haspopup`, `aria-expanded`, `role="menu/menuitem"`), ProjectCard outcome toggle (`aria-expanded`, `aria-label`), Settings API key visibility toggle (`aria-label`) **Done**
- DEBT-065: AbortSignal support added to all 27 API client getter methods in `api.ts` — enables HTTP request cancellation on component unmount **Done**

#### Files Changed
- `build.bat` — size reporting fix
- `backend/app/api/settings.py` — momentum validation + HTTPException import
- `backend/app/core/shutdown.py` — NEW: shared shutdown event
- `backend/app/main.py` — shutdown endpoint
- `backend/run.py` — shared shutdown event integration
- `frontend/src/services/api.ts` — AbortSignal on all getters
- `frontend/src/pages/Settings.tsx` — momentum validation + API key aria-label
- `frontend/src/components/common/Modal.tsx` — dialog ARIA attributes
- `frontend/src/components/auth/UserMenu.tsx` — menu ARIA attributes
- `frontend/src/components/projects/ProjectCard.tsx` — outcome toggle ARIA

#### Build Verification
- TypeScript: clean (0 errors)
- Python compile: PASS (all modified files)
- Backend tests: **174/174 pass (100%)**
