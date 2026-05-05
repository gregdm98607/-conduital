# Session 32 — Stripe Inline + Feedback Admin + R6 Scoping

## Context

Session 31 (2026-05-04) shipped **v1.3.2** in three clean commits:

- **`d38a0b1`** — DEBT-143 (FeedbackWidget apostrophe, build blocker) + DEBT-144 (6 license tests on legacy `gr_*` keys, CI red) + version bump to `1.3.2` across `pyproject.toml`, `package.json`, `installer/conduital.iss`. Note: v1.3.0/v1.3.1 commits had not bumped these files; S31 jumped them straight to `1.3.2`.
- **`777d72c`** — MON-009 PostHog frontend wiring. New [`frontend/src/services/telemetry.ts`](frontend/src/services/telemetry.ts) singleton (10-event batch / 5s flush / sendBeacon on unload). Events live: `app_first_launch`, `app_launched`, `license_activated`, `gate_hit_<module>`, `feedback_submitted`. New Settings → Privacy toggle (mirrors backend `/telemetry/opt-out`).
- **`bcc093e`** — MON-010 trial expiry banners. New [`useTrialStatus`](frontend/src/hooks/useTrialStatus.ts) hook + [`TrialBanner`](frontend/src/components/trial/TrialBanner.tsx) component. Day-7 amber / Day-11 red / Day-13 blocking modal with extension request. Per-session dismissal. Banner-shown/dismissed events all wired through telemetry.

**Build / test status (post-S31):**
- ✅ `npm run build` clean (~3.3s).
- ✅ `pytest backend/tests/` 479 passed, 1 skipped.
- ✅ Three commits ahead of last `auto-sync-2026-04-26`.

## Open R5 Monetization Items

| ID | What | Why it matters |
|----|------|----------------|
| MON-008 | **Stripe inline activation** — `/license/activate` returns 503 for `sk_live_*` / `sk_test_*` | If a buyer pastes the key from the Resend email instead of the activation link, they hit a dead end. Webhook is the only fulfillment path right now. |
| MON-011 | **Feedback admin view** — Settings → Feedback tab listing all SQLite submissions | Greg has zero triage path. Workaround is `sqlite3 conduital.db "SELECT * FROM feedback"`. |
| BACKLOG-159 | **Post-activation welcome flow** — replace bare "License accepted" toast with one-time celebratory state | First impression after the user pays. |
| BACKLOG-161 | **Public download URL** — `CONDUITAL_DOWNLOAD_URL` defaults to `https://conduital.com/download/v1.3.0` but conduital.com isn't hosting downloads. Stripe/Resend emails will 404. | Distribution blocker. Needs DNS + hosting decision, not just code. |

## Priority-Ordered Task List

### Phase 1 — MON-011: Feedback Admin View (~2-3 hours)

This unblocks Greg's triage workflow and is the smallest code change with the most personal-productivity payoff.

Suggested steps:
1. Backend: add `GET /api/v1/feedback` (list, filter by `category` + `resolved`, paginate) and `PATCH /api/v1/feedback/{id}` (toggle `resolved` field). Add `resolved BOOLEAN DEFAULT 0` to the `feedback` SQLite table via Alembic migration.
2. Frontend: add `'feedback'` to `SectionId` in [`Settings.tsx`](frontend/src/pages/Settings.tsx). Render a collapsible section with:
   - Filter chips: All / Bug / Feature / General / Unresolved.
   - List rows: category icon, message preview (first 80 chars), page, date, email-if-set, resolve checkbox.
   - Click row → expand inline (no modal, keep it lightweight).
   - "Export CSV" button (client-side blob).
3. Telemetry: nothing new — admin actions don't need to be tracked.

### Phase 2 — MON-008: Stripe Inline Activation (~3-4 hours)

The Stripe key in the Resend email comes from `checkout.session.id`. Two options:

- **Option A (preferred):** treat `sk_live_*` / `sk_test_*` as opaque receipts — store as `purchase_id`, set tier to `gtd` (or look up via Stripe price ID metadata), don't actually verify against Stripe API. Same risk profile as Gumroad's no-product-id path. Lowest-risk shipping option.
- **Option B:** call `stripe.checkout.sessions.retrieve()` to verify the key is real and `payment_status == 'paid'` before activating. Requires `STRIPE_API_KEY` in env (currently only set for the webhook). Higher cost but strictly correct.

Recommendation: Option A, with a sentence in the activation success message ("verified via webhook"). If Greg disagrees, switch to B.

### Phase 3 — R6 Scoping (1 hour, optional)

With v1.3.2 shipped and PostHog now collecting funnel data, R6 candidates can be ranked. Candidates:
- **BACKLOG-153** — File Sync UX. Sync is happening but invisible. Likely the #1 user-visible gap once they install.
- **BACKLOG-159** — Post-activation welcome flow. Small, but high-leverage for paid users.
- **BACKLOG-87** — Persona templates. Requires content design more than code.

Suggested deliverable: a short `r6-scope.md` with three bullets per option (effort / leverage / dependencies) so Greg can choose.

### Phase 4 — Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && cmd //c "npm run build"`
3. Update [`backlog.md`](backlog.md) — close MON-008 / MON-011 if shipped, add anything discovered.
4. Bump version `1.3.2 → 1.3.3` if Phase 1+2 ship together.
5. Commit + push (one commit per phase).
6. **Write Session 33 prompt → `next-prompt.md`** (per CLAUDE.md MEMORY rule).

## Read First

```
backlog.md                                              # R5 status, MON-008/011 details
backend/app/api/license.py                              # Stripe 503 path lives here (line 216-223)
backend/app/api/feedback.py                             # Existing POST handler — extend with GET/PATCH
backend/app/models/feedback.py                          # Add resolved field
backend/app/api/webhooks.py                             # Stripe webhook (working, reference for inline path)
frontend/src/pages/Settings.tsx                         # Where Feedback section lives
frontend/src/services/telemetry.ts                      # Reference pattern if Phase 2 needs new events
```

## Strategic Notes (PO context)

- **Why feedback admin first:** smallest scope, biggest personal-productivity win for Greg, no external dependencies. Phase 2 can land same day if Phase 1 goes fast.
- **Why Stripe inline second:** every paid customer who pastes the key from the email instead of clicking the activation link hits a 503. Estimated cost = lost activations + refund risk. Cheap insurance.
- **Why park R6 for now:** PostHog has only had ~24 hours of data when Session 32 starts. Wait one more week of usage data before committing to a major release direction. Greg's instinct + the funnel data together will be a much better signal than instinct alone.
- **Watch the trial banners in production:** the Day-13 modal is blocking. If anyone reports it appearing for paid users, the bug is almost certainly in [`useTrialStatus`](frontend/src/hooks/useTrialStatus.ts) — `is_trial_active` should already be false for paid users, but worth verifying with the production data.
- **PostHog dashboard first usage:** set `POSTHOG_DEV_WRITE_KEY` in `.env`, run the app, verify events flow. If they don't, check `GET /api/v1/telemetry/status` for `posthog_configured: true`.

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- Single test file: `backend\venv\Scripts\python.exe -m pytest backend/tests/test_feedback_api.py -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- Alembic migration: `backend\venv\Scripts\python.exe -m alembic -c backend/alembic.ini revision --autogenerate -m "add resolved to feedback"`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`

## Debt Watch

- **DEBT-078** — `backend\venv\Scripts\python.exe` required (no `pytest` on PATH). Low-priority but annoying. Consider a `Makefile` or `pyproject.toml` script entry.
- No new debt introduced in S31.
