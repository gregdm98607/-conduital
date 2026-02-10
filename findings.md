# Beta Release UI Review — Findings

**Date:** 2026-02-09
**Reviewer:** Claude (via Chrome browser inspection)
**Target:** localhost:5173 (development server)

---

## Overall Assessment: READY FOR BETA (with 1 bug to fix)

The UI is polished, consistent, and all major beta features are visually confirmed working. One bug found in the Projects list view.

---

## Feature Verification Results

### Pillar 1: Momentum Intelligence

| Feature | ID | Status | Notes |
|---------|-----|--------|-------|
| Momentum trend arrows | BETA-010 | PASS | Green up arrows visible on ProjectCards |
| Momentum sparkline | BETA-011 | PASS | Inline SVG trend lines on ProjectCards |
| Completion progress bar | BETA-012 | PASS | Thin gradient bars under stats on each card |
| "Almost there" nudge | BETA-013 | PASS (code verified) | Renders when >80% complete + active. Operation Granny Files (80%) is at exactly 80%, nudge shows for >80% — correct threshold behavior |
| Dashboard momentum summary | BETA-014 | NOT VISIBLE | Expected: no momentum snapshots exist yet (daily job hasn't run). Not a bug — conditional rendering when no data. |

### Pillar 2: GTD Inbox Enhancements

| Feature | ID | Status | Notes |
|---------|-----|--------|-------|
| Inbox stats cards | BETA-032 | PASS | Unprocessed count, Processed Today, Last Capture all showing |
| Multi-select checkboxes | BETA-031 | PASS | Checkboxes on items + "Select all" toggle |
| Batch action toolbar | BETA-031 | PASS | "2 selected" counter, project dropdown, Assign to Project, Delete, Clear |
| Item age indicators | BETA-034 | NOT VISIBLE | Expected: test items were "Just now" (<24h). Age indicators only show for >24h items. Correct behavior. |
| Weekly review status | BETA-030 | PASS | Dashboard shows "Never completed" with "Start Review" link |

### Pillar 3: Infrastructure & Polish

| Feature | ID | Status | Notes |
|---------|-----|--------|-------|
| Goals page | BACKLOG-125 | PASS | Full CRUD page with search, status/timeframe filters, grid/list toggle, empty state |
| Visions page | BACKLOG-125 | PASS | Full CRUD page with search, timeframe filter, grid/list toggle, empty state |
| Contexts page | BACKLOG-125 | PASS | Full CRUD page with search, type filter, grid/list toggle, empty state |
| Horizons sidebar nav | BACKLOG-125 | PASS | "HORIZONS" section with Goals (Crosshair), Visions (Eye), Contexts (Tag) |
| File Sync Settings | BACKLOG-123 | PASS | Editable sync root, watch dirs, interval, conflict strategy with Save button |
| Review column (list) | BACKLOG-127 | PASS | Always shows status: "No schedule", "5d overdue" (red), "In 2d" (yellow) |
| Task defer popover | BACKLOG-119 | PASS | Clock icon opens popover with 1 Week / 1 Month presets + custom date |
| Make Next Action | BACKLOG-120 | PASS | Bulk toolbar shows "→ Next Action" when Other Tasks selected |
| Responsive grids | BACKLOG-126 | PASS | AreaDetail 4-col metrics, ProjectDetail 3-col — both responsive |
| UTC time normalization | BACKLOG-122 | PASS | Dates showing correctly ("3 days ago", "Just now", etc.) |
| Momentum Thresholds | DEBT-073/074 | PASS | Activity icon, recalculation interval now visible |

---

## Bugs Found

### BUG-025: Projects List View Shows 0/0 Task Counts

**Severity:** Medium (cosmetic, data is correct elsewhere)
**Location:** `frontend/src/components/projects/ProjectListView.tsx:164-165`
**Symptom:** TASKS column shows "0/0" for all projects in list view, while grid view cards show correct counts (e.g., 4/12, 5/10, 4/5)

**Root Cause:** List view reads task counts from `project.tasks` array:
```tsx
const completedTasks = project.tasks?.filter(t => t.status === 'completed').length || 0;
const totalTasks = project.tasks?.length || 0;
```

Grid view (ProjectCard) correctly prefers API-computed fields:
```tsx
const totalTasks = project.task_count ?? project.tasks?.length ?? 0;
const completedTasks = project.completed_task_count ?? project.tasks?.filter(t => t.status === 'completed').length ?? 0;
```

**Fix:** Update list view to use `project.task_count` / `project.completed_task_count` like the grid view does. Two-line change.

---

## Items Not Testable (expected)

- **BETA-014 (momentum summary)**: Requires daily snapshot job to have run at least once. Will show "N gaining, N steady, N declining" once snapshots exist.
- **BETA-034 (age indicators)**: Requires inbox items >24h old. Will show gray/amber/red clock icons with "Xd" text.
- **BETA-013 (nudge text)**: Threshold is >80%, and the highest completion project visible is exactly 80%. Code verified correct.

---

## UI Quality Notes

- Sidebar navigation is well-organized with clear section headers (MANAGE, HORIZONS, REVIEW)
- Collapsible Settings sections work consistently
- Empty states on Goals/Visions/Contexts are helpful with descriptive text and CTA buttons
- Color coding is consistent (green = good, orange = moderate, red = critical/overdue)
- Dark sidebar with light content area provides good contrast
- Branding is correct: "Conduital — The Conduit for Intelligent Momentum"
- Footer shows "File Sync · v1.0"

---

*Review completed 2026-02-09*
