# Project Tracker

**A GTD + Manage Your Now project management system with Second Brain integration**

Built with FastAPI, SQLAlchemy, and Claude AI to help you maintain project momentum, surface next actions intelligently, and sync seamlessly with your PARA-organized Second Brain.

---

## 🎯 Project Status

### ✅ Phase 1: Database Foundation - COMPLETE

- [x] Project structure created
- [x] 11 SQLAlchemy models implemented
- [x] Database configuration and utilities
- [x] Alembic migrations configured
- [x] Poetry dependency management
- [x] Comprehensive documentation

### ✅ Phase 2: API Layer - COMPLETE

- [x] Pydantic schemas for validation (9 modules)
- [x] CRUD service layer (3 services, 23 methods)
- [x] REST API endpoints (50+ endpoints, 8 routers)
- [x] Smart next action prioritization engine
- [x] API documentation (Swagger/OpenAPI + comprehensive guide)
- [x] Basic test suite
- [ ] WebSocket for real-time updates (future enhancement)

### ✅ Phase 3: Sync Engine - COMPLETE

- [x] File system watcher with debouncing
- [x] Bidirectional sync (DB ↔ Files)
- [x] Conflict detection and resolution
- [x] Markdown parsing with YAML frontmatter
- [x] Markdown generation with task checkboxes
- [x] Unique task markers (HTML comments)
- [x] Batch scanning and sync
- [x] Sync API endpoints (7 endpoints)

### ⏳ Phase 4: Intelligence Layer

- [ ] Momentum calculation algorithm
- [ ] Stalled project detection
- [ ] Next action prioritization
- [ ] AI integration (Claude)
- [ ] Unstuck task generation

### ⏳ Phase 5: Frontend

- [ ] React + TypeScript setup
- [ ] Dashboard view
- [ ] Project/task management
- [ ] Context-based filtering
- [ ] Real-time updates

---

## 📚 Documentation

### Quick Start
- **[Setup Guide](SETUP_GUIDE.md)** - Installation and configuration
- **[Backend README](backend/README.md)** - Development guide

### Technical Documentation
- **[Technical Specification](Project_Tracker_Technical_Spec.md)** - Complete 95-page spec
- **[Database Models Summary](DATABASE_MODELS_SUMMARY.md)** - Model reference

### Architecture
- **[CLAUDE.MD](CLAUDE.md)** - Context for AI assistance

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- Your PARA-organized Second Brain

### Setup

```bash
# 1. Install dependencies
cd backend
poetry install

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings

# 3. Initialize database
poetry run python scripts/init_db.py

# 4. Run development server (when implemented)
poetry run uvicorn app.main:app --reload
```

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- FastAPI (async web framework)
- SQLAlchemy 2.0 (ORM)
- SQLite with WAL mode (database)
- Alembic (migrations)
- Anthropic SDK (AI integration)

**Frontend (Planned):**
- React 18 + TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query
- Socket.IO client

**AI Integration:**
- Claude Sonnet 4.5 via Anthropic API
- Model Context Protocol (MCP) server
- Natural language command processing

### Database Schema

11 core models implementing GTD and PARA methodology:

- **Project** - Multi-step outcomes with momentum tracking
- **Task** - Next actions with context and energy levels
- **Area** - Areas of responsibility
- **Goal** - 1-3 year objectives (GTD Horizon 3)
- **Vision** - 3-5 year vision and purpose (GTD Horizons 4-5)
- **ProjectPhase** - Multi-phase project stages
- **PhaseTemplate** - Reusable phase patterns
- **Context** - GTD contexts (@home, @computer, etc.)
- **ActivityLog** - Change tracking for momentum
- **SyncState** - File synchronization status
- **InboxItem** - Quick capture inbox

---

## 💡 Key Features

### Momentum-First Approach
- **Momentum Score** (0.0-1.0) calculated from:
  - Recent activity (40% weight)
  - Completion rate (30% weight)
  - Next action availability (20% weight)
  - Activity frequency (10% weight)

- **Stalled Detection**: Automatic flagging of projects with 14+ days inactivity
- **Unstuck Tasks**: AI-generated minimal viable actions (5-15 min) to restart stalled projects

### Smart Next Actions
- Context-aware filtering (@creative, @administrative, @deep_work)
- Energy level matching (high, medium, low)
- Time-based filtering (estimated duration)
- Priority-based ordering with momentum weighting

### Bidirectional Sync
- YAML frontmatter in markdown files for metadata
- Task markers for reliable synchronization
- Conflict detection and resolution
- Real-time file watching with debouncing

### GTD Compliant
- All five horizons of focus (Runway → Purpose)
- Capture → Clarify → Organize → Reflect → Engage workflow
- Contexts for organizing next actions
- Waiting For tracking
- Someday/Maybe lists

---

## 📂 Project Structure

```
project-tracker/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/              # API endpoints (coming)
│   │   ├── core/             # ✅ Config & database
│   │   ├── models/           # ✅ SQLAlchemy models (11)
│   │   ├── schemas/          # Pydantic schemas (coming)
│   │   └── services/         # Business logic (coming)
│   ├── scripts/              # ✅ Utility scripts
│   ├── tests/                # Test suite (coming)
│   ├── alembic.ini           # ✅ Alembic config
│   ├── pyproject.toml        # ✅ Poetry dependencies
│   └── README.md             # ✅ Backend docs
├── frontend/                 # React app (coming)
├── SETUP_GUIDE.md           # ✅ Installation guide
├── DATABASE_MODELS_SUMMARY.md  # ✅ Model reference
├── Project_Tracker_Technical_Spec.md  # ✅ Full specification
└── README.md                # ✅ This file
```

