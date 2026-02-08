# Conduital — Claude Code Instructions

This file provides context and instructions for Claude Code when working on this project.

## Project Overview

**Conduital** is an intelligent momentum-based productivity system with markdown file sync. Built with FastAPI (backend) and React + TypeScript (frontend).

### Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite, Alembic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, TanStack Query
- **AI Integration**: Anthropic Claude API

### Key Files
- `backlog.md` - Release-based backlog and task tracking
- `backend/app/main.py` - FastAPI entry point
- `frontend/src/main.tsx` - React entry point
- `backend/MODULE_SYSTEM.md` - Module architecture documentation

---

## Workflow Orchestration

### 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions)
- Use `/planning-with-files` skill for complex tasks
- If something goes sideways, STOP and re-plan immediately - don't keep pushing
- Use plan mode for verification steps, not just building
- Write detailed specs upfront to reduce ambiguity

### 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis to subagents
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

### 3. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules for yourself that prevent the same mistake
- Ruthlessly iterate on these lessons until mistake rate drops
- Review lessons at session start for relevant project

### 4. Verification Before Done
- Never mark a task complete without proving it works
- Diff your behavior between main and your changes when relevant
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

### 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution"
- Skip this for simple, obvious fixes - don't over-engineer
- Challenge your own work before presenting it

### 6. Autonomous Bug Fixing
- When given a bug report: just fix it. Don't ask for hand-holding
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

### 7. Task Management
1. **Plan First**: Use `/planning-with-files` methodology
2. **Verify Plan**: Check in before starting implementation
3. **Track Progress**: Mark items complete as you go
4. **Explain Changes**: High-level summary at each step
5. **Document Results**: Add review section to `tasks/todo.md`
6. **Capture Lessons**: Update `tasks/lessons.md` after corrections

---

## Core Principles

- **Simplicity First**: Make every change as simple as possible. Impact minimal code.
- **No Laziness**: Find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact**: Changes should only touch what's necessary. Avoid introducing bugs.

---

## Project-Specific Context

### GTD/MYN Concepts
- **Momentum Score**: 0.0-1.0 calculated from activity, completion rate, next actions
- **Stalled Projects**: 14+ days without activity
- **MYN Urgency Zones**: Critical Now, Opportunity Now, Over the Horizon
- **GTD Horizons**: Runway (tasks) through Purpose (vision)

### Module System
The codebase uses a modular architecture with commercial presets:
- `basic` - Core project/task management
- `gtd` - Full GTD workflow with inbox
- `proactive_assistant` - AI-augmented features
- `full` - All modules enabled

### File Sync
Bidirectional sync with PARA-organized Second Brain folders using YAML frontmatter in markdown files.

---

## Related Documentation

- `CLAUDE_CODE_PROMPTS.md` - Reusable prompt templates
- `Project_Tracker_Technical_Spec.md` - Full technical specification
- `backend/README.md` - Backend development guide
- `frontend/FRONTEND_IMPLEMENTATION_GUIDE.md` - Frontend patterns

---

*This file is automatically read by Claude Code at session start.*
