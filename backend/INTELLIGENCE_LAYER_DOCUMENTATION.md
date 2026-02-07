# Intelligence Layer Documentation

## Overview

The Intelligence Layer provides AI-powered project management features including momentum tracking, stalled project detection, automated task generation, and weekly review automation.

## Features

- ✅ **Momentum Scoring**: Multi-factor algorithm (0.0-1.0 scale)
- ✅ **Stalled Detection**: Automatic identification of inactive projects
- ✅ **Unstuck Tasks**: AI-generated minimal viable tasks to restart momentum
- ✅ **Project Health**: Comprehensive health summaries with recommendations
- ✅ **Weekly Review**: GTD-style weekly review automation
- ✅ **AI Integration**: Optional Claude API integration for enhanced suggestions

## Momentum Calculation

### Algorithm

Momentum scores are calculated on a 0.0 to 1.0 scale using four factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Recent Activity | 40% | Days since last activity (decay over 30 days) |
| Completion Rate | 30% | Tasks completed in last 7 days |
| Next Action | 20% | Has clear next action defined |
| Activity Frequency | 10% | Number of activities in last 14 days |

### Score Interpretation

| Score | Status | Description |
|-------|--------|-------------|
| 0.0-0.2 | Weak/Stalled | Project needs immediate attention |
| 0.2-0.4 | Low | Project at risk of stalling |
| 0.4-0.7 | Moderate | Project progressing steadily |
| 0.7-1.0 | Strong | Project has excellent momentum |

### Calculation Example

```python
# Factor 1: Recent Activity (40%)
days_since = (now - project.last_activity_at).days
activity_score = max(0, 1 - (days_since / 30))  # Decay over 30 days
score += activity_score * 0.4

# Factor 2: Completion Rate (30%)
recent_tasks = tasks_created_in_last_7_days
completed = tasks_completed_in_last_7_days
completion_rate = completed / len(recent_tasks) if recent_tasks else 0
score += completion_rate * 0.3

# Factor 3: Next Action (20%)
has_next_action = project.has_pending_next_action
score += 0.2 if has_next_action else 0

# Factor 4: Activity Frequency (10%)
activity_count = activities_in_last_14_days
frequency_score = min(1.0, activity_count / 10)  # Cap at 10 activities
score += frequency_score * 0.1
```

## Stalled Project Detection

### Criteria

A project is marked as stalled when:
1. No activity for 14+ days (configurable via `MOMENTUM_STALLED_THRESHOLD_DAYS`)
2. Automatically tracked via `stalled_since` timestamp
3. Momentum score typically < 0.2

### Auto-Unstalling

Projects are automatically unstalled when:
- Activity resumes (task created, completed, or project updated)
- Days since activity < threshold
- `stalled_since` is cleared and logged

## Unstuck Tasks

### Purpose

Minimal viable tasks (5-15 minutes) designed to restart momentum on stalled projects.

### Characteristics

- **Duration**: 5-15 minutes estimated
- **Energy**: Low energy requirement
- **Context**: "quick_win" context
- **Priority**: High (1)
- **Flags**: `is_next_action=True`, `is_unstuck_task=True`

### Generation Methods

#### 1. Non-AI Generation (Fallback)

Rule-based suggestions based on project state:

```python
if not pending_tasks:
    return f"Review project status and define next steps for {project.title}"

if not any(t.is_next_action for t in pending_tasks):
    return f"Choose the next action from {len(pending_tasks)} pending tasks"

days_stalled = (now - project.stalled_since).days
return f"Review project after {days_stalled} days and update status"
```

#### 2. AI Generation (Claude API)

Context-aware task generation using Claude API:

**Context Provided:**
- Project title, description, area
- Current phase
- Recent activity history (last 5 actions)
- Pending tasks (up to 10)
- Recently completed tasks (last 5)
- Days stalled
- Momentum score

**Prompt Requirements:**
1. Concrete, physical action (not "review" or "think")
2. Achievable in 5-15 minutes
3. Creates visible progress
4. Naturally leads to next step
5. Requires low energy/willpower
6. Specific enough to do immediately

