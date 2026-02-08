# Project Tracker - Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
cd backend
poetry install
```

This will install all required Python packages including:
- FastAPI (web framework)
- SQLAlchemy (database ORM)
- Alembic (database migrations)
- Anthropic SDK (Claude AI integration)
- And more...

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and update these key settings:

```env
# Point to your Second Brain
SECOND_BRAIN_ROOT=/path/to/your/second-brain

# Optional: Enable AI features
ANTHROPIC_API_KEY=your_api_key_here
AI_FEATURES_ENABLED=true
```

### 3. Initialize Database

```bash
# Option A: Use the initialization script
poetry run python scripts/init_db.py

# Option B: Manual steps
poetry run alembic revision --autogenerate -m "Initial schema"
poetry run alembic upgrade head
```

This creates:
- SQLite database at `~/.project-tracker/tracker.db`
- All tables based on the models
- Indexes for performance
- WAL mode enabled for better concurrency

### 4. Verify Setup

```bash
# Check Alembic version
poetry run alembic current

# You should see output like:
# INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
# INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
# 20260120_1234-abc123_initial_database_schema (head)
```

## Database Structure

The database includes these tables:

### Core Tables
- `projects` - Multi-step outcomes with clear endpoints
- `tasks` - Individual action items (GTD Next Actions)
- `areas` - Areas of Responsibility
- `goals` - 1-3 year objectives
- `visions` - 3-5 year vision and life purpose

### Supporting Tables
- `project_phases` - Stages in multi-phase projects
- `phase_templates` - Reusable phase definitions
- `contexts` - GTD contexts (@home, @computer, etc.)
- `activity_log` - Change tracking for momentum calculation
- `sync_state` - File synchronization status
- `inbox` - GTD inbox for quick capture

## Key Features

### Momentum Calculation
Projects automatically track:
- Last activity timestamp
- Momentum score (0.0 to 1.0)
- Stalled status (no activity for 14+ days)
- Activity logs for trend analysis

### Next Actions
Tasks can be marked as:
- `is_next_action` - The immediate next step
- `is_two_minute_task` - Quick wins
- `is_unstuck_task` - Minimal tasks to restart stalled projects

### File Integration
- `file_path` - Link to Second Brain markdown file
- `file_hash` - SHA-256 for change detection
- `file_marker` - Unique ID for task sync

## What's Created

```
~/.project-tracker/
└── tracker.db          # Main SQLite database
└── tracker.db-wal      # Write-Ahead Log
└── tracker.db-shm      # Shared memory

project-tracker/
├── backend/
│   ├── alembic/
│   │   └── versions/   # Migration files will appear here
│   ├── app/
│   │   ├── models/     # ✅ All 11 models created
│   │   ├── core/       # ✅ Database config, utilities
│   │   ├── api/        # ⏳ Coming next
│   │   ├── services/   # ⏳ Coming next
│   │   └── schemas/    # ⏳ Coming next
│   └── tests/          # ⏳ Coming next
```

## Next Development Steps

1. **API Endpoints** - Create FastAPI routes for CRUD operations
2. **Pydantic Schemas** - Request/response validation
3. **Sync Engine** - Bidirectional file synchronization
4. **Momentum Service** - Calculate project momentum scores
5. **AI Integration** - Unstuck task generation with Claude

## Common Commands

```bash
# Development server
poetry run uvicorn app.main:app --reload

# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1

# View migration history
poetry run alembic history

# Run tests (when implemented)
poetry run pytest

# Format code
poetry run black .

# Lint code
poetry run ruff check .
```

## Troubleshooting

### Database locked error
- This usually means another process is using the database
- Close any SQLite browser tools
- Make sure only one server instance is running

### Import errors
- Make sure you're in the `backend` directory
- Run `poetry install` to install all dependencies
- Activate the virtual environment: `poetry shell`

### Migration conflicts
- Check `alembic/versions/` for duplicate migrations
- Use `alembic history` to see migration chain
- Delete conflicting migrations and regenerate if needed

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECOND_BRAIN_ROOT` | - | Path to PARA Second Brain |
| `WATCH_DIRECTORIES` | `10_Projects,20_Areas` | Directories to watch |
| `SYNC_INTERVAL` | `30` | Seconds between sync checks |
| `MOMENTUM_STALLED_THRESHOLD_DAYS` | `14` | Days before project marked stalled |
| `ANTHROPIC_API_KEY` | - | Claude API key (optional) |
| `AI_FEATURES_ENABLED` | `false` | Enable AI features |

## Support

For issues or questions about the database models and migrations, refer to:
- Technical Specification: `Project_Tracker_Technical_Spec.md`
- Model definitions: `backend/app/models/`
- Database utilities: `backend/app/core/db_utils.py`
