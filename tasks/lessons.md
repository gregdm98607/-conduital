# Lessons Learned

Patterns and anti-patterns discovered during development. Review at session start.

---

## 2026-02-03: BACKLOG-074 Data Export/Backup

### What Went Well
1. **Planning-first approach** - Using `/planning-with-files` skill helped structure the work and kept context clear
2. **Subagent for exploration** - Offloading codebase research to Explore agent kept main context clean
3. **Direct service testing** - Testing ExportService directly (not via API) avoided FastAPI startup event issues

### Lessons Learned

#### 1. Model Consistency Check
**Issue:** InboxItem model doesn't inherit from TimestampMixin, so it lacks `created_at`/`updated_at` fields
**Fix:** Check model inheritance before assuming fields exist
**Rule:** When serializing models, verify each field exists on the model before accessing

#### 2. Test Suite Infrastructure
**Issue:** Existing test suite (test_api_basic.py) has broken database setup - tables aren't created before tests
**Root cause:** `TestClient` created at module level runs before pytest fixtures
**Workaround:** Test services directly with fresh db_session fixture instead of via API
**Backlog item:** DEBT-024 - Fix test infrastructure for API integration tests

#### 3. FastAPI Startup Events in Tests
**Issue:** TestClient triggers startup events which may fail in test context
**Pattern:** For unit tests, test services directly; reserve API tests for integration testing with proper setup

#### 4. Export Format Versioning
**Good practice:** Added `export_version` field to metadata for future import compatibility
**Note:** When adding import feature (future), use version to handle schema migrations

### Technical Debt Identified
- [ ] DEBT-024: Test infrastructure broken - API tests don't properly initialize database
- [ ] InboxItem model should inherit TimestampMixin for consistency

### Potential Backlog Items
1. **BACKLOG-090: Data Import Feature** - Complement to export, restore from JSON backup
2. **BACKLOG-091: Export UI in Frontend** - Settings page with export buttons, preview modal
3. **DEBT-024: Fix Test Infrastructure** - Proper conftest.py with working database setup

---

## 2026-02-04: SQLAlchemy Self-Referential Relationship Bug

### Issue
ALL TASKS page failed with "Internal Server Error" when `page_size > 100`.

### Root Cause
Self-referential relationship in `Task` model had incorrect configuration:
```python
# WRONG - caused serialization failure at >100 records
subtasks: Mapped[list["Task"]] = relationship(
    "Task",
    back_populates="parent_task",
    cascade="all, delete-orphan",
    remote_side=[parent_task_id],  # <-- INCORRECT
)
```

### Fix
Use `foreign_keys` instead of `remote_side` for the "many" side of self-referential relationships:
```python
# CORRECT
subtasks: Mapped[list["Task"]] = relationship(
    "Task",
    back_populates="parent_task",
    cascade="all, delete-orphan",
    foreign_keys=[parent_task_id],  # <-- CORRECT
)
parent_task: Mapped[Optional["Task"]] = relationship(
    "Task", back_populates="subtasks", foreign_keys=[parent_task_id], remote_side=[id]
)
```

