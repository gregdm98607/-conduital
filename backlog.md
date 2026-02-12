# Conduital — Release-Based Backlog

This backlog is organized by commercial release milestones. Each release builds on the previous, enabling incremental delivery.

**Module System:** See `backend/MODULE_SYSTEM.md` for technical details.

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

## R1: Conduital Basic

**Modules:** `core` + `projects`
**Target:** Production-ready project and task management with markdown file sync.
**Status:** ✅ **v1.0.0-alpha shipped** (2026-02-08) | Installer built, dev-tested, distributed

---

## R1.1: Conduital Beta

**Target:** Incremental improvements on alpha — remaining distribution items, polish, VM testing.
**Status:** ✅ **v1.0.0-beta shipped** (2026-02-09) — patch commits through 2026-02-11

### Beta Priorities
1. **Momentum Intelligence:** Granularity improvements (graduated scoring, exponential decay, sliding windows) + psychology-backed motivation signals (trend arrows, sparklines, progress bars)
2. **GTD Inbox Enhancements:** Weekly review completion tracking, batch processing, processing stats endpoint
3. **Distribution:** Privacy policy (Phase 4.3), app icon (Phase 5.1), Gumroad listing (Phase 5.3)
4. **Testing:** Clean Windows 10/11 VM testing (BACKLOG-118)
5. **Infrastructure:** ~~Version SSoT (BACKLOG-116)~~, ~~installer graceful shutdown (DEBT-083)~~ ✅ Both done

### Momentum Intelligence (New for Beta)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BETA-001 | **Graduated next-action scoring** — replace binary 0/1 with 4-tier scale (0, 0.3, 0.7, 1.0) based on recency | ✅ Done | Eliminates cliff effect |
| BETA-002 | **Exponential activity decay** — `e^(-days/7)` instead of linear `1-(days/30)` | ✅ Done | Recent activity matters more |
| BETA-003 | **Sliding completion window** — 30-day weighted window (7d×1.0, 14d×0.5, 30d×0.25) | ✅ Done | Prevents hard cliff at day 8 |
| BETA-004 | **Logarithmic frequency scaling** — `log(1+count)/log(11)` instead of `min(1, count/10)` | ✅ Done | Harder to saturate |
| BETA-010 | **Momentum trend indicator** — up/down/stable arrow on ProjectCard from delta | ✅ Done | Progress Principle |
| BETA-011 | **Momentum sparkline** — inline SVG trend line on ProjectCard | ✅ Done | Progress Principle |
| BETA-012 | **Project completion progress bar** — thin bar on ProjectCard (completed/total tasks) | ✅ Done | Goal Gradient Effect |
| BETA-013 | **"Almost there" nudge** — subtle text when >80% tasks complete | ✅ Done | Goal Gradient + Zeigarnik |
| BETA-014 | **Dashboard momentum summary** — aggregate trend view across all projects | ✅ Done | Progress Principle |
| BETA-020 | **`previous_momentum_score` column** — delta calculation support | ✅ Done | Data model |
| BETA-021 | **`MomentumSnapshot` table** — daily snapshots for sparklines | ✅ Done | Data model |
| BETA-022 | **Alembic migration** for BETA-020/021 | ✅ Done | Migration 011 |
| BETA-023 | **Snapshot creation** in scheduled recalculation job | ✅ Done | Scheduler updated |
| BETA-024 | **Momentum history API** — `GET /intelligence/momentum-history/{id}`, `GET /intelligence/dashboard/momentum-summary` | ✅ Done | API endpoints |

### GTD Inbox Enhancements (New for Beta)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BETA-030 | **Weekly review completion tracking** — `POST /weekly-review/complete`, history endpoint, Dashboard display | ✅ Done | Model + migration + API + frontend |
| BETA-031 | **Inbox batch processing** — multi-select + bulk assign/delete/convert | ✅ Done | Backend + frontend |
| BETA-032 | **Inbox processing stats endpoint** — `GET /inbox/stats` (fixes DEBT-064) | ✅ Done | Replaces client-side calc |
| BETA-034 | **Inbox item age indicator** — subtle visual aging (gray/amber/red clock) | ✅ Done | Zeigarnik Effect |

### R1 Release Notes

**What's Included:**
- Core CRUD for projects, tasks, areas, contexts, goals, visions
- Markdown file sync (Google Drive compatible)
- Auto-discovery of projects and areas from markdown files
- Momentum scoring and stalled project detection
- Next actions prioritization with MYN urgency zones
- Google OAuth authentication (optional)
- Data export/backup (JSON + SQLite)
- Dashboard with stalled projects widget

**Deferred to R2:**
- BACKLOG-076: List View Design Standard (UX consistency)
- DOC-005: Module System Documentation (user-facing docs)

**Pulled into Beta from R2:**
- GTD inbox enhancements (weekly review tracking, batch processing, processing stats)

**Known Limitations:**
- Single-user only (no multi-user/teams)

### R1 Current State
- Core CRUD for projects, tasks, areas, contexts, goals, visions
- Markdown file sync (Google Drive)
- Auto-discovery of projects and areas
- Momentum scoring and stalled detection
- Next actions prioritization
- MYN urgency zones (partial)
- List and grid views

### R1 Must Have (Release Blockers)

