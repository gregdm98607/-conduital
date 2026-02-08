# Task Plan: v1.0.0 Release Prep -- Round 7

**Goal:** Deep branding cleanup, strategic consistency fix, backlog hygiene, package-lock rebrand, backend docstring cleanup.
**Status:** `complete`
**Created:** 2026-02-07 (Session 7)

---

## Context

Rounds 1-6 completed: static serving, rebrand, migrations, Pydantic cleanup, end-to-end testing, bug fixes, accessibility, AI degradation, docs rebrand, test infra, version SSoT, 174/174 tests passing. Round 7 addresses deeper branding issues (backend docstrings, Skills directory, backlog Second Brain refs), strategic inconsistency (STRAT-001), backlog hygiene (22 done items cluttering active tables), and package-lock.json rebrand.

## Tasks (8 items)

| # | Source | Description | Status |
|---|--------|-------------|--------|
| 1 | STRAT-001 | **Fix strategic decision inconsistency** -- STRAT-001 said "SaaS Web-Only" but actual strategy is "Desktop-first"; corrected in backlog.md | Complete |
| 2 | Branding | **Clean Second Brain refs from backlog.md** -- 4 user-facing instances replaced (R1 target, R1 features x2, distribution model description) | Complete |
| 3 | Branding | **Clean backend Python docstrings** -- 10 files: Second Brain -> synced notes folder, PARA naming conventions -> numbered prefix conventions, logger messages updated | Complete |
| 4 | Branding | **Clean Skills directory** -- 17 replacements across 7 skill files: Project Tracker/Project-Tracker -> Conduital, Second Brain -> synced notes/file sync | Complete |
| 5 | Hygiene | **Backlog table cleanup** -- moved 22 Done/N/A items from Medium and Low priority debt tables to Completed Items table; removed 8 done items from Parking Lot; cleaned BACKLOG-113 description | Complete |
| 6 | Branding | **Expand .gitignore** -- added 5 missing dev files: MODULE_SYSTEM.md, Skills/, backend/diagnose.py, frontend/FRONTEND_IMPLEMENTATION_GUIDE.md, frontend/SETUP_AND_TEST.md | Complete |
| 7 | Branding | **Regenerate package-lock.json** -- name updated from "project-tracker-frontend" to "conduital-frontend" | Complete |
| 8 | All | **Build verification** -- TypeScript OK, Vite build OK (576KB), Python compile OK, 174/174 tests pass | Complete |

---

## Files Modified

### Direct edits
- `backlog.md` -- STRAT-001 fix, Second Brain cleanup (4 refs), 22 done items moved, Parking Lot cleaned, BACKLOG-113 condensed, last-updated line
- `.gitignore` -- added 5 missing dev file exclusions

### Background agent: Python docstrings (10 files)
- `backend/app/services/discovery_service.py` -- docstring cleanup
- `backend/app/services/area_discovery_service.py` -- docstring cleanup
- `backend/app/sync/file_watcher.py` -- module/class/param docstrings
- `backend/app/sync/folder_watcher.py` -- param docstring
- `backend/app/sync/markdown_parser.py` -- module docstring
- `backend/app/sync/markdown_writer.py` -- module/param docstrings
- `backend/app/sync/sync_engine.py` -- docstrings + logger message
- `backend/app/sync/__init__.py` -- module docstring
- `backend/app/core/config.py` -- comment + property docstring
- `backend/app/main.py` -- logger message

### Background agent: Skills directory (7 files)
- `Skills/capture-inbox.md` -- 3 replacements
- `Skills/context-switch.md` -- 1 replacement
- `Skills/daily-planning.md` -- 4 replacements
- `Skills/momentum-review.md` -- 1 replacement
- `Skills/next-actions-dashboard.md` -- 1 replacement
- `Skills/project-health-check.md` -- 1 replacement
- `Skills/sync-brain.md` -- 6 replacements

### Package regeneration
- `frontend/package-lock.json` -- name "project-tracker-frontend" -> "conduital-frontend"

## Errors Encountered

None.
