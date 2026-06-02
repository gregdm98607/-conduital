# Session 39 — next pick (post-S38)

## Context

Session 38 (2026-06-02) took the **MON-013 launch blocker** from "broken in prod" to
**code complete**. The decision (via plan mode) was *code + runbook* with a *Vercel function
beside the site*. Two repos changed:

- **`conduital-site`** (Astro/Vercel, branch `main`): NEW stateless fulfillment function
  [`api/stripe-webhook.js`](../conduital-site/api/stripe-webhook.js) — verify Stripe signature →
  generate 8×8-hex key → email via Resend. Zero deps (node:crypto + fetch). 20 `node --test`
  (`test/stripe-webhook.test.mjs`). `.env.example` + README documented.
- **`conduital`** (branch `master`): `config.py` — baked PostHog prod key (`phc_…`, publishable)
  + `CONDUITAL_DOWNLOAD_URL` → stable `https://conduital.com/download/latest`; `webhooks.py`
  production-note (local handler is now dev/reference only — Stripe can't reach localhost);
  `test_license_api.py::TestStripeWebhookKeyContract` pins the key format across both repos;
  `docs/MON-013-fulfillment-runbook.md`; version **1.5.1 → 1.5.2**. Backend **518 pass / 1 skip**.

**Key architecture fact (don't re-discover):** the desktop backend's `webhooks.py` only runs on the
buyer's `127.0.0.1` — Stripe can't reach it. The app activates Stripe keys **offline** (format-only,
`license.py::_activate_stripe_opaque`, MON-008), so the public function is stateless (no DB).

## ⭐ Recommended pick — DRIVE MON-013 TO ACTUALLY-DONE (external ops)

The code is done but **buyers still get no email until the external steps run.** This is still the
launch blocker. Work the runbook: **[`docs/MON-013-fulfillment-runbook.md`](docs/MON-013-fulfillment-runbook.md)**.
These need dashboards/secrets/DNS (Greg's hands; agent can deploy + verify):
1. **Deploy** the function (`cd conduital-site && git push` if Vercel-connected, else `vercel --prod`).
   Verify: `curl -i -X POST https://conduital.com/api/stripe-webhook` → 400 (once secret set) or 200.
2. **Vercel env vars**: `RESEND_API_KEY` (vault → Silver_Sage_Media → Account Information),
   `STRIPE_WEBHOOK_SECRET` (from step 4). Redeploy after setting.
3. **Resend domain + DNS** for `conduital.com` (sender `licenses@conduital.com`). **Snapshot the
   Cloudflare zone FIRST** (2026-04-18 incident).
4. **Stripe webhook** → `https://conduital.com/api/stripe-webhook`, event `checkout.session.completed`,
   copy signing secret → Vercel. Set checkout `metadata.conduital_tier`.
5. **PostHog**: confirm events flow (funnel `/insights/O3Fm24tR`) — needs the v1.5.2 build to ship first.
6. **End-to-end test purchase** (test mode) → delivered email → paste key → tier unlocks.
7. Close **MON-013** + flip **MON-002** to verified, with evidence.

## Carry items
1. **Push pending?** S38 committed both repos but may not have pushed (Greg said "commit").
   `git push` in `conduital` (master) and `conduital-site` (main) if not already synced. (Auto-sync
   may push the existing commits on its own — they already have proper messages.)
2. **No 1.5.x installer is hosted yet (BACKLOG-161).** The `/download/latest` redirect still targets
   `ConduitalSetup-1.4.1.exe` in `conduital-site/vercel.json`. After building/hosting the 1.5.2 `.exe`,
   **bump that redirect target** (no app rebuild needed for the URL). The v1.5.2 build is also what
   ships the baked PostHog key + new download URL to users.
3. **`backend/.env` may still be `STORAGE_MODE=storage_first`** (S37 carry). Tests are hermetic
   regardless; set back to `legacy` if you don't want live file-sync locally.

## Alternatives (if MON-013 ops are blocked on Greg)
- **Harden `storage_first`** (the S38 deferred alt) — integration test round-tripping every entity type
  (project/area/goal/vision/task) through create→persist→read in `storage_first` w/ `tmp_path`; fix any
  remaining enum/datetime serialization leaks. Pure in-repo, fully verifiable.
- **Perf: route code-splitting** — bundle is 834 kB (> Vite 500 kB warn). `React.lazy`+`Suspense` on
  `App.tsx` routes. Clean half-session win.
- **Wow-factor polish** — BACKLOG-093 quick-capture animation (S) + BACKLOG-150 Health sparklines (M).
- **Frontend lint backlog** (~18 errors/16 warnings in older pages).

## Read First
```
docs/MON-013-fulfillment-runbook.md          # the external-ops checklist (primary)
backlog.md                                    # MON-013 / MON-002 / Stats
task_plan.md, findings.md, progress.md        # S38 plan + verified findings + session log
conduital-site/api/stripe-webhook.js          # the function (+ test/stripe-webhook.test.mjs)
backend/app/api/license.py                    # _activate_stripe_opaque + _STRIPE_WEBHOOK_KEY_RE
```

## Phase 4 — Session Closeout (ritual)
1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q` (target ~519; hermetic).
2. Frontend build: `cd frontend && cmd //c "npm run build"`. Site fn tests: `cd conduital-site && npm test`.
3. Update `backlog.md` (mark pick, refresh Stats). Bump version per scope (**app version ≠ download URL**).
4. Commit (one feat per chunk; closeout commit), then push. **Two repos** if you touch `conduital-site`.
5. Write Session 40 prompt → `next-prompt.md` (MEMORY rule).

## Shell Notes (Windows)
- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Site function tests: `node --test C:/Dev/conduital-site/test/stripe-webhook.test.mjs`
- Other repo git: `git -C C:/Dev/conduital-site <cmd>` (branch `main`; conduital is `master`)