**Example AI-Generated Tasks:**
- "Open project file and read first 3 pages"
- "Send 2-sentence email to check on editor status"
- "Create bullet list of 5 potential next steps"
- "Set 15-minute timer and write opening paragraph"
- "Make phone call to schedule follow-up meeting"

## Project Health Summary

### Components

```json
{
  "project_id": 42,
  "title": "The Lund Covenant",
  "momentum_score": 0.65,
  "health_status": "moderate",
  "days_since_activity": 3,
  "is_stalled": false,
  "stalled_since": null,
  "tasks": {
    "total": 25,
    "completed": 18,
    "pending": 5,
    "in_progress": 2,
    "waiting": 0,
    "completion_percentage": 72.0
  },
  "next_actions_count": 1,
  "recent_activity_count": 8,
  "recommendations": [
    "Project healthy - keep up the momentum!"
  ]
}
```

### Health Status

| Status | Condition |
|--------|-----------|
| `stalled` | Project marked as stalled |
| `at_risk` | No activity for 7+ days |
| `strong` | Momentum score > 0.7 |
| `moderate` | Momentum score > 0.4 |
| `weak` | Momentum score ≤ 0.4 |

### Recommendations

Auto-generated based on project state:

- **Stalled**: "Project is stalled - create an unstuck task to restart momentum"
- **At Risk**: "No activity for X days - schedule review"
- **No Next Action**: "No next action defined - choose the very next physical action"
- **Too Many Next Actions**: "Too many next actions - focus on one primary next action"
- **Low Momentum**: "Low momentum - consider 15-minute quick win to build momentum"

## Weekly Review

### GTD Weekly Review Data

Provides data for weekly review process:

```json
{
  "review_date": "2026-01-21T10:30:00Z",
  "active_projects_count": 15,
  "projects_needing_review": 3,
  "projects_without_next_action": 2,
  "tasks_completed_this_week": 42,
  "projects_needing_review_details": [
    {
      "id": 5,
      "title": "Winter Fire, Summer Ash",
      "days_since_activity": 10,
      "is_stalled": false
    }
  ],
  "projects_without_next_action_details": [
    {
      "id": 8,
      "title": "Proactive Assistant"
    }
  ]
}
```

### Review Criteria

**Projects Needing Review:**
- Stalled projects (14+ days inactive)
- At-risk projects (7+ days inactive)

**Projects Without Next Action:**
- Active projects with pending tasks but no next action defined

## API Endpoints

### Momentum

#### `POST /api/v1/intelligence/momentum/update`

Update momentum scores for all active projects.

**Response:**
```json
{
  "success": true,
  "message": "Updated 15 projects",
  "stats": {
    "updated": 15,
    "stalled_detected": 2,
    "unstalled": 1
  }
}
```

#### `GET /api/v1/intelligence/momentum/{project_id}`

Calculate momentum score for specific project.

**Response:**
```json
0.65
```

### Health

#### `GET /api/v1/intelligence/health/{project_id}`

Get comprehensive health summary.

**Response:** See Project Health Summary above.

### Stalled Projects

#### `GET /api/v1/intelligence/stalled`

Get all stalled projects.

**Response:**
```json
[
  {
    "id": 5,
    "title": "Winter Fire, Summer Ash",
    "momentum_score": 0.15,
    "stalled_since": "2026-01-07T12:00:00Z",
    "days_stalled": 14
  }
]
```

### Unstuck Tasks

#### `POST /api/v1/intelligence/unstuck/{project_id}?use_ai=true`

Create unstuck task for stalled project.

**Query Parameters:**
- `use_ai` (boolean): Use AI generation (default: true)

**Requirements for AI:**
- `AI_FEATURES_ENABLED=true`
- `ANTHROPIC_API_KEY` configured

**Response:**
```json
{
  "id": 123,
  "project_id": 5,
  "title": "Open manuscript file and read first 3 pages",
  "status": "pending",
  "is_next_action": true,
  "is_unstuck_task": true,
  "estimated_minutes": 10,
  "context": "quick_win",
  "energy_level": "low",
  "priority": 1
}
```

