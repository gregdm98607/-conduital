# Session 31 — R2 Kickoff (GTD Inbox) + Polish

## Context

Session 30 cleared the pre-beta gate and closed both remaining "address by R2" debt items:

**Session 30 shipped:**
- **VM testing complete** — `ConduitalSetup-1.2.0.exe` passed all 9 test sections on clean Win10 + Win11 VMs. Uploaded to Gumroad and download validated. Results recorded in [`tasks/vm-test-plan.md`](tasks/vm-test-plan.md).
- **DEBT-015** (Overlapping setup docs) — Root README is now the canonical setup doc; backend/README.md reduced to reference-only. Deleted obsolete `frontend/SETUP_AND_TEST.md`, `INSTALL_TOAST.md`, `DEBUG_STEPS.md`, `QUICK_FIX.md`, `PHASE_5_FRONTEND_COMPLETE.md`.
- **DEBT-016** (WebSocket integration) — `/ws/discovery-status` endpoint with `DiscoveryBroadcaster` (asyncio.Queue pub/sub, thread-safe via `call_soon_threadsafe`). Frontend `useDiscoveryWebSocket` hook pushes events into TanStack Query cache; polling in `useDiscoveryStatus` now acts as a fallback. 7 new tests added.

Backend tests: **461 passing** (was 454). Frontend: Vite build clean.

**Remaining debt (none address-by-R2):** DEBT-078 (test runner requires explicit venv python) — low priority, only matters for new contributors.

## Read First

```
backlog.md                                               # R2 items start at line 26
backend/MODULE_SYSTEM.md                                 # Module architecture (gtd_inbox is a module)
backend/app/modules/                                     # Registered modules live here
backend/app/api/inbox.py                                 # Existing inbox endpoints
frontend/src/pages/                                      # Inbox page location TBD
```

## Priority-Ordered Task List

### Phase 1: R2 Planning — GTD Inbox Module

R1.1 Beta is shipped. R2 (Conduital GTD) adds the `gtd_inbox` module. Inbox items already exist in the DB; the R2 work is about surfacing them as a first-class GTD workflow.

Before implementing, draft a short design note covering:
1. GTD capture → clarify → organize → engage workflow (what's in scope for R2 vs later)
2. What the `gtd_inbox` module enables that's gated today
3. UI surface: dedicated Inbox page, quick-capture shortcut, processing modal
4. Metrics: zero-inbox tracker, items-per-week, capture-to-clarify latency

### Phase 2: R2 Implementation (scope TBD from Phase 1)

Likely work:
- `frontend/src/pages/Inbox.tsx` — capture + process queue
- `backend/app/modules/gtd_inbox/` — dedicated module (may already be scaffolded; verify)
- Keyboard shortcut for quick capture (e.g. `Ctrl+Shift+I`)
- Cross-link from inbox item → promote to project/task/reference

### Phase 3: Polish (if time)

- **Config/registry preset alignment**: `config.py` COMMERCIAL_PRESETS and `registry.py` COMMERCIAL_PRESETS disagree on what "basic" includes. Now that default is "full" this is cosmetic, but worth aligning before any user picks `basic` explicitly.
- **BACKLOG-087**: Starter Templates by Persona (Writer, Knowledge Worker, etc.) — R3 item but template infrastructure helps R2 onboarding.
- **BACKLOG-153**: File Sync UX design — sync happens invisibly; users want a status indicator.

### Phase 4: Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && npm run build`
3. Update `backlog.md`
4. Commit + push
5. **Write Session 32 prompt → `next-prompt.md`**

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- npm/vite: use `cmd` shell with `cd X && npm ...` pattern
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`

## Debt Watch

- **DEBT-078** — `backend\venv\Scripts\python.exe` required (no `pytest` on PATH). Low-priority but annoying for new devs. Consider a `Makefile` or `pyproject.toml` script entry.
