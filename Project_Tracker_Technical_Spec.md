# Project Tracker & Program Manager - Technical Specification

**Version:** 1.0
**Date:** 2026-01-20
**Status:** Draft
**Methodology:** GTD (Getting Things Done) + Manage Your Now

---

## Executive Summary

This document specifies a web-based project and task management system designed to integrate with a PARA-organized Second Brain file structure. The system prioritizes project momentum, surfaces next actions intelligently, and provides bidirectional synchronization between structured data and markdown files.

### Key Design Principles
1. **Momentum-First**: Maintain active project flow while identifying stalled projects
2. **Minimal Viable Actions**: For stalled projects, suggest small unsticking tasks
3. **Bidirectional Sync**: Changes flow both ways between tracker and file system
4. **Context-Aware**: Match tasks to user's current energy and context
5. **GTD Compliant**: Implement all core GTD workflows and horizons

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Dashboard (Frontend)                 │
│            React + TypeScript + Tailwind CSS                │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API / WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                   Application Server (Backend)               │
│                    Python FastAPI + SQLAlchemy              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Project      │  │ Sync         │  │ AI           │     │
│  │ Engine       │  │ Engine       │  │ Integration  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────┬─────────────────────┬───────────────────────┘
              │                     │
    ┌─────────▼─────────┐  ┌────────▼──────────┐
    │   SQLite DB       │  │  File System      │
    │   (Tracker Data)  │  │  (Second Brain)   │
    └───────────────────┘  └───────────────────┘
                                     │
                            ┌────────▼────────┐
                            │ Claude MCP      │
                            │ Integration     │
                            └─────────────────┘
```

### 1.2 Technology Stack

#### Frontend
- **Framework**: React 18+ with TypeScript
- **State Management**: Zustand or Redux Toolkit
- **UI Library**: Tailwind CSS + shadcn/ui components
- **Data Fetching**: TanStack Query (React Query)
- **Real-time**: Socket.IO client
- **Routing**: React Router v6
- **Charts**: Recharts or Chart.js
- **Date Handling**: date-fns
- **Drag & Drop**: dnd-kit

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite with WAL mode (single-file, backup-friendly)
- **Real-time**: Socket.IO (Python)
- **File Watching**: watchdog library
- **Background Tasks**: Celery with Redis or APScheduler
- **API Documentation**: OpenAPI/Swagger (auto-generated)
- **Markdown Processing**: python-frontmatter, markdown-it-py

#### AI Integration
- **Claude API**: Anthropic SDK
- **MCP Server**: Claude Model Context Protocol
- **Vector Store**: ChromaDB (for semantic search in Second Brain)

#### Development & DevOps
- **Package Manager**: Poetry (Python), npm/pnpm (JavaScript)
- **Testing**: pytest (backend), Jest + React Testing Library (frontend)
- **Linting**: ruff (Python), ESLint (JavaScript)
- **Formatting**: black (Python), Prettier (JavaScript)
- **Version Control**: Git
- **Containerization**: Docker + Docker Compose (optional)

---

## 2. Database Schema

### 2.1 Core Tables

#### `projects`
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'active', -- active, someday_maybe, completed, archived, stalled
    area_id INTEGER REFERENCES areas(id),
    phase_template_id INTEGER REFERENCES phase_templates(id),
    priority INTEGER DEFAULT 3, -- 1-5, 1 is highest
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP,
    completed_at TIMESTAMP,
    target_completion_date DATE,
    file_path TEXT UNIQUE, -- Path to project file in Second Brain
    file_hash TEXT, -- SHA-256 for change detection
    momentum_score REAL DEFAULT 0.0, -- Calculated momentum metric
    stalled_since TIMESTAMP,

    -- GTD Horizons alignment
    goal_id INTEGER REFERENCES goals(id),
    vision_id INTEGER REFERENCES visions(id),

    UNIQUE(file_path)
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_momentum ON projects(momentum_score);
CREATE INDEX idx_projects_area ON projects(area_id);
CREATE INDEX idx_projects_last_activity ON projects(last_activity_at);
```

#### `tasks`
```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, waiting, completed, cancelled
    task_type TEXT DEFAULT 'action', -- action, milestone, waiting_for, someday_maybe

    -- Sequencing
    sequence_order INTEGER, -- For sequential tasks
    parent_task_id INTEGER REFERENCES tasks(id),
    phase_id INTEGER REFERENCES project_phases(id),

    -- Scheduling
    due_date DATE,
    defer_until DATE,
    estimated_minutes INTEGER,
    actual_minutes INTEGER,

    -- Context and filtering
    context TEXT, -- creative, administrative, research, communication, deep_work, quick_win
    energy_level TEXT, -- high, medium, low
    location TEXT, -- home, office, anywhere, errand

    -- Priority and momentum
    priority INTEGER DEFAULT 3,
    is_next_action BOOLEAN DEFAULT FALSE,
    is_two_minute_task BOOLEAN DEFAULT FALSE,
    is_unstuck_task BOOLEAN DEFAULT FALSE, -- Minimal viable task for stalled projects

    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    started_at TIMESTAMP,

    -- Resources
    waiting_for TEXT, -- Person/thing we're waiting on
    resource_requirements TEXT, -- JSON: files, tools, people needed

    -- File sync
    file_line_number INTEGER, -- Line in project file where this task appears
    file_marker TEXT, -- Unique marker for sync (e.g., task UUID in comment)

    CHECK(status IN ('pending', 'in_progress', 'waiting', 'completed', 'cancelled')),
    CHECK(task_type IN ('action', 'milestone', 'waiting_for', 'someday_maybe'))
);

CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_next_action ON tasks(is_next_action) WHERE is_next_action = TRUE;
CREATE INDEX idx_tasks_context ON tasks(context);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
```

#### `areas`
```sql
CREATE TABLE areas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    folder_path TEXT UNIQUE, -- Path to area folder (e.g., 20_Areas/20.05_AI_Systems)
    standard_of_excellence TEXT, -- GTD: what does "good" look like?
    review_frequency TEXT DEFAULT 'weekly', -- daily, weekly, monthly
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(folder_path)
);
```

