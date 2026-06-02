# Conduital — Release-Based Backlog

> **R8 selection (S36):** **Starter Templates by Persona** (BACKLOG-087)
> — **Done** in S36 (v1.5.0). New `/templates` gallery + `TemplateService`
> apply 3 persona scaffolds (Writer / Knowledge Worker / Engineer): one click
> creates areas + projects (with phases via the now-activated `PhaseTemplate`
> model) + starter next actions, each with a live momentum score. Discoverable
> from the Projects empty state and the sidebar. `template_previewed` /
> `template_applied` telemetry added; +10 backend tests (509 total).
> **S37 (v1.5.1):** BACKLOG-160 sidebar license badge **shipped**. The session also
> fixed two pre-existing storage bugs surfaced by the test run: non-hermetic tests
> (a `storage_first` setting in the live `.env` made tests write to the real vault)
> and a `storage_first` enum-serialization bug that 500'd project creation. See
> `tasks/lessons.md` (2026-05-31) and `next-prompt.md` carry items (incl. real-DB
> propagation to verify).

> **🚨 LAUNCH BLOCKER (logged 2026-06-01, CTO) — S38 (2026-06-02): CODE COMPLETE; external ops remain.**
> Root cause: the Stripe→Resend fulfillment handler lived only in the **desktop** backend
> (`backend/app/api/webhooks.py`) — in prod it runs on the buyer's `127.0.0.1`, which Stripe can never
> reach; `RESEND_API_KEY` was unset; the Resend domain was unverified; PostHog was dark.
> **S38 shipped the code fix:** fulfillment relocated to a **stateless Vercel function beside the site**
> (`conduital-site/api/stripe-webhook.js`, 20 `node --test`); PostHog prod key wired into `config.py`;
> `CONDUITAL_DOWNLOAD_URL` → stable `/download/latest`; key-format contract pinned on both sides.
> **Remaining = human-only ops:** deploy the function, set Vercel env (incl. `RESEND_API_KEY` from vault
> *Silver_Sage_Media → Account Information*), verify Resend DNS (**snapshot-first**, 2026-04-18 incident),
> register the Stripe endpoint, run a test purchase. Step-by-step: **`docs/MON-013-fulfillment-runbook.md`**.
> See **MON-013** and vault `C-Suite/CTO/CTO_Conduital_Telemetry_StandUp_PostHog_Resend_2026-06-01.md`.

This backlog is organized by commercial release milestones. Each release builds on the previous, enabling incremental delivery.

**Module System:** See `backend/MODULE_SYSTEM.md` for technical details.
**Archive:** Full history in `backlog-archive-2026-02-12.md`

---

## Release Overview

| Release | Modules | Target Audience | Status |
|---------|---------|-----------------|--------|
| **R1: Conduital Basic** | `core` + `projects` | Project managers, individuals | **v1.0.0-alpha shipped** (2026-02-08) |
| **R1.1: Conduital Beta** | `core` + `projects` | Project managers, individuals | **v1.0.0-beta shipped** (2026-02-09) |
| **R2: Conduital GTD** | + `gtd_inbox` | GTD practitioners | **v1.2.0 shipped** — module wired, InboxPage live, weekly review + waiting-for + someday-maybe routes active |
| **R3: Proactive Assistant** | + `memory_layer` + `ai_context` | AI-augmented users | Memory Layer admin shipped (v1.2.0); AI Context modules deferred |
| **R4: Full Suite** | All modules | Power users | Default `COMMERCIAL_MODE=full` since v1.2.0 |
| **R5: Monetization** | License + Telemetry + Feedback | Paying users | **v1.3.3 shipped** — Gumroad activation; Stripe webhook + Stripe inline activation (opaque receipt); PostHog frontend wired; trial expiry banners; in-app feedback widget + admin view. R5 Must-Have backlog clean. |
| **R6: File Sync UX** | + sync broadcaster + conflict-resolution UI | Multi-device users | **v1.4.0 shipped** (S34) — BACKLOG-153 Phase 2 (Conflicts tab in `SyncDetailsPanel` + `useSyncConflicts` hook + `POST /sync/resolve/{id}`); shared `SyncEventList` renderer; Settings → Recent Sync Activity subsection. |
| **R7: Paid-Tier Activation Flow** | + welcome modal + license event bus | Paying users | **v1.4.1 shipped** (S35) — BACKLOG-159 `WelcomePaidTierModal` mounted in `Layout`; `conduital:license-activated` event dispatched on free→paid; per-tier unlock list; `welcome_paid_tier` telemetry; BACKLOG-161 public download URL hosted on conduital.com; DEBT-078 closed. |
| **R8: Onboarding Templates** | + starter template gallery | New users | **v1.5.0 shipped** (S36) — BACKLOG-087 persona starter templates: `/templates` gallery + `TemplateService.apply_template`; activates the `PhaseTemplate` model; creates areas + projects (phases) + next actions with live momentum; empty-state + sidebar discovery. |
| **R9: Weekly Review Assistant** | + guided weekly-review workflow | GTD-tier solopreneurs | **Spec APPROVED 2026-05-19 — not yet built.** BACKLOG-162; spec at `Silver_Sage_Software\C-Suite\CPO\Specs\Conduital_Weekly_Review_Spec_Draft.md`; M (2–3 wk) sizing; impl window 2026-05-25→06-08; **target v1.6.0** (CPO spec labeled v1.4.0 — that version shipped as R6 File Sync UX; CTO retargeted to next minor after v1.5.1). |

