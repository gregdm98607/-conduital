# Backend Scripts

Utility scripts for Conduital setup and maintenance.

## Scripts

### 1. `create_project_files.py`

**Purpose:** Creates minimal markdown files for project folders that don't have them.

**Why:** Ensures bidirectional sync works properly. Without markdown files, projects can only be partially imported and sync will fail.

**Usage:**

```bash
cd backend

# Preview what will be created (safe, no changes)
poetry run python scripts/create_project_files.py --dry-run

# Create markdown files
poetry run python scripts/create_project_files.py
```

**What it does:**
1. Scans `10_Projects/` for folders matching pattern `xx.xx Project_Name`
2. Checks for existing `.md` files in each folder
3. Creates markdown file for folders without one
4. Uses folder name as filename (e.g., `01.01 The_Lund_Covenant.md`)

**Template created:**
```markdown
---
project_status: active
priority: 3
created_at: 2026-01-22T12:00:00Z
---

# Project Title

Project folder: `01.01 Project_Name`

## Overview

<!-- Add project description here -->

## Next Actions

- [ ] Define project goals and objectives
- [ ] Break down into concrete tasks
- [ ] Identify first next action

## Notes

<!-- Add project notes, context, and resources here -->
```

**Options:**
- `--dry-run` - Show what would be created without creating files

**Output:**
- Summary of projects with/without markdown
- List of files to be created
- Confirmation prompt before creating
- Success/error report

### 2. `discover_projects.py`

**Purpose:** Discover and import all projects from Second Brain folder structure.

**Usage:**

```bash
cd backend

# Interactive discovery
poetry run python scripts/discover_projects.py
```

**What it does:**
1. Shows current area mappings
2. Identifies unmapped prefixes
3. Scans all project folders
4. Imports projects to database
5. Links to areas
6. Syncs markdown files
7. Reports statistics

**Output:**
```
🔍 Project Discovery Tool
====================================
📁 Second Brain Root: /path/to/your/second-brain
🗂️  Scanning directory: 10_Projects

📊 Current Area Mappings:
   01 → Literary Projects
   10 → Personal Projects

✅ All prefixes are mapped

🚀 Starting discovery...

📈 Discovery Results
====================================
✅ Success: True
📊 Folders discovered: 14
✨ Projects imported: 12
⏭️  Projects skipped: 2
❌ Errors: 0
```

### 3. `init_db.py`

**Purpose:** Initialize database schema and run migrations.

**Usage:**

```bash
cd backend
poetry run python scripts/init_db.py
```

**What it does:**
- Creates all database tables
- Runs Alembic migrations
- Sets up WAL mode
- Initializes default contexts

## Recommended Workflow

### Initial Setup

```bash
cd backend

# 1. Initialize database
poetry run python scripts/init_db.py

# 2. Create markdown files for projects
poetry run python scripts/create_project_files.py --dry-run  # Preview
poetry run python scripts/create_project_files.py            # Create

# 3. Discover and import projects
poetry run python scripts/discover_projects.py

# 4. Start server
poetry run python -m app.main
```

### After Adding New Projects

```bash
# If folder has no markdown file
poetry run python scripts/create_project_files.py

# Import new project
poetry run python scripts/discover_projects.py
```

### Regular Maintenance

```bash
# Update all momentum scores
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update

# Check for stalled projects
curl http://localhost:8000/api/v1/intelligence/stalled

# Sync all files
curl -X POST http://localhost:8000/api/v1/sync/scan
```

## Troubleshooting

### "Directory not found" error

Check `SECOND_BRAIN_ROOT` in `.env` or `config.py`:
```python
SECOND_BRAIN_ROOT = "/path/to/your/second-brain"
```

### "No project folders found"

Ensure folders match pattern: `xx.xx Project_Name`
- Valid: `01.01 The_Lund_Covenant`
- Invalid: `1.1 Project`, `01-01-Project`

### "Permission denied" error

Check file permissions on Google Drive folder. Ensure:
- Google Drive File Stream is running
- Folder is available offline (or online)
- No file locks

### Scripts run but nothing happens

Check if folders already have markdown files:
```bash
poetry run python scripts/create_project_files.py --dry-run
```

## Development

### Running Tests

```bash
cd backend
poetry run pytest
```

### Adding New Scripts

1. Create script in `backend/scripts/`
2. Add shebang: `#!/usr/bin/env python3`
3. Add docstring with usage
4. Add to this README
5. Make executable (Unix): `chmod +x script_name.py`

### Script Template

```python
#!/usr/bin/env python3
"""
Script Name

Description of what this script does.

Usage:
    python scripts/script_name.py [options]
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import SessionLocal

def main():
    """Main script entry point"""
    print("Script running...")
    # Your code here

if __name__ == "__main__":
    main()
```

## See Also

- [Discovery Guide](../DISCOVERY_GUIDE.md) - Complete discovery documentation
- [Setup Guide](../../GOOGLE_DRIVE_SETUP.md) - Initial setup instructions
- [API Documentation](../API_DOCUMENTATION.md) - API reference

---

**Last Updated:** 2026-01-22