#### `project_phases`
```sql
CREATE TABLE project_phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    phase_name TEXT NOT NULL,
    phase_order INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, active, completed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    description TEXT,

    UNIQUE(project_id, phase_order)
);

CREATE INDEX idx_phases_project ON project_phases(project_id);
```

#### `phase_templates`
```sql
CREATE TABLE phase_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    phases_json TEXT NOT NULL, -- JSON array of phase definitions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Example templates:
-- "Manuscript Development": ["Research", "Outline", "First Draft", "Revision", "Editing", "Submission"]
-- "Genealogy Research": ["Source Collection", "Digitization", "Analysis", "Narrative Writing", "Review"]
```

#### `goals`
```sql
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    timeframe TEXT, -- 1_year, 2_year, 3_year
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_date DATE,
    completed_at TIMESTAMP
);
```

#### `visions`
```sql
CREATE TABLE visions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    timeframe TEXT, -- 3_year, 5_year, life_purpose
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `contexts`
```sql
CREATE TABLE contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE, -- @computer, @home, @office, @errands, @calls, @creative, @administrative
    context_type TEXT, -- location, energy, work_type
    description TEXT,
    icon TEXT -- For UI display
);
```

#### `activity_log`
```sql
CREATE TABLE activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL, -- project, task, area
    entity_id INTEGER NOT NULL,
    action_type TEXT NOT NULL, -- created, updated, completed, status_changed, file_synced
    details TEXT, -- JSON with specific changes
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT -- user, file_sync, ai_assistant
);

CREATE INDEX idx_activity_entity ON activity_log(entity_type, entity_id);
CREATE INDEX idx_activity_timestamp ON activity_log(timestamp);
```

#### `sync_state`
```sql
CREATE TABLE sync_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    last_synced_at TIMESTAMP,
    last_file_modified_at TIMESTAMP,
    file_hash TEXT,
    sync_status TEXT, -- synced, pending, conflict, error
    error_message TEXT,
    entity_type TEXT, -- project, area, resource
    entity_id INTEGER
);

CREATE INDEX idx_sync_status ON sync_state(sync_status);
```

#### `inbox`
```sql
CREATE TABLE inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    source TEXT, -- web_ui, api, voice, email, file
    result_type TEXT, -- task, project, reference, trash
    result_id INTEGER, -- ID of created task/project if processed

    CHECK(result_type IN ('task', 'project', 'reference', 'trash', NULL))
);

CREATE INDEX idx_inbox_processed ON inbox(processed_at);
```

### 2.2 Views and Derived Data

#### `v_next_actions`
```sql
CREATE VIEW v_next_actions AS
SELECT
    t.*,
    p.title as project_title,
    p.momentum_score,
    p.status as project_status,
    CASE
        WHEN p.stalled_since IS NOT NULL THEN 1
        ELSE 0
    END as is_stalled_project
FROM tasks t
JOIN projects p ON t.project_id = p.id
WHERE t.status IN ('pending', 'in_progress')
    AND t.is_next_action = TRUE
    AND (t.defer_until IS NULL OR t.defer_until <= DATE('now'))
    AND p.status = 'active'
ORDER BY
    is_stalled_project DESC, -- Stalled projects first
    t.is_unstuck_task DESC,  -- Unstuck tasks prioritized
    p.momentum_score DESC,   -- Then by momentum
    t.priority ASC,          -- Then by priority
    t.due_date ASC NULLS LAST;
```

#### `v_project_health`
```sql
CREATE VIEW v_project_health AS
SELECT
    p.id,
    p.title,
    p.status,
    p.momentum_score,
    p.last_activity_at,
    JULIANDAY('now') - JULIANDAY(p.last_activity_at) as days_since_activity,
    COUNT(t.id) as total_tasks,
    SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
    SUM(CASE WHEN t.is_next_action THEN 1 ELSE 0 END) as next_actions_count,
    CASE
        WHEN p.stalled_since IS NOT NULL THEN 'stalled'
        WHEN JULIANDAY('now') - JULIANDAY(p.last_activity_at) > 7 THEN 'at_risk'
        WHEN p.momentum_score > 0.7 THEN 'strong'
        WHEN p.momentum_score > 0.4 THEN 'moderate'
        ELSE 'weak'
    END as health_status
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
WHERE p.status = 'active'
GROUP BY p.id;
```

---

## 3. API Design

### 3.1 REST API Endpoints

#### Projects

```
GET    /api/v1/projects                    # List all projects with filters
GET    /api/v1/projects/{id}               # Get single project with tasks
POST   /api/v1/projects                    # Create new project
PUT    /api/v1/projects/{id}               # Update project
DELETE /api/v1/projects/{id}               # Delete/archive project
PATCH  /api/v1/projects/{id}/status        # Change project status
GET    /api/v1/projects/{id}/health        # Get project health metrics
POST   /api/v1/projects/{id}/unstuck       # Generate unstuck task
```

#### Tasks

```
GET    /api/v1/tasks                       # List tasks with filters
GET    /api/v1/tasks/{id}                  # Get single task
POST   /api/v1/tasks                       # Create task
PUT    /api/v1/tasks/{id}                  # Update task
DELETE /api/v1/tasks/{id}                  # Delete task
PATCH  /api/v1/tasks/{id}/status           # Update task status
POST   /api/v1/tasks/{id}/complete         # Mark task complete
GET    /api/v1/tasks/next-actions          # Get prioritized next actions
POST   /api/v1/tasks/{id}/start            # Start task (timer)
POST   /api/v1/tasks/{id}/stop             # Stop task (timer)
```

#### Areas

```
GET    /api/v1/areas                       # List all areas
GET    /api/v1/areas/{id}                  # Get area with projects
POST   /api/v1/areas                       # Create area
PUT    /api/v1/areas/{id}                  # Update area
GET    /api/v1/areas/{id}/health           # Area health dashboard
```

#### Next Actions & Dashboard

```
GET    /api/v1/dashboard                   # Daily dashboard data
GET    /api/v1/next-actions                # Smart next action recommendations
GET    /api/v1/next-actions/by-context     # Next actions grouped by context
GET    /api/v1/stalled-projects            # List stalled projects with suggestions
```

#### Sync

```
POST   /api/v1/sync/scan                   # Scan file system for changes
POST   /api/v1/sync/project/{id}           # Sync specific project
POST   /api/v1/sync/all                    # Full bidirectional sync
GET    /api/v1/sync/status                 # Current sync status
GET    /api/v1/sync/conflicts              # List sync conflicts
POST   /api/v1/sync/resolve/{id}           # Resolve conflict
```

#### Inbox

```
GET    /api/v1/inbox                       # Get unprocessed inbox items
POST   /api/v1/inbox                       # Capture new item
POST   /api/v1/inbox/{id}/process          # Process inbox item
DELETE /api/v1/inbox/{id}                  # Delete inbox item
```

#### Reviews

```
GET    /api/v1/reviews/daily               # Generate daily review
GET    /api/v1/reviews/weekly              # Generate weekly review
POST   /api/v1/reviews/weekly/complete     # Mark weekly review complete
GET    /api/v1/reviews/monthly             # Generate monthly metrics
```

#### Analytics

```
GET    /api/v1/analytics/momentum          # Momentum trends over time
GET    /api/v1/analytics/completion-rate   # Task/project completion stats
GET    /api/v1/analytics/time-distribution # Time spent by project/context
GET    /api/v1/analytics/bottlenecks       # Identify recurring blockers
```

#### AI Integration

```
POST   /api/v1/ai/decompose-task           # Break task into subtasks
POST   /api/v1/ai/suggest-next-action      # AI suggestion for next action
POST   /api/v1/ai/analyze-project          # Project health analysis
POST   /api/v1/ai/generate-unstuck         # Generate unstuck task
POST   /api/v1/ai/weekly-review            # AI-assisted weekly review
POST   /api/v1/ai/chat                     # Natural language commands
```

### 3.2 WebSocket Events

```javascript
// Client -> Server
socket.emit('task:start', { taskId: 123 })
socket.emit('task:complete', { taskId: 123 })
socket.emit('sync:file-changed', { filePath: '...' })

