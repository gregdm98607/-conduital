# Second Brain Sync - How It Works

## 📂 What Files Are Scanned?

The sync engine looks in directories you specify in your `.env` file:

```env
SECOND_BRAIN_ROOT=G:/My Drive/999_SECOND_BRAIN
WATCH_DIRECTORIES=10_Projects,20_Areas
```

It will scan:
- `G:/My Drive/999_SECOND_BRAIN/10_Projects/**/*.md`
- `G:/My Drive/999_SECOND_BRAIN/20_Areas/**/*.md`

**All markdown files** in these directories (and subdirectories) are candidates for syncing.

---

## 🎯 Example 1: Brand New Project (No Sync Yet)

### Your Existing Markdown File

**Location:** `G:/My Drive/999_SECOND_BRAIN/10_Projects/01_Active/01.01_The_Lund_Covenant/Project.md`

```markdown
# The Lund Covenant

Literary fiction novel about a secret society in Minnesota.

## Status
- Currently in submission phase
- Targeting literary agents

## Next Steps
- Research 10 literary agents
- Draft personalized query letter
- Prepare 3-chapter sample

## Notes
Working with beta readers for final polish before queries.
```

### What Happens When You Sync

**Run sync:**
```bash
curl -X POST http://localhost:8000/api/v1/sync/scan
```

**The sync engine will:**

1. ✅ Find the file (ends in `.md`, in watched directory)
2. ✅ Extract title from `# The Lund Covenant` heading
3. ✅ Create a new project in database
4. ✅ Add YAML frontmatter to your file:

**Your file becomes:**

```markdown
---
tracker_id: 1
project_status: active
priority: 3
momentum_score: 0.0
last_synced: 2026-01-22T15:30:00Z
---

# The Lund Covenant

Literary fiction novel about a secret society in Minnesota.

## Status
- Currently in submission phase
- Targeting literary agents

## Next Steps
- Research 10 literary agents
- Draft personalized query letter
- Prepare 3-chapter sample

## Notes
Working with beta readers for final polish before queries.
```

**Now:** Any changes you make in the UI will update the file, and vice versa!

---

## 🎯 Example 2: Project With Tasks

### Your Markdown File With Checkboxes

```markdown
# Operation Granny Files - Mission 10

Genealogy research and multimedia storytelling project.

## Current Tasks

- [ ] Digitize old family photos from storage box
- [ ] Research Lund family immigration records
- [ ] Interview Aunt Martha about 1950s stories
- [x] Organize existing documents by date

## Waiting For

- [ ] DNA test results from ancestry.com
```

### After First Sync

```markdown
---
tracker_id: 5
project_status: active
priority: 3
momentum_score: 0.0
last_synced: 2026-01-22T15:35:00Z
---

# Operation Granny Files - Mission 10

Genealogy research and multimedia storytelling project.

## Current Tasks

- [ ] Digitize old family photos from storage box <!-- tracker:task:a1b2c3d4 -->
- [ ] Research Lund family immigration records <!-- tracker:task:e5f6g7h8 -->
- [ ] Interview Aunt Martha about 1950s stories <!-- tracker:task:i9j0k1l2 -->
- [x] Organized existing documents by date <!-- tracker:task:m3n4o5p6 -->

## Waiting For

- [ ] DNA test results from ancestry.com <!-- tracker:task:q7r8s9t0:waiting -->
```

**What was added:**
- Frontmatter with `tracker_id` to link to database
- HTML comment markers on each task (invisible in most markdown viewers)
- The `:waiting` suffix on the "Waiting For" task

**Now in the UI:**
- Project appears in your projects list
- 4 tasks created (3 pending, 1 completed)
- 1 task marked as "waiting_for" type
- You can mark tasks complete in UI → checkboxes update in file

---

## 🎯 Example 3: Advanced - With Metadata

### Power User Version

If you want more control, add frontmatter manually:

```markdown
---
tracker_id: 10
project_status: active
priority: 1
target_completion_date: 2026-03-15
area: Writing Projects
momentum_score: 0.82
phases:
  - name: Research
    status: completed
    order: 1
  - name: First Draft
    status: active
    order: 2
  - name: Revision
    status: pending
    order: 3
---

# Guardians of the Ley Lines - Phase IV

Fantasy series reboot working with editor Melanie Jarvis.

## Phase 2: First Draft

### Next Actions
- [ ] Revise chapter 1 based on feedback <!-- tracker:task:abc123 -->
  - Context: creative
  - Energy: high
  - Estimated: 120 minutes

- [ ] Schedule check-in with Melanie <!-- tracker:task:def456 -->
  - Context: administrative
  - Energy: low
  - Estimated: 10 minutes

### Completed
- [x] Complete Phase 1 manuscript <!-- tracker:task:ghi789 -->
- [x] Send to editor <!-- tracker:task:jkl012 -->
```

