import { useState, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  CalendarCheck, Sparkles, Star, Clock, AlertCircle, CheckCircle2,
  FolderOpen, Inbox, Lightbulb, ListChecks, ChevronDown, ChevronUp,
  ChevronRight, FolderKanban, Layers, CheckSquare
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useWeeklyReview, useProjectReviewInsight, useCompleteWeeklyReview } from '../hooks/useIntelligence';
import { useCreateUnstuckTask } from '../hooks/useProjects';
import { useAreas, useMarkAreaReviewed } from '../hooks/useAreas';
import { useProjects } from '../hooks/useProjects';
import { Loading } from '../components/common/Loading';
import { Error } from '../components/common/Error';
import { AIReviewSummary } from '../components/intelligence/AIReviewSummary';
import { formatDate, getReviewStatus } from '../utils/date';
import type { Area, WeeklyReviewAISummary, ProjectReviewInsight } from '../types';

// Get the ISO 8601 week key for localStorage (YYYY-WXX format)
// ISO 8601: Week 1 contains the first Thursday of the year; weeks start on Monday.
function getWeekKey(): string {
  const now = new Date();
  // Copy date and set to nearest Thursday (current date + 4 - day number, with Sunday as 7)
  const d = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
  const dayNum = d.getUTCDay() || 7; // Make Sunday = 7
  d.setUTCDate(d.getUTCDate() + 4 - dayNum); // Set to Thursday of this week
  const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
  const weekNum = Math.ceil(((d.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return `${d.getUTCFullYear()}-W${String(weekNum).padStart(2, '0')}`;
}

const CHECKLIST_STORAGE_KEY = 'pt-weeklyReviewChecklist';
const REVIEW_SECTIONS_KEY = 'pt-weeklyReviewSections';

type ReviewSectionId = 'areas-overdue' | 'areas-due-soon' | 'orphan-projects' | 'projects-needing-review' | 'projects-without-next-action';

function loadCollapsedReviewSections(): Set<ReviewSectionId> {
  try {
    const stored = localStorage.getItem(REVIEW_SECTIONS_KEY);
    if (stored) {
      return new Set(JSON.parse(stored) as ReviewSectionId[]);
    }
  } catch {
    localStorage.removeItem(REVIEW_SECTIONS_KEY);
  }
  return new Set<ReviewSectionId>();
}

interface ChecklistState {
  [stepId: string]: boolean;
}

function loadChecklist(): ChecklistState {
  try {
    const stored = localStorage.getItem(CHECKLIST_STORAGE_KEY);
    if (!stored) return {};
    const data = JSON.parse(stored);
    // Only return checklist for current week
    if (data.week === getWeekKey()) {
      return data.steps || {};
    }
    return {};
  } catch {
    return {};
  }
}

function saveChecklist(steps: ChecklistState) {
  localStorage.setItem(CHECKLIST_STORAGE_KEY, JSON.stringify({
    week: getWeekKey(),
    steps,
  }));
}

export function WeeklyReviewPage() {
  const { data: review, isLoading, error } = useWeeklyReview();
  const { data: areas, isLoading: areasLoading } = useAreas();
  const { data: projectsData, isLoading: projectsLoading } = useProjects({});
  const createUnstuck = useCreateUnstuckTask();
  const markReviewed = useMarkAreaReviewed();
  const completeReview = useCompleteWeeklyReview();
  const [checklistState, setChecklistState] = useState<ChecklistState>(loadChecklist);
  const [checklistExpanded, setChecklistExpanded] = useState(true);
  const [aiSummary, setAiSummary] = useState<WeeklyReviewAISummary | null>(null);
  const projectInsight = useProjectReviewInsight();
  const [expandedInsights, setExpandedInsights] = useState<Record<number, ProjectReviewInsight>>({});
  const [pendingInsightIds, setPendingInsightIds] = useState<Set<number>>(new Set());
  const [collapsedSections, setCollapsedSections] = useState<Set<ReviewSectionId>>(loadCollapsedReviewSections);

  const toggleSection = useCallback((id: ReviewSectionId) => {
    setCollapsedSections(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      localStorage.setItem(REVIEW_SECTIONS_KEY, JSON.stringify([...next]));
      return next;
    });
  }, []);

  const toggleStep = useCallback((stepId: string) => {
    setChecklistState(prev => {
      const next = { ...prev, [stepId]: !prev[stepId] };
      saveChecklist(next);
      return next;
    });
  }, []);

  // Calculate areas due for review based on their review_frequency and last_reviewed_at
  const areaReviewData = useMemo(() => {
    if (!areas) return { overdueAreas: [], dueSoonAreas: [], allAreas: [] };

    const overdueAreas: (Area & { reviewStatus: ReturnType<typeof getReviewStatus> })[] = [];
    const dueSoonAreas: (Area & { reviewStatus: ReturnType<typeof getReviewStatus> })[] = [];

    areas.forEach((area) => {
      const reviewStatus = getReviewStatus(area.last_reviewed_at, area.review_frequency);
      const areaWithStatus = { ...area, reviewStatus };

      if (reviewStatus.status === 'overdue' || reviewStatus.status === 'never-reviewed') {
        overdueAreas.push(areaWithStatus);
      } else if (reviewStatus.status === 'due-soon') {
        dueSoonAreas.push(areaWithStatus);
      }
    });

    return { overdueAreas, dueSoonAreas, allAreas: areas };
  }, [areas]);

  // Calculate orphan projects (projects without an area)
  const orphanProjects = useMemo(() => {
    if (!projectsData?.projects) return [];
    return projectsData.projects.filter(
      (p) => !p.area_id && p.status !== 'completed' && p.status !== 'archived'
    );
  }, [projectsData]);

  const handleGetInsight = (projectId: number) => {
    if (pendingInsightIds.has(projectId)) return; // Dedup: skip if already fetching
    setPendingInsightIds((prev) => new Set(prev).add(projectId));
    projectInsight.mutate(projectId, {
      onSuccess: (data) => {
        setExpandedInsights((prev) => ({ ...prev, [projectId]: data }));
        setPendingInsightIds((prev) => { const next = new Set(prev); next.delete(projectId); return next; });
      },
      onError: () => {
        toast.error('Failed to generate project insight');
        setPendingInsightIds((prev) => { const next = new Set(prev); next.delete(projectId); return next; });
      },
    });
  };

  const handleMarkAreaReviewed = (areaId: number, areaTitle: string) => {
    markReviewed.mutate(areaId, {
      onSuccess: () => {
        toast.success(`"${areaTitle}" marked as reviewed`);
      },
      onError: (error) => {
        console.error('Failed to mark area as reviewed:', error);
        toast.error('Failed to mark area as reviewed', { id: 'area-review-error' });
      },
    });
  };

  const isPageLoading = isLoading || areasLoading || projectsLoading;
  if (isPageLoading) return <Loading fullPage />;
  if (error) return <Error message="Failed to load weekly review" fullPage />;
  if (!review) return <Error message="No review data available" fullPage />;

  // Checklist items with dynamic status
  const checklistItems = [
    {
      id: 'inbox',
      label: 'Clear Inbox to Zero',
      icon: Inbox,
      description: review.inbox_count > 0
        ? `${review.inbox_count} items need processing`
        : 'Inbox is empty',
      link: '/inbox',
      linkLabel: 'Go to Inbox',
      done: review.inbox_count === 0,
    },
    {
      id: 'active_projects',
      label: 'Review Active Projects',
      icon: FolderKanban,
      description: `${review.active_projects_count} active projects`,
      link: '/projects',
      linkLabel: 'View Projects',
      done: false,
    },
    {
      id: 'next_actions',
      label: 'Ensure Every Project Has a Next Action',
      icon: CheckSquare,
      description: review.projects_without_next_action > 0
        ? `${review.projects_without_next_action} projects missing next actions`
        : 'All projects have next actions',
      link: undefined,
      linkLabel: undefined,
      done: review.projects_without_next_action === 0,
    },
    {
      id: 'someday_maybe',
      label: 'Review Someday/Maybe List',
      icon: Lightbulb,
      description: `${review.someday_maybe_count} someday/maybe projects`,
      link: '/someday-maybe',
      linkLabel: 'View List',
      done: false,
    },
    {
      id: 'areas',
      label: 'Review Areas of Responsibility',
      icon: Layers,
      description: areaReviewData.overdueAreas.length > 0
        ? `${areaReviewData.overdueAreas.length} areas overdue for review`
        : 'All areas are current',
      link: '/areas',
      linkLabel: 'View Areas',
      done: areaReviewData.overdueAreas.length === 0,
    },
    {
      id: 'stalled',
      label: 'Address Stalled Projects',
      icon: AlertCircle,
      description: review.projects_needing_review > 0
        ? `${review.projects_needing_review} projects need attention`
        : 'No stalled projects',
      link: undefined,
      linkLabel: undefined,
      done: review.projects_needing_review === 0,
    },
  ];

  const completedSteps = checklistItems.filter(item => checklistState[item.id] || item.done).length;
  const totalSteps = checklistItems.length;
  const progressPercent = Math.round((completedSteps / totalSteps) * 100);

  return (
    <div className="p-8">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <CalendarCheck className="w-8 h-8 text-primary-600" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Weekly Review</h1>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          {formatDate(review.review_date)}
        </p>
      </header>

      {/* AI Review Co-Pilot */}
      <AIReviewSummary onSummaryGenerated={(summary) => setAiSummary(summary)} />

      {/* Review Checklist */}
      <section className="mb-8">
        <div
          className="card border-2 border-primary-200 dark:border-primary-800 bg-primary-50/50 dark:bg-primary-900/10 cursor-pointer"
          onClick={() => setChecklistExpanded(!checklistExpanded)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <ListChecks className="w-6 h-6 text-primary-600" />
              <div>
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  Weekly Review Checklist
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {completedSteps}/{totalSteps} steps complete
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Progress bar */}
              <div className="w-32 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    progressPercent === 100 ? 'bg-green-500' : 'bg-primary-500'
                  }`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400 w-10">
                {progressPercent}%
              </span>
              {checklistExpanded ? (
                <ChevronUp className="w-5 h-5 text-gray-400" />
              ) : (
                <ChevronDown className="w-5 h-5 text-gray-400" />
              )}
            </div>
          </div>
        </div>

        {checklistExpanded && (
          <div className="mt-3 space-y-2">
            {checklistItems.map((item) => {
              const Icon = item.icon;
              const checked = checklistState[item.id] || item.done;
              return (
                <div
                  key={item.id}
                  className={`card flex items-center gap-4 transition-all ${
                    checked ? 'bg-green-50/50 dark:bg-green-900/10 border-green-200 dark:border-green-800' : ''
                  }`}
                >
                  <button
                    onClick={() => toggleStep(item.id)}
                    className={`w-6 h-6 rounded-md border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                      checked
                        ? 'bg-green-500 border-green-500 text-white'
                        : 'border-gray-300 dark:border-gray-600 hover:border-primary-500'
                    }`}
                  >
                    {checked && <CheckCircle2 className="w-4 h-4" />}
                  </button>
                  <Icon className={`w-5 h-5 flex-shrink-0 ${checked ? 'text-green-600' : 'text-gray-400'}`} />
                  <div className="flex-1">
                    <p className={`font-medium ${
                      checked ? 'text-green-800 dark:text-green-300 line-through' : 'text-gray-900 dark:text-gray-100'
                    }`}>
                      {item.label}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{item.description}</p>
                  </div>
                  {item.link && (
                    <Link
                      to={item.link}
                      className="btn btn-sm btn-secondary flex-shrink-0"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {item.linkLabel}
                    </Link>
                  )}
                </div>
              );
            })}

            {/* Complete Weekly Review button */}
            {completedSteps === totalSteps && !completeReview.isSuccess && (
              <div className="mt-4 text-center">
                <button
                  onClick={() => {
                    completeReview.mutate(
                      { aiSummary: aiSummary ? JSON.stringify(aiSummary) : undefined },
                      {
                        onSuccess: () => toast.success('Weekly review completed!'),
                        onError: () => toast.error('Failed to save review completion'),
                      }
                    );
                  }}
                  disabled={completeReview.isPending}
                  className="btn btn-primary px-6 py-2.5 flex items-center gap-2 mx-auto"
                >
                  <CalendarCheck className="w-4 h-4" />
                  {completeReview.isPending ? 'Saving...' : 'Complete Weekly Review'}
                </button>
              </div>
            )}
            {completeReview.isSuccess && (
              <div className="mt-4 text-center text-green-600 dark:text-green-400 font-medium flex items-center justify-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                Review completed and recorded!
              </div>
            )}
          </div>
        )}
      </section>

      {/* Summary Stats - Projects */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <StatCard
          title="Active Projects"
          value={review.active_projects_count}
          variant="blue"
        />
        <StatCard
          title="Projects Need Review"
          value={review.projects_needing_review}
          variant="yellow"
        />
        <StatCard
          title="Without Next Action"
          value={review.projects_without_next_action}
          variant="red"
        />
        <StatCard
          title="Completed This Week"
          value={review.tasks_completed_this_week}
          variant="green"
        />
      </div>

      {/* Summary Stats - Areas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          title="Total Areas"
          value={areaReviewData.allAreas.length}
          variant="blue"
        />
        <StatCard
          title="Areas Overdue"
          value={areaReviewData.overdueAreas.length}
          variant="red"
        />
        <StatCard
          title="Areas Due Soon"
          value={areaReviewData.dueSoonAreas.length}
          variant="yellow"
        />
        <StatCard
          title="Unassigned Projects"
          value={orphanProjects.length}
          variant={orphanProjects.length > 0 ? 'yellow' : 'green'}
        />
      </div>

      {/* Areas Due for Review - Overdue */}
      {areaReviewData.overdueAreas.length > 0 && (
        <section className="mb-8">
          <button
            type="button"
            onClick={() => toggleSection('areas-overdue')}
            aria-expanded={!collapsedSections.has('areas-overdue')}
            className="flex items-center gap-2 mb-4 w-full text-left"
          >
            {collapsedSections.has('areas-overdue') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <AlertCircle className="w-6 h-6 text-red-600" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Areas Overdue for Review</h2>
            <span className="badge badge-red ml-2">{areaReviewData.overdueAreas.length}</span>
          </button>
          {!collapsedSections.has('areas-overdue') && (<>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            These areas haven't been reviewed within their scheduled frequency
          </p>
          <div className="space-y-3">
            {areaReviewData.overdueAreas.map((area) => (
              <div key={area.id} className="card hover:shadow-md transition-shadow border-l-4 border-l-red-500">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-lg">{area.title}</h3>
                      <span className="badge badge-gray text-xs capitalize">{area.review_frequency}</span>
                    </div>
                    <p className="text-sm text-red-600 mb-2">
                      <Clock className="w-3 h-3 inline mr-1" />
                      {area.reviewStatus.text}
                    </p>
                    {area.standard_of_excellence && (
                      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md p-3 mt-2">
                        <div className="flex items-start gap-2">
                          <Star className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="text-xs font-medium text-amber-800 dark:text-amber-300 mb-1">
                              Are you maintaining this standard?
                            </p>
                            <p className="text-sm text-amber-700 dark:text-amber-200">{area.standard_of_excellence}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Link
                      to={`/areas/${area.id}`}
                      className="btn btn-sm btn-secondary"
                    >
                      Review
                    </Link>
                    <button
                      onClick={() => handleMarkAreaReviewed(area.id, area.title)}
                      disabled={markReviewed.isPending}
                      className="btn btn-sm btn-primary flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Mark Reviewed
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          </>)}
        </section>
      )}

      {/* Areas Due Soon */}
      {areaReviewData.dueSoonAreas.length > 0 && (
        <section className="mb-8">
          <button
            type="button"
            onClick={() => toggleSection('areas-due-soon')}
            aria-expanded={!collapsedSections.has('areas-due-soon')}
            className="flex items-center gap-2 mb-4 w-full text-left"
          >
            {collapsedSections.has('areas-due-soon') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <Clock className="w-6 h-6 text-yellow-600" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Areas Due for Review Soon</h2>
            <span className="badge badge-yellow ml-2">{areaReviewData.dueSoonAreas.length}</span>
          </button>
          {!collapsedSections.has('areas-due-soon') && (
          <div className="space-y-3">
            {areaReviewData.dueSoonAreas.map((area) => (
              <div key={area.id} className="card hover:shadow-md transition-shadow border-l-4 border-l-yellow-500">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-lg">{area.title}</h3>
                      <span className="badge badge-gray text-xs capitalize">{area.review_frequency}</span>
                    </div>
                    <p className="text-sm text-yellow-600 mb-2">
                      <Clock className="w-3 h-3 inline mr-1" />
                      {area.reviewStatus.text}
                    </p>
                    {area.standard_of_excellence && (
                      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-md p-3 mt-2">
                        <div className="flex items-start gap-2">
                          <Star className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="text-xs font-medium text-amber-800 dark:text-amber-300 mb-1">
                              Are you maintaining this standard?
                            </p>
                            <p className="text-sm text-amber-700 dark:text-amber-200">{area.standard_of_excellence}</p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Link
                      to={`/areas/${area.id}`}
                      className="btn btn-sm btn-secondary"
                    >
                      Review
                    </Link>
                    <button
                      onClick={() => handleMarkAreaReviewed(area.id, area.title)}
                      disabled={markReviewed.isPending}
                      className="btn btn-sm btn-primary flex items-center gap-1"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Mark Reviewed
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
          )}
        </section>
      )}

      {/* Projects Without Area Assignment */}
      {orphanProjects.length > 0 && (
        <section className="mb-8">
          <button
            type="button"
            onClick={() => toggleSection('orphan-projects')}
            aria-expanded={!collapsedSections.has('orphan-projects')}
            className="flex items-center gap-2 mb-4 w-full text-left"
          >
            {collapsedSections.has('orphan-projects') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <FolderOpen className="w-6 h-6 text-yellow-600" />
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Projects Without Area</h2>
            <span className="badge badge-yellow ml-2">{orphanProjects.length}</span>
          </button>
          {!collapsedSections.has('orphan-projects') && (<>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            These projects are not assigned to any Area. Assign them to maintain a complete project-area structure.
          </p>
          <div className="space-y-3">
            {orphanProjects.map((project) => (
              <div key={project.id} className="card hover:shadow-md transition-shadow border-l-4 border-l-yellow-500">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">{project.title}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">{project.status.replace('_', ' ')}</p>
                  </div>
                  <Link
                    to={`/projects/${project.id}`}
                    className="btn btn-sm btn-primary"
                  >
                    Assign Area
                  </Link>
                </div>
              </div>
            ))}
          </div>
          </>)}
        </section>
      )}

      {/* Projects Needing Review */}
      {review.projects_needing_review_details && review.projects_needing_review_details.length > 0 && (
        <section className="mb-8">
          <button
            type="button"
            onClick={() => toggleSection('projects-needing-review')}
            aria-expanded={!collapsedSections.has('projects-needing-review')}
            className="flex items-center gap-2 mb-4 w-full text-left"
          >
            {collapsedSections.has('projects-needing-review') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Projects Needing Review</h2>
            <span className="badge badge-yellow ml-2">{review.projects_needing_review_details.length}</span>
          </button>
          {!collapsedSections.has('projects-needing-review') && (
          <div className="space-y-3">
            {review.projects_needing_review_details.map((project) => {
              const insight = expandedInsights[project.id];
              return (
                <div key={project.id} className="card hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-lg">{project.title}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {project.days_since_activity} days since last activity
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {!insight && (
                        <button
                          onClick={() => handleGetInsight(project.id)}
                          disabled={pendingInsightIds.has(project.id)}
                          className="btn btn-sm flex items-center gap-1.5 bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/60"
                          title="Get AI insight"
                        >
                          <Sparkles className={`w-3 h-3 ${pendingInsightIds.has(project.id) ? 'animate-pulse' : ''}`} />
                          {pendingInsightIds.has(project.id) ? 'Loading...' : 'Insight'}
                        </button>
                      )}
                      <Link
                        to={`/projects/${project.id}`}
                        className="btn btn-sm btn-secondary"
                      >
                        Review
                      </Link>
                      <button
                        onClick={() => createUnstuck.mutate({
                          projectId: project.id,
                          useAI: true
                        })}
                        disabled={createUnstuck.isPending}
                        className="btn btn-sm btn-primary flex items-center gap-2"
                      >
                        <Sparkles className="w-3 h-3" />
                        Unstuck Task
                      </button>
                    </div>
                  </div>

                  {/* Per-project AI Insight */}
                  {insight && (
                    <div className="mt-3 p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg border border-violet-200 dark:border-violet-800/50">
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{insight.health_summary}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{insight.momentum_context}</p>
                      {insight.suggested_next_action && (
                        <p className="text-xs text-violet-700 dark:text-violet-300 mb-2">
                          <span className="font-medium">Suggested:</span> {insight.suggested_next_action}
                        </p>
                      )}
                      {insight.questions_to_consider.length > 0 && (
                        <ul className="space-y-0.5">
                          {insight.questions_to_consider.map((q, i) => (
                            <li key={i} className="text-xs text-gray-500 dark:text-gray-400 italic">
                              {q}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          )}
        </section>
      )}

      {/* Projects Without Next Actions */}
      {review.projects_without_next_action_details && review.projects_without_next_action_details.length > 0 && (
        <section className="mb-8">
          <button
            type="button"
            onClick={() => toggleSection('projects-without-next-action')}
            aria-expanded={!collapsedSections.has('projects-without-next-action')}
            className="flex items-center gap-2 mb-4 w-full text-left"
          >
            {collapsedSections.has('projects-without-next-action') ? <ChevronRight className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Projects Without Next Actions</h2>
            <span className="badge badge-yellow ml-2">{review.projects_without_next_action_details.length}</span>
          </button>
          {!collapsedSections.has('projects-without-next-action') && (<>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            These projects need a next action defined to maintain momentum
          </p>
          <div className="space-y-3">
            {review.projects_without_next_action_details.map((project) => (
              <div key={project.id} className="card hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">{project.title}</h3>
                  </div>
                  <Link
                    to={`/projects/${project.id}`}
                    className="btn btn-sm btn-primary"
                  >
                    Define Next Action
                  </Link>
                </div>
              </div>
            ))}
          </div>
          </>)}
        </section>
      )}

      {/* All Clear */}
      {review.projects_needing_review === 0 &&
       review.projects_without_next_action === 0 &&
       areaReviewData.overdueAreas.length === 0 &&
       areaReviewData.dueSoonAreas.length === 0 &&
       orphanProjects.length === 0 && (
        <div className="card text-center py-12 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
          <CalendarCheck className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-green-900 dark:text-green-200 mb-2">All Caught Up!</h3>
          <p className="text-green-700 dark:text-green-300">
            All projects have recent activity and defined next actions. All areas are reviewed. Great work!
          </p>
        </div>
      )}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  variant: 'blue' | 'yellow' | 'red' | 'green';
}

function StatCard({ title, value, variant }: StatCardProps) {
  const variants = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300',
    yellow: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-300',
    red: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-300',
    green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-300',
  };

  return (
    <div className={`card ${variants[variant]}`}>
      <p className="text-sm font-medium mb-1">{title}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}