// Server -> Client
socket.on('project:updated', { projectId, changes })
socket.on('task:created', { task })
socket.on('sync:started', { filesCount })
socket.on('sync:completed', { stats })
socket.on('next-actions:updated', { actions })
socket.on('momentum:changed', { projectId, oldScore, newScore })
```

---

## 4. Bidirectional Sync Mechanism

### 4.1 File Format Convention

Projects in the Second Brain will use YAML frontmatter for metadata:

```markdown
---
tracker_id: 42
project_status: active
priority: 2
last_synced: 2026-01-20T10:30:00Z
momentum_score: 0.75
area: 20.05_AI_Systems
phases:
  - name: Research
    status: completed
  - name: Development
    status: active
  - name: Testing
    status: pending
---

# Project Title

Project description and notes...

## Next Actions

- [ ] Task 1 <!-- tracker:task:101 -->
- [ ] Task 2 <!-- tracker:task:102 -->
- [x] Completed task <!-- tracker:task:100 -->

## Waiting For

- [ ] Feedback from editor <!-- tracker:task:103:waiting -->

## Someday/Maybe

- [ ] Future enhancement <!-- tracker:task:104:someday -->
```

### 4.2 Sync Algorithm

#### File -> Database (Pull)

```python
def sync_file_to_database(file_path: Path):
    # 1. Read file and parse frontmatter
    content = file_path.read_text()
    metadata, body = parse_frontmatter(content)

    # 2. Check if file has changed (hash comparison)
    current_hash = hashlib.sha256(content.encode()).hexdigest()
    sync_record = db.query(SyncState).filter_by(file_path=str(file_path)).first()

    if sync_record and sync_record.file_hash == current_hash:
        return  # No changes

    # 3. Update or create project
    tracker_id = metadata.get('tracker_id')
    if tracker_id:
        project = db.query(Project).get(tracker_id)
    else:
        project = Project()

    project.title = extract_title(body)
    project.status = metadata.get('project_status', 'active')
    project.priority = metadata.get('priority', 3)
    project.momentum_score = metadata.get('momentum_score', 0.0)
    project.file_path = str(file_path)
    project.file_hash = current_hash

    # 4. Parse tasks from markdown checkboxes
    tasks = parse_tasks_from_markdown(body)

    for task_data in tasks:
        task_marker = extract_task_marker(task_data['line'])
        if task_marker:
            task = db.query(Task).filter_by(file_marker=task_marker).first()
        else:
            task = Task()
            task.file_marker = generate_task_marker()

        task.title = task_data['title']
        task.status = 'completed' if task_data['checked'] else 'pending'
        task.file_line_number = task_data['line_number']
        task.project_id = project.id

        db.add(task)

    # 5. Update sync state
    update_sync_state(file_path, current_hash, 'synced')
    db.commit()
```

#### Database -> File (Push)

```python
def sync_database_to_file(project_id: int):
    project = db.query(Project).get(project_id)
    file_path = Path(project.file_path)

    # 1. Read current file
    if file_path.exists():
        content = file_path.read_text()
        metadata, body = parse_frontmatter(content)
    else:
        metadata, body = {}, ""

    # 2. Update frontmatter
    metadata.update({
        'tracker_id': project.id,
        'project_status': project.status,
        'priority': project.priority,
        'momentum_score': project.momentum_score,
        'last_synced': datetime.utcnow().isoformat(),
    })

    # 3. Update task checkboxes in body
    lines = body.split('\n')
    tasks = db.query(Task).filter_by(project_id=project.id).all()

    for task in tasks:
        if task.file_line_number and task.file_line_number < len(lines):
            # Update existing line
            checkbox = '[x]' if task.status == 'completed' else '[ ]'
            lines[task.file_line_number] = f"- {checkbox} {task.title} <!-- {task.file_marker} -->"
        else:
            # Append new task
            checkbox = '[x]' if task.status == 'completed' else '[ ]'
            lines.append(f"- {checkbox} {task.title} <!-- {task.file_marker} -->")

    # 4. Write file
    new_content = format_frontmatter(metadata) + '\n'.join(lines)
    file_path.write_text(new_content)

    # 5. Update hash
    new_hash = hashlib.sha256(new_content.encode()).hexdigest()
    project.file_hash = new_hash
    update_sync_state(project.file_path, new_hash, 'synced')
    db.commit()
