# Session 22 — Smoke Test, Object Tab Extraction, Pre-Release Prep

## Skill

Use `/planning-with-files` — Session 22

## Context

Session 21 committed v1.2.0 (Memory Layer admin complete) and decomposed MemoryPage.tsx by extracting HealthView, PrefetchView, and SessionsView into `pages/memory/`. The shell still holds the Objects tab + 6 modals at ~1,080 lines. Backend tests pass (327), frontend builds clean. All code is pushed.

**Session 21 shipped:**
- v1.2.0 committed: 7 new backend endpoints, 9 new FE hooks, 4-tab Memory page
- DEBT-139: Extracted HealthView (187 lines), PrefetchView (419), SessionsView (389), shared components (87)
- DEBT-141: Health tab retry/refresh button with spin animation
- Resolved 3 rebase conflicts against remote (backlog.md, Settings.tsx, next_session_prompt.md)
- Fixed orphan `ImportResult` import in Settings.tsx

**Open debt (small):** DEBT-138 (stats query consolidation), DEBT-140 (energy level enum)

## Read First (verified paths)

```
backlog.md                                               # Updated S21 — DEBT-139/141 done
frontend/src/pages/MemoryPage.tsx                        # 1,080 lines — Objects tab + 6 modals (extraction target)
frontend/src/pages/memory/HealthView.tsx                 # 187 lines — extracted S21
frontend/src/pages/memory/PrefetchView.tsx               # 419 lines — extracted S21
frontend/src/pages/memory/SessionsView.tsx               # 389 lines — extracted S21
frontend/src/pages/memory/components/shared.tsx          # 87 lines — StatCard, MiniBar, EnergyDots, helpers
```

## Priority-Ordered Task List

### Phase 1: Manual Smoke Test (15 min)

1. **Start dev servers** — backend + frontend
   - `cd backend && venv\Scripts\python.exe -m uvicorn app.main:app --reload`
   - `cd frontend && npm run dev`
2. **Memory page walkthrough** — verify all 4 tabs work identically to pre-refactor:
   - Objects tab: namespace sidebar, search, view/edit/create/delete
   - Prefetch tab: list, create, edit, toggle active, delete
   - Health tab: stats load, retry button works on error
   - Sessions tab: list, capture form, energy dots, expand/collapse
3. **Quick regression** — hit Dashboard, Projects, Settings to ensure no breakage

### Phase 2: Extract Objects Tab + Modals from MemoryPage (~60 min)

Complete DEBT-139 — bring MemoryPage.tsx under 300 lines.

Extract remaining components:
```
frontend/src/pages/memory/ObjectsView.tsx       # Namespace sidebar + object list + search
frontend/src/pages/memory/components/modals.tsx  # ViewObjectModal, EditObjectModal, CreateObjectModal,
                                                 # CreateNamespaceModal, EditNamespaceModal, DeleteNamespaceModal
```

**Acceptance criteria:**
- MemoryPage.tsx is a thin shell: header, tab switcher, conditional render — under 300 lines
- ObjectsView handles its own sidebar state, search, namespace menu
- Modals receive props (objectId, namespace, onClose) and are fully self-contained
- No behavior changes — pure refactor
- Frontend build clean after extraction

### Phase 3: Remaining Quick Debt (if time permits)

| ID | Description | Size | Notes |
|----|-------------|------|-------|
| DEBT-140 | Extract energy level constants (1-5) to shared enum | XS | `ENERGY_LEVELS` in shared types, used by SessionsView + CaptureModal |
| DEBT-138 | Consolidate `get_memory_stats` DB queries | S | 6+ queries → fewer round-trips |

### Phase 4: Pre-Release Checklist Review

1. Review `distribution-checklist.md` — identify what blocks alpha release
2. Check installer version in `conduital.iss` matches v1.2.0
3. Assess: is the app ready for a manual smoke test on a clean Windows VM?
4. Document any gaps in `backlog.md`

### Phase 5: Session Closeout

1. Backend tests: `backend\venv\Scripts\python.exe -m pytest backend/tests/ -x -q`
2. Frontend build: `cd frontend && npm run build`
3. Update `backlog.md` — mark completed items, log new debt
4. Commit with descriptive message
5. Push to origin
6. **Write Session 23 prompt → `next-prompt.md`** (do not skip this step)

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
- git commit with special chars: write message to temp file, use `git commit -F file.txt`
