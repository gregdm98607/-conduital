# v1.1.0 Session 9: Soft Delete Coverage + Frontend Polish + Release Prep

## Goal
Complete soft delete coverage across entire backend, add frontend polish, prep for v1.1.0-beta tag.

## Phase 1: Soft Delete Coverage (Backend) — `in_progress`
### 1A: Fix `select()` gaps (~36 locations)
Files to fix:
- [ ] `app/services/intelligence_service.py` (9 gaps)
- [ ] `app/services/next_actions_service.py` (6 gaps)
- [ ] `app/services/export_service.py` (2 gaps)
- [ ] `app/services/ai_service.py` (2 gaps)
- [ ] `app/api/intelligence.py` (10 gaps)
- [ ] `app/api/export.py` (5 gaps)
- [ ] `app/api/areas.py` (get_area by ID)

### 1B: Fix `db.get()` gaps (~24 locations)
Files to fix:
- [ ] `app/api/areas.py` (update, delete, mark_reviewed, archive, unarchive)
- [ ] `app/services/project_service.py` (update, revert)
- [ ] `app/services/task_service.py` (update, complete, revert)
- [ ] `app/api/intelligence.py` (6 db.get calls)
- [ ] `app/api/projects.py` (mark_reviewed)
- [ ] `app/api/inbox.py` (5 db.get calls)
- [ ] `app/core/db_utils.py` (log_activity)
- [ ] `app/sync/sync_engine.py` (2 db.get calls)

### 1C: Tests for new coverage
- [ ] Test: updating soft-deleted project → 404
- [ ] Test: completing soft-deleted task → 404
- [ ] Test: intelligence queries exclude soft-deleted records
- [ ] Test: export excludes soft-deleted records

## Phase 2: Frontend Polish (Pick 2-3 XS items) — `pending`
Candidates:
- BACKLOG-135: Empty State Illustrations (SVG + copy)
- BACKLOG-136: Keyboard Shortcut Overlay (? key)
- BACKLOG-134: Momentum Delta Toast

## Phase 3: Release Prep — `pending`
- [ ] Update version strings to v1.1.0-beta
- [ ] Review backlog R1.1 section completeness
- [ ] Tag v1.1.0-beta if criteria met

## Phase 4: Verification + Wrap — `pending`
- [ ] Backend tests pass (target: ~280+)
- [ ] Frontend TS check: 0 errors
- [ ] Frontend build: clean
- [ ] Update backlog.md, progress.md, lessons.md
- [ ] Commit + push, CI green

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
