import { useState } from 'react';
import { Brain, Sparkles, AlertCircle, ChevronDown, ChevronRight, Lightbulb, RefreshCw } from 'lucide-react';
import { useAnalyzeProject, useSuggestNextAction } from '../../hooks/useIntelligence';
import type { AIAnalysis, AITaskSuggestion } from '../../types';

interface AIProjectInsightsProps {
  projectId: number;
  projectTitle: string;
  isActive: boolean;
}

export function AIProjectInsights({ projectId, isActive }: AIProjectInsightsProps) {
  const [isExpanded, setIsExpanded] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('projectDetail.aiInsightsExpanded') || 'false');
    } catch {
      return false;
    }
  });
  const [analysis, setAnalysis] = useState<AIAnalysis | null>(null);
  const [suggestion, setSuggestion] = useState<AITaskSuggestion | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [suggestionError, setSuggestionError] = useState<string | null>(null);

  const analyzeProject = useAnalyzeProject(projectId);
  const suggestNextAction = useSuggestNextAction(projectId);

  const handleToggle = () => {
    const next = !isExpanded;
    setIsExpanded(next);
    localStorage.setItem('projectDetail.aiInsightsExpanded', JSON.stringify(next));
  };

  const handleAnalyze = () => {
    setAnalysisError(null);
    analyzeProject.mutate(undefined, {
      onSuccess: (data) => setAnalysis(data),
      onError: (err) => {
        const msg = err instanceof Error ? err.message : 'AI analysis unavailable';
        setAnalysisError(msg.includes('400') || msg.includes('403') ? 'AI features not configured. Add your Anthropic API key in Settings.' : msg);
      },
    });
  };

  const handleSuggest = () => {
    setSuggestionError(null);
    suggestNextAction.mutate(undefined, {
      onSuccess: (data) => setSuggestion(data),
      onError: (err) => {
        const msg = err instanceof Error ? err.message : 'AI suggestion unavailable';
        setSuggestionError(msg.includes('400') || msg.includes('403') ? 'AI features not configured. Add your Anthropic API key in Settings.' : msg);
      },
    });
  };

  return (
    <div className="mb-6 border border-violet-200 dark:border-violet-800 rounded-lg overflow-hidden">
      <button
        onClick={handleToggle}
        className="w-full flex items-center gap-2 p-4 text-left bg-violet-50 dark:bg-violet-900/20 hover:bg-violet-100 dark:hover:bg-violet-900/30 transition-colors"
        type="button"
        aria-expanded={isExpanded}
      >
        {isExpanded ? <ChevronDown className="w-4 h-4 text-violet-600" /> : <ChevronRight className="w-4 h-4 text-violet-600" />}
        <Brain className="w-5 h-5 text-violet-600" />
        <h3 className="font-semibold text-violet-800 dark:text-violet-300">AI Insights</h3>
        <span className="text-xs text-violet-500 dark:text-violet-400 ml-auto">Powered by Claude</span>
      </button>

      {isExpanded && (
        <div className="p-4 space-y-4">
          {/* AI Analysis Section */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-medium text-violet-700 dark:text-violet-400 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4" />
                Project Analysis
              </h4>
              <button
                onClick={handleAnalyze}
                disabled={analyzeProject.isPending}
                className="text-xs px-2.5 py-1 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/60 transition-colors flex items-center gap-1"
              >
                <RefreshCw className={`w-3 h-3 ${analyzeProject.isPending ? 'animate-spin' : ''}`} />
                {analysis ? 'Refresh' : 'Analyze'}
              </button>
            </div>

            {analyzeProject.isPending && (
              <div className="text-sm text-violet-500 dark:text-violet-400 flex items-center gap-2 py-2">
                <div className="w-4 h-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
                Analyzing project...
              </div>
            )}

            {analysisError && (
              <div className="text-sm text-red-600 dark:text-red-400 flex items-center gap-2 py-2 px-3 bg-red-50 dark:bg-red-900/20 rounded-md">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {analysisError}
              </div>
            )}

            {analysis && !analyzeProject.isPending && (
              <div className="space-y-3">
                <p className="text-sm text-gray-800 dark:text-gray-200">{analysis.analysis}</p>
                {analysis.recommendations.length > 0 && (
                  <div>
                    <h5 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">Recommendations</h5>
                    <ul className="space-y-1.5">
                      {analysis.recommendations.map((rec, i) => (
                        <li key={i} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-2">
                          <span className="text-violet-500 mt-0.5 shrink-0">&#x2022;</span>
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {!analysis && !analyzeProject.isPending && !analysisError && (
              <p className="text-sm text-gray-400 dark:text-gray-500 italic">
                Click "Analyze" to get AI-powered insights about this project's health and progress.
              </p>
            )}
          </div>

          {/* Divider */}
          <div className="border-t border-violet-200 dark:border-violet-800" />

          {/* AI Suggested Next Action */}
          {isActive && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-violet-700 dark:text-violet-400 flex items-center gap-1.5">
                  <Lightbulb className="w-4 h-4" />
                  Suggested Next Action
                </h4>
                <button
                  onClick={handleSuggest}
                  disabled={suggestNextAction.isPending}
                  className="text-xs px-2.5 py-1 rounded-md bg-violet-100 dark:bg-violet-900/40 text-violet-700 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-900/60 transition-colors flex items-center gap-1"
                >
                  <RefreshCw className={`w-3 h-3 ${suggestNextAction.isPending ? 'animate-spin' : ''}`} />
                  {suggestion ? 'New Suggestion' : 'Suggest'}
                </button>
              </div>

              {suggestNextAction.isPending && (
                <div className="text-sm text-violet-500 dark:text-violet-400 flex items-center gap-2 py-2">
                  <div className="w-4 h-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
                  Generating suggestion...
                </div>
              )}

              {suggestionError && (
                <div className="text-sm text-red-600 dark:text-red-400 flex items-center gap-2 py-2 px-3 bg-red-50 dark:bg-red-900/20 rounded-md">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {suggestionError}
                </div>
              )}

              {suggestion && !suggestNextAction.isPending && (
                <div className="p-3 bg-violet-50 dark:bg-violet-900/30 rounded-md border border-violet-200 dark:border-violet-800">
                  <p className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {suggestion.suggestion}
                  </p>
                  {suggestion.ai_generated && (
                    <span className="text-xs text-violet-500 dark:text-violet-400 mt-1 inline-block">AI-generated</span>
                  )}
                </div>
              )}

              {!suggestion && !suggestNextAction.isPending && !suggestionError && (
                <p className="text-sm text-gray-400 dark:text-gray-500 italic">
                  Click "Suggest" to get an AI-recommended next action for this project.
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
