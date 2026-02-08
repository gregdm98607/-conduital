# Google Drive Integration - Setup Guide

## Overview

Your Project Tracker is now integrated with your Google Drive Second Brain via project discovery. The system automatically scans your `10_Projects` folder and imports projects based on the `xx.xx Project_Name` naming pattern.

## Current Configuration

Based on your screenshot, here's your current structure:

```
/path/to/your/second-brain/10_Projects/
├── _Project_Templates/
├── 01.01 The_Lund_Covenant/
├── 01.02 Winter Fire, Summer Ash/
├── 01.03 Ley-Lines Reboot/
├── 01.11 Encyclopedia_of_Emery_County/
├── 01.12 Five Ordinary Years/
├── 10.01 Kitchen Remodel/
├── 10.02 Paris Vacation/
├── 10.03 CODENAME - Operation Granny Files/
├── 10.04 Direct Line Biographies/
├── 10.05 Genealogy Training Course/
├── 10.06_AI_Use_Cases/
├── 10.07_Neural_Link_System/
├── 10.08_Proactive_Assistant/
└── 10.09 Bamwiru_Shelter_of_Love_Chicken_Farm/
```

## Quick Start

### 1. Create Markdown Files (Recommended)

Before discovery, ensure all project folders have markdown files:

```bash
cd C:\Dev\project-tracker\backend

# Preview what will be created
poetry run python scripts\create_project_files.py --dry-run

# Create the files
poetry run python scripts\create_project_files.py
```

This creates a template markdown file for each project folder that doesn't have one.

**Why this matters:**
- ✅ Enables bidirectional sync (database ↔ file)
- ✅ Allows task tracking in markdown
- ✅ Stores metadata in frontmatter
- ✅ Prevents sync errors

### 2. Configure Area Mappings

Update your `.env` file to map prefixes to areas:

```bash
# Edit .env file (or create if it doesn't exist)
# Add these lines:
AREA_PREFIX_MAP={"01": "Literary Projects", "10": "Personal Projects"}
```

Or update `backend/app/core/config.py` directly:

```python
AREA_PREFIX_MAP: dict[str, str] = {
    "01": "Literary Projects",      # Novels, manuscripts
    "10": "Personal Projects",       # Home, family, personal development
    "20": "Research Projects",       # If you have these
}
```

### 3. Run Initial Discovery

**Using the script (recommended):**

```bash
poetry run python scripts\discover_projects.py
```

Option B: **Using the API**

```bash
# Start the server
poetry run python -m app.main

# In another terminal, run discovery
curl -X POST http://localhost:8000/api/v1/discovery/scan
```

### 3. Verify Import

Check imported projects:

```bash
# Get all projects
curl http://localhost:8000/api/v1/projects

# Or view in browser
# Open: http://localhost:8000/docs
# Navigate to GET /api/v1/projects and click "Try it out"
```

### 4. Update Momentum Scores

Calculate initial momentum for all projects:

```bash
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update
```

### 5. Check Dashboard

```bash
# Get next actions
curl http://localhost:8000/api/v1/next-actions

# Get project health
curl http://localhost:8000/api/v1/intelligence/stalled
```

## Detailed Setup

### Step-by-Step Configuration

#### 1. Verify Google Drive Path

Make sure your `.env` has the correct path:

```env
SECOND_BRAIN_ROOT=/path/to/your/second-brain
```

#### 2. Check for Unmapped Prefixes

Before running discovery, check what prefixes exist:

```bash
curl http://localhost:8000/api/v1/discovery/suggestions
```

This will show any prefixes (like `01`, `10`) that don't have area mappings.

#### 3. Add All Area Mappings

Based on your structure, you have:
- `01.xx` - Literary projects (6 projects)
- `10.xx` - Personal/tech projects (9 projects)

Update mappings:

```bash
curl -X POST http://localhost:8000/api/v1/discovery/mappings \
  -H "Content-Type: application/json" \
  -d "{\"01\": \"Literary Projects\", \"10\": \"Personal Projects\"}"
```

#### 4. Run Full Discovery and Sync

```bash
# This runs discovery + markdown sync
curl -X POST "http://localhost:8000/api/v1/sync/scan?discover_projects=true"
```

Expected output:
```json
{
  "success": true,
  "message": "Scanned 15 files, synced 12; Discovered 15 folders, imported 12 projects",
  "stats": {
    "discovery": {
      "discovered": 15,
      "imported": 12,
      "skipped": 3
    },
    "scanned": 15,
    "synced": 12
  }
}
```

## Understanding Your Projects

### Literary Projects (01.xx)

These will be mapped to "Literary Projects" area:
- 01.01 The_Lund_Covenant
- 01.02 Winter Fire, Summer Ash
- 01.03 Ley-Lines Reboot
- 01.11 Encyclopedia_of_Emery_County
- 01.12 Five Ordinary Years

**Expected behavior:**
- Each will become a project in the database
- Linked to "Literary Projects" area
- Markdown files synced with tasks
- Momentum scores calculated

### Personal Projects (10.xx)

