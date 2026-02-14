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
| BACKLOG-076 | **List View Design Standard** | Deferred to R2 | UX consistency + column header sorting (see BACKLOG-141) |
| DOC-005 | **Module System Documentation** | Deferred to R2 | User-facing docs |

---

## R3: Proactive Assistant — Open Items

### Should Have (Quality Bar)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-087 | Starter Templates by Persona | Open | Writer, Knowledge Worker, etc. |
| BACKLOG-082 | Session Summary Capture | Open | End-of-session memory updates |
| DOC-006 | Memory Layer API Documentation | Open | Developer docs |
| DOC-007 | AI Context API Documentation | Open | Developer docs |

### Nice to Have (Polish)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-089 | Memory Namespace Management UI | Open | Power users |
| BACKLOG-088 | Prefetch Rule Configuration UI | Open | Power users |
| BACKLOG-083 | Progress Dashboard (Memory) | Open | System health metrics |
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
| DEBT-081 | No app icon (.ico) — installer and exe use default icons | Need `assets/conduital.ico` | Open |
| DEBT-108 | `AIReviewSummary` loading spinner missing `aria-label` / `role="status"` | `AIReviewSummary.tsx:48` | **Done** (Session 6) |

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
| BACKLOG-090 | Data Import from JSON Backup | Complement to export feature |
| BACKLOG-093 | Quick Capture Success Animation | Visual flash/animation feedback |
| BACKLOG-095 | Collapsible Sections Pattern Extension | Weekly Review + ProjectDetail task sections |
| BACKLOG-099 | Archive Area Confirmation Dialog | **Done** (Session 1) — Already implemented with Modal + force archive |
| BACKLOG-104 | Area Health Score Drill-Down + Improvements | Backend ready, frontend needed |
| BACKLOG-110 | Auto-Discovery as Optional Setting | Toggle on/off independently in Settings |
| BACKLOG-113 | Website Redesign & Product Launch Content | conduital.com marketing workstream |
| BACKLOG-114 | Social Media & Marketing Content Plan | Multi-platform strategy, launch sequence |
| BACKLOG-117 | Installer upgrade-in-place testing | Verify data preservation + DB migrations |
| BACKLOG-118 | Clean Windows VM testing (Win10 + Win11) | Test on VMs with no Python/Node.js |
| BACKLOG-121 | Area Prefix Mapping UX Redesign | Clarify auto-discovery, progressive disclosure |
| BACKLOG-128 | Badge Configuration & Today's Focus Layout | Standardize badge pattern, accent-bar style |
| BACKLOG-130 | Momentum Pulse Ring | **Done** (Session 10) — Animated ring on ProjectDetail with color-coded pulse |
| BACKLOG-131 | Task Completion Celebration | **Done** (Session 6) — CompleteTaskButton with ripple animation |
| BACKLOG-132 | Streak Counter on Dashboard | **Done** (Session 10) — Flame icon + day count in dashboard stats |
| BACKLOG-133 | Smooth Card Reorder Transitions | FLIP / View Transitions API for card sorting |
| BACKLOG-134 | Momentum Delta Toast | **Done** (Session 9) — Rotating encouraging momentum messages in useCompleteTask hook |
| BACKLOG-135 | Empty State Illustrations | **Done** (Session 9) — EmptyState component with SVG illustrations for projects/tasks/areas/search |
| BACKLOG-136 | Keyboard Shortcut Overlay | **Done** (Session 10) — Press `?` for overlay, `g+key` chord navigation |
| BACKLOG-137 | Momentum Color Glow on Sidebar | **Done** (Session 11) — Active nav item glow matching avg momentum |
| BACKLOG-138 | Stalled Project Shake | **Done** (Session 11) — CSS shake animation on stalled project cards |
| BACKLOG-139 | Daily Momentum Heatmap | **Done** (Session 11) — GitHub-style 90-day heatmap on Dashboard |
| BACKLOG-141 | List View Column Header Sorting | Sort-by-column with ascending/descending toggle |
| BACKLOG-142 | localStorage Key Namespacing | **Done** (Session 6) — all keys use `pt-` prefix |
| BACKLOG-143 | CompleteTaskButton accessibility (aria-label, focus-visible ring, aria-disabled) | **Done** (Session 8) |

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
| Open backlog items | ~62 |
| Open tech debt | ~8 |
| Open documentation | 7 |
| Completed items (archived) | 200+ |
| Backend tests | 284 |

*Last updated: 2026-02-14 (Session 11)*
*Full history: `backlog-archive-2026-02-12.md`*