### Weekly Review

#### `GET /api/v1/intelligence/weekly-review`

Generate weekly review data.

**Response:** See Weekly Review section above.

### AI Features (Optional)

#### `POST /api/v1/intelligence/ai/analyze/{project_id}`

AI-powered project health analysis.

**Requirements:**
- `AI_FEATURES_ENABLED=true`
- `ANTHROPIC_API_KEY` configured

**Response:**
```json
{
  "analysis": "The Lund Covenant is in the submission phase with moderate momentum. Recent activity shows consistent query tracking, but no new submissions in the past week.",
  "recommendations": [
    "Schedule 30 minutes to research 5 new agents in target genre",
    "Review and update query letter based on recent feedback",
    "Set up tracking system for follow-up dates on pending queries"
  ]
}
```

#### `POST /api/v1/intelligence/ai/suggest-next-action/{project_id}`

AI-powered next action suggestion for active projects.

**Requirements:**
- `AI_FEATURES_ENABLED=true`
- `ANTHROPIC_API_KEY` configured

**Response:**
```json
{
  "suggestion": "Research 3 literary agents specializing in historical fiction and add to query tracker",
  "ai_generated": true
}
```

## Configuration

### Environment Variables

```env
# AI Integration
ANTHROPIC_API_KEY=your_api_key_here
AI_MODEL=claude-sonnet-4-5-20250929
AI_MAX_TOKENS=2000
AI_FEATURES_ENABLED=true

# Momentum Settings
MOMENTUM_ACTIVITY_DECAY_DAYS=30
MOMENTUM_STALLED_THRESHOLD_DAYS=14
MOMENTUM_AT_RISK_THRESHOLD_DAYS=7
MOMENTUM_RECALCULATE_INTERVAL=3600
```

### Momentum Thresholds

| Setting | Default | Description |
|---------|---------|-------------|
| `MOMENTUM_ACTIVITY_DECAY_DAYS` | 30 | Days for activity score to decay to 0 |
| `MOMENTUM_STALLED_THRESHOLD_DAYS` | 14 | Days before project marked as stalled |
| `MOMENTUM_AT_RISK_THRESHOLD_DAYS` | 7 | Days before project considered at risk |
| `MOMENTUM_RECALCULATE_INTERVAL` | 3600 | Seconds between automatic recalculations |

## Usage Examples

### Update All Momentum Scores

```bash
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update
```

### Get Project Health

```bash
curl http://localhost:8000/api/v1/intelligence/health/42
```

### Generate Unstuck Task (AI)

```bash
curl -X POST "http://localhost:8000/api/v1/intelligence/unstuck/5?use_ai=true"
```

### Generate Unstuck Task (Non-AI)

```bash
curl -X POST "http://localhost:8000/api/v1/intelligence/unstuck/5?use_ai=false"
```

### Get Weekly Review

```bash
curl http://localhost:8000/api/v1/intelligence/weekly-review
```

### AI Project Analysis

```bash
curl -X POST http://localhost:8000/api/v1/intelligence/ai/analyze/42
```

## Programmatic Usage

### Python Example

```python
from app.services.intelligence_service import IntelligenceService
from app.services.ai_service import AIService
from app.core.database import SessionLocal

db = SessionLocal()

# Update momentum scores
stats = IntelligenceService.update_all_momentum_scores(db)
print(f"Updated: {stats['updated']}, Stalled: {stats['stalled_detected']}")

# Get project health
project = db.get(Project, 42)
health = IntelligenceService.get_project_health_summary(db, project)
print(f"Status: {health['health_status']}, Score: {health['momentum_score']}")

# Create unstuck task (non-AI)
unstuck_task = IntelligenceService.create_unstuck_task(db, project, use_ai=False)
print(f"Created: {unstuck_task.title}")

# Create unstuck task (AI)
unstuck_task = IntelligenceService.create_unstuck_task(db, project, use_ai=True)
print(f"AI Generated: {unstuck_task.title}")

# AI project analysis
ai_service = AIService()
analysis = ai_service.analyze_project_health(db, project)
print(f"Analysis: {analysis['analysis']}")
for rec in analysis['recommendations']:
    print(f"- {rec}")

# Weekly review
review = IntelligenceService.get_weekly_review_data(db)
print(f"Active: {review['active_projects_count']}")
print(f"Needs Review: {review['projects_needing_review']}")
```