---

## R1.1: Conduital Beta — Remaining

### Should Have (Deferred)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-076 | **List View Design Standard** | **Done** (S12) | SortableHeader/StaticHeader components, wired in Projects + AllTasks pages |
| DOC-005 | **Module System Documentation** | **Retired** (2026-05-31 grooming B2) | Covered by `backend/MODULE_SYSTEM.md`; no customer-signal demand across launch-week reviews. Re-introduce only if a signal surfaces module-system confusion. |

---

## R5: Monetization — Active

This block tracks the v1.3.x monetization workstream and what remains for v1.4.

### Must Have (Launch Blocking)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| MON-001 | Gumroad license activation | **Done** (v1.3.0) | `POST /api/v1/license/activate` — UUID key format, /v2/licenses/verify call, 8HEX-8HEX-8HEX-8HEX strict regex |
| MON-002 | Stripe webhook fulfillment | **Done (code) — ⚠️ UNVERIFIED IN PROD** | `POST /api/v1/webhooks/stripe` — checkout.session.completed → key gen → Resend email. **2026-06-01 (CTO):** code present but no public deploy + `RESEND_API_KEY` unset → email not delivered in prod. **S38 (2026-06-02):** fulfillment relocated to the public Vercel function (see **MON-013**); this local handler retained as dev/reference. Prod delivery still pending the external deploy/DNS steps. |
| MON-003 | Trial system + daily expiry job | **Done** (v1.3.0) | 3AM scheduler downgrades expired trials |
| MON-004 | Settings → License panel | **Done** (v1.3.0) | Tier badge, key entry, activate button, inline feedback |
| MON-005 | App-level gate-hit handling | **Done** (v1.3.0) | 403 → toast + redirect to Settings |
| MON-006 | Feature gating per tier | **Done** (v1.3.0) | `is_module_allowed_for_tier()` enforces license boundaries |
| MON-007 | In-app feedback widget | **Done** (2026-04-26) | `FeedbackWidget.tsx` + `POST /api/v1/feedback` + SQLite `feedback` table |
| MON-008 | Stripe inline `/license/activate` | **Done** (v1.3.3, S32) | Removed 503. `sk_live_*`/`sk_test_*`/`cs_live_*`/`cs_test_*` and the 8-group hex webhook key all activate inline as opaque receipts (Option A). Webhook remains authoritative; inline path is the buyer-pasted-receipt fallback. Idempotent. |
| MON-009 | PostHog frontend wiring | **Done** (v1.3.2, S31) | `frontend/src/services/telemetry.ts` singleton (batch 10/5s, distinct_id cache, opt-out, sendBeacon flush). Wired: `app_first_launch`, `app_launched`, `license_activated`, `gate_hit_<module>`, `feedback_submitted`, `trial_day_7/11/13_*`. Settings → Privacy toggle. |
| MON-010 | Trial expiry banners (Day 7/11/13) | **Done** (v1.3.2, S31) | `useTrialStatus` hook + `TrialBanner` component. Day-7 amber sticky, Day-11 red sticky, Day-13 blocking modal with extension request. Per-session dismissal via sessionStorage. |
| MON-011 | Feedback admin view | **Done** (v1.3.3, S32) | Settings → Feedback section: filter chips (All / Bug / Feature / General / Unresolved), inline expand, resolve checkbox (PATCH `/feedback/{id}`), CSV export. New `resolved` column on `feedback` table (Alembic 018). |
| MON-012 | Auth-mode license activation | Deferred | Returns 501. Single-user desktop is the only supported path; multi-user is post-R4. |
| MON-013 | **🚨 Stripe→Resend fulfillment broken in prod (license email not delivered)** | **Code complete (S38, 2026-06-02) — blocked on external ops** | Root cause: handler lived only in the desktop backend (localhost → Stripe unreachable); `RESEND_API_KEY` unset; Resend domain unverified; PostHog dark. **S38 fix (code, all unit-verified):** stateless **Vercel function** `conduital-site/api/stripe-webhook.js` (verify sig → gen 8×8 key → Resend email; 20 `node --test`); PostHog prod key baked into `config.py` (publishable, send-only); `CONDUITAL_DOWNLOAD_URL` → stable `/download/latest`; `webhooks.py` prod-note; cross-repo key-format contract test (`test_license_api.py::TestStripeWebhookKeyContract`). **Remaining (human-only — `docs/MON-013-fulfillment-runbook.md`):** deploy function; set Vercel env (`RESEND_API_KEY` from vault *Account Information*); verify Resend DNS (snapshot-first, 2026-04-18); register Stripe endpoint + signing secret; test-mode purchase. **DoD:** real Stripe test purchase → delivered Resend email with a working key + correct download URL. |

---

## R3: Proactive Assistant — Open Items

