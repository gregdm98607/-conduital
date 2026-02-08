# Context Switch Skill

**Name:** context-switch

**Description:** When switching between work modes (@creative vs @administrative vs @home etc.), load relevant context from both systems and surface appropriate tasks. Reduces friction of mental context switching.

**Trigger phrases:** "Switch to @creative", "Going into admin mode", "Context: @home", "Switching contexts", "I'm now @[context]"

---

## Instructions

When the user triggers a context switch, facilitate a smooth transition:

### Step 1: Identify Target Context
Parse the target context from user input:

**Supported Contexts:**
- `@creative` - Writing, design, ideation, art
- `@administrative` - Email, paperwork, scheduling, finances
- `@computer` - General computer work, coding, research
- `@home` - Household tasks, errands, personal
- `@calls` - Phone calls, video meetings
- `@errands` - Out-of-house tasks
- `@deep-work` - Focused, uninterrupted work
- `@low-energy` - Tasks for tired/unfocused times

### Step 2: Acknowledge the Switch

```
## Context Switch: @[previous] → @[new]

Switching from [previous context] to [new context]...
```

### Step 3: Close Out Previous Context (Optional)
If coming from another active context:

```
### Closing @[previous]

**In progress when you left:**
- [Task] - [Project] (save state: [where you were])

**Quick capture before switching:**
Any thoughts to capture from @[previous] work? (or "none")
```

### Step 4: Load New Context - Proactive-Assistance
From Memory files, load context-relevant information:

**For @creative:**
- Active creative projects and their rules
- Writing threads and continuity
- Inspiration notes or references

**For @administrative:**
- Pending administrative items
- Deadlines and appointments
- Financial/paperwork contexts

**For @home:**
- Household projects
- Family-related threads
- Personal goals

### Step 5: Load New Context - Conduital
Fetch context-filtered tasks:

```
GET /api/next-actions?context=@[new_context]&limit=10
```

### Step 6: Present Context Dashboard

```
## @creative Mode Active

### Your Creative Context
**Active projects:** The Lund Covenant, Album Art Design
**Current thread:** Chapter 5 - Gill's confrontation scene
**Constraints loaded:** No em-dashes, no "sharp", etc.

### @creative Tasks Available

**Priority:**
1. [ ] Continue Chapter 5 scene - Lund Covenant
2. [ ] Review album cover draft - Album Art

**Also available:**
3. [ ] Brainstorm blog post topics - Content Calendar
4. [ ] Sketch character design - Side Project

### Energy Check
You're in creative mode. Current energy level?
- High → Tackle Chapter 5 (deep creative work)
- Medium → Album cover review (guided creative)
- Low → Brainstorming (generative, low pressure)
```

### Step 7: Environment Suggestions
Suggest environmental optimizations:

```
### Optimize Your Environment

**For @creative:**
- 🎵 Consider focus music or silence
- 📱 Notifications off recommended
- ⏱️ Suggested block: 90 minutes minimum
- 📝 Have notes visible for continuity

**For @administrative:**
- 📧 Email client ready
- 📋 Task list visible
- ⏱️ Batch in 30-45 min blocks
- ✅ Aim for completion over perfection
```

### Step 8: Quick Start
Provide a clear starting point:

```
### Quick Start

**Recommended first action:**
> [Specific task with clear first step]

**Why this one:**
[Brief reasoning - highest priority / continues thread / quick win]

Ready to begin? Or show me more options?
```

### Step 9: Set Context Timer (Optional)
If user wants time-boxing:

```
### Context Timer

How long in @[context]?
- [ ] 30 minutes
- [ ] 1 hour
- [ ] 2 hours
- [ ] Until done

I'll remind you when time is up and prompt for wrap-up or extension.
```

### Context Combinations
Handle combined contexts:

```
User: "Switch to @creative @low-energy"

## @creative + @low-energy Mode

Showing creative tasks suitable for low energy:
1. [ ] Brainstorm session (generative, no pressure)
2. [ ] Review and light edit (not heavy writing)
3. [ ] Organize reference materials
4. [ ] Mind-map plot ideas

Avoiding (save for high energy):
- Chapter drafting
- Complex scene work
- Detailed editing
```

### Exit Context
When user says "done with @creative" or switches again:

```
### Exiting @creative

**Session summary:**
- Time in context: 1h 45m
- Tasks completed: 2
- Tasks started: 1

**Capture before exit:**
- Any notes to save?
- Thread state to remember?
- Ideas that came up?

Switching to: [next context or general]
```

### Important Notes
- Context switching has cognitive cost - minimize unnecessary switches
- Loading the right context reduces "where was I?" friction
- Creative contexts especially benefit from continuity loading
- Keep context switches intentional, not reactive
- Honor energy levels - wrong context + wrong energy = poor output
