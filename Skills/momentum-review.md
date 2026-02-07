# Momentum Review Skill

**Name:** momentum-review

**Description:** Analyze momentum across all active projects, highlight trends, understand what's driving or draining momentum, and suggest actions to maintain flow.

**Trigger phrases:** "Momentum check", "Momentum review", "How's my momentum?", "Flow check", "Project momentum"

---

## Instructions

When the user triggers this skill, provide momentum analysis:

### Step 1: Fetch Momentum Data
Call the Project-Tracker API:

```
GET /api/intelligence/momentum-summary
GET /api/projects?include_momentum=true
GET /api/activity-log?days=14
```

### Step 2: Overall Momentum Score

```
## Momentum Review - [Date]

### Overall Portfolio Momentum: [0.XX]

[Visual representation]
Low ░░░░░░░░░░ High
         ▲ 0.62

Trend: [↑ Improving / → Stable / ↓ Declining] from last week
```

### Step 3: Momentum Breakdown by Project

```
### Project Momentum Scores

| Project | Score | Trend | Factors |
|---------|-------|-------|---------|
| [Name]  | 0.85  | ↑↑    | Daily activity, tasks completing |
| [Name]  | 0.72  | ↑     | Good task flow |
| [Name]  | 0.58  | →     | Steady but could use attention |
| [Name]  | 0.35  | ↓     | 8 days since activity |
| [Name]  | 0.18  | ↓↓    | Stalled - 16 days inactive |
```

### Step 4: Momentum Factor Analysis
Explain what's driving the scores:

```
### What's Driving Momentum

**Momentum Formula:**
- 40% Recent activity (30-day decay)
- 30% Task completion rate (7-day window)
- 20% Clear next action available
- 10% Activity frequency (14-day window)

**Your Top Momentum Drivers:**
✅ [Project] - Completing tasks regularly (+0.15)
✅ [Project] - Daily touches keeping it warm (+0.12)
✅ Clear next actions on 8/12 projects (+0.08)

**Momentum Drains:**
❌ [Project] - No activity in 16 days (-0.18)
❌ [Project] - No clear next action defined (-0.10)
❌ 3 projects below 0.4 threshold (-0.08)
```

### Step 5: Activity Pattern Analysis

```
### Activity Patterns (Last 14 Days)

**Most Active Days:** Tuesday, Thursday
**Least Active:** Sunday (expected), Saturday
**Average tasks/day:** 2.3
**Peak productivity window:** 9-11 AM (based on completion times)

**Activity Heatmap:**
Mon: ████░░░ 4 tasks
Tue: ██████░ 6 tasks
Wed: ███░░░░ 3 tasks
Thu: █████░░ 5 tasks
Fri: ██░░░░░ 2 tasks
Sat: █░░░░░░ 1 task
Sun: ░░░░░░░ 0 tasks
```

### Step 6: Momentum Recommendations

```
### Recommendations to Boost Momentum

**Quick Wins (Today):**
1. Touch [Project] - hasn't been active in 8 days
2. Define next action for [Project] - currently has none
3. Complete one task on [Highest momentum project] - ride the wave

**This Week:**
1. Add unstuck tasks to stalled projects
2. Review if [Low momentum project] should be paused
3. Batch @administrative tasks on Thursday (your admin day)

**Strategic:**
1. Consider WIP limit - 12 active projects may be too many
2. [Project] has been low momentum for 3 weeks - decision needed
```

### Step 7: Momentum Goals

```
### Momentum Targets

Current: 0.62 | Target: 0.70 | Gap: 0.08

To reach target:
- Revive 1 stalled project (+0.03)
- Add next actions to 2 projects (+0.03)
- Complete 3 more tasks this week (+0.02)
```

### Step 8: Compare to Last Week

```
### Week-over-Week Comparison

| Metric | Last Week | This Week | Change |
|--------|-----------|-----------|--------|
| Avg momentum | 0.58 | 0.62 | +0.04 ↑ |
| Tasks completed | 14 | 18 | +4 ↑ |
| Stalled projects | 3 | 2 | -1 ↑ |
| New projects | 1 | 0 | -1 → |
```

### Important Notes
- Momentum is a tool for awareness, not judgment
- It's okay for some projects to have low momentum if intentionally paused
- High momentum ≠ high importance; low momentum ≠ unimportant
- The goal is sustainable progress, not maximizing a number
- Watch for burnout indicators: very high activity followed by crash
