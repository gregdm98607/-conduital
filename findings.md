# Findings: v1.0.0-alpha Release Readiness Assessment

**Date:** 2026-02-07
**Context:** PM + CTO consultation on release strategy

---

## 1. Release Milestone Inventory

### R1: PT Basic — COMPLETE (Released 2026-02-03)
- All Must Have items: DONE
- 2 Should Have deferred (BACKLOG-076 UX consistency, DOC-005 module docs)
- In user testing since Feb 3

### R2: PT GTD — COMPLETE
- All Must Have, Should Have, Nice to Have: DONE
- GTD inbox, weekly review, MYN daily execution, contexts — all shipped

### R3: Proactive Assistant — NEARLY COMPLETE
- All Must Have: DONE
- Should Have open: 4 items (BACKLOG-087 starter templates, BACKLOG-082 session summary, DOC-006/007 API docs)
- Nice to Have open: 4 items (namespace mgmt UI, prefetch config UI, progress dashboard, memory diff view)
- Core AI context, memory layer, unstuck button, cross-memory search — all shipped

### R4: Full Suite — NOT STARTED
- Must Have: 2 heavyweight items (ROADMAP-007 AI Weekly Review, ROADMAP-002 AI Features Integration)
- Should Have: 3 items (workload indicator, blocked/waiting status, project standards)
- Nice to Have: 8 items (sub-projects, dependencies, templates, time tracking, etc.)
- Estimated: 8-12 weeks part-time for full R4

---

## 2. Current Codebase Health

| Metric | Status | Notes |
|--------|--------|-------|
| Frontend build | CLEAN | 576KB bundle (minor size warning), 0 TS errors |
| Backend syntax | CLEAN | No Python errors |
| Test suite | 18/18 PASSING | As of Batch 4 (requires venv activation) |
| Tech debt (high) | ALL CLEARED | 0 high-priority items remaining |
| Tech debt (medium) | 13 open | Non-blocking, mostly polish |
| Tech debt (low) | 20+ open | Address-when-touched items |
| Uncommitted work | 15 files | Batch 6 complete, needs commit |
| TODOs in code | 2 total | Both tracked in backlog |
| Lessons captured | 25+ patterns | 8 major documented, all codified |

---

## 3. What "Alpha" Means in Our Context

An **alpha** release is for early adopters / internal testers. It is:
- Feature-complete for the advertised scope
- Not necessarily polished (UX rough edges OK)
- Not packaged for end-user distribution (no installer, no code signing)
- Runnable by a technical user (developer, power user comfortable with CLI)

An alpha does NOT require:
- Distribution checklist (Phases 0-5) — that's for beta/GA
- Code signing, installer, Gumroad
- EULA, privacy policy, trademark cleanup
- Product branding/naming

An alpha DOES require:
- Core features working correctly
- No data-loss bugs
- Tests passing
- Documented setup process
- No exposed secrets in the repo

---

## 4. True Alpha Blockers Assessment

### BLOCKERS (Must fix before tagging alpha)

| # | Item | Effort | Why Blocking |
|---|------|--------|--------------|
| 1 | **Commit Batch 6 work** | 5 min | 15 files uncommitted — tag needs clean commit |
| 2 | **Security: Remove API key file** | 15 min | `backend/Anthropic API Key.txt` must not ship |
| 3 | **Security: Hardcoded paths** | 30 min | `SECOND_BRAIN_ROOT=G:/My Drive/...` is user-specific |
| 4 | **Create .env.example** | 20 min | Alpha testers need to know what env vars to set |
| 5 | **STRAT-008: Version tagging** | 10 min | Set version to 1.0.0-alpha in code + git tag |

**Total blocker effort: ~1.5 hours**

### NON-BLOCKERS (Nice for alpha but deferrable)

