# Project Discovery Guide

## Overview

The Project Discovery system automatically scans your Second Brain folder structure and imports projects based on PARA naming conventions. It recognizes the `xx.xx Project_Name` folder pattern and maps projects to areas using configurable prefix mappings.

## Features

- ✅ **Automatic folder scanning** - Discovers projects from `10_Projects/` directory
- ✅ **Area mapping** - Links projects to areas based on prefix (01, 10, 20, etc.)
- ✅ **Markdown sync** - Integrates with existing sync engine
- ✅ **Configuration** - Customizable area prefix mappings
- ✅ **Suggestions** - Identifies unmapped prefixes and suggests areas
- ✅ **Bulk import** - Command-line script for initial setup

## Folder Structure

Your Second Brain should follow this structure:

```
your-second-brain/
├── 10_Projects/
│   ├── 01.01 The_Lund_Covenant/
│   │   └── The_Lund_Covenant.md
│   ├── 01.02 Winter Fire, Summer Ash/
│   │   └── Winter_Fire_Summer_Ash.md
│   ├── 10.01 Kitchen_Remodel/
│   │   └── Kitchen_Remodel.md
│   └── ...
└── 20_Areas/
    ├── 01_Literary_Projects/
    ├── 10_Personal_Development/
    └── ...
```

### Naming Pattern

Projects must follow this pattern:

```
xx.xx Project_Name
```

Where:
- `xx` (first two digits) = Area prefix (e.g., 01, 10, 20)
- `xx` (second two digits) = Project number within area
- `Project_Name` = Project title (underscores or spaces)

**Examples:**
- `01.01 The_Lund_Covenant` → Area: 01, Project: The Lund Covenant
- `10.05 Kitchen_Remodel` → Area: 10, Project: Kitchen Remodel
- `20.03 Genealogy Research` → Area: 20, Project: Genealogy Research

## Configuration

### Area Prefix Mapping

Configure area mappings in your `.env` file or `config.py`:

```python
# In backend/app/core/config.py
AREA_PREFIX_MAP: dict[str, str] = {
    "01": "Literary Projects",
    "10": "Personal Development",
    "20": "Research"
}
```

Or in `.env`:

```env
AREA_PREFIX_MAP={"01": "Literary Projects", "10": "Personal Development"}
```

### Pattern Configuration

The folder pattern is configurable (default shown):

```python
PROJECT_FOLDER_PATTERN: str = r"^(\d{2})\.(\d{2})\s+(.+)$"
```

## Usage

### Step 0: Create Markdown Files (Recommended First Step)

Before running discovery, ensure all project folders have markdown files:

```bash
cd backend

# Preview what will be created
poetry run python scripts/create_project_files.py --dry-run

# Create markdown files for folders that don't have them
poetry run python scripts/create_project_files.py
```

**This creates:**
- Markdown file matching folder name
- Minimal frontmatter with metadata
- Template sections for tasks and notes
- Proper structure for bidirectional sync

**Without markdown files:**
- ⚠️ Projects import with minimal data
- ⚠️ No tasks can be tracked
- ⚠️ Bidirectional sync won't work properly
- ⚠️ Metadata only in database

**With markdown files:**
- ✅ Full project import with metadata
- ✅ Task tracking enabled
- ✅ Bidirectional sync works
- ✅ Metadata persisted in files

### Method 1: Command Line Script (Recommended for Initial Setup)

Run the discovery script:

```bash
# Navigate to backend directory
cd backend

# Run with Poetry
poetry run python scripts/discover_projects.py

# Or activate virtual environment and run
python scripts/discover_projects.py
```

**Output:**
```
🔍 Project Discovery Tool
====================================
📁 Second Brain Root: /path/to/your/second-brain
🗂️  Scanning directory: 10_Projects

📊 Current Area Mappings:
   01 → Literary Projects
   10 → Personal Development

🚀 Starting discovery...

📈 Discovery Results
====================================
✅ Success: True
📊 Folders discovered: 14
✨ Projects imported: 12
⏭️  Projects skipped: 2
❌ Errors: 0
```

