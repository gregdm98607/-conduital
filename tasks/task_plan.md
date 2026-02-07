# Backlog Items Batch — R3 Must-Haves + Tech Debt (2026-02-06)

**Goal:** Implement 5 items: 2 R3 Must-Have features + 1 R3 Nice-to-Have + 2 Tech Debt fixes
**Status:** In Progress

---

## Selected Items

| # | ID | Description | Release | Category |
|---|-----|-------------|---------|----------|
| 1 | BACKLOG-096 | Persist AI Key via Settings Page | R3 Must | Backend + Frontend |
| 2 | BACKLOG-081 | Context Export for AI Sessions | R3 Must | Backend + Frontend |
| 3 | BACKLOG-097 | Collapsible Settings Sections | R3 Nice | Frontend |
| 4 | DEBT-030 | MemoryPage setState in render body fix | Tech Debt | Frontend |
| 5 | DEBT-031 | MemoryPage missing error state handling | Tech Debt | Frontend |

---

## Phase 1: BACKLOG-096 — Persist AI Key via Settings Page [status: pending]

Currently, API key is only stored at runtime in memory. PUT to /ai updates the Settings object but reverts on restart. Need to persist to a .md file in Second Brain (safe backup) and to .env for server restarts.

### Backend Changes:
- [ ] Add `persist_ai_settings()` function to settings.py that writes key to `.env`
- [ ] On PUT /ai, call persist function to save to .env file
- [ ] Add endpoint to save AI config backup to Second Brain as markdown
- [ ] Remove hardcoded ANTHROPIC_API_KEY from .env default template

### Frontend Changes:
- [ ] Add "saved" indicator after successful persist
- [ ] Show whether key is from .env or was set via UI
- [ ] Add backup-to-markdown button (optional)

### Files to Modify:
- `backend/app/api/settings.py`
- `backend/app/core/config.py`
- `frontend/src/pages/Settings.tsx`

---

## Phase 2: BACKLOG-081 — Context Export for AI Sessions [status: pending]

One-click export of current project/task context for pasting into AI chat sessions. Should collect key information and format it as a structured prompt context.

### Backend Changes:
- [ ] Add GET /api/v1/ai/context-export endpoint
- [ ] Collect: active projects (with momentum), stalled projects, upcoming tasks, areas with health
- [ ] Format as structured markdown suitable for AI prompt context
- [ ] Support optional filters (project_id, area_id)

### Frontend Changes:
- [ ] Add "Export Context" button to relevant pages (Dashboard, ProjectDetail)
- [ ] Modal showing formatted context with "Copy to Clipboard" button
- [ ] Quick-copy toast confirmation

### Files to Modify:
- `backend/app/api/settings.py` or new `context.py` router
- `backend/app/services/intelligence_service.py` (data gathering)
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/ProjectDetail.tsx`
- `frontend/src/components/` (new ContextExportModal)

---

## Phase 3: BACKLOG-097 — Collapsible Settings Sections [status: pending]

Settings page has 6 sections that are always expanded. Add collapse/expand with localStorage persistence.

### Frontend Changes:
- [ ] Wrap each settings section in a CollapsibleSection component
- [ ] Chevron toggle indicator (up/down)
- [ ] localStorage persistence for expanded/collapsed state
- [ ] Default: all expanded

### Files to Modify:
- `frontend/src/pages/Settings.tsx`

---

## Phase 4: DEBT-030 — MemoryPage setState in render body [status: pending]

EditObjectModal in MemoryPage.tsx initializes form state with setState in render body (line 390). Move to useEffect.

### Fix:
- [ ] Move initialization block (lines 390-396) into a `useEffect` with `obj` as dependency
- [ ] Remove the `initialized` flag pattern
- [ ] Test that form populates correctly when editing existing objects

### Files to Modify:
- `frontend/src/pages/MemoryPage.tsx`

---

## Phase 5: DEBT-031 — MemoryPage missing error state handling [status: pending]

useMemoryObjects and useMemoryNamespaces queries don't destructure isError/error. No error UI shown when API fails.

### Fix:
- [ ] Destructure `isError` and `error` from both query hooks
- [ ] Add error banner UI when either query fails
- [ ] Show retry option

### Files to Modify:
- `frontend/src/pages/MemoryPage.tsx`

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|

---

*Created: 2026-02-06*
