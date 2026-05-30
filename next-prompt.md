# Session 37 — next pick (post-v1.5.0)

## Context

Session 36 (2026-05-30) shipped **v1.5.0** — **BACKLOG-087 Starter Templates by
Persona**. A new user can now one-click scaffold a tailored starting structure
instead of staring at an empty app. Two commits expected:

- `feat(BACKLOG-087)` Starter templates:
  - **Backend** — hardcoded persona definitions in
    [`template_data.py`](backend/app/services/template_data.py) (3 personas:
    Writer / Knowledge Worker / Engineer); [`template_service.py`](backend/app/services/template_service.py)
    (`list_templates` / `get_template` / `apply_template`); single-transaction
    apply creates Areas (get-or-create by title) + Projects (with NPM fields +
    live momentum via `IntelligenceService.calculate_momentum_score`) +
    ProjectPhases + next-action Tasks. **Activates the dormant `PhaseTemplate`
    model** via get-or-create on its unique `name`, linking `Project.phase_template_id`.
    New [`schemas/template.py`](backend/app/schemas/template.py) +
    [`api/templates.py`](backend/app/api/templates.py) (core router registered in
    [main.py](backend/app/main.py) beside projects). `template_previewed` /
    `template_applied` added to telemetry `KNOWN_EVENTS`.
  - **Frontend** — `getTemplates/getTemplate/applyTemplate` in
    [`api.ts`](frontend/src/services/api.ts); Template types in
    [`types/index.ts`](frontend/src/types/index.ts);
    [`useTemplates.ts`](frontend/src/hooks/useTemplates.ts) (mutation invalidates
    projects/areas/tasks caches + fires telemetry);
    [`TemplatesPage.tsx`](frontend/src/pages/TemplatesPage.tsx) gallery (persona
    cards, expandable preview, apply → toast → navigate to first project);
    `/templates` route in [App.tsx](frontend/src/App.tsx); sidebar nav entry +
    "Start from a template" CTA on the Projects empty state
    ([Projects.tsx](frontend/src/pages/Projects.tsx)).
- `chore(S36)` v1.5.0 closeout — version bump, backlog refresh, lessons entry,
  this prompt.

**Build / test status (post-S36):**
- ✅ `pytest backend/tests/` — **509 passed (508 pass + 1 skip)**; +10 new
  tests in `test_templates_api.py` (list/detail/404, apply creates
  areas/projects/phases/tasks, PhaseTemplate linkage, next-action flags, live
  momentum, idempotent re-apply).
- ✅ `npm run build` clean (~4.7s, 833 kB / 208 kB gzip). eslint clean on new files.
- ✅ Versions bumped `1.4.1 → 1.5.0`: `backend/pyproject.toml` (SoT),
  `config.py` `_FALLBACK_VERSION`, `frontend/package.json`,
  `installer/conduital.iss`, `backend/version_info.txt`.

> ⚠️ **Not done this session:** no live browser smoke of `/templates`. The
> app lifespan binds to the real local DB (`%LOCALAPPDATA%\Conduital\tracker.db`),
> so a live apply would pollute real data. Backend behavior is fully covered by
> the 10 isolated integration tests. **Suggest a 5-min manual smoke next
> session:** open `/templates`, apply a persona, confirm projects/areas/phases/
> momentum render, then delete them.

## ⚠️ Distribution carry (important)

**`CONDUITAL_DOWNLOAD_URL` still points to `ConduitalSetup-1.4.1.exe`.** The app
version is now 1.5.0 but **no 1.5.0 installer has been built or hosted**. If you
distribute v1.5.0, do the full BACKLOG-161 dance first or fulfillment emails 404:
1. Rebuild the `.exe` (PyInstaller spec uses `backend/version_info.txt` — now
   1.5.0; then Inno Setup `installer/conduital.iss` — now 1.5.0).
2. Copy `ConduitalSetup-1.5.0.exe` into `conduital-site/public/downloads/`.
3. Add `vercel.json` redirects for `/download/v1.5.0` + repoint `/download/latest`.
4. Bump `CONDUITAL_DOWNLOAD_URL` in [config.py:320](backend/app/core/config.py)
   (and the fallback in [webhooks.py:118](backend/app/api/webhooks.py)) to the
   new asset.
