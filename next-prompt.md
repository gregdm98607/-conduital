# Session 33 — R6 Selection + Welcome Flow + Sync UX (data-led)

## Context

Session 32 (2026-05-04) shipped **v1.3.3** in three commits:

- **MON-011 — Feedback admin view.** New Settings → Feedback section with filter
  chips (All / Bug / Feature / General / Unresolved), inline expand, resolve
  checkbox, and CSV export. Backend: new `resolved` boolean column on `feedback`
  (Alembic migration `018_add_resolved_to_feedback`), `GET /api/v1/feedback`
  gained a `resolved` filter, new `PATCH /api/v1/feedback/{id}` toggles the flag.
  9 new tests in [`backend/tests/test_feedback_api.py`](backend/tests/test_feedback_api.py).
- **MON-008 — Stripe inline activation.** Removed the 503 path in
  [`backend/app/api/license.py`](backend/app/api/license.py). Three formats
  now activate inline as opaque receipts:
  - `sk_live_*` / `sk_test_*` (Stripe API-style prefixes)
  - `cs_live_*` / `cs_test_*` (Stripe checkout session IDs)
  - 8-group hex (the webhook-emailed Conduital key)

  All map to tier `gtd`, are stored as `purchase_id`, and are idempotent. The
  webhook in [`backend/app/api/webhooks.py`](backend/app/api/webhooks.py)
  remains the authoritative fulfillment path; this is the buyer-pasted-receipt
  fallback. 6 new tests in [`backend/tests/test_license_api.py`](backend/tests/test_license_api.py).
- **R6 scoping doc** — see [`r6-scope.md`](r6-scope.md). Three candidates ranked
  on effort / leverage / dependencies. Tentative recommendation: **A. File Sync UX
  (BACKLOG-153)**, with a one-week wait for PostHog data before final commit.

**Build / test status (post-S32):**
- ✅ `npm run build` clean (~3.4s).
- ✅ `pytest backend/tests/` 492 passed, 1 skipped.
- ✅ Versions bumped: `pyproject.toml` / `package.json` / `installer/conduital.iss` → `1.3.3`.
- ✅ R5 Must-Have items all closed. Backlog open items reduced from ~69 → ~67.

## Decision First

**Read [`r6-scope.md`](r6-scope.md) and pick R6.** PostHog will have ~1 week of
data by S33 — enough to confirm or reject the "users bounce off invisible sync"
hypothesis. If the funnel data is silent on sync, default to A anyway (it
benefits trial + paid users equally and the engineering work is well-scoped).

## Priority-Ordered Task List

### Phase 1 — R6 Decision (15 min, blocking)

1. Open the PostHog dashboard. Look at:
   - `app_launched` → `gate_hit_*` ratio (do users actually hit features?).
   - Any `feedback_submitted` events — even one bug report about sync would tip A.
   - `trial_day_7_*` engagement (are people sticking around past day 7?).
2. Write the R6 selection at the top of [`backlog.md`](backlog.md) with one
   sentence of why.
3. If A wins, jump to Phase 2A. If B wins, Phase 2B. If C wins, Phase 2C.

### Phase 2A — File Sync UX (BACKLOG-153, ~1 week, recommended)

The first user-visible win once installed. Sync is happening but invisible.

Suggested skeleton:
1. **Backend**: extend the existing sync WebSocket channel (see
   [`useDiscoveryWebSocket`](frontend/src/hooks/useDiscoveryWebSocket.ts)) with
   per-event sync status: `sync_started`, `sync_progress`, `sync_completed`,
   `sync_error`, `last_synced_at`. If WS doesn't already broadcast these,
   add them in [`backend/app/services/`](backend/app/services/) or wherever
   sync orchestration lives.
2. **Frontend hook**: `useSyncStatus` — wraps the WS, exposes `{ status, lastSyncedAt, pendingCount, errors }`.
3. **Components**:
   - `SyncIndicator` in the sidebar footer (icon + relative time, e.g. "Synced 2m ago").
   - `SyncDetailsPanel` opened from the indicator — shows recent events + manual "Sync now" button.
   - Conflict-resolution UI for the existing `conflict_strategy: prompt` mode.
