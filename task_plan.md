# Task Plan: v1.1.0 Full Commercial Release

**Status:** planning
**Date:** 2026-02-11
**Goal:** First full commercial release of Conduital — AI-augmented productivity with all modules enabled.
**Version:** v1.0.0-beta → v1.1.0

---

## Release Philosophy

The full release builds on the solid beta foundation (v1.0.0-beta) by adding:
1. **AI-powered features** that differentiate Conduital (R3/R4 items)
2. **Professional polish** that meets commercial quality bar
3. **Distribution readiness** (code signing, testing, documentation)

The beta already ships: momentum intelligence, GTD inbox, file sync, horizons (goals/visions/contexts), and the full module system. The full release adds the AI brain on top.

---

## Phase 1: AI Core Features (Tier 1 Must-Ship)

*The primary value differentiator — "AI That Actually Helps"*

### Phase 1A: ROADMAP-002 — AI Features Integration

**Scope:** Bring AI analysis, suggestions, and prioritization to the forefront. Currently the backend has:
- `GET /ai/analyze/{project_id}` — project analysis
- `POST /ai/suggest-next-action/{project_id}` — next action suggestion
- `POST /tasks/{project_id}/unstuck` — generate unstuck task
- NPM fields already fed into AI prompts (BACKLOG-124 done)

**Work needed:**
- [ ] AI analysis summary on ProjectDetail (prominent placement)
- [ ] AI-suggested next actions surfaced on Dashboard ("AI recommends...")
- [x] Proactive stalled project analysis (auto-trigger when momentum drops) ✅
- [x] AI task decomposition from brainstorm notes (NPM Step 3 → tasks) ✅
- [x] Priority rebalancing suggestions when Opportunity Now overflows ✅
- [x] Energy-matched task recommendations ✅

**Estimated sessions:** 2-3

### Phase 1B: ROADMAP-007 — GTD Weekly Review with AI Advisors

**Scope:** Transform the weekly review from a manual checklist into an AI-guided dialogue.

**Current state:** Weekly review is a localStorage-based checklist (BACKLOG-024 done) with completion tracking (BETA-030 done). No AI involvement.

**Work needed:**
- [ ] AI review co-pilot: "Let's review your projects. Project X has been stalled for 14 days. What's blocking it?"
- [ ] AI-generated review summary: portfolio health, trend analysis, recommendations
- [ ] AI identifies projects that need attention (stalled, declining momentum, overdue reviews)
- [ ] Suggested next actions for each reviewed project
- [ ] Review session persistence (save AI dialogue + user decisions)
- [ ] Integration with existing weekly review completion tracking

**Estimated sessions:** 2-3

---

## Phase 2: Professional Polish (Tier 2 Should-Ship)

### Phase 2A: UI Consistency & Missing Features

| ID | Task | Est. |
|----|------|------|
| BACKLOG-104 | Area Health Drill-Down UI (backend ready) | 1-2h |
| BACKLOG-128 | Badge Configuration & Today's Focus layout | 2-3h |
| BACKLOG-101 | Dashboard Stats Block visual consistency | 1-2h |
| BACKLOG-099 | Archive Area confirmation dialog | 1h |
| BACKLOG-062 | Project Standard of Excellence | 2-3h |

### Phase 2B: Data & Memory Features

| ID | Task | Est. |
|----|------|------|
| BACKLOG-090 | Data Import from JSON backup | 2-3h |
| BACKLOG-082 | Session Summary Capture | 3-4h |
| BACKLOG-087 | Starter Templates by Persona | 2-3h |

### Phase 2C: Technical Housekeeping

| ID | Task | Est. |
|----|------|------|
| DEBT-010 | Update outdated dependencies | 1-2h |
| DOC-005 | Module system user documentation | 2-3h |
| DEBT-081 | App icon (.ico with 16-256px variants) | 1h (design) + 30m (integration) |

**Estimated sessions:** 3-4

---

## Phase 3: Distribution Readiness (Tier 1 Must-Ship)

### Phase 3A: Testing

| ID | Task | Notes |
|----|------|-------|
| BACKLOG-118 | Clean Windows VM testing | Win10 + Win11 VMs, no Python/Node |
| BACKLOG-117 | Upgrade-in-place testing | Install v1.0.0-beta, then v1.1.0 over it |

### Phase 3B: Code Signing & Packaging

| ID | Task | Notes |
|----|------|-------|
| DIST-030 | Windows code signing certificate | ~$70-200/yr, eliminates "Unknown Publisher" |
| Rebuild | Installer + exe with new icon + version | Full build.bat + ISCC cycle |

### Phase 3C: Documentation

