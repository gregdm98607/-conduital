# Session 34 — File Sync UX Phase 2 (conflict resolution + Settings activity)

## Context

Session 33 (2026-05-04) shipped **v1.3.4** with R6 Phase 1 (BACKLOG-153 file
sync UX) in one feat commit + one closeout commit:

- **Backend** — new [`backend/app/services/sync_broadcast.py`](backend/app/services/sync_broadcast.py)
  mirroring `discovery_broadcast.py` pattern (in-memory ring buffer + asyncio
  pub/sub + thread-safe `record_sync_event`). [`backend/app/sync/sync_engine.py`](backend/app/sync/sync_engine.py)
  now publishes events at: `scan_started`, `scan_completed`, `file_synced`,
  `project_synced`, `conflict_detected`, `sync_error`. New WebSocket
  `/ws/sync-status` in [`backend/app/main.py`](backend/app/main.py) (snapshot +
  per-event push) and HTTP fallback `GET /api/v1/sync/events` in
  [`backend/app/api/sync.py`](backend/app/api/sync.py). 6 new tests in
  [`backend/tests/test_sync_broadcast.py`](backend/tests/test_sync_broadcast.py).
- **Frontend** — [`frontend/src/hooks/useSyncStatus.ts`](frontend/src/hooks/useSyncStatus.ts)
  wraps the WS with reconnect + HTTP fallback (30s tick), derives
  `'idle' | 'syncing' | 'error' | 'conflict'`. [`frontend/src/components/sync/SyncIndicator.tsx`](frontend/src/components/sync/SyncIndicator.tsx)
  replaces the static "File Sync" footer in
  [`frontend/src/components/layout/Layout.tsx`](frontend/src/components/layout/Layout.tsx)
  with a live indicator ("Synced 2m ago"). [`frontend/src/components/sync/SyncDetailsPanel.tsx`](frontend/src/components/sync/SyncDetailsPanel.tsx)
  is the modal — recent events list + manual "Sync now" button.

**Build / test status (post-S33):**
- ✅ `npm run build` clean (~3.3s).
- ✅ `pytest backend/tests/` 498 passed, 1 skipped (was 492 → +6 new).
- ✅ Versions bumped: `pyproject.toml` / `package.json` / `installer/conduital.iss` → `1.3.4`.

## Phase 2 — What's left for BACKLOG-153

Phase 1 made sync visible. Phase 2 closes the loop on conflicts and gives a
denser view in Settings.

### 1. Conflict-resolution UI (~half day)

The backend already supports `conflict_strategy: prompt` and exposes
`GET /api/v1/sync/conflicts` + `POST /api/v1/sync/resolve/{sync_id}`. What's
missing is a frontend that surfaces them:

1. Extend `useSyncStatus` (or create a sibling `useSyncConflicts`) to poll
   `/sync/conflicts` whenever `status === 'conflict'` or after a
   `conflict_detected` event arrives over the WS.
2. Wire a "Conflicts (N)" tab into [`SyncDetailsPanel`](frontend/src/components/sync/SyncDetailsPanel.tsx)
   listing each conflict (file path, last-synced timestamp) with two buttons:
   "Use file version" / "Use database version". Each hits
   `POST /api/v1/sync/resolve/{sync_id}?use_file=true|false`.
3. Toast on success; refresh both the conflicts query and the events stream.
4. When no conflicts exist, hide the tab to keep the modal minimal.

### 2. Settings → Sync recent-activity subsection (~1-2 hours)

Right now [`frontend/src/pages/Settings.tsx`](frontend/src/pages/Settings.tsx)
has a Sync section but no live activity view (the modal in the sidebar is
ephemeral). Mirror the Discovery Activity panel pattern:

1. Add a "Recent Sync Activity" subsection under the existing Sync settings.
2. Reuse `useSyncStatus` and render the last 10 events using the same icon +
   label helpers from `SyncDetailsPanel` (consider extracting `eventIcon` /
   `actionLabel` into `frontend/src/components/sync/SyncEventList.tsx` so both
   places share the renderer).
3. Show `lastSyncedAt` prominently at the top of the section.

### 3. Polish (~30 min)

- Bundle is now 803 kB / 200 kB gzip — consider lazy-loading
  `SyncDetailsPanel` (only mounted when the modal opens). Optional, cheap.
- Add a small TS test covering the `relativeTime` / `deriveStatus` helpers in
  `useSyncStatus.ts`.

## Always-On Cleanup

1. **DEBT-078** — `pytest` not on PATH. Add a `[tool.poetry.scripts]` entry to
   `backend/pyproject.toml` so `poetry run test` works without the
   `backend\venv\Scripts\python.exe -m pytest` incantation. ~10 min.
2. **BACKLOG-161 (download URL)** — distribution blocker; needs DNS + hosting
   decision. Worth raising with Greg again if v1.4 release is in sight.

## Phase 4 — Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q` (target: 498+ pass).
2. Frontend build: `cd frontend && cmd //c "npm run build"`.
3. Update [`backlog.md`](backlog.md) — mark BACKLOG-153 fully done if Phase 2
   ships, update Stats, bump test count.
4. Bump version `1.3.4 → 1.3.5` (or `1.4.0` if BACKLOG-153 closes and warrants
   a minor).
5. Commit + push (one commit per chunk: conflict UI, Settings panel,
   closeout).
6. **Write Session 35 prompt → `next-prompt.md`** (per CLAUDE.md MEMORY rule).

## Read First

```
backend/app/services/sync_broadcast.py                  # S33 sync event broadcaster
backend/app/sync/sync_engine.py                         # SyncEngine publish points
backend/app/api/sync.py                                 # /sync/conflicts + /sync/resolve already exist
frontend/src/hooks/useSyncStatus.ts                     # Hook to extend or sibling hook off
frontend/src/components/sync/SyncDetailsPanel.tsx       # Add Conflicts tab here
frontend/src/components/sync/SyncIndicator.tsx          # Sidebar indicator (no changes expected)
frontend/src/pages/Settings.tsx                         # Add Recent Sync Activity subsection
```

## Strategic Notes (PO context)

- **Why Phase 2 next, not a different R6 candidate:** Phase 1 only delivers
  half of the user value. Without conflict resolution, a user who lands on
  `conflict_detected` is stuck — they can see it happened but can't fix it
  from the UI. Phase 2 finishes the user story.
- **Why surface Settings → Sync activity:** the sidebar indicator is great
  for at-a-glance, but power users want a longer history. The Discovery
  Activity panel is the precedent and is well-loved.
- **WS reconnect under load:** Phase 1's WS uses exponential backoff up to
  30s. If the backend restarts during a long scan, the frontend will
  reconnect but may miss the `scan_completed` event. The HTTP fallback
  fetches `/sync/events` every 30s, so worst-case the indicator is 30s
  stale — acceptable but worth verifying once Phase 2 is in.
- **Phase 1 introduced no new debt.** `sync_broadcast` is a clean copy of
  `discovery_broadcast`; if we ever genericize the pattern it's a 3-line
  refactor.

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- Single test file: `backend\venv\Scripts\python.exe -m pytest backend/tests/test_sync_broadcast.py -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- Alembic upgrade: `backend\venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`

## Debt Watch

- **DEBT-078** — `backend\venv\Scripts\python.exe` required (no `pytest` on PATH). Quick win for S34.
- No new debt introduced in S33.