### Should Have (Quality Bar)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-087 | Starter Templates by Persona | **Done** (S36, v1.5.0) | 3 personas (Writer / Knowledge Worker / Engineer); `/templates` gallery + `TemplateService.apply_template`; one-click areas + projects (phases) + next actions w/ live momentum; activates `PhaseTemplate` model |
| BACKLOG-082 | Session Summary Capture | **Done** (S20) | End-of-session memory updates — structured capture form, Sessions tab, auto-namespace |
| DOC-006 | Memory Layer API Documentation | Open | Developer docs |
| DOC-007 | AI Context API Documentation | Open | Developer docs |

### Nice to Have (Polish)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-089 | Memory Namespace Management UI | **Done** (S18) | Power users |
| BACKLOG-088 | Prefetch Rule Configuration UI | **Done** (S18) | Power users |
| BACKLOG-083 | Progress Dashboard (Memory) | **Done** (S19) | System health metrics — `/memory/stats` endpoint + Health tab |
| BACKLOG-085 | Memory Diff View | Open | Session continuity |

---

## R4: Full Suite — Open Items

### Should Have (Quality Bar)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-049 | Project Workload Indicator | Open | Capacity warnings |
| BACKLOG-050 | Project Blocked/Waiting Status | Open | External dependency tracking |
| BACKLOG-062 | Project Standard of Excellence | Open | Mirror area-level feature |

### Nice to Have (Future)

> **Deferred to post-R4 / v2 evaluation; not on the current roadmap (2026-05-31 grooming B7).** IDs preserved for reactivation by a specific decision.

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-001 | Sub-Projects | Open | Hierarchical organization |
| BACKLOG-056 | Project Dependencies | Open | Project-to-project tracking |
| BACKLOG-046 | Project Completion Criteria Checklist | Open | Explicit "done" definition |
| BACKLOG-051 | Project Type Classification | Open | Standard, multi_phase, ongoing, etc. |
| BACKLOG-052 | Project Cloning/Templates UI | Open | Clone and template browser |
| BACKLOG-055 | Project Time Investment Tracking | Open | Hours estimation and logging |
| BACKLOG-057 | Project Archive with History | Open | Lessons learned, retrospectives |
| BACKLOG-060 | Delegation/Accountability Tracking | Open | Multi-user foundation |

---

## R9: Weekly Review Assistant — Spec Approved (target v1.6.0)

Spec **APPROVED 2026-05-19** — all four gates closed: CTO M-sizing ✅ 5/14, CEO conditional ✅ 5/14, CRO §6/§8 tier-gating ✅ 5/14, CTO Gate 4 backlog mutation = this entry (✅ 2026-05-31). Source spec: `Silver_Sage_Software\C-Suite\CPO\Specs\Conduital_Weekly_Review_Spec_Draft.md`. Dispatched by SSS CPO 2026-05-19 (Gate 4 dispatch + `CPO/Conduital_Backlog_Grooming_2026-05-19.md` §B10).

**Version note (CTO):** the spec designates this "v1.4.0," but v1.4.0 shipped as R6 (File Sync UX, S34) and the product is now at v1.5.1. Retargeted to **v1.6.0** (next minor). Spec content unchanged; only the release label is reconciled — CPO to mark the spec in-development at v1.6.0.

### Should Have (Approved — not yet built)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-162 | **Weekly Review Assistant** | Approved (spec) | Timed, sequenced six-step weekly-review workflow with momentum scoring as an active filter at the Projects step; 8 acceptance criteria incl. telemetry. GTD-tier ($49) gated; Basic-tier teaser. M (2–3 wk). Impl window 2026-05-25→06-08 (subject to Mac-build sequencing). **CTO architectural notes folded into spec:** (1) session-state single-day in v1.6.0, cross-day deferred; (2) telemetry event naming `weekly_review.{step_name}.completed`; (3) reuse `WelcomePaidTierModal` for the Basic-tier teaser. |
| BACKLOG-163 | **FirstRunGuide onboarding deltas** (companion to BACKLOG-162) | Approved (spec) | Three heuristic-review spec deltas from `CPO/Conduital_Onboarding_Usability_Heuristic_2026-05-19.md`: (1) Step 1 "I'm not sure" branch → Basic-tier-friendly path (no methodology lecture); (2) Step 2 example chips (3 methodology-aware + "write my own"); (3) Step 4 worked example on the user's just-created project (binds Momentum Score to behavior). Plus three `first_run_guide.*` telemetry events per §5. No existing v1.4.0 onboarding ticket existed, so filed as a sibling row per the dispatch. |

---

## Cross-Cutting: Infrastructure

### Authentication & Authorization

| ID | Description | Status | Target |
|----|-------------|--------|--------|
| - | Multi-user / Teams | Future | Post-R4 |

### Inter-App Integration

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| ROADMAP-011 | **Conduital ↔ Board of Advisors Bi-Directional Local API** | **Retired — 2026-05-09 (CPO grooming decision)** | — | Retired in 2026-05-09 CPO grooming session; no further design work warranted. |

### Storage & Sync

