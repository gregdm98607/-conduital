# Conduital — Backend Reference

Intelligent momentum-based project management with markdown file sync.

**→ For installation, dev setup, and common commands, see the [root README](../README.md).** This document covers backend-specific architecture: database models, module system, and directory layout.

---

## Directory Layout

```
backend/
├── alembic/              # Database migrations (versions/, env.py)
├── app/
│   ├── api/              # FastAPI route handlers
│   ├── core/             # Config, database, logging
│   ├── models/           # SQLAlchemy models
│   ├── modules/          # Module system (memory_layer, ai_context, ...)
│   ├── schemas/          # Pydantic schemas (request/response validation)
│   ├── services/         # Business logic
│   ├── storage/          # Pluggable storage providers (StorageProvider ABC)
│   ├── sync/             # Markdown parsing, entity handlers
│   └── main.py           # FastAPI application entry point
├── scripts/              # Utility scripts (see scripts/README.md)
├── tests/                # Pytest test suite
├── alembic.ini
├── pyproject.toml
└── run.py                # Single-process launcher (used by packaged exe)
```

---

## Database Models

### Core Models

- **Project** — Multi-step outcomes with clear endpoints
- **Task** — Individual action items (next actions)
- **Area** — Areas of Responsibility (ongoing spheres of activity)
- **Goal** — 1–3 year objectives
- **Vision** — 3–5 year vision and life purpose

### Supporting Models

- **ProjectPhase** — Stages in multi-phase projects
- **PhaseTemplate** — Reusable phase definitions
- **Context** — Contexts for organizing tasks (`@home`, `@computer`, etc.)
- **ActivityLog** — Change tracking for momentum calculation
- **SyncState** — File synchronization status
- **InboxItem** — Inbox for quick capture

Models live in [`app/models/`](app/models). See [`alembic/versions/`](alembic/versions) for schema history.

---

## Module System

Modules are loaded based on `COMMERCIAL_MODE` (or explicit `ENABLED_MODULES`). Full architecture in [`MODULE_SYSTEM.md`](MODULE_SYSTEM.md).

| Mode | Modules |
|------|---------|
| `basic` | core, projects |
| `gtd` | core, projects, gtd_inbox |
| `proactive_assistant` | core, projects, memory_layer, ai_context |
| `full` (default) | all modules |

---

## Related

- [`MODULE_SYSTEM.md`](MODULE_SYSTEM.md) — Module architecture
- [`DISCOVERY_GUIDE.md`](DISCOVERY_GUIDE.md) — Auto-discovery workflow
- [`scripts/README.md`](scripts/README.md) — Utility scripts
- [`../docs/storage-providers.md`](../docs/storage-providers.md) — Storage provider design
