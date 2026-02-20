import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, CheckCircle, PlusCircle, FolderOpen, Activity, Save } from 'lucide-react';
import toast from 'react-hot-toast';
import { Modal } from './Modal';
import { useSessionSummary } from '../../hooks/useIntelligence';
import type { SessionSummaryResponse } from '../../types';

interface SessionSummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionStart: string | null;
  onSessionEnd: () => void;
}

export function SessionSummaryModal({ isOpen, onClose, sessionStart, onSessionEnd }: SessionSummaryModalProps) {
  const [preview, setPreview] = useState<SessionSummaryResponse | null>(null);
  const [notes, setNotes] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const sessionSummary = useSessionSummary();

  // Fetch preview when modal opens
  useEffect(() => {
    if (isOpen && sessionStart) {
      setPreview(null);
      setNotes('');
      sessionSummary.mutate(
        { sessionStart },
        {
          onSuccess: (data) => setPreview(data),
        }
      );
    }
  }, [isOpen, sessionStart]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSaveAndEnd = () => {
    if (!sessionStart) return;
    setIsSaving(true);
    sessionSummary.mutate(
      { sessionStart, persist: true, notes: notes.trim() || undefined },
      {
        onSuccess: () => {
          toast.success('Session summary saved');
          onSessionEnd();
          onClose();
          setIsSaving(false);
        },
        onError: () => {
          toast.error('Failed to save session summary');
          setIsSaving(false);
        },
      }
    );
  };

  const isLoading = sessionSummary.isPending && !preview;
  const isError = sessionSummary.isError && !preview;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="End Session" size="md">
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
          <span className="ml-3 text-gray-500 dark:text-gray-400">Loading session summary...</span>
        </div>
      )}

      {isError && (
        <div className="text-center py-8">
          <p className="text-red-600 dark:text-red-400 mb-4">Failed to load session summary</p>
          <button
            onClick={() => sessionStart && sessionSummary.mutate(
              { sessionStart },
              { onSuccess: (data) => setPreview(data) }
            )}
            className="btn btn-secondary"
          >
            Retry
          </button>
        </div>
      )}

      {preview && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center justify-center gap-1 mb-1">
                <CheckCircle className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-2xl font-bold text-green-700 dark:text-green-300">{preview.tasks_completed}</span>
              </div>
              <p className="text-xs text-green-600 dark:text-green-400">Completed</p>
            </div>
            <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center justify-center gap-1 mb-1">
                <PlusCircle className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-2xl font-bold text-blue-700 dark:text-blue-300">{preview.tasks_created}</span>
              </div>
              <p className="text-xs text-blue-600 dark:text-blue-400">Created</p>
            </div>
            <div className="text-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div className="flex items-center justify-center gap-1 mb-1">
                <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-2xl font-bold text-gray-700 dark:text-gray-300">{preview.activity_count}</span>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Activities</p>
            </div>
          </div>

          {/* Projects Touched */}
          {preview.projects_touched.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <FolderOpen className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Projects Touched</h3>
              </div>
              <div className="flex flex-wrap gap-2">
                {preview.projects_touched.map((name) => (
                  <span key={name} className="badge badge-gray text-xs">{name}</span>
                ))}
              </div>
            </div>
          )}

          {/* Momentum Changes */}
          {preview.momentum_changes.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Momentum Changes</h3>
              <div className="space-y-2">
                {preview.momentum_changes.map((mc) => {
                  const delta = mc.old_score !== null ? mc.new_score - mc.old_score : null;
                  const isPositive = delta !== null && delta >= 0;
                  return (
                    <div key={mc.project_name} className="flex items-center justify-between text-sm">
                      <span className="text-gray-700 dark:text-gray-300">{mc.project_name}</span>
                      <span className={`flex items-center gap-1 font-medium ${
                        isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {isPositive ? (
                          <TrendingUp className="w-3.5 h-3.5" />
                        ) : (
                          <TrendingDown className="w-3.5 h-3.5" />
                        )}
                        {delta !== null ? `${isPositive ? '+' : ''}${(delta * 100).toFixed(0)}%` : `${(mc.new_score * 100).toFixed(0)}%`}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Narrative Summary */}
          <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <p className="text-sm text-gray-700 dark:text-gray-300">{preview.summary_text}</p>
          </div>

          {/* Session Notes */}
          <div>
            <label htmlFor="session-notes" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Session Notes (optional)
            </label>
            <textarea
              id="session-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What did you focus on? Any blockers or wins?"
              className="input w-full h-24 resize-none"
              rows={3}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onClose}
              className="btn btn-secondary"
            >
              Dismiss
            </button>
            <button
              onClick={handleSaveAndEnd}
              disabled={isSaving}
              className="btn btn-primary flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save & End Session'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
