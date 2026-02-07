# R1 User Testing - Feedback Tracking

**Release:** R1 (PT Basic)
**Testing Period:** February 2026
**Status:** Active

---

## Feedback Prioritization Criteria

### Priority Levels

| Priority | Criteria | Response Time |
|----------|----------|---------------|
| **P0 - Critical** | App crashes, data loss, security vulnerability | Immediate |
| **P1 - High** | Feature completely broken, blocks testing | 24-48 hours |
| **P2 - Medium** | Feature partially broken, workaround exists | This testing cycle |
| **P3 - Low** | Minor issues, cosmetic, enhancement ideas | Backlog for R2+ |

### Categorization

- **BUG**: Something doesn't work as documented
- **UX**: Confusing interface, unclear workflow
- **PERF**: Slow performance, lag, timeouts
- **FEATURE**: Missing capability (may be intentional for R1)
- **DOC**: Documentation unclear or missing

---

## Bug Report Template

```markdown
### [BUG-XXX] Brief Title

**Reporter:** [Name]
**Date:** YYYY-MM-DD
**Priority:** P0/P1/P2/P3
**Category:** BUG/UX/PERF/FEATURE/DOC

**Environment:**
- OS:
- Browser:
- Auth enabled: Yes/No
- Second Brain configured: Yes/No

**Steps to Reproduce:**
1.
2.
3.

**Expected Behavior:**

**Actual Behavior:**

**Screenshots/Logs:**

**Workaround (if any):**

---
**Status:** Open | In Progress | Fixed | Won't Fix | Deferred
**Resolution:**
**Fixed in:**
```

---

## Reported Issues

### Critical (P0)
*None reported*

### High (P1)
*None reported*

### Medium (P2)
*None reported*

### Low (P3)
*None reported*

---

## Feature Requests

| ID | Request | Requester | Priority | Notes |
|----|---------|-----------|----------|-------|
| | | | | |

---

## UX Feedback

| Area | Feedback | Requester | Action |
|------|----------|-----------|--------|
| | | | |

---

## Testing Coverage

### Testers
| Name | Start Date | Environment | Focus Area |
|------|------------|-------------|------------|
| | | | |

### Test Areas Completed
- [ ] Project CRUD (create, read, update, delete)
- [ ] Task CRUD
- [ ] Task completion workflow
- [ ] Dashboard viewing
- [ ] Momentum score display
- [ ] Stalled projects widget
- [ ] Areas management
- [ ] Goals management
- [ ] Visions management
- [ ] Second Brain sync (if configured)
- [ ] Google OAuth login (if configured)
- [ ] Data export (JSON)
- [ ] Data export (SQLite backup)
- [ ] Navigation between views
- [ ] Error handling (invalid inputs)
- [ ] Browser refresh / state persistence

---

## Weekly Summary Template

```markdown
## Week of YYYY-MM-DD

### Testers Active: X

### Issues Reported
- P0: X
- P1: X
- P2: X
- P3: X

### Issues Resolved
- [List resolved issues]

### Key Findings
- [Summary of important feedback]

### Blockers
- [Any issues blocking further testing]

### Next Actions
- [ ] Action item 1
- [ ] Action item 2
```

---

## Session Notes

### Session: YYYY-MM-DD
**Tester:**
**Duration:**
**Focus:**

**Observations:**

**Issues Found:**

**Suggestions:**

---

## Metrics

### Issue Velocity
| Week | Reported | Resolved | Net Open |
|------|----------|----------|----------|
| | | | |

### Coverage by Feature
| Feature | Tested | Issues Found | Status |
|---------|--------|--------------|--------|
| Project CRUD | | | |
| Task CRUD | | | |
| Dashboard | | | |
| Momentum | | | |
| Auth | | | |
| Export | | | |
| Sync | | | |

---

## Escalation Path

1. **P3 issues**: Track in this document, address in backlog
2. **P2 issues**: Assign to developer, fix in current cycle
3. **P1 issues**: Immediate developer attention
4. **P0 issues**: Stop testing, notify all testers, emergency fix

---

*Last Updated: 2026-02-03*
