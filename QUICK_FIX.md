# Quick Fix for CORS and 500 Error

## Problem Summary

You're seeing two errors:
1. **CORS Error**: "Access-Control-Allow-Origin header is not present"
2. **500 Internal Server Error**: Backend crashing when accessing projects

## Root Cause

The backend server needs Python dependencies installed and the database needs to be initialized.

## Solution

Follow these steps in order:

### Step 1: Install Backend Dependencies

Choose **ONE** of these methods:

#### Method A: Using Poetry (Recommended)
```bash
# Open PowerShell or CMD
cd C:\Dev\project-tracker\backend

# Install Poetry if not already installed
pip install poetry

# Install dependencies
poetry install

# This should take 1-2 minutes
```

#### Method B: Using pip + venv
```bash
cd C:\Dev\project-tracker\backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Method C: Quick Install (no venv)
```bash
cd C:\Dev\project-tracker\backend

# Install minimum packages
pip install fastapi uvicorn[standard] sqlalchemy pydantic python-dotenv
```

### Step 2: Start the Backend Server

```bash
# Still in backend directory

# With Poetry:
poetry run uvicorn app.main:app --reload

# OR with pip/venv:
python -m uvicorn app.main:app --reload
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Project Tracker v0.1.0 started
📊 Database: C:\Users\YourName\.project-tracker\tracker.db
📁 Second Brain: G:/My Drive/999_SECOND_BRAIN
INFO:     Application startup complete.
```

### Step 3: Verify Backend is Working

Open a browser and go to: http://localhost:8000/docs

You should see the **FastAPI Swagger UI** with all API endpoints listed.

### Step 4: Test the API

In the Swagger UI:
1. Find the **GET /api/v1/projects** endpoint
2. Click "Try it out"
3. Click "Execute"
4. You should see a response (might be empty list `[]` if no projects yet)

### Step 5: Start Frontend

Open a **NEW** terminal/CMD window:

```bash
cd C:\Dev\project-tracker\frontend

# Install dependencies if not already done
npm install

# Start dev server
npm run dev
```

**You should see:**
```
  VITE v7.3.1  ready in 500 ms

  ➜  Local:   http://localhost:5173/
```

### Step 6: Test the Application

1. Open http://localhost:5173 in your browser
2. You should see the Projects page
3. Click "New Project" to create a project
4. Fill in the form and click "Create Project"
5. The project should appear in the list
6. Click "View Details" - this should now work!

## What I Fixed

I updated the backend to **automatically initialize the database** on startup. The file `backend/app/main.py` now includes:

```python
# Initialize database tables if they don't exist
from app.core.database import init_db
init_db()
```

This ensures the database tables are created before the server starts accepting requests.

## Troubleshooting

### Backend won't start - "No module named uvicorn"
- You didn't install dependencies. Go back to Step 1.

### Backend starts but shows errors about database
- The database should auto-initialize now
- If still having issues, manually run:
  ```bash
  cd backend
  poetry run python init_db.py
  # OR
  python init_db.py
  ```

### Still getting CORS errors
- Make sure backend is running on port 8000
- Make sure frontend is running on port 5173
- Check backend terminal for errors
- Restart both servers

### 500 Error persists
- Check backend terminal for detailed error
- Make sure database initialized successfully
- Try creating a project first via the API docs at http://localhost:8000/docs

### Frontend shows "Network Error"
- Backend is not running - start it!
- Wrong port - backend should be on 8000
- Check if firewall is blocking connections

## Still Need Help?

1. **Check backend terminal** - Copy any error messages
2. **Check browser console** - Look for detailed errors
3. **Check database exists**: Look for file at:
   - Windows: `C:\Users\YourName\.project-tracker\tracker.db`
4. **Test API directly**: http://localhost:8000/docs

## Quick Test Script

Save this as `test_api.py` in the backend folder:

```python
import requests

# Test if backend is running
try:
    response = requests.get("http://localhost:8000/health")
    print(f"✅ Backend is running: {response.json()}")
except:
    print("❌ Backend is not running!")
    exit(1)

# Test projects endpoint
try:
    response = requests.get("http://localhost:8000/api/v1/projects")
    print(f"✅ Projects endpoint works: {response.json()}")
except Exception as e:
    print(f"❌ Projects endpoint failed: {e}")
```

Run with:
```bash
cd backend
python test_api.py
```

---

*Once both servers are running properly, all the create/edit forms should work perfectly!*
