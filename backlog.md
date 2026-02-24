# Conduital — Release-Based Backlog

This backlog is organized by commercial release milestones. Each release builds on the previous, enabling incremental delivery.

**Module System:** See `backend/MODULE_SYSTEM.md` for technical details.
**Archive:** Full history in `backlog-archive-2026-02-12.md`

---

## Release Overview

| Release | Modules | Target Audience | Status |
|---------|---------|-----------------|--------|
| **R1: Conduital Basic** | `core` + `projects` | Project managers, individuals | **v1.0.0-alpha shipped** (2026-02-08) |
| **R1.1: Conduital Beta** | `core` + `projects` | Project managers, individuals | **v1.0.0-beta shipped** (2026-02-09) |
| **R2: Conduital GTD** | + `gtd_inbox` | GTD practitioners | Planned |
| **R3: Proactive Assistant** | + `memory_layer` + `ai_context` | AI-augmented users | Planned |
| **R4: Full Suite** | All modules | Power users | Planned |

---

## R1.1: Conduital Beta — Remaining

### Should Have (Deferred)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-076 | **List View Design Standard** | **Done** (S12) | SortableHeader/StaticHeader components, wired in Projects + AllTasks pages |
| DOC-005 | **Module System Documentation** | Deferred to R2 | User-facing docs |

---

## R3: Proactive Assistant — Open Items

### Should Have (Quality Bar)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-087 | Starter Templates by Persona | Open | Writer, Knowledge Worker, etc. |
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

## Cross-Cutting: Infrastructure

### Authentication & Authorization

| ID | Description | Status | Target |
|----|-------------|--------|--------|
| - | Multi-user / Teams | Future | Post-R4 |

