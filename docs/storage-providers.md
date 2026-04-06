# Storage Providers — Architecture Guide

Conduital supports pluggable storage backends via the **StorageProvider** abstraction. This guide explains the architecture, the built-in local folder provider, and how to add new providers.

---

## Overview

Conduital separates *where* data lives from *how* it's used. The storage layer handles persistence while SQLAlchemy/SQLite serves as a fast query cache.

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  API Layer   │────▶│  StorageService   │────▶│  Provider   │
│  (FastAPI)   │     │  (write-through)  │     │  (markdown) │
└─────────────┘     └──────────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  SQLite Cache │
                    │  (read-only)  │
                    └──────────────┘
```

### Two Modes

| Mode | Description | Default |
|------|-------------|---------|
| `legacy` | SQLite is the source of truth. Markdown sync is optional. | ✅ Yes |
| `storage_first` | Markdown files are the source of truth. SQLite is a read cache rebuilt on startup. | No |

Set the mode via environment variable:

```env
STORAGE_MODE=storage_first   # or "legacy" (default)
```

---

## StorageProvider ABC

All providers implement the abstract base class in `backend/app/storage/base.py`:

```python
class StorageProvider(ABC):
    def read_entity(self, entity_type: str, entity_id: str) -> dict: ...
    def write_entity(self, entity_type: str, entity_id: str, data: dict) -> str: ...
    def delete_entity(self, entity_type: str, entity_id: str) -> bool: ...
    def list_entities(self, entity_type: str) -> list[dict]: ...
    def exists(self, entity_type: str, entity_id: str) -> bool: ...
    def watch_for_changes(self) -> list[Change]: ...
```

### Entity Types

The provider supports these entity types, each with its own markdown handler:

| Entity Type | Handler Class | Directory | Description |
|------------|---------------|-----------|-------------|
| `project` | `MarkdownParser` | `10_Projects/` | Projects with embedded task checkboxes |
| `area` | `AreaMarkdown` | `areas/` | Areas of responsibility |
| `goal` | `GoalMarkdown` | `goals/` | 1-year goals |
| `vision` | `VisionMarkdown` | `visions/` | 3-5 year visions |
| `inbox` | `InboxMarkdown` | `inbox/` | Quick capture items |
| `context` | `ContextMarkdown` | `contexts/` | GTD contexts |
| `weekly_review` | `WeeklyReviewMarkdown` | `weekly-reviews/` | Weekly review records |


---

## Built-in: LocalFolderProvider

The default provider reads and writes YAML-frontmatter markdown files in a local folder. This is the same format used by Obsidian, Logseq, and other PKM tools.

### Configuration

```env
STORAGE_PROVIDER=local_folder
STORAGE_PATH=/path/to/your/notes          # or set SECOND_BRAIN_ROOT
WATCH_DIRECTORIES=["10_Projects","20_Areas"]
```

### File Format

Each entity is a markdown file with YAML frontmatter:

```markdown
---
tracker_id: 42
project_status: active
priority: 3
momentum_score: 0.75
---
# My Project

Project description here.

## Next Actions

- [ ] Write tests <!-- tracker:task:abc123 -->
- [x] Set up CI <!-- tracker:task:def456 -->
```

### Entity IDs

Entity IDs are POSIX-style relative paths from the storage root (e.g., `10_Projects/01_Active/My_Project.md`).

### Change Detection

`watch_for_changes()` uses SHA-256 file hashing to detect created, modified, and deleted files between calls. The first call builds a baseline snapshot; subsequent calls diff against it.

### Obsidian Compatibility

Files produced by LocalFolderProvider are fully compatible with Obsidian:
- Standard YAML frontmatter with `---` delimiters
- Obsidian-specific syntax (wikilinks, callouts, embeds, Dataview queries) in body content is preserved through read/write cycles
- Extra frontmatter fields added by Obsidian (tags, aliases, cssclass) are preserved
- Task markers use HTML comments (`<!-- tracker:task:id -->`) which are invisible in Obsidian's preview mode


---

## StorageService (Write-Through Layer)

`StorageService` in `backend/app/services/storage_service.py` wraps the provider and adds:

1. **Write-through**: In `storage_first` mode, every project/task mutation writes to the provider first, then updates SQLite.
2. **Cache rebuild**: On startup, scans all markdown files and populates SQLite as a read cache.
3. **External change detection**: Polls the provider for file changes (e.g., Obsidian edits) and syncs them into SQLite.

### Startup Flow (storage_first mode)

```
Application Start
  └─▶ rebuild_sqlite_cache_on_startup()
       └─▶ provider.list_entities("project")
       └─▶ For each: provider.read_entity() → upsert into SQLite
       └─▶ db.commit()
```

---

## Adding a New Provider

To add a new storage backend (e.g., Notion API, Google Drive):

### Step 1: Create the Provider Class

```python
# backend/app/storage/notion.py
from app.storage.base import StorageProvider, Change

class NotionProvider(StorageProvider):
    def __init__(self, api_key: str, database_id: str):
        self.api_key = api_key
        self.database_id = database_id

    def read_entity(self, entity_type, entity_id):
        # Call Notion API to read a page
        ...

    def write_entity(self, entity_type, entity_id, data):
        # Call Notion API to create/update a page
        ...

    def delete_entity(self, entity_type, entity_id):
        # Call Notion API to archive a page
        ...

    def list_entities(self, entity_type):
        # Query the Notion database
        ...

    def exists(self, entity_type, entity_id):
        # Check if page exists
        ...

    def watch_for_changes(self):
        # Use Notion's last_edited_time to detect changes
        ...
```

### Step 2: Register in the Factory

Edit `backend/app/storage/factory.py`:

```python
def create_storage_provider(provider_type=None, storage_path=None):
    ...
    if provider_type == "notion":
        from app.storage.notion import NotionProvider
        return NotionProvider(
            api_key=settings.NOTION_API_KEY,
            database_id=settings.NOTION_DATABASE_ID,
        )
    ...
```

### Step 3: Add Configuration

Add settings to `backend/app/core/config.py` and `.env.example`:

```python
# config.py
NOTION_API_KEY: Optional[str] = None
NOTION_DATABASE_ID: Optional[str] = None
```

### Step 4: Write Tests

Add tests in `backend/tests/test_storage_<provider>.py` following the pattern in `test_storage_provider.py`.

---

## Key Design Decisions

1. **Entity data as plain dicts**: The storage layer is decoupled from SQLAlchemy ORM models. All data is exchanged as plain Python dicts.
2. **Entity IDs are provider-specific**: Local folder uses relative file paths; a cloud provider might use UUIDs or API page IDs.
3. **Lazy singleton**: The provider instance is created once and cached via `get_storage_provider()`.
4. **Backward compatible**: The `legacy` mode preserves the original SQLite-first behavior. No existing functionality is broken.
