# Session 27 — Clean VM Testing + Distribution Prep

## Context

Session 26 rebuilt the installer and shipped two feature items:

**Session 26 shipped:**
- **Installer rebuilt:** `ConduitalSetup-1.2.0.exe` (27.4 MB) — fresh build including all S25+S26 changes. Frontend + PyInstaller + Inno Setup all clean.
- **DEBT-008 (File watcher toggle):** Auto-discovery can now be enabled/disabled from Settings UI. Toggle persists to .env (persist-first pattern). Toggling ON starts the folder watcher at runtime with all 6 callbacks; toggling OFF stops it. New `_apply_auto_discovery()` helper in `settings.py`.
- **BACKLOG-154 (Discovery status in Settings):** `/discovery/status` endpoint now wired into Settings page. "Recent Discovery Activity" panel shows event log with success/error badges, timestamps, action names, folder paths. Auto-refreshes every 30s via `useDiscoveryStatus()` hook. Only renders when events exist.

Backend tests: 346 passing. Frontend: TypeScript clean, Vite build clean.

**Open debt (small):** DEBT-013 (mobile), DEBT-015 (overlapping docs), DEBT-016 (WebSocket), DEBT-078 (venv python)

**Installer:** `ConduitalSetup-1.2.0.exe` (27.4 MB) at `installer/Output/` — **FRESH BUILD** from S26. Ready for VM testing.

## Read First (verified paths)

```
tasks/vm-test-plan.md                                    # 40+ test cases — execute this plan
distribution-checklist.md                                # Phase 3.1 (code signing) is next decision
installer/conduital.iss                                  # Inno Setup script
installer/Output/ConduitalSetup-1.2.0.exe                # FRESH — built S26
backend/app/api/settings.py                              # DEBT-008: auto_discovery_enabled + _apply_auto_discovery()
frontend/src/pages/Settings.tsx                           # BACKLOG-154: Discovery Activity panel
frontend/src/hooks/useDiscovery.ts                       # useDiscoveryStatus() hook
frontend/src/services/api.ts                             # getDiscoveryStatus() + updated sync types
```

## Priority-Ordered Task List

### Phase 1: Clean VM Testing (~60 min)

Follow the test plan in `tasks/vm-test-plan.md`:
1. Set up Windows 10 evaluation VM (Hyper-V or VirtualBox)
2. Set up Windows 11 evaluation VM
3. Copy `installer/Output/ConduitalSetup-1.2.0.exe` to each VM
4. Execute all 9 test sections on each VM
5. Record results in `tasks/vm-test-plan.md` test tables
6. Log any issues found as new DEBT/BACKLOG items

**Note:** This is a manual GUI task. Claude can guide through setup and record results interactively.

### Phase 2: Code Signing Decision (~15 min)

Review options and decide:
1. **Standard certificate** (~$70-200/yr from SSL.com, Sectigo, or Certum)
   - Requires SmartScreen reputation building
2. **EV certificate** (~$350-500/yr)
   - Immediate SmartScreen trust
3. **Defer** — ship alpha without signing
   - Acceptable for early adopters / testers

Reference: `distribution-checklist.md` Phase 3.1

### Phase 3: Fix VM Test Issues (if any)

Based on VM testing results:
1. Fix any blocker/major issues
2. Rebuild exe + installer if code changes needed
3. Retest on affected VM
4. Log minor issues as new DEBT items

### Phase 4: Remaining Debt (if time permits)

- DEBT-013: Mobile responsive improvements (medium effort — sidebar drawer needed)
- DEBT-015: Overlapping setup docs cleanup
- BACKLOG-152: Ship at "Full" module mode

### Phase 5: Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && npm run build`
3. Update `backlog.md`
4. Commit + push
5. **Write Session 28 prompt -> `next-prompt.md`**

## End-of-Session Protocol

1. Backend tests pass
2. TypeScript clean (`npx tsc --noEmit`)
3. Vite build clean
4. Update `backlog.md`
5. Commit + push
6. Post-session audit -> new DEBT items
7. **Design next session prompt -> `next-prompt.md`**

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- npm/vite: use `cmd` shell with `cd X && npm ...` pattern
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`
