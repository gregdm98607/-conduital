# Project Tracker - Release-Based Backlog

This backlog is organized by commercial release milestones. Each release builds on the previous, enabling incremental delivery.

**Module System:** See `backend/MODULE_SYSTEM.md` for technical details.

---

## Release Overview

| Release | Modules | Target Audience | Status |
|---------|---------|-----------------|--------|
| **R1: PT Basic** | `core` + `projects` | Project managers, individuals | **User Testing** (2026-02-03) |
| **R2: PT GTD** | + `gtd_inbox` | GTD practitioners | Planned |
| **R3: Proactive Assistant** | + `memory_layer` + `ai_context` | AI-augmented users | Planned |
| **R4: Full Suite** | All modules | Power users | Planned |

---

## R1: Project Tracker Basic

**Modules:** `core` + `projects`
**Target:** Production-ready project and task management with Second Brain sync.
**Status:** 🧪 **User Testing** | Released: 2026-02-03

### R1 Release Notes

**What's Included:**
- Core CRUD for projects, tasks, areas, contexts, goals, visions
- Second Brain folder sync (Google Drive compatible)
- Auto-discovery of projects and areas from markdown files
- Momentum scoring and stalled project detection
- Next actions prioritization with MYN urgency zones
- Google OAuth authentication (optional)
- Data export/backup (JSON + SQLite)
- Dashboard with stalled projects widget

**Deferred to R2:**
- BACKLOG-076: List View Design Standard (UX consistency)
- DOC-005: Module System Documentation (user-facing docs)

**Known Limitations:**
- 15 API integration tests failing (test harness issue, not production)
- Single-user only (no multi-user/teams)

### R1 Current State
- Core CRUD for projects, tasks, areas, contexts, goals, visions
- Second Brain folder sync (Google Drive)
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

## R2: Project Tracker GTD

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

**Distribution Model:** Desktop-first (Option A). Local-first personal productivity tool aligns with SQLite architecture and Second Brain philosophy. SaaS (Option B) is a future consideration requiring PostgreSQL + multi-tenancy.

#### Build & Packaging

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-010 | Strip development artifacts from build | Open | Pre-R1 | Remove CLAUDE.md, .claude/, conversation logs, dev configs |
| DIST-011 | FastAPI static file serving for React build | Open | Pre-R1 | Serve frontend `build/` from backend — single process, single port |
| DIST-012 | PyInstaller backend bundling | Open | R1 | Bundle FastAPI + SQLAlchemy + deps into standalone .exe; handle hidden imports (Pydantic, SQLAlchemy dynamic imports) |
| DIST-013 | Production React build pipeline | Open | R1 | `npm run build` optimization, env-specific config, asset hashing |
| DIST-014 | Desktop wrapper (Tauri) | Open | R1 | Native window via Tauri (~5MB installer); launches FastAPI as sidecar, renders React in webview |
| DIST-015 | Windows installer (NSIS/Inno Setup fallback) | Open | R1 | Alternative to Tauri — traditional installer, starts server + opens browser |

#### Code Preparation

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-020 | Dependency license audit | Open | Pre-R1 | Verify all deps permit commercial use |
| DIST-021 | Lock dependency versions | Open | Pre-R1 | Freeze requirements.txt + package-lock.json for reproducible builds |
| DIST-022 | Semantic versioning setup | Open | Pre-R1 | Per STRAT-008: SemVer `Major.Minor.Patch`, first public version `1.0.0-beta` |
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

#### CI/CD (when source hosting is established)

