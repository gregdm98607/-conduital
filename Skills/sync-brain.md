# Sync Brain Skill

**Name:** sync-brain

**Description:** Trigger bidirectional sync between Project-Tracker database and Second Brain markdown files. Ensures task completions, project updates, and status changes flow both directions.

**Trigger phrases:** "Sync brain", "Sync my files", "Update second brain", "Bidirectional sync", "Sync markdown"

---

## Instructions

When the user triggers this skill, orchestrate the bidirectional sync:

### Step 1: Pre-Sync Status
Check current sync state:

```
GET /api/sync/status
```

Present status:
```
## Second Brain Sync

### Current Status
- Last sync: [timestamp]
- Pending file changes: [X] files
- Pending DB changes: [X] records
- Conflicts detected: [X]
```

### Step 2: Detect Changes
Scan for changes in both directions:

```
GET /api/sync/scan
```

```
### Changes Detected

**Files → Database (Markdown changed):**
- 📄 10_Projects/Project-Tracker.md - 3 tasks checked off
- 📄 10_Projects/Lund-Covenant.md - Status updated to "editing"
- 📄 20_Areas/Health.md - New task added

**Database → Files (DB changed):**
- 🗄️ Project "API Refactor" - marked complete in app
- 🗄️ Task "Review PR" - completed via dashboard
- 🗄️ New project "Documentation Update" - needs file creation
```

### Step 3: Conflict Detection
If conflicts exist (both sides changed):

```
### ⚠️ Conflicts Detected

**Project-Tracker.md**
- File says: Task "Fix bug" is incomplete
- Database says: Task "Fix bug" completed 2 hours ago
- Recommendation: Trust database (more recent)

**Resolution:**
[ ] Use file version
[x] Use database version (recommended)
[ ] Manual review
```

### Step 4: Confirm Sync Direction
```
### Sync Plan

**Will apply:**
1. File → DB: Sync 3 task completions from markdown
2. File → DB: Update project status for Lund-Covenant
3. DB → File: Mark "Review PR" complete in markdown
4. DB → File: Create new file for "Documentation Update"

**Conflicts (using recommended resolution):**
1. "Fix bug" task - using database version

Proceed with sync? (yes/no/review conflicts)
```

### Step 5: Execute Sync
If confirmed:

```
POST /api/sync/execute
{
  "direction": "bidirectional",
  "conflict_resolution": "database_wins",
  "dry_run": false
}
```

### Step 6: Show Results

```
### Sync Complete ✓

**Applied Changes:**
✅ 3 tasks synced from markdown → database
✅ 1 project status updated
✅ 2 task completions written to markdown
✅ 1 new project file created

**File Markers Updated:**
- Project-Tracker.md: 3 task markers refreshed
- Lund-Covenant.md: tracker_id confirmed

**Summary:**
- Files updated: 4
- DB records updated: 5
- Conflicts resolved: 1
- Errors: 0

Next sync recommended: [timestamp + 4 hours]
```

### Step 7: Verify Integrity
Run post-sync verification:

```
GET /api/sync/verify
```

```
### Integrity Check
✅ All file markers valid
✅ All tracker_ids matched
✅ No orphaned records
✅ Hash verification passed
```

### Error Handling
If sync fails:

```
### ⚠️ Sync Error

**Failed Operations:**
❌ Could not write to 10_Projects/Locked-File.md
   Reason: File is open in another application

**Successful Operations:**
✅ 4 of 5 changes applied

**Recovery:**
- Close the file and retry: "Sync brain"
- Or skip this file: "Sync brain --skip Locked-File.md"
```

### Dry Run Mode
If user says "preview sync" or "dry run":

```
POST /api/sync/execute
{
  "dry_run": true
}
```

Show what would happen without making changes.

### Important Notes
- Sync uses SHA-256 hashing to detect file changes
- Task markers (<!-- tracker:task:abc123 -->) enable reliable sync
- Projects must have tracker_id in frontmatter for sync
- Conflicts default to "most recent wins" unless configured otherwise
- Always show what will change before applying
- Keep a backup/undo capability for sync operations