These will be mapped to "Personal Projects" area:
- 10.01 Kitchen Remodel
- 10.02 Paris Vacation
- 10.03 CODENAME - Operation Granny Files
- 10.04 Direct Line Biographies
- 10.05 Genealogy Training Course
- 10.06 AI_Use_Cases
- 10.07 Neural_Link_System
- 10.08 Proactive_Assistant
- 10.09 Bamwiru_Shelter_of_Love_Chicken_Farm

**Note:** Some of these (10.06-10.08) might be tech/AI projects. Consider:
- Keep them in "Personal Projects", OR
- Create a new area mapping: `"11": "Tech Projects"`

### Special Folders

`_Project_Templates` will be skipped (doesn't match pattern).

## Testing Discovery

### Test Single Project

Test import of one project:

```bash
curl -X POST http://localhost:8000/api/v1/discovery/scan-folder \
  -H "Content-Type: application/json" \
  -d "{\"folder_name\": \"01.01 The_Lund_Covenant\"}"
```

### View Specific Project

After import, view the project:

```bash
# List all projects
curl http://localhost:8000/api/v1/projects

# Get specific project (use ID from above)
curl http://localhost:8000/api/v1/projects/1
```

## Workflow Integration

### Creating New Projects

**Method 1: Create in Google Drive**
1. Create folder: `10_Projects/01.13 New_Novel/`
2. Add markdown file: `New_Novel.md`
3. Run discovery: `POST /api/v1/discovery/scan`

**Method 2: Create via API**
1. Create project: `POST /api/v1/projects`
2. System creates markdown file
3. Edit in Google Drive
4. Auto-syncs back to database

### Editing Projects

**In Google Drive:**
1. Edit markdown file
2. Changes sync automatically (if file watcher enabled)
3. Or run manual sync: `POST /api/v1/sync/file?file_path=...`

**In Application:**
1. Update via API: `PUT /api/v1/projects/{id}`
2. Sync to file: `POST /api/v1/sync/project/{id}`
3. Changes appear in Google Drive

## Troubleshooting

### Projects Not Appearing

**Check path:**
```bash
# Verify Second Brain root
curl http://localhost:8000/health
```

**Check naming:**
- Must be: `xx.xx Project_Name`
- Not: `1.1 Project` or `01-01-Project`

**Check logs:**
```bash
cd backend
poetry run python scripts\discover_projects.py
# Read output for errors
```

### Area Not Linked

If project imports without area:

```bash
# Check current mappings
curl http://localhost:8000/api/v1/discovery/mappings

# Get suggestions
curl http://localhost:8000/api/v1/discovery/suggestions

# Add missing mapping
curl -X POST http://localhost:8000/api/v1/discovery/mappings \
  -H "Content-Type: application/json" \
  -d "{\"01\": \"Literary Projects\", \"10\": \"Personal Projects\"}"

# Re-run discovery
curl -X POST http://localhost:8000/api/v1/discovery/scan
```

### Duplicate Prefixes

If you have many `10.xx` projects with different types:

**Option 1: Use subcategories**
- Keep all as "Personal Projects"
- Use project status/tags to differentiate

**Option 2: Reorganize prefixes**
- `01.xx` - Literary
- `10.xx` - Home/Family
- `11.xx` - Tech/AI
- `20.xx` - Research/Genealogy

Then update folder names in Google Drive.

## Next Steps

### 1. Enable File Watcher (Phase 2)

For automatic sync on file changes, uncomment in `backend/app/main.py`:

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

### 2. Start Frontend

```bash
cd C:\Dev\project-tracker\frontend
npm run dev
```

Open http://localhost:5173 to view dashboard.

### 3. Weekly Review

Set up weekly review workflow:

```bash
# Get weekly review data
curl http://localhost:8000/api/v1/intelligence/weekly-review

# Update all momentum scores
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update

# Check stalled projects
curl http://localhost:8000/api/v1/intelligence/stalled
```

## Complete Example Workflow

```bash
# 1. Start backend
cd C:\Dev\project-tracker\backend
poetry run python -m app.main

# 2. In new terminal, configure areas
curl -X POST http://localhost:8000/api/v1/discovery/mappings \
  -H "Content-Type: application/json" \
  -d "{\"01\": \"Literary Projects\", \"10\": \"Personal Projects\"}"

# 3. Run discovery + sync
curl -X POST "http://localhost:8000/api/v1/sync/scan?discover_projects=true"

# 4. Update momentum
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update

# 5. Get next actions
curl http://localhost:8000/api/v1/next-actions

# 6. Check stalled projects
curl http://localhost:8000/api/v1/intelligence/stalled

# 7. Start frontend
cd ..\frontend
npm run dev

# 8. Open browser
# http://localhost:5173
```

## Support

For issues or questions:
1. Check logs in `backend/logs/`
2. Review API docs: http://localhost:8000/docs
3. Read detailed guide: `backend/DISCOVERY_GUIDE.md`
4. Check sync documentation: `backend/SYNC_ENGINE_DOCUMENTATION.md`

---

**Setup Date:** 2026-01-22
**Phase:** 1 - Project Discovery
**Status:** Ready for Initial Import