## Best Practices

### 1. Regular Momentum Updates

Run momentum updates regularly (hourly recommended):

```bash
# Via cron job
0 * * * * curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update
```

Or enable automatic updates via scheduled task in application.

### 2. Weekly Review Workflow

1. Get weekly review data
2. Review stalled projects
3. Create unstuck tasks for stalled projects
4. Review projects without next actions
5. Define next actions

```bash
# Get review data
curl http://localhost:8000/api/v1/intelligence/weekly-review > review.json

# For each stalled project, create unstuck task
curl -X POST "http://localhost:8000/api/v1/intelligence/unstuck/5?use_ai=true"
```

### 3. AI vs Non-AI Generation

**Use AI when:**
- You have API key configured
- Project has rich context (description, recent activity)
- You want context-aware suggestions
- Cost is acceptable

**Use Non-AI when:**
- No API key available
- Simple fallback needed
- Minimizing external dependencies
- Cost is a concern

### 4. Health Monitoring

Check project health regularly:

```python
# Check all active projects
projects = db.execute(
    select(Project).where(Project.status == "active")
).scalars().all()

for project in projects:
    health = IntelligenceService.get_project_health_summary(db, project)
    if health['health_status'] in ['stalled', 'at_risk', 'weak']:
        print(f"⚠️  {project.title}: {health['health_status']}")
        print(f"   Recommendations: {health['recommendations']}")
```

## Troubleshooting

### Momentum Scores Not Updating

**Check:**
1. Last activity timestamp is being updated
2. Tasks are being created/completed
3. Momentum calculation interval setting

**Solution:**
```bash
# Force update
curl -X POST http://localhost:8000/api/v1/intelligence/momentum/update
```

### AI Features Not Working

**Check:**
1. `AI_FEATURES_ENABLED=true` in .env
2. `ANTHROPIC_API_KEY` is valid
3. API key has sufficient credits
4. Network connectivity to Anthropic API

**Error Messages:**
- "AI features not enabled" → Set `AI_FEATURES_ENABLED=true`
- "Anthropic API key not configured" → Set `ANTHROPIC_API_KEY`
- API errors → Check Anthropic console for status

### Stalled Detection Too Sensitive

**Adjust threshold:**
```env
# Increase to 21 days
MOMENTUM_STALLED_THRESHOLD_DAYS=21
```

### Too Many Unstuck Tasks

Unstuck tasks are auto-generated by system. To prevent:
1. Review and complete existing unstuck tasks
2. Update project activity regularly
3. Increase stalled threshold

## Performance

### Momentum Calculation

- **Per Project**: ~50-100ms
- **Batch Update (100 projects)**: ~5-10 seconds
- **Database Queries**: 4-5 per project

### AI Generation

- **Unstuck Task**: ~1-3 seconds
- **Project Analysis**: ~2-5 seconds
- **API Calls**: 1 per request
- **Token Usage**: ~200-500 tokens per request

### Optimization Tips

1. **Cache momentum scores** - Update hourly, not per request
2. **Batch operations** - Update all projects at once
3. **Limit AI calls** - Use for important projects only
4. **Index properly** - Ensure database indexes on key fields

## Integration with Sync Engine

Momentum and intelligence features integrate seamlessly with the sync engine:

1. **File → Database**: Activity timestamps updated on sync
2. **Database → File**: Momentum score synced to frontmatter
3. **Unstuck Tasks**: Created in database and synced to file
4. **Activity Logging**: All sync operations logged for momentum

---

**Last Updated:** 2026-01-21
**Version:** 1.0
