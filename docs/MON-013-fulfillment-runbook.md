# MON-013 — Fulfillment + Telemetry Runbook (Stripe → Resend, PostHog)

**Status:** code complete (S38, 2026-06-02). This runbook covers the **external steps that
must be done by a human** (dashboards, DNS, secrets, a real test purchase) to make paid-purchase
fulfillment actually deliver a license key in production.

> **TL;DR of the architecture.** The Stripe webhook handler in the *desktop* backend
> (`backend/app/api/webhooks.py`) can never be reached by Stripe — it only runs on the buyer's
> `127.0.0.1`. Production fulfillment is a **standalone Vercel function beside the marketing site**:
> `conduital-site/api/stripe-webhook.js` → `POST https://conduital.com/api/stripe-webhook`.
> It is **stateless**: verify Stripe signature → generate an 8×8-hex key → email it via Resend.
> The desktop app activates that key **offline** (no server call), so no database is involved.

---

## What is already done (code — S38)
- ✅ `conduital-site/api/stripe-webhook.js` — the function (zero deps; `npm test` green).
- ✅ `conduital-site/.env.example` — documents the six env vars.
- ✅ `backend/app/core/config.py` — PostHog prod key baked in; `CONDUITAL_DOWNLOAD_URL` → stable
  `https://conduital.com/download/latest` redirect.
- ✅ Key-format contract pinned by tests on both sides (Python `test_license_api.py`
  `TestStripeWebhookKeyContract`; JS `test/stripe-webhook.test.mjs`).

## What this runbook covers (human-only)
1. Deploy the function to Vercel
2. Set Vercel environment variables
3. Verify the Resend domain + sender (DNS)
4. Register the Stripe webhook endpoint
5. Confirm PostHog telemetry
6. End-to-end test purchase
7. Close MON-013 with evidence

---

## Prerequisites
- Access to: **Vercel** (conduital-site project), **Stripe** dashboard, **Resend** dashboard,
  **Cloudflare** (DNS for conduital.com).
- `RESEND_API_KEY` already exists in the vault: **Silver_Sage_Media → Account Information**.
- Vercel CLI if deploying from the terminal: `npm i -g vercel` (only if conduital-site isn't
  already git-connected to Vercel).

---

## Step 1 — Deploy the function

The function auto-deploys from the `api/` directory — no Astro/adapter changes needed.

**If `conduital-site` is git-connected to Vercel (most likely):**
```
cd C:\Dev\conduital-site
git add api/stripe-webhook.js .env.example test/ package.json README.md
git commit -m "feat: Stripe→Resend fulfillment serverless function (MON-013)"
git push           # Vercel builds + deploys automatically
```

**If not connected, deploy with the CLI:**
```
cd C:\Dev\conduital-site
vercel --prod
```

**Verify the endpoint is live.** The apex domain 307-redirects to `www`, so hit the canonical host
(or `curl -L`). The function is **fail-closed**, so the response tells you whether the secret is set:
```
curl -i -X POST https://www.conduital.com/api/stripe-webhook -H "content-type: application/json" -d "{}"
# BEFORE the secret is set:  HTTP 200  {"status":"unconfigured"}
#   → live, but fail-closed: it refuses to fulfill until STRIPE_WEBHOOK_SECRET is set. This is your
#     "secret not set yet" signal.
# AFTER the secret is set, an unsigned request:  HTTP 400  {"error":"Missing stripe-signature header"}
# A 404 means the function is not deployed.
```

---

## Step 2 — Set Vercel environment variables
Vercel → conduital-site → **Settings → Environment Variables** (Production scope). Add:

| Variable | Value | Notes |
|---|---|---|
| `RESEND_API_KEY` | `re_…` | From vault → Silver_Sage_Media → Account Information. **Never commit.** |
| `STRIPE_WEBHOOK_SECRET` | `whsec_…` | From Step 4 (set after creating the Stripe endpoint). |
| `CONDUITAL_DOWNLOAD_URL` | `https://conduital.com/download/latest` | Optional; this is the default. |
| `RESEND_FROM` | `Conduital <licenses@conduital.com>` | Optional; this is the default. |
| `STRIPE_GTD_PRICE_ID` | `price_…` | Optional; only if you use price-id → tier mapping instead of metadata. |
| `STRIPE_FULL_PRICE_ID` | `price_…` | Optional. |

**Redeploy** after changing env vars (Vercel does not apply them to existing deployments).

> **Security — the signing secret is mandatory.** The function is **fail-closed**: with no
> `STRIPE_WEBHOOK_SECRET` it returns `{"status":"unconfigured"}` and fulfills nothing. So adding
> `RESEND_API_KEY` alone can never make it an open "email a key to anyone" relay — but it also means
> **no fulfillment happens until `STRIPE_WEBHOOK_SECRET` is set** (Step 4). Set both before going live.

---

## Step 3 — Verify the Resend domain + sender (DNS)

> ⚠️ **DNS is snapshot-first (2026-04-18 incident).** Before touching Cloudflare, export the
> conduital.com zone file (Cloudflare → DNS → Records → **Export**) and save it. Then proceed.

