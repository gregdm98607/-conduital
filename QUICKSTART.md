# Project Tracker - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- Poetry (install: `pip install poetry`)
- Your PARA-organized Second Brain

## Setup (First Time)

### 1. Install Dependencies

```bash
cd backend
poetry install
```

This installs all required packages.

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
SECOND_BRAIN_ROOT=G:/My Drive/999_SECOND_BRAIN
```

### 3. Initialize Database

```bash
poetry run python scripts/init_db.py
```

This creates the SQLite database with all tables.

## Running the Server

```bash
poetry run uvicorn app.main:app --reload
```

The API will start at: **http://localhost:8000**

## Explore the API

### Interactive Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Test the API

```bash
# Health check
curl http://localhost:8000/health

# Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Project", "status": "active", "priority": 2}'

# List projects
curl http://localhost:8000/api/v1/projects

# Get your daily dashboard
curl http://localhost:8000/api/v1/next-actions/dashboard
```

## Quick Examples

### Create Your First Project & Task

```python
import requests

# Create project
project = requests.post(
    "http://localhost:8000/api/v1/projects",
    json={
        "title": "The Lund Covenant",
        "description": "Literary fiction submission",
        "status": "active",
        "priority": 1
    }
).json()

print(f"Created project: {project['id']}")

# Create next action
task = requests.post(
    "http://localhost:8000/api/v1/tasks",
    json={
        "title": "Submit to agent",
        "project_id": project['id'],
        "is_next_action": True,
        "context": "administrative",
        "estimated_minutes": 20
    }
).json()

print(f"Created task: {task['id']}")

# Get your next actions
next_actions = requests.get(
    "http://localhost:8000/api/v1/next-actions"
).json()

print(f"Your top priority: {next_actions['tasks'][0]['title']}")
```

### GTD Workflow: Quick Capture

```python
import requests

# 1. Capture
inbox_item = requests.post(
    "http://localhost:8000/api/v1/inbox",
    json={"content": "Research comp titles for pitch"}
).json()

# 2. Clarify & Organize - Create task
task = requests.post(
    "http://localhost:8000/api/v1/tasks",
    json={
        "title": "Research comp titles",
        "project_id": 1,
        "context": "research",
        "estimated_minutes": 60
    }
).json()

# 3. Mark inbox as processed
requests.post(
    f"http://localhost:8000/api/v1/inbox/{inbox_item['id']}/process",
    json={
        "result_type": "task",
        "result_id": task['id']
    }
)
```

## Using the Swagger UI

1. Open http://localhost:8000/docs
2. Click on any endpoint (e.g., `POST /api/v1/projects`)
3. Click "Try it out"
4. Edit the JSON body
5. Click "Execute"
6. See the response

## Common Queries

### Get Next Actions by Context

```bash
# Creative work
curl "http://localhost:8000/api/v1/next-actions?context=creative"

# With time limit (60 minutes available)
curl "http://localhost:8000/api/v1/next-actions?time_available=60"

# Low energy tasks
curl "http://localhost:8000/api/v1/next-actions?energy_level=low"
```

### Find Overdue Tasks

```bash
curl http://localhost:8000/api/v1/tasks/overdue
```

### Get Quick Wins (< 2 minutes)

```bash
curl http://localhost:8000/api/v1/tasks/quick-wins
```

### Check Project Health

```bash
curl http://localhost:8000/api/v1/projects/1/health
```

## Database Location

Your data is stored in:
```
~/.project-tracker/tracker.db
```

Or on Windows:
```
C:\Users\YourName\.project-tracker\tracker.db
```

## Running Tests

```bash
poetry run pytest tests/test_api_basic.py -v
```

## Troubleshooting

### Port Already in Use

If port 8000 is busy:
```bash
poetry run uvicorn app.main:app --reload --port 8001
```

### Import Errors

Make sure you're in the backend directory:
```bash
cd backend
poetry install
```

### Database Issues

Reset the database:
```bash
rm ~/.project-tracker/tracker.db
poetry run python scripts/init_db.py
```

## Next Steps

- Read **API_DOCUMENTATION.md** for full API reference
- Explore **API_IMPLEMENTATION_SUMMARY.md** for architecture details
- Check **SETUP_GUIDE.md** for advanced configuration
- Review **Project_Tracker_Technical_Spec.md** for complete specification

## Support

For issues or questions:
- Check the documentation in the project root
- Review the Swagger UI at /docs
- Examine test files in `tests/` for usage examples

---

**Happy Tracking!** 🎯

Your projects are now backed by a smart, momentum-first system that helps you maintain flow and unstick stalled work.
