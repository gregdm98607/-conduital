# Conduital — Backend

Intelligent momentum-based project management with markdown file sync.

## Setup

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)

### Installation

1. Install dependencies:
```bash
poetry install
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Edit `.env` and configure your settings (especially `SECOND_BRAIN_ROOT`)

4. Initialize database:
```bash
poetry run alembic upgrade head
```

### Running the Application

```bash
# Development server with auto-reload
poetry run uvicorn app.main:app --reload --port 8000
```

## Database Migrations

### Create a new migration

```bash
# Auto-generate migration from model changes
poetry run alembic revision --autogenerate -m "description of changes"

# Create empty migration
poetry run alembic revision -m "description of changes"
```

### Apply migrations

```bash
# Upgrade to latest
poetry run alembic upgrade head

# Upgrade one version
poetry run alembic upgrade +1

# Downgrade one version
poetry run alembic downgrade -1

# Show current version
poetry run alembic current

# Show migration history
poetry run alembic history
```

## Project Structure

```
backend/
├── alembic/              # Database migrations
│   ├── versions/         # Migration scripts
│   └── env.py           # Alembic configuration
├── app/
│   ├── api/             # API endpoints
│   ├── core/            # Core configuration
│   │   ├── config.py    # Settings
│   │   └── database.py  # Database setup
│   ├── models/          # SQLAlchemy models
│   │   ├── project.py
│   │   ├── task.py
│   │   ├── area.py
│   │   └── ...
│   ├── schemas/         # Pydantic schemas (coming soon)
│   ├── services/        # Business logic (coming soon)
│   └── main.py          # FastAPI application
├── tests/               # Test suite
├── alembic.ini          # Alembic configuration
├── pyproject.toml       # Poetry dependencies
└── README.md
```

## Database Models

### Core Models

- **Project**: Multi-step outcomes with clear endpoints
- **Task**: Individual action items (next actions)
- **Area**: Areas of Responsibility (ongoing spheres of activity)
- **Goal**: 1-3 year objectives
- **Vision**: 3-5 year vision and life purpose

### Supporting Models

- **ProjectPhase**: Stages in multi-phase projects
- **PhaseTemplate**: Reusable phase definitions
- **Context**: Contexts for organizing tasks (@home, @computer, etc.)
- **ActivityLog**: Change tracking for momentum calculation
- **SyncState**: File synchronization status
- **InboxItem**: Inbox for quick capture

## Configuration

Key settings in `.env`:

- `SECOND_BRAIN_ROOT`: Path to your synced notes folder
- `WATCH_DIRECTORIES`: Directories to watch for changes (default: 10_Projects, 20_Areas)
- `SYNC_INTERVAL`: How often to check for file changes (seconds)
- `ANTHROPIC_API_KEY`: Optional - for AI features
- `MOMENTUM_STALLED_THRESHOLD_DAYS`: Days of inactivity before project is marked stalled

## Development

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy app
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_models.py
```

## Next Steps

1. Implement API endpoints (`app/api/`)
2. Create Pydantic schemas for request/response validation
3. Implement sync engine for bidirectional file sync
4. Build momentum calculation service
5. Add AI integration for unstuck task generation

## License

Private project for personal use.