```

#### Conflict Resolution

```python
def handle_sync_conflict(file_path: Path):
    # 1. Detect conflict: both file and DB changed since last sync
    sync_record = get_sync_state(file_path)
    file_hash = calculate_file_hash(file_path)

    if sync_record.file_hash != file_hash:
        # File changed externally
        file_timestamp = file_path.stat().st_mtime

        project = db.query(Project).filter_by(file_path=str(file_path)).first()
        db_timestamp = project.updated_at.timestamp()

        if abs(file_timestamp - db_timestamp) < 2:
            # Timestamps very close, likely safe to merge
            merge_changes(file_path, project)
        else:
            # True conflict - create backup and notify user
            backup_path = create_backup(file_path)
            mark_conflict(sync_record, {
                'file_backup': str(backup_path),
                'db_version_id': project.id,
                'timestamp': datetime.utcnow()
            })
            notify_user_conflict(file_path)
```

### 4.3 File Watcher

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SecondBrainWatcher(FileSystemEventHandler):
    def __init__(self, sync_engine):
        self.sync_engine = sync_engine
        self.debounce_timers = {}

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only watch specific directories
        if not self.should_watch(file_path):
            return

        # Debounce: wait 1 second before syncing
        if file_path in self.debounce_timers:
            self.debounce_timers[file_path].cancel()

        timer = threading.Timer(1.0, self.sync_engine.sync_file, [file_path])
        self.debounce_timers[file_path] = timer
        timer.start()

    def should_watch(self, file_path: Path) -> bool:
        # Watch markdown files in 10_Projects and 20_Areas
        return (
            file_path.suffix in ['.md', '.markdown'] and
            any(part in file_path.parts for part in ['10_Projects', '20_Areas'])
        )
```

---

## 5. Next Action Engine

### 5.1 Momentum Calculation

```python
def calculate_momentum_score(project: Project) -> float:
    """
    Calculate project momentum score (0.0 to 1.0)

    Factors:
    - Recent activity (tasks completed, updates made)
    - Time since last activity
    - Completion velocity
    - Next action availability
    """
    now = datetime.utcnow()
    score = 0.0

    # Factor 1: Days since last activity (40% weight)
    if project.last_activity_at:
        days_since = (now - project.last_activity_at).days
        activity_score = max(0, 1 - (days_since / 30))  # Decay over 30 days
        score += activity_score * 0.4

    # Factor 2: Recent completion rate (30% weight)
    recent_tasks = get_recent_tasks(project, days=7)
    if recent_tasks:
        completed = sum(1 for t in recent_tasks if t.status == 'completed')
        completion_rate = completed / len(recent_tasks)
        score += completion_rate * 0.3

    # Factor 3: Has clear next action (20% weight)
    has_next_action = db.query(Task).filter_by(
        project_id=project.id,
        is_next_action=True,
        status='pending'
    ).count() > 0

    if has_next_action:
        score += 0.2

    # Factor 4: Activity frequency (10% weight)
    activity_count = db.query(ActivityLog).filter(
        ActivityLog.entity_type == 'project',
        ActivityLog.entity_id == project.id,
        ActivityLog.timestamp > now - timedelta(days=14)
    ).count()

    frequency_score = min(1.0, activity_count / 10)  # Cap at 10 activities
    score += frequency_score * 0.1

    return round(score, 2)
```

### 5.2 Stalled Project Detection

```python
def detect_stalled_projects():
    """
    Identify projects that need attention

    A project is stalled if:
    - No activity in 14+ days
    - Momentum score < 0.2
    - Has pending tasks but no next action
    """
    threshold_date = datetime.utcnow() - timedelta(days=14)

    stalled = db.query(Project).filter(
        Project.status == 'active',
        or_(
            Project.last_activity_at < threshold_date,
            Project.momentum_score < 0.2
        )
    ).all()

    for project in stalled:
        if not project.stalled_since:
            project.stalled_since = datetime.utcnow()

            # Generate unstuck task if none exists
            has_unstuck = db.query(Task).filter_by(
                project_id=project.id,
                is_unstuck_task=True,
                status='pending'
            ).first()

            if not has_unstuck:
                generate_unstuck_task(project)

    db.commit()
    return stalled
```

### 5.3 Unstuck Task Generation

```python
async def generate_unstuck_task(project: Project) -> Task:
    """
    Use AI to suggest minimal viable task to restart project

    Characteristics of good unstuck tasks:
    - 5-15 minutes max
    - Low friction (easy to start)
    - Moves project forward even slightly
    - Rebuilds context/momentum
    """

    # Gather context
    recent_activity = get_recent_activity(project, days=30)
    pending_tasks = get_pending_tasks(project)
    project_notes = read_project_file(project.file_path)

    # Query Claude
    prompt = f"""
    Project: {project.title}
    Status: Stalled (no activity for {days_since_activity(project)} days)

    Recent activity:
    {format_activity(recent_activity)}

    Pending tasks:
    {format_tasks(pending_tasks)}

    Notes:
    {project_notes[:500]}

    Generate ONE minimal viable task (5-15 minutes) that will:
    1. Rebuild momentum for this project
    2. Be easy to start with low friction
    3. Provide clear value/progress

    Return just the task title, nothing else.
    """

    response = await claude_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    task_title = response.content[0].text.strip()

    # Create task
    unstuck_task = Task(
        project_id=project.id,
        title=task_title,
        is_next_action=True,
        is_unstuck_task=True,
        estimated_minutes=10,
        context='quick_win',
        energy_level='low',
        description=f"Minimal task to restart project momentum (AI-generated)"
    )

    db.add(unstuck_task)
    db.commit()

    return unstuck_task
```

### 5.4 Next Action Selection Algorithm