### Inter-App Integration

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| ROADMAP-011 | **Conduital ↔ Board of Advisors Bi-Directional Local API** | Needs Design | R3+ | Both apps in `C:\Dev\`; share data & functions via local REST/IPC. Requires design doc first — define shared data model, auth model, API surface, sync conflict resolution. |

### Storage & Sync

| ID | Description | Status | Target |
|----|-------------|--------|--------|
| ROADMAP-010 | BYOS Foundation (Bring Your Own Storage) | Open | R1/R2 |
| DEBT-020 | SyncEngine area markdown handling | Open | R1 |

### Distribution & Marketing

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-001 | Landing Page | Open | R1 | Product website |
| DIST-002 | Pricing Model | Open | R1 | One-time purchase vs subscription |
| DIST-003 | Payment Integration (Stripe/Gumroad) | Open | R1 | Direct download distribution |
| DIST-004 | Documentation Site | Open | R1 | User-facing docs |
| DIST-005 | Email/Newsletter System | Open | R2 | Updates, onboarding |
| DIST-014 | Desktop wrapper (Tauri) | Deferred | Post-R4 | Inno Setup installer works well |
| DIST-023 | Path resolution for packaged exe | Open | R1 | .env/config paths must resolve relative to executable |
| DIST-030 | Windows code signing certificate | Open | R1 | Avoid "Unknown Publisher" warnings (~$70-200/yr) |
| DIST-031 | Auto-update mechanism | Open | R2 | Version-check endpoint or Sparkle-style updater |
| DIST-051 | Register conduital.app domain | Open | P1 | $19.99, confirmed available |

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
| DEBT-008 | File watcher disabled by default | `main.py` | Open |
| DEBT-013 | Mobile views not optimized | Frontend | Open |
| DEBT-015 | Overlapping setup docs | Multiple MD files | Open |
| DEBT-016 | WebSocket updates not integrated | Frontend/Backend | Open |
| DEBT-017 | Auto-discovery debounce | `folder_watcher.py` | Open |
| DEBT-018 | Google Drive network interruptions | `folder_watcher.py` | Open |
| DEBT-019 | Silent auto-discovery failures | Auto-discovery service | Open |
| DEBT-075 | Momentum PUT endpoint mutates singleton `settings` object in-memory | `settings.py:282-292` | Documented |
| DEBT-078 | Test run requires explicit venv python | `backend/venv` | Open |
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
| DEBT-138 | `get_memory_stats` builds 6+ separate DB queries — could consolidate into fewer round-trips | `memory_layer/routes.py:36-152` | Open |
| DEBT-139 | `MemoryPage.tsx` is ~1,600 lines — decompose into tab components | `MemoryPage.tsx` | **Done** (S22) — Complete: ObjectsView + 6 modals extracted; MemoryPage.tsx now 75 lines |
| DEBT-140 | Session capture `energy_level` uses magic numbers 1-5 — no shared constant/enum between FE and BE | `schemas.py:495`, `MemoryPage.tsx` | **Done** (S22) — `ENERGY_LEVELS` constant in shared.tsx, used by SessionsView + EnergyDots |
| DEBT-141 | Health tab has no retry/refresh if `/memory/stats` fails — shows error with no recovery path | `MemoryPage.tsx` (Health tab) | **Done** (S21) — Added refetch button with spin animation |
| DEBT-142 | Version strings stale at `1.1.0-beta` — should be `1.2.0` in `pyproject.toml`, `package.json`, `conduital.iss` | Multiple files | Open |

---

## Cross-Cutting: Documentation

| ID | Description | Priority | Target |
|----|-------------|----------|--------|
| DOC-005 | Module system user documentation | High | R1 |
| DOC-001 | Area mapping configuration guide | Medium | R1 |
| DOC-002 | Folder watcher troubleshooting | Medium | R1 |
| DOC-004 | Areas page user guide | Medium | R2 |
| DOC-003 | Area discovery API docs | Low | R2 |
| DOC-006 | Memory layer API documentation | Medium | R3 |
| DOC-007 | AI context API documentation | Medium | R3 |
| DOC-008 | `POST /export/import` endpoint missing from `API_DOCUMENTATION.md` | Medium | **Done** (S17) |

---

## Strategic Decisions

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| STRAT-001 | **Distribution: Desktop-first** | Decided | Local-first personal productivity; SQLite + file sync; Gumroad |
| STRAT-002 | **Monetization Model** | Open | TBD: Open Source, Book, SaaS, Certification |
| STRAT-003 | **BYOS (Bring Your Own Storage)** | Decided | User-owned cloud storage |
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
| DIFF-003 | **Local-First Option** | Open | Self-hosted option for privacy |
| DIFF-004 | **Cross-Platform Sync** | Open | Via BYOS (Google Drive, Dropbox) |

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
| BACKLOG-061 | Register Claude Code Skills | Developer tooling |
| BACKLOG-066 | Automated Urgency Zone (Phase 3) | Zone lock capability |
| BACKLOG-093 | Quick Capture Success Animation | Visual flash/animation feedback |
| BACKLOG-095 | Collapsible Sections Pattern Extension | **Done** (S17) — Collapsible sections in WeeklyReviewPage (5 sections) + ProjectDetail (3 task sections) with localStorage persistence |
| BACKLOG-099 | Archive Area Confirmation Dialog | **Done** (Session 1) — Already implemented with Modal + force archive |
| BACKLOG-104 | Area Health Score Drill-Down + Improvements | Backend ready, frontend needed |
| BACKLOG-110 | Auto-Discovery as Optional Setting | Toggle on/off independently in Settings |
| BACKLOG-113 | Website Redesign & Product Launch Content | conduital.com marketing workstream |
| BACKLOG-114 | Social Media & Marketing Content Plan | Multi-platform strategy, launch sequence |
| BACKLOG-117 | Installer upgrade-in-place testing | Verify data preservation + DB migrations |
| BACKLOG-118 | Clean Windows VM testing (Win10 + Win11) | Test on VMs with no Python/Node.js |
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
| BACKLOG-090 | S14 | Data Import from JSON Backup |
| BACKLOG-099 | S1 | Archive Area Confirmation Dialog |
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
| Open backlog items | ~65 |
| Open tech debt | ~9 |
| Open documentation | 6 |
| Completed items (archived) | 200+ |
| Backend tests | 327 |

*Last updated: 2026-02-23 (Session 22)*
*Full history: `backlog-archive-2026-02-12.md`*
