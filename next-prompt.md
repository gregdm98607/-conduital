# Session 23 — Version Bump, DEBT-138, Clean VM Testing Prep

## Skill

Use `/planning-with-files` — Session 23

## Context

Session 22 completed the MemoryPage.tsx decomposition (DEBT-139 fully done) and DEBT-140 (energy level constant). MemoryPage.tsx is now a 75-line thin shell with ObjectsView, modals, HealthView, PrefetchView, SessionsView all in `pages/memory/`. Pre-release checklist review identified version mismatch (DEBT-142) and several distribution gaps. Backend tests pass (327), frontend builds clean.

**Session 22 shipped:**
- DEBT-139 complete: ObjectsView.tsx (~320 lines), components/modals.tsx (~430 lines) extracted; MemoryPage.tsx → 75 lines
- DEBT-140: `ENERGY_LEVELS` constant in shared.tsx, used by SessionsView + EnergyDots
- Pre-release checklist review: identified version mismatch, missing icon, no VM testing
- Logged DEBT-142 (version string mismatch)

**Open debt (small):** DEBT-138 (stats query consolidation), DEBT-142 (version bump to 1.2.0)

## Read First (verified paths)

```
backlog.md                                               # Updated S22 — DEBT-139/140 done, DEBT-142 logged
distribution-checklist.md                                # Full pre-release checklist (reviewed S22)
frontend/src/pages/MemoryPage.tsx                        # 75 lines — thin shell (verified S22)
frontend/src/pages/memory/ObjectsView.tsx                # ~320 lines — new S22
frontend/src/pages/memory/components/modals.tsx          # ~430 lines — new S22
backend/app/modules/memory_layer/routes.py               # DEBT-138 target: get_memory_stats
backend/pyproject.toml                                   # Version: 1.1.0-beta (needs bump)
frontend/package.json                                    # Version: 1.1.0-beta (needs bump)
installer/conduital.iss                                  # Version: 1.1.0-beta (needs bump)
```

## Priority-Ordered Task List

### Phase 1: Version Bump (DEBT-142) (~10 min)

Bump all version strings from `1.1.0-beta` to `1.2.0`:
1. `backend/pyproject.toml` — version field
2. `frontend/package.json` — version field
3. `installer/conduital.iss` — `#define MyAppVersion`
4. Verify backend config reads from pyproject.toml correctly
5. Run tests to confirm nothing breaks

### Phase 2: DEBT-138 — Consolidate get_memory_stats Queries (~30 min)

The `/memory/stats` endpoint runs 6+ separate DB queries. Consolidate into fewer round-trips:
- Review `memory_layer/routes.py` lines 36-152
- Identify queries that can be combined (e.g., object counts by status, storage type, priority band)
- Use SQLAlchemy `func.count`, `case()`, or subqueries to batch
- Maintain identical response shape
- Backend tests must still pass

### Phase 3: Clean VM Testing Preparation (~30 min)

1. Build the frontend: `cd frontend && npm run build`
2. Build the exe: `cd backend && build.bat`
3. Build the installer: compile `installer/conduital.iss` with Inno Setup
4. Document exact steps for clean VM testing in a `tasks/vm-test-plan.md`:
   - What to test (install, first-run setup, all pages, AI degradation, uninstall)
   - Expected results for each test
   - How to capture and report issues

### Phase 4: Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && npm run build`
3. Update `backlog.md` — mark completed items, log new debt
4. Commit with descriptive message
5. Push to origin
6. **Write Session 24 prompt → `next-prompt.md`** (do not skip this step)

## End-of-Session Protocol

1. Backend tests pass
2. TypeScript clean (`npx tsc --noEmit`)
3. Vite build clean
4. Update `backlog.md`
5. Commit + push
6. Post-session audit → new DEBT items
7. **Design next session prompt → `next-prompt.md`**

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- npm/vite: use `cmd` shell with `cd X && npm ...` pattern
- git commit with special chars: write message to temp file, use `git commit -F file.txt`
