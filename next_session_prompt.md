# Session 15 — Feature Polish + Next Feature

## Skill

Use `/planning-with-files` — Session 15

## Context

v1.1.0 development, Session 14 complete. 299 backend tests (298 pre-existing + 1 new from DEBT-130). TypeScript clean, Vite build passing. All 8 Session 14 items shipped.

**Session 14 shipped:**
- DEBT-125/126/127/128/129/130/131/132 — full debt sweep
- BACKLOG-090 — Data Import from JSON backup (backend + frontend, merge strategy)

**Note on backend tests:** Poetry not available in this workspace shell. Backend tests were not run this session (no Python env). If possible, set up Poetry or a venv before running tests. The test count is estimated at 299 (298 + DEBT-130 test).

## Read First (verified paths)

```
backlog.md                                    # Current debt + feature priorities
progress.md                                   # Session 14 log
lessons_learned.md                            # Friction patterns
backend/app/services/import_service.py        # New: import service (BACKLOG-090)
backend/app/api/export.py                     # Modified: POST /export/import endpoint
frontend/src/pages/Settings.tsx               # Modified: import UI in Data Export section
frontend/src/services/api.ts                  # Modified: importJSON() method
```

## Known Debt (new from S14 audit)

| ID | Description | Location | Priority |
|----|-------------|----------|----------|
| DEBT-133 | `importResult` type is duplicated inline in Settings.tsx and api.ts — extract to shared types file | `Settings.tsx:97-106`, `api.ts:780-800` | XS |
| DEBT-134 | Import error handler shows raw JS Error message to user — should show user-friendly message for JSON parse failures and HTTP errors | `Settings.tsx:handleImportJSON catch block` | S |
| DEBT-135 | `React` default import added to Settings.tsx for `React.ChangeEvent` — could use `import type { ChangeEvent }` from react instead (cleaner) | `Settings.tsx:1` | XS |

## Priority-Ordered Task List

### Warmup (15 min): Quick Debt Sweep

1. **DEBT-135** [XS]: Clean up React import — `import type { ChangeEvent }` instead of default React import
   - AC: No `React.` prefix needed; use `ChangeEvent<HTMLInputElement>` directly
2. **DEBT-133** [XS]: Extract importResult type to shared types or inline the api.ts type
   - AC: Settings.tsx uses `Awaited<ReturnType<typeof api.importJSON>>` or a named type
3. **DEBT-134** [S]: Improve import error UX — parse JSON errors show "Invalid JSON file", HTTP errors show status-appropriate message
   - AC: User sees helpful message, not raw Error.message

### Part A: Choose ONE

**Option A: BACKLOG-087 — Starter Templates by Persona**
- Backend: seed endpoint `POST /api/v1/templates/apply/{persona}` (writer, knowledge-worker, developer)
- Templates define 2-3 areas, 3-5 projects per persona with pre-set priorities/contexts
- Frontend: Templates tab or modal in onboarding/Setup wizard

**Option B: BACKLOG-082 — Session Summary Capture**
- After user marks session complete, capture what changed and store in memory layer
- Backend: `POST /api/v1/memory/session-summary` auto-generates summary from recent activity
- Frontend: "End Session" button in dashboard with summary preview

**Option C: BACKLOG-095 — Collapsible Sections Pattern Extension**
- Weekly Review page: collapse/expand each review section (persist to localStorage)
- ProjectDetail: collapse task sections (Upcoming, In Progress, Done)
- Consistent with Settings page pattern already implemented

### Part B: Release Polish

- Update CHANGELOG.md with v1.1.0-beta features
- Review installer version bump (version_info.txt, conduital.spec)
- End-of-session audit → new DEBT items → Session 16 prompt

## End-of-Session Protocol

1. Backend tests: set up venv first — `python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && pytest tests/ -x -q`
2. TypeScript: `node_modules\.bin\tsc.cmd --noEmit` (from frontend dir, cmd shell)
3. Vite build: `node_modules\.bin\vite.cmd build` (from frontend dir, cmd shell)
4. Update `backlog.md` + `progress.md`
5. Commit with descriptive message (use `-F` flag with temp file to avoid shell escaping issues)
6. Push: `C:\PROGRA~1\Git\bin\git.exe push origin master`
7. Post-session audit → new DEBT items
8. Update `lessons_learned.md`
9. Design Session 16 prompt → save to `next_session_prompt.md`

## Shell Notes (Windows-specific)

- Git: `C:\PROGRA~1\Git\bin\git.exe` (use 8.3 path in cmd shell)
- npm: use `cmd` shell with `cd X && npm ...` pattern
- tsc/vite: `node_modules\.bin\tsc.cmd` / `node_modules\.bin\vite.cmd` (cmd shell)
- npm install: `npm install --include=dev` (not just `npm ci` — gets only 77 pkgs)
- PowerShell `&&` doesn't work — use `;` or separate commands
- git commit with special chars: write message to temp file, use `git commit -F file.txt`
- Poetry not found in PATH — use pip + venv for backend
