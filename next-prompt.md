# Session 36 — R8 selection (post-v1.4.1)

## Context

Session 35 (2026-05-04) shipped **v1.4.1**, closing R7 / BACKLOG-159 plus the
DEBT-078 quick win. Two commits expected:

- `feat(BACKLOG-159)` Paid-tier post-activation flow:
  - **Frontend** — new
    [`WelcomePaidTierModal`](frontend/src/components/license/WelcomePaidTierModal.tsx)
    mounted globally in
    [`Layout`](frontend/src/components/layout/Layout.tsx); shows once per
    free→paid activation with the unlocked-feature list for GTD vs GTD+;
    fires `welcome_paid_tier` PostHog event; per-session dismissal via
    `sessionStorage`. Activation path in
    [`Settings.handleActivateLicense`](frontend/src/pages/Settings.tsx)
    dispatches `conduital:license-activated` window event when the prior
    `is_paid` was false and the new state flips to paid.
  - **Backend** — `welcome_paid_tier` + `welcome_paid_tier_dismissed` added
    to `KNOWN_EVENTS` in
    [`backend/app/api/telemetry.py`](backend/app/api/telemetry.py).
- `chore(S35)` v1.4.1 closeout — DEBT-078 (`[tool.poetry.scripts]` `test`
  entry added to `backend/pyproject.toml`), version bumps, backlog refresh,
  this prompt.

**Build / test status (post-S35):**
- ✅ `npm run build` clean (~3.6s, 812 kB / 202 kB gzip).
- ✅ `pytest backend/tests/` 498 passed, 1 skipped (no new tests; the welcome
  modal is a thin frontend-only wrapper around an existing event surface).
- ✅ Versions bumped: `pyproject.toml` / `package.json` /
  `installer/conduital.iss` → `1.4.1`.

## Pick R8

R5 done (monetization), R6 done (file sync UX), R7 done (paid-tier
post-activation polish). Backlog has zero open tech debt. The next swing
should target either (a) sidebar license visibility (the other small loose
end from R6 deferrals), (b) onboarding for new installs, or (c) the
distribution gap that's still blocking a real launch.

### Recommended: **BACKLOG-160 — Sidebar license badge** (~2–3 hours)

Smallest, finishes the license-visibility loop. The Welcome modal closes the
"what just happened" gap; this closes the "what tier am I on right now" gap.

Plan:
1. New
   [`SidebarLicenseBadge`](frontend/src/components/license/SidebarLicenseBadge.tsx)
   reads `useTrialStatus` (already polls `/license/status` every 30 min).
2. Renders compact pill: `Free Trial · 9d`, `GTD`, or `GTD+`. Clicking
   navigates to Settings → License (use a query param like
   `?section=license` if useful — cheap to add).
3. Mount in
   [`Layout`](frontend/src/components/layout/Layout.tsx) sidebar footer
   beside `SyncIndicator`. Should not push `SyncIndicator` off when the
   sidebar drawer is collapsed on mobile — pick layout carefully.
4. Day-7/11/13 styling can mirror `TrialBanner` colors (amber/red).
5. Add small `sidebar_license_badge_clicked` PostHog event.

**Why this:** finishes the post-activation arc cleanly (modal +
always-visible badge), takes a single short session, and unblocks any
"Where do I see my plan?" support questions before launch.

### Alternative: **BACKLOG-087 — Starter Templates by Persona** (~half day)

Pre-baked project templates (Writer, Knowledge Worker, Engineer). Bigger
onboarding win for first-launch UX. Pick this if Greg has fresh data showing
new-install drop-off in the first hour. Otherwise BACKLOG-160 first because
it can ride alongside it.

### Alternative: **BACKLOG-161 — Public download URL** (Distribution blocker)

`CONDUITAL_DOWNLOAD_URL` defaults to `https://conduital.com/download/v1.3.0`
but `conduital.com` isn't hosting downloads yet, so Stripe/Resend
fulfillment emails will 404. Needs a DNS/hosting decision from Greg, not
just code. Worth raising with him at the top of S36 — even a placeholder
GitHub Releases redirect would unblock a real launch.

### Cleanup (always-on)

1. **Frontend lint backlog** — still 18 errors / 16 warnings in
   `frontend/src/pages/{Contexts,Goals,Visions,InboxPage,ProjectDetail,Projects,SomedayMaybe}.tsx`
   and `pages/memory/`. None block build. `npm run lint -- --fix` + manual
   pass for conditional-hook errors is ~1 hour. Side-quest if R8 work is
   light.
