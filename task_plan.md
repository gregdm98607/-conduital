# Task Plan — Batch 5: R3 Should Have + Tech Debt (2026-02-07)

## Goal
Implement 5 backlog items: 2 R3 Should Have features + 3 medium-priority tech debt items.

## Selected Items

| # | ID | Description | Impact |
|---|-----|-------------|--------|
| 1 | BACKLOG-072 | **Unstuck Task Button** — AI helps stalled projects | R3 Should Have feature |
| 2 | BACKLOG-084 | **Cross-Memory Search/Query** — Find relevant context | R3 Should Have feature |
| 3 | DEBT-042/043 | **_persist_to_env safety** — Race condition + sanitization | Security/reliability |
| 4 | BACKLOG-094 | **Whitespace-Only Content Validation** — Backend validators | Data quality |
| 5 | BACKLOG-109 | **CORS Origins from Environment Variable** — Configurable origins | DevOps flexibility |

---

## Phase 1: BACKLOG-072 — Unstuck Task Button `complete`
- Added `useCreateUnstuckTask` import + Zap icon to ProjectDetail.tsx
- "Get Unstuck" button appears when `project.stalled_since` is set
- Wired to existing POST /intelligence/unstuck/{project_id} endpoint (useAI: false)
- Loading state (animate-pulse), toast success/error notifications

## Phase 2: BACKLOG-084 — Cross-Memory Search/Query `complete`
- Added `MemoryService.search_objects()` — searches object_id, namespace, tags, content via ILIKE
- Added `GET /memory/objects/search?q=&namespace=&limit=` endpoint in routes.py
- Added `useSearchMemoryObjects(query, namespace)` hook in useMemory.ts (enabled at 2+ chars)
- MemoryPage.tsx uses server-side search for 2+ char queries, client-side for shorter

## Phase 3: DEBT-042/043 — _persist_to_env Safety `complete`
- Added `threading.Lock` (`_env_write_lock`) protecting read-modify-write cycle
- Added `_sanitize_env_value()` — strips newlines/CR, quotes values with spaces/special chars
- All values pass through sanitization before writing to .env

## Phase 4: BACKLOG-094 — Whitespace-Only Content Validation `complete`
- Added `strip_whitespace()` helper to `schemas/common.py`
- Applied `@field_validator(..., mode="before")` to:
  - InboxItemBase.content, InboxItemUpdate.content, InboxItemProcess.title
  - TaskBase.title, TaskUpdate.title
  - ProjectBase.title, ProjectUpdate.title
  - AreaBase.title, AreaUpdate.title
- Whitespace-only strings now stripped to "" which fails min_length=1

## Phase 5: BACKLOG-109 — CORS Origins from Environment Variable `complete`
- Added `@field_validator("CORS_ORIGINS", mode="before")` to Settings class
- Parses comma-separated strings: `http://localhost:3000,http://localhost:5173`
- Also handles JSON arrays: `["http://localhost:3000"]`
- Falls through to pydantic-settings default for list values
- Updated .env.example with format documentation

## Phase 6: Verification `complete`
- TypeScript: clean (0 errors)
- Vite build: clean (570KB bundle)
- Python syntax: all 9 modified files compile OK
- backlog.md: 6 items marked Done + added to completed items table
- progress.md: Batch 5 session logged

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none) | | |
