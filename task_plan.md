# Task Plan — Session 38: MON-013 Launch Blocker (Stripe→Resend Fulfillment + Telemetry)

**Status:** PLAN — awaiting go-ahead before implementation
**Date:** 2026-06-02
**Goal:** Make paid-purchase fulfillment actually work in production — a real Stripe
purchase issues a license key and emails it to the buyer; PostHog telemetry goes live.
Build **all in-repo code** this session; hand off the external-only steps
(DNS, dashboards, secrets, real test purchase) as a precise runbook.

**Decisions locked (2026-06-02, via AskUserQuestion):**
- Session pick: **MON-013 — code + runbook** (Harden `storage_first` deferred to alternative).
- Deploy target: **Vercel serverless function beside the site** (not a full-backend host).

---

## Key architecture findings (detail in findings.md)
- `backend/app/api/webhooks.py` lives in the **desktop backend** → in prod it runs only on
  the buyer's `127.0.0.1:52140` → **Stripe can never reach it**. Fulfillment must relocate.
- Public site = **separate repo `C:\Dev\conduital-site`** (Astro 6, static, on Vercel).
  Add a **native Vercel function `api/stripe-webhook.js`** — served beside the static build,
  zero Astro changes, **zero new npm deps** (Node 22 `crypto` + global `fetch`).
- **App accepts Stripe keys OFFLINE** (`license.py::_activate_stripe_opaque`, MON-008/Option A):
  an 8×8-hex key is trusted by format with no server round-trip ⇒ **function is stateless**
  (verify sig → gen key → email). No DB/KV.

## Scope split (two repos)
- **conduital-site** (NEW code): `api/stripe-webhook.js` + `.env.example` + `node --test` tests.
- **conduital** (config + docs + tests): PostHog key, download URL, webhooks.py prod-note,
  cross-repo contract test, runbook, backlog, version bump, S39 prompt.

---

## Phases

### Phase 0 — Discovery & decision ✅ COMPLETE
- Verified all MON-013 claims against source; located site repo; confirmed offline-key model.

### Phase 1 — Serverless fulfillment function (conduital-site) ✅ COMPLETE
- [x] `api/stripe-webhook.js`: Web-signature `POST(request)`; raw body via `await request.text()`;
      HMAC-SHA256 sig verify w/ 5-min replay window (+multi-v1); `checkout.session.completed` only
      (200 otherwise); tier from metadata/price-id; 8×8 hex key gen (matches `_STRIPE_WEBHOOK_KEY_RE`);
      Resend email (ported HTML/text + dynamic URL/tier); never logs the key; email failure stays 200
      (no retry → no duplicate keys). Pure helpers exported for tests. **Zero deps** (node:crypto + fetch).
- [x] `.env.example` + README section: all six env vars documented (defaults: stable `/download/latest`
      URL, `Conduital <licenses@conduital.com>` sender).
- [x] Tests at **`test/stripe-webhook.test.mjs`** (NOT `/api/` — every `/api` file is a public endpoint).
      `npm test` → `node --test test/`. **20/20 pass.** Covers: sig valid/tampered/expired/multi-v1/missing;
      key-format contract (×200) + deterministic RNG; tier resolution; email build; send (skip/200/non-2xx);
      end-to-end fulfillment (sent / no-email / resend-failure); env defaults.
- Verified Vercel contract via docs: non-Next `/api/*.js` web functions supported; `node:crypto` ⇒ Node runtime.

### Phase 2 — Desktop-app config + contract (conduital) ✅ COMPLETE
- [x] `config.py`: `POSTHOG_WRITE_KEY` default = `phc_ygx9…` (publishable client key — safe to bake, +comment);
      `CONDUITAL_DOWNLOAD_URL` → stable `https://conduital.com/download/latest` (+comment).
- [x] `webhooks.py`: PRODUCTION-NOTE docstring → canonical fulfillment is the Vercel function; local
      handler retained as reference/dev only.
- [x] `backend/.env.example`: added Telemetry (PostHog) section + Stripe/Resend "legacy local webhook only" note.
- [x] Cross-repo contract test: `test_license_api.py::TestStripeWebhookKeyContract` (4 tests) — regex matches
      canonical/lowercase, **reference generator output always matches validator (×100)**, rejects Gumroad/near-misses,
      generated key activates `gtd` via the real endpoint. **26/26 pass in test_license_api.py.**
- [x] Frontend PostHog: NO change needed — `frontend/src/services/telemetry.ts` forwards events to the backend,
      which forwards to PostHog. Only the backend key matters (wired at `main.py:187-188`).

### Phase 3 — Runbook ✅ COMPLETE
- [x] `docs/MON-013-fulfillment-runbook.md` — deploy (git/CLI) + endpoint verify curl; Vercel env table;
      Resend domain+DNS (**Cloudflare snapshot-first**) + sender; Stripe endpoint + signing secret + metadata;
      PostHog verify; test-mode E2E; close-out w/ evidence; known limitations; troubleshooting table.

### Phase 4 — Verify + closeout ✅ COMPLETE (commits in progress)
- [x] Verify: site `node --test` 20/20; frontend build clean (tsc+vite, 2080 modules); backend pytest
      **518 pass / 1 skip** (519 total, +4 contract tests). No telemetry tests → baked PostHog key safe.
- [x] backlog.md: MON-013 → code-complete/blocked-on-external + MON-002 note + callout rewrite; Stats refreshed.
- [x] Version bump 1.5.1 → 1.5.2 via pyproject + `sync_version.py` (package.json, conduital.iss, config fallback); `--check` ok.
- [x] Wrote S39 `next-prompt.md` (primary pick = drive the MON-013 runbook ops to done).
- [~] Commit conduital + conduital-site (per user go). **Push held** unless requested.

---

## Out of scope (flagged, not done)
- Building/hosting the 1.5.x `.exe` (BACKLOG-161 dance) — runbook references it.
- Real Stripe purchase / DNS edits / Resend dashboard / secret provisioning — human-only (runbook).
- Tier > gtd via Stripe (app forces `gtd` on opaque keys) — known limitation, noted.
- Offline-key forgeability (format-only trust) — pre-existing MON-008 decision, not expanded here.

## Risks
| Risk | Mitigation |
|---|---|
| Function lives in 2nd repo I can't deploy | Runbook + I verify build/tests locally |
| Stripe needs the raw body for sig verify | Disable body parser; read raw stream |
| Wrong key format → app rejects pasted key | Contract test pins 8×8 hex on both sides |
| Baking PostHog key into config | It's a publishable client key (safe); confirmed in runbook |
| DNS change risk | Snapshot-first instruction (2026-04-18 incident) |

*Plan created 2026-06-02 (S38). Replaces stale v1.1.0/S14 plan.*