| ID | Description | Status | Target |
|----|-------------|--------|--------|
| ROADMAP-010 | BYOS Foundation (Bring Your Own Storage) | **Done** (Phase 1-5) | R1/R2 — StorageProvider ABC, LocalFolderProvider, StorageService write-through, full test suite |
| DEBT-020 | SyncEngine area markdown handling | Open (verify) | R1 — flagged 2026-05-31 grooming (B1); **not closed without a sync-engine verification pass.** Stats reconciled to 1. |

### Distribution & Marketing

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-001 | Landing Page | **Closed** (2026-05-31 grooming B3) | R1 | Subsumed by live conduital.com + public download endpoint (BACKLOG-161, S35). PPC landing-page work tracked separately (`CPO/Capterra_PPC_Landing_Page_Concept_2026-05-19.md`). |
| DIST-002 | Pricing Model | **Done** | R1 | Tiered perpetual license (Free / GTD $49 / Full $79) — locked in v1.3.x; STRAT-002 decided |
| DIST-003 | Payment Integration (Stripe/Gumroad) | **Done** | R1 | Gumroad activation MON-001 (v1.3.0); Stripe webhook MON-002 (v1.3.1); Stripe inline activation MON-008 (v1.3.3); ConvertKit signup live |
| DIST-004 | Documentation Site | Open | R1 | User-facing docs |
| DIST-005 | Email/Newsletter System | **Done** | R2 | ConvertKit live; trial nurture + paid-tier welcome email flows wired through MON-002/MON-008 fulfillment |
| DIST-014 | Desktop wrapper (Tauri) | Deferred | Post-R4 | Inno Setup installer works well |
| DIST-023 | Path resolution for packaged exe | Open | R1 | .env/config paths must resolve relative to executable |
| DIST-030 | Windows code signing certificate | **Cert in hand 2026-04-25; pipeline wiring status TBC** | R1 | Cert confirmed 2026-04-25; per CPO grooming 2026-05-09, build-pipeline wiring was overdue. CTO to verify current state at next signing step and update; intent: signed installer pre-v1.4.x distribution refresh. |
| DIST-031 | Auto-update mechanism | Open | R2 | Version-check endpoint or Sparkle-style updater |
| DIST-051 | Register conduital.app domain | **Retired** (2026-05-31 grooming B5) | — | No documented strategic intent; a brand-defense domain purchase is a CRO/Chairman call, not a Conduital backlog item. Reopen if intent is documented. |

### CI/CD

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-041 | GitHub repo setup + .gitignore | **Done** (Session 7) | Pre-R1 | Remote: `gregdm98607/-conduital` (private) |
| DIST-042 | CI/CD pipeline (GitHub Actions) | **Done** (Session 7) | R1 | Backend tests + frontend checks; installer-on-tag still TODO |

---

## Cross-Cutting: Technical Debt

### Medium Priority (Address by R2)

| ID | Description | Location | Status |
|----|-------------|----------|--------|
| DEBT-007 | Soft delete not implemented | `db_utils.py:99-106` | **Done** (Session 8) |
| DEBT-116 | Soft delete coverage gaps — missing `deleted_at` filters in 62 queries | 12 backend files | **Done** (Session 9) |
| DEBT-010 | Outdated dependencies | `pyproject.toml`, `package.json` | **Done** (Session 10) |
| DEBT-021 | Area discovery direct DB session | `auto_discovery_service.py` | **Done** (Session 10) |
| DEBT-022 | Area folder pattern reuses project pattern | `auto_discovery_service.py` | **Done** (Session 10) |
| DEBT-023 | Memory migration down_revision | `006_add_memory_layer_tables.py` | **Done** (Session 10 — verified valid) |
| DEBT-041 | `create_unstuck_task` commits inside potentially larger transaction | `intelligence_service.py` | **Done** (Session 10) |
| DEBT-112 | JSON fence stripping in AI service uses naive string ops — fragile | `ai_service.py:482-502` | **Done** (Session 6) |
| DEBT-115 | TZ-naive datetime arithmetic — `datetime.now(tz) - project.stalled_since` crashes when SQLite returns naive dt | `ai_service.py:261`, `project_service.py:317` | **Done** (Session 7) |

### Low Priority (Address when touched)

