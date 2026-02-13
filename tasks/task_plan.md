# Session 7: DEBT-115 Fix + GitHub Setup + Commit Session 6 (2026-02-XX)

## Context
- **Starting state**: 257 backend tests passing, 0 TS errors, clean Vite build
- **Last commit**: `bda86d3` — Session 6 (test hardening + UX polish)
- **Uncommitted work**: Session 6 Phase 3-4 changes (25 new tests, 4 UX polish items, backlog updates) — need to verify and commit
- **Branch**: master

## Goal
Fix the highest-priority latent bug (DEBT-115), set up GitHub remote + CI pipeline, and commit all outstanding work.

## Pre-Session Context Read
Read these files first to establish context:
- `tasks/lessons.md` — review patterns (especially tz-naive lessons from 2026-02-06)
- `backlog.md` — current state, DEBT-115 entry
- `CLAUDE.md` — project instructions
- `backend/app/services/ai_service.py` lines ~255-270 — DEBT-115 location 1
- `backend/app/services/project_service.py` lines ~310-325 — DEBT-115 location 2
- `backend/app/models/project.py` — column definitions for stalled_since, last_activity_at

---

## Phase 1: Verify + Commit Session 6 Outstanding Work

Session 6 made 2 commits but the second commit (bda86d3) may not include the final backlog.md and progress.md updates. Verify:

1. Run all 3 verification checks:
   - `cd /c/Dev/project-tracker/backend && poetry run python -m pytest tests/ -x -q`
   - `cd /c/Dev/project-tracker/frontend && npx tsc --noEmit`
   - `cd /c/Dev/project-tracker/frontend && npx vite build`
2. Check `git status` and `git diff` for any uncommitted Session 6 work
3. If there are uncommitted changes, commit them with a clear message
4. If clean, proceed to Phase 2

---

## Phase 2: DEBT-115 — Fix TZ-Naive Datetime Arithmetic (HIGH Priority)

### Problem
SQLite strips timezone info from DateTime columns. When code does:
```python
days_stalled = (datetime.now(timezone.utc) - project.stalled_since).days
```
...it crashes with `TypeError: can't subtract offset-naive and offset-aware datetimes` because `project.stalled_since` comes back from SQLite as a naive datetime.

### Locations
1. `backend/app/services/ai_service.py:261` — `datetime.now(timezone.utc) - project.stalled_since`
2. `backend/app/services/project_service.py:317` — `datetime.now(timezone.utc) - project.last_activity_at`

### Recommended Fix: Defensive `_ensure_tz_aware()` helper
```python
from datetime import datetime, timezone

def _ensure_tz_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (UTC). SQLite strips tz info."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
```

### Steps
1. **Audit**: Grep for ALL datetime arithmetic involving model fields across the backend
   - Pattern: `datetime.now.*-.*project\.` or `datetime.now.*-.*\.stalled_since` etc.
   - Check: `ai_service.py`, `project_service.py`, `intelligence_service.py`, `discovery_service.py`
2. **Implement**: Add `_ensure_tz_aware()` utility (either in a shared utils module or as a staticmethod)
3. **Apply**: Wrap all model datetime fields in `_ensure_tz_aware()` before arithmetic
4. **Test**: Add regression tests that specifically set naive datetimes (simulating SQLite) and verify no TypeError
5. **Verify**: 257+ tests passing, 0 TS errors

### Acceptance Criteria
- [ ] No `datetime.now(timezone.utc) - model_field` without `_ensure_tz_aware()` wrapper
- [ ] Regression test for stalled_since arithmetic
- [ ] Regression test for last_activity_at arithmetic
- [ ] All existing 257 tests still pass
- [ ] DEBT-115 marked Done in backlog.md

---

## Phase 3: GitHub Remote + CI Foundation (DIST-041 + DIST-042)

### DIST-041: GitHub Repo Setup
1. Create GitHub repo (private initially): `conduital/conduital` or `gregm/conduital`
2. Verify `.gitignore` covers all sensitive files (already comprehensive)
3. Push master branch to remote
4. Verify no secrets leaked (API keys, .env, etc.)

### DIST-042: CI Pipeline (GitHub Actions)
Create `.github/workflows/ci.yml`:
```yaml
name: CI
on: [push, pull_request]
jobs:
  backend-tests:
    runs-on: ubuntu-latest  # or windows-latest for Windows-specific testing
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install poetry && poetry install
      - name: Run tests
        run: poetry run python -m pytest tests/ -x -q
        working-directory: backend

  frontend-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
        working-directory: frontend
      - run: npx tsc --noEmit
        working-directory: frontend
      - run: npx vite build
        working-directory: frontend
```

### Steps
1. Ask user for GitHub repo name/org preference
2. Create repo via `gh repo create` (if gh CLI available) or instruct user
3. Add remote, push master
4. Create `.github/workflows/ci.yml`
5. Commit + push, verify CI passes

### Acceptance Criteria
- [ ] GitHub remote configured and pushed
- [ ] CI workflow runs backend tests + frontend checks
- [ ] First CI run passes green
- [ ] DIST-041 and DIST-042 marked Done in backlog.md

---

## Phase 4: Verification + Wrap

1. Run all verification checks one final time
2. Update `backlog.md` — mark completed items Done
3. Update `progress.md` — add Session 7 log
4. Update `tasks/lessons.md` if new patterns discovered
5. Commit all Session 7 work
6. Push to GitHub remote

---

## Stretch Goals (If Time Permits)

Pick 1-2 from this priority-ordered list:

| ID | Description | Effort | Impact |
|----|-------------|--------|--------|
| BACKLOG-143 | CompleteTaskButton accessibility (aria-label, focus-visible, aria-disabled) | XS | Accessibility |
| DEBT-007 | Soft delete not implemented | S | Data safety |
| DIST-023 | Path resolution for packaged exe | S | Distribution |
| DIST-051 | Register conduital.app domain | XS | Branding |
| DIST-030 | Windows code signing certificate | S | Trust/UX |

---

## Commands Reference
```bash
# Backend tests
cd /c/Dev/project-tracker/backend && poetry run python -m pytest tests/ -x -q

# Frontend TypeScript
cd /c/Dev/project-tracker/frontend && npx tsc --noEmit

# Frontend build
cd /c/Dev/project-tracker/frontend && npx vite build

# Git
cd /c/Dev/project-tracker && git status
cd /c/Dev/project-tracker && git log --oneline -5
```

## Key Lessons to Remember
- POSIX paths in bash: `/c/Dev/...` not `C:\Dev\...`
- Poetry managed: `poetry run python -m pytest`
- SQLite strips tz info — use `_ensure_tz_aware()` for model datetime fields
- When mocking AI: mock at `create_provider` factory level
- localStorage keys use `pt-` prefix
- Never leak raw `str(e)` in HTTP responses
- For Axios errors: check `err.response?.status`, not string matching
