# Session 35 — R7 selection (post-v1.4.0)

## Context

Session 34 (2026-05-04) shipped **v1.4.0**, closing R6 / BACKLOG-153 in two
commits:

- `feat(BACKLOG-153)` Phase 2 file sync UX:
  - **Backend** — [`backend/app/api/sync.py`](backend/app/api/sync.py)
    `/sync/conflicts` now returns `id` + `error_message` so the frontend can
    drive `POST /sync/resolve/{sync_id}`.
  - **Frontend** — new [`useSyncConflicts`](frontend/src/hooks/useSyncConflicts.ts)
    hook polls `/sync/conflicts` (30s) with optimistic removal; new
    [`SyncEventList`](frontend/src/components/sync/SyncEventList.tsx) shared
    renderer (eventIcon / actionLabel / shortPath); a Conflicts tab in
    [`SyncDetailsPanel`](frontend/src/components/sync/SyncDetailsPanel.tsx)
    with "Use file" / "Use database" actions; Settings → File Sync grew a
    Recent Sync Activity subsection mirroring the Discovery Activity panel
    pattern; `relativeTime` + `deriveStatus` exported from
    [`useSyncStatus`](frontend/src/hooks/useSyncStatus.ts).
- `chore(S34)` v1.4.0 closeout — version bumps + backlog refresh + this prompt.

**Build / test status (post-S34):**
- ✅ `npm run build` clean (~3.5s, 808 kB / 202 kB gzip).
- ✅ `pytest backend/tests/` 498 passed, 1 skipped (no new tests added — Phase
  2 was frontend-heavy; the small TS test for `relativeTime` / `deriveStatus`
  noted in the S34 prompt was skipped because no JS test runner is installed).
- ✅ Versions bumped: `pyproject.toml` / `package.json` /
  `installer/conduital.iss` → `1.4.0`.

## Pick R7

R6 is done. We have a clean monetization story (R5 done in S31-S32) and a
clean file-sync UX (R6 done in S33-S34). The next swing should be high-value
and well-scoped. Candidates:

### Recommended: **BACKLOG-159 — Paid-tier post-activation flow** (~half day)

This was the **deferred R6 candidate B**. After a user activates a license
(Stripe inline or Gumroad), today they get a bare "License accepted" toast
and the Settings page silently flips state. Plan:

1. Detect a successful activation transition (free → paid) in the license
   hook, fire a one-time celebratory state.
2. Show a modal listing what just unlocked (modules, features) — read from
   `is_module_allowed_for_tier()` so it stays accurate.
3. Link to a quick feature tour OR persist a "What's new" badge on relevant
   sidebar links for one session.
4. Add a `welcome_paid_tier` PostHog event so we can measure activation→TTV.

**Why this:** finishes the monetization story (we instrumented the funnel in
MON-009 but the post-purchase moment is bare). Small surface area. No backend
changes.

### Alternative: **BACKLOG-160 — Sidebar license badge** (~2-3 hours)

Small tier badge ("Free Trial · 9d", "GTD", "Full") next to the SyncIndicator
in the sidebar footer. Click → Settings → License. Useful for users on long
trials who keep losing track of remaining days.

### Alternative: **BACKLOG-087 — Starter Templates by Persona** (~half day)

Deferred R6 candidate C. Pre-baked project templates (Writer, Knowledge
Worker, Engineer, etc.) that drop in 5-10 starter projects + areas. Big
onboarding win for new installs. Higher uncertainty on UX surface (do we add
an onboarding wizard or just a "Load template" button?).

### Cleanup (always-on, regardless of R7 pick)

1. **DEBT-078** — `pytest` not on PATH. Add a `[tool.poetry.scripts]` entry
   to `backend/pyproject.toml` so `poetry run test` works without the
   `backend\venv\Scripts\python.exe -m pytest` incantation. ~10 min. Worth
   knocking out at the top of S35.
2. **BACKLOG-161** — distribution blocker (download URL); needs DNS + hosting
   decision. Worth raising with Greg again if v1.4 release/announcement is
   imminent.
3. **Frontend lint backlog** — 18 errors / 16 warnings still in
   `frontend/src/pages/{Contexts,Goals,Visions,InboxPage,ProjectDetail,Projects,SomedayMaybe}.tsx`
   and `pages/memory/`. None block build (`tsc && vite build` is clean). A
   `npm run lint -- --fix` pass + manual fix for the conditional-hook errors
   is ~1 hour. Could be a side-quest if R7 work is light.

## Phase 4 — Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q` (target: 498+ pass).
2. Frontend build: `cd frontend && cmd //c "npm run build"`.
3. Update [`backlog.md`](backlog.md) — mark R7 selection's items done, update
   Stats, bump test count if applicable.
4. Bump version `1.4.0 → 1.4.1` (patch) or `1.5.0` (minor) depending on R7
   scope.
5. Commit + push (one feat commit per chunk; one closeout commit at the end).
6. **Write Session 36 prompt → `next-prompt.md`** (per CLAUDE.md MEMORY rule).

## Read First (regardless of R7 pick)

```
backlog.md                                              # current state
frontend/src/services/telemetry.ts                      # PostHog event surface (for BACKLOG-159 event)
frontend/src/hooks/useTrialStatus.ts                    # license-state hook to extend
frontend/src/components/banners/TrialBanner.tsx         # existing banner pattern to mirror
frontend/src/pages/Settings.tsx                         # Settings → License section
backend/app/core/feature_flags.py                       # is_module_allowed_for_tier helper
```

## Strategic Notes (PO context)

- **Why BACKLOG-159 next:** v1.4.0 lands with sync UX polished and license
  activation working — but the moment a user converts is anticlimactic.
  Closing this loop ties off the monetization arc. It's also small enough to
  ship in a single session, leaving room for cleanup.
- **Why not BACKLOG-087 first:** templates touch onboarding, which deserves
  its own session. Picking it over BACKLOG-159 makes sense only if Greg has
  fresh data showing new-install drop-off in the first hour.
- **R6 produced no new debt.** `sync_broadcast` cleanly mirrors
  `discovery_broadcast`; if a third pub/sub channel ever appears, genericizing
  is a 30-line refactor — not now.
- **Test count regression risk:** S34 added zero backend tests (Phase 2 was
  frontend-only). If R7 has backend work, target +N new tests to keep the
  trend up.

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- Single test file: `backend\venv\Scripts\python.exe -m pytest backend/tests/<name>.py -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Frontend lint (changed files only): `cd frontend && cmd //c "npx eslint <path> --ext ts,tsx"`
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- Alembic upgrade: `backend\venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`

## Debt Watch

- **DEBT-078** — `backend\venv\Scripts\python.exe` required (no `pytest` on
  PATH). Quick win still pending; carries from S33-S34.
- No new debt introduced in S34.
