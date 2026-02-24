import { useState } from 'react';
import toast from 'react-hot-toast';
import { Plus, ChevronDown, Tag, Clock, ClipboardList, CheckCircle2 } from 'lucide-react';
import { Modal } from '@/components/common/Modal';
import {
  useSessionSummaries,
  useCaptureSession,
  type SessionCapture,
} from '@/hooks/useMemory';
import { EnergyDots } from './components/shared';

export function SessionCaptureButton() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="btn btn-primary flex items-center gap-2"
      >
        <Plus className="w-4 h-4" />
        Log Session
      </button>
      {isOpen && <CaptureSessionModal onClose={() => setIsOpen(false)} />}
    </>
  );
}

export function SessionsView() {
  const { data: sessions, isLoading, isError } = useSessionSummaries(50);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (objectId: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(objectId)) next.delete(objectId);
      else next.add(objectId);
      return next;
    });
  };

  if (isError) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300 text-sm">
          Failed to load sessions. The memory layer module may not be enabled.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Loading sessions...</div>;
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="card text-center py-12">
        <ClipboardList className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">No sessions captured</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Log your first session to start building a record of your work.
        </p>
        <SessionCaptureButton />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        {sessions.length} session{sessions.length !== 1 ? 's' : ''} captured
      </p>

      {sessions.map((session) => {
        const content = session.content as {
          date?: string;
          accomplishments?: string[];
          blockers?: string[];
          next_focus?: string;
          energy_level?: number;
          duration_minutes?: number;
          notes?: string;
        } | null;

        const accomplishments = content?.accomplishments ?? [];
        const isExpanded = expandedIds.has(session.object_id);
        const sessionDate = content?.date ?? session.effective_from;
        const energy = content?.energy_level;

        return (
          <div key={session.id} className="card py-3">
            {/* Header row */}
            <button
              onClick={() => toggleExpand(session.object_id)}
              className="w-full text-left flex items-center gap-3 group"
            >
              <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                    {sessionDate}
                  </span>
                  <span className="font-mono text-xs text-gray-400 dark:text-gray-500">
                    {session.object_id}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1 flex-wrap">
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {accomplishments.length} accomplishment{accomplishments.length !== 1 ? 's' : ''}
                  </span>
                  {energy !== undefined && energy !== null && (
                    <EnergyDots level={energy} />
                  )}
                  {content?.duration_minutes && (
                    <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {content.duration_minutes} min
                    </span>
                  )}
                  {accomplishments.length > 0 && !isExpanded && (
                    <span className="text-xs text-gray-400 dark:text-gray-500 truncate italic">
                      {accomplishments[0]}
                      {accomplishments.length > 1 ? ` +${accomplishments.length - 1} more` : ''}
                    </span>
                  )}
                </div>
              </div>
              <ChevronDown
                className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              />
            </button>

            {/* Expanded detail */}
            {isExpanded && (
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 space-y-3 text-sm">
                {accomplishments.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Accomplishments
                    </p>
                    <ul className="space-y-1">
                      {accomplishments.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                          <span className="text-green-500 mt-0.5 flex-shrink-0">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {content?.blockers && content.blockers.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Blockers
                    </p>
                    <ul className="space-y-1">
                      {content.blockers.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                          <span className="text-orange-500 mt-0.5 flex-shrink-0">•</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {content?.next_focus && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Next Focus
                    </p>
                    <p className="text-gray-700 dark:text-gray-300">{content.next_focus}</p>
                  </div>
                )}

                {content?.notes && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">
                      Notes
                    </p>
                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line">{content.notes}</p>
                  </div>
                )}

                {session.tags && session.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 pt-1">
                    {session.tags.map((tag) => (
                      <span key={tag} className="badge badge-blue text-xs flex items-center gap-1">
                        <Tag className="w-3 h-3" />
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function CaptureSessionModal({ onClose }: { onClose: () => void }) {
  const captureSession = useCaptureSession();
  const today = new Date().toISOString().split('T')[0];

  const [sessionDate, setSessionDate] = useState(today);
  const [accomplishmentsStr, setAccomplishmentsStr] = useState('');
  const [blockersStr, setBlockersStr] = useState('');
  const [nextFocus, setNextFocus] = useState('');
  const [energyLevel, setEnergyLevel] = useState<number | null>(null);
  const [durationMinutes, setDurationMinutes] = useState('');
  const [notes, setNotes] = useState('');
  const [tags, setTags] = useState('');

  const handleCapture = () => {
    const accomplishments = accomplishmentsStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    if (accomplishments.length === 0) {
      toast.error('Add at least one accomplishment');
      return;
    }

    const blockers = blockersStr
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    const data: SessionCapture = {
      session_date: sessionDate || undefined,
      accomplishments,
      blockers: blockers.length > 0 ? blockers : undefined,
      next_focus: nextFocus.trim() || undefined,
      energy_level: energyLevel ?? undefined,
      duration_minutes: durationMinutes ? parseInt(durationMinutes, 10) || undefined : undefined,
      notes: notes.trim() || undefined,
      tags: tags
        ? tags.split(',').map((t) => t.trim()).filter(Boolean)
        : undefined,
    };

    captureSession.mutate(data, {
      onSuccess: () => {
        toast.success('Session captured');
        onClose();
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to capture session');
      },
    });
  };

  return (
    <Modal isOpen onClose={onClose} title="Log Session Summary">
      <div className="space-y-4">
        {/* Date */}
        <div>
          <label className="label">Session Date</label>
          <input
            type="date"
            className="input"
            value={sessionDate}
            onChange={(e) => setSessionDate(e.target.value)}
          />
        </div>

        {/* Accomplishments */}
        <div>
          <label className="label">
            Accomplishments <span className="text-red-500">*</span>
          </label>
          <textarea
            className="input text-sm"
            rows={4}
            value={accomplishmentsStr}
            onChange={(e) => setAccomplishmentsStr(e.target.value)}
            placeholder={"Finished refactoring the auth module\nFixed DEBT-133 import error handling\nReviewed PR #42"}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">One item per line</p>
        </div>

        {/* Blockers */}
        <div>
          <label className="label">Blockers (optional)</label>
          <textarea
            className="input text-sm"
            rows={2}
            value={blockersStr}
            onChange={(e) => setBlockersStr(e.target.value)}
            placeholder={"Waiting for design review on feature X\nNeed access to staging DB"}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">One item per line</p>
        </div>

        {/* Next focus */}
        <div>
          <label className="label">Next Session Focus (optional)</label>
          <input
            type="text"
            className="input"
            value={nextFocus}
            onChange={(e) => setNextFocus(e.target.value)}
            placeholder="e.g., Pick up design review and complete BACKLOG-083"
          />
        </div>

        {/* Energy + Duration row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Energy Level (optional)</label>
            <div className="flex gap-2 mt-1">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  onClick={() => setEnergyLevel(energyLevel === n ? null : n)}
                  className={`w-9 h-9 rounded-full text-sm font-bold transition-colors border-2 ${
                    energyLevel === n
                      ? n >= 4
                        ? 'bg-green-500 border-green-500 text-white'
                        : n >= 2
                        ? 'bg-yellow-500 border-yellow-500 text-white'
                        : 'bg-red-400 border-red-400 text-white'
                      : 'border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400'
                  }`}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Duration (minutes, optional)</label>
            <input
              type="number"
              className="input"
              min={1}
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(e.target.value)}
              placeholder="e.g., 90"
            />
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="label">Notes (optional)</label>
          <textarea
            className="input text-sm"
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any additional context or observations..."
          />
        </div>

        {/* Tags */}
        <div>
          <label className="label">Tags (optional, comma-separated)</label>
          <input
            type="text"
            className="input"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g., backend, deep-work, refactor"
          />
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleCapture}
            disabled={captureSession.isPending}
            className="btn btn-primary flex items-center gap-2"
          >
            <ClipboardList className="w-4 h-4" />
            {captureSession.isPending ? 'Saving...' : 'Save Session'}
          </button>
        </div>
      </div>
    </Modal>
  );
}
