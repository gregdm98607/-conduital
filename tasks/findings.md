# Findings — R3 Must-Have + Tech Debt Batch (2026-02-06)

## Previous Session Patterns (retained)
- Models use SQLAlchemy 2.0 Mapped/mapped_column style
- TimestampMixin provides created_at/updated_at
- Services use static methods with db session parameter
- Routes use FastAPI APIRouter with Depends(get_db)
- Alembic migrations use batch mode for SQLite FK support
- Tailwind CSS with dark: prefix for dark mode
- lucide-react for icons, TanStack Query for data fetching
- Collapsible sections use localStorage for persistence

## AI Key Persistence Analysis

### Current State:
- API key loaded from `.env` via pydantic-settings `BaseSettings` (config.py:82)
- PUT /ai endpoint updates `settings.ANTHROPIC_API_KEY` at runtime only (settings.py:89)
- On server restart, runtime changes are lost → reverts to .env value
- No database storage for AI settings

### Approach: Write to .env file
- Simplest approach, consistent with existing pydantic-settings pattern
- Must handle .env file not existing (create it)
- Must handle updating existing key line vs adding new one
- Must NOT overwrite other .env settings
- .env is already in .gitignore (secure)

## Context Export Analysis

### Data Available for Export:
1. Active projects (name, status, momentum, outcome_statement, next actions)
2. Stalled projects (14+ days inactive)
3. Areas (name, health_score, standard_of_excellence)
4. Upcoming/overdue tasks
5. GTD horizons (goals, visions)
6. Recent activity log

### Format: Structured markdown
- Sections for projects, tasks, areas
- Include momentum scores for priority context
- Keep concise for AI context windows
- Support both full overview and per-project export

---

*Updated: 2026-02-06*
