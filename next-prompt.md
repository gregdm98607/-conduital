# Session 38 — next pick (post-v1.5.1)

## Context

Session 37 (2026-05-30 → 05-31) shipped **v1.5.1**. What started as a small UX
feature (BACKLOG-160) turned up two serious pre-existing storage bugs and a vault
pollution incident. Three commits expected:

1. `docs:` — committed the dangling S36 storage-fix lessons entry (`86e5977`).
2. `feat(BACKLOG-160)` — **always-visible license tier badge** in the sidebar
   footer: new [`LicenseBadge.tsx`](frontend/src/components/license/LicenseBadge.tsx)
   (states: `GTD+` / `GTD` / `Free Trial · Nd` / `Free`, links → Settings);
   [`useTrialStatus`](frontend/src/hooks/useTrialStatus.ts) extended with
   `tier`/`effectiveTier`; mounted in [`Layout.tsx`](frontend/src/components/layout/Layout.tsx);
   `license_badge_clicked` + the two previously-unregistered `trial_day_7/11_banner_dismissed`
   events added to `KNOWN_EVENTS` ([telemetry.py](backend/app/api/telemetry.py)).
3. `fix(storage)` — **test isolation + storage_first serialization** (see below).

### The storage incident (what S37 actually spent its time on)
Running the full backend suite went 513 pass → **61 failed**, all in code the badge
never touched. Root cause chain:
- Tests weren't hermetic: `StorageService` reads `STORAGE_MODE` from the live
  `backend/.env`, which was set to **`storage_first`** (+ real `STORAGE_PATH`) while
  testing the S36-followup storage fix. So project-creating tests wrote markdown into
  the **real Obsidian vault** (`C:\Users\gregm\999_SECOND_BRAIN\_Obsidian\05_Projects`).
- That exposed a real bug: `persist_project` serializes `project.status`, an ORM
  `StatusEnum` (`str`+`Enum`), which PyYAML's safe dumper can't represent →
  `RepresenterError`, re-raised → **`storage_first` project creation 500s in the live app.**
- `write_entity` truncates (`open("w")`) before the dump raises → 60+ empty `.md` files
  were created in the vault.

**Fixes shipped:** autouse `conftest` fixture forces `STORAGE_MODE=legacy` for every
test (storage tests override with their own `tmp_path`); recursive `_yaml_safe()` at
the write boundary ([local_folder.py](backend/app/storage/local_folder.py)) coerces
enums/datetimes to primitives; regression test added. Full suite green again.

**Vault cleanup:** all 67 test-fixture files removed from `05_Projects/` (55 had been
swept by your overnight automation; I deleted the remaining 12). The real project
`The_Coherence_Dashboard` was a false-positive in my scan — left untouched.

## ⚠️ Carry items (read before picking work)

1. **Real-DB propagation (verify!).** At 2026-05-31 00:13 local, your vault's sync
   re-ingested the leftover test `.md` files into the **real Conduital DB**
   (`%LOCALAPPDATA%\Conduital\tracker.db`), assigning real tracker_ids (saw 3219
   "With Area", 3220 "Neural Link Systems (Deprecated)"). **Your live app may now
   contain junk test projects.** Since markdown is the source of truth in
   `storage_first`, deleting the `.md` files (done) *should* let a sync/restart
   reconcile them out — but **verify in the app** and hard-delete any stragglers.
   Quick check: open Projects, filter for names like `*_Test`, `*_Ghost`, `Rebal_*`,
   `Unstuck_*`, `TZ_*`, `With Area`, `Status Ghost`.
2. **`storage_first` was never exercised end-to-end before today** — the enum bug
   proves it. Other entity paths (areas, goals, tasks via `entity_markdown` handlers)
   may have the same enum/datetime issue. Consider a `storage_first` integration sweep
   (BACKLOG candidate below).
3. **Your `backend/.env` is still `STORAGE_MODE=storage_first`.** With the enum fix it
   now works, but if you don't want live file-sync, set it back to `legacy`.
4. **Distribution carry (unchanged):** `CONDUITAL_DOWNLOAD_URL` still points to
   `ConduitalSetup-1.4.1.exe`. App is 1.5.1; no 1.5.x installer built/hosted. Do the
   BACKLOG-161 dance before distributing (rebuild `.exe` from `version_info.txt`/`conduital.iss`,
   host, repoint `vercel.json` + `config.py:320` + `webhooks.py:118`).

## Pick the next swing

### Recommended: **Harden `storage_first` (new debt from S37)** (~2–4 hours)
The enum bug means this mode shipped untested. Add an integration test that, in
`storage_first` with a `tmp_path`, round-trips **every** entity type (project, area,
goal, vision, task) through create→persist→read and asserts no serialization error +
correct frontmatter. Fix any other enum/datetime leaks the sweep finds. Highest-value
because it's a correctness gap in a mode you're actually running.

### Alternatives
- **Wow-factor polish** — BACKLOG-093 quick-capture success animation (S) +
  BACKLOG-150 Health-tab sparkline trends (M). Screenshot-worthy, frontend-only.
- **Perf debt: route code-splitting** — bundle is 834 kB (> Vite's 500 kB warn).
  `React.lazy`+`Suspense` on `App.tsx` routes. Clean half-session win.
- **Templates follow-ups** (BACKLOG-087) — 4th persona; "Start from a template" in
  `FirstRunGuide`; persist templated projects via `StorageService` (now that the enum
  bug is fixed, storage_first users would get markdown).
- **BACKLOG-085 Memory Diff View** / **BACKLOG-049/050** workload + blocked status.

### Cleanup (always-on)
- Frontend lint backlog (~18 errors/16 warnings in older pages) — `npm run lint --fix`
  + manual hook-rule pass (~1h). Not introduced by S37.

## Read First (regardless of pick)
```
backlog.md                                              # current state, Stats
tasks/lessons.md                                        # S37 entry: hermetic tests + enum serialization
backend/tests/conftest.py                               # the new autouse storage-isolation fixture
backend/app/storage/local_folder.py                     # _yaml_safe write-boundary sanitizer
backend/app/services/storage_service.py                 # _project_to_dict (status enum source)
frontend/src/components/license/LicenseBadge.tsx        # S37 badge pattern
```

## Phase 4 — Session Closeout (ritual)
1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q`
   (target ~514). **Note:** the suite is now hermetic — it forces legacy storage; do
   NOT rely on `.env`. A bare `... | tail` masks failures (exit code is tail's) — read
   the summary line.
2. Frontend build: `cd frontend && cmd //c "npm run build"`.
3. Update [backlog.md](backlog.md) — mark pick done, refresh Stats.
4. Bump version (patch/minor per scope). **App version ≠ download URL** (lessons S36).
5. Commit (one feat per chunk; one closeout commit), then push.
6. **Write Session 39 prompt → `next-prompt.md`** (MEMORY rule).

## Shell Notes (Windows)
- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q`
- Single test: `backend\venv\Scripts\python.exe -m pytest backend/tests/<name>.py -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Frontend lint (changed files): `cd frontend && cmd //c "npx eslint <path>"`
- git commit with special chars: write message to temp file, `git commit -F file.txt`
