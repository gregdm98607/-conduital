# Task Plan: Session Wrap-Up & Beta Prep

**Status:** in_progress
**Date:** 2026-02-08
**Goal:** Clean slate for beta development — commit all work, archive clutter, update release planning

---

## Phase 1: Commit All Uncommitted Work

The alpha has shipped. All work since the last commit needs to be committed as a single coherent checkpoint.

### 1.1 Stage & Commit
- [ ] Stage all modified files
- [ ] Stage untracked source files (CHANGELOG, setup wizard, shutdown, tray, paths, build.bat, installer, spec)
- [ ] Do NOT stage `assets/` (design files — gitignored)
- [ ] Commit with descriptive message

### 1.2 Verify Clean Working Tree
- [ ] `git status` shows clean after commit
- [ ] Only gitignored files remain

---

## Phase 2: Root Directory Cleanup

Move dev-only, historical, and transitional files to `archive/` folder.

### 2.1 Create `archive/` directory and move files
### 2.2 Clean junk files (nul, tmpclaude-*.cwd, .coverage)
### 2.3 Update .gitignore with `archive/` exclusion

---

## Phase 3: Release Planning Update

### 3.1 Update backlog.md — add beta context, review parking lot
### 3.2 Update CHANGELOG.md — add [Unreleased] section for beta work
### 3.3 Update distribution-checklist.md — mark completed phases

---

## Phase 4: Final Verification

- [ ] `git status` clean
- [ ] Root directory tidy
- [ ] All tracking docs current
- [ ] Ready for tomorrow's beta work
