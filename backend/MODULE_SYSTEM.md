# Module System Documentation

## Overview

Conduital uses a modular architecture that enables commercial feature flags and flexible deployment configurations. Each module encapsulates related functionality (models, routes, services) and can be enabled or disabled via configuration.

## Commercial Configurations

Four pre-configured commercial modes are available:

| Mode | Modules Enabled | Use Case |
|------|-----------------|----------|
| `basic` | core, projects | Basic project management |
| `gtd` | core, projects, gtd_inbox | Full GTD workflow |
| `proactive_assistant` | core, projects, memory_layer, ai_context | AI-powered context management |
| `full` | All modules | Complete feature set |

### Configuration

Set the commercial mode in your `.env` file:

```env
# Use a preset
COMMERCIAL_MODE=gtd

# Or specify modules directly (overrides COMMERCIAL_MODE)
ENABLED_MODULES=["core", "projects", "memory_layer"]
```

## Module Architecture

### Module Base Class

All modules inherit from `ModuleBase`:

```python
from app.modules.base import ModuleBase, ModuleInfo, ModuleCategory

class MyModule(ModuleBase):
    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="my_module",
            display_name="My Module",
            description="Does something useful",
            category=ModuleCategory.FEATURE,
            version="1.0.0",
            dependencies=["core"],  # Required modules
        )

    @property
    def router(self) -> Optional[APIRouter]:
        from app.modules.my_module.routes import router
        return router

    async def initialize(self, app_context: dict) -> None:
        # Called on startup
        pass

    async def shutdown(self) -> None:
        # Called on shutdown
        pass
```

### Module Categories

- **CORE**: Always enabled, fundamental functionality
- **FEATURE**: Optional feature modules
- **INTEGRATION**: External integrations (AI, sync, etc.)

## Available Modules

### Core Module (`core`)

**Category:** CORE
**Dependencies:** None
**Always Enabled:** Yes

Provides fundamental functionality:
- User authentication (when AUTH_ENABLED)
- Areas for organizational grouping
- Contexts for GTD filtering
- Goals and Visions (GTD horizons)

### Projects Module (`projects`)

**Category:** CORE
**Dependencies:** core
**Always Enabled:** Yes

Provides project and task management:
- Project CRUD with phases
- Task management with GTD attributes
- Next action prioritization
- File sync with Second Brain
- Momentum tracking
- Intelligence features (stalled detection, AI suggestions)

### GTD Inbox Module (`gtd_inbox`)

**Category:** FEATURE
**Dependencies:** core, projects
**Enabled In:** gtd, full

Provides GTD workflow features:
- Inbox capture and processing
- Weekly review automation
- Waiting-for tracking
- Someday/Maybe lists

**Endpoints:**
- `GET /api/v1/gtd/inbox` - List inbox items
- `POST /api/v1/gtd/inbox` - Capture item
- `GET /api/v1/gtd/weekly-review` - Get review data
- `POST /api/v1/gtd/weekly-review/complete` - Mark review complete
- `GET /api/v1/gtd/waiting-for` - List waiting-for items
- `GET /api/v1/gtd/someday-maybe` - List someday/maybe items

### Memory Layer Module (`memory_layer`)

**Category:** FEATURE
**Dependencies:** core, projects
**Enabled In:** proactive_assistant, full

Provides persistent memory for AI assistants:
- Memory objects with priority scores (0-100)
- Namespace-based organization
- Effective date management
- Priority-based hydration
- Import/export for migration

**Endpoints:**
- `GET /api/v1/memory/objects` - List memory objects
- `POST /api/v1/memory/objects` - Create object
- `GET /api/v1/memory/objects/{id}` - Get object
- `PATCH /api/v1/memory/objects/{id}` - Update object
- `DELETE /api/v1/memory/objects/{id}` - Delete object
- `GET /api/v1/memory/namespaces` - List namespaces
- `POST /api/v1/memory/namespaces` - Create namespace
- `POST /api/v1/memory/hydrate` - Hydrate context
- `GET /api/v1/memory/export` - Export all memory
- `POST /api/v1/memory/import` - Import memory

### AI Context Module (`ai_context`)

**Category:** INTEGRATION
**Dependencies:** core, projects
**Optional:** memory_layer
**Enabled In:** proactive_assistant, full

Provides AI-specific context features:
- Context aggregation from multiple sources
- Macro execution (Good Morning Board, etc.)
- Persona-based routing
- Project-memory integration

**Endpoints:**
- `POST /api/v1/ai/context` - Get aggregated context
- `POST /api/v1/ai/macros/{name}` - Execute macro (gmb, wrap_up, weekly_review)
- `GET /api/v1/ai/personas` - List personas
- `GET /api/v1/ai/personas/{name}` - Get persona config

## Creating a New Module

1. Create module directory:
```
backend/app/modules/my_module/
├── __init__.py
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas
├── services.py    # Business logic
└── routes.py      # API endpoints
```

2. Implement the module class in `__init__.py`:
```python
from app.modules.base import ModuleBase, ModuleInfo, ModuleCategory

class MyModule(ModuleBase):
    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="my_module",
            display_name="My Module",
            description="Description here",
            category=ModuleCategory.FEATURE,
            dependencies=["core", "projects"],
        )

    @property
    def router(self):
        from app.modules.my_module.routes import router
        return router

    @property
    def prefix(self) -> str:
        return "my-module"  # Routes under /api/v1/my-module/
```

3. Register in `registry.py`:
```python
def register_all_modules() -> None:
    # ...existing modules...

    try:
        from app.modules.my_module import MyModule
        registry.register(MyModule())
    except ImportError:
        pass
```

4. Add to commercial presets if needed:
```python
COMMERCIAL_PRESETS = {
    # ...
    "my_preset": ["core", "projects", "my_module"],
}
```

5. Create Alembic migration for any new models.

## API Introspection

The `/modules` endpoint shows available and enabled modules:

```bash
curl http://localhost:8000/modules
```

Response:
```json
{
  "commercial_mode": "gtd",
  "enabled_modules": ["core", "projects", "gtd_inbox"],
  "available_modules": [
    {
      "name": "core",
      "display_name": "Core",
      "description": "...",
      "category": "core",
      "enabled": true,
      "dependencies": []
    },
    // ...
  ]
}
```

## Database Migrations

Each module that adds models should include an Alembic migration:

```bash
cd backend
poetry run alembic revision --autogenerate -m "Add my_module tables"
```

## Best Practices

1. **Declare Dependencies**: Always list required modules in `dependencies`
2. **Check Module Status**: Use `is_module_enabled("module_name")` in services
3. **Backwards Compatibility**: Core routes remain mounted for existing clients
4. **Graceful Degradation**: Handle missing optional dependencies
5. **Feature Gating**: Return 403 with feature name for disabled modules

## Checking Module Status in Code

```python
from app.modules import is_module_enabled

if is_module_enabled("memory_layer"):
    # Include memory context
    pass

# Or from settings
from app.core.config import settings

if settings.is_module_enabled("ai_context"):
    # Enable AI features
    pass
```
