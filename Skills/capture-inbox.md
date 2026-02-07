# Capture Inbox Skill

**Name:** capture-inbox

**Description:** Quick capture to GTD inbox with minimal friction. Just the thought, optional project association. Follows GTD "capture everything" principle.

**Trigger phrases:** "Capture", "Quick add", "Add to inbox", "Remember to", "Don't let me forget"

---

## Instructions

When the user triggers this skill, provide frictionless capture:

### Step 1: Capture the Thought
If the user included the item in their trigger:
- "Capture: Call the dentist about that appointment"
- Extract: "Call the dentist about that appointment"

If not, prompt simply:
- "What do you want to capture?"

### Step 2: Quick Classification (Optional)
Only if obvious or user provides it:
- **Project association:** If they mention a project name, link it
- **Context hint:** If they mention @home, @computer, etc., note it
- **Energy level:** If they say "when I have energy" or "quick task", note it

Do NOT ask for these if not provided - the inbox is for raw capture.

### Step 3: Add to Inbox
Call the Project-Tracker API:

```
POST /api/inbox
{
  "content": "[The captured thought]",
  "source": "quick_capture",
  "captured_at": "[timestamp]",
  "hints": {
    "project": "[if mentioned]",
    "context": "[if mentioned]",
    "energy": "[if mentioned]"
  }
}
```

### Step 4: Confirm (Briefly)
Keep confirmation minimal:
- "✓ Captured: [item]"
- Or if project linked: "✓ Captured → [Project Name]"

### Step 5: Offer Continuity
- "Anything else to capture?"
- If they say no or nothing: end cleanly, no extra prompts

### Batch Capture Mode
If user says "I have a few things" or provides a list:
- Accept multiple items
- Capture each to inbox
- Confirm with count: "✓ 5 items captured"

### Example Interactions

**Minimal:**
```
User: Capture call mom about Sunday dinner
Assistant: ✓ Captured: Call mom about Sunday dinner
```

**With context:**
```
User: Quick add - review the PR for auth module, it's for Project Tracker
Assistant: ✓ Captured → Project Tracker: Review the PR for auth module
```

**Batch:**
```
User: Capture these: buy milk, schedule car service, reply to Jake's email
Assistant: ✓ 3 items captured to inbox
```

### Important Notes
- Speed over completeness - capture now, process later (GTD principle)
- Never ask clarifying questions during capture
- Processing/clarification happens during dedicated processing time
- The inbox is a trusted place - everything goes in, nothing is lost
- If the API is unavailable, store locally and note for later sync
