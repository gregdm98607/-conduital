# Project Tracker Setup Guide

## Prerequisites

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** - [Download here](https://nodejs.org/)
- **Git** (optional) - [Download here](https://git-scm.com/)

## Backend Setup

The backend uses FastAPI and can be set up with either Poetry or pip.

### Option A: Using Poetry (Recommended)

Poetry manages dependencies and virtual environments automatically.

```bash
# 1. Install Poetry
pip install poetry

# 2. Navigate to backend directory
cd C:\Dev\project-tracker\backend

# 3. Install dependencies
poetry install

# 4. Verify installation
poetry run python --version
poetry run uvicorn --version

# 5. Run the server
poetry run uvicorn app.main:app --reload
```

### Option B: Using pip + Virtual Environment

```bash
# 1. Navigate to backend directory
cd C:\Dev\project-tracker\backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
python -m uvicorn --version

# 6. Run the server
python -m uvicorn app.main:app --reload
```

### Option C: Quick Install (No Virtual Environment)

**Warning:** This installs packages globally, which may cause conflicts.

```bash
cd C:\Dev\project-tracker\backend

# Install minimum required packages
pip install fastapi uvicorn[standard] sqlalchemy pydantic python-dotenv

# Run the server
python -m uvicorn app.main:app --reload
```

### Backend Verification

Once the server starts, you should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Visit these URLs to verify:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health (if endpoint exists)

## Frontend Setup

The frontend uses React with Vite.

```bash
# 1. Navigate to frontend directory
cd C:\Dev\project-tracker\frontend

# 2. Install dependencies
npm install

# 3. Verify installation
npm run build --dry-run

# 4. Run development server
npm run dev
```

### Frontend Verification

Once the server starts, you should see:

```
  VITE v7.3.1  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

Visit http://localhost:5173 in your browser.

## Database Setup

The backend uses SQLite by default (no setup required).

### Initialize Database

```bash
cd C:\Dev\project-tracker\backend

# Using Poetry
poetry run python -m app.database.init_db

# Using pip/venv
python -m app.database.init_db
```

If no init script exists, the database will be created automatically on first run.

## Quick Start (Both Servers)

### Method 1: Batch Script (Windows)

Double-click `start-dev.bat` in the project root, or run:

```bash
cd C:\Dev\project-tracker
start-dev.bat
```

### Method 2: Manual (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd C:\Dev\project-tracker\backend

# With Poetry
poetry run uvicorn app.main:app --reload

# With pip/venv
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd C:\Dev\project-tracker\frontend
npm run dev
```

## Common Issues

### Issue 1: "No module named uvicorn"

**Solution:** Dependencies not installed. Run:
```bash
cd backend
poetry install
# OR
pip install -r requirements.txt
```

### Issue 2: "npm: command not found"

**Solution:** Node.js not installed or not in PATH.
- Install Node.js from https://nodejs.org/
- Restart terminal after installation

### Issue 3: "python: command not found"

**Solution:** Python not installed or not in PATH.
- Install Python from https://www.python.org/
- During installation, check "Add Python to PATH"
- Restart terminal after installation

### Issue 4: "Port 8000 already in use"

**Solution:** Another process is using port 8000.
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# OR use a different port
uvicorn app.main:app --reload --port 8001
```

### Issue 5: "CORS error" in browser console

**Solution:** Backend not running or CORS not configured.
- Ensure backend is running on port 8000
- Check `app/main.py` has CORS middleware configured

### Issue 6: Forms not submitting / Modal not closing

**Solution:** Backend endpoints not working.
- Check browser console for API errors
- Verify backend logs for errors
- Test API manually: http://localhost:8000/docs

## Environment Variables

### Backend (.env)

Create `backend/.env` if needed:

```env
# Database
DATABASE_URL=sqlite:///./project_tracker.db

# API
API_V1_PREFIX=/api/v1

# CORS (for development)
CORS_ORIGINS=http://localhost:5173

# Optional: Anthropic API for AI features
ANTHROPIC_API_KEY=your_api_key_here
```

### Frontend (.env)

Create `frontend/.env` if needed:

```env
# API Base URL (only if backend is on different host)
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Development Workflow

1. **Start servers** (use `start-dev.bat` or manual method)
2. **Open browser** to http://localhost:5173
3. **Make changes:**
   - Frontend: Files auto-reload on save
   - Backend: Server auto-restarts on save (with `--reload`)
4. **Test changes** in browser
5. **Check logs** in terminal for errors

## Production Build

### Backend

```bash
cd backend
poetry install --no-dev
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm run build
# Outputs to frontend/dist

# Serve with a static server
npx serve -s dist -p 5173
```

## Project Structure

```
project-tracker/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Database models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI app
│   ├── pyproject.toml    # Poetry config
│   ├── requirements.txt  # Pip dependencies
│   └── project_tracker.db # SQLite database
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── package.json      # NPM config
│   └── vite.config.ts    # Vite config
├── start-dev.bat         # Windows startup script
├── SETUP.md              # This file
└── TROUBLESHOOTING.md    # Debug guide
```

## Testing

### Backend Tests

```bash
cd backend

# Using Poetry
poetry run pytest

# Using pip/venv
pytest
```

### Frontend Tests (if configured)

```bash
cd frontend
npm run test
```

## Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **Vite Docs:** https://vitejs.dev/
- **TanStack Query:** https://tanstack.com/query/latest
- **Tailwind CSS:** https://tailwindcss.com/

## Getting Help

If you encounter issues:

1. Check **TROUBLESHOOTING.md** for common solutions
2. Check browser console (F12) for frontend errors
3. Check backend terminal for server errors
4. Verify both servers are running
5. Test API directly at http://localhost:8000/docs

---

*Last updated: January 22, 2026*
