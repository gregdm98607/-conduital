# Findings — Session 41 MVP Progress Review

**Date:** 2026-06-27

## Summary

Conduital is **feature-complete enough for the original Windows desktop MVP**, but it is **not yet fully launch-ready for real buyers** because the newest source build has not been packaged/hosted and Stripe live-mode fulfillment still needs to be armed.

## Evidence

| Area | Finding | Evidence |
|---|---|---|
| Monetization blockers | R5 must-have launch blockers are closed except live-mode checkout wiring caveat. | `backlog.md` MON-001 through MON-013; MON-013 evidence from S40 test purchase. |
| Stripe fulfillment | Test-mode Stripe to Resend to app activation was verified end-to-end. | `backlog.md` MON-013: test checkout, delivered email, key activated as GTD. |
| Live sales readiness | Live-mode Stripe webhook still needs to be repeated before real buyers. | `next-prompt.md` warning; MON-013 note in `backlog.md`. |
| Current source version | Dev source is v1.5.2. | `backend/pyproject.toml`, `frontend/package.json`, `installer/conduital.iss`. |
| Hosted/latest installer | Public download redirect still points to v1.4.1. | `C:\Dev\conduital-site\vercel.json`: `/download/latest` -> `/downloads/ConduitalSetup-1.4.1.exe`. |
| Local build artifacts | No local 1.5.2 installer output exists yet. | `installer/Output` contains installers through `ConduitalSetup-1.4.1.exe`; `backend/dist/Conduital/Conduital.exe` timestamp is 2026-05-11. |
| Email authentication | `conduital.com` has no DMARC record; SPF is softfail; Resend DKIM is present. Treat DMARC as a pre-dissemination launch gate. | DNS checks on 2026-06-27: `_dmarc.conduital.com` absent; SPF `v=spf1 include:_spf.mx.cloudflare.net ~all`; `resend._domainkey.conduital.com` has a DKIM TXT key. |
| Repo cleanliness | Main repo is synced with origin; only `AGENTS.md` is untracked. | `git status --short --branch`: `## master...origin/master`, `?? AGENTS.md`. |
| Site repo cleanliness | Site repo is synced with origin. | `git -C C:\Dev\conduital-site status --short --branch`: `## main...origin/main`. |

## MVP Position

### Built
- Core project/task system, modules, setup wizard, local-first packaging architecture.
- Markdown/file sync UX, conflict UI, and storage hardening.
- License activation UI, trial expiry UX, telemetry plumbing, feedback widget/admin view.
- Stripe/Gumroad activation paths and PostHog/Resend production plumbing.
- Starter templates/onboarding value for new users.

### Still Needed Before Real-Buyer MVP
- Package v1.5.2 and host it as `/download/latest`.
- Register/set Stripe webhook secret in live mode.
- Publish and verify DMARC for `conduital.com`; do not hardfail SPF until all legitimate outbound senders are known.
- Run clean Windows 10/11 installer tests and at least one upgrade-in-place test from v1.4.1 to v1.5.2.
- Decide whether unsigned installer warnings are acceptable for alpha, or purchase/sign before broader paid distribution.

## Recommendation

Do not start R9 by default. First close the distribution gap:
1. Build and smoke-test `ConduitalSetup-1.5.2.exe`.
2. Upload/host it and update the public redirect.
3. Arm Stripe live-mode fulfillment.
4. Add DMARC and verify Resend fulfillment passes aligned authentication.
5. Run clean VM plus upgrade tests.

After that, the strongest product next step is R9 / BACKLOG-162 Weekly Review Assistant.

## Historical Context

S38 identified the original MON-013 launch blocker: fulfillment lived in the desktop backend, which Stripe could not reach. S38 relocated fulfillment to a Vercel function; S39 verified and hardened it; S40 completed the test-mode end-to-end purchase and activation path.
