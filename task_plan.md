# Task Plan — Session 41: MVP Progress Review + Next Steps

**Status:** COMPLETE — review performed and planning artifacts refreshed
**Date:** 2026-06-27
**Goal:** Review current Conduital progress against MVP readiness, reconcile stale planning context, and update recommended next steps.

---

## Current MVP Read

Conduital's **software MVP is functionally past the original Windows desktop MVP bar**:
- Core desktop app, setup wizard, packaged runtime architecture, installer script, local data directory, markdown sync, modules, licensing UI, telemetry plumbing, feedback loop, onboarding templates, and paid-tier activation flows are built.
- R5 monetization launch blockers are marked done in `backlog.md`; MON-013 Stripe to Resend fulfillment was verified end-to-end in S40 test mode.
- Dev source is at **v1.5.2**.

Conduital's **distributable/sales MVP is not yet fully live**:
- Latest hosted installer still points to **v1.4.1** (`conduital-site/vercel.json` redirects `/download/latest` to `ConduitalSetup-1.4.1.exe`).
- Local installer outputs show no `ConduitalSetup-1.5.2.exe` yet.
- Stripe production/live-mode webhook registration still needs to be repeated before real buyers go through live checkout.
- Clean VM testing and signed-installer work remain the main distribution confidence gaps.

## Recommended Next Steps

### P0 — Ship the current build to users
- Build `ConduitalSetup-1.5.2.exe` with `build.bat`.
- Smoke test install/launch/activation on the dev machine.
- Upload/host the 1.5.2 installer.
- Update `conduital-site/vercel.json` so `/download/latest` targets the 1.5.2 installer, then redeploy the site.

### P0 — Arm live purchases
- Repeat `docs/MON-013-fulfillment-runbook.md` Step 4 in Stripe **live mode**.
- Set the live `STRIPE_WEBHOOK_SECRET` in Vercel Production scope.
- Redeploy and verify the endpoint fails closed on unsigned input (`400`, not `unconfigured`).

### P1 — Distribution confidence pass
- Run clean Windows 10 and Windows 11 install tests against the 1.5.2 installer.
- Verify upgrade-in-place from the currently hosted 1.4.1 installer preserves `%LOCALAPPDATA%\Conduital`.
- Capture any installer/runtime issues in `backlog.md` before starting the next feature release.

### P2 — Choose the next product swing
- After P0/P1, start **R9 / BACKLOG-162 Weekly Review Assistant** if the goal is paid-tier product value.
- Choose route code-splitting first only if bundle size/perceived startup becomes a near-term sales/support concern.
- Keep DEBT-020 open until a sync-engine verification pass produces evidence.

---

## Phases

### Phase 1 — Restore planning context ✅ COMPLETE
- Read root `task_plan.md`, `findings.md`, `progress.md`, `backlog.md`, and `next-prompt.md`.
- Checked `tasks/` planning artifacts and confirmed `tasks/todo.md` was missing.

### Phase 2 — Compare against MVP evidence ✅ COMPLETE
- Verified MON-013 is closed in `backlog.md` and `next-prompt.md`.
- Verified dev version is 1.5.2 in `backend/pyproject.toml`, `frontend/package.json`, and `installer/conduital.iss`.
- Verified local installer outputs stop at `ConduitalSetup-1.4.1.exe`; no 1.5.2 installer exists yet.
- Verified public site redirect still serves `ConduitalSetup-1.4.1.exe`.

### Phase 3 — Update planning artifacts ✅ COMPLETE
- Replaced stale S38 launch-blocker plan with this MVP review plan.
- Updated `findings.md`, `progress.md`, `tasks/todo.md`, `next-prompt.md`, `backlog.md`, and `distribution-checklist.md`.

### Phase 4 — Closeout ✅ COMPLETE
- No product tests run; this was a planning/review-only task.
- Verification was document/state inspection via repository files and git status.

## Decisions

- Treat **MVP software scope** and **MVP distribution readiness** as separate gates.
- Do not start R9 until the 1.5.2 installer and live-mode webhook are handled, unless explicitly choosing feature development over launch readiness.
- Keep signing as recommended but not a hard alpha blocker; clean VM and upgrade tests are more immediate risk reducers.

## Errors Encountered

None.