---

## 🎯 Design Principles

1. **Momentum-First**: Keep projects moving, identify when they stall
2. **Minimal Friction**: Quick capture, smart prioritization
3. **Context-Aware**: Match work to your current state
4. **File-Based**: Your data lives in markdown files you control
5. **AI-Assisted**: Let Claude help with planning and unsticking
6. **GTD-Aligned**: Trusted system for stress-free productivity

---

## 🔧 Configuration

Key environment variables (see `.env.example`):

```env
# Second Brain Integration
SECOND_BRAIN_ROOT=/path/to/your/second-brain
WATCH_DIRECTORIES=10_Projects,20_Areas

# Momentum Thresholds
MOMENTUM_STALLED_THRESHOLD_DAYS=14
MOMENTUM_AT_RISK_THRESHOLD_DAYS=7

# AI Features (Optional)
ANTHROPIC_API_KEY=your_key_here
AI_FEATURES_ENABLED=true
```

---

## 🚦 Current Implementation Status

### ✅ Completed (Phase 1)

**Database Layer:**
- 11 SQLAlchemy models with full relationships
- TimestampMixin for automatic timestamps
- Computed properties (is_stalled, completion_percentage, etc.)
- Comprehensive indexes for query performance
- Type-safe with Python 3.11+ type hints

**Configuration:**
- Pydantic settings management
- Environment variable loading
- Database URL construction
- Second Brain path configuration

**Migrations:**
- Alembic setup and configuration
- Auto-generation support
- Black formatting integration
- Migration template customization

**Utilities:**
- Activity logging
- File hash calculation
- Get-or-create pattern
- Recent activity queries
- Unique marker generation

**Documentation:**
- 95-page technical specification
- Database models summary
- Setup guide
- Backend README

### 🔄 In Progress

None - Phases 1 & 2 are complete!

### 📋 Next Steps (Phase 3)

1. **File System Watcher**
   - Monitor Second Brain directories
   - Detect file changes
   - Debounce rapid changes

2. **Bidirectional Sync**
   - Parse markdown with YAML frontmatter
   - Sync tasks from checkboxes
   - Write changes back to files
   - Conflict detection

3. **Or Skip to Phase 5: Frontend**
   - React dashboard
   - Interactive UI
   - Real-time updates

---

## 📊 Statistics

### Current Implementation
- **Lines of Code**: ~2,500+
- **Models**: 11
- **Tables**: 12
- **Fields**: 100+
- **Relationships**: 20+
- **Indexes**: 15+
- **Documentation Pages**: 150+

### Estimated Completion
- **Phase 1** (Database): ✅ 100% complete
- **Phase 2** (API): ✅ 100% complete
- **Phase 3** (Sync): ✅ 100% complete
- **Phase 4** (Intelligence): 0%
- **Phase 5** (Frontend): 0%

**Overall Progress**: ~60% of full MVP (3 of 5 phases complete)

---

## 🤝 Integration with Your Second Brain

### File Format

Projects sync with markdown files using YAML frontmatter:

```markdown
---
tracker_id: 42
project_status: active
priority: 2
momentum_score: 0.75
area: 20.05_AI_Systems
---

# Project Title

Project notes and context...

## Next Actions

- [ ] Task 1 <!-- tracker:task:abc123 -->
- [ ] Task 2 <!-- tracker:task:def456 -->
- [x] Completed <!-- tracker:task:ghi789 -->

## Waiting For

- [ ] Feedback from editor <!-- tracker:task:jkl012:waiting -->
```

### Sync Strategy

1. **File → Database**: Watch for file changes, parse and update DB
2. **Database → File**: On task completion, update markdown checkboxes
3. **Conflict Detection**: Compare file hashes, prompt user if both changed
4. **Markers**: HTML comments with unique IDs keep tasks in sync

---

## 🧠 AI Integration (Planned)

### Claude Features
- **Unstuck Task Generation**: Minimal tasks to restart stalled projects
- **Project Health Analysis**: AI assessment of project status
- **Weekly Review**: Automated GTD weekly review prompts
- **Natural Language**: "What should I work on next?"
- **Task Decomposition**: Break large tasks into steps

### MCP Server
- Tools for project/task CRUD
- Next action queries
- Analytics and insights
- Natural language interface

---

## 🎓 Methodology

### Getting Things Done (GTD)
- Capture everything in trusted system
- Clarify: is it actionable?
- Organize by context and priority
- Reflect with regular reviews
- Engage with confidence

### Manage Your Now
- Focus on momentum over perfection
- Minimum viable actions for progress
- Context and energy matching
- Strategic alignment with goals

### PARA Method
- **Projects**: Active outcomes with endpoints
- **Areas**: Ongoing responsibilities
- **Resources**: Reference materials
- **Archives**: Completed/inactive items

---

## 📝 License

Private project for personal use.

---

## 🙏 Acknowledgments

Built using:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database toolkit
- [Alembic](https://alembic.sqlalchemy.org/) - Migration tool
- [Anthropic Claude](https://www.anthropic.com/) - AI assistance
- [GTD](https://gettingthingsdone.com/) - David Allen's methodology
- [PARA](https://fortelabs.com/blog/para/) - Tiago Forte's organization system

---

**Last Updated**: 2026-01-20
**Phase**: 1 - Database Foundation ✅ COMPLETE
**Next**: Phase 2 - API Layer