```python
def get_prioritized_next_actions(
    context: Optional[str] = None,
    energy_level: Optional[str] = None,
    time_available: Optional[int] = None,
    include_stalled: bool = True
) -> List[Task]:
    """
    Return prioritized list of next actions

    Prioritization logic:
    1. Stalled projects with unstuck tasks (if include_stalled)
    2. High momentum projects with due dates
    3. Medium momentum projects
    4. Recently started tasks (minimize context switching)
    """

    query = db.query(Task).join(Project).filter(
        Task.is_next_action == True,
        Task.status.in_(['pending', 'in_progress']),
        or_(Task.defer_until.is_(None), Task.defer_until <= date.today()),
        Project.status == 'active'
    )

    # Apply filters
    if context:
        query = query.filter(Task.context == context)
    if energy_level:
        query = query.filter(Task.energy_level == energy_level)
    if time_available:
        query = query.filter(
            or_(
                Task.estimated_minutes.is_(None),
                Task.estimated_minutes <= time_available
            )
        )

    tasks = query.all()

    # Sort by priority
    def sort_key(task):
        project = task.project

        # Priority tiers
        if project.stalled_since and task.is_unstuck_task:
            tier = 0  # Highest: unstuck stalled projects
        elif task.due_date and task.due_date <= date.today() + timedelta(days=3):
            tier = 1  # Due soon
        elif project.momentum_score > 0.7:
            tier = 2  # High momentum
        elif task.started_at:
            tier = 3  # Already in progress
        elif project.momentum_score > 0.4:
            tier = 4  # Medium momentum
        else:
            tier = 5  # Low momentum

        return (
            tier,
            -project.momentum_score,  # Higher momentum first (within tier)
            task.priority,            # Lower number = higher priority
            task.due_date or date.max # Sooner due dates first
        )

    tasks.sort(key=sort_key)
    return tasks
```

---

## 6. User Interface Design

### 6.1 Core Views

#### Daily Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│  🌅 Good Morning! Monday, January 20, 2026                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ⚡ TODAY'S TOP 3                                            │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. [🎯] Review agent feedback - The Lund Covenant      │ │
│  │    Context: Creative • Est: 45min • Due: Today         │ │
│  │    [Start] [Defer] [Complete]                          │ │
│  │                                                         │ │
│  │ 2. [⚠️] Generate test scenarios - Proactive Assistant  │ │
│  │    Context: Deep Work • Est: 60min                     │ │
│  │    ⚠️ Project stalled 12 days - Unstuck task          │ │
│  │    [Start] [Defer] [Complete]                          │ │
│  │                                                         │ │
│  │ 3. [📝] Draft Mission 11 outline - Operation Granny    │ │
│  │    Context: Administrative • Est: 20min                │ │
│  │    [Start] [Defer] [Complete]                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📊 PROJECT MOMENTUM                                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ███████████░░░░░ The Lund Covenant (0.85)              │ │
│  │ ████████░░░░░░░░ Ley-Lines Reboot (0.62)               │ │
│  │ ██░░░░░░░░░░░░░░ Proactive Assistant (0.18) ⚠️         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  🕒 QUICK WINS (< 15 min)                                   │
│  • Review submission tracker                                │
│  • Update project status in file                            │
│  • Capture genealogy source note                            │
│                                                              │
│  📥 INBOX (3 items)   |   📅 DUE THIS WEEK (7)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Project List View
```
┌─────────────────────────────────────────────────────────────┐
│  Projects                          [+ New] [Sync] [⚙️]      │
├─────────────────────────────────────────────────────────────┤
│  Filter: [All] Active Stalled Someday     Sort: Momentum ▼  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📚 LITERARY PROJECTS                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 📖 The Lund Covenant                    🟢 0.85 ▲      │ │
│  │    Status: Submission Phase                             │ │
│  │    Next: Review agent feedback (Creative, 45min)        │ │
│  │    Last activity: 2 hours ago                           │ │
│  │    Progress: 12/15 tasks ███████████░░░ 80%            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ⚠️ Proactive Assistant                 🔴 0.18 ▼      │ │
│  │    Status: Development (Phase II)                       │ │
│  │    ⚠️ STALLED 12 days                                  │ │
│  │    Unstuck: Generate test scenarios (Deep Work, 60min)  │ │
│  │    Last activity: 12 days ago                           │ │
│  │    Progress: 8/24 tasks ███░░░░░░░░░░░ 33%            │ │
│  │    [View Details] [Generate Unstuck Task]               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Project Detail View
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Projects                                          │
│                                                              │
│  📖 The Lund Covenant                          [Edit] [...]  │
│  Literary Fiction • Submission Phase                         │
│  Momentum: 0.85 🟢 • Priority: High • Area: Literary Work   │
│  Last activity: 2 hours ago                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [Overview] [Tasks] [Phases] [Timeline] [Notes] [Files]     │
│                                                              │
│  ⚡ NEXT ACTION                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Review agent feedback from query letter                 │ │
│  │ Context: Creative • Energy: Medium • Est: 45 min        │ │
│  │ [Start Task] [Snooze] [Not Now]                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📋 PENDING TASKS (4)                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ □ Submit to 3 additional agents (Admin, 30min)         │ │
│  │ □ Update query tracker spreadsheet (Quick, 10min)      │ │
│  │ □ Research comp titles for pitch (Research, 60min)     │ │
│  │ □ Draft synopsis variations (Creative, 90min)          │ │
│  │ [+ Add Task]                                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ⏳ WAITING FOR (1)                                          │
│  │ • Response from Agent #3 (waiting 5 days)               │
│                                                              │
│  ✅ COMPLETED (12)                                           │
│  │ ✓ Finalize submission draft v17                         │
│  │ ✓ Complete developmental edit review                    │
│  │ ✓ Prepare 3-chapter sample                              │
│  │ ... [View All]                                           │
│                                                              │
│  📊 PHASES                                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ✓ Writing & Revision                                    │ │
│  │ ✓ Developmental Editing                                 │ │
│  │ ► Submission / Query (Active)                           │ │
│  │ ○ Publication                                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  🔗 RESOURCES                                                │
│  • Project folder: 10_Projects/01.01_The_Lund_Covenant     │
│  • Submission drafts, Query tracker, Style guide...         │
│  [Open in File Browser] [Sync Now]                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Context View
```
┌─────────────────────────────────────────────────────────────┐
│  Next Actions by Context                                     │
├─────────────────────────────────────────────────────────────┤
│  [All] @Creative @Deep_Work @Admin @Research @Communication │
│                                                              │
│  🎨 CREATIVE (4 tasks)                                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ □ Review agent feedback - The Lund Covenant             │ │
│  │   Medium energy • 45min • Due today                     │ │
│  │                                                          │ │
│  │ □ Draft chapter outline - Winter Fire                   │ │
│  │   High energy • 90min                                   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  🧠 DEEP WORK (3 tasks)                                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ □ Generate test scenarios - Proactive Assistant ⚠️      │ │
│  │   High energy • 60min • Unstuck task                    │ │
│  │                                                          │ │
│  │ □ Analyze GEDCOM data - AI Use Cases                    │ │
│  │   Medium energy • 120min                                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  📋 ADMINISTRATIVE (5 tasks)                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ □ Update query tracker - The Lund Covenant              │ │
│  │   Low energy • 10min • Quick win                        │ │
│  │                                                          │ │
│  │ □ Draft Mission 11 outline - Operation Granny           │ │
│  │   Medium energy • 20min                                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### Stalled Projects Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ Projects Needing Attention                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  3 projects stalled or at risk                              │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🔴 Proactive Assistant                                  │ │
│  │ Stalled 12 days • Last: Updated memory architecture     │ │
│  │                                                          │ │
│  │ 💡 Suggested unstuck task:                              │ │
│  │ "Review existing test suite and identify 3 test cases"  │ │
│  │ Deep Work • 30 min                                      │ │
│  │                                                          │ │
│  │ [Start This Task] [Different Suggestion] [Archive]      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🟡 Winter Fire, Summer Ash                              │ │
│  │ At risk (7 days) • Last: Updated character profiles     │ │
│  │                                                          │ │
│  │ 💡 Suggested unstuck task:                              │ │
│  │ "Write 200-word scene snippet to test voice"           │ │
│  │ Creative • 15 min                                       │ │
│  │                                                          │ │
│  │ [Start This Task] [Different Suggestion] [Defer]        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 🟡 Direct Line Biographies                              │ │
│  │ At risk (8 days) • Last: Added source citation         │ │
│  │                                                          │ │
│  │ Next action available:                                  │ │
│  │ "Research birth record for Johann Schmidt"             │ │
│  │ Research • 45 min                                       │ │
│  │                                                          │ │
│  │ [Start This Task] [View Project]                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Component Library

