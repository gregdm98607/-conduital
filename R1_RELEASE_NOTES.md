# Project Tracker R1 Release Notes

**Version:** R1 (PT Basic)
**Release Date:** February 3, 2026
**Release Type:** User Testing (Non-Commercial)

---

## Overview

R1 is the first user testing release of Project Tracker, a GTD/MYN-inspired productivity system with Second Brain integration. This release focuses on core project and task management functionality.

---

## Features Included

### Core Functionality
- **Project Management** - Create, edit, archive, and delete projects with full CRUD operations
- **Task Management** - Tasks with status, priority, target dates, and project assignment
- **Areas of Responsibility** - PARA-style areas for organizing projects
- **Goals & Visions** - GTD Horizons of Focus (1-3 year goals, 3-5 year visions)
- **Contexts** - GTD-style contexts for filtering tasks by location/tool/energy

### Intelligence Layer
- **Momentum Scoring** - 0.0-1.0 score based on activity, completion rate, and next actions
- **Stalled Project Detection** - Automatic identification of projects inactive for 14+ days
- **Next Actions Prioritization** - Smart sorting of available next actions
- **MYN Urgency Zones** - Critical Now, Opportunity Now, Over the Horizon classification

### Second Brain Integration
- **Folder Sync** - Bidirectional sync with PARA-organized directories
- **Auto-Discovery** - Automatic detection of projects and areas from markdown files
- **YAML Frontmatter** - Metadata extraction from markdown project files
- **Google Drive Compatible** - Works with cloud-synced Second Brain folders

### Authentication
- **Google OAuth** - Optional single sign-on with Google accounts
- **JWT Tokens** - Secure session management with refresh tokens
- **Graceful Degradation** - App works fully without authentication enabled

### Data Portability
- **JSON Export** - Complete data export in versioned JSON format (v1.0.0)
- **SQLite Backup** - Point-in-time database backup download
- **API Endpoints** - Programmatic access to export functionality

### User Interface
- **Dashboard** - Overview with momentum scores and stalled project alerts
- **List & Grid Views** - Multiple viewing options for projects and tasks
- **Responsive Design** - Works on desktop browsers
- **Protected Routes** - Secure navigation when auth is enabled

---

## Technical Specifications

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Database | SQLite (WAL mode) |
| Auth | Google OAuth 2.0, JWT |
| State | TanStack Query |

### Test Coverage
- **169 tests** total
- **154 passing** (91% pass rate)
- **42% code coverage**
- 15 API integration test failures (known test harness issue, not affecting production)

---

## Known Limitations

### Deferred to R2
- **BACKLOG-076**: List View Design Standard (UX consistency across views)
- **DOC-005**: Module System Documentation (user-facing documentation)

### Current Limitations
- **Single-user only** - No multi-user or team features
- **No AI features** - AI modules not enabled in R1 (basic mode)
- **Export UI missing** - Export available via API only, no frontend buttons
- **Desktop only** - Mobile views not optimized

### Technical Notes
- SQLite database (not for high-concurrency use cases)
- File watcher disabled by default
- Some legacy enum values in existing data (`someday_maybe`)

---

## Setup Requirements

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- Git

### Optional
- Google Cloud Console account (for OAuth)
- Second Brain folder (PARA-organized)

### Quick Start
```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

See `TESTER_SETUP_GUIDE.md` for detailed instructions.

---

## API Endpoints (Export)

For data export without frontend UI:

```bash
# Preview export (counts and size estimate)
GET http://localhost:8000/api/v1/export/preview

# Download JSON export
GET http://localhost:8000/api/v1/export/json

# Download SQLite backup
GET http://localhost:8000/api/v1/export/backup
```

---

## Reporting Issues

### Issue Template
```
**Summary:** [Brief description]

**Steps to Reproduce:**
1.
2.
3.

**Expected:** [What should happen]
**Actual:** [What happened]

**Environment:**
- OS:
- Browser:
- Python:
- Node:

**Screenshots/Logs:** [If applicable]
```

### Priority Levels
- **P0 - Critical**: App crashes, data loss, security issue
- **P1 - High**: Feature completely broken, no workaround
- **P2 - Medium**: Feature partially broken, workaround exists
- **P3 - Low**: Minor issue, cosmetic, enhancement request

---

## What's Next (R2 Preview)

R2 will add full GTD workflow support:
- GTD Inbox processing flow
- Someday/Maybe project workflow
- Weekly Review checklist
- Quick capture to project
- Review frequency intelligence

---

## Changelog

### 2026-02-03: R1 User Testing Release
- All R1 Must Have items complete
- Google OAuth authentication
- Data export/backup (JSON + SQLite)
- Migration integrity checks
- Test coverage at 42% (169 tests)
- SQLite migration compatibility fix (batch mode)

### Previous Development
- See `backlog.md` Completed Items section for full history

---

*Thank you for participating in the R1 user testing program!*
