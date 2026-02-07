# Project Tracker API Documentation

Base URL: `http://localhost:8000`

API Version: `v1`

Prefix: `/api/v1`

## Authentication

Currently no authentication required (local-only application).

## Response Format

All successful responses return JSON with appropriate HTTP status codes:
- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST (creation)
- `204 No Content` - Successful DELETE
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error

## API Endpoints

### Health & Info

#### `GET /health`
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "app": "Project Tracker",
  "version": "0.1.0"
}
```

#### `GET /`
Root endpoint with API information

---

## Projects

### `GET /api/v1/projects`
List all projects with optional filtering

**Query Parameters:**
- `status` (optional): Filter by status (active, completed, etc.)
- `area_id` (optional): Filter by area ID
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page

**Response:**
```json
{
  "projects": [...],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

### `GET /api/v1/projects/{project_id}`
Get a single project by ID

**Query Parameters:**
- `include_tasks` (default: true): Include tasks

**Response:** Project object with tasks

### `GET /api/v1/projects/stalled`
Get all stalled projects (no activity for 14+ days)

**Response:** Array of projects

### `GET /api/v1/projects/search?q={term}`
Search projects by title or description

**Query Parameters:**
- `q` (required): Search term
- `limit` (default: 20, max: 100): Maximum results

### `POST /api/v1/projects`
Create a new project

**Request Body:**
```json
{
  "title": "The Lund Covenant",
  "description": "Literary fiction submission",
  "status": "active",
  "priority": 1,
  "area_id": 5,
  "target_completion_date": "2026-06-01"
}
```

**Response:** Created project (201)

### `PUT /api/v1/projects/{project_id}`
Update a project

**Request Body:** Partial project object (only fields to update)

**Response:** Updated project

### `PATCH /api/v1/projects/{project_id}/status?status={new_status}`
Change project status

**Query Parameters:**
- `status` (required): New status value

**Response:** Updated project

### `GET /api/v1/projects/{project_id}/health`
Get project health metrics

**Response:**
```json
{
  "id": 1,
  "title": "Project Name",
  "status": "active",
  "momentum_score": 0.75,
  "days_since_activity": 2,
  "total_tasks": 15,
  "completed_tasks": 8,
  "pending_tasks": 5,
  "in_progress_tasks": 2,
  "waiting_tasks": 0,
  "next_actions_count": 1,
  "health_status": "strong",
  "completion_percentage": 53.3
}
```

### `DELETE /api/v1/projects/{project_id}`
Delete a project

**Response:** 204 No Content

---

## Tasks

### `GET /api/v1/tasks`
List all tasks with optional filtering

**Query Parameters:**
- `project_id` (optional): Filter by project
- `status` (optional): Filter by status
- `context` (optional): Filter by context
- `is_next_action` (optional): Filter next actions
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page

**Response:** Paginated task list

### `GET /api/v1/tasks/{task_id}`
Get a single task by ID

**Query Parameters:**
- `include_project` (default: true): Include project details

**Response:** Task object with project

### `GET /api/v1/tasks/overdue`
Get all overdue tasks

**Query Parameters:**
- `limit` (default: 50, max: 100): Maximum results

### `GET /api/v1/tasks/quick-wins`
Get quick tasks (2 minutes or less)

**Query Parameters:**
- `limit` (default: 20, max: 100): Maximum results

### `GET /api/v1/tasks/by-context/{context}`
Get tasks filtered by specific context

**Query Parameters:**
- `limit` (default: 20, max: 100): Maximum results

### `GET /api/v1/tasks/search?q={term}`
Search tasks by title or description

**Query Parameters:**
- `q` (required): Search term
- `limit` (default: 20, max: 100): Maximum results

### `POST /api/v1/tasks`
Create a new task

**Request Body:**
```json
{
  "title": "Review agent feedback",
  "description": "Review feedback from query letter",
  "project_id": 1,
  "status": "pending",
  "context": "creative",
  "energy_level": "medium",
  "estimated_minutes": 45,
  "priority": 2,
  "is_next_action": true,
  "due_date": "2026-01-25"
}
```

**Response:** Created task (201)

### `PUT /api/v1/tasks/{task_id}`
Update a task

**Request Body:** Partial task object

**Response:** Updated task

### `POST /api/v1/tasks/{task_id}/complete`
Mark a task as complete

**Query Parameters:**
- `actual_minutes` (optional): Actual time taken

**Response:** Completed task

### `POST /api/v1/tasks/{task_id}/start`
Start a task (mark as in progress)

**Response:** Updated task

### `DELETE /api/v1/tasks/{task_id}`
Delete a task

**Response:** 204 No Content

---

## Next Actions (Smart Prioritization)

### `GET /api/v1/next-actions`
Get prioritized next actions based on momentum and context

**Query Parameters:**
- `context` (optional): Filter by context (@creative, @administrative, etc.)
- `energy_level` (optional): Filter by energy level (high, medium, low)
- `time_available` (optional): Show only tasks fitting in time (minutes)
- `include_stalled` (default: true): Include unstuck tasks from stalled projects
- `limit` (default: 20, max: 100): Maximum results

**Prioritization Logic:**
1. Stalled projects with unstuck tasks
2. High momentum projects with approaching due dates
3. Medium momentum projects
4. Tasks already in progress (minimize context switching)
5. Lower momentum projects

**Response:**
```json
{
  "tasks": [...],
  "stalled_projects_count": 2,
  "context_filter": "creative",
  "energy_filter": "high",
  "time_available": 60
}
```

### `GET /api/v1/next-actions/by-context`
Get next actions grouped by context

**Query Parameters:**
- `limit_per_context` (default: 10, max: 50): Tasks per context

**Response:**
```json
{
  "creative": [...],
  "administrative": [...],
  "research": [...]
}
```

### `GET /api/v1/next-actions/dashboard`
Get daily dashboard data

**Response:**
```json
{
  "top_3_priorities": [...],
  "quick_wins": [...],
  "due_today": [...],
  "stalled_projects_count": 2,
  "top_momentum_projects": [...]
}
```

---

## Areas

### `GET /api/v1/areas`
List all areas

### `GET /api/v1/areas/{area_id}`
Get a single area with projects

### `POST /api/v1/areas`
Create a new area

**Request Body:**
```json
{
  "title": "AI Systems",
  "description": "AI automation and development",
  "folder_path": "20_Areas/20.05_AI_Systems",
  "review_frequency": "weekly"
}
```

### `PUT /api/v1/areas/{area_id}`
Update an area

### `DELETE /api/v1/areas/{area_id}`
Delete an area

---

## Goals

### `GET /api/v1/goals`
List all goals

### `GET /api/v1/goals/{goal_id}`
Get a single goal by ID

### `POST /api/v1/goals`
Create a new goal

**Request Body:**
```json
{
  "title": "Publish first novel",
  "description": "Traditional publishing deal for The Lund Covenant",
  "timeframe": "1_year",
  "target_date": "2027-01-01"
}
```

### `PUT /api/v1/goals/{goal_id}`
Update a goal

### `DELETE /api/v1/goals/{goal_id}`
Delete a goal

---

## Visions

### `GET /api/v1/visions`
List all visions

### `GET /api/v1/visions/{vision_id}`
Get a single vision by ID

### `POST /api/v1/visions`
Create a new vision

**Request Body:**
```json
{
  "title": "Establish literary career",
  "description": "Published author with multiple works",
  "timeframe": "5_year"
}
```

### `PUT /api/v1/visions/{vision_id}`
Update a vision

### `DELETE /api/v1/visions/{vision_id}`
Delete a vision

---

## Contexts

### `GET /api/v1/contexts`
List all contexts

### `GET /api/v1/contexts/{context_id}`
Get a single context by ID

### `POST /api/v1/contexts`
Create a new context

**Request Body:**
```json
{
  "name": "@creative",
  "context_type": "work_type",
  "description": "Creative writing and editing work",
  "icon": "✍️"
}
```

### `PUT /api/v1/contexts/{context_id}`
Update a context

### `DELETE /api/v1/contexts/{context_id}`
Delete a context

---

## Inbox (GTD Capture)

### `GET /api/v1/inbox`
List inbox items

**Query Parameters:**
- `processed` (default: false): Show processed items
- `limit` (default: 50, max: 200): Maximum results

**Response:** Array of inbox items (unprocessed by default)

### `GET /api/v1/inbox/{item_id}`
Get a single inbox item by ID

### `POST /api/v1/inbox`
Quick capture to inbox (GTD Capture phase)

**Request Body:**
```json
{
  "content": "Research manuscript submission guidelines for Agent XYZ",
  "source": "web_ui"
}
```

**Response:** Created inbox item (201)

### `POST /api/v1/inbox/{item_id}/process`
Process an inbox item (GTD Clarify phase)

**Request Body:**
```json
{
  "result_type": "task",
  "result_id": 42
}
```

**Response:** Updated inbox item with processing result

### `DELETE /api/v1/inbox/{item_id}`
Delete an inbox item

**Response:** 204 No Content

---

## Status Enums

### Project Status
- `active` - Currently active
- `someday_maybe` - Future consideration
- `completed` - Completed
- `archived` - Archived
- `stalled` - No activity for 14+ days

### Task Status
- `pending` - Not started
- `in_progress` - Currently working on
- `waiting` - Waiting on someone/something
- `completed` - Done
- `cancelled` - Cancelled

### Task Type
- `action` - Actionable task
- `milestone` - Project milestone
- `waiting_for` - Waiting for item
- `someday_maybe` - Future consideration

### Priority (1-5)
- `1` - Critical
- `2` - High
- `3` - Medium (default)
- `4` - Low
- `5` - Very Low

### Energy Level
- `high` - High energy required
- `medium` - Medium energy
- `low` - Low energy

### Context Types
- `location` - Physical location (@home, @office)
- `energy` - Energy level requirement
- `work_type` - Type of work (@creative, @administrative)
- `time` - Time requirement (@quick_win, @focus_block)
- `tool` - Tool requirement (@computer, @phone)

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both interfaces allow you to:
- View all endpoints and their parameters
- Test endpoints directly from the browser
- See request/response schemas
- Download OpenAPI specification

---

## Example Workflows

### Creating a New Project with Tasks

```bash
# 1. Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "title": "New Project",
    "status": "active",
    "priority": 2
  }'

# Response: {"id": 5, "title": "New Project", ...}

# 2. Create next action task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Define project scope",
    "project_id": 5,
    "is_next_action": true,
    "context": "creative",
    "estimated_minutes": 30
  }'
```

### GTD Workflow: Capture → Clarify → Organize

```bash
# 1. Capture
curl -X POST http://localhost:8000/api/v1/inbox \
  -H "Content-Type: application/json" \
  -d '{"content": "Research topic X"}'

# Response: {"id": 10, ...}

# 2. Clarify & Organize - create task from inbox item
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Research topic X",
    "project_id": 5,
    "context": "research",
    "estimated_minutes": 60
  }'

# Response: {"id": 15, ...}

# 3. Mark inbox item as processed
curl -X POST http://localhost:8000/api/v1/inbox/10/process \
  -H "Content-Type: application/json" \
  -d '{
    "result_type": "task",
    "result_id": 15
  }'
```

### Get Your Daily Dashboard

```bash
curl http://localhost:8000/api/v1/next-actions/dashboard
```

Returns your top priorities, quick wins, tasks due today, and project momentum overview.

---

## Error Handling

Validation errors return 422 with details:

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

Not found errors return 404:

```json
{
  "detail": "Project not found"
}
```

---

**Last Updated:** 2026-01-20
**API Version:** v1
