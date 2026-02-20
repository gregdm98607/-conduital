import { useState } from 'react';
import { Brain, RefreshCw, AlertCircle, Lightbulb, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import { getAIErrorMessage } from '../../utils/aiErrors';
import type { StalledProject, AITaskSuggestion } from '../../types';

interface AIDashboardSuggestionsProps {
  stalledProjects: StalledProject[];
}

interface ProjectSuggestion {
  projectId: number;
  projectTitle: string;
  suggestion: AITaskSuggestion | null;
  loading: boolean;
  error: string | null;
}

export function AIDashboardSuggestions({ stalledProjects }: AIDashboardSuggestionsProps) {
  const [suggestions, setSuggestions] = useState<ProjectSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasRun, setHasRun] = useState(false);

  // Take top 3 stalled projects to generate suggestions for
  const targetProjects = stalledProjects.slice(0, 3);

  const handleGenerateSuggestions = async () => {
    setIsLoading(true);
    setHasRun(true);

    const initial: ProjectSuggestion[] = targetProjects.map((p) => ({
      projectId: p.id,
      projectTitle: p.title,
      suggestion: null,
      loading: true,
      error: null,
    }));
    setSuggestions(initial);

    // Fetch suggestions in parallel
    const results = await Promise.allSettled(
      targetProjects.map((p) => api.suggestNextAction(p.id))
    );

    const updated = initial.map((s, i) => {
      const result = results[i];
      if (result.status === 'fulfilled') {
        return { ...s, suggestion: result.value, loading: false };
      } else {
        const displayError = getAIErrorMessage(result.reason, 'Suggestion unavailable');
        return { ...s, loading: false, error: displayError };
      }
    });

    setSuggestions(updated);
    setIsLoading(false);
  };

  if (targetProjects.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="card border border-violet-200 dark:border-violet-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-violet-600" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">AI Recommendations</h3>
            <span className="text-xs text-violet-500 dark:text-violet-400">for stalled projects</span>
          </div>
          <button
            onClick={handleGenerateSuggestions}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/60 transition-colors flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            {hasRun ? 'Refresh' : 'Get AI Suggestions'}
          </button>
        </div>

        {!hasRun && (
          <p className="text-sm text-gray-400 dark:text-gray-500 italic">
            Click "Get AI Suggestions" to get recommended next actions for your {targetProjects.length} stalled project{targetProjects.length !== 1 ? 's' : ''}.
          </p>
        )}

        {suggestions.length > 0 && (
          <div className="space-y-3">
            {suggestions.map((s) => (
              <div
                key={s.projectId}
                className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <Link
                    to={`/projects/${s.projectId}`}
                    className="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-violet-600 dark:hover:text-violet-400 flex items-center gap-1"
                  >
                    {s.projectTitle}
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                </div>

                {s.loading && (
                  <div className="text-sm text-violet-500 flex items-center gap-2">
                    <div className="w-3.5 h-3.5 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
                    Thinking...
                  </div>
                )}

                {s.error && (
                  <div className="text-sm text-red-500 dark:text-red-400 flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {s.error}
                  </div>
                )}

                {s.suggestion && (
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-violet-500 shrink-0 mt-0.5" />
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      {s.suggestion.suggestion}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
