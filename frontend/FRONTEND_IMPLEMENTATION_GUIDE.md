# Frontend Implementation Guide

## Overview

The frontend for the Project Tracker is a React + TypeScript application built with Vite, Tailwind CSS, and React Query for state management. This guide provides the foundation and structure for completing the implementation.

## Current Status

### ✅ Completed

1. **Project Setup**
   - Vite configuration with React + TypeScript
   - Tailwind CSS configured with custom colors
   - Path aliases (@/) configured
   - PostCSS and Autoprefixer setup

2. **TypeScript Types** (`src/types/index.ts`)
   - Complete type definitions matching backend schemas
   - Project, Task, Area, Phase types
   - Intelligence types (Health, WeeklyReview, etc.)
   - API response types
   - Filter types

3. **API Client** (`src/services/api.ts`)
   - Complete APIClient class with all endpoints
   - Projects CRUD + health
   - Tasks CRUD + actions
   - Next Actions with filters
   - Intelligence features (momentum, stalled, weekly review)
   - AI features (analyze, suggest)
   - Sync operations

4. **Utilities**
   - `utils/momentum.ts` - Momentum scoring utilities
   - `utils/date.ts` - Date formatting functions

5. **React Query Hooks**
   - `hooks/useProjects.ts` - Project queries and mutations
   - `hooks/useTasks.ts` - Task queries and mutations
   - `hooks/useNextActions.ts` - Next actions queries
   - `hooks/useIntelligence.ts` - Intelligence queries

6. **Styling**
   - Base CSS with Tailwind
   - Component utility classes
   - Custom buttons, cards, badges

### 🚧 To Implement

The following components and pages need to be built. This guide provides structure and key implementation details.

## Component Architecture

```
src/
├── components/
│   ├── layout/
│   │   ├── Layout.tsx           # Main layout wrapper
│   │   ├── Sidebar.tsx          # Navigation sidebar
│   │   └── Header.tsx           # Top header with user info
│   ├── projects/
│   │   ├── ProjectCard.tsx      # Project card with momentum
│   │   ├── ProjectList.tsx      # List of projects
│   │   ├── ProjectHealth.tsx    # Health indicator
│   │   └── MomentumBar.tsx      # Momentum visualization
│   ├── tasks/
│   │   ├── TaskCard.tsx         # Individual task
│   │   ├── TaskList.tsx         # Task list
│   │   └── QuickActions.tsx     # Quick task actions
│   ├── intelligence/
│   │   ├── StalledAlert.tsx     # Stalled projects alert
│   │   ├── WeeklyReview.tsx     # Weekly review component
│   │   └── AIInsights.tsx       # AI-powered insights
│   └── common/
│       ├── Loading.tsx          # Loading spinner
│       ├── Error.tsx            # Error display
│       └── Modal.tsx            # Modal dialog
├── pages/
│   ├── Dashboard.tsx            # Main dashboard
│   ├── Projects.tsx             # Projects list view
│   ├── ProjectDetail.tsx        # Single project view
│   ├── NextActions.tsx          # Next actions view
│   ├── WeeklyReviewPage.tsx    # Weekly review page
│   └── Settings.tsx             # Settings page
├── App.tsx                      # Main app component
└── main.tsx                     # Entry point
```

## Key Components to Build

### 1. Layout Component

**File**: `src/components/layout/Layout.tsx`

**Purpose**: Main application layout with sidebar navigation

**Key Features**:
- Responsive sidebar (collapsible on mobile)
- Navigation to Dashboard, Projects, Next Actions, Weekly Review
- Active route highlighting
- User profile section

**Implementation Hints**:
```typescript
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Home, FolderKanban, ListTodo, CalendarCheck, Settings } from 'lucide-react';

export function Layout() {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Projects', href: '/projects', icon: FolderKanban },
    { name: 'Next Actions', href: '/next-actions', icon: ListTodo },
    { name: 'Weekly Review', href: '/weekly-review', icon: CalendarCheck },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-64 bg-white border-r border-gray-200">
        {/* Sidebar navigation */}
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
```

### 2. Dashboard Page

**File**: `src/pages/Dashboard.tsx`

**Purpose**: Main landing page with overview

**Key Features**:
- Summary statistics (active projects, pending tasks, momentum avg)
- Stalled projects alert
- Top 5 next actions
- Momentum chart
- Quick wins section

