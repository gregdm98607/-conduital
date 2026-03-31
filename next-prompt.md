# Session 29 — VM Testing + User-Facing Polish

## Context

Session 28 was a lightweight session:

**Session 28 shipped:**
- **Gumroad upload verified** — `ConduitalSetup-1.2.0.exe` confirmed uploaded and downloadable from Gumroad product page.
- **No code changes** — Session focused on verification; codebase unchanged.

Backend tests: 346 passing. Frontend: TypeScript clean, Vite build clean.

**Open debt (small):** DEBT-013 (mobile), DEBT-015 (overlapping docs), DEBT-016 (WebSocket), DEBT-078 (venv python)

**Installer:** `ConduitalSetup-1.2.0.exe` (27.4 MB) at `installer/Output/` — built in S26, still current.

## Read First (verified paths)

```
tasks/vm-test-plan.md                                    # 40+ test cases — execute when ready
distribution-checklist.md                                # Phase 3.1 (code signing) deferred
backlog.md                                               # Central task/debt tracking
installer/Output/ConduitalSetup-1.2.0.exe                # Current installer
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

### Phase 3: User-Facing Polish

- **BACKLOG-152**: Ship at "Full" module mode (enable all modules for alpha users)
- **BACKLOG-151**: Display app version in sidebar
- **DEBT-013**: Mobile responsive improvements

### Phase 4: Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && npm run build`
3. Update `backlog.md`
4. Commit + push
5. **Write Session 30 prompt -> `next-prompt.md`**

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