### Method 2: API Endpoints

#### Discover All Projects

```bash
POST /api/v1/discovery/scan
```

**Response:**
```json
{
  "success": true,
  "discovered": 14,
  "imported": 12,
  "skipped": 2,
  "errors": []
}
```

#### Get Area Mappings

```bash
GET /api/v1/discovery/mappings
```

**Response:**
```json
{
  "01": "Literary Projects",
  "10": "Personal Development",
  "20": "Research"
}
```

#### Update Area Mappings

```bash
POST /api/v1/discovery/mappings
Content-Type: application/json

{
  "01": "Literary Projects",
  "10": "Personal Development",
  "20": "Research",
  "30": "Business Projects"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Area mappings updated (runtime only - update .env to persist)",
  "mappings": {...},
  "note": "Run /discovery/scan to apply new mappings to projects"
}
```

#### Get Suggestions for Unmapped Prefixes

```bash
GET /api/v1/discovery/suggestions
```

**Response:**
```json
{
  "unmapped_prefixes": {
    "11": {
      "project_count": 3,
      "sample_projects": ["Neural Link System", "Proactive Assistant"],
      "suggested_area": "Area 11"
    }
  }
}
```

#### Scan Specific Folder

```bash
POST /api/v1/discovery/scan-folder
Content-Type: application/json

{
  "folder_name": "01.01 The_Lund_Covenant"
}
```

### Method 3: Integrated with Sync

Run regular sync with discovery:

```bash
POST /api/v1/sync/scan?discover_projects=true
```

This will:
1. Run project discovery
2. Sync all markdown files
3. Update projects and tasks

## Workflow

### Initial Setup

1. **Configure area mappings** in `.env` or `config.py`
2. **Run discovery script**:
   ```bash
   poetry run python scripts/discover_projects.py
   ```
3. **Review imported projects**:
   ```bash
   curl http://localhost:8000/api/v1/projects
   ```
4. **Update momentum scores**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update
   ```

### Ongoing Usage

**Option A: Automatic (recommended for Phase 2)**
- File watcher detects new folders
- Auto-discovery runs on folder creation
- Projects automatically imported

**Option B: Manual**
- Create new project folder in Second Brain
- Run discovery: `POST /api/v1/discovery/scan`
- Or sync with discovery: `POST /api/v1/sync/scan?discover_projects=true`

### Adding New Areas

1. **Identify new prefix** from suggestions:
   ```bash
   GET /api/v1/discovery/suggestions
   ```

2. **Update mappings**:
   ```bash
   POST /api/v1/discovery/mappings
   ```

3. **Run discovery** to apply:
   ```bash
   POST /api/v1/discovery/scan
   ```

4. **Make persistent** by updating `.env`

## How It Works

### Discovery Process

1. **Scan folders** - Read all subdirectories in `10_Projects/`
2. **Match pattern** - Check folder name against pattern `xx.xx Project_Name`
3. **Extract metadata** - Parse area prefix, project number, title
4. **Map to area** - Lookup area from prefix mapping
5. **Find markdown** - Look for `.md` file in folder
6. **Sync file** - Use existing sync engine to import
7. **Update project** - Link to area, set metadata

### Integration with Sync Engine

Discovery leverages the existing sync engine:

```python
# Discovery finds folder
folder = Path("10_Projects/01.01 The_Lund_Covenant")

# Extracts metadata
area_prefix = "01"  # First two digits
project_title = "The Lund Covenant"

# Finds markdown
md_file = folder / "The_Lund_Covenant.md"

# Uses sync engine
sync_engine.sync_file_to_database(md_file)

# Updates with area
project.area_id = get_area_for_prefix(area_prefix).id
```

### Area Creation

Areas are auto-created if they don't exist:

```python
if not Area.exists(area_name):
    area = Area(
        title=area_name,
        folder_path=f"20_Areas/{prefix}_{area_name}"
    )
    db.add(area)
