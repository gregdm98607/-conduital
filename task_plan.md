# Task Plan: v1.0.0 Release Prep — Round 3 (Deep Cleanup)

**Goal:** Find and fix all remaining pre-Conduital references, verify builds, clean distribution checklist.
**Status:** `complete`
**Created:** 2026-02-07 (Session 3)

---

## Context

Round 1 (commit 0662006) completed: JWT auto-gen, static serving, Alembic startup, run.py launcher, GTD UI cleanup, LICENSE, THIRD_PARTY_LICENSES.txt.

Round 2 (commit d9b538e) completed: Full Conduital rebrand (56 user-facing occurrences), GTD/PARA/Second Brain trademark cleanup, branding research blob removal. 30 files changed, +306/-1,801.

Namespace claims completed: conduital.com purchased, @conduital claimed on GitHub/X/Gumroad.

## Completed Tasks (6 items)

| # | Source | Description | Status |
|---|--------|-------------|--------|
| 1 | Audit | **Clean 18 internal "Project Tracker" references** — docstrings/comments across 15 Python/TypeScript files | ✅ |
| 2 | Testing | **Fix FastAPI title** — local .env had stale APP_NAME override (Pydantic BaseSettings precedence) | ✅ |
| 3 | Audit | **Fix alembic.ini path** — `.project-tracker/` → `.conduital/` database path | ✅ |
| 4 | Audit | **Fix package.json name** — `project-tracker-frontend` → `conduital-frontend` | ✅ |
| 5 | Audit | **Clean distribution-checklist.md** — 8 stale "ProjectTracker" refs + 1 "Second Brain" in future phases | ✅ |
| 6 | All | **Build verification + commit + update tracking docs** | ✅ |

### Build Verification
- TypeScript: clean (0 errors)
- Vite build: clean (576KB)
- Python compile: PASS (all backend files)

### Still Out of Scope (requires external action)
- Icon/favicon design — deferred to Phase 5
- Phase 1.3: User data directory (%LOCALAPPDATA%\Conduital\)
- Phase 1.4: First-run setup wizard
- Phase 1.5: Graceful AI degradation testing
- Phase 2-5: PyInstaller, installer, legal docs, Gumroad

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| .env APP_NAME override | Discovered via static serving test | Updated local .env (gitignored) from "Project Tracker" to "Conduital" |
