import { Sparkles, AlertCircle, TrendingUp, TrendingDown, Minus, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useWeeklyReviewAISummary } from '../../hooks/useIntelligence';
import type { WeeklyReviewAISummary } from '../../types';

interface AIReviewSummaryProps {
  onSummaryGenerated?: (summary: WeeklyReviewAISummary) => void;
}

const trendIcon = (trend: string) => {
  if (trend === 'rising') return <TrendingUp className="w-3 h-3 text-green-500" />;
  if (trend === 'falling') return <TrendingDown className="w-3 h-3 text-red-500" />;
  return <Minus className="w-3 h-3 text-gray-400" />;
};

export function AIReviewSummary({ onSummaryGenerated }: AIReviewSummaryProps) {
  const summary = useWeeklyReviewAISummary();

  const handleGenerate = () => {
    summary.mutate(undefined, {
      onSuccess: (data) => {
        onSummaryGenerated?.(data);
      },
    });
  };

  return (
    <div className="card border border-violet-200 dark:border-violet-800/50 mb-6">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-violet-500" />
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">AI Review Co-Pilot</h3>
        </div>
        {!summary.data && (
          <button
            onClick={handleGenerate}
            disabled={summary.isPending}
            className="text-xs px-3 py-1.5 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/60 transition-colors flex items-center gap-1.5 disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${summary.isPending ? 'animate-pulse' : ''}`} />
            {summary.isPending ? 'Analyzing...' : 'Generate AI Review'}
          </button>
        )}
      </div>

      {/* Loading state */}
      {summary.isPending && (
        <div className="text-sm text-violet-500 flex items-center gap-2 py-4 justify-center">
          <div className="w-3.5 h-3.5 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
          Analyzing your portfolio...
        </div>
      )}

      {/* Error state */}
      {summary.isError && (
        <div className="flex items-center justify-between py-3">
          <div className="text-sm text-red-500 dark:text-red-400 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5" />
            Failed to generate review summary.
          </div>
          <button
            onClick={handleGenerate}
            className="text-xs px-2 py-1 rounded text-violet-600 dark:text-violet-400 hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Idle state - no summary yet, no loading */}
      {!summary.data && !summary.isPending && !summary.isError && (
        <p className="text-sm text-gray-400 dark:text-gray-500 italic">
          Generate an AI summary to see portfolio insights, wins, and attention items.
        </p>
      )}

      {/* Success state */}
      {summary.data && (
        <div className="space-y-4">
          {/* Portfolio Narrative */}
          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
            {summary.data.portfolio_narrative}
          </p>

          {/* Wins */}
          {(summary.data.wins ?? []).length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-green-600 dark:text-green-400 uppercase tracking-wide mb-1.5">
                Wins
              </h4>
              <ul className="space-y-1">
                {(summary.data.wins ?? []).map((win, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-1.5">
                    <span className="text-green-500 mt-0.5">+</span>
                    {win}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Attention Items */}
          {(summary.data.attention_items ?? []).length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wide mb-1.5">
                Needs Attention
              </h4>
              <div className="space-y-2">
                {(summary.data.attention_items ?? []).map((item) => (
                  <Link
                    key={item.project_id}
                    to={`/projects/${item.project_id}`}
                    className="block p-2.5 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-200 dark:border-amber-800/50 hover:border-amber-300 dark:hover:border-amber-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {item.project_title}
                        </span>
                        {trendIcon(item.trend)}
                        <span className="text-xs text-gray-500">{(item.momentum_score * 100).toFixed(0)}%</span>
                      </div>
                      <ChevronRight className="w-3 h-3 text-gray-400" />
                    </div>
                    <p className="text-xs text-amber-700 dark:text-amber-300 mt-1">{item.reason}</p>
                    {item.suggested_action && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 italic">
                        {item.suggested_action}
                      </p>
                    )}
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {(summary.data.recommendations ?? []).length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-violet-600 dark:text-violet-400 uppercase tracking-wide mb-1.5">
                Recommendations
              </h4>
              <ul className="space-y-1">
                {(summary.data.recommendations ?? []).map((rec, i) => (
                  <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-1.5">
                    <span className="text-violet-500 mt-0.5">{i + 1}.</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Regenerate button */}
          <div className="pt-2 border-t border-gray-200 dark:border-gray-700 flex justify-end">
            <button
              onClick={handleGenerate}
              disabled={summary.isPending}
              className="text-xs px-2 py-1 rounded text-violet-600 dark:text-violet-400 hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors flex items-center gap-1"
            >
              <Sparkles className="w-3 h-3" />
              Regenerate
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
