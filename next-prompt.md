# Session 30 — VM Testing + Installer Upload

## Context

Session 29 shipped four items + rebuilt the installer:

**Session 29 shipped:**
- **BACKLOG-152**: Default `COMMERCIAL_MODE` changed from `"basic"` to `"full"` — all modules enabled by default for alpha users.
- **DEBT-013**: Mobile responsive — collapsible sidebar with hamburger menu (slide-in drawer on mobile, static on md+), responsive padding (`p-4 md:p-8`) on all 16 pages, mobile header bar.
- **BACKLOG-133**: Smooth card reorder animations — zero-dependency FLIP hook (`useFlipAnimation`), wired into Projects grid + AllTasks card view.
- **Fixes**: Unused `FolderSync` import removed from SetupWizard.tsx; two AI decompose-tasks tests patched for full-mode.
- **Installer rebuilt**: `ConduitalSetup-1.2.0.exe` (28 MB) at `C:\Dev\conduital\installer\Output\` — includes all S29 changes.

Backend tests: 454 passing. Frontend: TypeScript clean, Vite build clean.

**Open debt (small):** DEBT-015 (overlapping docs), DEBT-016 (WebSocket), DEBT-078 (venv python)

## Read First (verified paths)

```
tasks/vm-test-plan.md                                    # 40+ test cases — execute when ready
distribution-checklist.md                                # Phase 3.1 (code signing) deferred
backlog.md                                               # Central task/debt tracking
installer/Output/ConduitalSetup-1.2.0.exe                # Current installer (rebuilt S29)
```

## Priority-Ordered Task List

### Phase 1: Clean VM Testing (~60 min, manual)

**This is the highest-priority remaining pre-beta gate.**

Follow the test plan in `tasks/vm-test-plan.md`:
1. Set up Windows 10 evaluation VM (Hyper-V or VirtualBox)
2. Set up Windows 11 evaluation VM
3. Copy `installer/Output/ConduitalSetup-1.2.0.exe` to each VM
4. Execute all 9 test sections on each VM
5. Record results in `tasks/vm-test-plan.md` test tables
6. Log any issues found as new DEBT/BACKLOG items

**Note:** This is a manual GUI task. Claude can guide through setup and record results interactively.

### Phase 2: Fix VM Test Issues (if any)

Based on VM testing results:
1. Fix any blocker/major issues
2. Rebuild exe + installer if code changes needed
3. Retest on affected VM
4. Log minor issues as new DEBT items

### Phase 3: Upload New Installer to Gumroad

If VM tests pass (or after fixes):
1. Upload `ConduitalSetup-1.2.0.exe` to Gumroad product page (replaces S26 build)
2. Verify download works from Gumroad

### Phase 4: Additional Polish (if time)

- **Discrepancy**: `config.py` COMMERCIAL_PRESETS and `registry.py` COMMERCIAL_PRESETS disagree on what "basic" includes (config: core+projects, registry: core+projects+gtd_inbox). Low priority since default is "full", but should be aligned.
- **DEBT-015**: Consolidate overlapping setup documentation
- **DEBT-016**: WebSocket updates not integrated

### Phase 5: Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && npm run build`
3. Update `backlog.md`
4. Commit + push
5. **Write Session 31 prompt -> `next-prompt.md`**

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- npm/vite: use `cmd` shell with `cd X && npm ...` pattern
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`
