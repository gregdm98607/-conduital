# Full Release Planning — Open Items Inventory

**Date:** 2026-02-11
**Purpose:** Comprehensive analysis of all open backlog items to inform the v1.1.0 full commercial release plan.
**Current Version:** v1.0.0-beta (commit `ad02145`)

---

## Open Items by Section

### R1.1 Beta — Remaining Open Items

| ID | Description | Type |
|----|-------------|------|
| BACKLOG-118 | Clean Windows VM testing (Win10 + Win11) | Testing |
| BACKLOG-117 | Installer upgrade-in-place testing | Testing |
| DEBT-081 | No app icon (.ico) — installer and exe use defaults | Polish |

### R3: Proactive Assistant — Should Have (Open)

| ID | Description | Backend Status |
|----|-------------|----------------|
| BACKLOG-087 | Starter Templates by Persona | Open — no code yet |
| BACKLOG-082 | Session Summary Capture | Open — no code yet |
| DOC-006 | Memory Layer API Documentation | Open |
| DOC-007 | AI Context API Documentation | Open |

### R3: Proactive Assistant — Nice to Have (Open)

| ID | Description |
|----|-------------|
| BACKLOG-089 | Memory Namespace Management UI |
| BACKLOG-088 | Prefetch Rule Configuration UI |
| BACKLOG-083 | Progress Dashboard (Memory) |
| BACKLOG-085 | Memory Diff View |

### R4: Full Suite — Must Have (Open)

| ID | Description | Significance |
|----|-------------|--------------|
| ROADMAP-007 | GTD Weekly Review with AI Advisors | Core differentiator — AI-powered review dialogue |
| ROADMAP-002 | AI Features Integration | Analysis, suggestions, prioritization |

### R4: Full Suite — Should Have (Open)

| ID | Description |
|----|-------------|
| BACKLOG-049 | Project Workload Indicator |
| BACKLOG-050 | Project Blocked/Waiting Status |
| BACKLOG-062 | Project Standard of Excellence |

### R4: Full Suite — Nice to Have (Open)

| ID | Description |
|----|-------------|
| BACKLOG-001 | Sub-Projects |
| BACKLOG-056 | Project Dependencies |
| BACKLOG-046 | Project Completion Criteria Checklist |
| BACKLOG-051 | Project Type Classification |
| BACKLOG-052 | Project Cloning/Templates UI |
| BACKLOG-055 | Project Time Investment Tracking |
| BACKLOG-057 | Project Archive with History |
| BACKLOG-060 | Delegation/Accountability Tracking |

### Infrastructure — Open Items

| ID | Description | Section |
|----|-------------|---------|
| ROADMAP-010 | BYOS Foundation | Storage & Sync |
| DEBT-020 | SyncEngine area markdown handling | Storage & Sync |
| DIST-012 | PyInstaller backend bundling | Build (already done via build.bat?) |
| DIST-013 | Production React build pipeline | Build (already done via Vite build?) |
| DIST-014 | Desktop wrapper (Tauri) | Build — deferred |
| DIST-015 | Windows installer (NSIS/Inno Setup) | Build — already done via Inno Setup |
| DIST-023 | Path resolution for packaged exe | Build |
| DIST-030 | Windows code signing certificate | Distribution |
| DIST-031 | Auto-update mechanism | Distribution |
| DIST-001 | Landing Page | Marketing |
| DIST-002 | Pricing Model | Marketing |
| DIST-003 | Payment Integration | Marketing |
| DIST-004 | Documentation Site | Marketing |
| DIST-005 | Email/Newsletter System | Marketing |
| DIST-041 | GitHub repo setup | CI/CD |
| DIST-042 | CI/CD pipeline (GitHub Actions) | CI/CD |
| DIST-051 | Register conduital.app domain | Branding |

### Technical Debt — Medium Priority (Open)

| ID | Description |
|----|-------------|
| DEBT-007 | Soft delete not implemented |
| DEBT-010 | Outdated dependencies |
| DEBT-021 | Area discovery direct DB session |
| DEBT-022 | Area folder pattern reuses project pattern |
| DEBT-023 | Memory migration down_revision |
| DEBT-041 | create_unstuck_task commits inside larger transaction |

### Technical Debt — Low Priority (Open)

| ID | Description |
|----|-------------|
| DEBT-008 | File watcher disabled by default |
| DEBT-013 | Mobile views not optimized |
| DEBT-015 | Overlapping setup docs |
| DEBT-016 | WebSocket updates not integrated |
| DEBT-017 | Auto-discovery debounce |
| DEBT-018 | Google Drive network interruptions |
| DEBT-019 | Silent auto-discovery failures |
| DEBT-075 | Momentum PUT endpoint mutates singleton settings |
| DEBT-078 | Test run requires explicit venv python |

### Documentation — Open

| ID | Description | Priority |
|----|-------------|----------|
| DOC-005 | Module system user documentation | High |
| DOC-001 | Area mapping configuration guide | Medium |
| DOC-002 | Folder watcher troubleshooting | Medium |
| DOC-004 | Areas page user guide | Medium |
| DOC-003 | Area discovery API docs | Low |

### Parking Lot — Candidates for Promotion

