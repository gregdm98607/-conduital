# Progress Log

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
