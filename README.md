# Conduital

**The Conduit for Intelligent Momentum**

A momentum-based productivity system with markdown file sync, built with FastAPI and React + TypeScript. Conduital helps you maintain project momentum, surface next actions intelligently, and sync seamlessly with your note folders.

---

## Features

- **Momentum Scoring** -- 0.0-1.0 score per project based on activity, completion rate, and next action availability
- **Stalled Project Detection** -- Automatic flagging of projects with 14+ days inactivity
- **Next Actions Prioritization** -- MYN urgency zones (Critical Now, Opportunity Now, Over the Horizon)
- **Markdown File Sync** -- Bidirectional sync with YAML frontmatter in your note folders
- **AI Integration** -- Optional Claude/OpenAI/Google AI for unstuck suggestions and analysis
- **Module System** -- Enable only what you need: basic, GTD inbox, memory layer, AI context
- **Data Export** -- JSON export and SQLite backup from the Settings page
- **Dark Mode** -- Full dark theme support

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, SQLite, Alembic |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| AI | Anthropic Claude, OpenAI, Google (optional, bring your own key) |

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env       # Edit with your settings
python run.py              # Starts server + opens browser

# Frontend (development)
cd frontend
npm install
npm run dev
```

For production, the frontend is pre-built and served by FastAPI -- no Node.js required at runtime.

## Project Structure

```
conduital/
  backend/
    app/
      api/          # REST API endpoints
      core/         # Config, database, logging
      models/       # SQLAlchemy models
      modules/      # Module system (memory layer, etc.)
      schemas/      # Pydantic schemas
      services/     # Business logic
    alembic/          # Database migrations
    tests/            # Backend test suite
    run.py            # Single-process launcher
  frontend/
    src/
      components/   # React components
      pages/        # Page components
      hooks/        # Custom hooks
      services/     # API client
    index.html
  README.md
```

## Configuration

Key environment variables (see `backend/.env.example` for full list):

```env
# Sync folder (optional)
SECOND_BRAIN_ROOT=/path/to/your/notes

# AI features (optional -- all other features work without a key)
ANTHROPIC_API_KEY=your_key_here
AI_FEATURES_ENABLED=true

# Module configuration
COMMERCIAL_MODE=full  # basic, gtd, proactive_assistant, full
```

## Version

Current: **1.0.0-alpha**

## License

Proprietary. See [LICENSE](LICENSE) for details.
Third-party licenses: [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt)
