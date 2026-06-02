# Findings — S38 / MON-013 Fulfillment + Telemetry

**Date:** 2026-06-02 · Verified by reading source, not by trusting the handoff.

## 1. MON-013 claims — all verified TRUE
| Claim | Verdict | Evidence |
|---|---|---|
| Fulfillment email skipped when key unset | TRUE | `webhooks.py:113-115` returns False + warns |
| `RESEND_API_KEY` unset | TRUE | `config.py:319` → `Optional[str] = None` |
| PostHog dark | TRUE | `config.py:323` → `POSTHOG_WRITE_KEY = None` |
| No deploy config in `conduital` | TRUE | no Dockerfile/Procfile/render/fly/railway/vercel.json |
| Download URL stale (1.4.1) | TRUE | `config.py:320` + `conduital-site/vercel.json` redirects |

## 2. Architecture (the part the handoff understated)
- **`webhooks.py` is part of the DESKTOP backend.** In prod that backend runs only on the
  buyer's `127.0.0.1:52140` (bundled in the .exe). Stripe cannot deliver there. That is *why*
  "no public deploy" exists — there was never meant to be one for the desktop backend.
- **Public site = separate repo `C:\Dev\conduital-site`.** Astro 6.1 static, on Vercel
  (`@vercel/analytics` dep; `vercel.json` redirects). Node >=22.12. No `/api` dir, no SSR adapter.
- `conduital-site/vercel.json` currently only redirects `/download/v1.4.1` and `/download/latest`
  → `/downloads/ConduitalSetup-1.4.1.exe`. The stable **`/download/latest`** indirection is the
  right target for app + email (decouples app version from the URL).

## 3. DECISIVE: app verifies Stripe keys OFFLINE → stateless function is sufficient
- `license.py::activate_license` dispatches by format:
  - 4-group hex → Gumroad (remote `/v2/licenses/verify`)
  - **8-group hex → `_activate_stripe_opaque()` — trusts FORMAT ONLY, no server call**, stores key
    as `purchase_id`, sets `tier=gtd`.
  - `sk_`/`cs_` prefixes → opaque receipt fallback.
- Code rationale (MON-008/Option A): "the webhook fulfillment path is authoritative … exists for
  the buyer who pastes the receipt."
- ⇒ Function needs **no datastore**. Jobs: verify sig → gen 8×8 hex key → Resend email. App unlocks
  offline when buyer pastes the key.
- **Key-format contract:** `_STRIPE_WEBHOOK_KEY_RE = ^(?:[0-9A-Fa-f]{8}-){7}[0-9A-Fa-f]{8}$`.
  Python gen = `secrets.token_hex(32).upper()` grouped 8×8.
  JS equiv = `crypto.randomBytes(32).toString('hex').toUpperCase()` grouped 8×8.

## 4. Known limitations (pre-existing — NOT expanded this session)
- **Offline key forgeability:** anyone who knows the 8×8 format can self-issue a "valid" key
  (format-only trust). Deliberate MON-008 tradeoff for a desktop app. Flag, don't fix here.
- **Tier ceiling:** `_activate_stripe_opaque` always grants `gtd` regardless of purchase
  ("only paid Stripe tier today"). If GTD+/full is sold via Stripe, a pasted key under-grants.
  Note in runbook.

## 5. PostHog
- Key: `phc_ygx9UwhNNRCrQPhx98zeBuTcezc3W5zr3sMrMiEV3Cm8`, host `https://us.i.posthog.com`
  (already correct in `telemetry_service.py`). `phc_` = publishable client key → safe to bake as default.

## 6. Stale planning artifacts
- Root `task_plan.md`/`findings.md`/`progress.md` were from v1.1.0 S12-14 (Feb 2026) — abandoned
  (we're at v1.5.1). Refreshed for S38. Canonical tracking stays `backlog.md` + `next-prompt.md` + vault.
