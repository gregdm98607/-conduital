import { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Plus, CheckCircle, Edit, X, Trash2, Target, Star, ChevronDown, ChevronRight, Lightbulb, FileText, RefreshCw, Clock, Zap, ArrowUp, ArrowDown, Calendar } from 'lucide-react';
import { useProject, useMarkProjectReviewed, useCreateUnstuckTask } from '../hooks/useProjects';
import { useArea } from '../hooks/useAreas';
import { useUpdateTask, useDeleteTask } from '../hooks/useTasks';
import { Error } from '../components/common/Error';
import { MomentumBar } from '../components/projects/MomentumBar';
import { MomentumBreakdown } from '../components/projects/MomentumBreakdown';
import { AIProjectInsights } from '../components/projects/AIProjectInsights';
import { AITaskDecomposition } from '../components/projects/AITaskDecomposition';
import { formatRelativeTime, getReviewStatus } from '../utils/date';
import { EditProjectModal } from '../components/projects/EditProjectModal';
import { CreateTaskModal } from '../components/tasks/CreateTaskModal';
import { EditTaskModal } from '../components/tasks/EditTaskModal';
import { ContextExportModal } from '../components/common/ContextExportModal';
import { DeferPopover } from '../components/tasks/DeferPopover';
import { ProjectHeaderSkeleton, TaskItemSkeleton } from '@/components/common/Skeleton';
import { SearchInput } from '@/components/common/SearchInput';
import toast from 'react-hot-toast';

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);

  const { data: project, isLoading, error } = useProject(projectId);
  const { data: areaDetail } = useArea(project?.area_id || 0);
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();
  const markProjectReviewed = useMarkProjectReviewed();
  const createUnstuckTask = useCreateUnstuckTask();

  const [isEditProjectModalOpen, setIsEditProjectModalOpen] = useState(false);
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [isContextExportOpen, setIsContextExportOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<any>(null);
  const [taskSearchQuery, setTaskSearchQuery] = useState('');
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<number>>(new Set());
  const [npmExpanded, setNpmExpanded] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('pt-projectDetail.npmExpanded') || 'false');
    } catch {
      localStorage.removeItem('pt-projectDetail.npmExpanded');
      return false;
    }
  });

  if (error) {
    console.error('Project load error:', error);
    return <Error message={`Failed to load project: ${error instanceof Error ? error.message : String(error)}`} fullPage />;
  }
  if (!isLoading && !project) return <Error message="Project not found" fullPage />;

  const allTasks = project?.tasks || [];

  // Filter tasks by search query
  const filteredTasks = useMemo(() => {
    if (!taskSearchQuery) return allTasks;

    const query = taskSearchQuery.toLowerCase();
    return allTasks.filter((task) => {
      const matchesTitle = task.title.toLowerCase().includes(query);
      const matchesDescription = task.description?.toLowerCase().includes(query);
      const matchesContext = task.context?.toLowerCase().includes(query);
      return matchesTitle || matchesDescription || matchesContext;
    });
  }, [allTasks, taskSearchQuery]);

  const nextActions = filteredTasks.filter(t => t.is_next_action && t.status !== 'completed' && t.status !== 'cancelled');
  const completedTasks = filteredTasks.filter(t => t.status === 'completed' || t.status === 'cancelled');
  const otherTasks = filteredTasks.filter(t => !t.is_next_action && t.status !== 'completed' && t.status !== 'cancelled');

  // Bulk action handlers
  const toggleTaskSelection = (taskId: number) => {
    setSelectedTaskIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(taskId)) {
        newSet.delete(taskId);
      } else {
        newSet.add(taskId);
      }
      return newSet;
    });
  };

  const selectAllTasks = () => {
    const allTaskIds = filteredTasks.filter(t => t.status !== 'completed').map(t => t.id);
    setSelectedTaskIds(new Set(allTaskIds));
  };

  const clearSelection = () => {
    setSelectedTaskIds(new Set());
  };

  const handleBulkComplete = async () => {
    try {
      const updates = Array.from(selectedTaskIds).map(id =>
        updateTask.mutateAsync({ id, task: { status: 'completed' } })
      );
      await Promise.all(updates);
      toast.success(`Completed ${selectedTaskIds.size} tasks`);
      clearSelection();
    } catch (error) {
      toast.error('Failed to complete tasks');
    }
  };

  const handleBulkCancel = async () => {
    try {
      const updates = Array.from(selectedTaskIds).map(id =>
        updateTask.mutateAsync({ id, task: { status: 'cancelled' } })
      );
      await Promise.all(updates);
      toast.success(`Cancelled ${selectedTaskIds.size} tasks`);
      clearSelection();
    } catch (error) {
      toast.error('Failed to cancel tasks');
    }
  };

  const handleBulkMakeNextAction = async () => {
    try {
      const updates = Array.from(selectedTaskIds).map(id =>
        updateTask.mutateAsync({ id, task: { is_next_action: true } })
      );
      await Promise.all(updates);
      toast.success(`Promoted ${selectedTaskIds.size} task${selectedTaskIds.size !== 1 ? 's' : ''} to Next Actions`);
      clearSelection();
    } catch {
      toast.error('Failed to promote tasks');
    }
  };

  const handleBulkDemoteToOther = async () => {
    try {
      const updates = Array.from(selectedTaskIds).map(id =>
        updateTask.mutateAsync({ id, task: { is_next_action: false } })
      );
      await Promise.all(updates);
      toast.success(`Moved ${selectedTaskIds.size} task${selectedTaskIds.size !== 1 ? 's' : ''} to Other Tasks`);
      clearSelection();
    } catch {
      toast.error('Failed to demote tasks');
    }
  };

  // Determine if selection contains only Other Tasks, only Next Actions, or mixed
  const selectedAreAllOtherTasks = selectedTaskIds.size > 0 && Array.from(selectedTaskIds).every(
    id => otherTasks.some(t => t.id === id)
  );
  const selectedAreAllNextActions = selectedTaskIds.size > 0 && Array.from(selectedTaskIds).every(
    id => nextActions.some(t => t.id === id)
  );

  const handleDeferTask = (taskId: number, deferUntil: string) => {
    updateTask.mutate(
      { id: taskId, task: { defer_until: deferUntil } },
      {
        onSuccess: () => toast.success(`Task deferred to ${deferUntil}`),
        onError: () => toast.error('Failed to defer task'),
      }
    );
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to delete ${selectedTaskIds.size} tasks? This cannot be undone.`)) {
      return;
    }
    try {
      const deletes = Array.from(selectedTaskIds).map(taskId =>
        deleteTask.mutateAsync(taskId)
      );
      await Promise.all(deletes);
      toast.success(`Deleted ${selectedTaskIds.size} tasks`);
      clearSelection();
    } catch (error) {
      toast.error('Failed to delete tasks');
    }
  };

  return (
    <div className="p-8">
      {/* Back Button */}
      <Link
        to="/projects"
        className="inline-flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-6"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Projects
      </Link>

      {isLoading ? (
        <>
          {/* Loading State */}
          <ProjectHeaderSkeleton />
          <section className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Next Actions</h2>
            </div>
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <TaskItemSkeleton key={i} />
              ))}
            </div>
          </section>
        </>
      ) : project ? (
        <>
          {/* Project Header */}
          <div className="card mb-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">{project.title}</h1>
            {project.area && (
              <span className="badge badge-blue">{project.area.title}</span>
            )}
          </div>
          <div className="flex gap-2 items-center">
            {project.last_reviewed_at && (() => {
              const reviewInfo = getReviewStatus(project.last_reviewed_at, 'weekly');
              return (
                <span className={`badge text-xs flex items-center gap-1 ${
                  reviewInfo.status === 'overdue' ? 'badge-red' :
                  reviewInfo.status === 'due-soon' ? 'badge-yellow' :
                  'badge-green'
                }`}>
                  <Clock className="w-3 h-3" />
                  {reviewInfo.text}
                </span>
              );
            })()}
            <button
              onClick={() => setIsContextExportOpen(true)}
              className="btn btn-sm btn-secondary flex items-center gap-2"
              title="Export project context for AI sessions"
            >
              <FileText className="w-4 h-4" />
              AI Context
            </button>
            <button
              onClick={() => {
                markProjectReviewed.mutate(projectId, {
                  onSuccess: () => toast.success('Project marked as reviewed'),
                  onError: () => toast.error('Failed to mark project as reviewed'),
                });
              }}
              disabled={markProjectReviewed.isPending}
              className="btn btn-sm btn-primary flex items-center gap-2"
              title="Mark this project as reviewed"
            >
              <RefreshCw className={`w-4 h-4 ${markProjectReviewed.isPending ? 'animate-spin' : ''}`} />
              Mark Reviewed
            </button>
            <button
              onClick={() => setIsEditProjectModalOpen(true)}
              className="btn btn-sm btn-secondary flex items-center gap-2"
            >
              <Edit className="w-4 h-4" />
              Edit
            </button>
            {project.stalled_since && (
              <>
                <span className="badge badge-red">Stalled</span>
                <button
                  onClick={() => {
                    createUnstuckTask.mutate(
                      { projectId: project.id, useAI: false },
                      {
                        onSuccess: () => toast.success(`Created unstuck task for "${project.title}"`),
                        onError: () => toast.error('Failed to create unstuck task', { id: 'unstuck-error' }),
                      }
                    );
                  }}
                  disabled={createUnstuckTask.isPending}
                  className="btn btn-sm flex items-center gap-1 text-orange-600 dark:text-orange-400 border-orange-300 dark:border-orange-700 hover:bg-orange-50 dark:hover:bg-orange-900/20"
                  title="Create a quick task to restart momentum"
                >
                  <Zap className={`w-4 h-4 ${createUnstuckTask.isPending ? 'animate-pulse' : ''}`} />
                  Get Unstuck
                </button>
              </>
            )}
            <span className={`badge ${
              project.status === 'active' ? 'badge-green' :
              project.status === 'completed' ? 'badge-blue' :
              'badge-yellow'
            }`}>
              {project.status}
            </span>
          </div>
        </div>

        {project.description && (
          <p className="text-gray-700 dark:text-gray-300 mb-6">{project.description}</p>
        )}

        {/* Outcome Statement - Prominent Display */}
        {project.outcome_statement && (
          <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5 text-emerald-600" />
              <h3 className="font-semibold text-emerald-800 dark:text-emerald-300">Outcome Statement</h3>
            </div>
            <p className="text-emerald-800 dark:text-emerald-200 italic">
              "{project.outcome_statement}"
            </p>
          </div>
        )}

        {/* Area Standard of Excellence */}
        {areaDetail?.standard_of_excellence && (
          <div className="mb-6 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Star className="w-5 h-5 fill-amber-400 text-amber-500" />
              <h3 className="font-semibold text-amber-800 dark:text-amber-300">
                Standard of Excellence
                <Link to={`/areas/${areaDetail.id}`} className="text-sm font-normal text-amber-600 dark:text-amber-400 ml-2 hover:underline">
                  ({areaDetail.title})
                </Link>
              </h3>
            </div>
            <p className="text-amber-900 dark:text-amber-200 text-sm">{areaDetail.standard_of_excellence}</p>
          </div>
        )}

        {/* Natural Planning Model Section */}
        {(project.purpose || project.vision_statement || project.brainstorm_notes || project.organizing_notes) && (
          <div className="mb-6 border border-indigo-200 dark:border-indigo-800 rounded-lg overflow-hidden">
            <button
              onClick={() => {
                const next = !npmExpanded;
                setNpmExpanded(next);
                localStorage.setItem('pt-projectDetail.npmExpanded', JSON.stringify(next));
              }}
              className="w-full flex items-center gap-2 p-4 text-left bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/30"
            >
              {npmExpanded ? <ChevronDown className="w-4 h-4 text-indigo-600" /> : <ChevronRight className="w-4 h-4 text-indigo-600" />}
              <Lightbulb className="w-5 h-5 text-indigo-600" />
              <h3 className="font-semibold text-indigo-800 dark:text-indigo-300">Natural Planning Model</h3>
            </button>
            {npmExpanded && (
              <div className="p-4 space-y-4">
                {project.purpose && (
                  <div>
                    <h4 className="text-sm font-medium text-indigo-700 dark:text-indigo-400 mb-1">Purpose</h4>
                    <p className="text-gray-800 dark:text-gray-200 text-sm whitespace-pre-wrap">{project.purpose}</p>
                  </div>
                )}
                {project.vision_statement && (
                  <div>
                    <h4 className="text-sm font-medium text-indigo-700 dark:text-indigo-400 mb-1">Vision</h4>
                    <p className="text-gray-800 dark:text-gray-200 text-sm whitespace-pre-wrap">{project.vision_statement}</p>
                  </div>
                )}
                {project.brainstorm_notes && (
                  <div>
                    <h4 className="text-sm font-medium text-indigo-700 dark:text-indigo-400 mb-1">Brainstorming</h4>
                    <p className="text-gray-800 dark:text-gray-200 text-sm whitespace-pre-wrap">{project.brainstorm_notes}</p>
                  </div>
                )}
                {project.organizing_notes && (
                  <div>
                    <h4 className="text-sm font-medium text-indigo-700 dark:text-indigo-400 mb-1">Organizing</h4>
                    <p className="text-gray-800 dark:text-gray-200 text-sm whitespace-pre-wrap">{project.organizing_notes}</p>
                  </div>
                )}

                {/* AI Task Decomposition — ROADMAP-002 */}
                <AITaskDecomposition
                  projectId={project.id}
                  hasBrainstormNotes={!!project.brainstorm_notes}
                  hasOrganizingNotes={!!project.organizing_notes}
                />
              </div>
            )}
          </div>
        )}

        {/* AI Insights — Prominent Placement */}
        <AIProjectInsights
          projectId={project.id}
          projectTitle={project.title}
          isActive={project.status === 'active'}
        />

        <MomentumBar score={project.momentum_score} />
        <MomentumBreakdown projectId={project.id} />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Last Activity</span>
            <div className="font-medium text-gray-900 dark:text-gray-100">{formatRelativeTime(project.last_activity_at)}</div>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Total Tasks</span>
            <div className="font-medium text-gray-900 dark:text-gray-100">{allTasks.length}</div>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Completed</span>
            <div className="font-medium text-gray-900 dark:text-gray-100">{completedTasks.length}</div>
          </div>
        </div>
      </div>

      {/* Task Search */}
      {allTasks.length > 0 && (
        <div className="mb-6">
          <SearchInput
            value={taskSearchQuery}
            onChange={setTaskSearchQuery}
            placeholder="Search tasks by title, description, or context..."
          />
          {taskSearchQuery && (
            <div className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Showing {filteredTasks.length} of {allTasks.length} tasks
            </div>
          )}
        </div>
      )}

      {/* Bulk Actions Toolbar */}
      {selectedTaskIds.size > 0 && (
        <div className="card mb-6 bg-primary-50 border-primary-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {selectedTaskIds.size} task{selectedTaskIds.size !== 1 ? 's' : ''} selected
              </span>
              <button
                onClick={selectAllTasks}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Select All
              </button>
              <button
                onClick={clearSelection}
                className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              >
                Clear
              </button>
            </div>
            <div className="flex items-center gap-2">
              {selectedAreAllOtherTasks && (
                <button
                  onClick={handleBulkMakeNextAction}
                  className="btn btn-sm flex items-center gap-2 text-emerald-600 dark:text-emerald-400 border-emerald-300 dark:border-emerald-700 hover:bg-emerald-50 dark:hover:bg-emerald-900/20"
                  disabled={updateTask.isPending}
                  title="Promote selected tasks to Next Actions"
                >
                  <ArrowUp className="w-4 h-4" />
                  → Next Action
                </button>
              )}
              {selectedAreAllNextActions && (
                <button
                  onClick={handleBulkDemoteToOther}
                  className="btn btn-sm flex items-center gap-2 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800"
                  disabled={updateTask.isPending}
                  title="Move selected tasks to Other Tasks"
                >
                  <ArrowDown className="w-4 h-4" />
                  → Other
                </button>
              )}
              <button
                onClick={handleBulkComplete}
                className="btn btn-sm btn-primary flex items-center gap-2"
                disabled={updateTask.isPending}
              >
                <CheckCircle className="w-4 h-4" />
                Complete
              </button>
              <button
                onClick={handleBulkCancel}
                className="btn btn-sm btn-secondary flex items-center gap-2"
                disabled={updateTask.isPending}
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
              <button
                onClick={handleBulkDelete}
                className="btn btn-sm btn-secondary flex items-center gap-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                disabled={deleteTask.isPending}
              >
                <Trash2 className="w-4 h-4" />
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Next Actions Section */}
      <section className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Next Actions</h2>
          <button
            onClick={() => setIsCreateTaskModalOpen(true)}
            className="btn btn-sm btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add Task
          </button>
        </div>
        {nextActions.length > 0 ? (
          <div className="space-y-2">
            {nextActions.map((task) => (
              <TaskItem
                key={task.id}
                task={task}
                onEdit={setEditingTask}
                onDefer={handleDeferTask}
                isSelected={selectedTaskIds.has(task.id)}
                onToggleSelect={() => toggleTaskSelection(task.id)}
              />
            ))}
          </div>
        ) : taskSearchQuery ? (
          <div className="card text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">No next actions match your search</p>
          </div>
        ) : (
          <div className="card bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
            <p className="text-yellow-800 dark:text-yellow-300 text-center">No next actions defined</p>
          </div>
        )}
      </section>

      {/* Other Tasks Section */}
      {otherTasks.length > 0 && (
        <section className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">Other Tasks</h2>
          <div className="space-y-2">
            {otherTasks.map((task) => (
              <TaskItem
                key={task.id}
                task={task}
                onEdit={setEditingTask}
                onDefer={handleDeferTask}
                isSelected={selectedTaskIds.has(task.id)}
                onToggleSelect={() => toggleTaskSelection(task.id)}
              />
            ))}
          </div>
        </section>
      )}

      {/* Completed Tasks Section */}
      {completedTasks.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">Completed Tasks</h2>
          <div className="space-y-2">
            {completedTasks.map((task) => (
              <TaskItem key={task.id} task={task} completed onEdit={setEditingTask} />
            ))}
          </div>
        </section>
      )}
        </>
      ) : null}

      {/* Modals */}
      {project && (
        <>
          <EditProjectModal
            isOpen={isEditProjectModalOpen}
            onClose={() => setIsEditProjectModalOpen(false)}
            project={project}
          />
          <CreateTaskModal
            isOpen={isCreateTaskModalOpen}
            onClose={() => setIsCreateTaskModalOpen(false)}
            projectId={project.id}
          />
          {editingTask && (
            <EditTaskModal
              isOpen={!!editingTask}
              onClose={() => setEditingTask(null)}
              task={editingTask}
            />
          )}
          <ContextExportModal
            isOpen={isContextExportOpen}
            onClose={() => setIsContextExportOpen(false)}
            projectId={project.id}
          />
        </>
      )}
    </div>
  );
}

interface TaskItemProps {
  task: any;
  completed?: boolean;
  onEdit: (task: any) => void;
  onDefer?: (taskId: number, deferUntil: string) => void;
  isSelected?: boolean;
  onToggleSelect?: () => void;
}

function TaskItem({ task, completed = false, onEdit, onDefer, isSelected = false, onToggleSelect }: TaskItemProps) {
  return (
    <div className={`card ${completed ? 'opacity-60' : ''} ${isSelected ? 'ring-2 ring-primary-500 bg-primary-50' : ''}`}>
      <div className="flex items-start justify-between">
        {/* Checkbox for non-completed tasks */}
        {!completed && onToggleSelect && (
          <div className="flex items-start pt-1 mr-3">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={onToggleSelect}
              className="w-4 h-4 text-primary-600 rounded border-gray-300 dark:border-gray-600 focus:ring-primary-500"
            />
          </div>
        )}
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            {completed && <CheckCircle className="w-4 h-4 text-green-600" />}
            {task.context && <span className="badge badge-gray text-xs">{task.context}</span>}
            {task.energy_level && <span className="badge badge-gray text-xs">{task.energy_level}</span>}
            {task.estimated_minutes && <span className="badge badge-gray text-xs">{task.estimated_minutes}m</span>}
            {task.defer_until && (
              <span className="badge badge-blue text-xs flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                Deferred to {task.defer_until}
              </span>
            )}
          </div>
          <h3 className={`font-medium ${completed ? 'line-through text-gray-500 dark:text-gray-400' : 'text-gray-900 dark:text-gray-100'}`}>
            {task.title}
          </h3>
          {task.description && (
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{task.description}</p>
          )}
        </div>
        <div className="flex items-center gap-1 ml-4">
          {!completed && onDefer && (
            <DeferPopover
              compact
              onDefer={(date) => onDefer(task.id, date)}
            />
          )}
          <button
            onClick={() => onEdit(task)}
            className="btn btn-sm btn-secondary"
          >
            <Edit className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
