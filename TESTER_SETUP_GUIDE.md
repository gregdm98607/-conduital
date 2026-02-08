# Project Tracker R1 - Tester Setup Guide

**Release:** R1 (User Testing)
**Date:** February 2026
**Status:** Pre-release testing

---

## Overview

Project Tracker is a GTD/MYN-inspired productivity system with Second Brain integration. This guide will help you set up the application for testing.

### What's Included in R1

- Project and task management
- Areas, Goals, and Visions tracking
- Momentum scoring and stalled project detection
- MYN urgency zones (Critical Now, Opportunity Now, Over the Horizon)
- Second Brain folder sync (Google Drive compatible)
- Google OAuth authentication
- Data export/backup (JSON and SQLite)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| Git | Any recent | Clone repository |

### Optional (for full features)

- Google Cloud Console account (for OAuth)
- Second Brain folder structure (PARA-organized)

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project-tracker
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Or with Poetry:
poetry install

# Copy environment template
cp .env.example .env
```

### 3. Configure Environment

Edit `backend/.env` with your settings:

```ini
# Minimum required settings
DEBUG=true
COMMERCIAL_MODE=basic

# Optional: Second Brain path (for sync features)
# SECOND_BRAIN_ROOT=/path/to/your/second-brain

# Optional: Google OAuth (see Authentication section)
# AUTH_ENABLED=true
# GOOGLE_CLIENT_ID=your-client-id
# GOOGLE_CLIENT_SECRET=your-client-secret
```

### 4. Initialize Database

```bash
cd backend

# Run database migrations
alembic upgrade head
```

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template (if exists)
# cp .env.example .env
```

### 6. Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # or source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 7. Access the Application

Open your browser to: **http://localhost:5173**

---

## Authentication Setup (Optional)

For Google OAuth authentication:

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable "Google+ API" or "Google People API"

### 2. Configure OAuth Consent Screen

1. Go to APIs & Services > OAuth consent screen
2. Select "External" user type
3. Fill in required fields (app name, support email)
4. Add scopes: `openid`, `email`, `profile`

### 3. Create OAuth Credentials

1. Go to APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application"
4. Add authorized redirect URI: `http://localhost:8000/api/v1/auth/google/callback`
5. Copy the Client ID and Client Secret

### 4. Update Environment

```ini
AUTH_ENABLED=true
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

---

## Testing Areas

Please focus testing on these areas:

### Core Functionality
- [ ] Create, edit, delete projects
- [ ] Create, edit, complete tasks
- [ ] Assign tasks to projects
- [ ] View dashboard with momentum scores

### Navigation & Views
- [ ] Dashboard loads correctly
- [ ] Projects list view works
- [ ] Areas, Goals, Visions pages work
- [ ] Detail views for each entity type

### Second Brain Sync (if configured)
- [ ] Projects sync from markdown files
- [ ] Areas auto-discovered
- [ ] Changes reflect in app after file edits

### Authentication (if configured)
- [ ] Google login works
- [ ] Session persists after browser close
- [ ] Logout works correctly

### Data Export
- [ ] JSON export downloads correctly (via API: GET http://localhost:8000/api/v1/export/json)
- [ ] SQLite backup downloads (via API: GET http://localhost:8000/api/v1/export/backup)

---

## Reporting Issues

When reporting issues, please include:

1. **Steps to reproduce** - What exactly did you do?
2. **Expected behavior** - What should have happened?
3. **Actual behavior** - What actually happened?
4. **Screenshots** - If applicable
5. **Browser console errors** - Press F12, go to Console tab
6. **Backend logs** - Check the terminal running uvicorn

### Issue Template

```
**Summary:** [Brief description]

**Steps to Reproduce:**
1.
2.
3.

**Expected:** [What should happen]

**Actual:** [What happened instead]

**Environment:**
- OS: [Windows 10/11, macOS, Linux]
- Browser: [Chrome, Firefox, Edge]
- Python version: [3.11.x]
- Node version: [18.x]

**Screenshots/Logs:**
[Attach if relevant]
```

---

## Known Limitations

### R1 Scope
- Single-user only (no multi-user/teams)
- No AI features enabled in basic mode
- Export UI not in frontend (API-only)
- List view design not standardized

### Technical Notes
- SQLite database (not for high-concurrency)
- File watcher disabled by default
- Some legacy enum values in demo data

---

## Troubleshooting

### Backend won't start
```
ModuleNotFoundError: No module named 'app'
```
**Fix:** Make sure you're in the `backend` directory and venv is activated.

### Database migration fails
```
alembic.util.exc.CommandError: Can't locate revision
```
**Fix:** Delete `backend/tracker.db` and re-run `alembic upgrade head`.

### Frontend shows blank page
**Fix:** Check browser console (F12) for errors. Ensure backend is running.

### Google OAuth redirect fails
**Fix:** Verify redirect URI in Google Console matches exactly:
`http://localhost:8000/api/v1/auth/google/callback`

---

## Contact

For urgent issues during testing, contact the development team.

Thank you for helping test Project Tracker R1!