**Supported metadata:**
- `tracker_id` - Links to database (assigned automatically)
- `project_status` - active, completed, stalled, archived, someday_maybe
- `priority` - 1 (critical) to 5 (very low)
- `target_completion_date` - YYYY-MM-DD
- `area` - Area name (creates if doesn't exist)
- `momentum_score` - 0.0 to 1.0 (calculated automatically)
- `phases` - Project phases with name, status, order

**Task metadata** (in markdown content):
The sync engine doesn't parse inline metadata yet, but tasks are tracked by their markers.

---

## 🔄 How Bidirectional Sync Works

### Scenario 1: You Edit in UI

1. You complete a task in the web UI
2. Task status changes to "completed" in database
3. **Automatic sync to file:** Checkbox changes from `- [ ]` to `- [x]`
4. File's `last_synced` timestamp updates

### Scenario 2: You Edit the File

1. You check off a task in your markdown editor
2. File's modification time changes
3. **Next sync:** File scanner detects change
4. Task marked as completed in database
5. Frontend automatically shows updated status

### Scenario 3: Both Changed (Conflict!)

1. You complete task in UI (database updated)
2. **Before sync**, you also edit the file externally
3. Next sync detects conflict (both changed since last sync)
4. Sync engine marks file as "conflict" status
5. You must manually resolve:
   ```bash
   # Keep file version (file wins)
   curl -X POST http://localhost:8000/api/v1/sync/resolve/5?use_file=true

   # Keep database version (database wins)
   curl -X POST http://localhost:8000/api/v1/sync/resolve/5?use_file=false
   ```

---

## 📋 What Files Are Recognized?

### ✅ Will Be Synced

**Files ending in `.md` in watched directories:**
```
10_Projects/01_Active/01.01_My_Project/README.md
10_Projects/01_Active/01.02_Another/Project.md
20_Areas/20.05_AI_Systems/Notes.md
```

**Any markdown file with:**
- A title (from `# Heading` or frontmatter `title:`)
- Optionally: task checkboxes
- Optionally: existing `tracker_id` in frontmatter

### ❌ Will Be Ignored

**Non-markdown files:**
```
10_Projects/Budget.xlsx
10_Projects/Photo.jpg
```

**Files outside watched directories:**
```
30_Resources/Reference.md  (not in 10_Projects or 20_Areas)
```

**Markdown without titles:**
```markdown
Some notes here but no # heading
and no title: in frontmatter
```

---

## 🚀 Setting Up Sync

### Step 1: Configure .env

Edit `backend/.env`:

```env
# Your Second Brain location
SECOND_BRAIN_ROOT=G:/My Drive/999_SECOND_BRAIN

# Which folders to watch (comma-separated)
WATCH_DIRECTORIES=10_Projects,20_Areas

# How to handle conflicts
CONFLICT_STRATEGY=prompt  # or: file_wins, db_wins
```

### Step 2: Initial Sync

**Scan all files:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/scan" -Method POST
```

**Or via browser API docs:**
1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/sync/scan`
3. Click "Try it out" → "Execute"

### Step 3: Check Results

**View in UI:**
- Refresh http://localhost:5173
- Your markdown projects now appear!

**Check sync status:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/status" -Method GET
```

### Step 4: Keep Syncing

**Manual sync (when you edit files):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/scan" -Method POST
```

**Auto-sync (optional):**
Enable file watcher in `app/main.py` to auto-sync on file changes.

---

## 💡 Best Practices

### 1. Start Simple
Begin with one project file, sync it, verify it works before syncing all files.

### 2. Backup First
Make a backup of your Second Brain before first sync:
```powershell
Copy-Item -Recurse "G:/My Drive/999_SECOND_BRAIN" "G:/My Drive/999_SECOND_BRAIN_BACKUP"
```

### 3. Use Frontmatter Minimally
The sync engine adds what's needed. You can manually add more, but it's optional.

### 4. Don't Delete Markers
Keep the `<!-- tracker:task:... -->` comments. They're invisible in most viewers but critical for sync.

### 5. Handle Conflicts Promptly
Check for conflicts regularly:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/sync/conflicts" -Method GET
```

### 6. One Source of Truth
Pick your preferred workflow:
- **Edit mostly in UI** → Sync occasionally to update files
- **Edit mostly in markdown** → Sync frequently to update database
- **Mix of both** → Sync before and after each session

---

## 🔍 Troubleshooting

### "File not synced"

**Check:**
1. Is file in a watched directory? (`10_Projects` or `20_Areas`)
2. Does file have a title (`# Heading`)?
3. Is file actually markdown (`.md` extension)?

### "Conflict detected"

**Solution:**
Both file and database changed. Manually resolve:
```bash
# See conflicts
GET /api/v1/sync/conflicts

# Resolve (choose file or database version)
POST /api/v1/sync/resolve/{sync_id}?use_file=true
```

### "Tasks not syncing"

**Check:**
1. Are checkboxes in correct format? `- [ ] Title`
2. Do tasks have markers? (added automatically on first sync)
3. Are tasks actually changing? (same checked state won't sync)

---

## 📊 Summary

### What Gets Synced

| Item | File → Database | Database → File |
|------|----------------|-----------------|
| Project title | ✅ From `# Heading` | ✅ Updates heading |
| Project description | ✅ From content | ✅ Updates content |
| Project status | ✅ From frontmatter | ✅ Updates frontmatter |
| Priority | ✅ From frontmatter | ✅ Updates frontmatter |
| Tasks | ✅ From `- [ ]` checkboxes | ✅ Updates checkboxes |
| Task completion | ✅ From `[x]` vs `[ ]` | ✅ Updates checked state |
| Momentum score | ❌ Calculated only | ✅ Updates frontmatter |

### Current Limitations

- ⚠️ Task metadata (context, energy) not parsed from markdown (use UI to set)
- ⚠️ Subtasks (nested checkboxes) not fully supported yet
- ⚠️ Task descriptions must be in database (not parsed from markdown)
- ⚠️ No real-time sync (must manually trigger or enable file watcher)

### Future Enhancements

- 🔮 Parse task metadata from markdown comments
- 🔮 Support nested subtasks
- 🔮 Real-time WebSocket sync
- 🔮 Conflict resolution UI
- 🔮 Sync history and undo

---

**Ready to sync?** Start with one test file and see how it works! 🚀
