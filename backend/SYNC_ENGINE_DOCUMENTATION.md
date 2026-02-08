# Sync Engine Documentation

## Overview

The Sync Engine provides bidirectional synchronization between the Project Tracker database and your PARA-organized Second Brain markdown files.

## Features

- ✅ **Bidirectional Sync**: File ↔ Database
- ✅ **YAML Frontmatter**: Metadata in markdown files
- ✅ **Task Checkboxes**: Markdown checkboxes sync with database
- ✅ **File Watching**: Auto-sync on file changes (optional)
- ✅ **Conflict Detection**: Detect when both file and database changed
- ✅ **Debouncing**: Prevent rapid-fire syncs
- ✅ **Unique Markers**: HTML comments for reliable task tracking

## File Format

### Project File Structure

```markdown
---
tracker_id: 42
project_status: active
priority: 2
momentum_score: 0.75
area: AI Systems
last_synced: 2026-01-20T10:30:00Z
phases:
  - name: Research
    status: completed
    order: 1
  - name: Development
    status: active
    order: 2
---

# Project Title

Project description and notes...

## Next Actions

- [ ] Task 1 <!-- tracker:task:abc123 -->
- [ ] Task 2 <!-- tracker:task:def456 -->

## Tasks

- [ ] Additional task <!-- tracker:task:ghi789 -->
- [x] Completed task <!-- tracker:task:jkl012 -->

## Waiting For

- [ ] Feedback from editor <!-- tracker:task:mno345:waiting -->

## Completed

- [x] Previous task <!-- tracker:task:pqr678 -->
```

### YAML Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `tracker_id` | int | Project ID in database |
| `project_status` | str | active, completed, stalled, etc. |
| `priority` | int | 1-5 (1 is highest) |
| `momentum_score` | float | 0.0-1.0 |
| `area` | str | Area name (e.g., "AI Systems") |
| `target_completion_date` | date | ISO format YYYY-MM-DD |
| `last_synced` | datetime | ISO format timestamp |
| `phases` | list | Project phases with name, status, order |

### Task Markers

Tasks use HTML comments as unique markers:

```markdown
- [ ] Task title <!-- tracker:task:abc123 -->
```

**Marker Format**: `tracker:task:{unique_id}` or `tracker:task:{unique_id}:type`

**Types**:
- No suffix = regular action
- `:waiting` = waiting_for task
- `:someday` = someday_maybe task

## API Endpoints

### `POST /api/v1/sync/scan`
Scan Second Brain and sync all files to database.

**Response:**
```json
{
  "success": true,
  "message": "Scanned 45 files, synced 42",
  "stats": {
    "scanned": 45,
    "synced": 42,
    "errors": 1,
    "skipped": 2
  }
}
```

### `POST /api/v1/sync/project/{project_id}`
Sync a specific project to its file (Database → File).

**Response:**
```json
{
  "success": true,
  "message": "Project 42 synced to file"
}
```

### `POST /api/v1/sync/file?file_path={path}`
Sync a specific file to database (File → Database).

**Response:**
```json
{
  "success": true,
  "message": "File synced: The Lund Covenant",
  "stats": {"project_id": 42}
}
```

### `GET /api/v1/sync/status`
Get sync status for all tracked files.

**Response:**
```json
{
  "total_files": 45,
  "synced": 42,
  "pending": 1,
  "conflicts": 1,
  "errors": 1,
  "files": [...]
}
```

### `GET /api/v1/sync/conflicts`
Get all files with sync conflicts.

**Response:**
```json
[
  {
    "file_path": "/path/to/file.md",
    "last_synced": "2026-01-20T10:00:00Z",
    "entity_type": "project",
    "entity_id": 42
  }
]
```

### `POST /api/v1/sync/resolve/{sync_id}?use_file={true|false}`
Resolve a sync conflict.

- `use_file=true` - Keep file version (File → Database)
- `use_file=false` - Keep database version (Database → File)

## Sync Strategies

### Conflict Resolution

When both file and database have changed since last sync:

**1. Prompt Strategy** (default):
```env
CONFLICT_STRATEGY=prompt
```
- API returns 409 Conflict error
- User must manually resolve via `/sync/resolve`

**2. File Wins**:
```env
CONFLICT_STRATEGY=file_wins
```
- Always use file version
- Database overwrit with file data

**3. Database Wins**:
```env
CONFLICT_STRATEGY=db_wins
```
- Always use database version
- Skip file sync

## File Watcher

### Enable Auto-Sync

Uncomment in `app/main.py`:

```python
# In startup_event():
from app.sync.file_watcher import start_file_watcher
from app.sync.sync_engine import SyncEngine

def on_file_change(file_path):
    db = next(get_db())
    engine = SyncEngine(db)
    engine.sync_file_to_database(file_path)

start_file_watcher(on_file_change)
```

### How It Works

1. **Watches directories**: `10_Projects`, `20_Areas` (configurable)
2. **Detects changes**: File created, modified
3. **Debounces**: Waits 1 second after last change
4. **Syncs**: Calls sync engine to update database

## Usage Examples

### Initial Sync

Scan all existing files:

```bash
curl -X POST http://localhost:8000/api/v1/sync/scan
```

### Manual File Sync

After editing a file manually:

```bash
curl -X POST "http://localhost:8000/api/v1/sync/file?file_path=/path/to/project.md"
```