```

## Troubleshooting

### Projects Not Discovered

**Check folder naming:**
```bash
# Valid
01.01 Project_Name
10.05 Another_Project

# Invalid (will be skipped)
1.1 Project  # Need two digits
01-01 Project  # Need dot separator
Project_Name  # Need prefix
```

**Check area mapping:**
```bash
# Get suggestions for unmapped prefixes
GET /api/v1/discovery/suggestions

# Add missing mappings
POST /api/v1/discovery/mappings
```

### Projects Skipped

Projects may be skipped if:
- Folder name doesn't match pattern
- No markdown file found (minimal project created instead)
- Project already exists in database
- Area prefix not mapped (project created without area)

### Area Not Linked

If projects import without area:
1. Check area mapping exists: `GET /api/v1/discovery/mappings`
2. Add missing mapping: `POST /api/v1/discovery/mappings`
3. Re-run discovery: `POST /api/v1/discovery/scan`

### Duplicate Projects

Discovery checks for existing projects by `file_path`. If you re-run discovery:
- Existing projects are updated (via sync)
- New projects are created
- Deleted folders are not removed from database

## Best Practices

### Naming Convention

**Do:**
- Use consistent two-digit prefixes: `01`, `10`, `20`
- Separate with dot and space: `01.01 Project`
- Use descriptive names: `01.01 The_Lund_Covenant`

**Don't:**
- Skip leading zeros: `1.1 Project`
- Use hyphens: `01-01-Project`
- Use inconsistent separators: `01.01_Project`

### Area Organization

**Recommended prefixes:**
```
01-09: Creative/Personal projects
10-19: Professional/Career projects
20-29: Learning/Research projects
30-39: Health/Wellness projects
40-49: Financial/Business projects
50-59: Relationships/Social projects
```

### Markdown Files

**Best practice:**
- One markdown file per project folder
- File name matches folder name
- Contains frontmatter with metadata
- Includes task lists

**Example:**
```markdown
---
tracker_id: 42
project_status: active
priority: 2
---

# The Lund Covenant

Novel manuscript in submission phase.

## Next Actions
- [ ] Review agent feedback <!-- tracker:task:abc123 -->
- [ ] Submit to next agent <!-- tracker:task:def456 -->
```

## Future Enhancements (Phase 2)

Planned features:
- [ ] Automatic folder watching
- [ ] Real-time discovery on folder creation
- [ ] Template detection by project type
- [ ] Automatic phase assignment
- [ ] Folder rename detection
- [ ] Archive detection and handling
- [ ] Bulk area operations
- [ ] Project migration tools

## API Reference

### Discovery Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/discovery/scan` | POST | Discover all projects |
| `/api/v1/discovery/mappings` | GET | Get area mappings |
| `/api/v1/discovery/mappings` | POST | Update area mappings |
| `/api/v1/discovery/suggestions` | GET | Get unmapped prefix suggestions |
| `/api/v1/discovery/scan-folder` | POST | Scan specific folder |

### Sync with Discovery

| Endpoint | Method | Parameters |
|----------|--------|------------|
| `/api/v1/sync/scan` | POST | `?discover_projects=true` |

## Examples

### Full Workflow Example

```bash
# 1. Check current mappings
curl http://localhost:8000/api/v1/discovery/mappings

# 2. Get suggestions for unmapped prefixes
curl http://localhost:8000/api/v1/discovery/suggestions

# 3. Add new mapping
curl -X POST http://localhost:8000/api/v1/discovery/mappings \
  -H "Content-Type: application/json" \
  -d '{"01": "Literary Projects", "10": "Personal Development"}'

# 4. Run discovery
curl -X POST http://localhost:8000/api/v1/discovery/scan

# 5. Check imported projects
curl http://localhost:8000/api/v1/projects

# 6. Update momentum scores
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update

# 7. View dashboard
curl http://localhost:8000/api/v1/next-actions
```

---

**Last Updated:** 2026-01-22
**Version:** 1.0 - Phase 1 Complete