Until then, v1.5.0 runs fine locally; only the buy→email→download path serves 1.4.1.

## Pick the next swing

Zero open tech debt; onboarding is now strong (FirstRunGuide + templates).

### Recommended: **BACKLOG-160 — Sidebar license badge** (~2–3 hours)
The long-standing small loose end. Always-visible tier pill (`Free Trial · 9d`,
`GTD`, `GTD+`) in the sidebar footer, click → Settings → License. Reads
`useTrialStatus`. Closes the license-visibility loop (Welcome modal handled the
activation moment; this handles every other moment). Smallest finishing move
before any non-Greg users.

### Alternatives
- **Wow-factor polish** — BACKLOG-093 quick-capture success animation (S,
  reuse `animate-celebrate-ripple`) + BACKLOG-150 Health-tab sparkline trends (M).
  Screenshot-worthy, low risk, frontend-only.
- **Perf debt: route code-splitting** — bundle is 833 kB (> Vite's 500 kB warn).
  `React.lazy` + `Suspense` on the page routes in `App.tsx` would cut initial
  load meaningfully. Clean half-session win; first real perf debt of v1.x.
- **Templates follow-ups** (extend BACKLOG-087): add a 4th persona
  (Personal / Life Admin or Student); offer "Start from a template" inside
  `FirstRunGuide` step 2; optionally persist templated projects through
  `StorageService` so file-sync users get markdown immediately (currently
  DB-only — see below).
- **BACKLOG-085 Memory Diff View** / **BACKLOG-049/050** project workload +
  blocked status — older R3/R4 quality items.

### Cleanup (always-on)
- Frontend lint backlog (~18 errors / 16 warnings in older pages) — not
  introduced by S36; `npm run lint -- --fix` + manual hook-rule pass (~1h).

## Read First (regardless of pick)
```
backlog.md                                                  # current state
backend/app/services/template_service.py                    # S36 reference: bulk scaffold + dormant-model activation
backend/app/services/template_data.py                       # persona content (easy to extend)
frontend/src/pages/TemplatesPage.tsx                        # gallery UI pattern
frontend/src/hooks/useTrialStatus.ts                        # for BACKLOG-160 sidebar badge
frontend/src/components/layout/Layout.tsx                   # sidebar footer mount point (badge)
tasks/lessons.md                                            # S36 entry: version-vs-download-URL gotcha
```

## Known scope notes (S36 decisions)
- Templates create **DB entities only** (no `StorageService.persist_project`
  call) — clean + test-safe; default mode is SQLite-as-source-of-truth, so this
  is correct. Only matters if a user runs `STORAGE_MODE=storage_first` (opt-in
  BYOS), where templated projects won't get markdown until edited. Revisit if
  storage_first becomes default.
- Apply is **additive** for projects/tasks (re-applying makes more), but
  **idempotent** for Areas + PhaseTemplates. Surfaced mainly from empty states,
  so duplicate scaffolds are unlikely.
- Per-tier persona content is **hardcoded** (like the WelcomePaidTierModal tier
  list). Fine for 3 static personas; revisit if templates become user-authored.

## Phase 4 — Session Closeout (ritual)
1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q` (target 509+).
2. Frontend build: `cd frontend && cmd //c "npm run build"`.
3. Update [backlog.md](backlog.md) — mark the pick done, refresh Stats.
4. Bump version (patch/minor per scope). Remember: **app version ≠ download URL** (see lessons.md S36).
5. Commit (one feat per chunk; one closeout commit), then push.
6. **Write Session 38 prompt → `next-prompt.md`** (MEMORY rule).

## Shell Notes (Windows)
- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- Single test file: `backend\venv\Scripts\python.exe -m pytest backend/tests/<name>.py -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Frontend lint (changed files): `cd frontend && cmd //c "npx eslint <path>"`
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- git commit with special chars: write message to temp file, `git commit -F file.txt`
