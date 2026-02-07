# Markdown File Creation Script - Documentation

## Overview

The `create_project_files.py` script ensures all project folders have markdown files, which is essential for proper bidirectional sync between your Google Drive Second Brain and the Project Tracker database.

## Why This Matters

### Without Markdown Files ❌

When a project folder doesn't have a markdown file:

```
10_Projects/
└── 01.01 The_Lund_Covenant/
    └── (no markdown file)
```

**Problems:**
- ❌ Project imports with minimal data only
- ❌ No task tracking possible
- ❌ Bidirectional sync fails (DB → File doesn't work)
- ❌ Metadata only stored in database
- ❌ Can't edit in Second Brain and sync back
- ❌ Momentum scores not persisted

**What gets created:**
```python
Project(
    title="The Lund Covenant",
    description="Discovered from folder: 01.01 The_Lund_Covenant\nNo markdown file found.",
    file_path="G:/My Drive/.../01.01 The_Lund_Covenant.md",  # Points to non-existent file
    # No tasks, limited metadata
)
```

### With Markdown Files ✅

When each project folder has a markdown file:

```
10_Projects/
└── 01.01 The_Lund_Covenant/
    └── 01.01 The_Lund_Covenant.md
```

**Benefits:**
- ✅ Full project import with all metadata
- ✅ Task tracking from markdown checkboxes
- ✅ Bidirectional sync works perfectly
- ✅ Metadata persisted in frontmatter
- ✅ Edit anywhere (database or file)
- ✅ Complete change tracking

**What gets created:**
```python
Project(
    title="The Lund Covenant",
    description="Project description from markdown",
    status="active",
    priority=3,
    file_path="G:/My Drive/.../01.01 The_Lund_Covenant.md",
    tasks=[...],  # Tasks from markdown
    momentum_score=0.75,  # Calculated and persisted
)
```

## The Script

### What It Does

1. **Scans** `10_Projects/` directory
2. **Identifies** folders matching pattern `xx.xx Project_Name`
3. **Checks** for existing `.md` files
4. **Creates** markdown files for folders without them
5. **Reports** what was created

### What It Creates

**Filename:** Same as folder name (e.g., `01.01 The_Lund_Covenant.md`)

**Content Template:**
```markdown
---
project_status: active
priority: 3
created_at: 2026-01-22T12:00:00Z
---

# The Lund Covenant

Project folder: `01.01 The_Lund_Covenant`

## Overview

<!-- Add project description here -->

## Next Actions

- [ ] Define project goals and objectives
- [ ] Break down into concrete tasks
- [ ] Identify first next action

## Notes

<!-- Add project notes, context, and resources here -->

## Reference

- Project discovered and initialized: 2026-01-22T12:00:00Z
```

## Usage

### Preview Mode (Safe)

See what would be created without making changes:

```bash
cd backend
poetry run python scripts\create_project_files.py --dry-run
```

**Output:**
```
📝 Create Project Markdown Files
====================================
📁 Scanning: G:\My Drive\999_SECOND_BRAIN\10_Projects

🔍 DRY RUN MODE - No files will be created

📊 Summary:
   Total project folders: 14
   ✅ With markdown: 8
   ⚠️  Without markdown: 6

⚠️  Projects missing markdown files:
   • 01.01 The_Lund_Covenant
     Title: The Lund Covenant
   • 10.06_AI_Use_Cases
     Title: AI Use Cases

Would create files:
   📄 G:\My Drive\...\01.01 The_Lund_Covenant.md
   📄 G:\My Drive\...\10.06_AI_Use_Cases.md
```

### Create Mode

Actually create the files:

```bash
poetry run python scripts\create_project_files.py
```

**Output:**
```
📝 Create Project Markdown Files
====================================
📁 Scanning: G:\My Drive\999_SECOND_BRAIN\10_Projects

📊 Summary:
   Total project folders: 14
   ✅ With markdown: 8
   ⚠️  Without markdown: 6

⚠️  Projects missing markdown files:
   • 01.01 The_Lund_Covenant
   • 10.06_AI_Use_Cases

====================================
Create 6 markdown files? (y/n): y

📝 Creating files...

✅ Created: 01.01 The_Lund_Covenant.md
   Path: G:\My Drive\...\01.01 The_Lund_Covenant.md
✅ Created: 10.06_AI_Use_Cases.md
   Path: G:\My Drive\...\10.06_AI_Use_Cases.md

====================================
📈 Results
====================================

✅ Files created: 6
❌ Errors: 0

✅ Done!

Next steps:
   1. Review created files in your Second Brain
   2. Add project details, tasks, and notes
   3. Run discovery: poetry run python scripts/discover_projects.py
```

## Workflow Integration

### Recommended: Before First Discovery

```bash
# 1. Create markdown files first
cd backend
poetry run python scripts\create_project_files.py --dry-run  # Preview
poetry run python scripts\create_project_files.py            # Create

# 2. Then run discovery
poetry run python scripts\discover_projects.py

# 3. Start server
poetry run python -m app.main
```

### For New Projects

When you create a new project folder in Google Drive:

```bash
# Option A: Use the script
poetry run python scripts\create_project_files.py

# Option B: Manually create markdown file
# Create: 01.13 New_Project.md in folder 01.13 New_Project/

# Then discover
poetry run python scripts\discover_projects.py
```

## Technical Details

### File Naming Convention

Script uses **exact folder name** as filename:

| Folder Name | Markdown Filename |
|------------|-------------------|
| `01.01 The_Lund_Covenant` | `01.01 The_Lund_Covenant.md` |
| `10.06_AI_Use_Cases` | `10.06_AI_Use_Cases.md` |
| `01.02 Winter Fire, Summer Ash` | `01.02 Winter Fire, Summer Ash.md` |

### Frontmatter Fields

```yaml
project_status: active      # Project status
priority: 3                 # Priority (1-5, 1 is highest)
created_at: ISO8601        # Creation timestamp
```

These fields are synced with the database during discovery.

### Template Sections

- **# Title** - Project title from folder name
- **## Overview** - Project description
- **## Next Actions** - Task list with checkboxes
- **## Notes** - General notes and context
- **## Reference** - Metadata and timestamps

## Safety Features

### Preview Mode

- `--dry-run` flag shows what would happen
- No files created or modified
- Safe to run anytime

### Confirmation Prompt

- Interactive confirmation before creating files
- Shows exact count and file paths
- Can cancel at any time

### Error Handling

- Continues on errors
- Reports all errors at end
- Doesn't stop batch operation

### Non-Destructive

- Only creates files that don't exist
- Never overwrites existing markdown files
- Preserves all existing data

## Troubleshooting

### "No project folders found"

**Check:**
- `SECOND_BRAIN_ROOT` path in config
- Folder naming matches pattern `xx.xx Project_Name`
- Google Drive File Stream is running

### "Permission denied"

**Solutions:**
- Ensure Google Drive folder is synced
- Check file permissions
- Make folder "Available offline"

### "Files created but not syncing"

**Check:**
- Run discovery after creating files
- Verify files appear in Google Drive
- Check sync status: `GET /api/v1/sync/status`

### Script finds 0 projects without markdown

**This means:**
- ✅ All project folders already have markdown files
- ✅ You can skip this step
- ✅ Ready to run discovery directly

## Examples

### Example 1: Fresh Setup

```bash
cd backend

# Check what needs files
poetry run python scripts\create_project_files.py --dry-run

# Output shows 14 folders, 0 with markdown
# Create all files
poetry run python scripts\create_project_files.py
# Answer: y

# All files created
# Now run discovery
poetry run python scripts\discover_projects.py
```

### Example 2: Partial Setup

```bash
cd backend

# Some projects already have markdown
poetry run python scripts\create_project_files.py --dry-run

# Output shows:
#   ✅ With markdown: 8 projects
#   ⚠️  Without markdown: 6 projects

# Create files for remaining 6
poetry run python scripts\create_project_files.py
# Answer: y

# Now all 14 have markdown
poetry run python scripts\discover_projects.py
```

### Example 3: Add New Project

```bash
# 1. Create folder in Google Drive
#    G:\My Drive\...\10_Projects\01.13 New_Novel\

# 2. Create markdown file
cd backend
poetry run python scripts\create_project_files.py
# Creates: 01.13 New_Novel.md

# 3. Edit file in Second Brain
# Add description, tasks, etc.

# 4. Import to database
poetry run python scripts\discover_projects.py
```

## Best Practices

### Before Discovery

1. ✅ Run `create_project_files.py` first
2. ✅ Review created files in Google Drive
3. ✅ Add initial content if desired
4. ✅ Then run discovery

### File Content

**Minimal (for quick start):**
- Just create files with script
- Add content later

**Detailed (recommended):**
- Create files with script
- Edit each file to add:
  - Project description
  - Initial tasks
  - Context and notes
- Then run discovery

### Maintenance

- Run script when adding new project folders
- Use `--dry-run` to check before creating
- Review created files before discovery

## See Also

- **Discovery Guide:** `backend/DISCOVERY_GUIDE.md`
- **Setup Guide:** `GOOGLE_DRIVE_SETUP.md`
- **Quick Start:** `QUICK_START.md`
- **Scripts README:** `backend/scripts/README.md`

---

**Script Location:** `backend/scripts/create_project_files.py`
**Last Updated:** 2026-01-22
**Status:** Production Ready
