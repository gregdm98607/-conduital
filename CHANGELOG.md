# Changelog

All notable changes to Conduital will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **BACKLOG-120:** "Make Next Action" / "Move to Other" quick actions on ProjectDetail bulk toolbar — promote/demote tasks between Next Actions and Other Tasks with one click
- **BACKLOG-119:** Task Push/Defer quick action — clock icon on task items opens popover with "1 Week" / "1 Month" presets and custom date picker; defers task to Over the Horizon zone. Available on ProjectDetail and NextActions pages.
- Graceful shutdown endpoint (`POST /api/v1/shutdown`) — localhost-only, cooperative with system tray and installer
- AbortSignal support on all 27 API client getter methods — enables HTTP request cancellation on component unmount
- Momentum settings validation — server returns HTTP 422 when at-risk threshold >= stalled threshold; client shows inline warning
- **BETA-001:** Graduated next-action scoring — 4-tier scale (0, 0.3, 0.7, 1.0) based on next-action age replaces binary 0/1. Eliminates cliff effect.
- **BETA-002:** Exponential activity decay — `e^(-days/7)` replaces linear `1-(days/30)`. Recent activity matters more; stale activity fades faster.
- **BETA-003:** Sliding completion window — 30-day weighted window (7d×1.0, 14d×0.5, 15-30d×0.25) replaces hard 7-day cutoff.
- **BETA-004:** Logarithmic frequency scaling — `log(1+count)/log(11)` replaces `min(1, count/10)`. Diminishing returns per action.
- **BETA-020:** `previous_momentum_score` column on projects for trend/delta calculation
- **BETA-021:** `MomentumSnapshot` table for daily momentum history (sparklines, trend data)
- **BETA-022:** Alembic migration `011_momentum_snapshots`
- **BETA-023:** Scheduled recalculation job now creates daily momentum snapshots
- **BETA-024:** Momentum history API — `GET /intelligence/momentum-history/{id}` (sparkline data) and `GET /intelligence/dashboard/momentum-summary` (aggregate trend counts)
- **BETA-010:** Momentum trend indicator — up/down/stable arrow on ProjectCard based on `previous_momentum_score` delta
- **BETA-011:** Momentum sparkline — inline 2-point SVG trend line on ProjectCard (rising/falling/flat)
- **BETA-012:** Project completion progress bar — thin gradient bar on ProjectCard showing `completed/total` tasks
- **BETA-013:** "Almost there" nudge — subtle text when >80% tasks complete: "N tasks to finish line" (Goal Gradient + Zeigarnik)
- **BETA-014:** Dashboard momentum summary — aggregate section showing gaining/steady/declining project counts with declining project links
- **BETA-030:** Weekly review completion tracking — `POST /intelligence/weekly-review/complete` persists completion timestamp + notes; `GET /intelligence/weekly-review/history` returns completion history with `days_since_last_review`. New `WeeklyReviewCompletion` model + Alembic migration `012`. Dashboard shows "Last completed: X days ago".
- **BETA-031:** Inbox batch processing — `POST /inbox/batch-process` endpoint for bulk actions (assign_to_project, delete, convert_to_task). Frontend: multi-select checkboxes, select-all toggle, bulk action toolbar with project dropdown.
- **BETA-032:** Inbox processing stats — `GET /inbox/stats` returns `unprocessed_count`, `processed_today`, `avg_processing_time_hours`. Replaces client-side calculation (DEBT-064).
- **BETA-034:** Inbox item age indicator — subtle visual aging on unprocessed items: gray clock (24h-3d), amber (3d-7d), red (>7d). Informational, not gamified.

### Changed
- **DEBT-083:** Installer graceful shutdown — `InitializeSetup()` and `InitializeUninstall()` now try `POST /api/v1/shutdown` before falling back to `taskkill /F`. Gives the running app 8 seconds to shut down cleanly.
- **BACKLOG-116 / DEBT-080:** Version single source of truth — `config.py` now reads version from `pyproject.toml` at startup; `scripts/sync_version.py` propagates to `package.json`, `conduital.iss`, and `config.py` fallback. Only edit `pyproject.toml` to change version.
- **DEBT-061:** Project model `task_count` and `completed_task_count` are now explicit class attributes with defaults, replacing fragile dynamic `setattr()` assignment in service layer.