| ID | Description | Status | Target | Notes |
|----|-------------|--------|--------|-------|
| DIST-040 | Initialize git repository | ✅ Done | Pre-R1 | Git init + .gitignore created (awaiting initial commit — needs git config) |
| DIST-041 | GitHub repo setup + .gitignore | Open | Pre-R1 | Remote hosting, issue tracking, PR workflow |
| DIST-042 | CI/CD pipeline (GitHub Actions) | Open | R1 | Automated tests, build, produce installer on release tag |
| DIST-043 | Automated test suite stabilization | **Unblocked** | Pre-R1 | DEBT-024 fixed — 18/18 API tests pass. Ready for CI integration |

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
| DEBT-024 | Test infrastructure broken - API tests don't init DB | `tests/test_api_basic.py` | ✅ Done — fixture-based TestClient, StaticPool, startup patches, 18/18 pass |
| DEBT-027 | ESLint `no-console` rule to prevent debug logging in production | Frontend | **Done** |
| DEBT-028 | Inbox "Processed Today" stat inaccurate (shows 0 or all-time count) | `InboxPage.tsx` | ✅ Done — filters processed_at by today's date |
| DEBT-041 | `create_unstuck_task` commits inside potentially larger transaction | `intelligence_service.py:494` | Open |
| DEBT-042 | `_persist_to_env` race condition on concurrent .env writes | `settings.py:73-98` | **Done** — threading.Lock added |
| DEBT-043 | `_persist_to_env` no value sanitization (newlines/special chars in API keys) | `settings.py:83-86` | **Done** — _sanitize_env_value() added |
| DEBT-044 | Unused imports: `os` in settings.py, `PlainTextResponse`/`Task` in export.py | `settings.py:8`, `export.py:20,27` | **Done** |
| DEBT-045 | AI context export N+1: overview fetches all active projects twice | `export.py:231-236,316-322` | **Done** — Single `all_active` query, stalled/counts derived from it |
| DEBT-046 | ContextExportModal setState-in-render anti-pattern (same as DEBT-030) | `ContextExportModal.tsx:59-61` | ✅ Done — moved to useEffect |
| DEBT-047 | ContextExportModal stale data on reopen + memory leak on unmount | `ContextExportModal.tsx:15-39` | ✅ Done — reset on close + AbortController cleanup |
| DEBT-048 | SQLAlchemy `== False` should use `.is_(False)` in export.py | `export.py:272` | ✅ Done — also fixed in areas.py + intelligence_service.py |
| DEBT-053 | Projects.tsx early return before hooks — violates React rules of hooks | `Projects.tsx:64` | **Done** (BUG-021) |
| DEBT-055 | ContextExportModal missing backdrop overlay — page content visible and scrollable behind modal | `ContextExportModal.tsx` | ✅ N/A — uses shared Modal component which has backdrop |
| DEBT-056 | Toast notifications stack without deduplication — identical error toasts pile up (10+ visible) | Frontend (react-hot-toast config) | **Done** |
| DEBT-057 | Project list API missing task counts — `/projects` response lacks `task_count`/`completed_task_count`, ProjectCard shows "Tasks 0/0" | `projects.py` API + `ProjectCard.tsx` | **Done** (BACKLOG-106) |

### Low Priority (Address when touched)