4. **Settings → Sync section**: add a "Recent activity" subsection showing the
   last 10 sync events.

### Phase 2B — Welcome / Post-Activation Flow (BACKLOG-159, ~2-3 days)

If R6 picks the activation experience:
1. New `WelcomeModal` triggered on first `is_paid=true` transition.
2. Tier-specific copy (gtd vs full); "What you just unlocked" feature list.
3. Telemetry: `welcome_shown`, `welcome_dismissed`, `welcome_tour_started`.
4. Optional feature tour stub (can ship without the tour content; iterate).
5. Replace the bare `toast.success('License activated!')` in
   [`frontend/src/pages/Settings.tsx`](frontend/src/pages/Settings.tsx).

### Phase 2C — Persona Templates (BACKLOG-087, ~2 weeks)

Highest effort. Defer unless A and B both miss. Bulk of the work is content
authoring, not engineering. If chosen, scope tightly: pick ONE persona (Writer
is a good first pick given Greg's other work) and ship it end-to-end before
adding more.

### Phase 3 — Always-On Cleanup (~30 min)

1. **DEBT-078** — `pytest` not on PATH. Easiest fix: add a Poetry script entry
   so `poetry run test` works without the `backend\venv\Scripts\python.exe`
   incantation. Lifts a daily papercut.
2. **BACKLOG-161 (download URL)** — still a distribution blocker. Needs DNS +
   hosting decision, not just code. Worth raising with Greg again if v1.4
   release is in sight.
3. Verify the trial banners look right with the new v1.3.3 in dev: spin up
   `useTrialStatus` with mock dates (Day 6 / 8 / 12 / 14) and screenshot.

### Phase 4 — Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q` (target: 492+ pass).
2. Frontend build: `cd frontend && cmd //c "npm run build"`.
3. Update [`backlog.md`](backlog.md) — close anything shipped, update Stats.
4. Bump version `1.3.3 → 1.3.4` (or `1.4.0` if R6 lands).
5. Commit + push (one commit per phase).
6. **Write Session 34 prompt → `next-prompt.md`** (per CLAUDE.md MEMORY rule).

## Read First

```
r6-scope.md                                             # R6 candidate ranking
backlog.md                                              # R5 closed; R6 candidates listed
backend/app/api/license.py                              # MON-008 inline activation logic
backend/app/api/feedback.py                             # MON-011 GET/PATCH/list
frontend/src/pages/Settings.tsx                         # Feedback section + Privacy + License panels
frontend/src/services/api.ts                            # listFeedback / updateFeedback / FeedbackListItem type
frontend/src/hooks/useDiscoveryWebSocket.ts             # Reference for sync status WS channel (Phase 2A)
```

## Strategic Notes (PO context)

- **Why decide R6 first:** the work scope differs by 3-5x between A, B, and C.
  Don't start any of them until the call is made — context-switching cost is high.
- **Why prefer A over B:** B helps paid users only (small absolute count); A helps
  every install. Even with no PostHog data, the priors favor A.
- **Why park C:** the bottleneck is content design, not engineering. Don't burn
  engineering cycles waiting for content; commission content authoring as a
  separate stream and revisit C in S35+.
- **MON-008 sanity check:** the new inline path activates as `gtd` regardless of
  what the buyer actually paid for. If we ever sell a `full`-tier product via
  Stripe and the buyer pastes the receipt, they'll be under-provisioned. Today
  there's only one paid tier (gtd) so this is fine; flag if/when a second tier ships.
- **Feedback admin watch:** the section auto-loads when expanded. If load is
  slow, add lazy fetching + pagination chips. Currently capped at 200 entries.
- **No new debt introduced in S32.**

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- Single test file: `backend\venv\Scripts\python.exe -m pytest backend/tests/test_feedback_api.py -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- Alembic upgrade: `backend\venv\Scripts\python.exe -m alembic -c backend/alembic.ini upgrade head`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`

## Debt Watch

- **DEBT-078** — `backend\venv\Scripts\python.exe` required (no `pytest` on PATH). Quick win for S33.
- No new debt introduced in S32.