### Sync Project to File

After updating in database:

```bash
curl -X POST http://localhost:8000/api/v1/sync/project/42
```

### Check Sync Status

```bash
curl http://localhost:8000/api/v1/sync/status
```

### Resolve Conflict

Use file version:
```bash
curl -X POST "http://localhost:8000/api/v1/sync/resolve/5?use_file=true"
```

Use database version:
```bash
curl -X POST "http://localhost:8000/api/v1/sync/resolve/5?use_file=false"
```

## Programmatic Usage

### Python Example

```python
from pathlib import Path
from app.sync.sync_engine import SyncEngine
from app.core.database import SessionLocal

db = SessionLocal()
engine = SyncEngine(db)

# Scan all files
stats = engine.scan_and_sync()
print(f"Synced {stats['synced']} files")

# Sync specific file
file_path = Path("/path/to/your/second-brain/10_Projects/My_Project.md")
project = engine.sync_file_to_database(file_path)
print(f"Synced: {project.title}")

# Sync project to file
success = engine.sync_project_to_file(project_id=42)
if success:
    print("Synced to file")
```

## Sync State

The `sync_state` table tracks synchronization:

| Field | Description |
|-------|-------------|
| `file_path` | Path to file |
| `last_synced_at` | When last synced |
| `file_hash` | SHA-256 of file content |
| `sync_status` | synced, pending, conflict, error |
| `entity_type` | project, area |
| `entity_id` | ID in database |
| `error_message` | Error if failed |

## Best Practices

### 1. Initial Setup

```bash
# Scan existing files
curl -X POST http://localhost:8000/api/v1/sync/scan

# Check status
curl http://localhost:8000/api/v1/sync/status
```

### 2. Regular Workflow

**Option A: Manual Sync**
- Edit files in your Second Brain
- Run sync command when ready
- Review changes

**Option B: Auto-Sync**
- Enable file watcher
- Files sync automatically
- Check dashboard for updates

### 3. Conflict Handling

```bash
# Check for conflicts
curl http://localhost:8000/api/v1/sync/conflicts

# Review each conflict
# Decide which version to keep
# Resolve programmatically or via API
```

### 4. Task Management

**Creating Tasks in File:**
```markdown
## Next Actions
- [ ] New task <!-- tracker:task:new123 -->
```

**Completing Tasks in File:**
```markdown
- [x] Completed task <!-- tracker:task:abc123 -->
```

**Completing Tasks in API:**
```bash
curl -X POST http://localhost:8000/api/v1/tasks/42/complete
# File will update on next sync
```

## Troubleshooting

### Tasks Not Syncing

**Check marker format:**
```markdown
✅ Correct: - [ ] Task <!-- tracker:task:abc123 -->
❌ Wrong:   - [ ] Task (no marker)
❌ Wrong:   - [ ] Task <!-- wrong:format -->
```

### Conflicts

**Understand what changed:**
1. Check `last_synced_at` in sync_state
2. Check file modification time
3. Check project `updated_at` in database
4. If both changed since last sync = conflict

**Resolution:**
- If you edited file: use file version
- If you edited in API: use database version
- If both: manually merge changes first

### File Not Found

**Check paths:**
- Ensure file is in watched directory
- Verify `SECOND_BRAIN_ROOT` in .env
- Check `WATCH_DIRECTORIES` setting

### Sync Errors

**Check logs:**
```bash
# View API logs
tail -f logs/api.log

# Check sync status
curl http://localhost:8000/api/v1/sync/status
```

## Configuration

### Environment Variables

```env
# Second Brain root path
SECOND_BRAIN_ROOT=/path/to/your/second-brain

# Directories to watch (comma-separated)
WATCH_DIRECTORIES=10_Projects,20_Areas

# Sync interval for periodic sync (seconds)
SYNC_INTERVAL=30

# Conflict resolution strategy
CONFLICT_STRATEGY=prompt  # prompt, file_wins, db_wins
```

## Architecture

### Components

```
┌─────────────────────────────────────────┐
│         File System                      │
│  (Second Brain Markdown Files)          │
└──────────────┬──────────────────────────┘
               │
    ┌──────────▼──────────┐
    │   File Watcher      │
    │  (watchdog + debounce)│
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   Sync Engine        │
    │  - Parse markdown    │
    │  - Detect conflicts  │
    │  - Update database   │
    │  - Write files       │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   Database           │
    │  (SQLite + Models)   │
    └──────────────────────┘
```

### File Flow

**File → Database:**
1. File change detected or manual trigger
2. Read file and parse frontmatter + tasks
3. Check sync state for conflicts
4. Update/create project in database
5. Update/create tasks with markers
6. Update sync state

**Database → File:**
1. API call or scheduled sync
2. Load project with tasks
3. Build frontmatter from project
4. Update task checkboxes in content
5. Write file preserving other content
6. Update sync state

## Performance

### Optimization Tips

1. **Debounce file changes** (default: 1 second)
2. **Batch sync** during initial setup
3. **Limit concurrent syncs** to avoid conflicts
4. **Use markers** for reliable task tracking
5. **Index by file_path** in sync_state table

### Scalability

- Tested with 100+ projects
- 1000+ tasks
- Sync time: ~2-5 seconds per file
- Memory: ~50MB for typical workload

---

**Last Updated:** 2026-01-20
**Version:** 1.0
