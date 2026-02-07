import { useState, useEffect, useRef, useCallback } from 'react';
import { Copy, Check, RefreshCw, FileText } from 'lucide-react';
import toast from 'react-hot-toast';
import { Modal } from './Modal';
import { api } from '@/services/api';

interface ContextExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId?: number;
  areaId?: number;
}

export function ContextExportModal({ isOpen, onClose, projectId, areaId }: ContextExportModalProps) {
  const [context, setContext] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [stats, setStats] = useState<{ project_count: number; task_count: number; area_count: number } | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleGenerate = useCallback(async () => {
    // Cancel any in-flight request
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoading(true);
    setCopied(false);
    try {
      const params: { project_id?: number; area_id?: number } = {};
      if (projectId) params.project_id = projectId;
      if (areaId) params.area_id = areaId;

      const result = await api.getAIContext(Object.keys(params).length > 0 ? params : undefined);

      // Only update state if not aborted
      if (!controller.signal.aborted) {
        setContext(result.context);
        setStats({
          project_count: result.project_count,
          task_count: result.task_count,
          area_count: result.area_count,
        });
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        toast.error('Failed to generate AI context');
      }
    }
    if (!controller.signal.aborted) {
      setLoading(false);
    }
  }, [projectId, areaId]);

  // DEBT-046: Auto-generate on open via useEffect (not in render body)
  useEffect(() => {
    if (isOpen && !context && !loading) {
      handleGenerate();
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  // DEBT-047: Reset state on close and cancel in-flight requests
  useEffect(() => {
    if (!isOpen) {
      setContext('');
      setStats(null);
      setCopied(false);
      setLoading(false);
      abortControllerRef.current?.abort();
    }
  }, [isOpen]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(context);
      setCopied(true);
      toast.success('Context copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy to clipboard');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Export AI Context" size="lg">
      <div className="space-y-4">
        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Generate a structured context summary to paste into AI chat sessions (Claude, ChatGPT, etc.)
        </p>

        {/* Stats */}
        {stats && (
          <div className="flex gap-4 text-sm">
            <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded">
              {stats.project_count} projects
            </span>
            <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
              {stats.task_count} tasks
            </span>
            {stats.area_count > 0 && (
              <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded">
                {stats.area_count} areas
              </span>
            )}
          </div>
        )}

        {/* Context Output */}
        {loading ? (
          <div className="flex items-center justify-center py-12 text-gray-500 dark:text-gray-400">
            <RefreshCw className="w-5 h-5 animate-spin mr-2" />
            Generating context...
          </div>
        ) : context ? (
          <div className="relative">
            <textarea
              readOnly
              value={context}
              className="w-full h-80 p-4 font-mono text-sm bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 resize-y"
            />
          </div>
        ) : null}

        {/* Action Buttons */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handleCopy}
            disabled={!context || loading}
            className="btn btn-primary flex items-center gap-2"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4" />
                Copied
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy to Clipboard
              </>
            )}
          </button>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Regenerate
          </button>
        </div>

        {/* Usage tip */}
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <div className="flex items-start gap-2">
            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
            <p className="text-xs text-blue-800 dark:text-blue-300">
              Paste this context at the start of an AI conversation to give the AI full awareness of your projects, tasks, and priorities.
            </p>
          </div>
        </div>
      </div>
    </Modal>
  );
}