**Implementation Hints**:
```typescript
import { useProjects, useStalledProjects, useUpdateMomentum } from '@/hooks/useProjects';
import { useNextActions } from '@/hooks/useNextActions';

export function Dashboard() {
  const { data: projects } = useProjects({ status: 'active' });
  const { data: stalled } = useStalledProjects();
  const { data: nextActions } = useNextActions({ limit: 5 });
  const updateMomentum = useUpdateMomentum();

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <button
          onClick={() => updateMomentum.mutate()}
          className="btn btn-secondary btn-sm mt-2"
        >
          Update Momentum
        </button>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Stats cards */}
        <StatsCard
          title="Active Projects"
          value={projects?.total || 0}
        />

        {/* Stalled projects alert */}
        {stalled && stalled.length > 0 && (
          <StalledAlert projects={stalled} />
        )}

        {/* Next actions list */}
        <NextActionsList actions={nextActions || []} />

        {/* Momentum chart */}
        <MomentumChart projects={projects?.projects || []} />
      </div>
    </div>
  );
}
```

### 3. Project Card Component

**File**: `src/components/projects/ProjectCard.tsx`

**Purpose**: Display project with momentum visualization

**Key Features**:
- Project title and description
- Momentum bar with color coding
- Last activity timestamp
- Task completion percentage
- Quick actions (view, complete, sync)

**Implementation Hints**:
```typescript
import { Project } from '@/types';
import { MomentumBar } from './MomentumBar';
import { formatRelativeTime } from '@/utils/date';

export function ProjectCard({ project }: { project: Project }) {
  const completionPct = project.tasks
    ? (project.tasks.filter(t => t.status === 'completed').length / project.tasks.length) * 100
    : 0;

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold">{project.title}</h3>
          {project.area && (
            <span className="badge badge-blue text-xs">{project.area.name}</span>
          )}
        </div>
        {project.stalled_since && (
          <span className="badge badge-red">Stalled</span>
        )}
      </div>

      <MomentumBar score={project.momentum_score} />

      <div className="mt-4 text-sm text-gray-600">
        <div>Last activity: {formatRelativeTime(project.last_activity_at)}</div>
        <div>Completion: {completionPct.toFixed(0)}%</div>
      </div>

      <div className="mt-4 flex gap-2">
        <Link to={`/projects/${project.id}`} className="btn btn-sm btn-primary">
          View
        </Link>
      </div>
    </div>
  );
}
```

### 4. Momentum Bar Component

**File**: `src/components/projects/MomentumBar.tsx`

**Purpose**: Visual representation of momentum score

**Implementation Hints**:
```typescript
import { getMomentumColor, getMomentumLabel, formatMomentumScore } from '@/utils/momentum';

export function MomentumBar({ score }: { score: number }) {
  const color = getMomentumColor(score);
  const label = getMomentumLabel(score);
  const percentage = formatMomentumScore(score);

  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm font-medium text-gray-700">Momentum</span>
        <span className="text-sm font-semibold" style={{ color }}>
          {label} ({percentage})
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-300"
          style={{
            width: `${score * 100}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}
```

### 5. Next Actions Page

**File**: `src/pages/NextActions.tsx`

**Purpose**: Prioritized list of next actions

**Key Features**:
- Filter by context, energy, time available
- Priority tiers visualization
- Quick complete action
- Start task button
- Reason for prioritization

**Implementation Hints**:
```typescript
import { useNextActions } from '@/hooks/useNextActions';
import { useCompleteTask, useStartTask } from '@/hooks/useTasks';
import { useState } from 'react';