2. **Welcome modal test coverage** — no tests added in S35. If we add a JS
   test runner (vitest) we should backfill `WelcomePaidTierModal` and
   `useTrialStatus` (both are pure-ish and would catch regressions). Could
   pair with BACKLOG-160 since they share the same surface.

## Phase 4 — Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q` (target: 498+ pass).
2. Frontend build: `cd frontend && cmd //c "npm run build"`.
3. Update [`backlog.md`](backlog.md) — mark R8 selection's items done, update
   Stats.
4. Bump version `1.4.1 → 1.4.2` (patch) or `1.5.0` (minor) depending on R8
   scope.
5. Commit + push (one feat commit per chunk; one closeout commit at the end).
6. **Write Session 37 prompt → `next-prompt.md`** (per CLAUDE.md MEMORY rule).

## Read First (regardless of R8 pick)

```
backlog.md                                                      # current state
frontend/src/components/license/WelcomePaidTierModal.tsx        # S35 reference for tier-aware UI
frontend/src/hooks/useTrialStatus.ts                            # license-state hook (used by sidebar badge)
frontend/src/components/layout/Layout.tsx                       # sidebar footer mount point
frontend/src/components/sync/SyncIndicator.tsx                  # sibling component for sidebar badge layout
frontend/src/pages/Settings.tsx                                 # license activation handler — already wired
backend/app/core/config.py                                      # CONDUITAL_DOWNLOAD_URL (BACKLOG-161)
```

## Strategic Notes (PO context)

- **Why BACKLOG-160 next:** the welcome modal handles the activation moment;
  the badge handles every other moment. Together they make license state
  legible at a glance, which matters once we have non-Greg users. Small
  enough to leave room in the session for either lint cleanup or seeding
  BACKLOG-087.
- **Why pause on BACKLOG-087:** templates are an onboarding workstream —
  picking the right personas, content, and surface deserves its own session.
  The reward is bigger but the planning load is non-trivial.
- **BACKLOG-161 closed mid-S35** (Option A — static asset on conduital.com):
  - Backend default `CONDUITAL_DOWNLOAD_URL` repointed to
    `https://conduital.com/downloads/ConduitalSetup-1.4.1.exe`
    ([config.py:316](backend/app/core/config.py), [webhooks.py:118](backend/app/api/webhooks.py)).
  - v1.4.1 installer built fresh: `installer/Output/ConduitalSetup-1.4.1.exe`
    (28.27 MB, SHA256 `833C0FC796207A8CE5782D033071E3C7C3EB7A15FC32988D7EBECCC4FFBAEE56`).
  - conduital-site shipped at commit `98aa61e`: binary in `public/downloads/`,
    `vercel.json` redirects for `/download/v1.4.1` + `/download/latest`,
    new `/download` page exposes version/size/hash. All four URL
    variants verified live (HEAD returns 200, content-length matches build).
  - **Open follow-ups (not blocking):**
    1. End-to-end Stripe webhook → Resend email test in test-mode (real
       Resend send to a Greg inbox; click the download button in the
       email and confirm the .exe arrives). Defer to whenever Stripe
       test-mode is next on a session.
    2. Cosmetic: bump `VersionInfoVersion` / `VersionInfoProductVersion`
       in `installer/conduital.iss` from `1.2.1.0` → `1.4.1.0` and
       re-run Inno Setup. Currently the .exe's file-properties dialog
       shows the wrong version. Not user-visible during install.
    3. Future versions: rebuild the .exe locally, copy into
       `conduital-site/public/downloads/`, update `vercel.json`
       redirects for the new tag, and bump `CONDUITAL_DOWNLOAD_URL` to
       match. The `/download/latest` redirect is the stable URL —
       updating only its destination keeps email links from older
       releases working.
- **Test count flat at 499.** R7 was a small frontend addition; no
  regression risk surfaced. If R8 has any backend work, target +N new tests
  to keep the trend up.
- **Welcome modal tradeoff captured:** we hardcoded the per-tier feature
  list in `WelcomePaidTierModal.tsx` instead of building a backend
  endpoint. That's fine while there are exactly two paid tiers and the
  feature list rarely changes. Revisit if/when we add a third tier or
  start A/B-testing the unlock copy.

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- Single test file: `backend\venv\Scripts\python.exe -m pytest backend/tests/<name>.py -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Frontend lint (changed files only): `cd frontend && cmd //c "npx eslint <path> --ext ts,tsx"`
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- Alembic upgrade: `backend\venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`

## Debt Watch

- **Zero open tech debt** as of S35 (DEBT-078 closed). First time in the
  v1.x series the debt column is empty — try to keep it that way.
- New surface in S35 (`WelcomePaidTierModal`) has no automated test
  coverage. Worth backfilling once we add a JS test runner.