Key UI components to develop:

1. **TaskCard** - Display task with context, energy, time estimate
2. **ProjectCard** - Project summary with momentum indicator
3. **MomentumBar** - Visual momentum score (0-1 scale)
4. **HealthIndicator** - Traffic light status (🟢🟡🔴)
5. **PhaseTimeline** - Visual phase progression
6. **NextActionWidget** - Prominent next action display
7. **QuickCaptureModal** - Fast inbox entry
8. **ContextFilter** - Filter by context/energy/time
9. **SyncStatusIndicator** - Real-time sync status
10. **WeeklyReviewChecklist** - GTD weekly review workflow

---

## 7. Claude Integration

### 7.1 MCP Server Implementation

```python
# mcp_server.py
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("project-tracker")

@server.tool()
async def get_next_actions(
    context: str | None = None,
    energy: str | None = None
) -> list[dict]:
    """Get prioritized next actions"""
    actions = get_prioritized_next_actions(context, energy)
    return [serialize_task(t) for t in actions]

@server.tool()
async def complete_task(task_id: int, actual_minutes: int | None = None) -> dict:
    """Mark a task as complete"""
    task = db.query(Task).get(task_id)
    task.status = 'completed'
    task.completed_at = datetime.utcnow()
    if actual_minutes:
        task.actual_minutes = actual_minutes

    # Update project momentum
    update_project_momentum(task.project_id)
    db.commit()

    return {"success": True, "task": serialize_task(task)}

@server.tool()
async def create_project(
    title: str,
    description: str,
    area: str | None = None,
    priority: int = 3
) -> dict:
    """Create a new project"""
    project = Project(
        title=title,
        description=description,
        priority=priority,
        status='active'
    )

    if area:
        area_obj = db.query(Area).filter_by(title=area).first()
        if area_obj:
            project.area_id = area_obj.id

    db.add(project)
    db.commit()

    # Create project file in Second Brain
    create_project_file(project)

    return {"success": True, "project": serialize_project(project)}

@server.tool()
async def add_task(
    project_id: int,
    title: str,
    context: str | None = None,
    estimated_minutes: int | None = None,
    is_next_action: bool = False
) -> dict:
    """Add a task to a project"""
    task = Task(
        project_id=project_id,
        title=title,
        context=context,
        estimated_minutes=estimated_minutes,
        is_next_action=is_next_action,
        status='pending'
    )

    db.add(task)
    db.commit()

    # Sync to file
    sync_database_to_file(project_id)

    return {"success": True, "task": serialize_task(task)}

@server.tool()
async def analyze_project_health(project_id: int) -> str:
    """Get AI analysis of project health"""
    project = db.query(Project).get(project_id)
    tasks = db.query(Task).filter_by(project_id=project_id).all()
    activity = get_recent_activity(project, days=30)

    prompt = f"""
    Analyze this project's health and provide recommendations:

    Project: {project.title}
    Status: {project.status}
    Momentum: {project.momentum_score}
    Days since activity: {days_since_activity(project)}

    Tasks:
    - Total: {len(tasks)}
    - Completed: {sum(1 for t in tasks if t.status == 'completed')}
    - Pending: {sum(1 for t in tasks if t.status == 'pending')}
    - In progress: {sum(1 for t in tasks if t.status == 'in_progress')}
    - Waiting: {sum(1 for t in tasks if t.status == 'waiting')}

    Recent activity:
    {format_activity(activity)}

    Provide:
    1. Health assessment (1-2 sentences)
    2. Key blockers or concerns
    3. 2-3 specific recommendations
    """

    response = await claude_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

@server.tool()
async def weekly_review() -> str:
    """Generate weekly review report"""
    # Implementation similar to analyze_project_health
    # but covering all active projects
    pass
```

### 7.2 Natural Language Interface

