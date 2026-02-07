# Database Models Summary

## Overview

Created 11 SQLAlchemy models implementing the complete database schema for the Project Tracker application. All models follow best practices with proper relationships, indexes, and type hints.

## Models Created

### 1. Base Models (`app/models/base.py`)

**Base**
- Declarative base for all models

**TimestampMixin**
- Provides `created_at` and `updated_at` timestamps
- Automatic timestamp management
- `to_dict()` method for serialization

---

### 2. Project Model (`app/models/project.py`)

The core model representing multi-step outcomes.

**Key Fields:**
- `title`, `description`, `status`
- `priority` (1-5), `momentum_score` (0.0-1.0)
- `last_activity_at`, `stalled_since`, `completed_at`
- `file_path`, `file_hash` (for Second Brain sync)

**Relationships:**
- Belongs to: `Area`, `Goal`, `Vision`
- Has many: `Task`, `ProjectPhase`

**Properties:**
- `is_stalled` - Check if project is stalled
- `days_since_activity` - Days since last update
- `completion_percentage` - % of completed tasks

**Status Values:**
- `active`, `someday_maybe`, `completed`, `archived`, `stalled`

---

### 3. Task Model (`app/models/task.py`)

Individual action items (GTD Next Actions).

**Key Fields:**
- `title`, `description`, `status`, `task_type`
- `due_date`, `defer_until`, `estimated_minutes`, `actual_minutes`
- `context`, `energy_level`, `location`
- `priority`, `is_next_action`, `is_two_minute_task`, `is_unstuck_task`
- `file_line_number`, `file_marker` (for sync)

**Relationships:**
- Belongs to: `Project`, `ProjectPhase`, `parent_task`
- Has many: `subtasks`

**Properties:**
- `is_overdue` - Check if past due date
- `is_due_soon` - Due within 3 days
- `duration_display` - Human-readable time estimate

**Status Values:**
- `pending`, `in_progress`, `waiting`, `completed`, `cancelled`

**Task Types:**
- `action`, `milestone`, `waiting_for`, `someday_maybe`

**Context Examples:**
- `creative`, `administrative`, `research`, `communication`, `deep_work`, `quick_win`

**Energy Levels:**
- `high`, `medium`, `low`

---

### 4. Area Model (`app/models/area.py`)

Areas of Responsibility (GTD / PARA).

**Key Fields:**
- `title`, `description`
- `folder_path` (link to Second Brain)
- `standard_of_excellence` (GTD: what does "good" look like?)
- `review_frequency` (daily, weekly, monthly)

**Relationships:**
- Has many: `Project`

**Properties:**
- `active_projects_count` - Count of active projects

---

### 5. Goal Model (`app/models/goal.py`)

1-3 year objectives (GTD Horizon 3).

**Key Fields:**
- `title`, `description`
- `timeframe` (1_year, 2_year, 3_year)
- `target_date`, `completed_at`
- `status`

**Relationships:**
- Has many: `Project`

---

### 6. Vision Model (`app/models/vision.py`)

3-5 year vision and life purpose (GTD Horizons 4-5).

**Key Fields:**
- `title`, `description`
- `timeframe` (3_year, 5_year, life_purpose)

**Relationships:**
- Has many: `Project`

---

### 7. ProjectPhase Model (`app/models/project_phase.py`)

Stages in multi-phase projects.

**Key Fields:**
- `phase_name`, `phase_order`, `description`
- `status` (pending, active, completed)
- `started_at`, `completed_at`

**Relationships:**
- Belongs to: `Project`
- Has many: `Task`

**Properties:**
- `is_active` - Currently active phase
- `is_completed` - Phase completed

**Example Phases:**
- Manuscript: Research → Outline → Draft → Revision → Editing → Submission
- Genealogy: Collection → Digitization → Analysis → Writing → Review

---

### 8. PhaseTemplate Model (`app/models/phase_template.py`)

Reusable phase definitions for common project types.

**Key Fields:**
- `name`, `description`
- `phases_json` (JSON array of phase definitions)

**Examples:**
```json
{
  "name": "Manuscript Development",
  "phases": [
    {"name": "Research", "order": 1},
    {"name": "Outline", "order": 2},
    {"name": "First Draft", "order": 3},
    {"name": "Revision", "order": 4},
    {"name": "Editing", "order": 5},
    {"name": "Submission", "order": 6}
  ]
}
```

---

### 9. Context Model (`app/models/context.py`)

GTD contexts for organizing next actions.

**Key Fields:**
- `name` (e.g., @home, @computer, @creative)
- `context_type` (location, energy, work_type, time, tool)
- `description`, `icon`

**Context Types:**
- **Location:** @home, @office, @errands
- **Tool:** @computer, @phone, @tablet
- **Energy:** @creative, @administrative, @deep_work
- **Time:** @quick_win (<15min), @focus_block (60+ min)

---

### 10. ActivityLog Model (`app/models/activity_log.py`)

Tracks all entity changes for momentum and audit trail.

**Key Fields:**
- `entity_type`, `entity_id` (what changed)
- `action_type` (created, updated, completed, status_changed, file_synced)
- `details` (JSON with specific changes)
- `timestamp`, `source` (user, file_sync, ai_assistant, system)

**Uses:**
- Momentum calculation
- Audit trail
- Analytics
- Future undo functionality

---

### 11. SyncState Model (`app/models/sync_state.py`)

Tracks file synchronization status.

**Key Fields:**
- `file_path`
- `last_synced_at`, `last_file_modified_at`
- `file_hash` (SHA-256 for change detection)
- `sync_status` (synced, pending, conflict, error)
- `error_message`
- `entity_type`, `entity_id` (mapping to Project/Area)

