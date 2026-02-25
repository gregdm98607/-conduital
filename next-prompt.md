# Session 25 — Clean VM Testing + Code Signing Decision

## Context

Session 24 completed the installer compilation pipeline and distribution prep. Inno Setup 6.7.1 installed, `ConduitalSetup-1.2.0.exe` compiled successfully (27.4 MB). Privacy policy drafted and served via `/api/v1/legal/privacy`. Full clean build verified: frontend clean, PyInstaller ~62 MB, 327 backend tests passing.

**Session 24 shipped:**
- Inno Setup 6.7.1 installed (user-local: `%LOCALAPPDATA%\Programs\Inno Setup 6\`)
- `ConduitalSetup-1.2.0.exe` compiled (27.4 MB) at `installer/Output/`
- Full clean PyInstaller build (~62 MB)
- Privacy policy (`PRIVACY_POLICY.md` — 8 sections, local-first focused)
- `/api/v1/legal/privacy` endpoint added to main.py
- `PRIVACY_POLICY.md` bundled in installer .iss
- Distribution checklist Phase 4.3 marked done

**Installer ready for testing but NOT yet tested on clean VMs.**

**Open debt (small):** DEBT-008 (file watcher), DEBT-013 (mobile), DEBT-015 (overlapping docs), DEBT-016 (WebSocket), DEBT-017 (debounce), DEBT-018 (network), DEBT-019 (silent failures), DEBT-075 (settings mutation), DEBT-078 (venv python)

Backend tests: 327 passing. Frontend: TypeScript clean, Vite build clean.

## Read First (verified paths)

```
tasks/vm-test-plan.md                                    # 40+ test cases — execute this plan
distribution-checklist.md                                # Phase 3.1 (code signing) is next decision
installer/conduital.iss                                  # Includes PRIVACY_POLICY.md now
installer/Output/ConduitalSetup-1.2.0.exe                # Ready for VM testing
PRIVACY_POLICY.md                                        # Drafted S24
backend/app/main.py                                      # Privacy endpoint at line ~317
```

## Priority-Ordered Task List

### Phase 1: Clean VM Testing (~60 min)

Follow the test plan in `tasks/vm-test-plan.md`:
1. Set up Windows 10 evaluation VM (download from Microsoft if not already available)
2. Set up Windows 11 evaluation VM
3. Copy `installer/Output/ConduitalSetup-1.2.0.exe` to each VM
4. Execute all 9 test sections on each VM
5. Record results in `tasks/vm-test-plan.md` test tables
6. Log any issues found as new DEBT/BACKLOG items

**VM download links:**
- Windows 10: https://www.microsoft.com/en-us/software-download/windows10ISO
- Windows 11: https://www.microsoft.com/en-us/software-download/windows11

**Note:** VMs need at least 4 GB RAM, 64 GB disk. Use Hyper-V (built into Win11 Pro) or VirtualBox.

### Phase 2: Code Signing Decision (~15 min)

Review options and decide:
1. **Standard certificate** (~$70-200/yr from SSL.com, Sectigo, or Certum)
   - Requires SmartScreen reputation building (first installs still warn)
   - Cheaper, simpler
2. **EV certificate** (~$350-500/yr)
   - Immediate SmartScreen trust, no "Unknown Publisher" warning
   - More expensive, requires hardware token
3. **Defer** — ship alpha without signing
   - Users must click through SmartScreen warnings
   - Acceptable for early adopters / testers

Reference: `distribution-checklist.md` Phase 3.1

### Phase 3: Fix VM Test Issues (if any)

Based on VM testing results:
1. Fix any blocker/major issues
2. Rebuild exe + installer if code changes needed
3. Retest on affected VM
4. Log minor issues as new DEBT items

### Phase 4: Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && npm run build`
3. Update `backlog.md` — mark completed items, log new debt
4. Commit with descriptive message
5. Push to origin
6. **Write Session 26 prompt → `next-prompt.md`** (do not skip this step)

## End-of-Session Protocol

1. Backend tests pass
2. TypeScript clean (`npx tsc --noEmit`)
3. Vite build clean
4. Update `backlog.md`
5. Commit + push
6. Post-session audit → new DEBT items
7. **Design next session prompt → `next-prompt.md`**

## Shell Notes (Windows-specific)

- Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
- npm/vite: use `cmd` shell with `cd X && npm ...` pattern
- Inno Setup: `"$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe" installer/conduital.iss`
- git commit with special chars: write message to temp file, use `git commit -F file.txt`
