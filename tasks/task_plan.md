# Session 17 Task Plan — 2026-02-20

## Goal
Tech debt sweep: resolve stale debt items, fix remaining AI component issues, fix import service gaps, update backlog tracking.

## Phases

### Phase 1: Housekeeping + DEBT-133 — `pending`
- Delete `backend/requirements.txt` (stale, conflicts with pyproject.toml)
- Update `backend/README.md` — pip → poetry install instructions
- Update `build.bat` line 91 — error hint references requirements.txt
- Update `next_session_prompt.md` — backend test setup
- Mark 6 AI debt items as Done in backlog (DEBT-093/096/097/099/100/101)
- Mark DEBT-105 as N/A (description mismatch — no `mb-0` exists)

### Phase 2: DEBT-102 + DEBT-104 — AI endpoint fixes — `pending`
- DEBT-102: Add upfront `ANTHROPIC_API_KEY` check to proactive analysis + decompose endpoints
- DEBT-104: Convert pipe-delimited task parsing to JSON-structured parsing (matches pattern from ROADMAP-007)

### Phase 3: Import service fixes (DEBT-134/135/136/137) — `pending`
- DEBT-134/135: Add `deleted_at.is_(None)` filter to goals/visions dedup in import_service.py
- DEBT-136: Invalidate TanStack Query caches after successful import
- DEBT-137: Add client-side file size validation before import upload

### Phase 4: DOC-008 — Fresh install setup guide — `pending`
- Write new machine / fresh install setup guide
- Cover: Python, Poetry, venv, frontend deps, first run

### Phase 5: Session closeout — `pending`
- Update backlog.md stats + last updated date
- Write lessons learned
- Commit changes

## Decisions
- Skip BACKLOG-147/148/149 (machine migration story) — larger feature, defer to future session
- Focus on debt cleanup to reduce open debt count before R2

## Errors Encountered
None yet.
