# Task Plan: v1.0.0 Release Preparation — Code & Infrastructure Work

**Goal:** Execute all distribution-checklist items that are code/config tasks (no human decisions required).
**Status:** `in_progress`
**Created:** 2026-02-07

---

## Scope: What Can Be Done Now

From findings.md Tier 2 + distribution-checklist Phases 0-1, these items are concrete engineering work:

### Selected Items (7 tasks)

| # | Source | Description | Effort |
|---|--------|-------------|--------|
| 1 | Checklist 0.5 | **JWT secret auto-generation on first run** | 30 min |
| 2 | Checklist 1.1 | **FastAPI static file serving for React build** (DIST-011) | 45 min |
| 3 | Checklist 1.2 | **Auto-run Alembic migrations on startup** | 20 min |
| 4 | Checklist 1.6 | **Single-process launcher script** (run.py) | 30 min |
| 5 | Checklist 4.4 | **GTD trademark audit — replace in UI text** | 30 min |
| 6 | Findings Tier 2 | **Dependency license audit** (DIST-020) | 20 min |
| 7 | Checklist 4.5 | **LICENSE file + THIRD_PARTY_LICENSES.txt** | 20 min |

**Total estimated: ~3.5 hours**

### Out of Scope (requires human decisions)
- 0.6 Product naming (Operaxis research done, awaiting final decision)
- Phase 2-3 PyInstaller/installer (requires naming + logo first)
- Phase 4.1-4.3 Legal documents (EULA, privacy policy, license key system)
- Phase 5 Gumroad setup (requires all above)

---

## Phase 1: JWT Secret Auto-Generation `pending`
- [ ] Review current config.py SECRET_KEY default behavior
- [ ] Add auto-generation using secrets.token_urlsafe(64) when no SECRET_KEY in env
- [ ] Persist generated secret to .env file on first run
- [ ] Remove weak default from config

## Phase 2: FastAPI Static File Serving `pending`
- [ ] Configure StaticFiles mount for frontend/dist/
- [ ] Add catch-all route for SPA client-side routing
- [ ] Test full app with only backend running
- [ ] Update vite.config.ts base path if needed

## Phase 3: Auto-Run Alembic Migrations `pending`
- [ ] Check if already wired in lifespan
- [ ] Handle first-run (no DB file yet)
- [ ] Handle already-current (no-op)
- [ ] Add error handling + logging

## Phase 4: Single-Process Launcher `pending`
- [ ] Create run.py entry point
- [ ] Port detection + browser auto-open
- [ ] Clean shutdown handling

## Phase 5: GTD Trademark Cleanup in UI `pending`
- [ ] Audit all "GTD" instances in frontend .tsx files
- [ ] Replace user-facing text with generic alternatives
- [ ] Keep internal code identifiers (module names, etc.)

## Phase 6: Dependency License Audit `pending`
- [ ] Scan all Python deps for license types
- [ ] Scan all npm deps for license types
- [ ] Flag any non-commercial-compatible licenses
- [ ] Generate THIRD_PARTY_LICENSES.txt

## Phase 7: LICENSE File `pending`
- [ ] Create proprietary LICENSE file
- [ ] Commit THIRD_PARTY_LICENSES.txt

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