| ID | Description | Location | Status |
|----|-------------|----------|--------|
| DEBT-008 | File watcher disabled by default | `main.py` | **Done** (S26) — Auto-discovery toggle in Settings UI + runtime start/stop of folder watcher |
| DEBT-013 | Mobile views not optimized | Frontend | **Done** (S29) — Collapsible sidebar with hamburger menu, responsive padding (p-4 md:p-8) on all 16 pages |
| DEBT-015 | Overlapping setup docs | Multiple MD files | **Done** (S30) — Root README is canonical; backend/README reduced to reference-only; deleted SETUP_AND_TEST.md, INSTALL_TOAST.md, DEBUG_STEPS.md, QUICK_FIX.md, PHASE_5_FRONTEND_COMPLETE.md |
| DEBT-016 | WebSocket updates not integrated | Frontend/Backend | **Done** (S30) — `/ws/discovery-status` + `DiscoveryBroadcaster` asyncio pub/sub + `useDiscoveryWebSocket` hook; real-time discovery events replace 30s polling in Settings; 7 tests added |
| DEBT-017 | Auto-discovery debounce | `folder_watcher.py` | **Done** (S25) — Already implemented: `threading.Timer` + `threading.Lock` debounce in `folder_watcher.py` |
| DEBT-018 | Google Drive network interruptions | `folder_watcher.py` | **N/A** (S25) — App is local-first; cloud sync deferred to ROADMAP-010 (BYOS) |
| DEBT-019 | Silent auto-discovery failures | Auto-discovery service | **Done** (S25) — In-memory event log + `/discovery/status` endpoint |
| DEBT-075 | Momentum PUT endpoint mutates singleton `settings` object in-memory | `settings.py:282-292` | **Done** (S25) — Persist-first pattern: .env written before in-memory mutation; 19 tests added |
| DEBT-078 | Test run requires explicit venv python | `backend/venv` | **Done** (S35) — Added `[tool.poetry.scripts] test = "pytest:console_main"` to `backend/pyproject.toml`; `poetry run test` works in poetry-managed environments. The venv path remains the default Windows runner. |
| DEBT-081 | No app icon (.ico) — installer and exe use default icons | Need `assets/conduital.ico` | **Done** (Session 1) |
| DEBT-108 | `AIReviewSummary` loading spinner missing `aria-label` / `role="status"` | `AIReviewSummary.tsx:48` | **Done** (Session 6) |
| DEBT-117 | Heatmap color thresholds (0.25/0.5/0.75) inconsistent with `getMomentumLevel()` (0.2/0.4/0.7) | `MomentumHeatmap.tsx:9-15` | Done (S12) |
| DEBT-118 | Heatmap task completions don't filter by project active status — deleted/archived project tasks inflate count | `intelligence.py:535-542` | Done (S12) |
| DEBT-119 | MomentumHeatmap missing a11y — no `aria-label` on grid cells, no keyboard nav, tooltip mouse-only | `MomentumHeatmap.tsx` | Done (S12) |
| DEBT-120 | Heatmap month labels use fragile absolute positioning (`col * 16 + 32px`) | `MomentumHeatmap.tsx:122` | Done (S12) |
| DEBT-121 | `getMomentumColorClass()` in `ProjectListView.tsx` uses 0.7/0.5/0.3 thresholds — drifted from `MOMENTUM_THRESHOLDS` (0.7/0.4/0.2) | `ProjectListView.tsx:75-79` | **Done** (S13) |
| DEBT-122 | SortableHeader button missing `focus:` ring styling — fails WCAG keyboard nav | `SortableHeader.tsx:31` | **Done** (S13) |
| DEBT-123 | TaskListView `getEnergyInfo()` missing `dark:` color variants — energy labels hard to read in dark mode | `TaskListView.tsx:46-50` | **Done** (S13) |
| DEBT-124 | `parseSortOption()` duplicated in Projects.tsx and AllTasks.tsx — extract to shared utility | `Projects.tsx:49`, `AllTasks.tsx:71` | **Done** (S13) |
| DEBT-125 | TaskListView due date status colors missing `dark:` variants — hard to read in dark mode | `TaskListView.tsx:205-208` | **Done** (S14) |
| DEBT-126 | TaskListView default due date color `text-gray-600` insufficient contrast in dark mode | `TaskListView.tsx:208` | **Done** (S14) |
| DEBT-127 | `aiErrors.ts` missing handlers for 429 (rate limit) and 502/503/504 (gateway errors) | `utils/aiErrors.ts:9-20` | **Done** (S14) |
| DEBT-128 | AIDashboardSuggestions uses `getAIErrorStatus()` directly instead of `getAIErrorMessage()` like other components | `AIDashboardSuggestions.tsx:50-54` | **Done** (S14) |
| DEBT-129 | `parseSortOption()` lacks defensive validation for malformed input | `utils/sort.ts:5-7` | **Done** (S14) |
| DEBT-130 | Decompose-tasks generic exception handler leaks `str(e)` in detail — should sanitize | `intelligence.py:1319-1321` | **Done** (S14) |
| DEBT-131 | Rebalance/energy endpoint soft-delete filters — verify subqueries respect `deleted_at` | `intelligence.py:1345-1485` | **Done** (S14) — verified, no changes needed |
| DEBT-132 | SortableHeader `focus-visible:ring-offset-1` may cause visual overflow in tight table headers | `SortableHeader.tsx:31` | **Done** (S14) |
| DEBT-133 | Import handler catches `err instanceof Error ? err.message` — raw Axios error message shown to user | `Settings.tsx:handleImportJSON` | **Done** (S17) |
| DEBT-134 | `import_service._import_goals` dedup uses `db.query(Goal).all()` — missing soft-delete filter; soft-deleted goals block reimport | `import_service.py:_import_goals` | **N/A** (S17) — `Goal` has no `deleted_at`; `SoftDeleteMixin` not applied |
| DEBT-135 | `import_service._import_visions` dedup uses `db.query(Vision).all()` — same soft-delete gap as DEBT-134 | `import_service.py:_import_visions` | **N/A** (S17) — `Vision` has no `deleted_at` |
| DEBT-136 | After import, TanStack Query caches for projects/tasks/areas not invalidated — stale data until manual refresh | `Settings.tsx:handleImportJSON` | **Done** (S17) |
| DEBT-137 | No client-side file size validation before import upload — large files cause slow/silent failures | `Settings.tsx:handleImportJSON` | **Done** (S17) — 10 MB client-side guard |
| DEBT-138 | `get_memory_stats` builds 6+ separate DB queries — could consolidate into fewer round-trips | `memory_layer/routes.py:36-152` | **Done** (S23) — Consolidated 12+ queries into 3 using `case()` aggregates |
| DEBT-139 | `MemoryPage.tsx` is ~1,600 lines — decompose into tab components | `MemoryPage.tsx` | **Done** (S22) — Complete: ObjectsView + 6 modals extracted; MemoryPage.tsx now 75 lines |
| DEBT-140 | Session capture `energy_level` uses magic numbers 1-5 — no shared constant/enum between FE and BE | `schemas.py:495`, `MemoryPage.tsx` | **Done** (S22) — `ENERGY_LEVELS` constant in shared.tsx, used by SessionsView + EnergyDots |
| DEBT-141 | Health tab has no retry/refresh if `/memory/stats` fails — shows error with no recovery path | `MemoryPage.tsx` (Health tab) | **Done** (S21) — Added refetch button with spin animation |
| DEBT-142 | Version strings stale at `1.1.0-beta` — should be `1.2.0` in `pyproject.toml`, `package.json`, `conduital.iss` | Multiple files | **Done** (S23) — All 5 version locations bumped to 1.2.0 via sync script |

