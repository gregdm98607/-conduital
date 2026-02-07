# Claude Code Prompts for Project Tracker

A collection of reusable prompts for working with Claude Code on this project. These prompts are designed to leverage Claude's capabilities for software development, project management, and productivity system design.

---

## Backlog & Task Management

### Review Conversation and Extract Features
```
Review this conversation with the principal user representative. Then brainstorm any relevant feature, backlog, or roadmap elements that enhance the application's current state. Show your decision about that, as well as add to backlog.md.
```

### Add Backlog Item (Not for Immediate Work)
```
Add a BACKLOG item, not to be worked on now: [DESCRIPTION]. Capture your initial thoughts in the backlog item.
```

### Add Bug Report with Initial Thoughts
```
Add a BUG: [DESCRIPTION]. Include your initial thoughts.
```

### Pick and Fix a Backlog Item
```
Review backlog.md for an item of priority or preference and fix it.
```

### Update Existing Backlog Item
```
Update BACKLOG-XXX such that [NEW REQUIREMENT OR CLARIFICATION].
```

---

## Code Investigation & Debugging

### Investigate a Bug
```
Investigate BUG-XXX. Check the relevant frontend and backend code, identify the root cause, and propose a fix.
```

### Compare Create vs Edit Behavior
```
Compare how [ENTITY] is created vs edited. Check if there are differences in data serialization, validation, or API handling that could cause [ISSUE].
```

### Trace Data Flow
```
Trace the data flow for [FEATURE] from frontend form submission through API to database. Identify any transformation or validation issues.
```

### Find All Usages
```
Find all places where [FUNCTION/COMPONENT/PATTERN] is used and ensure they handle [SPECIFIC CASE] correctly.
```

---

## Feature Implementation

### Implement with Plan Mode
```
Implement BACKLOG-XXX. Enter plan mode first to design the approach, then implement after approval.
```

### Add UI Element with Consistency
```
Add [UI ELEMENT] to [PAGE/COMPONENT]. Follow existing patterns in the codebase for styling and behavior.
```

### Add API Endpoint
```
Add a new API endpoint for [FUNCTIONALITY]. Include the route, schema, service layer logic, and update API documentation.
```

### Add Database Field
```
Add a new field [FIELD_NAME] to [MODEL]. Include: model update, schema update, migration, frontend type update, and UI to display/edit.
```

---

## Productivity System Design (GTD/MYN)

### Map Concepts Between Systems
```
Can you map [SYSTEM A] concepts to [SYSTEM B]? Then suggest how the two could be used in collaboration in an optimal productivity workflow architecture.
```

### Design Workflow Integration
```
Design how [PRODUCTIVITY CONCEPT] should integrate with the existing GTD-based architecture. Consider: data model changes, UI changes, and workflow impact.
```

### Visualize Architecture
```
Sketch a strawman visual diagram for [CONCEPT/ARCHITECTURE].
```

---

## Code Quality & Refactoring

### Review for Patterns
```
Review [FILE/COMPONENT] for consistency with existing patterns. Suggest improvements without over-engineering.
```

### Extract Reusable Component
```
The pattern in [LOCATION] is repeated in [OTHER LOCATIONS]. Extract it into a reusable [COMPONENT/UTILITY/HOOK].
```

### Add Type Safety
```
Review [FILE] for type safety gaps. Add proper TypeScript types where missing.
```

---

## Documentation

### Document Implementation
```
Document what was just implemented in [LOCATION]. Include: what it does, how to use it, and any important notes.
```

### Update Backlog with Completion Details
```
Mark [ITEM-ID] as completed in backlog.md. Add detailed completion notes to the Completed Items section.
```

### Create User Guide
```
Create a user-facing guide for [FEATURE]. Explain how to use it, not how it's implemented.
```

---

## Testing & Validation

### Test Edge Cases
```
What edge cases should be tested for [FEATURE]? List them and check if the current implementation handles them.
```

### Validate Against Requirements
```
Review [IMPLEMENTATION] against the original requirements in [BACKLOG-XXX]. Are there any gaps?
```

---

## Quick Operations

### Simple Fix
```
Fix [SPECIFIC ISSUE] in [FILE].
```

### Add to Existing
```
Add [ELEMENT] to [EXISTING STRUCTURE] following the same pattern.
```

### Remove/Clean Up
```
Remove [UNUSED CODE/FEATURE] and clean up any references.
```

---

## Project-Specific Prompts

### MYN Zone Classification
```
How should [TASK/FEATURE] be classified in the MYN urgency zones (Critical Now, Opportunity Now, Over the Horizon)?
```

### GTD Horizon Alignment
```
What GTD Horizon of Focus does [FEATURE/CONCEPT] belong to? How should it be modeled in the database?
```

### Momentum Impact
```
How does [CHANGE] affect momentum calculation? Should momentum scoring be updated?
```

---

## Tips for Effective Prompts

1. **Be Specific**: Include item IDs (BACKLOG-XXX, BUG-XXX) when referencing tracked items
2. **Provide Context**: Reference the conversation or previous decisions when relevant
3. **Request Reasoning**: Ask Claude to "include initial thoughts" to capture diagnostic thinking
4. **Scope Appropriately**: Use "not to be worked on now" for items that should just be tracked
5. **Chain Prompts**: Start with investigation, then move to implementation
6. **Request Updates**: Always ask to update backlog.md when completing tracked work

---

## Prompt Patterns

### Investigation Pattern
1. "Investigate [ISSUE]"
2. "What are the possible causes?"
3. "Propose a fix"
4. "Implement the fix"
5. "Update backlog.md"

### Feature Pattern
1. "Add BACKLOG item for [FEATURE] with initial thoughts"
2. "Review backlog and pick [ITEM] to implement"
3. "Enter plan mode and design approach"
4. "Implement after approval"
5. "Mark completed with details"

### Bug Fix Pattern
1. "Add BUG for [ISSUE] with initial thoughts"
2. "Investigate BUG-XXX"
3. "Fix the issue"
4. "Test the fix"
5. "Update backlog.md with completion"

---

*Last updated: 2026-01-25*