### Fixed
- **DEBT-039:** MemoryPage priority inputs now clamp values to 0-100 range — prevents out-of-range values entered via keyboard
- `build.bat` size reporting shows correct total (was always "~0 MB" due to broken findstr parsing)

### Accessibility
- Modal: `role="dialog"`, `aria-modal="true"`, `aria-labelledby` linking title to dialog
- UserMenu: `aria-haspopup="menu"`, `aria-expanded`, `role="menu"` and `role="menuitem"`
- ProjectCard: outcome toggle has `aria-expanded` and descriptive `aria-label`
- Settings: API key visibility toggle has `aria-label`

## [1.0.0-alpha] - 2026-02-08

### Added
- Core CRUD for projects, tasks, areas, contexts, goals, and visions
- Markdown file sync with Google Drive compatibility (bidirectional)
- Auto-discovery of projects and areas from folder structure
- Momentum scoring with configurable thresholds (stalled, at-risk, decay)
- Next actions prioritization with MYN urgency zones (Critical Now, Opportunity Now, Over the Horizon)
- Dashboard with stalled projects widget, area health overview, and review reminders
- Weekly review checklist with interactive progress tracking
- Daily execution dashboard with prioritized task view
- Quick capture with project assignment and keep-open batch entry
- Data export (JSON) and database backup (SQLite) with preview UI
- Google OAuth authentication (optional, single-user)
- Multi-AI provider support (Anthropic Claude, OpenAI, Google) with graceful degradation
- AI-powered "Get Unstuck" task generation
- AI context export for external AI sessions
- Memory layer with namespace management, search, and CRUD
- User onboarding wizard with initial memory object creation
- Module system with commercial presets (basic, gtd, proactive_assistant, full)
- Sidebar module-aware navigation
- Dark mode with Settings toggle
- Collapsible settings sections and urgency zone sections
- Project health indicators, review badges, and mark-reviewed workflow
- Area health scores, archival workflow, and quick actions
- Momentum settings UI (stalled/at-risk thresholds, decay rate, recalculation interval)
- CORS configuration from environment variable
- Whitespace-only content validation on all title/content fields
- Global React error boundary with retry protection
- Toast notification deduplication
- FastAPI static file serving for production builds (no Node.js runtime required)
- Single-process launch via `run.py` with auto port detection and browser open
- Auto-run database migrations on startup
- Comprehensive third-party license documentation

### Fixed
- SPA catch-all route excludes `/modules`, `/health`, and `/openapi.json` endpoints, preventing JSON responses from being overridden by `index.html` in production builds
- Duplicate blob download logic extracted into shared helper method in API client

### Changed
- All "GTD", "PARA", and "Second Brain" trademark references removed from model docstrings, module comments, AI prompts, scripts, and documentation — replaced with generic methodology descriptions
- API documentation updated to reflect app name ("Conduital") and version
- Momentum section in Settings has Activity icon matching other sections
- .gitignore hygiene: restored user-facing API docs; excluded dev-only files, Office temp files, and design assets

### Security
- Auto-generated JWT secret on first run (persisted to .env)
- Hardcoded paths removed from all committed files
- API key file excluded from repository
- CORS origins configurable via environment variable

### Infrastructure
- 174/174 backend tests passing
- Semantic versioning established (single source of truth across config files)
- Dependency license audit complete (all permissive: MIT, BSD, Apache 2.0, ISC)
- Locked dependency versions (requirements.txt, poetry.lock, package-lock.json)
- Dev artifacts excluded from distribution via .gitignore
- Pydantic V2 migration complete (no V1 deprecation warnings)
- FastAPI lifespan context manager (no deprecated on_event handlers)
- SQLAlchemy best practices (.is_() for boolean comparisons)
