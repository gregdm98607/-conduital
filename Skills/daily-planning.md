# Daily Planning Skill

**Name:** daily-planning

**Description:** Combined skill that loads Proactive-Assistance context, fetches Conduital next actions, and creates a focused daily plan. Integrates both systems for comprehensive planning.

**Trigger phrases:** "Plan my day", "Daily planning", "What's my day look like?", "Help me plan today"

---

## Instructions

When the user triggers this skill, orchestrate both systems for comprehensive daily planning:

### Step 1: Load Personal Context
From Proactive-Assistance (C:/Dev/Proactive-Assistance/):

```
Read: Memory/user_profile.json
Read: Memory/important_contexts.json
Read: Memory/current_projects.json
Read: Memory/memory_threads.json
```

Extract:
- Current life priorities and goals
- Any situational contexts (health, work situations, etc.)
- Active threads that need continuation
- Energy patterns and preferences

### Step 2: Fetch Conduital Data
From Conduital (C:/Dev/project-tracker/):

```
GET /api/next-actions?limit=15
GET /api/intelligence/stalled-projects
GET /api/inbox (count only)
```

Extract:
- Prioritized next actions (5-tier system)
- Any stalled projects needing attention
- Inbox items waiting to be processed

### Step 3: Synthesize Context

```
## Daily Planning - [Date]

### Your Context Today
**Energy:** [From user profile or ask]
**Available time:** [From calendar context or ask]
**Current focus:** [From important_contexts]
**Active threads:** [From memory_threads]
```

### Step 4: Present Integrated View

```
### Today's Landscape

**From Your Memory:**
- [Relevant context from Proactive-Assistance]
- [Any active threads to continue]
- [Goals this connects to]

**From Conduital:**
- 🔴 [X] stalled projects need attention
- 📥 [X] inbox items to process
- ✅ [X] tasks ready for today

**Alignment Check:**
Your stated priority: [from user_profile]
Today's top task: [from next-actions]
Alignment: [Good / Consider adjusting]
```

### Step 5: Build the Daily Plan

```
### Suggested Daily Plan

**Morning Block (High Energy)**
1. [ ] [Highest priority task] - [Project] (Tier 0/1)
2. [ ] [Second priority] - [Project]
3. [ ] [Creative work if @creative context]

**Midday Block**
4. [ ] Process inbox ([X] items, ~15 min)
5. [ ] [Administrative tasks if any]

**Afternoon Block**
6. [ ] [In-progress task to continue]
7. [ ] [Maintenance/review tasks]

**If Time Permits**
- Touch [stalled project] - small unstuck task
- [Lower priority items]

**Carry to Tomorrow If Needed**
- [Items that can wait]
```

### Step 6: Thread Continuation
If there are active memory threads:

```
### Threads to Continue

**[Thread Name]** (from [X] days ago)
- Last context: [summary]
- Suggested action: [what to do next]
- Related project: [if any]
```

### Step 7: Time Blocking (Optional)
If user wants specific times:

```
### Time Blocked Schedule

09:00 - 10:30  [Task 1] - Deep work block
10:30 - 10:45  Break
10:45 - 11:30  [Task 2]
11:30 - 12:00  Inbox processing
12:00 - 13:00  Lunch
13:00 - 14:30  [Task 3]
14:30 - 15:00  [Administrative]
15:00 - 15:30  Quick wins / Unstuck tasks
15:30 - 16:00  Wrap-up prep
```

### Step 8: Confirm and Commit

```
### Ready to Start?

Today's focus: [One sentence summary]
Top 3 must-dos:
1. [Task]
2. [Task]
3. [Task]

Adjustments needed? Or shall we begin?
```

### Step 9: Log the Plan
Save the daily plan for wrap-up reference:
- Store in Proactive-Assistance/Continuity/daily_plans/[date].md
- Reference during wrap-up to assess completion

### Dynamic Adjustments
If user says "I only have 2 hours" or "Low energy today":

```
### Adjusted Plan (2 hours, low energy)

Focus on:
1. [ ] [Easiest high-value task]
2. [ ] [Quick wins only]
3. [ ] [Skip deep work, do maintenance]

Defer to tomorrow:
- [Complex tasks]
- [High-energy items]
```

### Important Notes
- This skill bridges both systems - personal context AND task management
- Respect energy levels - don't push high-complexity on low-energy days
- The plan is a suggestion, not a mandate
- Leave buffer time - plans never go exactly as expected
- Connect tasks to larger goals for motivation
- End with clear "start here" guidance