```python
async def process_natural_language_command(user_input: str) -> dict:
    """
    Process natural language commands via Claude

    Examples:
    - "What should I work on next?"
    - "Show me creative tasks under 30 minutes"
    - "Mark the Lund review task as complete"
    - "Create a new project for blog writing"
    - "What projects are stalled?"
    """

    # Provide Claude with available tools and current state
    system_prompt = """
    You are a project management assistant. You have access to tools for:
    - Getting next actions (get_next_actions)
    - Completing tasks (complete_task)
    - Creating projects (create_project)
    - Adding tasks (add_task)
    - Analyzing projects (analyze_project_health)

    Current state:
    {get_dashboard_summary()}

    Parse the user's request and use the appropriate tools.
    """

    response = await claude_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}],
        tools=[
            # Tool definitions from MCP server
        ]
    )

    # Execute tool calls and return results
    return process_tool_calls(response)
```

---

## 8. Deployment & Infrastructure

### 8.1 Development Setup

```bash
# Backend
cd backend
poetry install
poetry run alembic upgrade head  # Run migrations
poetry run uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
pnpm install
pnpm dev  # Runs on port 3000
```

### 8.2 Production Deployment

**Option 1: Local Desktop Application**
- Package as Electron app with embedded Python backend
- SQLite database stored in user data directory
- Auto-start file watcher on launch
- System tray integration

**Option 2: Self-Hosted Server**
- Deploy backend via Docker
- Serve frontend as static files
- Use Caddy/nginx for reverse proxy
- Optional: Tailscale for secure remote access

**Option 3: Hybrid (Recommended)**
- Backend runs locally (access to file system)
- Frontend can be web-based or Electron
- Optional cloud sync for mobile access

### 8.3 Configuration

```yaml
# config.yaml
project_tracker:
  database:
    path: ~/.project-tracker/tracker.db
    backup_frequency: daily
    backup_retention: 30

  second_brain:
    root_path: /path/to/your/second-brain
    watch_directories:
      - 10_Projects
      - 20_Areas
    sync_interval: 30  # seconds
    conflict_strategy: prompt  # prompt, file_wins, db_wins, merge

  ai:
    provider: anthropic
    model: claude-sonnet-4-5-20250929
    api_key_env: ANTHROPIC_API_KEY
    max_tokens: 2000
    features:
      unstuck_tasks: true
      project_analysis: true
      weekly_review: true
      natural_language: true

  momentum:
    activity_decay_days: 30
    stalled_threshold_days: 14
    at_risk_threshold_days: 7
    recalculate_interval: 3600  # seconds

  ui:
    theme: auto  # light, dark, auto
    default_view: dashboard
    tasks_per_page: 20
    show_completed_days: 7
```

---

## 9. Testing Strategy

### 9.1 Backend Tests

```python
# tests/test_sync.py
import pytest
from app.sync import sync_file_to_database, sync_database_to_file

def test_sync_new_project_file(tmp_path, db_session):
    # Create markdown file
    project_file = tmp_path / "test_project.md"
    project_file.write_text("""
---
project_status: active
priority: 2
---

# Test Project

## Next Actions
- [ ] Task 1
- [ ] Task 2
""")

    # Sync to database
    sync_file_to_database(project_file)

    # Assert project created
    project = db_session.query(Project).filter_by(title="Test Project").first()
    assert project is not None
    assert project.priority == 2
    assert len(project.tasks) == 2

def test_sync_task_completion_to_file(tmp_path, db_session):
    # Create project and task in DB
    project = Project(title="Test", file_path=str(tmp_path / "test.md"))
    task = Task(title="Task 1", status="pending", project=project)
    db_session.add_all([project, task])
    db_session.commit()

    # Complete task
    task.status = "completed"
    db_session.commit()

    # Sync to file
    sync_database_to_file(project.id)

    # Assert file updated
    content = (tmp_path / "test.md").read_text()
    assert "[x] Task 1" in content

# tests/test_momentum.py
def test_momentum_calculation():
    project = create_test_project()

    # New project with no activity
    assert calculate_momentum_score(project) == 0.0

    # Add recent activity
    complete_task(project, days_ago=1)
    score1 = calculate_momentum_score(project)
    assert score1 > 0.0

    # More activity increases momentum
    complete_task(project, days_ago=2)
    complete_task(project, days_ago=3)
    score2 = calculate_momentum_score(project)
    assert score2 > score1

def test_stalled_detection():
    project = create_test_project()
    project.last_activity_at = datetime.utcnow() - timedelta(days=15)

    stalled = detect_stalled_projects()
    assert project.id in [p.id for p in stalled]
```

### 9.2 Frontend Tests

```typescript
// tests/components/NextActionWidget.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { NextActionWidget } from '@/components/NextActionWidget'

describe('NextActionWidget', () => {
  it('displays next action for project', () => {
    const task = {
      id: 1,
      title: 'Review feedback',
      project: { title: 'The Lund Covenant' },
      estimatedMinutes: 45,
      context: 'creative'
    }

    render(<NextActionWidget task={task} />)

    expect(screen.getByText('Review feedback')).toBeInTheDocument()
    expect(screen.getByText('The Lund Covenant')).toBeInTheDocument()
    expect(screen.getByText('45min')).toBeInTheDocument()
  })

  it('calls onStart when start button clicked', () => {
    const onStart = jest.fn()
    const task = { id: 1, title: 'Test Task' }

    render(<NextActionWidget task={task} onStart={onStart} />)

    fireEvent.click(screen.getByText('Start'))
    expect(onStart).toHaveBeenCalledWith(1)
  })
})
```

### 9.3 Integration Tests

```python
# tests/integration/test_full_workflow.py
@pytest.mark.integration
async def test_complete_project_workflow(app_client, second_brain_path):
    """Test full workflow: create project -> add tasks -> sync -> complete"""

    # 1. Create project via API
    response = await app_client.post('/api/v1/projects', json={
        'title': 'Test Workflow',
        'description': 'Integration test project'
    })
    assert response.status_code == 201
    project_id = response.json()['id']

    # 2. Verify file created in Second Brain
    project_file = second_brain_path / '10_Projects' / 'Test_Workflow.md'
    assert project_file.exists()

    # 3. Add tasks via file edit
    content = project_file.read_text()
    content += "\n\n## Next Actions\n- [ ] Task 1\n- [ ] Task 2"
    project_file.write_text(content)

    # 4. Wait for file sync
    await asyncio.sleep(2)

    # 5. Verify tasks in database
    response = await app_client.get(f'/api/v1/projects/{project_id}')
    tasks = response.json()['tasks']
    assert len(tasks) == 2

    # 6. Complete task via API
    task_id = tasks[0]['id']
    response = await app_client.post(f'/api/v1/tasks/{task_id}/complete')
    assert response.status_code == 200

    # 7. Verify file updated
    await asyncio.sleep(1)
    content = project_file.read_text()
    assert '[x] Task 1' in content
```

