# Session 18 — Hotfix Verification + Next Feature

## Skill

Use `/planning-with-files` — Session 18

## Context

v1.1.0 development, Session 17 complete. 321 backend tests, TypeScript clean, Vite build passing.

**Session 17 shipped:**
- DEBT-133/134/135 — type extraction, error UX, React import cleanup
- BACKLOG-095 — Collapsible Sections in WeeklyReviewPage (5 sections) + ProjectDetail (3 task sections)

**Post-Session 17 hotfixes (applied on branch `claude/plan-s17-files-TwzKE`):**
Two bugs were discovered after Session 17 and fixed:

1. **Backend: pydantic-settings JSON parse error** — `WATCH_DIRECTORIES`, `ENABLED_MODULES`, and `CORS_ORIGINS` were typed as `list[str]`, but pydantic-settings v2 tries to JSON-decode env vars for complex types *before* field validators run. Comma-separated values in `.env` (e.g., `WATCH_DIRECTORIES=10_Projects,20_Areas`) caused `JSONDecodeError`. **Fix:** Changed all three fields to `str` type with `@property` accessors (`watch_directories`, `enabled_modules`, `cors_origins`) that parse comma-separated values. Updated all callers (4 files).

2. **Frontend: React hooks violation in ProjectDetail.tsx** — The `useMemo` for `filteredTasks` was called after conditional early returns for error/not-found states, violating React's Rules of Hooks. Caused "Rendered fewer hooks than expected" crash. **Fix:** Moved early returns below all hook calls.

**These hotfixes must be merged to master before starting Session 18 work.**

## Pre-Session Checklist

1. Merge hotfix branch `claude/plan-s17-files-TwzKE` to master (or verify already merged)
2. Run backend tests: `pytest tests/ -x -q` — expect 321 passing
3. Run TypeScript check: `tsc --noEmit` — expect 0 errors
4. Run Vite build: `vite build` — expect clean build
5. Update `backlog.md` stats block (backend tests: 321, last updated S18)

## Read First (verified paths)

```
backlog.md                                    # Current priorities — BACKLOG-087 and BACKLOG-082 still open
tasks/progress.md                             # Session 17 log + all prior history
tasks/lessons.md                              # Friction patterns — review at session start
backend/app/core/config.py                    # Hotfix: str fields + @property for list settings
frontend/src/pages/ProjectDetail.tsx          # Hotfix: hooks ordering fix
```

## Known Debt (new from S17 hotfix audit)

| ID | Description | Location | Priority |
|----|-------------|----------|----------|
| DEBT-136 | `AREA_PREFIX_MAP: dict[str, str]` has the same pydantic-settings JSON parsing vulnerability as the fixed list fields — will fail if set as non-JSON in `.env` | `config.py:197` | S |
| DEBT-137 | Lessons from hooks violation: add ESLint rule `react-hooks/exhaustive-deps` and `react-hooks/rules-of-hooks` if not already configured | `frontend/.eslintrc` or `eslint.config` | XS |

## Priority-Ordered Task List

### Warmup (15 min): Hotfix Follow-Up

1. **DEBT-136** [S]: Fix `AREA_PREFIX_MAP` parsing — same pattern as WATCH_DIRECTORIES fix. Change to `str` with property, or add a note that this field must use JSON format in `.env`.
   - AC: `AREA_PREFIX_MAP` does not crash on non-JSON `.env` values, OR is documented as requiring JSON
2. **DEBT-137** [XS]: Verify ESLint hooks rules are configured — `react-hooks/rules-of-hooks` (error) and `react-hooks/exhaustive-deps` (warn)
   - AC: Linter catches hooks-after-early-return pattern
3. **Backlog stats update**: Update `backlog.md` Stats section — backend tests to 321, last updated S18

### Part A: Choose ONE Feature

**Option A: BACKLOG-087 — Starter Templates by Persona** (Recommended)
- Backend: seed endpoint `POST /api/v1/templates/apply/{persona}` (writer, knowledge-worker, developer)
- Templates define 2-3 areas + 3-5 projects per persona with pre-set priorities/contexts
- Frontend: Templates tab or modal in onboarding/Setup wizard or Settings page
- Scope: ~2 hours for backend + frontend + tests

**Option B: BACKLOG-082 — Session Summary Capture**
- After user marks session complete, capture what changed and store in memory layer
- Backend: `POST /api/v1/memory/session-summary` auto-generates summary from recent activity
- Frontend: "End Session" button in dashboard with summary preview
- Scope: ~2 hours, depends on memory layer module being enabled

### Part B: Release Polish

- Review and update `tasks/progress.md` with Session 18 log
- End-of-session audit — new DEBT items
- Design Session 19 prompt → save to `next_session_prompt.md`

## End-of-Session Protocol

1. Backend tests: `pytest tests/ -x -q` (from backend dir)
2. TypeScript: `tsc --noEmit` (from frontend dir)
3. Vite build: `vite build` (from frontend dir)
4. Update `backlog.md` + `tasks/progress.md`
5. Commit with descriptive message (use `-F` flag with temp file to avoid shell escaping issues)
6. Push: `git push origin master`
7. Post-session audit → new DEBT items
8. Update `tasks/lessons.md` if new patterns discovered
9. Design Session 19 prompt → save to `next_session_prompt.md`

## Shell Notes (Windows-specific)

- Git: `C:\PROGRA~1\Git\bin\git.exe` (use 8.3 path in cmd shell)
- npm: use `cmd` shell with `cd X && npm ...` pattern
- tsc/vite: `node_modules\.bin\tsc.cmd` / `node_modules\.bin\vite.cmd` (cmd shell)
- npm install: `npm install --include=dev` (not just `npm ci` — gets only 77 pkgs)
- PowerShell `&&` doesn't work — use `;` or separate commands
- git commit with special chars: write message to temp file, use `git commit -F file.txt`
- Poetry not found in PATH — use pip + venv for backend
