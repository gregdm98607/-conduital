# Quick Start - Google Drive Project Discovery

## 🚀 Get Started in 6 Minutes

### 1. Configure Area Mappings (1 min)

Edit `backend/.env` or `backend/app/core/config.py`:

```python
AREA_PREFIX_MAP = {
    "01": "Literary Projects",
    "10": "Personal Projects"
}
```

### 2. Create Markdown Files (1 min)

Ensure all project folders have markdown files:

```bash
cd backend

# Preview what will be created
poetry run python scripts\create_project_files.py --dry-run

# Create files
poetry run python scripts\create_project_files.py
```

### 3. Run Discovery (1 min)

```bash
poetry run python scripts\discover_projects.py
```

### 4. Start Server (1 min)

```bash
poetry run python -m app.main
```

### 5. Calculate Momentum (30 sec)

```bash
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update
```

### 6. View Projects (30 sec)

Open browser: http://localhost:8000/docs

Or:
```bash
curl http://localhost:8000/api/v1/projects
```

## ✅ Done!

Your 14 projects from Google Drive are now in the tracker.

## 🔄 Enable Auto-Discovery (Optional - Phase 2)

Want new projects to import automatically? Enable auto-discovery:

```bash
# Add to backend/.env
echo "AUTO_DISCOVERY_ENABLED=true" >> .env

# Restart server
poetry run python -m app.main
```

**What this does:**
- Watches `10_Projects/` folder
- Auto-imports new project folders
- Handles folder renames
- No manual discovery needed

**Test it:**
1. Create folder: `10_Projects/01.15 New_Novel/`
2. Watch server console for: `🆕 New project folder detected`
3. Project appears in database automatically!

## 📊 What You Get

- **All projects imported** from `10_Projects/`
- **Areas automatically linked** (01 → Literary, 10 → Personal)
- **Markdown files synced** with tasks
- **Momentum scores** calculated
- **Next actions** prioritized
- **Stalled projects** detected

## 🎯 Next Actions

```bash
# Get your top next actions
curl http://localhost:8000/api/v1/next-actions

# Check stalled projects
curl http://localhost:8000/api/v1/intelligence/stalled

# Start frontend
cd ..\frontend
npm run dev
# Open: http://localhost:5173
```

## 📚 Full Documentation

- **Setup Guide:** `GOOGLE_DRIVE_SETUP.md`
- **Feature Guide:** `backend/DISCOVERY_GUIDE.md`
- **API Docs:** http://localhost:8000/docs

## 🆘 Troubleshooting

**Projects not found?**
```bash
# Check path
echo $env:SECOND_BRAIN_ROOT  # PowerShell
# Should be: /path/to/your/second-brain
```

**Need help?**
- Read `GOOGLE_DRIVE_SETUP.md`
- Check API docs: http://localhost:8000/docs
- Review logs in `backend/logs/`

---

**That's it!** Your Project Tracker is connected to Google Drive. 🎉
