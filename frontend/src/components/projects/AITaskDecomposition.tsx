import { useState } from 'react';
import { Sparkles, AlertCircle, Plus, Clock, Zap, Tag, Check } from 'lucide-react';
import { useDecomposeTasksFromNotes } from '../../hooks/useIntelligence';
import { useCreateTask } from '../../hooks/useTasks';
import { getAIErrorMessage } from '../../utils/aiErrors';
import type { DecomposedTask } from '../../types';
import toast from 'react-hot-toast';

interface AITaskDecompositionProps {
  projectId: number;
  hasBrainstormNotes: boolean;
  hasOrganizingNotes: boolean;
}

const energyLabels: Record<string, string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

const energyColors: Record<string, string> = {
  high: 'text-red-600 dark:text-red-400',
  medium: 'text-yellow-600 dark:text-yellow-400',
  low: 'text-green-600 dark:text-green-400',
};

export function AITaskDecomposition({ projectId, hasBrainstormNotes, hasOrganizingNotes }: AITaskDecompositionProps) {
  const decompose = useDecomposeTasksFromNotes();
  const createTask = useCreateTask();
  const [tasks, setTasks] = useState<DecomposedTask[]>([]);
  const [createdTasks, setCreatedTasks] = useState<Set<number>>(new Set());
  const [isExpanded, setIsExpanded] = useState(false);
  const [creatingAll, setCreatingAll] = useState(false);

  if (!hasBrainstormNotes && !hasOrganizingNotes) return null;

  const handleDecompose = () => {
    setIsExpanded(true);
    setCreatedTasks(new Set());
    decompose.mutate(projectId, {
      onSuccess: (data) => {
        setTasks(data.tasks);
      },
    });
  };

  const handleCreateTask = (task: DecomposedTask, index: number) => {
    createTask.mutate(
      {
        project_id: projectId,
        title: task.title,
        estimated_minutes: task.estimated_minutes || undefined,
        energy_level: task.energy_level || undefined,
        context: task.context || undefined,
        status: 'pending',
        is_next_action: false,
        priority: 5,
      },
      {
        onSuccess: () => {
          setCreatedTasks((prev) => new Set([...prev, index]));
          toast.success(`Task created: ${task.title}`);
        },
        onError: () => {
          toast.error('Failed to create task');
        },
      }
    );
  };

  const handleCreateAll = async () => {
    setCreatingAll(true);
    const uncreated = tasks
      .map((task, idx) => ({ task, idx }))
      .filter(({ idx }) => !createdTasks.has(idx));
    for (const { task, idx } of uncreated) {
      try {
        await createTask.mutateAsync({
          project_id: projectId,
          title: task.title,
          estimated_minutes: task.estimated_minutes || undefined,
          energy_level: task.energy_level || undefined,
          context: task.context || undefined,
          status: 'pending',
          is_next_action: false,
          priority: 5,
        });
        setCreatedTasks((prev) => new Set([...prev, idx]));
      } catch {
        toast.error(`Failed to create "${task.title}"`);
        break;
      }
    }
    setCreatingAll(false);
  };

  return (
    <div className="mt-4">
      <button
        onClick={handleDecompose}
        disabled={decompose.isPending}
        className="text-xs px-3 py-1.5 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/60 transition-colors flex items-center gap-1.5"
      >
        <Sparkles className={`w-3.5 h-3.5 ${decompose.isPending ? 'animate-pulse' : ''}`} />
        {tasks.length > 0 ? 'Re-decompose Notes' : 'Decompose Notes into Tasks'}
      </button>

      {decompose.isPending && (
        <div className="text-sm text-violet-500 flex items-center gap-2 py-3">
          <div className="w-3.5 h-3.5 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
          Analyzing notes and generating tasks...
        </div>
      )}

      {decompose.isError && (
        <div className="text-sm text-red-500 dark:text-red-400 flex items-center gap-1.5 mt-2">
          <AlertCircle className="w-3.5 h-3.5" />
          {getAIErrorMessage(decompose.error, 'Decomposition failed')}
        </div>
      )}

      {isExpanded && tasks.length > 0 && (
        <div className="mt-3 space-y-2">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {tasks.length} tasks generated
            </span>
            {tasks.length > 1 && createdTasks.size < tasks.length && (
              <button
                onClick={handleCreateAll}
                disabled={creatingAll}
                className="text-xs px-2 py-1 rounded bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50 transition-colors flex items-center gap-1"
              >
                {creatingAll ? (
                  <><div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" /> Creating...</>
                ) : (
                  <><Plus className="w-3 h-3" /> Create All</>
                )}
              </button>
            )}
          </div>

          {tasks.map((task, i) => {
            const isCreated = createdTasks.has(i);
            return (
              <div
                key={i}
                className={`p-2.5 rounded-lg border text-sm ${
                  isCreated
                    ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                    : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className={`font-medium ${isCreated ? 'text-green-700 dark:text-green-300 line-through' : 'text-gray-900 dark:text-gray-100'}`}>
                    {task.title}
                  </span>
                  {isCreated ? (
                    <Check className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                  ) : (
                    <button
                      onClick={() => handleCreateTask(task, i)}
                      className="text-violet-600 dark:text-violet-400 hover:text-violet-800 dark:hover:text-violet-300 shrink-0 mt-0.5"
                      title="Create this task"
                      aria-label={`Create task: ${task.title}`}
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1.5">
                  {task.estimated_minutes && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-0.5">
                      <Clock className="w-3 h-3" /> {task.estimated_minutes}m
                    </span>
                  )}
                  {task.energy_level && (
                    <span className={`text-xs flex items-center gap-0.5 ${energyColors[task.energy_level] || 'text-gray-500'}`}>
                      <Zap className="w-3 h-3" /> {energyLabels[task.energy_level] || task.energy_level}
                    </span>
                  )}
                  {task.context && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-0.5">
                      <Tag className="w-3 h-3" /> {task.context.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
