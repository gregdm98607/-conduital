# Session 41 — next pick (post-S40)

## Context

**MON-013 is closed** (2026-06-04, S40 paired session). The full Stripe→Resend→app
fulfillment chain was verified end-to-end:
- Stripe test checkout → `https://www.conduital.com/api/stripe-webhook` → `200 OK {"status":"fulfilled","tier":"gtd","email_sent":"true"}`
- Email delivered to `gregmaxfield@gmail.com` with key `731D8449-…-BFA72BA7`
- App: **"Licensed — GTD, Activated 6/4/2026"** ✅

S38–S40 history:
- **S38:** relocated fulfillment to stateless Vercel function + wired PostHog + storage_first enum fix + v1.5.2.
- **S39:** verified deploy live; hardened webhook fail-closed; hardened `storage_first` handler-path serialization (6-test sweep); 524 backend pass.
- **S40 (paired):** Resend domain verified, Stripe test-mode webhook registered, end-to-end purchase completed. MON-013 → Done.

## ⚠️ One remaining action before real buyers go through checkout

The Stripe webhook is **test-mode only** — live purchases won't trigger it. Before
going live, repeat **Step 4 of `docs/MON-013-fulfillment-runbook.md`** in **live mode**:
1. Stripe → switch to live mode → Developers → Webhooks → Add endpoint
2. Same URL: `https://www.conduital.com/api/stripe-webhook`
3. Same event: `checkout.session.completed`
4. Reveal live-mode `whsec_…` → update `STRIPE_WEBHOOK_SECRET` in Vercel (Production scope) → redeploy
5. Verify: `curl -X POST https://www.conduital.com/api/stripe-webhook -d "{}"` → `400` (not `unconfigured`)

## Pick the next swing

### Recommended: **Build + host the v1.5.2 installer (BACKLOG-161)**
The most direct path to real-buyer value. The PostHog key + stable `/download/latest` URL
from S38 only reach users in the new build. Steps (all Greg-side):
1. Run `build.bat` from `C:\Dev\conduital` to produce `ConduitalSetup-1.5.2.exe`.
2. Host it (wherever the 1.4.1 .exe is currently hosted, or a new location).
3. Update the redirect in `conduital-site/vercel.json`: `/download/latest` → new file.
   (No app rebuild needed — just change the redirect target + redeploy the site.)

### Alternatives
- **Live-mode Stripe webhook** (see above — 5 minutes, Greg-side only)
- **Perf: route code-splitting** — bundle is 834 kB (> Vite 500 kB warn). `React.lazy`+`Suspense` on `App.tsx` routes. Clean half-session win.
- **Wow-factor polish** — BACKLOG-093 quick-capture animation (S) + BACKLOG-150 Health sparklines (M).
- **Frontend lint backlog** (~18 errors/16 warnings in older pages).
- **DEBT-020** SyncEngine area markdown handling — needs a sync-engine verification pass before closing.

## State
- `conduital` master: synced as of last S40 commit (backlog + MON-013 close)
- `conduital-site` main: synced (fail-closed webhook `2917faa`)
- Installed app: v1.4.1 (no license UI — predates the license system)
- Dev backend source: v1.5.2 (has license endpoints, not yet packaged)

## Phase 4 — Session Closeout (ritual)
1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q` (target ~524 pass / 1 skip).
2. Frontend build: `cd frontend && cmd //c "npm run build"`. Site fn tests: `node --test C:/Dev/conduital-site/test/`.
3. Update `backlog.md` (mark pick, refresh Stats). Bump version per scope.
4. Commit + push. Two repos if `conduital-site` touched.
5. Write Session 42 prompt → `next-prompt.md` (MEMORY rule).

## Shell Notes (Windows)
- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Site function tests: `node --test C:/Dev/conduital-site/test/stripe-webhook.test.mjs`
- Other repo git: `git -C C:/Dev/conduital-site <cmd>` (branch `main`; conduital is `master`)
- Probe prod webhook: `curl -sS -X POST https://www.conduital.com/api/stripe-webhook -d "{}"`
  - `400 Missing stripe-signature` = armed (test-mode secret set) ✅
  - `200 unconfigured` = signing secret not set ❌