---

## 10. Security & Privacy

### 10.1 Data Security

- **Local-First**: All data stored locally by default
- **Encryption**: Optional database encryption at rest
- **Backups**: Automated daily backups with rotation
- **API Authentication**: JWT tokens for API access
- **File Permissions**: Respect OS file permissions

### 10.2 Privacy Considerations

- **No Cloud by Default**: All processing happens locally
- **AI Opt-In**: AI features require explicit enablement
- **API Key Storage**: Secure keychain/credential storage
- **Audit Log**: Track all data access and modifications
- **Export/Delete**: Easy data export and complete deletion

---

## 11. Performance Requirements

### 11.1 Response Time Targets

- Dashboard load: < 500ms
- Next action query: < 200ms
- Task creation: < 100ms
- File sync: < 2s for typical project file
- Full sync: < 30s for 100 projects

### 11.2 Scalability

- Support 500+ projects
- 10,000+ tasks
- 100,000+ activity log entries
- Real-time updates for 10+ concurrent clients
- File watching for 1000+ files

### 11.3 Optimization Strategies

- Database indexes on frequent queries
- Lazy loading for project lists
- Virtual scrolling for long lists
- Debounced file watching
- Background momentum calculation
- Cached dashboard queries
- WebSocket for real-time updates only

---

## 12. Migration & Onboarding

### 12.1 Initial Setup Wizard

1. **Welcome**: Introduce GTD concepts and app features
2. **Configure Second Brain**: Point to root directory
3. **Scan Existing Projects**: Import from file structure
4. **Define Areas**: Map to 20_Areas folders
5. **Set Contexts**: Customize context tags
6. **AI Setup** (Optional): Configure Claude API
7. **Review Settings**: Confirm configuration

### 12.2 Project Import

```python
async def import_existing_projects(root_path: Path):
    """
    Scan Second Brain and import existing projects
    """
    projects_dir = root_path / "10_Projects"

    for project_dir in projects_dir.glob("**/"):
        # Look for markdown files
        for md_file in project_dir.glob("*.md"):
            try:
                # Parse and import
                project = parse_project_file(md_file)
                db.add(project)

                # Extract tasks
                tasks = extract_tasks(md_file)
                for task in tasks:
                    db.add(task)

                # Calculate initial momentum
                project.momentum_score = calculate_momentum_score(project)

            except Exception as e:
                log_import_error(md_file, e)

    db.commit()
```

### 12.3 Tutorial & Help

- Interactive tutorial for first-time users
- Contextual help tooltips
- GTD methodology guide
- Video walkthroughs
- Keyboard shortcuts cheat sheet

---

## 13. Future Enhancements (v2.0+)

### Phase 2 Features
- Mobile app (React Native)
- Voice capture integration
- Calendar integration (Google Cal, Outlook)
- Email integration (process emails to inbox)
- Collaboration features (shared projects)
- Time tracking and reporting
- Habit tracking
- Goal decomposition wizard
- Advanced analytics and insights

### Phase 3 Features
- Multi-user support
- Team dashboards
- Project templates marketplace
- Integrations (Zapier, IFTTT)
- Advanced AI features (predictive scheduling, automatic task breakdown)
- Mind mapping view
- Gantt chart view
- Resource allocation

---

## 14. Documentation Plan

### 14.1 User Documentation
- Getting Started Guide
- GTD Methodology Overview
- Feature Walkthroughs
- Troubleshooting Guide
- FAQ
- Video Tutorials
- Keyboard Shortcuts

### 14.2 Developer Documentation
- Architecture Overview
- API Reference
- Database Schema
- Sync Protocol
- Contributing Guide
- Extension Development
- Deployment Guide

---

## 15. Success Metrics

### Key Performance Indicators

**Usage Metrics:**
- Daily active usage rate
- Tasks completed per day
- Projects active vs. stalled ratio
- Time to complete tasks
- Weekly review completion rate

**System Health:**
- Sync success rate (target: >99%)
- API response times
- Error rates
- Database size growth
- File conflict frequency

**User Satisfaction:**
- Feature usage patterns
- Momentum score trends
- Project completion rates
- User feedback sentiment

---

## Appendix A: Glossary

- **Next Action**: The very next physical, visible activity required to move a project forward (GTD)
- **Momentum Score**: Calculated metric (0-1) indicating project activity level
- **Unstuck Task**: Minimal viable action to restart a stalled project
- **Context**: Situation/location/tool required for a task (@computer, @home, etc.)
- **Horizon**: GTD level of focus (runway, projects, areas, goals, vision, purpose)
- **Someday/Maybe**: Projects you might do in the future but not committed to now
- **Waiting For**: Items dependent on someone/something else
- **Two-Minute Rule**: If it takes less than 2 minutes, do it immediately (GTD)
- **PARA**: Projects, Areas, Resources, Archives organizational method

---

## Appendix B: Example Workflows

### Weekly Review Workflow
1. **Clear Inbox**: Process all captured items
2. **Review Projects**: Check each active project
3. **Identify Next Actions**: Ensure each project has a next action
4. **Update Stalled**: Address stalled projects with unstuck tasks
5. **Check Waiting Fors**: Follow up on delegated items
6. **Review Calendar**: Look ahead 2 weeks
7. **Review Someday/Maybe**: Promote any to active projects
8. **Sync Files**: Ensure all changes synced to Second Brain

### Daily Startup Workflow
1. **View Dashboard**: See today's priorities
2. **Check Momentum**: Review project health
3. **Select Top 3**: Choose today's critical tasks
4. **Set Context**: Filter by current energy/location
5. **Start First Task**: Begin work
6. **Quick Capture**: Add new items to inbox as they arise

---

**Document Status**: Draft v1.0 - Ready for Review
**Next Steps**: Technical review, user feedback, prototype development
**Estimated Implementation**: 8-12 weeks for MVP

