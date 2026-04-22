# Conduital

**The Conduit for Intelligent Momentum**

A momentum-based productivity system with markdown file sync, built with FastAPI and React + TypeScript. Conduital helps you maintain project momentum, surface next actions intelligently, and sync seamlessly with your note folders.

---

## Features

- **Momentum Scoring** — 0.0-1.0 score per project based on activity, completion rate, and next action availability
- **Stalled Project Detection** — Automatic flagging of projects with 14+ days inactivity
- **Next Actions Prioritization** — MYN urgency zones (Critical Now, Opportunity Now, Over the Horizon)
- **Markdown File Sync** — Bidirectional sync with YAML frontmatter in your note folders
- **AI Integration** — Optional Claude / OpenAI / Google AI for unstuck suggestions and analysis
- **Module System** — Enable only what you need: basic, GTD inbox, memory layer, AI context
- **Data Export** — JSON export and SQLite backup from the Settings page
- **Dark Mode** — Full dark theme support

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite, Alembic |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| AI | Anthropic Claude, OpenAI, Google (optional, bring your own key) |

---

## Quick Start (End Users)

The packaged Windows installer is the fastest path — no Python or Node.js required.

1. Download `ConduitalSetup-<version>.exe` from [Gumroad](https://gregdm.gumroad.com/l/conduital).
2. Run the installer. A browser opens to the setup wizard.
3. Complete the 4-step wizard (welcome → sync folder → API key → confirm).

Data lives in `%LOCALAPPDATA%\Conduital\`.

---

## Developer Setup

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (only needed for frontend dev; production bundle ships pre-built)
- Git

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate              # Windows
# source venv/bin/activate          # macOS / Linux

pip install -r requirements.txt     # or: poetry install
cp .env.example .env                # edit as needed — see Configuration below
alembic upgrade head                # initialize / migrate database
python run.py                       # starts server + opens browser at http://localhost:52140
```

For development with auto-reload:

```bash
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (development only)

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173
```

The frontend `.env` defaults to `VITE_API_BASE_URL=http://localhost:8000/api/v1`. Edit if your backend runs elsewhere.

For production, run `npm run build` — FastAPI then serves the bundle directly; Node.js is not required at runtime.

---

## Configuration

Key environment variables (full list in [`backend/.env.example`](backend/.env.example)):

```env
# Sync folder (optional)
SECOND_BRAIN_ROOT=/path/to/your/notes

# Storage mode (optional — default: "legacy")
STORAGE_MODE=storage_first          # or "legacy"
STORAGE_PROVIDER=local_folder

# AI features (optional — all other features work without a key)
AI_PROVIDER=anthropic               # anthropic | openai | google | mistral | groq | ollama | ...
ANTHROPIC_API_KEY=your_key_here
AI_FEATURES_ENABLED=true

# Module configuration
COMMERCIAL_MODE=full                # basic | gtd | proactive_assistant | full
```

**Windows paths:** use forward slashes (`D:/notes`) or escaped backslashes (`D:\\notes`).

---

## Common Commands

```bash
# Backend tests
cd backend
venv\Scripts\python.exe -m pytest tests/ -x -q

# Backend lint / format / type-check
ruff check .
black .
mypy app

# Frontend build + lint
cd frontend
npm run build
npm run lint
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"    # generate from model changes
alembic upgrade head                                 # apply pending migrations
alembic downgrade -1                                 # roll back one revision
alembic current                                      # show current revision
```

---

## Project Structure

```
conduital/
├── backend/
│   ├── app/
│   │   ├── api/           # REST API endpoints
│   │   ├── core/          # Config, database, logging
│   │   ├── models/        # SQLAlchemy models
│   │   ├── modules/       # Module system (memory layer, etc.)
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic (incl. StorageService)
│   │   ├── storage/       # Pluggable storage providers
│   │   └── sync/          # Markdown parsing, entity handlers
│   ├── alembic/           # Database migrations
│   ├── scripts/           # Utility scripts (see backend/scripts/README.md)
│   ├── tests/             # Backend test suite
│   └── run.py             # Single-process launcher
├── docs/                  # Architecture docs
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── services/
├── installer/             # Inno Setup config + build output
└── README.md              # (this file — canonical setup doc)
```

---

## Data Storage

Conduital supports pluggable storage backends via a **StorageProvider** abstraction. Your data can live in markdown files, with SQLite as a fast query cache.

| Mode | Description |
|------|-------------|
| `legacy` (default) | SQLite is the source of truth. Markdown sync is optional. |
| `storage_first` | Markdown files are the source of truth. SQLite is rebuilt on startup. |

In `storage_first` mode, project files are standard YAML-frontmatter markdown — fully compatible with **Obsidian**, Logseq, and other PKM tools. External edits are auto-detected and synced.

See [`docs/storage-providers.md`](docs/storage-providers.md) for the architecture guide and how to add new providers.

---

## Related Documentation

- [`backend/MODULE_SYSTEM.md`](backend/MODULE_SYSTEM.md) — Module architecture
- [`backend/DISCOVERY_GUIDE.md`](backend/DISCOVERY_GUIDE.md) — Auto-discovery workflow
- [`backend/scripts/README.md`](backend/scripts/README.md) — Utility scripts reference
- [`frontend/FRONTEND_IMPLEMENTATION_GUIDE.md`](frontend/FRONTEND_IMPLEMENTATION_GUIDE.md) — Frontend patterns
- [`docs/storage-providers.md`](docs/storage-providers.md) — Storage provider architecture
- [`distribution-checklist.md`](distribution-checklist.md) — Pre-release gates
- [`backlog.md`](backlog.md) — Release-based backlog

---

## Version

Current: **1.2.0** (beta)

## License

Proprietary. See [LICENSE](LICENSE) for details.
Third-party licenses: [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt)
