import { useState } from 'react';
import { Scale, ArrowUp, ArrowDown, AlertTriangle, ChevronDown, ChevronRight } from 'lucide-react';
import { useRebalanceSuggestions } from '../../hooks/useIntelligence';
import { useUpdateTask } from '../../hooks/useTasks';
import toast from 'react-hot-toast';

export function AIRebalanceSuggestions() {
  const [isExpanded, setIsExpanded] = useState(false);
  const { data, isLoading, isError, refetch } = useRebalanceSuggestions(7, isExpanded);
  const updateTask = useUpdateTask();

  const handleApply = (taskId: number, suggestedZone: string) => {
    updateTask.mutate(
      { id: taskId, task: { urgency_zone: suggestedZone as 'critical_now' | 'opportunity_now' | 'over_the_horizon' } },
      {
        onSuccess: () => {
          toast.success('Task priority updated');
          refetch();
        },
        onError: () => {
          toast.error('Failed to update task');
        },
      }
    );
  };

  const hasOverflow = data && data.suggestions.length > 0;

  return (
    <div className="mb-8">
      <div className={`card ${hasOverflow ? 'border border-amber-200 dark:border-amber-800' : ''}`}>
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-controls="rebalance-content"
          className="flex items-center justify-between w-full"
        >
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-amber-500" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Priority Balance</h3>
            {hasOverflow && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300">
                {data.suggestions.length} suggestion{data.suggestions.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          {isExpanded ? (
            <ChevronDown className="w-4 h-4 text-gray-400" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-400" />
          )}
        </button>

        <div id="rebalance-content">
        {isExpanded && isLoading && (
          <div className="text-sm text-gray-500 flex items-center gap-2 py-3 justify-center mt-2">
            <div className="w-3.5 h-3.5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            Checking balance...
          </div>
        )}

        {isExpanded && isError && (
          <div className="text-sm text-red-500 dark:text-red-400 flex items-center gap-2 py-3 justify-center mt-2">
            <AlertTriangle className="w-3.5 h-3.5" />
            Failed to check priority balance.
          </div>
        )}

        {isExpanded && data && data.suggestions.length === 0 && (
          <p className="text-sm text-green-600 dark:text-green-400 mt-2">
            Opportunity Now zone is balanced ({data.opportunity_now_count}/{data.threshold} tasks).
          </p>
        )}

        {isExpanded && data && data.suggestions.length > 0 && (
          <div className="mt-3 space-y-2">
            <p className="text-xs text-amber-600 dark:text-amber-400 flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5" />
              Opportunity Now has {data.opportunity_now_count} tasks (threshold: {data.threshold})
            </p>

            {data.suggestions.map((s) => (
              <div
                key={s.task_id}
                className="p-2.5 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{s.task_title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{s.project_title}</p>
                  </div>
                  <button
                    onClick={() => handleApply(s.task_id, s.suggested_zone)}
                    className={`text-xs px-2 py-1 rounded shrink-0 flex items-center gap-1 transition-colors ${
                      s.suggested_zone === 'critical_now'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300'
                    }`}
                  >
                    {s.suggested_zone === 'critical_now' ? (
                      <><ArrowUp className="w-3 h-3" /> Critical</>
                    ) : (
                      <><ArrowDown className="w-3 h-3" /> Horizon</>
                    )}
                  </button>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{s.reason}</p>
              </div>
            ))}
          </div>
        )}
        </div>
      </div>
    </div>
  );
}
