# Session 14 — Phase 2B Data Feature + Debt Sweep

## Skill

Use `/planning-with-files` — Session 14

## Context

v1.1.0 development, Session 13 complete. 298 backend tests, all passing. AI E2E validation done. 8 new DEBT items logged from Session 13 audit. Bi-directional API with Board of Advisors added as ROADMAP-011 (needs design).

## Read First (verified paths)

```
backlog.md                                    # Current debt + feature priorities
progress.md                                   # Session 13 log
lessons_learned.md                            # Friction patterns from S13
frontend/src/utils/aiErrors.ts                # New shared AI error utility
frontend/src/utils/sort.ts                    # New shared sort utility
backend/app/api/intelligence.py               # Decompose-tasks error handling (DEBT-130)
frontend/src/components/tasks/TaskListView.tsx # DEBT-125/126 dark mode gaps
frontend/src/components/intelligence/AIDashboardSuggestions.tsx # DEBT-128 inconsistency
```

## Priority-Ordered Task List

### Warmup (15 min): Quick Debt Sweep — 5 XS/S items

1. **DEBT-125** [S]: Add `dark:` variants to due date status colors in `TaskListView.tsx:205-208`
   - AC: `text-red-600 dark:text-red-400`, `text-yellow-600 dark:text-yellow-400`, `text-gray-600 dark:text-gray-300`
2. **DEBT-126** [XS]: Fix gray contrast — already addressed by DEBT-125 fix
3. **DEBT-128** [XS]: Refactor `AIDashboardSuggestions.tsx:50-54` to use `getAIErrorMessage()` instead of manual status check
   - AC: Component uses same pattern as other 5 AI components
4. **DEBT-129** [XS]: Add input validation to `parseSortOption()` in `utils/sort.ts`
   - AC: Returns sensible default if input is empty or missing delimiter
5. **DEBT-132** [XS]: Test `ring-offset-1` in browser; if visual overflow, change to `ring-offset-0`

### Part A (2-3h): DEBT-130 Backend Error Sanitization + DEBT-127 AI Error Expansion

6. **DEBT-130** [M]: Sanitize generic exception in decompose-tasks (`intelligence.py:1319-1321`)
   - AC: `detail` never contains raw `str(e)`, add test for it
7. **DEBT-127** [S]: Expand `aiErrors.ts` to handle 429, 502, 503, 504 status codes
   - AC: Rate-limited shows "AI service is busy, please try again shortly", gateway errors show distinct message
8. **DEBT-131** [S]: Verify soft-delete filters in rebalance/energy subqueries
   - AC: All task/project queries in intelligence.py rebalance + energy endpoints include `deleted_at.is_(None)`

### Part B (2-3h): Pick ONE Data Feature

Option 1: **BACKLOG-090** — Data Import from JSON Backup
- Backend: `POST /api/v1/data/import` endpoint accepting JSON export format
- Frontend: Import button in Settings page with file picker, progress indicator
- Tests: round-trip export→import, conflict handling, validation

Option 2: **BACKLOG-087** — Starter Templates by Persona
- Backend: Template model + seeding endpoint
- Frontend: Template picker in "New Project" flow
- Personas: Writer, Knowledge Worker, Student, Home/Family

### End-of-Session Protocol

1. Run tests: target 300+ (`cd /c/Dev/project-tracker/backend && poetry run python -m pytest tests/ -x -q`)
2. TS check: `cd /c/Dev/project-tracker/frontend && npx tsc --noEmit`
3. Vite build: `cd /c/Dev/project-tracker/frontend && npx vite build`
4. Update `backlog.md`, `progress.md`, `MEMORY.md`
5. Commit with descriptive message
6. Push to GitHub: `git push`
7. Post-session audit: scan for new bugs/debt
8. Update `lessons_learned.md` with friction patterns
9. Design Session 15 prompt → save to `next_session_prompt.md`

## KNOWN PITFALLS

### From lessons_learned.md (Session 13)

1. **AI-disabled tests fail on dev machine**: Local `.env` has `AI_FEATURES_ENABLED=True`. Always patch explicitly:
   ```python
   with patch("app.core.config.settings.AI_FEATURES_ENABLED", False):
   ```

2. **Rebalance/Energy are NOT AI-gated**: Don't test these for AI-disabled behavior — they return 200 regardless.

3. **Schema mismatches**: Always read the Pydantic response model before writing test assertions. Don't guess from endpoint names.

4. **Chrome extension disconnects**: Call `tabs_context_mcp` to reconnect during browser testing.

5. **AITaskDecomposition location**: Inside "Natural Planning Model" collapsible section — only renders if project has brainstorm/organizing notes.

### General Codebase Pitfalls

6. **SQLite strips timezone**: Use `ensure_tz_aware()` before datetime arithmetic with model fields.
7. **Soft delete**: ALL list queries need `.where(Model.deleted_at.is_(None))`. `db.get()` bypasses filters — check `deleted_at` manually.
8. **Axios errors**: Use `(err as any)?.response?.status` (number), NOT `err.message.includes('400')`.
9. **replaceAll unavailable**: Use `.replace(/pattern/g, '')` with regex global flag.
10. **Poetry version normalization**: `1.1.0-beta` → `1.1.0b0` (PEP 440).

## Fallback Instructions

- **If tests fail after warmup edits**: Run `npx tsc --noEmit` first to catch type errors before pytest
- **If Chrome extension won't reconnect**: Skip browser testing, verify via curl + code review instead
- **If git push hangs**: Check credential helper with `git config credential.helper`, try `git push --verbose`
- **If poetry install fails**: Check for locked .pyd files — close all Python processes first, then `poetry lock && poetry install`
- **If vite build has warnings**: Check for unused imports with `npx tsc --noEmit` first — build warnings are usually from TS issues

## What NOT to Do

- Don't refactor beyond the targeted DEBT items — stay focused
- Don't add new AI endpoints — AI surface is complete
- Don't update dependencies (done in Session 10)
- Don't touch the heatmap (done in Sessions 11-12)
- Don't modify existing test structure — only add new tests
