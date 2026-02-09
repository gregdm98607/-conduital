# Task Plan: v1.0.0-beta Preparation

**Status:** ready
**Date:** 2026-02-08
**Goal:** Track remaining work for the incremental beta release over v1.0.0-alpha.

---

## Current State

- **v1.0.0-alpha**: Shipped and distributed (2026-02-08)
- **Commit**: `4a69e62` — all alpha + post-release work committed
- **Tests**: 174/174 passing (100%)
- **Root directory**: Cleaned — historical docs archived to `archive/`
- **Tracking**: backlog.md, CHANGELOG.md, progress.md all current

---

## Beta Release Priorities

### Distribution (from distribution-checklist.md)

| Phase | Item | Status |
|-------|------|--------|
| 4.3 | Privacy Policy draft | Not started |
| 5.1 | App icon (.ico, multiple sizes) | Not started |
| 5.1 | Screenshots (5-8 polished) | Not started |
| 5.1 | Product description | Not started |
| 5.2 | Pricing research & decision | Not started |
| 5.3 | Gumroad listing setup | Not started |
| 5.4 | Support infrastructure (FAQ, email) | Not started |
| 5.5 | Update mechanism | Not started |

### Testing

| Item | Status |
|------|--------|
| BACKLOG-118: Clean Windows 10 VM testing | Not started |
| BACKLOG-118: Clean Windows 11 VM testing | Not started |
| BACKLOG-117: Upgrade-in-place testing | Not started |

### Tech Debt (from backlog.md)

| ID | Description | Priority |
|----|-------------|----------|
| DEBT-007 | Soft delete for entities | Medium |
| DEBT-080 | Installer version not SSoT | Medium |
| DEBT-083 | Installer kills without graceful shutdown attempt | Medium |
| BACKLOG-116 | Version single source of truth | Medium |

### Code Quality & Polish

| ID | Description | Priority |
|----|-------------|----------|
| DEBT-013 | Mobile views not optimized | Low |
| DEBT-016 | WebSocket updates not integrated | Low |
| DEBT-039 | MemoryPage priority input out-of-range | Low |
| DEBT-061 | Dynamic attribute assignment fragility | Low |

---

## What's NOT in Beta Scope

- License key system (Phase 4.1) — shipping free, deferred to paid transition
- Code signing (Phase 3.1) — deferred, saves $200-500/year
- Multi-user/teams
- R2 features (GTD inbox enhancements)
