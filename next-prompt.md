# Session 40 — next pick (post-S39)

## Context

S38 made the **MON-013** Stripe→Resend fulfillment *code complete*. **S39 (2026-06-03)** then:
1. **Verified the function is live in prod.** The S38 push auto-deployed
   `conduital-site/api/stripe-webhook.js` to Vercel. `POST https://www.conduital.com/api/stripe-webhook`
   responds. (Apex 307-redirects to `www`.)
2. **Hardened the webhook to fail-closed** (deployed + verified live). With no `STRIPE_WEBHOOK_SECRET`
   it now returns `200 {"status":"unconfigured"}` and fulfills nothing — so adding `RESEND_API_KEY`
   alone can't make it an open relay. 25 `node --test`. Commits: conduital-site `2917faa`, conduital `a1690d7`.
3. **Hardened `storage_first` serialization** (the S38 deferred alt). The S37 `_yaml_safe` fix only
   covered the *project* write path; the *handler* entities (area/goal/vision/inbox/context/weekly_review)
   wrote via `entity_markdown.py` without enum sanitization — same RepresenterError class. Moved
   `_yaml_safe` to `entity_markdown.py` (single source, applied in `_write_frontmatter_file`); `local_folder.py`
   imports it. New `TestStorageFirstSerializationSweep` (6 tests) round-trips every entity type with leaked
   enums/datetimes. (Committed in the S39 closeout.)

**Probed prod state:** `STRIPE_WEBHOOK_SECRET` is **NOT set** on Vercel yet (endpoint returns
`{"status":"unconfigured"}`). So MON-013's external ops are still pending.

## ⭐ Recommended pick — FINISH MON-013 (external ops; launch blocker still open)

The launch blocker is NOT cleared until paid buyers actually receive a key. All code is done +
deployed + fail-closed. Remaining = **dashboard/secret/DNS work (Greg's hands; agent verifies)**.
Drive **[`docs/MON-013-fulfillment-runbook.md`](docs/MON-013-fulfillment-runbook.md)**:
1. **Vercel env vars**: `RESEND_API_KEY` (vault → Silver_Sage_Media → Account Information) +
   `STRIPE_WEBHOOK_SECRET` (from step 3). Redeploy. (Verify: unsigned `POST` flips from
   `{"status":"unconfigured"}` → `400 {"error":"Missing stripe-signature header"}`.)
2. **Resend domain + DNS** for `conduital.com` / sender `licenses@conduital.com`. **Snapshot the
   Cloudflare zone FIRST** (2026-04-18 incident).
3. **Stripe webhook** → `https://www.conduital.com/api/stripe-webhook`, event `checkout.session.completed`,
   copy signing secret → Vercel `STRIPE_WEBHOOK_SECRET`. Set checkout `metadata.conduital_tier`.
4. **PostHog**: confirm events flow (funnel `/insights/O3Fm24tR`) — needs the v1.5.2 build shipped.
5. **Test-mode purchase** → delivered email → paste key → tier unlocks → close **MON-013** + flip
   **MON-002** to verified.

## Carry items
1. **Push state:** S39 pushed conduital-site `2917faa` + conduital `a1690d7` (webhook hardening + runbook).
   The S39 closeout commit (storage_first hardening + planning + this prompt) should also be pushed —
   confirm `git -C C:/Dev/conduital-site status` and `git status` are clean/synced.
2. **No 1.5.x installer hosted yet (BACKLOG-161).** `/download/latest` still → `ConduitalSetup-1.4.1.exe`
   in `conduital-site/vercel.json`. Build/host the 1.5.2 `.exe`, then bump that redirect target. The
   v1.5.2 build is also what ships the baked PostHog key + new download URL to users.
3. **`backend/.env` may still be `STORAGE_MODE=storage_first`** (S37 carry). Tests are hermetic; set
   back to `legacy` if you don't want live file-sync locally.

## Alternatives (if MON-013 ops are blocked on Greg)
- **Perf: route code-splitting** — bundle is 834 kB (> Vite 500 kB warn). `React.lazy`+`Suspense` on
  `App.tsx` routes. Clean half-session win.
- **Wow-factor polish** — BACKLOG-093 quick-capture animation (S) + BACKLOG-150 Health sparklines (M).
- **Frontend lint backlog** (~18 errors/16 warnings in older pages).
- **DEBT-020** SyncEngine area markdown handling — needs a sync-engine verification pass before closing.

## Read First
```
docs/MON-013-fulfillment-runbook.md          # external-ops checklist (primary)
backlog.md                                    # MON-013 / MON-002 / Stats
task_plan.md, findings.md, progress.md        # plan + findings + session log (S38/S39)
conduital-site/api/stripe-webhook.js          # the function (fail-closed) + test/stripe-webhook.test.mjs
backend/app/sync/entity_markdown.py           # _yaml_safe choke point (handler writes)
```

## Phase 4 — Session Closeout (ritual)
1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q` (hermetic; ~525).
2. Frontend build: `cd frontend && cmd //c "npm run build"`. Site fn tests: `node --test C:/Dev/conduital-site/test/`.
3. Update `backlog.md` (mark pick, refresh Stats). Bump version per scope (**app version ≠ download URL**).
4. Commit (one feat per chunk; closeout commit), then push. **Two repos** if you touch `conduital-site`.
5. Write Session 41 prompt → `next-prompt.md` (MEMORY rule).

## Shell Notes (Windows)
- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Site function tests: `node --test C:/Dev/conduital-site/test/stripe-webhook.test.mjs`
- Other repo git: `git -C C:/Dev/conduital-site <cmd>` (branch `main`; conduital is `master`)
- Probe prod webhook: `curl -sS -X POST https://www.conduital.com/api/stripe-webhook -d "{}"`