**Properties:**
- `has_conflict` - Sync conflict detected
- `has_error` - Sync error occurred

---

### 12. InboxItem Model (`app/models/inbox.py`)

GTD inbox for quick capture.

**Key Fields:**
- `content`
- `captured_at`, `processed_at`
- `source` (web_ui, api, voice, email, file)
- `result_type` (task, project, reference, trash)
- `result_id` (ID of created entity)

**Properties:**
- `is_processed` - Item has been processed
- `preview` - First 100 characters

---

## Indexes Created

For optimal query performance:

- `projects.status`
- `projects.momentum_score`
- `projects.area_id`
- `projects.last_activity_at`
- `tasks.status`
- `tasks.project_id`
- `tasks.is_next_action`
- `tasks.context`
- `tasks.due_date`
- `project_phases.project_id`
- `activity_log.entity_type`, `activity_log.entity_id`
- `activity_log.timestamp`
- `sync_state.sync_status`
- `inbox.processed_at`

---

## Database Constraints

### Unique Constraints
- `projects.file_path` - One project per file
- `areas.folder_path` - One area per folder
- `phase_templates.name` - Unique template names
- `contexts.name` - Unique context names
- `sync_state.file_path` - One sync record per file
- `project_phases.(project_id, phase_order)` - Unique phase order per project

### Check Constraints
- `tasks.status` - Must be valid status value
- `tasks.task_type` - Must be valid task type

### Cascade Rules
- Delete Project → Delete Tasks, Phases (CASCADE)
- Delete Task → Delete Subtasks (CASCADE)
- Delete Area → Set NULL on Projects (SET NULL)
- Delete Goal → Set NULL on Projects (SET NULL)

---

## Supporting Infrastructure

### Database Configuration (`app/core/database.py`)
- SQLAlchemy engine with SQLite
- Session management
- Connection pooling
- WAL mode for concurrency

### Settings (`app/core/config.py`)
- Pydantic settings from environment variables
- Database path configuration
- Second Brain integration settings
- AI configuration
- Momentum thresholds

### Utilities (`app/core/db_utils.py`)
- `log_activity()` - Log changes
- `update_project_activity()` - Update activity timestamp
- `get_or_create()` - Find or create pattern
- `count_by_status()` - Status aggregation
- `get_recent_activity()` - Fetch activity logs
- `ensure_unique_file_marker()` - Generate task markers
- `calculate_file_hash()` - File change detection

### Alembic Configuration
- `alembic.ini` - Migration settings
- `alembic/env.py` - Environment configuration
- `alembic/script.py.mako` - Migration template
- Auto-formatting with Black

---

## Migration Management

### Initial Setup
```bash
# Generate first migration
poetry run alembic revision --autogenerate -m "Initial schema"

# Apply migration
poetry run alembic upgrade head
```

### Future Changes
1. Modify models in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Apply: `alembic upgrade head`

### Best Practices
- Always review auto-generated migrations
- Test migrations on dev database first
- Include both upgrade and downgrade functions
- Document complex migrations
- Use meaningful migration messages

---

## Type Safety

All models use modern Python type hints:
- `Mapped[int]` - Required integer
- `Mapped[Optional[str]]` - Nullable string
- `Mapped[datetime]` - Timestamp
- `Mapped[list["Task"]]` - One-to-many relationship
- `TYPE_CHECKING` guards to prevent circular imports

---

## GTD Alignment

Models implement core GTD concepts:

**Capture:** `InboxItem` for quick capture
**Clarify:** Process inbox into `Task`, `Project`, or reference
**Organize:** `Context`, `Area`, `Goal`, `Vision` for categorization
**Reflect:** `ActivityLog` for review, `momentum_score` for health
**Engage:** `is_next_action` flag for immediate actions

**Horizons of Focus:**
- Runway (0): `Task` (Next Actions)
- Projects (1): `Project`
- Areas (2): `Area` (Responsibilities)
- Goals (3): `Goal` (1-3 years)
- Vision (4): `Vision` (3-5 years)
- Purpose (5): `Vision` with `life_purpose` timeframe

---

## File Structure

```
backend/app/models/
├── __init__.py           # Model exports
├── base.py              # Base class and TimestampMixin
├── project.py           # Project model
├── task.py              # Task model
├── area.py              # Area model
├── goal.py              # Goal model
├── vision.py            # Vision model
├── project_phase.py     # ProjectPhase model
├── phase_template.py    # PhaseTemplate model
├── context.py           # Context model
├── activity_log.py      # ActivityLog model
├── sync_state.py        # SyncState model
└── inbox.py             # InboxItem model
```

---

## Next Steps

1. ✅ Models created and validated
2. ✅ Database configuration complete
3. ✅ Migration setup complete
4. ⏳ Create Pydantic schemas for API validation
5. ⏳ Implement CRUD operations
6. ⏳ Build API endpoints
7. ⏳ Implement sync engine
8. ⏳ Add momentum calculation service
9. ⏳ Integrate Claude AI features

---

## Statistics

- **11 models** implementing complete database schema
- **12 tables** (11 models + junction tables if needed)
- **100+ fields** across all models
- **20+ relationships** (one-to-many, many-to-one)
- **15+ indexes** for query optimization
- **5+ properties** for computed values
- **Full type safety** with Python type hints
- **SQLAlchemy 2.0** modern API
- **Alembic migrations** for schema management

---

**Status:** ✅ Complete and ready for next phase (API development)
**Last Updated:** 2026-01-20