✅ All items complete — see [Completed Items](#completed-items)

### R1 Should Have (Quality Bar)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-076 | **List View Design Standard** | Deferred to R2 | UX consistency |
| DOC-005 | **Module System Documentation** | Deferred to R2 | User-facing docs |

### R1 Nice to Have (Polish)

✅ All items complete — see [Completed Items](#completed-items)

---

## R2: Conduital GTD

**Modules:** `core` + `projects` + `gtd_inbox`
**Target:** Complete GTD workflow implementation.
**Prerequisite:** R1 Complete

### R2 Must Have (Release Blockers)

✅ All items complete — see [Completed Items](#completed-items)

### R2 Should Have (Quality Bar)

✅ All items complete — see [Completed Items](#completed-items)

### R2 Nice to Have (Polish)

✅ All items complete — see [Completed Items](#completed-items)

---

## R3: Proactive Assistant

**Modules:** `core` + `projects` + `memory_layer` + `ai_context`
**Target:** AI-augmented productivity with persistent memory.
**Prerequisite:** R1 Complete (R2 not required)

### R3 Must Have (Release Blockers)

✅ All items complete — see [Completed Items](#completed-items)

### R3 Should Have (Quality Bar)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-087 | **Starter Templates by Persona** | Open | Writer, Knowledge Worker, etc. |
| BACKLOG-082 | **Session Summary Capture** | Open | End-of-session memory updates |
| BACKLOG-084 | **Cross-Memory Search/Query** | **Done** | Backend search endpoint + frontend server-side search |
| BACKLOG-072 | **Unstuck Task Button** | **Done** | "Get Unstuck" button on ProjectDetail page |
| DOC-006 | **Memory Layer API Documentation** | Open | Developer docs |
| DOC-007 | **AI Context API Documentation** | Open | Developer docs |

### R3 Nice to Have (Polish)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-089 | Memory Namespace Management UI | Open | Power users |
| BACKLOG-088 | Prefetch Rule Configuration UI | Open | Power users |
| BACKLOG-083 | Progress Dashboard (Memory) | Open | System health metrics |
| BACKLOG-085 | Memory Diff View | Open | Session continuity |

---

## R4: Full Suite

**Modules:** All (`core` + `projects` + `gtd_inbox` + `memory_layer` + `ai_context`)
**Target:** Power users who want everything.
**Prerequisite:** R2 + R3 Complete

### R4 Must Have (Release Blockers)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| ROADMAP-007 | **GTD Weekly Review with AI Advisors** | Open | AI-powered review dialogue |
| ROADMAP-002 | **AI Features Integration** | Open | Analysis, suggestions, prioritization |

### R4 Should Have (Quality Bar)

| ID | Description | Status | Notes |
|----|-------------|--------|-------|
| BACKLOG-049 | Project Workload Indicator | Open | Capacity warnings |
| BACKLOG-050 | Project Blocked/Waiting Status | Open | External dependency tracking |
| BACKLOG-062 | Project Standard of Excellence | Open | Mirror area-level feature |

### R4 Nice to Have (Future)

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

*Required across all releases*

### Authentication & Authorization

| ID | Description | Status | Target |
|----|-------------|--------|--------|
| - | Multi-user / Teams | Future | Post-R4 |

### Storage & Sync

| ID | Description | Status | Target |
|----|-------------|--------|--------|
| ROADMAP-010 | BYOS Foundation (Bring Your Own Storage) | Open | R1/R2 |
| DEBT-020 | SyncEngine area markdown handling | Open | R1 |

### Release Planning & Distribution

**Distribution Model:** Desktop-first (Option A). Local-first personal productivity tool aligns with SQLite architecture and local-first philosophy. SaaS (Option B) is a future consideration requiring PostgreSQL + multi-tenancy.

#### Build & Packaging

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-010 | Strip development artifacts from build | ✅ Done | Pre-R1 | 32 dev-only files added to .gitignore; .claude/ already excluded (2026-02-07) |
| DIST-011 | FastAPI static file serving for React build | ✅ Done | Pre-R1 | StaticFiles mount + catch-all SPA route in main.py (verified 2026-02-07) |
| DIST-012 | PyInstaller backend bundling | ✅ Done | R1 | Bundled via `build.bat` — handles Pydantic, SQLAlchemy hidden imports (2026-02-08) |
| DIST-013 | Production React build pipeline | ✅ Done | R1 | `npm run build` via Vite — optimized, hashed assets, env-specific config (2026-02-08) |
| DIST-014 | Desktop wrapper (Tauri) | Deferred | Post-R4 | Inno Setup installer works well; Tauri deferred |
| DIST-015 | Windows installer (NSIS/Inno Setup fallback) | ✅ Done | R1 | Inno Setup installer with graceful shutdown, version SSoT (2026-02-08) |

#### Code Preparation

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-020 | Dependency license audit | ✅ Done | Pre-R1 | All deps permissive (MIT/BSD/Apache 2.0/ISC); THIRD_PARTY_LICENSES.txt created 2026-02-07 |
| DIST-021 | Lock dependency versions | ✅ Done | Pre-R1 | requirements.txt (pinned ==), poetry.lock, package-lock.json all present (verified 2026-02-07) |
| DIST-022 | Semantic versioning setup | ✅ Done | Pre-R1 | SemVer established; v1.0.0-alpha set in pyproject.toml, package.json, config.py, .env.example (2026-02-07) |
| DIST-023 | Path resolution for packaged exe | Open | R1 | .env/config paths must resolve relative to executable, not source tree |
| DIST-024 | Fix deprecated on_event → lifespan handlers | ✅ Done | Pre-R1 | FastAPI modernization required before packaging (DEBT-067) |

#### Distribution & Marketing

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-001 | Landing Page | Open | R1 | Product website |
| DIST-002 | Pricing Model | Open | R1 | One-time purchase vs subscription |
| DIST-003 | Payment Integration (Stripe/Gumroad) | Open | R1 | Direct download distribution |
| DIST-004 | Documentation Site | Open | R1 | User-facing docs |
| DIST-005 | Email/Newsletter System | Open | R2 | Updates, onboarding |
| DIST-030 | Windows code signing certificate | Open | R1 | Avoid "Unknown Publisher" warnings (~$70-200/yr) |
| DIST-031 | Auto-update mechanism | Open | R2 | Version-check endpoint or Sparkle-style updater |

#### Branding & Identity

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-050 | Register conduital.com domain | ✅ Done | **P0 — Immediate** | Purchased 2026-02-07 |
| DIST-051 | Register conduital.app domain | Open | P1 | $19.99, confirmed available |
| DIST-052 | Claim @conduital on Twitter/X | ✅ Done | P1 | Claimed 2026-02-07 |
| DIST-053 | Claim conduital on GitHub | ✅ Done | P1 | Claimed as gregdm98607/conduital 2026-02-07 |
| DIST-054 | Claim conduital on Gumroad | ✅ Done | P1 | Claimed conduital.gumroad.com 2026-02-07 |
| DIST-055 | Remove ChatGPT branding notes from distribution-checklist.md | ✅ Done | Pre-R1 | 1,603 lines of research blob removed 2026-02-07 |
| DIST-056 | Update all codebase references from "Project Tracker" to "Conduital" | ✅ Done | Pre-R1 | 56+ occurrences updated across 3 rounds (commits d9b538e, 54c5b7f) |

#### CI/CD (when source hosting is established)

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-040 | Initialize git repository | ✅ Done | Pre-R1 | Git init + .gitignore created (awaiting initial commit — needs git config) |
| DIST-041 | GitHub repo setup + .gitignore | Open | Pre-R1 | Remote hosting, issue tracking, PR workflow |
| DIST-042 | CI/CD pipeline (GitHub Actions) | Open | R1 | Automated tests, build, produce installer on release tag |
| DIST-043 | Automated test suite stabilization | ✅ Done | Pre-R1 | 216/216 tests pass as of v1.0.0-beta. Ready for CI integration |

---

## Cross-Cutting: Technical Debt

### High Priority (Address by R1)

✅ All items complete — see [Completed Items](#completed-items)

### Medium Priority (Address by R2)

| ID | Description | Location | Status |
|----|-------------|----------|--------|
| DEBT-007 | Soft delete not implemented | `db_utils.py:99-106` | Open |
| DEBT-010 | Outdated dependencies | `pyproject.toml`, `package.json` | Open |
| DEBT-021 | Area discovery direct DB session | `auto_discovery_service.py` | Open |
| DEBT-022 | Area folder pattern reuses project pattern | `auto_discovery_service.py` | Open |
| DEBT-023 | Memory migration down_revision | `006_add_memory_layer_tables.py` | Open |
| DEBT-041 | `create_unstuck_task` commits inside potentially larger transaction | `intelligence_service.py:494` | Open |

### Low Priority (Address when touched)

| ID | Description | Location | Status |
|----|-------------|----------|--------|
| DEBT-008 | File watcher disabled by default | `main.py` | Open |
| DEBT-013 | Mobile views not optimized | Frontend | Open |
| ~~DEBT-014~~ | ~~ARIA labels missing~~ | ~~Frontend~~ | ✅ Done |
| DEBT-015 | Overlapping setup docs | Multiple MD files | Open |
| DEBT-016 | WebSocket updates not integrated | Frontend/Backend | Open |
| DEBT-017 | Auto-discovery debounce | `folder_watcher.py` | Open |
| DEBT-018 | Google Drive network interruptions | `folder_watcher.py` | Open |
| DEBT-019 | Silent auto-discovery failures | Auto-discovery service | Open |
| ~~DEBT-039~~ | ~~MemoryPage priority input allows out-of-range values client-side~~ | ~~`MemoryPage.tsx:447`~~ | ✅ Done |
| ~~DEBT-052~~ | ~~Empty model dropdown edge case when provider_models not yet loaded~~ | ~~`Settings.tsx`~~ | ✅ Done |
| ~~DEBT-061~~ | ~~Dynamic attribute assignment on ORM objects for task counts (fragile)~~ | ~~`project_service.py`~~ | ✅ Done |
| ~~DEBT-062~~ | ~~Redundant task_count fields in ProjectWithTasks schema~~ | ~~`project.py`~~ | ✅ Closed (by design) |

| ~~DEBT-064~~ | ~~"Processed Today" count — dedicated API endpoint~~ | ~~`InboxPage.tsx`, backend inbox API~~ | ✅ Done |
| ~~DEBT-065~~ | ~~API client methods AbortSignal support~~ | ~~`api.ts` (all methods)~~ | ✅ Done |
| DEBT-075 | Momentum PUT endpoint mutates the singleton `settings` object in-memory — not safe if Pydantic Settings is frozen | `settings.py:282-292` | Documented |
| DEBT-078 | Test run requires explicit venv python — `python -m pytest` fails without venv activation | `backend/venv` exists but PATH doesn't include it | Open |
| ~~DEBT-080~~ | ~~Inno Setup version hardcoded — now SSoT with pyproject.toml~~ | ~~`installer/conduital.iss:24`~~ | ✅ Done |
| DEBT-081 | No app icon (.ico) — installer and exe use default icons | Need `assets/conduital.ico` with 16-256px variants | Open |
| ~~DEBT-082~~ | ~~`build.bat` size reporting loop fixed~~ | ~~`build.bat:112-115`~~ | ✅ Done |
| ~~DEBT-083~~ | ~~Installer graceful shutdown (tries /shutdown before force-kill)~~ | ~~`installer/conduital.iss`~~ | ✅ Done |

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
| STRAT-001 | **Distribution: Desktop-first** | Decided | Local-first personal productivity; SQLite + file sync architecture; Gumroad distribution |
| STRAT-002 | **Monetization Model** | Open | TBD: Open Source, Book, SaaS, Certification |
| STRAT-003 | **BYOS (Bring Your Own Storage)** | Decided | User-owned cloud storage |
| STRAT-004 | **Multi-AI Provider Support** | Decided | Claude, ChatGPT, provider-agnostic |
| STRAT-005 | **Unified Codebase Architecture** | Implemented | Module system (2026-02-02) |
| STRAT-006 | **Commercial Configuration Presets** | Implemented | basic, gtd, proactive_assistant, full |
| STRAT-007 | **Conduital Leads Shared Infrastructure** | Implemented | Single codebase for all features |
| STRAT-008 | **Semantic Versioning (SemVer)** | Decided | `Major.Minor.Patch` — Major: breaking/incompatible changes; Minor: backward-compatible features; Patch: backward-compatible bug fixes. First public version: `1.0.0-alpha` (shipping without code signing) |
| STRAT-009 | **Alpha Launch: Free First** | Decided | Ship free alpha installer (no license key) for early users/feedback. Implement Gumroad license key validation before beta/paid release. Step-by-step guide: `tasks/gumroad-license-guide.md` |

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
| BACKLOG-093 | Quick Capture Success Animation | Visual flash/animation feedback on Capture & Next for consecutive entries |
| BACKLOG-095 | Collapsible Sections Pattern Extension | Apply collapsible pattern to Weekly Review checklist and ProjectDetail task sections |
| BACKLOG-099 | Archive Area Confirmation Dialog | Warn when area has active projects, offer cascade options |
| BACKLOG-101 | Dashboard Stats Block Visual Consistency | Active Projects, Pending Tasks, Avg Momentum blocks mix bold text and color-coded badges for counts — pick one treatment and apply consistently |
| BACKLOG-104 | **Area Health Score Drill-Down + Calculation Improvements** | **Backend ready:** `GET /areas/{area_id}/health` endpoint returns 4-factor breakdown. **Frontend needed:** `AreaHealthBreakdown.tsx` mirroring `MomentumBreakdown.tsx`. Consider area-specific scoring improvements. |
| BACKLOG-110 | Auto-Discovery as Optional Setting | Toggle on/off Project/Area/Prefix discovery independently in Settings. |
| BACKLOG-113 | **Website Redesign & Product Launch Content (conduital.com)** | Separate marketing workstream. Sitemap, hero content, demo screenshots, SEO. |
| BACKLOG-117 | Installer upgrade-in-place testing | Verify data preservation + DB migrations on upgrade |
| BACKLOG-118 | Clean Windows VM testing (Win10 + Win11) | Test on VMs with no Python/Node.js |
| BACKLOG-114 | **Social Media & Marketing Content Plan** | Separate marketing workstream. Multi-platform strategy, AI agent automation, launch sequence. |
| BACKLOG-121 | **Area Prefix Mapping UX Redesign** | Clarify auto-discovery concept, show folder paths, progressive disclosure |
| BACKLOG-128 | **Badge Configuration & Today's Focus Layout** | Standardize badge pattern across app. Accent-bar style badges on Today's Focus. |
| BACKLOG-130 | **Momentum Pulse Ring** | Animated concentric ring around momentum score on ProjectDetail — gentle pulse when momentum is rising, static glow at steady, fade when declining. CSS-only, ~30 lines. Makes the score feel alive. |
| BACKLOG-131 | **Task Completion Celebration** | Satisfying checkmark animation on task complete: checkbox morphs to checkmark with a brief green ripple. Scale up slightly then settle. CSS keyframes only. Dopamine hit for every completed task. |
| BACKLOG-132 | **Streak Counter on Dashboard** | "X-day streak" badge showing consecutive days with at least one task completed. Flame icon intensifies (amber → orange → red) as streak grows. Backend: simple query on task completion dates. Motivates daily engagement. |
| BACKLOG-133 | **Smooth Card Reorder Transitions** | When project cards shift position (sort by momentum, filter change), animate card movement with `layout` transitions instead of instant DOM reflow. Uses CSS `View Transitions API` or FLIP technique. Makes sorting feel premium. |
| BACKLOG-134 | **Momentum Delta Toast** | After completing a task, show a subtle floating "+0.05 momentum" toast near the momentum bar with a gentle slide-up fade. Real-time feedback connecting actions to progress. Reinforces the Progress Principle. |
| BACKLOG-135 | **Empty State Illustrations** | Replace "No projects found" / "No tasks" / "Inbox empty" bare text with lightweight SVG illustrations + encouraging copy. "All clear — what's next?" for empty inbox, "Time to build something" for no projects. Small investment, big polish signal. |
| BACKLOG-136 | **Keyboard Shortcut Overlay** | Press `?` anywhere to show a floating shortcut cheat-sheet (modal). `N` = new task, `P` = new project, `/` = search, `G D` = go dashboard. Power-user signal. Feels like a pro tool. |
| BACKLOG-137 | **Momentum Color Glow on Sidebar Active Item** | Sidebar active nav item gets a subtle left-border glow that matches the user's average momentum color. Green glow when things are going well, amber when attention needed. Ambient awareness without being distracting. |
| BACKLOG-138 | **Stalled Project Shake** | Stalled project cards get a very subtle CSS shake animation (2px, 0.3s) when first rendered into view, then stop. Draws the eye without being annoying. Urgency without anxiety. Single `animation-iteration-count: 1`. |
| BACKLOG-139 | **Daily Momentum Heatmap** | GitHub-style contribution heatmap on Dashboard showing momentum scores over the last 90 days. Green = high momentum days, gray = low. Uses existing momentum history data. One glance tells the whole story. |

---

## Completed Items

| ID | Description | Completed |
|----|-------------|-----------|
| BUG-001 through BUG-019 | Various bug fixes | 2026-01-24 to 2026-01-26 |
| DEBT-001, 002, 003, 012 | Technical debt cleanup | 2026-01-24 |
| FEATURE-001 through 007 | Core features | 2026-01-24 |
| BACKLOG-002, 005-008, 011-014, 016-017, 019-020, 025-029, 041, 047, 063-066 | Various backlog items | 2026-01-24 to 2026-02-01 |
| STRAT-005, 006, 007 | Module system architecture | 2026-02-02 |
| INT-001 through INT-004 | PA integration items | 2026-02-02 |
| TECH-008 | Shared module architecture | 2026-02-02 |
| ROADMAP-004 | Proactive Assistant Integration | 2026-02-02 |
| DEBT-004 | Configuration Externalization (SERVER_HOST/PORT, sync root, VITE vars) | 2026-02-02 |
| BACKLOG-069 | Scheduled Momentum Recalculation (APScheduler, daily at 2AM) | 2026-02-02 |
| DEBT-006 | Input Validation (Pydantic validators, max_length, enum validation) | 2026-02-02 |
| BACKLOG-070 | Dashboard Stalled Projects Widget (MomentumBar, Unstuck action) | 2026-02-02 |
| BACKLOG-075 | Migration Integrity Checks (chain analysis, validators, CLI tools) | 2026-02-02 |
| BACKLOG-074 | Data Export/Backup (JSON export, SQLite backup, API endpoints) | 2026-02-03 |
| DEBT-005 | Test Coverage ~30% (169 tests, 42% coverage across services) | 2026-02-03 |
| ROADMAP-009 | Google OAuth Authentication (full frontend + backend auth layer) | 2026-02-03 |
| DEBT-092 | SQLite Migration Compatibility (batch mode for foreign keys) | 2026-02-03 |
| **R1 RELEASE** | **User Testing Release** | **2026-02-03** |
| BACKLOG-071 | Project Health Indicators on ProjectCard (health badge, activity indicators) | 2026-02-03 |
| DEBT-011 | Missing database indexes (FKs, priority, energy_level, defer_until, stalled_since, etc.) | 2026-02-04 |
| BACKLOG-058 | Momentum Score Drill-Down (factor breakdown API + expandable UI on ProjectDetail) | 2026-02-04 |
| DEBT-009 | N+1 query fixes in intelligence_service.py (batch momentum, eager-load tasks) | 2026-02-04 |
| BACKLOG-065 | Sidebar Visual Enhancement (dark theme, section grouping, logo, hover effects) | 2026-02-04 |
| ROADMAP-001 | Dark Mode (Tailwind class-based, Settings toggle, localStorage persistence) | 2026-02-05 |
| DEBT-026 | TypeScript build errors fixed (37 errors across AreaDetail, ProjectDetail, modals) | 2026-02-05 |
| BACKLOG-077 | Inbox Processing Flow Gaps (editable title/description, custom entity creation) | 2026-02-05 |
| BACKLOG-078 | Processed Inbox Items Visibility (result_title + clickable links to created entities) | 2026-02-05 |
| BACKLOG-043 | Someday/Maybe Project Workflow (dedicated page, activate/archive workflow, sidebar nav) | 2026-02-05 |
| BACKLOG-024 | Weekly Review Checklist (interactive GTD checklist, localStorage persistence, progress bar) | 2026-02-05 |
| BACKLOG-042 | Project Review Indicators (review badges on cards + list view: overdue/soon/current) | 2026-02-05 |
| BACKLOG-079 | Inbox Item Edit Before Processing (PUT endpoint, inline edit UI on unprocessed items) | 2026-02-06 |
| BACKLOG-048 | Quick Capture to Project (project selector in Quick Capture modal, direct task creation) | 2026-02-06 |
| BACKLOG-035 | Review Frequency Intelligence (review reminders widget on Dashboard, overdue/due-soon areas) | 2026-02-06 |
| BACKLOG-029 | Standard of Excellence Visibility Phase 2 (SoE on ProjectDetail via area context) | 2026-02-06 |
| BACKLOG-031 | Orphan Projects Warning (banner on Projects page, orphan count on Dashboard) | 2026-02-06 |
| BACKLOG-092 | Collapsible Urgency Zone Sections (chevron toggle, localStorage persistence) | 2026-02-06 |
| BACKLOG-023 | Opportunity Now Limit Warning (banner when zone exceeds 20 items) | 2026-02-06 |
| BACKLOG-022 | MYN Daily Execution Dashboard (/daily page with priorities, due today, quick wins) | 2026-02-06 |
| BACKLOG-033 | Area Card Quick Actions (Add Project with pre-selected area, compact icon buttons) | 2026-02-06 |
| BACKLOG-034 | Areas Dashboard Widget (area overview with review status on main Dashboard) | 2026-02-06 |
| ROADMAP-006 | All Action Items Page (comprehensive task list across all projects) | 2026-02-04 |
| BACKLOG-044 | Natural Planning Model Fields (purpose, vision, brainstorm, organizing on Projects) | 2026-02-06 |
| BACKLOG-030 | Area Health Score (4-factor weighted calculation, health bar on AreaCard/AreaDetail) | 2026-02-06 |
| BACKLOG-036 | Area Archival (soft archive with toggle, filtered list, archive/unarchive UI) | 2026-02-06 |
| BACKLOG-073 | AI Settings Page (enable/disable, API key, model selector, max tokens, test connection) | 2026-02-06 |
| BACKLOG-080 | Memory Editor UI (namespace sidebar, CRUD modals, search, priority indicators) | 2026-02-06 |
| DEBT-025 | InboxItem TimestampMixin (created_at/updated_at + migration 009) | 2026-02-06 |
| DEBT-029 | `/next-actions/dashboard` Pydantic response model (DailyDashboardResponse) | 2026-02-06 |
| DEBT-032 | Falsy-zero recalculation bug fix (`is None` check) | 2026-02-06 |
| DEBT-033 | Filter archived areas from health score updates | 2026-02-06 |
| DEBT-034 | `delete_area` IntegrityError handling (409 response) | 2026-02-06 |
| DEBT-035 | `archive_area` active projects check (force param, on_hold cascade) | 2026-02-06 |
| DEBT-036 | `/ai/test` actually tests connection (minimal API call) | 2026-02-06 |
| DEBT-037 | Removed unused `threshold_date` variable | 2026-02-06 |
| DEBT-038 | Removed duplicate `joinedload` import | 2026-02-06 |
| DEBT-040 | `/ai/test` Pydantic response model (AITestResponse) | 2026-02-06 |
| BACKLOG-096 | Persist AI Key via Settings Page (settings saved to .env) | 2026-02-06 |
| BACKLOG-081 | Context Export for AI Sessions (GET /export/ai-context + Dashboard/ProjectDetail UI) | 2026-02-06 |
| BACKLOG-097 | Collapsible Settings Sections (6 sections, localStorage persistence) | 2026-02-06 |
| DEBT-030 | MemoryPage EditObjectModal setState moved to useEffect | 2026-02-06 |
| DEBT-031 | MemoryPage error state handling for queries | 2026-02-06 |
| BUG-020 | Dashboard Pending Tasks Count (dedicated stats endpoint replacing faulty inline calc) | 2026-02-06 |
| BACKLOG-102 | Project Mark Reviewed Button (endpoint + button + review badge on ProjectDetail) | 2026-02-06 |
| BACKLOG-100 | Settings Sections Default Collapsed (all sections collapsed on first visit) | 2026-02-06 |
| ROADMAP-008 | Multi-AI Provider Settings (Anthropic/OpenAI/Google with provider abstraction) | 2026-02-06 |
| BACKLOG-086 | User Onboarding Flow (4-step wizard creating initial memory objects) | 2026-02-06 |
| DEBT-054 | Frontend `.env` VITE_API_BASE_URL fixed to use Vite proxy (`/api/v1`) | 2026-02-07 |
| BUG-021 | Projects page white screen crash (moved error return after all hooks) | 2026-02-07 |
| BUG-022 | AI Context Export 500 (repair migration for missing user_id on goals/visions) | 2026-02-07 |
| BUG-023 | CORS config fragile (expanded default origins, added fallback ports 5174/5175) | 2026-02-07 |
| BACKLOG-106 | Project Card Task Counts (SQL subquery annotations on list API, ProjectCard uses new fields) | 2026-02-07 |
| BACKLOG-108 | Global React Error Boundary (ErrorBoundary class component wrapping App root) | 2026-02-07 |
| BACKLOG-105 | Sidebar Module-Aware Navigation (fetches /modules, filters Inbox/Memory by enabled modules) | 2026-02-07 |
| DEBT-056 | Toast notification deduplication (added stable IDs to high-frequency error toast patterns) | 2026-02-07 |
| DEBT-044 | Unused imports removed (PlainTextResponse, Task from export.py) | 2026-02-07 |
| DEBT-051 | Inconsistent BaseModel naming fixed (PydanticBaseModel alias removed in routes.py) | 2026-02-07 |
| DEBT-057 | Project list API task counts (same as BACKLOG-106) | 2026-02-07 |
| DEBT-058 | Project detail page task_count fix (get_by_id now computes counts) | 2026-02-07 |
| DEBT-059 | Layout.tsx /modules fetch uses API client with AbortController | 2026-02-07 |
| DEBT-060 | ErrorBoundary retry loop prevention (max 2 resets, then "Go Home" only) | 2026-02-07 |
| DEBT-027 | ESLint no-console rule (.eslintrc.cjs with warn, allow error/warn) | 2026-02-07 |
| BACKLOG-107 | Dashboard stalled/at-risk count reconciled with Weekly Review | 2026-02-07 |
| BACKLOG-072 | Unstuck Task Button on ProjectDetail ("Get Unstuck" button wired to intelligence endpoint) | 2026-02-07 |
| BACKLOG-084 | Cross-Memory Search/Query (backend search endpoint + frontend server-side search) | 2026-02-07 |
| DEBT-042 | _persist_to_env race condition fixed (threading.Lock) | 2026-02-07 |
| DEBT-043 | _persist_to_env value sanitization (_sanitize_env_value for newlines/special chars) | 2026-02-07 |
| BACKLOG-094 | Whitespace-Only Content Validation (strip_whitespace validator on all title/content fields) | 2026-02-07 |
| BACKLOG-109 | CORS Origins from Environment Variable (field_validator parses CSV or JSON) | 2026-02-07 |
| BACKLOG-091 | Export UI in Frontend (preview, JSON download, DB backup in Settings page) | 2026-02-07 |
| BACKLOG-098 | Momentum Settings PUT Endpoint (PUT /settings/momentum + editable UI) | 2026-02-07 |
| DEBT-045 | AI context export N+1 fix (single all_active query, derived counts) | 2026-02-07 |
| DEBT-050 | Unused timedelta import removed from ai_service.py | 2026-02-07 |
| DEBT-066 | SQLAlchemy `== True` → `.is_(True)` in 8 locations across 4 files | 2026-02-07 |
| DEBT-067 | FastAPI on_event → lifespan context manager migration | 2026-02-07 |
| DIST-024 | Fix deprecated on_event → lifespan handlers (same as DEBT-067) | 2026-02-07 |
| DEBT-068 | Pydantic V1 deprecations: class Config→ConfigDict, example=→examples= (9 instances in auth.py, discovery.py, memory_layer/schemas.py) | 2026-02-07 |
| DEBT-071 | Unused `get_db` import removed from main.py | 2026-02-07 |
| DIST-011 | FastAPI static file serving for React build (StaticFiles mount + catch-all SPA route) | 2026-02-07 |
| DIST-020 | Dependency license audit (all permissive: MIT/BSD/Apache 2.0/ISC; THIRD_PARTY_LICENSES.txt) | 2026-02-07 |
| DIST-021 | Dependency versions locked (requirements.txt pinned, poetry.lock, package-lock.json) | 2026-02-07 |
| DIST-022 | Semantic versioning setup (v1.0.0-alpha across 4 files) | 2026-02-07 |
| DIST-050 | conduital.com domain registered | 2026-02-07 |
| DIST-052 | @conduital on Twitter/X claimed | 2026-02-07 |
| DIST-053 | conduital on GitHub claimed (gregdm98607/conduital) | 2026-02-07 |
| DIST-054 | conduital on Gumroad claimed | 2026-02-07 |
| DIST-055 | ChatGPT branding notes removed from distribution-checklist.md (1,603 lines) | 2026-02-07 |
| DIST-056 | All codebase references updated from "Project Tracker" to "Conduital" (56+ occurrences) | 2026-02-07 |
| BUG-024 | Deferred tasks not filtered from next actions (defer_until SQL filter added to query) | 2026-02-07 |
| DEBT-049 | Collapsible section buttons: added `type="button"` + `aria-expanded` to 8 buttons (Settings + NextActions) | 2026-02-07 |
| DEBT-077 | pytest-asyncio `asyncio_mode = "auto"` warning removed from pyproject.toml | 2026-02-07 |
| DIST-010 | Dev artifacts stripped: 32 dev-only files added to .gitignore | 2026-02-07 |
| DEBT-069 | conftest.py StaticPool fix (consistent with test_api_basic.py) | 2026-02-07 |
| DEBT-070 | Test infrastructure consolidation (shared in_memory_engine from conftest.py) | 2026-02-07 |
| DIST-056b | Documentation rebrand: README.md rewritten, backlog.md, .gitignore, scripts/README.md, 5 skill files updated | 2026-02-07 |
| DIST-022b | Version single source of truth: run.py reads from config.py Settings.VERSION | 2026-02-07 |
| DEBT-024 | Test infrastructure fixed (fixture-based TestClient, StaticPool, 18/18 pass) | 2026-02-07 |
| DEBT-028 | Inbox "Processed Today" stat filters by today's date | 2026-02-07 |
| DEBT-046 | ContextExportModal setState-in-render moved to useEffect | 2026-02-07 |
| DEBT-047 | ContextExportModal stale data + memory leak fixed (reset on close, AbortController) | 2026-02-07 |
| DEBT-048 | SQLAlchemy `== False` → `.is_(False)` in export.py, areas.py, intelligence_service.py | 2026-02-07 |
| DEBT-053 | Projects.tsx early return before hooks fixed (BUG-021) | 2026-02-07 |
| DEBT-055 | ContextExportModal backdrop — N/A (already uses shared Modal) | 2026-02-07 |
| DEBT-072 | Path import in main.py — N/A (actively used in 5 locations) | 2026-02-07 |
| DIST-056c | Final branding pass: dev scripts (3 files), THIRD_PARTY_LICENSES.txt, .env.example, CLAUDE.md, .gitignore stale pattern | 2026-02-08 |
| DEBT-079 | auto_discovery_service.py: 33 print() statements converted to logger.info/warning/error | 2026-02-08 |
| DEBT-080 | folder_watcher.py: 3 print() statements converted to logger.info | 2026-02-08 |
| DEBT-063 | SPA catch-all route excludes `/modules` and `/health` API endpoints (production fix) | 2026-02-08 |
| DIST-056d | Deep branding pass: API_DOCUMENTATION.md, backend README, scripts (3 files), sync.py, projects/__init__.py, .env | 2026-02-08 |
| DEBT-073 | Momentum section icon added (Activity icon matching other Settings sections) | 2026-02-08 |
| DEBT-074 | Recalculation interval exposed in Settings UI (was loaded but hidden) | 2026-02-08 |
| DEBT-076 | Duplicate blob download logic extracted into shared `triggerBlobDownload` helper in api.ts | 2026-02-08 |
| DEBT-063b | SPA catch-all route extended to also exclude `/openapi.json` endpoint | 2026-02-08 |
| DIST-056e | Trademark cleanup: all GTD/PARA refs removed from model docstrings (7 files), module comments (5 files), AI prompt (1 file) | 2026-02-08 |
| DIST-010b | .gitignore hygiene: restored backend/API_DOCUMENTATION.md, added frontend/INSTALL_TOAST.md + frontend/QUICK_FIX.md | 2026-02-08 |
| DIST-010c | .gitignore hardening: added `~$*` for Office temp files, root-level design asset exclusions (/*.docx, /*.png, /*.jpg, /*.jpeg) | 2026-02-08 |
| DEBT-082 | `build.bat` size reporting loop fixed (corrected findstr parsing with `usebackq tokens` and byte display) | 2026-02-08 |
| BACKLOG-111 | Momentum Settings stalled > at_risk validation (server-side HTTPException 422 + client-side guard + inline warning) | 2026-02-08 |
| BACKLOG-115 | `/api/v1/shutdown` graceful shutdown endpoint (shared shutdown_event, localhost-only, cooperative with tray) | 2026-02-08 |
| DEBT-014 | ARIA labels added to Modal (`role="dialog"`, `aria-modal`, `aria-labelledby`), UserMenu (`aria-haspopup`, `aria-expanded`, `role="menu/menuitem"`), ProjectCard outcome toggle, Settings API key toggle | 2026-02-08 |
| DEBT-065 | AbortSignal support added to all API client getter methods (27 methods in api.ts) | 2026-02-08 |
| BETA-001 | Graduated next-action scoring (4-tier: 0/0.3/0.7/1.0 based on NA age) | 2026-02-09 |
| BETA-002 | Exponential activity decay (`e^(-days/7)` replaces linear decay) | 2026-02-09 |
| BETA-003 | Sliding completion window (30-day weighted: 7d×1.0, 14d×0.5, 30d×0.25) | 2026-02-09 |
| BETA-004 | Logarithmic frequency scaling (`log(1+count)/log(11)`) | 2026-02-09 |
| BETA-020 | `previous_momentum_score` column added to projects table | 2026-02-09 |
| BETA-021 | `MomentumSnapshot` table for daily momentum history | 2026-02-09 |
| BETA-022 | Alembic migration 011_momentum_snapshots | 2026-02-09 |
| BETA-023 | Snapshot creation added to scheduled recalculation job | 2026-02-09 |
| DEBT-039 | MemoryPage priority input clamped to 0-100 range (3 locations) | 2026-02-09 |
| DEBT-061 | Project model task_count/completed_task_count defined as explicit class attributes | 2026-02-09 |
| DEBT-064 | "Processed Today" stat replaced with dedicated `GET /inbox/stats` endpoint (BETA-032) | 2026-02-09 |
| DEBT-080 | Installer version now synced from pyproject.toml via `scripts/sync_version.py` | 2026-02-09 |
| DEBT-083 | Installer graceful shutdown — tries `POST /shutdown` endpoint before force-kill | 2026-02-09 |
| BACKLOG-116 | Version SSoT — `config.py` reads from pyproject.toml; sync script for all files | 2026-02-09 |
| BACKLOG-119 | Task Push/Defer quick action — DeferPopover component (1 Week / 1 Month / custom) on ProjectDetail + NextActions | 2026-02-09 |
| BACKLOG-120 | Make Next Action quick action — "→ Next Action" / "→ Other" buttons in ProjectDetail bulk toolbar | 2026-02-09 |
| DEBT-062 | Closed by design — task_count fields serve different purposes (SQL counts vs embedded tasks) | 2026-02-09 |
| BACKLOG-103 | Project Review Frequency — replaced manual next_review_date with review_frequency dropdown | 2026-02-11 |
| BACKLOG-112 | Export Preview auto-refreshes after JSON or DB backup download | 2026-02-11 |
| DEBT-052 | Empty model dropdown — disabled with "Loading models..." when provider_models not loaded | 2026-02-11 |
| BUG-026 | Inbox sidebar — added gtd_inbox to basic preset, removed module gate | 2026-02-11 |
| BACKLOG-129 | Version display — sidebar footer shows version from /health endpoint | 2026-02-11 |
| DIST-012 | PyInstaller backend bundling — via build.bat with hidden imports | 2026-02-08 |
| DIST-013 | Production React build — Vite optimized build with asset hashing | 2026-02-08 |
| DIST-015 | Windows installer — Inno Setup with graceful shutdown + version SSoT | 2026-02-08 |
| DIST-043 | Test suite stabilization — 216/216 tests passing | 2026-02-11 |

*See git history for detailed completion notes.*

---

## Pre-Distribution Checklist

Before any release is distributed to end users, complete all items in:

**[`distribution-checklist.md`](distribution-checklist.md)**

This checklist covers:
- Security issues (API keys, secrets, JWT configuration)
- Hardcoded paths removal
- Cross-platform support
- Licensing and trademark review
- Packaging and installer setup

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

*Last updated: 2026-02-11 (backlog cleanup; beta patches committed; full release plan created)*
*Reorganized by commercial release milestones*