| Item | Why Not Blocking |
|------|-----------------|
| R3 Should Have items (templates, session summary) | Alpha scope is R1+R2+R3 core; polish is post-alpha |
| R4 Must Have items (AI weekly review, AI integration) | Separate release milestone |
| Distribution checklist (Phases 0-5) | Alpha is pre-distribution |
| DEBT-063 (Vite proxy in production) | Dev-mode only issue |
| Medium/low tech debt items | Non-functional, won't affect testers |
| Documentation (DOC-005, 006, 007) | Alpha testers can ask questions |

---

## 5. The R4 Question: Wait or Ship?

### What R4 adds beyond R3:
1. **ROADMAP-007: GTD Weekly Review with AI Advisors** — Multi-turn AI dialogue during weekly review. HIGH complexity (conversation state, context management, structured AI outputs).
2. **ROADMAP-002: AI Features Integration** — AI-powered analysis, suggestions, prioritization across all modules. HIGH complexity (cross-module intelligence, UI integration).
3. 3 Should Have quality items (moderate complexity)

### Analysis:

| Factor | Wait for R4 | Ship Alpha Now |
|--------|-------------|----------------|
| Time to alpha | +8-12 weeks | ~1.5 hours |
| Feature completeness | R1+R2+R3+R4 (everything) | R1+R2+R3 (core + AI foundation) |
| Risk | Scope creep, feature fatigue, no feedback | Missing AI dialogue features |
| Feedback loop | None until full build | Immediate from early users |
| Value proposition | "Full suite" with AI weekly review | Already strong: GTD + memory + AI context |
| R4 Must Haves difficulty | HIGH — novel AI dialogue system | N/A |

### Verdict: **Ship alpha now. Do NOT wait for R4.**

**Rationale:**
1. R4's Must Haves (ROADMAP-002, 007) are the two most complex items in the entire backlog — multi-turn AI dialogue systems with cross-module state. These are high-uncertainty, high-effort features.
2. R1+R2+R3 already delivers a compelling product: full GTD workflow, Second Brain sync, AI context export, memory layer, unstuck task intelligence, momentum scoring.
3. Alpha feedback on R1-R3 will directly inform how to build R4's AI features. Building R4 in a vacuum risks building the wrong thing.
4. The alpha blockers are trivial (~1.5 hours). Waiting 8-12 weeks for R4 when the product is shippable today is a classic "one more feature" trap.

---

## 6. Recommended Alpha Task List (Priority Order)

### Tier 1: BLOCKERS (~1.5 hours)
1. **Commit Batch 6** — git add + commit the 15 modified files
2. **Remove `backend/Anthropic API Key.txt`** — delete from working tree + .gitignore
3. **Remove hardcoded SECOND_BRAIN_ROOT** — grep and clean any committed references
4. **Create `backend/.env.example`** — document all required/optional env vars
5. **Tag v1.0.0-alpha** — set version in package.json + pyproject.toml + git tag

### Tier 2: SHOULD DO BEFORE ALPHA (~2-3 hours)
6. **README.md for alpha testers** — setup instructions (venv, npm, env vars, run commands)
7. **DEBT-078: Document test venv requirement** — so CI/testers can run tests
8. **Verify JWT secret handling** — ensure it doesn't ship with a weak default
9. **Quick security grep** — scan for any other hardcoded secrets/paths

### Tier 3: NICE TO HAVE POST-ALPHA
10. R3 Should Have items (BACKLOG-087, 082)
11. Medium tech debt items
12. Documentation (DOC-005, 006, 007)
13. Begin R4 planning (ROADMAP-002, 007 design docs)

---

## 7. Strategic Recommendation

**Ship v1.0.0-alpha today with R1+R2+R3 scope.**

Then plan two follow-up milestones:
- **v1.0.0-beta**: R3 polish (Should Have items) + distribution prep (Phase 0-1 of checklist) + R4 design docs
- **v1.0.0-rc / v1.0.0**: R4 features + full distribution (Phases 2-5) + beta feedback incorporated

This gives us:
- Immediate feedback on the 80% of value that's already built
- Time-boxed R4 development informed by real usage
- Progressive quality gates (alpha → beta → release)
