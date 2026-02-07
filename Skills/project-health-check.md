# Project Health Check Skill

**Name:** project-health-check

**Description:** Review stalled projects, momentum scores, and generate unstuck tasks for projects needing attention. Strategic view of project portfolio health.

**Trigger phrases:** "Project health", "What's stalled?", "Health check", "Project review", "What needs attention?"

---

## Instructions

When the user triggers this skill, provide a comprehensive project health assessment:

### Step 1: Fetch Project Health Data
Call the Project-Tracker API:

```
GET /api/projects/health
GET /api/intelligence/stalled-projects
GET /api/intelligence/momentum-summary
```

### Step 2: Present Health Overview

```
## Project Health Check - [Date]

### Portfolio Summary
- Total active projects: [X]
- Healthy (momentum > 0.6): [X] ✅
- Needs attention (0.3-0.6): [X] ⚠️
- Stalled (< 0.3 or 14+ days inactive): [X] 🔴

### Health Distribution
🟢🟢🟢🟢🟢🟡🟡🟡🔴🔴 (visual bar)
```

### Step 3: Stalled Projects Deep Dive

```
### 🔴 Stalled Projects (Immediate Attention)

**[Project Name]** - Stalled 18 days
- Last activity: [date] - [what was done]
- Momentum score: 0.15
- Why stalled: [No clear next action / Blocked / Lost focus]
- **Unstuck suggestion:** [5-15 min task to restart momentum]

**[Project Name]** - Stalled 14 days
- Last activity: [date]
- Momentum score: 0.22
- **Unstuck suggestion:** [minimal viable action]
```

### Step 4: Warning Zone

```
### ⚠️ Warning Zone (Momentum Declining)

**[Project Name]** - Momentum: 0.45 (↓ from 0.62 last week)
- Days since activity: 8
- Risk: Will stall in ~6 days at current rate
- **Suggested action:** [task to maintain momentum]

**[Project Name]** - Momentum: 0.38 (↓ from 0.51)
- Risk: Approaching stall threshold
```

### Step 5: Healthy Projects (Brief)

```
### ✅ Healthy Projects
| Project | Momentum | Trend | Last Activity |
|---------|----------|-------|---------------|
| [Name]  | 0.85     | ↑     | Today         |
| [Name]  | 0.72     | →     | 2 days ago    |
| [Name]  | 0.68     | ↑     | Yesterday     |
```

### Step 6: Generate Unstuck Tasks
For each stalled project, offer to generate an unstuck task:

```
### Unstuck Task Generator

For **[Stalled Project]**, I suggest:
> "[5-15 minute task description]"
> Estimated time: 10 minutes
> Why this helps: [Gets you back in the codebase / Clears a blocker / Creates momentum]

Add this task? (yes/no)
```

If AI features are enabled, use the intelligence API:
```
POST /api/intelligence/generate-unstuck-task
{
  "project_id": [id],
  "max_duration_minutes": 15
}
```

### Step 7: Recommendations

```
### Recommended Actions

1. **Immediate:** Add unstuck task to [Project] - 10 min to restart
2. **This week:** Touch [Project] before it stalls (6 days remaining)
3. **Consider:** Archive or pause [Project] if no longer relevant?
```

### Step 8: Offer Next Steps
- "Want me to add unstuck tasks for all stalled projects?"
- "Should we look deeper at any specific project?"
- "Time to archive any of these?"

### Important Notes
- Stalled doesn't mean failed - it means needs a small push
- Unstuck tasks should be tiny (5-15 min) to reduce friction
- Declining momentum is a leading indicator - catch it early
- Some projects may need to be paused intentionally - that's okay
- The goal is awareness and intentional choices, not guilt