### Rule
For SQLAlchemy self-referential relationships:
- `foreign_keys` specifies which column is the FK (use on BOTH sides for clarity)
- `remote_side` specifies which column is on the "one" side (use only on the child→parent relationship, with the parent's PK)
- The "children" relationship should NOT use `remote_side`

### Debugging Approach
1. Binary search on query parameters to find exact failure threshold
2. Check SQLAlchemy relationship configurations for self-referential models
3. Look for `remote_side` misuse in parent-child relationships

---

## 2026-02-06: Urgency Zones, Over the Horizon, Quick Capture UX

### What Went Well
1. **Root cause analysis on Critical Now** - Traced empty section to two separate issues (stale zones + narrow criteria) rather than settling for just one fix
2. **Startup recalculation pattern** - Added both scheduled job AND startup recalculation to handle server restarts gracefully
3. **Backlog cleanup** - Moving completed items out of release tables keeps the backlog scannable

### Lessons Learned

#### 1. Date-Dependent Computed Fields Go Stale
**Issue:** `urgency_zone` was only calculated at task create/update time. As days passed, tasks due "tomorrow" never promoted to "today" = Critical Now was always empty.
**Fix:** Added daily scheduled recalculation job (12:05 AM) + startup recalculation.
**Rule:** Any stored field computed from dates MUST have a scheduled recalculation mechanism. Ask: "Will this value still be correct tomorrow without an edit?"

#### 2. Don't Filter Out Data the Frontend Needs to Display
**Issue:** Over the Horizon was always empty because the backend SQL query excluded deferred tasks entirely (`defer_until <= today`). The frontend had a section for OTH but never received the data.
**Fix:** Removed the SQL filter; added a sort tier (tier 6) so deferred tasks appear last.
**Rule:** When the frontend has a UI section for a data category, the backend API must return that data. Use sorting/grouping to control display order, not query exclusion.

#### 3. Negative Values in Relative Date Displays
**Issue:** "Due in X days" text used raw date arithmetic, producing "Due in -4 days" for overdue tasks.
**Fix:** Changed to static "Due date priority" text. Alternatively, handle negative case explicitly (e.g., "Overdue by 4 days").
**Rule:** Any `daysUntilX` calculation can go negative. Always handle past-date cases explicitly before displaying.

#### 4. Keep-Open Modal Pattern for Batch Entry
**Issue:** Quick Capture closed after each entry, requiring re-opening for multiple items.
**Fix:** `handleQuickCapture(keepOpen: boolean)` parameter — Ctrl+Enter saves and keeps modal open, clears text for next entry.
**Rule:** For batch-entry modals, support a "save and continue" action alongside "save and close". Use Ctrl+Enter as the keyboard shortcut.

### Potential Backlog Items
1. **BACKLOG-093 (candidate):** Quick Capture success animation/flash for clearer feedback during consecutive entries

---

## 2026-02-06: R2 Should Have Items + Last Activity Date Bug

### What Went Well
1. **Batch implementation of 5 backlog items** — all 5 R2 Should Have items implemented in sequence with clean builds after each phase
2. **Comprehensive date audit** — subagent audited all 7+ locations where `last_activity_at` is set, found the single inconsistency
3. **Post-implementation code review** — caught a critical bug in orphan projects filter (`status` vs `p.status`) that would have surfaced in production

### Lessons Learned

#### 1. Variable Shadowing in Filter Callbacks
**Issue:** In `Projects.tsx`, the orphan projects filter used `status` (component state variable for the tab filter) instead of `p.status` (the project's own status). When the "All" tab was active (`status === ''`), every project without an area was treated as an orphan, including completed and archived ones.
**Fix:** Changed `status === ''` to `p.status === 'active'` — orphan check should always filter by project status, not the UI filter state.
**Rule:** In filter callbacks, always prefix with the iterator variable (e.g., `p.status`) when the outer scope has a variable of the same name. Watch for this pattern especially in `useMemo` filter functions.

#### 2. Naive vs Aware Datetimes — One Bad Apple
**Issue:** 6 out of 7 locations setting `last_activity_at` used `datetime.now(timezone.utc)` (timezone-aware), but `discovery_service.py` used `datetime.utcnow()` (naive). SQLite stored the naive timestamp, which got misinterpreted as local time by the frontend, causing "in about 7 hours" (future) display.
**Fix:** Changed to `datetime.now(timezone.utc)`. Also hardened the frontend to clamp future dates to "Just now".
**Rule:** Search for ALL setters of a timestamp field when investigating a timezone bug. Use `datetime.now(timezone.utc)` everywhere, never `datetime.utcnow()`. Add defensive frontend handling for future timestamps (clamp to "Just now").

#### 3. Relative Time Display Gets Vague for Old Dates
**Issue:** `formatDistanceToNow` shows "about 2 months ago" for 65-day-old dates — not useful for understanding when something actually happened.
**Fix:** Show absolute date (e.g., "Jan 6, 2026") for dates 30+ days old, relative time for recent dates.
**Rule:** Relative time ("3 days ago") is great for recent events. For anything older than ~30 days, switch to absolute dates for clarity.

#### 4. Remove Debug console.logs Before Shipping
**Issue:** `ProjectDetail.tsx` had two `console.log` statements that fire on every render, adding noise to production browser console.
**Fix:** Removed them.
**Rule:** Scan for `console.log` before marking a component complete. Consider adding an ESLint rule (`no-console`) to catch these automatically.

### Technical Debt Identified
- [ ] DEBT-027: Add ESLint `no-console` rule (warn) to catch debug logging in production code
- [ ] DEBT-028: Inbox "Processed Today" stat is misleading — shows 0 or all-time count, not today's count

### Potential Backlog Items
1. **BACKLOG-094 (candidate):** Whitespace-only content validation on backend API (inbox, tasks) — `min_length` doesn't catch `"   "`
2. **DEBT-027:** ESLint `no-console` rule
3. **DEBT-028:** Fix Inbox "Processed Today" stat accuracy

---

## 2026-02-06: R2 Nice-to-Have Items (5 Backlog Items)

### What Went Well
1. **Fast batch delivery** — 5 frontend features implemented in sequence, all passing TypeScript + Vite builds on first compile (except one unused import)
2. **Reuse of existing backend** — BACKLOG-022 (Daily Dashboard) leveraged the existing `/next-actions/dashboard` API endpoint with zero backend changes
3. **Post-implementation review** — Used Explore agent to audit for bugs after completing all 5 items, caught a localStorage cleanup issue

### Lessons Learned

#### 1. Clear Corrupted localStorage on Parse Failure
**Issue:** When initializing state from localStorage with `JSON.parse()` in a `try/catch`, the catch block returned a safe default `{}` but left the corrupted data in localStorage. On next load, it would fail again silently, repeatedly.
**Fix:** Added `localStorage.removeItem(key)` in the catch block so corrupted data is cleaned up.
**Rule:** Any `try { JSON.parse(localStorage.getItem(...)) } catch {}` pattern should also `removeItem` in the catch. Corrupted localStorage should be self-healing, not silently persistent.

#### 2. Optional Props for Progressive Enhancement
**Issue:** Adding `onAddProject` to AreaCard could break existing usages if the prop were required.
**Fix:** Made it optional (`onAddProject?: (areaId: number) => void`) — AreaCard renders the button only when the callback is provided.
**Rule:** When adding new callback props to shared components, always make them optional. Use conditional rendering (`{onX && <Button />}`) so consumers opt in.

#### 3. Pre-Selected Form Values via Props
**Issue:** CreateProjectModal always started with `area_id: undefined`. When triggered from an Area's "Add Project" button, the user had to manually re-select the area.
**Fix:** Added `defaultAreaId?: number` prop + a `useEffect` that syncs it when the modal opens. The reset logic on close clears it properly.
**Rule:** For modals that can be opened from different contexts, accept optional default values as props. Use `useEffect` to sync defaults when the trigger changes (not just initial render).

### Potential Backlog Items
1. **DEBT-029 (candidate):** Add Pydantic response model to `/next-actions/dashboard` endpoint — currently returns unvalidated dict
2. **BACKLOG-095 (candidate):** Apply collapsible section pattern to Weekly Review checklist and ProjectDetail task sections (as noted in BACKLOG-092 description)

---

## 2026-02-06: R2 Nice-to-Have + R3 Must-Have Batch (5 Backlog Items)

### What Went Well
1. **Combined migration strategy** — Merged Area health_score and archival columns into a single migration (008), reducing migration count and avoiding two ALTER TABLE passes on the same table
2. **Pattern reuse** — Area health score calculation reused the weighted-factor approach from existing momentum scoring, keeping the codebase consistent
3. **Post-implementation audit** — Ran a dedicated audit subagent after all 5 items were complete, which surfaced 34 issues across varying severity

### Lessons Learned

#### 1. setState During Render is a React Anti-Pattern
**Issue:** `EditObjectModal` in MemoryPage.tsx initializes form state with an `if` block in the render body that calls `setState`. This causes double-renders and is fragile in React strict mode.
**Fix:** Move initialization into a `useEffect` with the data object as dependency.
**Rule:** Never call `setState` directly in the render body. Always use `useEffect` for syncing state from props/data. The pattern `if (data && !initialized) { setState(...) }` in render is always wrong.

#### 2. Always Surface Query Error States
**Issue:** Both `useMemoryObjects` and `useMemoryNamespaces` destructure only `data` and `isLoading`, ignoring `isError`/`error`. When the API fails, users see either an infinite spinner or "No items" with no error indication.
**Fix:** Destructure `isError` and `error`, render an error banner when queries fail.
**Rule:** Every `useQuery` destructuring should include `isError` at minimum. If the query can fail (any network call), the component must render an error state.

#### 3. Falsy Zero Causes Infinite Recalculation
**Issue:** `get_project_health_summary` checks `if not project.momentum_score or project.momentum_score == 0` to decide whether to recalculate. Since `0.0` is falsy in Python, projects with a legitimately calculated score of 0.0 get recalculated on every single API call.
**Fix:** Use explicit `is None` check: `if project.momentum_score is None`.
**Rule:** Never use truthiness checks on numeric fields where zero is a valid value. Always use `is None` for "not yet calculated" vs `== 0` for "calculated as zero".

#### 4. Archive Operations Must Handle Dependent Active Entities
**Issue:** `archive_area` does not check for active projects belonging to the area. Archiving an area with active projects creates orphaned projects that are invisible in the default Areas view but still show up in Projects.
**Fix:** Either warn/block if area has active projects, or cascade-set projects to on_hold/someday status.
**Rule:** Any "archive" or "soft delete" operation must audit what depends on the entity being archived. Ask: "What becomes orphaned or invisible when this goes away?"

#### 5. Test Endpoints Should Actually Test
**Issue:** `/ai/test` creates an Anthropic client but never makes an API call, returning `success: True` for any non-empty key. Users think their key is valid when it may not be.
**Fix:** Make a minimal API call (e.g., `messages.create` with a 1-token max response) or at minimum validate the key format.
**Rule:** If an endpoint is named "test connection," it must actually test the connection. A constructor that doesn't throw is not a test.

### Technical Debt Identified
- [ ] DEBT-030: MemoryPage EditObjectModal setState in render body → move to useEffect
- [ ] DEBT-031: MemoryPage missing error state handling for queries (useMemoryObjects, useMemoryNamespaces)
- [ ] DEBT-032: `get_project_health_summary` falsy-zero recalculation bug (intelligence_service.py:510)
- [ ] DEBT-033: `update_all_area_health_scores` processes archived areas (intelligence_service.py:757)
- [ ] DEBT-034: `delete_area` does not handle cascading project IntegrityError (areas.py:153)
- [ ] DEBT-035: `archive_area` does not handle active projects belonging to the area (areas.py:190)
- [ ] DEBT-036: `/ai/test` endpoint doesn't actually test the connection (settings.py:87)
- [ ] DEBT-037: `detect_stalled_projects` has unused `threshold_date` variable (intelligence_service.py:366)
- [ ] DEBT-038: Duplicate `joinedload` import in intelligence_service.py (line 10 + line 755)
- [ ] DEBT-039: Priority input in MemoryPage allows out-of-range values client-side
- [ ] DEBT-040: `/ai/test` has no response_model (settings.py:87)
- [ ] DEBT-041: `create_unstuck_task` commits inside potentially larger transaction (intelligence_service.py:494)

### Potential Backlog Items
1. **BACKLOG-098 (candidate):** Momentum settings PUT endpoint — GET exists but no update counterpart
2. **BACKLOG-099 (candidate):** Archive area confirmation dialog — warn when area has active projects, offer cascade options

---

## 2026-02-06: R3 Must-Have + Tech Debt Batch (BACKLOG-096, 081, 097, DEBT-030/031)

### What Went Well
1. **Fast 5-item batch delivery** — All items implemented with clean TS + Vite builds after each phase
2. **Post-implementation audit** — Dedicated subagent audit caught 8 new issues, including a repeat of the DEBT-030 anti-pattern in freshly written code

### Lessons Learned

#### 1. Don't Introduce the Same Anti-Pattern You Just Fixed
**Issue:** DEBT-030 was a setState-in-render anti-pattern in MemoryPage. It was fixed by moving to useEffect. Then the brand-new ContextExportModal.tsx introduced the exact same pattern at lines 59-61: `if (isOpen && !context && !loading) { handleOpen(); }` in the render body.
**Fix:** Move auto-generate trigger into a useEffect with `[isOpen]` dependency.
**Rule:** After fixing an anti-pattern, search for the same pattern in any code written in the same session. If you just fixed "setState in render body," grep for it in all new components before marking complete.

#### 2. File-Write Functions Need Value Sanitization
**Issue:** `_persist_to_env()` writes API keys to .env without sanitizing the value. A key containing newlines could inject additional environment variables; special regex chars in values could cause corruption on subsequent updates.
**Fix:** Strip newlines from values, and use string replacement instead of regex for the value portion.
**Rule:** Any function that writes user-provided values to a config/env file must sanitize: strip newlines, validate format, and avoid regex on untrusted values.

#### 3. File I/O Has Race Conditions — Add Locking for Config Files
**Issue:** `_persist_to_env()` reads, modifies, and writes .env without any locking. Concurrent API requests could lose each other's changes (TOCTOU race).
**Fix:** Use `fcntl.flock()` (Unix) or `msvcrt.locking()` (Windows) or a threading Lock for single-process safety.
**Rule:** Any read-modify-write cycle on a shared file needs a lock. For single-process FastAPI, a `threading.Lock` is sufficient. For multi-process, use file-level locking.

#### 4. Don't Query the Same Data Twice in One Endpoint
**Issue:** The AI context export overview path queries `func.count(Project.id)` for the summary, then fetches ALL active projects with joinedload just to count them again for the response stats.
**Fix:** Reuse the summary count, or use a single aggregate query for task counts: `select(func.count(Task.id)).join(Project).where(Project.status == 'active')`.
**Rule:** Before writing a new query, check if the data is already available from an earlier query in the same function. If you need a count, use `func.count()`, not `len(list)`.

#### 5. Modal Components Need Cleanup on Close
**Issue:** ContextExportModal keeps stale `context` state when closed and reopened. Also has no AbortController for in-flight API calls, causing React memory leak warnings on unmount.
**Fix:** Reset state in an `onClose` handler or useEffect cleanup. Use AbortController for fetch cancellation.
**Rule:** Any modal that fetches data on open should: (a) reset state when closing, (b) cancel in-flight requests on unmount, (c) never auto-trigger fetches in the render body.

### Technical Debt Identified
- [ ] DEBT-042: `_persist_to_env` race condition on concurrent .env writes
- [ ] DEBT-043: `_persist_to_env` no value sanitization (newlines/special chars)
- [ ] DEBT-044: Unused imports in settings.py and export.py
- [ ] DEBT-045: AI context export N+1 query in overview path
- [ ] DEBT-046: ContextExportModal setState-in-render (same as DEBT-030)
- [ ] DEBT-047: ContextExportModal stale data + memory leak on unmount
- [ ] DEBT-048: SQLAlchemy `== False` → `.is_(False)` in export.py
- [ ] DEBT-049: Collapsible section buttons missing `type="button"` and `aria-expanded`

### Potential Backlog Items
1. **BACKLOG-100:** Settings sections default collapsed (already added)
2. **BACKLOG-101:** Dashboard stats block visual consistency (already added)
3. **BUG-020:** Dashboard Pending Tasks count incorrect (already added)
4. **BACKLOG-102:** Project Mark Reviewed button (already added)

---

## 2026-02-06: BUG-020, BACKLOG-102, BACKLOG-100, ROADMAP-008, BACKLOG-086 Batch

### What Went Well
1. **5-item batch delivery** — All items implemented with clean builds, spanning both backend and frontend
2. **Provider abstraction design** — ABC + factory pattern for multi-AI provider is extensible without touching existing code
3. **Pattern reuse** — Mark Reviewed on ProjectDetail replicated existing AreaDetail pattern exactly for consistency

### Lessons Learned

#### 1. Always Verify SQLAlchemy Imports When Using Aggregates
**Issue:** New `get_dashboard_stats` endpoint used `func.count(Task.id)` but only `select` was imported from sqlalchemy at module level. Caused `NameError: name 'func' is not defined` at runtime.
**Fix:** Added `func` to the import: `from sqlalchemy import func, select`.
**Rule:** When writing new endpoints that use `func.count()`, `func.sum()`, or similar SQLAlchemy aggregates, verify `func` is imported at the module level. Don't assume prior imports cover it — check the actual import line.

#### 2. Lazy Imports for Optional Dependencies
**Issue:** Multi-provider support (OpenAI, Google) requires packages that may not be installed. Importing at module level would crash the entire app.
**Fix:** Import inside `__init__` with try/except, raising a clear error message: `"Install openai package: pip install openai"`.
**Rule:** For optional provider integrations, use lazy imports inside the class constructor. This keeps the app functional even without optional packages installed.

#### 3. Settings Default State Matters for UX
**Issue:** Settings sections defaulting to expanded forced users to scroll past irrelevant sections. Small detail, big UX impact.
**Fix:** Default all sections to collapsed via `new Set(['appearance', 'area-mappings', 'database', 'sync', 'ai', 'momentum'])`.
**Rule:** For settings pages with many sections, default to collapsed. Users can expand what they need. The expand-all pattern is appropriate for pages with 2-3 sections, not 6+.

#### 4. Onboarding Re-Entry Must Be Idempotent
**Issue:** If a user runs onboarding twice (e.g., after a reset), creating new memory objects would fail or create duplicates.
**Fix:** Check for existing objects by `object_id` and update them instead of creating new ones.
**Rule:** Any onboarding/setup endpoint should handle re-entry gracefully — check for existing data and update rather than fail or duplicate.

### Technical Debt Identified
- [ ] DEBT-050: Unused `timedelta` import in ai_service.py
- [ ] DEBT-051: Inconsistent BaseModel naming in memory_layer/routes.py (`PydanticBaseModel` alias)
- [ ] DEBT-052: Empty model dropdown edge case in Settings.tsx when provider_models not yet loaded

### Potential Backlog Items
1. **BACKLOG-103:** Project Review Frequency + Mark Reviewed Next Date (already added to Parking Lot)

---

## 2026-02-07: Batch 2 — BUG-021/022/023 + BACKLOG-105/106/108 + DEBT-044/056

### What Went Well
1. **3 release blockers fixed in one session** — BUG-021/022/023 all resolved, unblocking user testing
2. **Subquery annotation pattern** — BACKLOG-106 used correlated SQL subqueries instead of eager-loading tasks, avoiding N+1
3. **Module-aware navigation** — BACKLOG-105 uses graceful degradation (shows all items until modules endpoint responds)

### Lessons Learned

#### 1. React Hooks Must Be Called Unconditionally
**Issue:** BUG-021 — Projects.tsx had an `if (error) return <Error />` between `useEffect` and `useMemo` hooks, violating Rules of Hooks. Caused white screen crash on error.
**Fix:** Moved the early return after ALL hooks are called.
**Rule:** Never place early returns between hook calls. All hooks must execute on every render. Place conditional returns AFTER the last hook.

#### 2. Partial Migration Application Can Leave Inconsistent Schema
**Issue:** BUG-022 — The auth migration (user_id columns) was partially applied. projects/areas/inbox had user_id but goals/visions did not, despite alembic_version showing the migration as complete.
**Fix:** Created a targeted repair migration that checks for column existence before adding.
**Rule:** When a migration fails partway through on SQLite, alembic_version may still be stamped. Always verify actual column existence with `PRAGMA table_info()` rather than trusting version stamps.

#### 3. Dynamic Attribute Assignment on ORM Objects is Fragile
**Issue:** BACKLOG-106 — `project.task_count = task_count` dynamically assigns to SQLAlchemy ORM objects. Works because Pydantic's `from_attributes=True` picks them up, but is invisible to type checkers and breaks if the ORM model adds a conflicting column.
**Rule:** When annotating ORM query results with extra computed columns, prefer returning a separate DTO/dict rather than monkey-patching ORM instances. Accept the trade-off for simplicity only when the scope is limited.

#### 4. Raw fetch() Bypasses API Client
**Issue:** BACKLOG-105 — Layout.tsx uses `fetch('/modules')` directly instead of the shared API client. Misses auth headers, error handling, and abort cleanup.
**Rule:** Always use the project's API client/service layer for HTTP calls, even for simple GETs. The client handles auth tokens, base URL, and consistent error formatting.

#### 5. ErrorBoundary "Try Again" Can Loop on Deterministic Errors
**Issue:** BACKLOG-108 — The "Try Again" button calls `setState({ hasError: false })` which re-renders the children. If the error is deterministic (e.g., missing data, bad prop), it immediately crashes again, creating an infinite loop.
**Rule:** ErrorBoundary reset should navigate to a known-safe route (like `/`) or at minimum track reset attempts and offer "Go Home" after 2 consecutive crashes.

#### 6. Keep Enum Definitions in Sync with Application Code
**Issue:** Integrity checker's ENUM_DEFINITIONS was missing `someday_maybe` for task_type and `archived`/`someday_maybe` for project status, causing false positive warnings during migrations.
**Rule:** When adding new enum values to models/schemas, also update any validation/integrity checking code that hardcodes allowed values.

### Technical Debt Identified
- [ ] DEBT-058: `get_by_id` returns `task_count: 0` — detail pages show misleading counts
- [ ] DEBT-059: Raw `fetch('/modules')` in Layout.tsx bypasses API client (auth, error handling, AbortController)
- [ ] DEBT-060: ErrorBoundary "Try Again" can infinite-loop on deterministic errors
- [ ] DEBT-061: Dynamic attribute assignment on ORM objects for task counts (fragile pattern)
- [ ] DEBT-062: Redundant task_count fields in ProjectWithTasks schema
- [ ] DEBT-063: `/modules` proxy needs production server configuration

---

## 2026-02-07: Batch 4 — DIST-040, DEBT-024/028/046/047/048/055

### What Went Well
1. **DEBT-024 fully resolved** — The longstanding broken API test infrastructure (noted since 2026-02-03!) is finally fixed. 18/18 tests pass. This unblocks CI (DIST-043).
2. **Systematic `== False` grep** — After fixing one instance (DEBT-048), searched for and fixed 2 more instances in areas.py and intelligence_service.py. Pattern: always grep after a targeted fix.
3. **DEBT-055 verified N/A** — Instead of blindly implementing, confirmed ContextExportModal already uses the shared Modal component which has a backdrop. Saved wasted work.

### Lessons Learned

#### 1. In-Memory SQLite Needs StaticPool for TestClient
**Issue:** `sqlite:///:memory:` creates a *separate database per connection*. Without `StaticPool`, `Base.metadata.create_all(bind=engine)` creates tables on one connection, but each `TestingSessionLocal()` opens a different connection to a brand new (empty) database.
**Fix:** Use `poolclass=StaticPool` from `sqlalchemy.pool` to force all connections to share the same in-memory database.
**Rule:** **Always** use `StaticPool` when testing with `sqlite:///:memory:` and a multi-session setup (TestClient + dependency override). This is THE canonical pattern for SQLAlchemy + FastAPI testing.

#### 2. Patch Startup Side-Effects Explicitly in TestClient Fixtures
**Issue:** `TestClient(app)` triggers `@app.on_event("startup")` which calls `init_db()`, `start_scheduler()`, `enable_wal_mode()`, `run_urgency_zone_recalculation_now()`, `start_folder_watcher()` — all of which fail or interfere in a test context.
**Fix:** Patch each side-effect before creating TestClient: `init_db` (would create tables on production engine), `enable_wal_mode` (requires real SQLite file), `register_modules`, `start_scheduler`, etc.
**Rule:** When creating a TestClient fixture, list every startup event side-effect and decide: patch it, override it, or let it run. Document the decision in comments above each `patch()`.

#### 3. After a Targeted Fix, Grep for the Same Pattern Project-Wide
**Issue:** DEBT-048 only specified `export.py` line 272. But `== False` was also in `areas.py` and `intelligence_service.py` (and `== True` exists in 8 more places).
**Fix:** After fixing the specified location, grepped for `== False` and `== True` across the entire backend.
**Rule:** When fixing a pattern-based issue (anti-pattern, style issue, SQL correctness), always `grep -r` the entire codebase for the same pattern before marking complete. File the remaining instances as new debt items.

#### 4. The "Processed Today" Filter Must Handle the showProcessed Toggle
**Issue:** DEBT-028 — When `showProcessed=false`, the API only returns unprocessed items. Filtering `items.filter(i => i.processed_at)` yields 0. When `showProcessed=true`, it returns ALL processed items ever, not just today's.
**Fix:** Client-side date filter comparing `processed_at` year/month/day to today. Note: this only works correctly when `showProcessed=true` (processed items are loaded). When `showProcessed=false`, the stat will show 0 because the data isn't loaded.
**Remaining gap:** DEBT-064 — "Processed Today" stat requires a dedicated API endpoint or a separate query that always returns today's count, independent of the main list filter. Current fix is partial — shows 0 when viewing unprocessed items.

#### 5. AbortController in Component vs. Signal in API Client — Two Different Things
**Issue:** ContextExportModal now has an `AbortController` ref, but `api.getAIContext()` doesn't accept an `AbortSignal` parameter. The controller only prevents setState-after-unmount; it doesn't actually cancel the HTTP request.
**Fix applied:** Checking `controller.signal.aborted` before `setState` prevents memory leak warnings.
**Remaining gap:** DEBT-065 — API client methods should accept an optional `AbortSignal` and pass it to axios: `this.client.get(url, { signal })`. This enables true request cancellation.

### Technical Debt Identified
- [x] DEBT-024: ~~Test infrastructure broken~~ → FIXED (18/18 pass)
- [x] DEBT-028: ~~Inbox Processed Today stat~~ → FIXED (partial — see DEBT-064)
- [x] DEBT-046: ~~ContextExportModal setState-in-render~~ → FIXED
- [x] DEBT-047: ~~ContextExportModal stale data + memory leak~~ → FIXED
- [x] DEBT-048: ~~SQLAlchemy `== False`~~ → FIXED in 3 files
- [x] DEBT-055: ~~ContextExportModal missing backdrop~~ → N/A (already has backdrop via Modal)
- [ ] DEBT-064: "Processed Today" count needs dedicated API endpoint (current fix shows 0 when viewing unprocessed tab)
- [ ] DEBT-065: API client methods don't accept AbortSignal — prevents true HTTP request cancellation
- [ ] DEBT-066: SQLAlchemy `== True` pattern exists in 8 locations (intelligence_service.py ×3, next_actions_service.py ×3, task_service.py ×1, memory_layer/services.py ×1)
- [ ] DEBT-067: FastAPI `@app.on_event("startup"/"shutdown")` deprecated — migrate to lifespan context manager (9 deprecation warnings in test output)
- [ ] DEBT-068: Pydantic V1-style `class Config` and `Field(example=...)` deprecated — migrate to `ConfigDict` and `json_schema_extra`
- [ ] DEBT-069: conftest.py `in_memory_engine` fixture missing `StaticPool` — will break if used with multi-session patterns
- [ ] DEBT-070: conftest.py `db_session` fixture and test_api_basic.py `test_client` fixture duplicate engine setup — consolidate into shared conftest

### Potential Backlog Items
1. **DIST-040 pending:** Git repo initialized but needs `git config user.name/email` before initial commit
2. **DIST-043 unblocked:** Test suite now stable (18/18 pass), ready for CI pipeline setup

---

## 2026-02-07: Batch 5+6 — BACKLOG-072/084/091/098 + DEBT-042/043/045/050/066/067

### What Went Well
1. **11 items across 2 batches** — Clean builds after every phase, zero regressions
2. **Lifespan migration (DEBT-067)** was clean — tests still pass 18/18 after converting on_event to asynccontextmanager
3. **N+1 elimination (DEBT-045)** — Removed 3 redundant queries from AI context export by reusing a single `all_active` fetch
4. **Pattern-based grep (DEBT-066)** — Found and fixed all 8 `== True` instances across 4 files in one pass

### Lessons Learned

#### 1. Lifespan Functions Must Be Defined Before `app = FastAPI()`
**Issue:** After converting `@app.on_event("startup")` and `@app.on_event("shutdown")` to a `lifespan` async context manager, the initial attempt defined `lifespan()` below `app = FastAPI(lifespan=lifespan)`. Python evaluates `FastAPI(lifespan=lifespan)` at import time, causing a NameError.
**Fix:** Move `lifespan()` and all helper functions (`register_modules`, `mount_module_routers`) above the `app = FastAPI(...)` call.
**Rule:** When converting to FastAPI's lifespan pattern, restructure the file so: (1) imports, (2) helper functions, (3) lifespan function, (4) `app = FastAPI(lifespan=lifespan)`, (5) middleware/routes. The lifespan must be defined before it's referenced.

#### 2. `mount_module_routers` Needs Explicit `app` Parameter in Lifespan
**Issue:** The old `mount_module_routers()` function used the global `app` variable. Inside `lifespan(app)`, the `app` parameter shadows the global. The function worked by accident before because the global was defined by the time startup ran, but it's cleaner and more correct to pass `app` explicitly.
**Fix:** Changed signature to `mount_module_routers(app: FastAPI, enabled_modules)` and called with the lifespan's `app` parameter.
**Rule:** Functions called inside lifespan should receive `app` as a parameter, not rely on module-level globals. This makes testing easier and avoids subtle import-order bugs.

#### 3. Unused Imports Accumulate After Refactoring — Always Check
**Issue:** After DEBT-045 removed `func.count()` queries from export.py, the `func` import from sqlalchemy became unused. After DEBT-067 refactored main.py, `get_db` and potentially `Path` became unused imports.
**Fix:** Grepped for remaining usages of `func` and removed the import. Filed DEBT-071/072 for the main.py leftovers.
**Rule:** After any refactor that removes code, immediately check if the imports used by that code are still needed elsewhere in the file. `grep` for the import name in the same file.

#### 4. Venv Must Be Documented for Claude Code Sessions
**Issue:** `python -m pytest` fails because the system Python doesn't have sqlalchemy installed. The project has a `venv/` directory with all dependencies, but nothing tells Claude Code to use it. The fix is `"C:\Dev\...\venv\Scripts\python.exe" -m pytest`.
**Fix:** Filed DEBT-078. For now, always use the explicit venv python path when running backend commands.
**Rule:** If a project uses a venv, document the activation command in CLAUDE.md or QUICKSTART.md so automated tools (and future Claude sessions) know how to run tests.

#### 5. Settings Mutations on Singleton Config Objects Are Risky
**Issue:** The momentum PUT endpoint does `settings.MOMENTUM_STALLED_THRESHOLD_DAYS = value` directly on the Pydantic Settings singleton. If Pydantic Settings has `model_config = ConfigDict(frozen=True)`, this will raise an error. Currently works because the config isn't frozen, but it's fragile.
**Fix:** Filed DEBT-075. Consider using a separate mutable runtime config dict or a dedicated settings service.
**Rule:** Don't mutate Pydantic Settings objects at runtime unless you've verified they're not frozen. Prefer a separate runtime config layer for dynamic settings.

### Technical Debt Identified
- [ ] DEBT-071: Unused `get_db` import in main.py after lifespan refactor
- [ ] DEBT-072: Potentially unused `Path` import in main.py
- [ ] DEBT-073: Momentum section missing icon in Settings.tsx (inconsistent with other sections)
- [ ] DEBT-074: `recalculateInterval` loaded but not shown in UI
- [ ] DEBT-075: Momentum PUT mutates singleton settings object (fragile if frozen)
- [ ] DEBT-076: Duplicate blob download logic in api.ts
- [ ] DEBT-077: pytest-asyncio mode=AUTO warning from pyproject.toml
- [ ] DEBT-078: Tests require explicit venv python path

### Potential Backlog Items
1. **BACKLOG-111:** Momentum settings stalled > at_risk validation (client + server)
2. **BACKLOG-112:** Export preview refresh after download

---

## 2026-02-07: Release Prep Round 4 — Tech Debt, End-to-End Testing, Tracking Reconciliation

### What Went Well
1. **End-to-end testing caught 3 real bugs** — root endpoint serving, migration idempotency, Windows encoding. All 3 would have affected first-time users.
2. **Backlog reconciliation** — 11 stale DIST items updated from "Open" to "Done", keeping tracking accurate.
3. **Subagent strategy** — 4 parallel explore agents at session start gathered version refs, dependency status, unused imports, and DIST item status simultaneously, saving ~3 minutes.

### Lessons Learned

#### 1. Repair Migrations Must Be Idempotent
**Issue:** Migration 010 (repair_user_id) unconditionally added `user_id` to `goals` and `visions` tables. On a fresh install, auth migration 007 already adds these columns. When 010 runs, `batch_alter_table` creates `_alembic_tmp_goals` which conflicts with the already-correct schema.
**Fix:** Added `_column_exists()` helper using `PRAGMA table_info` to check before altering. Both `upgrade()` and `downgrade()` now guard on column existence.
**Rule:** Any "repair" or "fixup" migration MUST check whether the repair is actually needed before applying it. Use `PRAGMA table_info(table_name)` on SQLite to check column existence. This makes migrations safe for both fresh installs and existing databases with partial state.

#### 2. FastAPI Route Priority — First Match Wins
**Issue:** Root `/` had a JSON API info endpoint defined before the SPA catch-all `/{full_path:path}`. The catch-all pattern doesn't match empty string, so root always served JSON even in production with the frontend build present.
**Fix:** Updated root endpoint to conditionally serve `index.html` when `frontend/dist/index.html` exists, falling back to API info JSON for development.
**Rule:** In FastAPI, the first defined route matching a path wins. The `{path:path}` parameter matches one or more path segments, NOT the empty string. Always test the root `/` path separately from catch-all patterns.

#### 3. Windows Console Encoding Is Not UTF-8 by Default
**Issue:** `run.py` used Unicode box-drawing character `─` (U+2500) in the startup banner. On Windows, the default console encoding is `cp1252`, which doesn't support this character. Result: `UnicodeEncodeError` on `print()`.
**Fix:** Changed to ASCII `-` character for cross-platform compatibility.
**Rule:** Any `print()` output that might run on Windows must use ASCII-safe characters unless `sys.stdout.encoding` is verified. Common offenders: box-drawing characters (`─│┌┐`), checkmarks (`✓✗`), arrows (`→←`). Use ASCII alternatives or wrap in `try/except UnicodeEncodeError`.

#### 4. Pydantic BaseSettings .env Overrides Defaults
**Issue:** `config.py` had `VERSION: str = "1.0.0-alpha"` but local `.env` file had `VERSION=0.1.0` (stale from early development). Pydantic BaseSettings reads `.env` first, so the stale value won.
**Fix:** Updated local `.env` to `1.0.0-alpha`. Also a distribution lesson: the `.env.example` should always reflect the correct version.
**Rule:** When bumping version numbers, check ALL locations: config.py default, .env.example template, AND the local .env file. Pydantic BaseSettings precedence: env vars > .env file > class defaults.

### Technical Debt Identified
- [x] DEBT-068: ~~Pydantic V1 deprecations~~ → FIXED (9 instances across 3 files)
- [x] DEBT-071: ~~Unused `get_db` import~~ → FIXED (removed from main.py)
- [x] DEBT-072: ~~`Path` unused in main.py~~ → N/A (actively used in 5 locations)

### Potential Backlog Items
1. **BUG-024 (candidate):** Pre-existing test failure — `test_excludes_deferred_tasks` asserts `len(results) == 2` but gets 3 (deferred task not filtered)
2. **DEBT-079 (candidate):** Root endpoint dual behavior should be documented in API docs or removed from OpenAPI schema when SPA is active

---

## 2026-02-07: Release Prep Round 5 — BUG-024, DEBT-049/077, DIST-010, Phase 1.5

### What Went Well
1. **100% test pass rate achieved** — BUG-024 fix brought tests from 173/174 to 174/174, eliminating the last pre-existing failure
2. **Parallel subagent triage** — 3 explore agents at session start identified all open items (deferred bug, branding refs, AI degradation status) simultaneously
3. **Clean distribution prep** — .gitignore approach for dev artifacts is simpler and more maintainable than build-time exclusion scripts

### Lessons Learned

#### 1. Deferred Tasks Need SQL-Level Filtering, Not Just Sort-Level
**Issue:** `get_prioritized_next_actions()` included deferred tasks (where `defer_until > today`) in query results and tried to handle them via sort tier 6 (sort to bottom). But the test expected them excluded entirely, and the UX intent was to hide them until their defer date arrives.
**Fix:** Added `(Task.defer_until.is_(None)) | (Task.defer_until <= today)` to the SQL WHERE clause. Removed the now-dead sort tier 6 code.
**Rule:** When a task has a "don't show until date X" field, filter it out at the SQL level, not at the sort level. Sort tiers are for ordering visible items; WHERE clauses are for excluding invisible ones. If you find yourself sorting items to the bottom to "hide" them, you should be filtering them out instead.

#### 2. Toggle Buttons Need `type="button"` to Prevent Form Submission
**Issue:** Collapsible section toggle buttons in Settings.tsx and NextActions.tsx lacked `type="button"`. Inside a form context, the default `type="submit"` could cause unintended form submission on click.
**Fix:** Added `type="button"` to all 8 toggle buttons. Also added `aria-expanded={!collapsed}` for screen reader accessibility.
**Rule:** Any `<button>` that toggles UI state (collapse/expand, show/hide) must have `type="button"`. Also add `aria-expanded` to communicate state to assistive technology. Grep for `onClick.*collapsed\|onClick.*toggle` to find candidates.

#### 3. Dev Artifact Exclusion via .gitignore Is Simpler Than Build Scripts
**Issue:** DIST-010 required excluding dev-only files (CLAUDE.md, MODULE_SYSTEM.md, diagnose.py, distribution-checklist.md, tasks/) from distribution builds.
**Fix:** Added entries to .gitignore rather than creating build-time exclusion scripts. Since distribution is via git-based packaging, .gitignore naturally excludes these files.
**Rule:** For projects distributed via git (or built from git checkouts), .gitignore is the simplest mechanism to exclude dev artifacts. Reserve build-time exclusion for files that must be in git but not in the distribution (rare case).

#### 4. AI Feature Degradation Should Be a Boolean Flag, Not Try/Catch Everywhere
**Issue:** Needed to verify that the app works gracefully when AI features are unavailable (no API key, optional dependency).
**Finding:** The codebase already handles this well — `AI_FEATURES_ENABLED` flag checked at startup, `create_provider()` raises clean ValueError, API endpoints return HTTP 400 with descriptive messages. No silent failures or stack traces.
**Rule:** For optional integrations (AI, external APIs), use a single boolean flag at startup to gate feature availability. Don't scatter try/catch blocks across individual endpoints. Check the flag once, set it at startup, and have endpoints check it before attempting operations.

### Technical Debt Resolved
- [x] BUG-024: ~~Deferred tasks not filtered in next actions~~ → FIXED (SQL WHERE clause)
- [x] DEBT-049: ~~Collapsible buttons missing type/aria~~ → FIXED (8 buttons)
- [x] DEBT-077: ~~pytest-asyncio mode warning~~ → FIXED (removed from pyproject.toml)
- [x] DIST-010: ~~Dev artifacts in distribution~~ → FIXED (.gitignore)

---

## 2026-02-08: Distribution — PyInstaller Packaging, Runtime Testing, Inno Setup Installer

### What Went Well
1. **Comprehensive runtime testing** — 13-point test checklist (launch, migrations, server, browser, setup wizard, SPA routes, static assets, API, data dir, logs, tray, shutdown, persistence) all passed on first run from `dist/`
2. **Inno Setup installer** — Script created, compiled, and full install→launch→use→uninstall cycle verified within a single session
3. **Fast bug turnaround** — Uvicorn logging crash discovered during install testing, root-caused via subagent research, fixed with one-line change, rebuilt, and re-verified all within minutes

### Lessons Learned

#### 1. Uvicorn's Default Logging Config Crashes in Console-False PyInstaller Bundles
**Issue:** `ValueError: Unable to configure formatter 'default'` when launching the installed exe from `C:\Program Files\Conduital\`. The exe launched fine from `dist/` during dev testing (which has a console), but crashed when run via the installer (no console window).
**Root cause:** Uvicorn's `LOGGING_CONFIG` dict uses `"()": "uvicorn.logging.DefaultFormatter"` which calls `sys.stderr.isatty()` during class instantiation. In a PyInstaller `console=False` bundle, `sys.stderr` is `None` or a null device, causing the formatter factory to fail inside `logging.config.dictConfig()`.
**Fix:** Added `log_config=None` to `uvicorn.Config()` in `run_packaged()`. The app's own `logging_config.py` handles all logging.
**Rule:** When embedding Uvicorn in a packaged app (especially `console=False`), ALWAYS set `log_config=None` to disable Uvicorn's default logging setup. Provide your own logging configuration. The same issue affects any library that assumes `sys.stderr.isatty()` works — audit third-party libs for TTY assumptions when packaging with `console=False`.

#### 2. Inno Setup Preprocessor (ISPP) Conflicts with Pascal Script `#` Constants
**Issue:** `#13#10` (carriage return + line feed) in Pascal Script `[Code]` section caused `Unknown preprocessor directive` error. ISPP runs before Pascal compilation and interprets `#13` as a preprocessor directive.
**Fix:** Replace `#13#10` with `Chr(13) + Chr(10)` in all `[Code]` section strings.
**Rule:** In Inno Setup `.iss` files, NEVER use `#N` character constants in `[Code]` sections — they conflict with ISPP. Use `Chr(N)` function calls instead. This applies to any Pascal Script constant syntax that starts with `#`.

#### 3. Windows `VersionInfoProductVersion` Requires x.x.x.x Format
**Issue:** Setting `VersionInfoProductVersion=1.0.0-alpha` in the `.iss` file caused `Value of [Setup] section directive "VersionInfoProductVersion" is invalid`.
**Fix:** Changed to `VersionInfoProductVersion=1.0.0.0`. The human-readable version (`1.0.0-alpha`) is in `AppVersion` and `AppVerName` instead.
**Rule:** Windows version info fields (`VersionInfoVersion`, `VersionInfoProductVersion`) require strict `x.x.x.x` numeric format. SemVer prerelease tags (`-alpha`, `-beta`) cannot be used in these fields. Use `AppVersion` for the display version with prerelease tags.

#### 4. Silent Uninstall with /SUPPRESSMSGBOXES Auto-Accepts Destructive Prompts
**Issue:** During testing, ran uninstaller with `/VERYSILENT /SUPPRESSMSGBOXES` which auto-accepted the "Remove user data?" prompt, deleting the test database with data the user wanted to keep.
**Fix:** Awareness — document that `/SUPPRESSMSGBOXES` will auto-remove user data. For CI/automation, use `/VERYSILENT` without `/SUPPRESSMSGBOXES` if the data prompt should block.
**Rule:** Custom uninstall prompts in Inno Setup `[Code]` will be auto-accepted by `/SUPPRESSMSGBOXES`. If your uninstaller has destructive options (like deleting user data), document this clearly and consider making the destructive path opt-IN (require `/REMOVEDATA` flag) rather than auto-accepted.

#### 5. Test Data Is Ephemeral — Back Up Before Destructive Testing
**Issue:** The test data created during runtime testing was lost when the uninstall cycle test removed `%LOCALAPPDATA%\Conduital\`. The user had wanted to keep that data.
**Fix:** N/A — data was lost.
**Rule:** Before running install/uninstall cycle tests, always back up `%LOCALAPPDATA%\Conduital\` if the data has any value. Better yet, create a separate test data profile or copy the database file to a safe location before destructive testing.

### Technical Debt Identified
- [ ] DEBT-080: Inno Setup `.iss` version is hardcoded (`#define MyAppVersion "1.0.0-alpha"`) — not a single source of truth with pyproject.toml/config.py
- [ ] DEBT-081: No app icon (.ico) — installer and exe use default icons; needs `assets/conduital.ico` with 16x16 through 256x256 variants
- [ ] DEBT-082: `build.bat` size reporting loop is broken — shows "Total size: ~0 MB" for most lines (findstr parsing issue with dir output)
- [ ] DEBT-083: Installer `InitializeSetup()` uses `taskkill /F` which force-kills without allowing graceful shutdown — should attempt graceful close first (e.g., via WM_CLOSE or a shutdown endpoint) then fall back to force-kill

### Potential Backlog Items
1. **BACKLOG-115:** Add a `/api/v1/shutdown` endpoint for graceful programmatic shutdown — would allow installer and tray to request clean shutdown instead of force-killing
2. **BACKLOG-116:** Version single source of truth — read version from one canonical file (e.g., pyproject.toml) at build time for PyInstaller spec, Inno Setup `.iss`, and frontend package.json
3. **BACKLOG-117:** Installer upgrade-in-place testing — verify that installing a new version over an existing one preserves user data and applies new migrations correctly
4. **BACKLOG-118:** Clean Windows VM testing — test on Win10 and Win11 VMs with no Python/Node.js installed to catch missing DLLs or runtime dependencies

---

## 2026-02-12: Session 2 — ROADMAP-002 AI Features Integration

### What Went Well
1. **4 full-stack features in one session** — Each feature (proactive analysis, task decomposition, rebalancing, energy recs) implemented end-to-end (Pydantic models + endpoint + types + API method + hook + component + integration)
2. **Test-driven bug discovery** — The energy recommendations test caught the wrong task creation endpoint (`/projects/{id}/tasks` vs `/tasks`) before any manual testing
3. **Pattern reuse** — All 4 components followed established violet-theme, expandable-section, mutation-hook patterns from Session 1

### Lessons Learned

#### 1. Task Creation Endpoint Is POST /api/v1/tasks, Not /projects/{id}/tasks
**Issue:** Test for energy recommendations created a task via `POST /api/v1/projects/{project_id}/tasks`, which returned 404. The task was never created, so the energy endpoint found 0 tasks.
**Fix:** Changed to `POST /api/v1/tasks` with `project_id` in the request body.
**Rule:** In Conduital, task creation uses a flat endpoint (`POST /tasks`) with `project_id` in the body — NOT a nested resource path. Always check the router prefix before writing tests.

#### 2. String.replace() Only Replaces First Match
**Issue:** `task.context.replace('_', ' ')` only replaces the first underscore. A context like `"deep_work_mode"` displays as `"deep work_mode"`.
**Fix:** Use `.replace(/_/g, ' ')` (regex) or `.replaceAll('_', ' ')`.
**Rule:** JavaScript `String.replace(string, string)` only replaces the first occurrence. For replace-all behavior, use regex with global flag or `.replaceAll()`.

#### 3. handleCreateAll Needs Sequential Mutation Calls
**Issue:** `handleCreateAll` in AITaskDecomposition fires N `createTask.mutate()` calls in a tight synchronous loop. TanStack Query mutations are not queued — this sends N parallel POST requests. Also uses `tasks.indexOf(task)` for index lookup, which fails for duplicate task objects.
**Fix:** Use `mutateAsync` with sequential `await` or `Promise.allSettled`.
**Rule:** When calling mutations in a loop, use `mutateAsync` + `await` for sequential execution or `Promise.allSettled` for controlled parallelism. Never fire N `.mutate()` calls synchronously — they race.

#### 4. isinstance(date, datetime) Is Always False
**Issue:** In the rebalance endpoint, `isinstance(t.due_date, datetime)` is always False because `due_date` is a `date` object, not a `datetime` object. Python's `datetime` is a subclass of `date`, but `date` is NOT a subclass of `datetime`. This makes the due-date promotion to critical_now dead code.
**Fix:** Check `isinstance(t.due_date, date)` and compare using date arithmetic instead of datetime arithmetic.
**Rule:** In Python, `isinstance(date_obj, datetime)` is False even though `isinstance(datetime_obj, date)` is True. When checking date columns, use `isinstance(x, date)` if you want to match both. For type-specific behavior, check `datetime` first (narrower type).

#### 5. Frontend Components Must Handle Query Error States
**Issue:** AIEnergyRecommendations and AIRebalanceSuggestions destructure `{ data, isLoading }` but ignore `isError/error`. When the API fails, users see nothing — no error, no retry option.
**Rule:** Every `useQuery` destructuring should include `isError` at minimum. If the query can fail, the component must render an error state. Pattern: `if (isError) return <ErrorBanner retry={refetch} />`.

#### 6. Premature Cache Invalidation Wastes Network Requests
**Issue:** `useDecomposeTasksFromNotes` invalidates `['projects']` query cache on success, but decomposition doesn't create tasks — it only returns suggestions. The actual task creation happens later in the component.
**Fix:** Remove `onSuccess` invalidation from the decompose hook. The `useCreateTask` hook already invalidates properly when tasks are actually created.
**Rule:** Only invalidate query caches when the underlying data actually changes. A read/compute operation (like AI decomposition) should not invalidate the entity cache.

### Technical Debt Identified
- [ ] BUG-027: Rebalance endpoint `due_date` type check — `isinstance(t.due_date, datetime)` always False for date columns; critical_now promotion is dead code
- [ ] DEBT-093: `String.replace('_', ' ')` only replaces first underscore in AITaskDecomposition.tsx and AIEnergyRecommendations.tsx (2 locations)
- [ ] DEBT-094: `handleCreateAll` in AITaskDecomposition fires N parallel mutations without throttling + uses `indexOf` for index lookup
- [ ] DEBT-095: AIEnergyRecommendations and AIRebalanceSuggestions missing error state handling (no isError destructure)
- [ ] DEBT-096: `useDecomposeTasksFromNotes` hook invalidates `['projects']` cache prematurely (decomposition doesn't modify data)
- [ ] DEBT-097: AIProactiveInsights stores data in both mutation result AND separate useState (split source of truth)
- [ ] DEBT-098: `getProactiveAnalysis` and `decomposeTasksFromNotes` API methods lack AbortSignal support (POST mutations to slow AI endpoints)
- [ ] DEBT-099: AIEnergyRecommendations missing violet border (inconsistent with other AI components)
- [ ] DEBT-100: AIRebalanceSuggestions expand/collapse button missing `aria-expanded` and `aria-controls`
- [ ] DEBT-101: AITaskDecomposition "Create this task" Plus button missing `aria-label`
- [ ] DEBT-102: Proactive analysis and decompose endpoints missing upfront ANTHROPIC_API_KEY check (inconsistent with other AI endpoints; falls back to try/except)
- [ ] DEBT-103: Proactive analysis per-project error handler leaks raw exception strings to client
- [ ] DEBT-104: Task decomposition AI response parsing is fragile (pipe-delimited text); no error indication when zero tasks are parsed
- [ ] DEBT-105: Dashboard AI grid uses `mb-0` (layout inconsistency — all other sections use `mb-8`)
- [ ] DEBT-106: Rebalance and Energy endpoints don't use AI but live under `/ai/` URL path (misleading)

### Test Coverage Gaps (not blocking, but noted)
- No test for successful task decomposition with mocked AI response
- No test for rebalance with actual overflow conditions (tasks in opportunity_now exceeding threshold)
- No test for proactive analysis "AI not configured" graceful degradation path
- No test for deferred task exclusion in energy recommendations
- No test for per-project AI failure handling in proactive analysis

### Potential Backlog Items
1. **BACKLOG-130 (candidate):** Rebalance threshold should be user-configurable (currently hardcoded to 7)
2. **BACKLOG-131 (candidate):** Proactive analysis needs timeout/progress indication — can take 30+ seconds with N sequential AI calls

---

## 2026-02-12: Session 4 — Warmup Fixes + ROADMAP-007 AI Weekly Review Co-Pilot

### What Went Well
1. **Clean warmup-to-feature pipeline** — 4 fixes verified before ROADMAP-007 started, no regressions introduced
2. **JSON-structured AI prompts** — More reliable than line-by-line text parsing used in earlier AI methods; markdown fence stripping handles inconsistent AI response formatting
3. **Comprehensive testing** — 6 new tests including regression test for BUG-027 fix; 232/232 all passing

### Lessons Learned

#### 1. JSON-Structured AI Prompts Are More Reliable Than Line-by-Line Parsing
**Issue:** Earlier AI endpoints (proactive analysis, task decomposition) used text-based parsing with pipe delimiters and line-by-line scanning. This is fragile when the AI adds extra commentary or changes formatting.
**Fix:** ROADMAP-007 endpoints request JSON output with explicit field names, parse with `json.loads()`, and strip markdown code fences (```` ```json ... ``` ````). Fallback to a generic response on `json.JSONDecodeError`.
**Rule:** For AI service methods that need structured data, always request JSON output and parse it. Include markdown fence stripping (`response.strip().strip('`').strip('json')`) since models often wrap JSON in code fences. Always provide a graceful fallback for parse failures.

#### 2. TS6133 When Changing Mutation Hook Signatures
**Issue:** Updated `useCompleteWeeklyReview` from `mutationFn: () => api.completeWeeklyReview()` to `mutationFn: (params?) => api.completeWeeklyReview(params?.notes, params?.aiSummary)`. Then added `aiSummary` state to WeeklyReviewPage but initially had no code that read it, triggering TS6133 "declared but never read".
**Fix:** Wired up the `useCompleteWeeklyReview` hook with a "Complete Weekly Review" button that passes `aiSummary`.
**Rule:** When adding state that's meant for later use (like storing AI output for persistence), immediately wire it to its consumer in the same step. Don't leave state dangling — TypeScript will flag it as unused.

#### 3. Alembic Migration Chain Must Reference Correct Previous Revision
**Issue:** Migration 014 depends on 013 (`down_revision = "013_add_review_frequency"`). If the chain is broken (wrong revision ID), alembic upgrade will fail with "Can't locate revision".
**Rule:** Always verify `down_revision` matches the actual `revision` string of the previous migration, not just the filename. Check with `alembic history` if unsure.

#### 4. Reuse Existing Service Helpers in New Endpoints
**Issue:** The new `generate_project_review_insight` needed project context (tasks, area, momentum). Rather than writing new queries, it reused `_build_project_context()` from the existing AI service.
**Rule:** Before writing new data-gathering code for AI endpoints, check what helpers already exist in `ai_service.py` and `intelligence_service.py`. Reuse `_build_project_context()`, `get_weekly_review_data()`, `_compute_trend()`, etc.

#### 5. N+1 Queries Sneak In During AI Endpoint Data Gathering
**Issue:** The weekly review summary endpoint loops over each active project and queries `MomentumSnapshot` individually — classic N+1. With 50 projects, that's 50 separate DB queries just for momentum data.
**Fix:** Use a single query with `IN()` filter for all project IDs, then match results in Python.
**Rule:** When building data for AI prompts that span multiple entities, always batch-query. The pattern `for project in projects: db.query(Snapshot).filter(project_id=project.id)` is always wrong — use `db.query(Snapshot).filter(Snapshot.project_id.in_(project_ids))` and group in Python.

#### 6. Mutation Hooks Need onError Callbacks for User-Triggered Actions
**Issue:** `completeReview.mutate()` fires on button click but has no `onError` callback. Unlike queries (which auto-show error state via `isError`), mutations silently fail unless you wire up error handling. The user clicks "Complete" and nothing happens — no success, no error.
**Fix:** Add `onError` callback with toast notification, or use `mutateAsync` with try/catch.
**Rule:** Any mutation triggered by an explicit user action (button click) MUST have either an `onError` callback or be wrapped in `mutateAsync` + try/catch. Pattern: `mutate(data, { onError: (err) => toast.error(...) })`. Queries handle errors automatically; mutations do not.

### Technical Debt Resolved
- [x] BUG-027: Rebalance due_date type check → FIXED (date arithmetic)
- [x] DEBT-094: handleCreateAll parallel mutations → FIXED (async/await loop)
- [x] DEBT-095: Missing error state in 2 AI components → FIXED (AlertCircle UI)
- [x] DEBT-103: Proactive analysis leaks raw exceptions → FIXED (sanitized message)

### Technical Debt Identified
- [ ] DEBT-107: New AI API methods (`getWeeklyReviewAISummary`, `getProjectReviewInsight`) missing `signal?: AbortSignal` — inconsistent with other API methods (`api.ts:875-881`)
- [ ] DEBT-108: `AIReviewSummary` loading spinner missing `aria-label` / `role="status"` for screen readers (`AIReviewSummary.tsx:48`)
- [ ] DEBT-109: `projectInsight.mutate()` can fire multiple times for same project — no deduplication or cancellation (`WeeklyReviewPage.tsx:95`)
- [ ] DEBT-110: `completeReview.mutate()` has no `onError` callback — user won't know if review completion fails (`WeeklyReviewPage.tsx:365`)
- [ ] DEBT-111: N+1 query in `get_weekly_review_ai_summary` — loops per-project for MomentumSnapshot instead of single batch query (`intelligence.py:922-940`)
- [ ] DEBT-112: JSON fence stripping in AI service uses naive string ops — embedded triple-backticks in narrative could break parsing (`ai_service.py:482-502`)
- [ ] DEBT-113: `getWeekKey()` ISO week calculation doesn't match ISO 8601 Thursday rule — may assign wrong week number (`WeeklyReviewPage.tsx:27-30`)
- [ ] DEBT-114: `AIReviewSummary` renders `attention_items` without null check — partial API response could crash component (`AIReviewSummary.tsx:104-107`)

### Potential Backlog Items
1. **BACKLOG-142 (candidate):** localStorage keys should be namespaced by user/session for multi-user scenarios (`weeklyReviewChecklist` key would conflict)

---

## Template for Future Sessions

```markdown
## YYYY-MM-DD: BACKLOG-XXX Description

### What Went Well
-

### Lessons Learned
#### 1. Title
**Issue:**
**Fix:**
**Rule:**

### Technical Debt Identified
- [ ]

### Potential Backlog Items
-
```

---

*Review this file at session start for relevant project patterns.*