export function NextActions() {
  const [context, setContext] = useState('');
  const [energy, setEnergy] = useState('');
  const [timeAvailable, setTimeAvailable] = useState<number>();

  const { data: actions, isLoading } = useNextActions({
    context: context || undefined,
    energy_level: energy || undefined,
    time_available: timeAvailable,
  });

  const completeTask = useCompleteTask();
  const startTask = useStartTask();

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Next Actions</h1>
        <p className="text-gray-600">Prioritized tasks ready to do now</p>
      </header>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="label">Context</label>
            <select
              value={context}
              onChange={(e) => setContext(e.target.value)}
              className="input"
            >
              <option value="">All</option>
              <option value="work">Work</option>
              <option value="home">Home</option>
              <option value="errands">Errands</option>
            </select>
          </div>
          <div>
            <label className="label">Energy Level</label>
            <select
              value={energy}
              onChange={(e) => setEnergy(e.target.value)}
              className="input"
            >
              <option value="">All</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div>
            <label className="label">Time Available (min)</label>
            <input
              type="number"
              value={timeAvailable || ''}
              onChange={(e) => setTimeAvailable(Number(e.target.value))}
              className="input"
              placeholder="Any"
            />
          </div>
        </div>
      </div>

      {/* Actions list */}
      <div className="space-y-4">
        {actions?.map((action) => (
          <div key={action.task.id} className="card">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="badge badge-blue">Tier {action.priority_tier}</span>
                  {action.task.is_unstuck_task && (
                    <span className="badge badge-yellow">Unstuck Task</span>
                  )}
                </div>
                <h3 className="text-lg font-semibold">{action.task.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{action.project.title}</p>
                <p className="text-sm text-gray-500 mt-2">{action.reason}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => startTask.mutate(action.task.id)}
                  className="btn btn-sm btn-secondary"
                >
                  Start
                </button>
                <button
                  onClick={() => completeTask.mutate(action.task.id)}
                  className="btn btn-sm btn-primary"
                >
                  Complete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 6. Weekly Review Page

**File**: `src/pages/WeeklyReviewPage.tsx`

**Purpose**: GTD weekly review interface

**Key Features**:
- Projects needing review list
- Projects without next actions
- Completed tasks this week
- Generate unstuck tasks button
- Mark review complete

**Implementation Hints**:
```typescript
import { useWeeklyReview } from '@/hooks/useIntelligence';
import { useCreateUnstuckTask } from '@/hooks/useProjects';

export function WeeklyReviewPage() {
  const { data: review, isLoading } = useWeeklyReview();
  const createUnstuck = useCreateUnstuckTask();

  if (isLoading) return <Loading />;

  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold">Weekly Review</h1>
        <p className="text-gray-600">
          {review?.review_date && formatDate(review.review_date)}
        </p>
      </header>

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatsCard title="Active Projects" value={review?.active_projects_count || 0} />
        <StatsCard
          title="Needs Review"
          value={review?.projects_needing_review || 0}
          variant="warning"
        />
        <StatsCard
          title="Without Next Action"
          value={review?.projects_without_next_action || 0}
          variant="danger"
        />
        <StatsCard
          title="Completed This Week"
          value={review?.tasks_completed_this_week || 0}
          variant="success"
        />
      </div>

      {/* Projects needing review */}
      <section className="mb-8">
        <h2 className="text-xl font-bold mb-4">Projects Needing Review</h2>
        <div className="space-y-3">
          {review?.projects_needing_review_details.map((project) => (
            <div key={project.id} className="card">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{project.title}</h3>
                  <p className="text-sm text-gray-600">
                    {project.days_since_activity} days since activity
                  </p>
                </div>
                <button
                  onClick={() => createUnstuck.mutate({
                    projectId: project.id,
                    useAI: true
                  })}
                  className="btn btn-sm btn-primary"
                >
                  Create Unstuck Task
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Projects without next actions */}
      <section>
        <h2 className="text-xl font-bold mb-4">Projects Without Next Actions</h2>
        <div className="space-y-3">
          {review?.projects_without_next_action_details.map((project) => (
            <div key={project.id} className="card">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">{project.title}</h3>
                <Link to={`/projects/${project.id}`} className="btn btn-sm btn-secondary">
                  Define Next Action
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
```

### 7. Stalled Alert Component

**File**: `src/components/intelligence/StalledAlert.tsx`

**Purpose**: Alert for stalled projects on dashboard

**Implementation Hints**:
```typescript
import { StalledProject } from '@/types';
import { AlertTriangle } from 'lucide-react';

export function StalledAlert({ projects }: { projects: StalledProject[] }) {
  if (projects.length === 0) return null;

  return (
    <div className="col-span-full bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
      <div className="flex items-start">
        <AlertTriangle className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-red-800">
            {projects.length} Stalled {projects.length === 1 ? 'Project' : 'Projects'}
          </h3>
          <p className="text-sm text-red-700 mt-1">
            These projects need attention to restart momentum
          </p>
          <ul className="mt-3 space-y-2">
            {projects.map((project) => (
              <li key={project.id} className="flex items-center justify-between">
                <span className="text-sm">{project.title}</span>
                <span className="text-xs text-red-600">
                  {project.days_stalled} days stalled
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
```

### 8. Project Health Component

**File**: `src/components/projects/ProjectHealth.tsx`

**Purpose**: Display comprehensive project health

**Implementation Hints**:
```typescript
import { useProjectHealth } from '@/hooks/useProjects';
import { getMomentumBgColor, getMomentumTextColor } from '@/utils/momentum';

export function ProjectHealth({ projectId }: { projectId: number }) {
  const { data: health, isLoading } = useProjectHealth(projectId);

  if (isLoading) return <Loading />;
  if (!health) return null;

  return (
    <div className="card">
      <h3 className="text-lg font-bold mb-4">Project Health</h3>

      <div className="space-y-4">
        {/* Health status badge */}
        <div>
          <span className={`badge ${getMomentumBgColor(health.momentum_score)}`}>
            <span className={getMomentumTextColor(health.momentum_score)}>
              {health.health_status.toUpperCase()}
            </span>
          </span>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-600">Total Tasks</div>
            <div className="text-2xl font-bold">{health.tasks.total}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Completion</div>
            <div className="text-2xl font-bold">
              {health.tasks.completion_percentage.toFixed(0)}%
            </div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Next Actions</div>
            <div className="text-2xl font-bold">{health.next_actions_count}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">Recent Activity</div>
            <div className="text-2xl font-bold">{health.recent_activity_count}</div>
          </div>
        </div>

        {/* Recommendations */}
        {health.recommendations.length > 0 && (
          <div>
            <h4 className="font-semibold mb-2">Recommendations</h4>
            <ul className="space-y-2">
              {health.recommendations.map((rec, idx) => (
                <li key={idx} className="text-sm text-gray-700 flex items-start">
                  <span className="mr-2">•</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
```

## Main App Setup

### main.tsx

```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

### App.tsx

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Projects } from './pages/Projects';
import { ProjectDetail } from './pages/ProjectDetail';
import { NextActions } from './pages/NextActions';
import { WeeklyReviewPage } from './pages/WeeklyReviewPage';
import { Settings } from './pages/Settings';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="projects" element={<Projects />} />
            <Route path="projects/:id" element={<ProjectDetail />} />
            <Route path="next-actions" element={<NextActions />} />
            <Route path="weekly-review" element={<WeeklyReviewPage />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

## Installation & Running

### Install Dependencies

```bash
cd frontend
npm install
```

### Development Server

```bash
npm run dev
```

Runs on: http://localhost:5173

### Build for Production

```bash
npm run build
```

Output: `dist/` directory

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Create `.env` file in `frontend/`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Update `src/services/api.ts` to use:

```typescript
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
```

## Design System

### Colors

- **Primary**: Blue (`primary-*` in Tailwind)
- **Momentum**:
  - Weak: Red (`#ef4444`)
  - Low: Orange (`#f97316`)
  - Moderate: Yellow (`#eab308`)
  - Strong: Green (`#22c55e`)

### Typography

- **Headings**: Bold, larger sizes
- **Body**: Gray-900
- **Secondary**: Gray-600

### Spacing

- **Page padding**: `p-8`
- **Card padding**: `p-6`
- **Gap between elements**: `gap-4` or `gap-6`

## Testing Recommendations

1. **Unit Tests**: Test utilities and hooks
2. **Component Tests**: Test individual components
3. **Integration Tests**: Test page flows
4. **E2E Tests**: Test complete workflows

## Next Steps

1. **Implement all components** from this guide
2. **Add error boundaries** for better error handling
3. **Implement loading states** throughout
4. **Add animations** with Framer Motion (optional)
5. **Implement search** functionality
6. **Add keyboard shortcuts** for power users
7. **Build mobile-responsive** views
8. **Add dark mode** support (optional)
9. **Implement notifications** system
10. **Add data visualizations** with Recharts

## Performance Optimization

- Use React.memo for expensive components
- Implement virtualization for long lists
- Code split routes with React.lazy
- Optimize images and assets
- Use production build for deployment

## Deployment

### Build

```bash
npm run build
```

### Serve with Backend

Place `dist/` contents in backend `static/` directory or configure reverse proxy.

### Nginx Example

```nginx
server {
  listen 80;
  server_name yourdomain.com;

  location / {
    root /path/to/frontend/dist;
    try_files $uri $uri/ /index.html;
  }

  location /api {
    proxy_pass http://localhost:8000;
  }
}
```

---

**Status**: Foundation Complete
**Next**: Implement components and pages from this guide
**Timeline**: 2-3 days for core features, 1 week for polish
