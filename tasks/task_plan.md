# v1.1.0 Session 8: Backlog Hygiene + Quick Wins + Soft Delete

## Context
- 263 backend tests, 0 TS errors, clean Vite build
- Last commit: `c6c5e07` (Session 7)
- Branch: master, pushed to `gregdm98607/-conduital`
- CI pipeline green

## Phase 1: Backlog Housekeeping (No Code)

Session 7 completed DEBT-115, DIST-041, DIST-042 but didn't mark them Done.

1. Mark DEBT-115 → **Done** (Session 7) in backlog.md
2. Mark DIST-041 → **Done** (Session 7) in backlog.md
3. Mark DIST-042 → **Done** (Session 7) — CI tests+checks live, installer-on-tag still TODO
4. Update `backlog.md` Stats section (263 tests)
5. Update `progress.md` with Session 7 log entry
6. Update `tasks/lessons.md` with two new lessons from Session 7

## Phase 2: Quick Wins

### BACKLOG-143: CompleteTaskButton Accessibility (XS)
- Add `aria-label="Complete task"`, `focus-visible` ring, `aria-disabled` attribute
- Frontend only, no backend changes

### DEBT-007: Soft Delete Foundation (S)
- Add `deleted_at` nullable DateTime column to Project, Task, Area models
- Alembic migration (017)
- Implement `soft_delete()` in db_utils.py (replace NotImplementedError)
- Update delete endpoints to set `deleted_at` instead of hard delete
- Add `.where(Model.deleted_at.is_(None))` to all list queries
- Tests for soft delete behavior

## Phase 3: CI Enhancement
- Add `--cov` flag to pytest for coverage reporting (informational)
- Verify CI triggers already include main + master

## Phase 4: Verification + Wrap
1. Run all 3 verification checks
2. Update backlog.md, progress.md, lessons.md
3. Commit with clear message
4. Push to GitHub, verify CI green

## Acceptance Criteria
- [ ] DEBT-115, DIST-041, DIST-042 marked Done in backlog
- [ ] Session 7 + 8 log entries in progress.md
- [ ] CompleteTaskButton has aria-label, focus-visible, aria-disabled
- [ ] Soft delete works for Project, Task, Area
- [ ] All tests pass (263+ total)
- [ ] 0 TypeScript errors, clean Vite build
- [ ] Committed and pushed
