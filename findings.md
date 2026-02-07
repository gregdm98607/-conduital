# Findings — Batch 5 (2026-02-07)

## BACKLOG-072: Unstuck Task Button
- Backend: `POST /intelligence/unstuck/{project_id}?use_ai=true/false` exists and works
- Frontend hook: `useCreateUnstuckTask()` in useProjects.ts — already wired
- StalledAlert.tsx: Has working "Get Unstuck" button using `useAI: false`
- ProjectDetail.tsx: Shows red "Stalled" badge but **NO unstuck button** — this is the gap
- API client: `api.createUnstuckTask(projectId, useAI)` method exists
- **Implementation**: Add "Get Unstuck" button to ProjectDetail when `project.stalled_since` is set

## BACKLOG-084: Cross-Memory Search/Query
- MemoryObject has: `object_id`, `namespace`, `content` (JSON dict), `tags` (JSON list)
- Current search: Client-side only — filters `object_id` and `namespace` in MemoryPage.tsx
- No server-side search endpoint exists
- Service has `list_objects()` with namespace/priority filters but no text search
- **Implementation**: Add `GET /memory/objects/search?q=query` endpoint + expand frontend search

## DEBT-042/043: _persist_to_env Safety
- `_persist_to_env()` in settings.py:87-117 reads/modifies/writes .env file
- No locking — concurrent requests can corrupt
- Regex `re.sub()` on values — newlines in values can inject env vars
- **Implementation**: Add threading.Lock, sanitize values, escape regex in values

## BACKLOG-094: Whitespace Validation
- All schemas use `min_length=1` but don't strip whitespace first
- A string of "   " passes `min_length=1` but is meaningless
- Affects: inbox `content`, task `title`, project `title`, area `title`
- **Implementation**: Add `@field_validator` that strips whitespace before length check

## BACKLOG-109: CORS from Environment
- Currently: `CORS_ORIGINS: list[str]` hardcoded to 4 localhost ports
- `.env.example` has `CORS_ORIGINS=` placeholder but it expects a list, not a CSV string
- Pydantic-settings can't parse CSV into list[str] by default
- **Implementation**: Add `@field_validator` to parse CSV string OR use JSON array
