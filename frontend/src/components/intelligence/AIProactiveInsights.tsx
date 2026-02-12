import { useState } from 'react';
import { RefreshCw, AlertCircle, Lightbulb, TrendingDown, ChevronRight, Activity } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useProactiveAnalysis } from '../../hooks/useIntelligence';
import type { ProactiveInsight } from '../../types';

export function AIProactiveInsights() {
  const proactiveAnalysis = useProactiveAnalysis();
  const [insights, setInsights] = useState<ProactiveInsight[]>([]);
  const [hasRun, setHasRun] = useState(false);

  const handleAnalyze = () => {
    setHasRun(true);
    proactiveAnalysis.mutate(5, {
      onSuccess: (data) => {
        setInsights(data.insights);
      },
    });
  };

  return (
    <div className="mb-8">
      <div className="card border border-violet-200 dark:border-violet-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-violet-600" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Proactive Analysis</h3>
            <span className="text-xs text-violet-500 dark:text-violet-400">declining &amp; stalled projects</span>
          </div>
          <button
            onClick={handleAnalyze}
            disabled={proactiveAnalysis.isPending}
            className="text-xs px-3 py-1.5 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/60 transition-colors flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${proactiveAnalysis.isPending ? 'animate-spin' : ''}`} />
            {hasRun ? 'Refresh' : 'Analyze Projects'}
          </button>
        </div>

        {!hasRun && (
          <p className="text-sm text-gray-400 dark:text-gray-500 italic">
            Click "Analyze Projects" to get AI insights on declining and stalled projects.
          </p>
        )}

        {proactiveAnalysis.isPending && (
          <div className="text-sm text-violet-500 flex items-center gap-2 py-4 justify-center">
            <div className="w-4 h-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
            Analyzing projects...
          </div>
        )}

        {proactiveAnalysis.isError && (
          <div className="text-sm text-red-500 dark:text-red-400 flex items-center gap-1.5 py-2">
            <AlertCircle className="w-4 h-4" />
            {proactiveAnalysis.error instanceof Error && proactiveAnalysis.error.message.includes('400')
              ? 'AI not configured — set up your API key in Settings'
              : 'Analysis unavailable'}
          </div>
        )}

        {hasRun && !proactiveAnalysis.isPending && insights.length === 0 && !proactiveAnalysis.isError && (
          <p className="text-sm text-green-600 dark:text-green-400 py-2">
            All projects are healthy — no declining or stalled projects found.
          </p>
        )}

        {insights.length > 0 && (
          <div className="space-y-3 mt-2">
            {insights.map((insight) => (
              <div
                key={insight.project_id}
                className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <Link
                    to={`/projects/${insight.project_id}`}
                    className="text-sm font-medium text-gray-900 dark:text-gray-100 hover:text-violet-600 dark:hover:text-violet-400 flex items-center gap-1"
                  >
                    {insight.project_title}
                    <ChevronRight className="w-3 h-3" />
                  </Link>
                  <div className="flex items-center gap-2">
                    {insight.trend === 'falling' && (
                      <span className="text-xs text-red-500 flex items-center gap-0.5">
                        <TrendingDown className="w-3 h-3" /> Declining
                      </span>
                    )}
                    <span className="text-xs text-gray-500">
                      {Math.round(insight.momentum_score * 100)}%
                    </span>
                  </div>
                </div>

                {insight.error && (
                  <div className="text-sm text-red-500 dark:text-red-400 flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5" />
                    {insight.error}
                  </div>
                )}

                {insight.analysis && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {insight.analysis}
                  </p>
                )}

                {insight.recommended_action && (
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-4 h-4 text-violet-500 shrink-0 mt-0.5" />
                    <p className="text-sm text-violet-700 dark:text-violet-300 font-medium">
                      {insight.recommended_action}
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