| ID | Description | Recommendation |
|----|-------------|----------------|
| BACKLOG-104 | Area Health Score Drill-Down (backend READY) | **PROMOTE to Tier 2** — backend exists, frontend only |
| BACKLOG-128 | Badge Configuration & Today's Focus Layout | **PROMOTE to Tier 2** — UI polish |
| BACKLOG-101 | Dashboard Stats Block Visual Consistency | **PROMOTE to Tier 2** — UI polish |
| BACKLOG-099 | Archive Area Confirmation Dialog | **PROMOTE to Tier 2** — safety UX |
| BACKLOG-090 | Data Import from JSON Backup | **PROMOTE to Tier 2** — complements export |
| BACKLOG-093 | Quick Capture Success Animation | **PROMOTE to Tier 3** — polish |
| BACKLOG-095 | Collapsible Sections Extension | **PROMOTE to Tier 3** — consistency |
| BACKLOG-009 | Inline target date edit on Task Card | Defer |
| BACKLOG-040 | Area Visual Hierarchy (color-coding) | Defer |
| BACKLOG-110 | Auto-Discovery as Optional Setting | Defer |
| BACKLOG-121 | Area Prefix Mapping UX Redesign | Defer — larger UX project |
| BACKLOG-113 | Website Redesign & Launch Content | **Separate workstream** — marketing |
| BACKLOG-114 | Social Media & Marketing Plan | **Separate workstream** — marketing |

---

## Backlog Cleanup Observations

### Items to Remove (Completed Inline)
The following items are marked done inline but still appear in active sections — they should be moved to Completed Items or struck through:
- BACKLOG-103 (review frequency) — done, still in Parking Lot
- BACKLOG-111 (momentum validation) — done, still in Parking Lot
- BACKLOG-112 (export refresh) — done, still in Parking Lot
- BACKLOG-115, 116, 119, 120, 122-127, 129 — all done, all in Parking Lot
- BUG-026 — done, still in Parking Lot

### Infrastructure Items Already Done
Several DIST items in the Build & Packaging section are effectively done but not marked:
- DIST-012/013 — PyInstaller + React build are working via build.bat
- DIST-015 — Windows installer IS Inno Setup (done)
- DIST-043 — Test suite stabilization at 216 tests (done)

### Sections with All Items Complete
R2 Must Have, R2 Should Have, R2 Nice to Have, R3 Must Have all show "All items complete" — these sections could be collapsed to reduce noise.

---

## Full Release Tiering

### Tier 1: Must Ship (release blockers)

| ID | Description | Rationale |
|----|-------------|-----------|
| DEBT-081 | App icon (.ico) | Professional appearance — default icons look amateur |
| BACKLOG-118 | Windows VM testing (Win10 + Win11) | Can't ship without testing on clean machines |
| DIST-030 | Code signing certificate | "Unknown Publisher" warnings kill trust |
| BACKLOG-117 | Upgrade-in-place testing | Must verify data preservation on upgrade |
| ROADMAP-002 | AI Features Integration | Core value prop — AI analysis/suggestions/prioritization |
| ROADMAP-007 | GTD Weekly Review with AI Advisors | Key differentiator — AI-powered review dialogue |

### Tier 2: Should Ship (quality bar)

| ID | Description | Rationale |
|----|-------------|-----------|
| BACKLOG-104 | Area Health Drill-Down UI | Backend ready, frontend ~2h work |
| BACKLOG-128 | Badge Configuration | UI polish consistency |
| BACKLOG-101 | Dashboard Stats Consistency | Visual polish |
| BACKLOG-099 | Archive Area Confirmation | Safety UX |
| BACKLOG-082 | Session Summary Capture | Memory layer value |
| BACKLOG-087 | Starter Templates by Persona | Onboarding quality |
| BACKLOG-090 | Data Import from JSON | Complements existing export |
| DOC-005 | Module System Documentation | User-facing docs |
| DEBT-010 | Outdated dependencies | Maintenance hygiene |
| BACKLOG-062 | Project Standard of Excellence | Mirrors area feature |

### Tier 3: Nice to Have (polish)

| ID | Description | Rationale |
|----|-------------|-----------|
| BACKLOG-093 | Quick Capture Animation | Delight factor |
| BACKLOG-095 | Collapsible Sections Extension | Consistency |
| BACKLOG-049 | Project Workload Indicator | Capacity insight |
| BACKLOG-050 | Project Blocked/Waiting Status | Dependency tracking |
| BACKLOG-009 | Inline target date edit | UX convenience |
| BACKLOG-040 | Area Visual Hierarchy | Color customization |

### Defer to Post-Release

| ID | Description | Reason |
|----|-------------|--------|
| BACKLOG-001 | Sub-Projects | Major architecture change |
| BACKLOG-056 | Project Dependencies | Complex, low demand |
| BACKLOG-060 | Delegation/Accountability | Multi-user foundation needed |
| BACKLOG-055 | Time Investment Tracking | Scope creep risk |
| DIST-014 | Tauri Desktop Wrapper | Inno Setup works fine |
| DIST-031 | Auto-update Mechanism | Post-launch optimization |
| BACKLOG-121 | Area Prefix Mapping Redesign | Large UX project |
| BACKLOG-110 | Auto-Discovery Toggle | Low demand |

### Separate Workstreams (Not Software)

| ID | Description | Owner |
|----|-------------|-------|
| DIST-001 | Landing Page | Marketing |
| DIST-002 | Pricing Model | Business |
| DIST-003 | Payment Integration | Business |
| DIST-004 | Documentation Site | Marketing |
| BACKLOG-113 | Website Redesign | Marketing |
| BACKLOG-114 | Social Media Strategy | Marketing |

---

*Analysis completed 2026-02-11*
