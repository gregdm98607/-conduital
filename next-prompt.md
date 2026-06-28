# Session 42 — recommended next pick

## Current State

Conduital is **software-MVP complete enough for the Windows desktop product**, but the
**distribution/sales MVP is still open**.

Evidence from Session 41 review:
- Source version is **v1.5.2** in `backend/pyproject.toml`, `frontend/package.json`, and `installer/conduital.iss`.
- Local installer outputs stop at `installer/Output/ConduitalSetup-1.4.1.exe`; no 1.5.2 installer is present.
- Public site redirect still maps `/download/latest` to `/downloads/ConduitalSetup-1.4.1.exe`.
- MON-013 Stripe to Resend fulfillment was verified end-to-end in **test mode** during S40.
- Before live buyers go through checkout, Stripe live-mode webhook setup still needs to be repeated.
- Session 41 DNS check found no `_dmarc.conduital.com` TXT record; SPF is currently `v=spf1 include:_spf.mx.cloudflare.net ~all`, and Resend DKIM is present.

## Recommended Pick: Build + Host v1.5.2, Arm Live Stripe, Fix DMARC

### P0.1 — Build the installer
1. Run `build.bat` from `C:\Dev\conduital`.
2. Confirm `installer\Output\ConduitalSetup-1.5.2.exe` exists.
3. Smoke test the installer on the dev machine:
   - install
   - launch
   - setup status
   - app health
   - license activation path

### P0.2 — Host the installer
1. Upload/host `ConduitalSetup-1.5.2.exe` where `conduital-site` serves downloads.
2. Update `C:\Dev\conduital-site\vercel.json`:
   - `/download/v1.5.2` -> `/downloads/ConduitalSetup-1.5.2.exe`
   - `/download/latest` -> `/downloads/ConduitalSetup-1.5.2.exe`
3. Redeploy `conduital-site`.
4. Verify `/download/latest` resolves to 1.5.2.

### P0.3 — Arm live-mode Stripe fulfillment
Repeat **Step 4** of `docs/MON-013-fulfillment-runbook.md` in **Stripe live mode**:
1. Stripe -> live mode -> Developers -> Webhooks -> Add endpoint.
2. URL: `https://www.conduital.com/api/stripe-webhook`.
3. Event: `checkout.session.completed`.
4. Reveal live `whsec_...`.
5. Set `STRIPE_WEBHOOK_SECRET` in Vercel Production scope and redeploy.
6. Verify:
   - `curl -sS -X POST https://www.conduital.com/api/stripe-webhook -d "{}"`
   - Expected: `400 Missing stripe-signature` or equivalent fail-closed response.
   - Bad: `200 unconfigured`.

### P0.4 — Add email authentication before wide dissemination
This is a launch trust/deliverability gate because 1.5.2 purchase fulfillment sends license email from `licenses@conduital.com`.

1. Export/snapshot Cloudflare DNS.
2. Inventory legitimate senders for `conduital.com`:
   - Resend fulfillment (`licenses@conduital.com`)
   - personal/support mailbox sending
   - ConvertKit/newsletter, if it sends as the domain
   - Gumroad/Stripe receipt settings, if either sends as the domain
3. Add a DMARC TXT record at `_dmarc.conduital.com`.
4. Start with reporting/monitoring or quarantine if sender confidence is high; move to `p=reject` after legitimate mail passes.
5. Verify Resend fulfillment email passes aligned DKIM/DMARC.
6. Do **not** blindly change SPF from `~all` to `-all` until every outbound source is included; that can break legitimate mail.

## P1 Confidence Pass

After P0:
- Clean Windows 10 install test.
- Clean Windows 11 install test.
- Upgrade-in-place from installed 1.4.1 to 1.5.2.
- Confirm `%LOCALAPPDATA%\Conduital` data survives upgrade.
- Update `distribution-checklist.md`, `backlog.md`, and `tasks/todo.md` with evidence.

## P2 Product Build After Launch Path

Recommended after P0/P1:
- **R9 / BACKLOG-162 Weekly Review Assistant** — highest paid-tier product value.

Alternatives only if they become risk-driven:
- Route code-splitting if bundle size/perceived startup is hurting distribution.
- Frontend lint cleanup if it blocks confidence.
- DEBT-020 sync-engine area markdown verification.

## Shell Notes

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -q`
- Frontend build: `cd frontend && cmd //c "npm run build"`
- Site function tests: `node --test C:/Dev/conduital-site/test/stripe-webhook.test.mjs`
- Other repo git: `git -C C:/Dev/conduital-site <cmd>` (branch `main`; conduital is `master`)
- Current public redirect file: `C:\Dev\conduital-site\vercel.json`