| ID | Description | Location | Status |
|----|-------------|----------|--------|
| DEBT-008 | File watcher disabled by default | `main.py` | Open |
| DEBT-013 | Mobile views not optimized | Frontend | Open |
| DEBT-014 | ARIA labels missing | Frontend | Open |
| DEBT-015 | Overlapping setup docs | Multiple MD files | Open |
| DEBT-016 | WebSocket updates not integrated | Frontend/Backend | Open |
| DEBT-017 | Auto-discovery debounce | `folder_watcher.py` | Open |
| DEBT-018 | Google Drive network interruptions | `folder_watcher.py` | Open |
| DEBT-019 | Silent auto-discovery failures | Auto-discovery service | Open |
| DEBT-039 | MemoryPage priority input allows out-of-range values client-side | `MemoryPage.tsx:447` | Open |
| DEBT-049 | Collapsible section buttons missing `type="button"` and `aria-expanded` | `Settings.tsx` | Open |
| DEBT-050 | Unused `timedelta` import | `ai_service.py:12` | **Done** |
| DEBT-051 | Inconsistent BaseModel naming (`PydanticBaseModel` alias) | `memory_layer/routes.py` | **Done** |
| DEBT-052 | Empty model dropdown edge case when provider_models not yet loaded | `Settings.tsx` | Open |
| DEBT-058 | `get_by_id` returns `task_count: 0` — detail pages show misleading task counts | `project_service.py` | **Done** |
| DEBT-059 | Raw `fetch('/modules')` bypasses API client (auth, error handling, AbortController) | `Layout.tsx` | **Done** |
| DEBT-060 | ErrorBoundary "Try Again" can infinite-loop on deterministic errors | `ErrorBoundary.tsx` | **Done** |
| DEBT-061 | Dynamic attribute assignment on ORM objects for task counts (fragile) | `project_service.py` | Open |
| DEBT-062 | Redundant task_count fields in ProjectWithTasks schema | `project.py` | Open |
| DEBT-063 | `/modules` proxy needs production server configuration (Vite dev proxy only) | `vite.config.ts` | Open |
| DEBT-064 | "Processed Today" count shows 0 on unprocessed tab — needs dedicated API endpoint | `InboxPage.tsx`, backend inbox API | Open |
| DEBT-065 | API client methods don't accept AbortSignal — prevents true HTTP request cancellation | `api.ts` (all methods) | Open |
| DEBT-066 | SQLAlchemy `== True` pattern in 8 locations — should use `.is_(True)` | `intelligence_service.py` ×3, `next_actions_service.py` ×3, `task_service.py` ×1, `memory_layer/services.py` ×1 | **Done** |
| DEBT-067 | FastAPI `@app.on_event("startup"/"shutdown")` deprecated — migrate to lifespan context manager | `main.py:110,178` | **Done** — asynccontextmanager lifespan, helpers moved before app creation |
| DEBT-068 | Pydantic V1-style `class Config` + `Field(example=...)` deprecated — migrate to `ConfigDict` + `json_schema_extra` | Multiple schema files | Open |
| DEBT-069 | conftest.py `in_memory_engine` fixture missing `StaticPool` — inconsistent with test_api_basic.py | `tests/conftest.py` | Open |
| DEBT-070 | conftest.py and test_api_basic.py duplicate engine/session setup — consolidate into shared conftest | `tests/conftest.py`, `tests/test_api_basic.py` | Open |
| DEBT-071 | `get_db` imported but unused in main.py after lifespan refactor | `main.py:38` | Open |
| DEBT-072 | `Path` imported but unused in main.py (only used in setup_logging call which can use string) | `main.py:15` — verify if still needed | Open |
| DEBT-073 | Momentum section missing icon — other Settings sections have colored icons, Momentum has none | `Settings.tsx:862` | Open |
| DEBT-074 | `recalculateInterval` state variable loaded from API but never exposed in UI — hidden from user | `Settings.tsx:69` | Open |
| DEBT-075 | Momentum PUT endpoint mutates the singleton `settings` object in-memory — not safe if Pydantic Settings is frozen | `settings.py:282-292` | Open |
| DEBT-076 | `downloadJSONExport` and `downloadDatabaseBackup` duplicate blob download logic — extract shared helper | `api.ts:532-558` | Open |
| DEBT-077 | Tests use `pytest-asyncio` but test_api_basic.py uses sync TestClient — `asyncio: mode=AUTO` warning in pytest config | `pyproject.toml` | Open |
| DEBT-078 | Test run requires explicit venv python — `python -m pytest` fails without venv activation | `backend/venv` exists but PATH doesn't include it | Open |

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
| STRAT-001 | **Distribution: SaaS Web-Only** | Decided | Recurring revenue, single codebase |
| STRAT-002 | **Monetization Model** | Open | TBD: Open Source, Book, SaaS, Certification |
| STRAT-003 | **BYOS (Bring Your Own Storage)** | Decided | User-owned cloud storage |
| STRAT-004 | **Multi-AI Provider Support** | Decided | Claude, ChatGPT, provider-agnostic |
| STRAT-005 | **Unified Codebase Architecture** | Implemented | Module system (2026-02-02) |
| STRAT-006 | **Commercial Configuration Presets** | Implemented | basic, gtd, proactive_assistant, full |
| STRAT-007 | **PT Leads Shared Infrastructure** | Implemented | Single codebase for all features |
| STRAT-008 | **Semantic Versioning (SemVer)** | Decided | `Major.Minor.Patch` — Major: breaking/incompatible changes; Minor: backward-compatible features; Patch: backward-compatible bug fixes. First public version: `1.0.0-beta` |

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
| BACKLOG-091 | ~~Export UI in Frontend~~ | **Done** — Export section in Settings with preview, JSON download, DB backup |
| BACKLOG-093 | Quick Capture Success Animation | Visual flash/animation feedback on Capture & Next for consecutive entries |
| BACKLOG-094 | ~~Whitespace-Only Content Validation~~ | **Done** — strip_whitespace validator on inbox, task, project, area schemas |
| BACKLOG-095 | Collapsible Sections Pattern Extension | Apply collapsible pattern to Weekly Review checklist and ProjectDetail task sections |
| BACKLOG-098 | ~~Momentum Settings PUT Endpoint~~ | **Done** — PUT /settings/momentum + editable controls in Settings UI |
| BACKLOG-099 | Archive Area Confirmation Dialog | Warn when area has active projects, offer cascade options |
| BACKLOG-101 | Dashboard Stats Block Visual Consistency | Active Projects, Pending Tasks, Avg Momentum blocks mix bold text and color-coded badges for counts — pick one treatment and apply consistently |
| BACKLOG-103 | Project Review Frequency + Mark Reviewed Next Date |
| BACKLOG-104 | Area Health Score "How is this calculated?" Drill-Down | Add a "How is this calculated?" expandable section beneath the Health bar on AreaDetail, mirroring the existing Momentum Score drill-down on ProjectDetail (BACKLOG-058). Show the weighted factor breakdown (project health, review cadence, activity, standards). | 1) Add `review_frequency` field to Project model (matching Area model pattern: daily/weekly/monthly). 2) Display review frequency badge and review status on ProjectDetail (matching AreaDetail pattern). 3) Fix both Area and Project `mark-reviewed` endpoints to calculate and set `next_review_date` based on frequency when marked reviewed. Currently neither endpoint sets a future review target. |
| BACKLOG-105 | ~~Sidebar Module-Aware Navigation~~ | **Done** — Nav items filtered by enabled modules via `/modules` API |
| BACKLOG-106 | ~~Project Card Task Counts~~ | **Done** — SQL subquery annotations on list endpoint |
| BACKLOG-107 | ~~Weekly Review vs Dashboard Stalled Count Inconsistency~~ | **Done** — Dashboard now shows both stalled + at-risk projects via `include_at_risk` param |
| BACKLOG-108 | ~~Global React Error Boundary~~ | **Done** — ErrorBoundary wraps App root |
| BACKLOG-109 | ~~CORS Origins from Environment Variable~~ | **Done** — field_validator parses comma-separated or JSON array from .env |
| BACKLOG-110 | Auto-Discovery as Optional Setting | Add a user setting on the Settings page to toggle on/off Project discovery, Area discovery, and Project Prefix discovery independently. Design what "off" means (skip on startup, ignore file changes, preserve existing data vs. clear). |
| BACKLOG-111 | Momentum Settings: Validate stalled > at_risk | Frontend allows saving stalled_threshold < at_risk_threshold, which is logically invalid (a project can't be at-risk before it's stalled). Add client-side + server-side validation. |
| BACKLOG-112 | Export Preview: Refresh after download | After downloading JSON export or DB backup, the export preview data doesn't refresh. Add a re-fetch or stale indicator. |
| BACKLOG-113 | **Website Redesign & Product Launch Content (gregmaxfield.com)** | Redesign and deploy new content for www.gregmaxfield.com to announce, promote, and demo Project Tracker. Site hosted on GoDaddy. Use AI agents liberally for content generation, design iteration, and deployment. **Content Plan:** **Sitemap:** Home (hero + features + CTA) → Features (GTD Workflow, MYN, AI Assistant, Second Brain Integration) → How It Works (3-step onboarding) → Pricing (free/open-source + cost transparency) → Docs → Blog → About → Get Started/Download. **Hero messaging:** "Your Second Brain Meets Intelligent Task Management" — 3 pillars: Your Data Your Control, Proven Productivity Methods, AI That Actually Helps. **Demo strategy:** 8 priority annotated screenshots (dashboard, inbox processing, urgency zones, AI chat, sync, weekly review, project hierarchy, module selection) + 2-3 min demo video + GIF animations. **SEO targets:** GTD software, Second Brain integration, local-first productivity app, AI task manager, MYN productivity system, PARA method digital organization. **Trust elements:** GitHub star count, open-source transparency, "your data never leaves your computer" messaging, founder bio, tech stack disclosure. **CTA strategy:** Primary "Download Project Tracker" on every page, secondary contextual CTAs (Watch Demo, View on GitHub, Star on GitHub). **Implementation phases:** Phase 1 (MVP): Home + Get Started + Features + About. Phase 2 (Launch): How It Works + Pricing + Demo video + SEO. Phase 3 (Growth): Blog + Expanded docs + Community showcase + Testimonials. |
| BACKLOG-114 | **AI-Agentic-First Social Media & Marketing Content Plan** | Envision and deploy an AI-agentic-first social media and marketing content strategy for awareness, promotion, engagement, and marketing. **Platform strategy:** Priority 1: Twitter/X (productivity/PKM community) + Reddit (r/gtd, r/productivity, r/ObsidianMD, r/PKMS). Priority 2: LinkedIn (professional audience) + Hacker News + YouTube (tutorials/demos). **Content pillars:** 40% Education/How-To, 25% Philosophy/Thought Leadership (local-first, data ownership, methodology), 20% Technical Deep-Dives (architecture, AI integration), 15% Community/UGC. **AI agent automation:** Content repurposing agents (blog → tweets/threads/LinkedIn/Reddit), engagement monitoring + response drafting agents, performance analytics + optimization agents, launch timing + A/B testing agents, SEO content generation agents, newsletter curation agents. **Cadence:** Twitter 1-2x/day, Reddit 2-3x/week, LinkedIn 2-3x/week, YouTube 1-2x/month, Blog 1-2x/week, Newsletter weekly. **Launch sequence:** 30-day countdown — Week 4: teaser campaign + "building in public" threads. Week 3: feature spotlights + beta signups. Week 2: demo videos + influencer outreach. Week 1: daily countdown + launch prep. Launch day: coordinated multi-platform push. Post-launch: sustained engagement + community building. **Metrics:** Awareness (followers, impressions), Engagement (replies, shares, saves), Conversion (site visits, downloads, GitHub stars), Agent efficiency (content throughput, response time). **Extended channels:** Blog/SEO strategy, email newsletter funnel, YouTube tutorial series, podcast guest appearances, developer relations via GitHub. **Ratio:** 10:1 value-to-promotion. Emphasize authentic community building, transparency about AI use, privacy-first/local-first differentiation. |

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
| DEBT-004 | Configuration Externalization (SERVER_HOST/PORT, SECOND_BRAIN_ROOT, VITE vars) | 2026-02-02 |
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

*Last updated: 2026-02-07 (BACKLOG-113: Website Redesign + BACKLOG-114: AI-Agentic Marketing Plan)*
*Reorganized by commercial release milestones*