1. Resend → **Domains → Add Domain** → `conduital.com`.
2. Resend shows DKIM / SPF / (optional) DMARC records. Add each to **Cloudflare** exactly as shown
   (type, name, value). Leave proxy **off** (DNS-only / grey cloud) for mail records.
3. Back in Resend, click **Verify**. Wait for all records to go green (can take minutes to ~an hour).
4. Confirm the sender `licenses@conduital.com` is usable under the verified domain.

Until the domain is verified, Resend will reject sends and buyers get no email.

---

## Step 4 — Register the Stripe webhook endpoint
1. Stripe → **Developers → Webhooks → Add endpoint**.
2. Endpoint URL: `https://conduital.com/api/stripe-webhook`
3. Events to send: **`checkout.session.completed`** (only).
4. Create, then **reveal the Signing secret** (`whsec_…`) → put it in Vercel as
   `STRIPE_WEBHOOK_SECRET` (Step 2) → **redeploy**.
5. Make sure checkout sets the tier. Easiest: set **`metadata.conduital_tier`** to `gtd` (or `full`)
   on the Checkout Session / Payment Link. Otherwise set `STRIPE_GTD_PRICE_ID` / `STRIPE_FULL_PRICE_ID`
   so the price id maps to a tier. With neither, the function defaults to `gtd`.

> Do this in **test mode** first (test-mode endpoint + test signing secret), validate end-to-end,
> then repeat for live mode.

---

## Step 5 — Confirm PostHog telemetry
- The production write key (`phc_…`, publishable/send-only) is baked into `config.py` and ships in
  the build. **Existing installs won't emit until they update to the v1.5.2 rebuild** (BACKLOG-161).
- After a build is running, confirm events arrive: PostHog → Activity, and the funnel
  `/insights/O3Fm24tR` should begin populating.
- To disable telemetry for a build: set `ANALYTICS_ENABLED=false`.

---

## Step 6 — End-to-end test (test mode)
1. Trigger a **test-mode** checkout for Conduital (Payment Link or a test Checkout Session).
2. Complete payment with a Stripe test card (`4242 4242 4242 4242`, any future expiry/CVC).
3. **Stripe → Webhooks** shows the delivery to `/api/stripe-webhook` returning **200** with
   `{"status":"fulfilled","tier":"gtd","email_sent":"true"}`.
4. **Resend → Emails** shows a **Delivered** message to the buyer address.
5. Open the email → copy the key (format `XXXXXXXX-…` 8 groups) → in the app:
   **Settings → License → paste → Activate**. The tier unlocks (gtd).
6. (Optional) `GET /api/v1/license/status` in the app shows `is_paid: true`, `tier: gtd`.

If all six hold in test mode, repeat Steps 2/4 for **live mode** (live `whsec_`, live price/links).

---

## Step 7 — Close out
- Mark **MON-013 Done** in `backlog.md` with evidence (Stripe 200 screenshot, Resend Delivered,
  successful in-app activation).
- Update **MON-002** from "UNVERIFIED IN PROD" → verified.
- File the evidence to the vault handoff:
  `C-Suite/CTO/CTO_Conduital_Telemetry_StandUp_PostHog_Resend_2026-06-01.md`.

---

## Known limitations (by design — flagged, not fixed this session)
- **Offline key forgeability.** The app trusts any correctly-formatted 8×8-hex key without a server
  check (MON-008 / Option A). Anyone who knows the format can self-issue a key. Accepted tradeoff for
  an offline desktop app; revisit only if piracy becomes material (would require server-side key
  verification + a durable issued-key store).
- **Tier ceiling.** Opaque Stripe keys always activate **gtd** (`license.py::_activate_stripe_opaque`).
  If you ever sell a **GTD+/full** tier via Stripe, a pasted key under-grants — you'd need to extend
  the activation path to carry tier (e.g., signed key or server lookup).
- **Download URL redirect.** `/download/latest` currently points at `ConduitalSetup-1.4.1.exe` in
  `conduital-site/vercel.json`. **Bump that redirect target** when the 1.5.x installer is hosted
  (BACKLOG-161) — no app rebuild needed for the URL itself.

## Troubleshooting
| Symptom | Likely cause / fix |
|---|---|
| 200 `{"status":"unconfigured"}` | Fail-closed: `STRIPE_WEBHOOK_SECRET` not set on Vercel. Set it (Step 4) + redeploy. |
| Stripe shows 400 on delivery | Signature mismatch → `STRIPE_WEBHOOK_SECRET` wrong or not redeployed; ensure raw body (already handled). |
| 200 but `email_sent:"false"` | `RESEND_API_KEY` unset on Vercel, or buyer email missing on the session. |
| Email sent but not delivered | Resend domain/sender not verified (Step 3), or in spam — check Resend logs. |
| 404 on the endpoint | Function not deployed, or wrong path — must be `/api/stripe-webhook`. |
| Buyer "invalid key" in app | Key format drift — run `npm test` (site) + `pytest test_license_api.py` (app); both pin the regex. |