### High Priority (S31 hotfix sweep)

| ID | Description | Location | Status |
|----|-------------|----------|--------|
| DEBT-143 | `FeedbackWidget.tsx` line 219 single-quote apostrophe broke TS build | `frontend/src/components/feedback/FeedbackWidget.tsx:219` | **Done** (v1.3.2, S31) — switched outer JSX string to double quotes |
| DEBT-144 | 6 license tests failed against tightened Gumroad key regex | `backend/tests/test_license_api.py::TestActivateGumroad::*` | **Done** (v1.3.2, S31) — replaced `gr_*` keys with valid 8HEX-8HEX-8HEX-8HEX format |

---

## Cross-Cutting: Documentation

| ID | Description | Priority | Target |
|----|-------------|----------|--------|
| DOC-005 | Module system user documentation | Retired | **Retired** 2026-05-31 grooming (B2) — see R1.1 table |
| DOC-001 | Area mapping configuration guide | Medium | post-launch v1.4.x |
| DOC-002 | Folder watcher troubleshooting | Medium | post-launch v1.4.x |
| DOC-004 | Areas page user guide | Medium | post-launch v1.4.x |
| DOC-003 | Area discovery API docs | Low | R2 |
| DOC-006 | Memory layer API documentation | Medium | R3 |
| DOC-007 | AI context API documentation | Medium | R3 |
| DOC-008 | `POST /export/import` endpoint missing from `API_DOCUMENTATION.md` | Medium | **Done** (S17) |

---

## Strategic Decisions

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| STRAT-001 | **Distribution: Desktop-first** | Decided | Local-first personal productivity; SQLite + file sync; Gumroad |
| STRAT-002 | **Monetization Model** | **Decided** — perpetual license, Gumroad + Stripe direct | Resolved v1.3.x (Gumroad fulfillment + Stripe webhook + inline activation all live; no SaaS/subscription path pursued for v1.x) |
| STRAT-003 | **BYOS (Bring Your Own Storage)** | **Done** (Phase 1-5) | User-owned cloud storage — foundation shipped with local folder provider |
| STRAT-004 | **Multi-AI Provider Support** | Decided | Claude, ChatGPT, provider-agnostic |
| STRAT-005 | **Unified Codebase Architecture** | Implemented | Module system (2026-02-02) |
| STRAT-006 | **Commercial Configuration Presets** | Implemented | basic, gtd, proactive_assistant, full |
| STRAT-007 | **Conduital Leads Shared Infrastructure** | Implemented | Single codebase for all features |
| STRAT-008 | **Semantic Versioning (SemVer)** | Decided | `Major.Minor.Patch` |
| STRAT-009 | **Alpha Launch: Free First** | Decided | Free alpha, Gumroad license key before beta |

---

## Competitive Differentiation

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| DIFF-001 | **AI-Agnostic Design** | Decided | Works with any LLM provider |
| DIFF-002 | **Data Portability (BYOS)** | Decided | User owns data, can export/migrate |
| DIFF-003 | **Local-First Option** | **Implemented** | Local-first since R1 — SQLite + local folder watcher + offline-capable; no cloud dependency for core functionality. BYOS Phase 5 (454 tests passing) extends with optional StorageProvider abstraction. |
| DIFF-004 | **Cross-Platform Sync** | **Done** (2026-05-31 grooming B4) | Implemented via BYOS Phase 1–5 (STRAT-003 Done). Direct cloud integration beyond local-folder BYOS would spec as a STORAGE-* concept. |

---

## Content & Education

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| CONTENT-001 | "The External Brain" Book | Medium | Open |
| CONTENT-002 | Video Walkthrough Course | Low | Open |
| CONTENT-003 | Community Platform (Discord/Forum) | Low | Open |

