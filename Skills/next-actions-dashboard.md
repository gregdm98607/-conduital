# Next Actions Dashboard Skill

**Name:** next-actions-dashboard

**Description:** Fetch prioritized next actions using the 5-tier priority system, filtered by current context and energy level. The core "what should I work on?" answer.

**Trigger phrases:** "What should I work on?", "Next actions", "What's next?", "Show me my tasks", "Dashboard"

---

## Instructions

When the user triggers this skill, fetch and present prioritized next actions:

### Step 1: Gather Filters (Optional)
If the user specified filters, use them:
- Context: @creative, @administrative, @home, @computer, @errands, @calls
- Energy level: high, medium, low
- Time available: 15min, 30min, 1hr, 2hr+

If not specified, ask briefly or use defaults:
- "What's your context right now? (@creative / @administrative / any)"
- Or proceed with no filters for full view

### Step 2: Fetch Prioritized Actions
Call the Conduital API:

```
GET /api/next-actions?context=[context]&energy=[level]&limit=10
```

The API returns tasks in the 5-tier priority order:
1. **Tier 0:** Unstuck tasks for stalled projects (HIGHEST)
2. **Tier 1:** Tasks due within 3 days
3. **Tier 2:** High momentum projects (score > 0.7)
4. **Tier 3:** Tasks already in progress
5. **Tier 4:** Medium momentum projects (score > 0.4)

### Step 3: Present the Dashboard

```
## Next Actions Dashboard

### 🔴 Urgent: Stalled Projects Need Attention
These projects haven't had activity in 14+ days. Small actions to get unstuck:
- [ ] [Task] → [Project] (stalled 18 days)
- [ ] [Task] → [Project] (stalled 14 days)

### 🟠 Due Soon
- [ ] [Task] → [Project] (due tomorrow)
- [ ] [Task] → [Project] (due in 2 days)

### 🟢 High Momentum - Keep Going
- [ ] [Task] → [Project] (momentum: 0.85)
- [ ] [Task] → [Project] (momentum: 0.72)

### 🔵 In Progress - Finish What You Started
- [ ] [Task] → [Project] (started 2 days ago)

### ⚪ Ready When You Are
- [ ] [Task] → [Project] (momentum: 0.55)
- [ ] [Task] → [Project] (momentum: 0.45)
```

### Step 4: Context-Specific View
If a context was specified, note it:
```
Showing: @creative tasks only
[Dashboard filtered to context]

Switch context? (@administrative / @home / all)
```

### Step 5: Quick Actions
Offer immediate actions:
- "Start [task name]?" - Marks task as in_progress
- "Complete [task name]?" - Marks task as done
- "Show me more about [project]?" - Deep dive into project

### Step 6: Summary Stats
At the bottom, show quick stats:
```
---
📊 Quick Stats
- Active projects: 12
- Stalled projects: 2
- Tasks due this week: 5
- Inbox items to process: 8
```

### Compact Mode
If user asks for "quick" or "brief":
```
## Top 5 Next Actions
1. [Task] → [Project] 🔴 stalled
2. [Task] → [Project] 🟠 due tomorrow
3. [Task] → [Project] 🟢 momentum 0.85
4. [Task] → [Project] 🔵 in progress
5. [Task] → [Project] ⚪ ready
```

### Important Notes
- Tier 0 (stalled projects) should always be visible - these need attention
- Momentum scores help the user understand why tasks are prioritized
- Keep it actionable - every item should be a clear next action
- If no tasks match filters, say so and suggest broadening
- Respect the GTD principle: next actions should be concrete, not vague