| ID | Task | Notes |
|----|------|-------|
| DOC-005 | Module system docs (user-facing) | How presets work, what each enables |
| DOC-001 | Area mapping configuration guide | For file sync users |
| DOC-002 | Folder watcher troubleshooting | Common issues + fixes |

**Estimated sessions:** 2-3

---

## Phase 4: Nice to Have (Tier 3 — if time permits)

| ID | Task |
|----|------|
| BACKLOG-093 | Quick Capture success animation |
| BACKLOG-095 | Collapsible sections extension |
| BACKLOG-049 | Project Workload Indicator |
| BACKLOG-050 | Project Blocked/Waiting Status |
| R3 Nice-to-Have | Memory Namespace UI, Prefetch Config, Progress Dashboard, Memory Diff |

---

## Phase 5: Release (v1.1.0)

### Pre-Release Checklist

| Step | Description |
|------|-------------|
| 1 | All Tier 1 items complete |
| 2 | All Tier 2 items complete or explicitly deferred with rationale |
| 3 | Bump version `1.0.0-beta` → `1.1.0` |
| 4 | Run `sync_version.py` to propagate |
| 5 | Finalize CHANGELOG.md |
| 6 | Full test suite pass (target: 250+ tests) |
| 7 | TypeScript clean build |
| 8 | Vite production build |
| 9 | Build signed installer |
| 10 | Clean VM testing pass |
| 11 | Upgrade-in-place testing pass |
| 12 | Create annotated git tag `v1.1.0` |
| 13 | Distribution (Gumroad, GitHub) |

---

## Implementation Order (Suggested Sessions)

### Session 1: Quick Wins + AI Surface ✅ DONE
- ~~DEBT-081: Design and integrate app icon~~ ✅
- ~~BACKLOG-104: Area Health Drill-Down UI~~ ✅
- ~~BACKLOG-099: Archive Area confirmation dialog~~ ✅
- ~~DEBT-010: Dependency audit (pyproject.toml + package.json)~~ ✅
- ~~AI analysis prominent on ProjectDetail~~ ✅
- ~~AI suggestions on Dashboard~~ ✅

### Session 2-3: AI Features Integration (ROADMAP-002) ✅ DONE
- ~~Proactive stalled project analysis~~ ✅
- ~~AI task decomposition from brainstorm notes~~ ✅
- ~~Priority rebalancing suggestions (Opportunity Now overflow)~~ ✅
- ~~Energy-matched task recommendations~~ ✅

### Session 4-5: AI Weekly Review Co-Pilot (ROADMAP-007)
- AI review dialogue system
- Review summary generation
- Integration with existing review tracking
- Review session persistence

### Session 6: UI Polish Batch (Phase 2A)
- BACKLOG-128: Badge configuration
- BACKLOG-101: Dashboard stats consistency
- BACKLOG-062: Project Standard of Excellence

### Session 7: Data & Memory Features (Phase 2B)
- BACKLOG-090: Data import
- BACKLOG-082: Session summary capture
- BACKLOG-087: Starter templates

### Session 8: Tech Debt & Docs (Phase 2C)
- DEBT-010: Dependency updates
- DOC-005, DOC-001, DOC-002: Documentation

### Session 9: Distribution (Phase 3)
- DIST-030: Code signing setup
- BACKLOG-118: Windows VM testing
- BACKLOG-117: Upgrade testing
- Installer rebuild with icon + signing

### Session 10: Release (Phase 5)
- Version bump, CHANGELOG, full test suite
- Build signed installer
- Clean VM smoke test
- Tag + distribute

---

## Parking Lot Promotions Summary

**Promoted to Tier 2 (Should Ship):**
- BACKLOG-104 (Area Health Drill-Down) — from Parking Lot
- BACKLOG-128 (Badges) — from Parking Lot
- BACKLOG-101 (Dashboard consistency) — from Parking Lot
- BACKLOG-099 (Archive confirmation) — from Parking Lot
- BACKLOG-090 (Data Import) — from Parking Lot

**Promoted to Tier 3 (Nice to Have):**
- BACKLOG-093 (Capture animation) — from Parking Lot
- BACKLOG-095 (Collapsible sections) — from Parking Lot

**Kept in Parking Lot (Deferred):**
- BACKLOG-009, 040, 110, 121 — low impact or large scope
- BACKLOG-113, 114 — separate marketing workstreams

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| AI features take longer than estimated | Delays release | Start with minimal viable AI features, iterate |
| Code signing process complex | Minor delay | Research process early, purchase cert in Session 1 |
| Windows VM testing reveals issues | Could be significant | Test early (before AI work), fix in parallel |
| Dependency updates break things | Test regressions | Update one at a time, run full suite after each |

---

*Plan created 2026-02-11*