---

## Parking Lot (Unscheduled)

*Items not assigned to a release yet*

> **Age-sweep scheduled (2026-05-31 grooming B9):** joint CTO + CPO retire-or-promote pass on all Parking Lot items >60 days old at the next grooming touchpoint (~2026-06-15, post-HVAC go/no-go).

| ID | Description | Notes |
|----|-------------|-------|
| BACKLOG-003 | Bulk/Mass task creation | Nice-to-have |
| BACKLOG-009 | Inline target date edit on Task Card | UX polish |
| BACKLOG-010 | Project Templates auto-detect | Advanced feature |
| BACKLOG-015 | Manual area discovery button | Already have auto |
| BACKLOG-018 | Area Detail page cards | Design work needed |
| BACKLOG-037 | Area Templates | Onboarding helper |
| BACKLOG-038 | Batch Area Assignment | Bulk operations |
| BACKLOG-039 | Area Metrics Over Time | Analytics |
| BACKLOG-040 | Area Visual Hierarchy | Color-coding |
| BACKLOG-045 | Project Start Date | MYN alignment |
| BACKLOG-053 | Project Notes/Reference Material | In-app storage |
| BACKLOG-054 | Project Energy/Context | Filter enhancement |
| BACKLOG-059 | Stuck Task Identification | Beyond stalled projects |
| BACKLOG-061 | Register Claude Code Skills | **Retired** (2026-05-31 grooming B6) — out of CPO Charter v2 §3 scope (developer tooling, no external commercial value); lives in `11_Systems\` / `.claude\Scheduled\`. |
| BACKLOG-066 | Automated Urgency Zone (Phase 3) | Zone lock capability |
| BACKLOG-093 | Quick Capture Success Animation | Visual flash/animation feedback |
| BACKLOG-104 | Area Health Score Drill-Down + Improvements | Backend ready, frontend needed |
| BACKLOG-110 | Auto-Discovery as Optional Setting | Toggle on/off independently in Settings |
| BACKLOG-113 | Website Redesign & Product Launch Content | conduital.com marketing workstream |
| BACKLOG-114 | Social Media & Marketing Content Plan | Multi-platform strategy, launch sequence |
| BACKLOG-117 | Installer upgrade-in-place testing | Verify data preservation + DB migrations |
| BACKLOG-121 | Area Prefix Mapping UX Redesign | Clarify auto-discovery, progressive disclosure |
| BACKLOG-128 | Badge Configuration & Today's Focus Layout | Standardize badge pattern, accent-bar style |
| BACKLOG-133 | Smooth Card Reorder Transitions | FLIP / View Transitions API for card sorting |
| BACKLOG-146 | Import: conflict resolution UI — show duplicate list before import, let user choose skip/overwrite | UX Enhancement |
| BACKLOG-147 | Import: progress indicator for large files — streaming or polling approach | UX Enhancement |
| BACKLOG-148 | Import: export format version migration — handle older export schemas gracefully | Reliability |
| BACKLOG-149 | Session Capture: pre-fill accomplishments from git log or task completions | Auto-populate from today's activity |
| BACKLOG-150 | Health tab: sparkline trend charts for 7d/30d activity | Visual trends beyond raw numbers |

### Parking Lot — Completed (Archived)

*Kept for reference; no longer active*

| ID | Session | Summary |
|----|---------|---------|
| BACKLOG-160 | S37 | Always-visible sidebar license tier badge (links to Settings → License) |
| BACKLOG-090 | S14 | Data Import from JSON Backup |
| BACKLOG-095 | S17 | Collapsible Sections Pattern Extension |
| BACKLOG-099 | S1 | Archive Area Confirmation Dialog |
| BACKLOG-118 | S30 | Clean Windows VM testing (Win10 + Win11) |
| BACKLOG-130 | S10 | Momentum Pulse Ring |
| BACKLOG-131 | S6 | Task Completion Celebration |
| BACKLOG-132 | S10 | Streak Counter on Dashboard |
| BACKLOG-134 | S9 | Momentum Delta Toast |
| BACKLOG-135 | S9 | Empty State Illustrations |
| BACKLOG-136 | S10 | Keyboard Shortcut Overlay |
| BACKLOG-137 | S11 | Momentum Color Glow on Sidebar |
| BACKLOG-138 | S11 | Stalled Project Shake |
| BACKLOG-139 | S11 | Daily Momentum Heatmap |
| BACKLOG-141 | S12 | List View Column Header Sorting |
| BACKLOG-142 | S6 | localStorage Key Namespacing |
| BACKLOG-143 | S8 | CompleteTaskButton Accessibility |
| BACKLOG-144 | S12 | MomentumHeatmap Mobile Touch |
| BACKLOG-145 | S13 | AI Features End-to-End Validation |
| BACKLOG-151 | S25 | Display app version number in sidebar |
| BACKLOG-152 | S29 | Ship all releases at "Full" commercial mode |
| BACKLOG-153 | S33–S34 (v1.3.4 + v1.4.0) | File Sync UX — Phase 1 sync broadcaster + Phase 2 conflict-resolution UI |
| BACKLOG-154 | S26 | File Sync auto-discovery UX (Discovery Activity panel) |
| BACKLOG-155 | v1.3.2 (S31) | PostHog frontend wiring (MON-009) |
| BACKLOG-156 | v1.3.2 (S31) | Trial expiry banners — Day-7/11/13 (MON-010) |
| BACKLOG-157 | S32 (v1.3.3) | Feedback admin view (MON-011) |
| BACKLOG-158 | S32 (v1.3.3) | Stripe inline activation (MON-008) |
| BACKLOG-159 | S35 (v1.4.1) | Welcome / paid-tier post-activation flow |
| BACKLOG-161 | S35 (v1.4.1) | Public download URL hosted on conduital.com |
| BACKLOG-087 | S36 (v1.5.0) | Starter Templates by Persona — Writer / Knowledge Worker / Engineer one-click scaffolds (areas + projects + phases + next actions) |

---

## Future Storage Providers — Concepts (Not Roadmapped)

> Aspirational concepts, not committed roadmap work (re-titled 2026-05-31 grooming B8 to disambiguate from committed items).

Ideas for additional `StorageProvider` implementations (see `docs/storage-providers.md` for the architecture):

| ID | Provider | Description | Status | Notes |
|----|----------|-------------|--------|-------|
| STORAGE-001 | **Notion API** | Read/write entities as Notion database pages via the Notion API | Open | Would allow Notion as the source of truth; needs API key + database ID config |
| STORAGE-002 | **Google Drive API** | Store markdown files in a Google Drive folder | Open | OAuth2 flow needed; could leverage existing Google auth infrastructure |
| STORAGE-003 | **Git-backed Storage** | Auto-commit markdown changes to a git repo | Open | Version history for free; could use GitPython or subprocess |
| STORAGE-004 | **S3 / Cloud Object Storage** | Store entities in AWS S3, GCS, or Azure Blob | Open | Good for teams; needs cloud auth config |
| STORAGE-005 | **REST API Provider** | Generic provider that syncs with any REST API | Open | Template for custom integrations |

---

## Pre-Distribution Checklist

Before any release is distributed to end users, complete all items in:

**[`distribution-checklist.md`](distribution-checklist.md)**

---

## Release Checklist Template

For each release, verify:

- [ ] All "Must Have" items complete
- [ ] All "Should Have" items complete or explicitly deferred
- [ ] Relevant technical debt addressed
- [ ] Documentation updated
- [ ] Test coverage meets target
- [ ] Migration tested (fresh install + upgrade)
- [ ] Performance acceptable
- [ ] Security review complete
- [ ] Commercial mode configurations tested (basic, gtd, proactive_assistant, full)
- [ ] **Distribution checklist complete** (see `distribution-checklist.md`)

---

## Stats

| Metric | Count |
|--------|-------|
| Open backlog items | ~47 (2026-05-31 CTO grooming: +2 approved — BACKLOG-162 Weekly Review Assistant + BACKLOG-163 onboarding deltas; −5 closed/retired via CPO 10-delta sweep — DIST-001, DIFF-004, DIST-051, DOC-005, BACKLOG-061) |
| Open tech debt | 1 (DEBT-020 SyncEngine area markdown handling — surfaced grooming B1; retained Open pending a sync-engine verification pass, not closed without evidence) |
| Open documentation | 3 (DOC-001/002/004 retargeted post-launch v1.4.x; DOC-005 retired 2026-05-31 grooming B2; DOC-006/007 Memory/AI Context open) |
| Completed items (archived) | 216+ |
| Backend tests | 519 (518 pass, 1 skip) — S38 +4 MON-013 cross-repo key-format contract tests; suite hermetic (forces legacy storage). Plus conduital-site `api/stripe-webhook.js`: 20 `node --test`. |

*Last updated: 2026-06-02 (S38 — MON-013 launch blocker CODE COMPLETE: relocated Stripe→Resend fulfillment to a stateless Vercel function (`conduital-site/api/stripe-webhook.js`, 20 `node --test`); wired PostHog prod key + stable `/download/latest` URL in `config.py`; added cross-repo key-format contract test; authored `docs/MON-013-fulfillment-runbook.md` for the external ops; v1.5.1→1.5.2. Backend 518 pass / 1 skip. External deploy/DNS/Stripe steps + push remain Greg-side.)*
*Prior: 2026-05-31 (CTO Cowork — Gate 4 Weekly Review Assistant backlog mutation filed as R9 / BACKLOG-162 + BACKLOG-163 onboarding deltas; applied SSS CPO 10-delta grooming sweep B1–B9: DEBT-020 Stats reconciled, DOC-005 retired, DIST-001 + DIFF-004 closed, DIST-051 + BACKLOG-061 retired, R4 Nice-to-Have deferred-banner, Storage Providers re-titled, Parking Lot age-sweep scheduled ~6/15. Commit + push remain Greg-side.)*
*Prior: 2026-05-31 (S37 — BACKLOG-160 sidebar license badge shipped in v1.5.1; fixed non-hermetic tests writing to the real vault + storage_first enum-serialization bug; backend tests 513→514 pass)*
*Full history: `backlog-archive-2026-02-12.md`*
