/**
 * SyncDetailsPanel — modal showing recent sync events + manual "Sync now"
 * button + conflict-resolution tab (BACKLOG-153, S33-S34).
 */

import { useState } from 'react';
import { X, RefreshCw, AlertTriangle, FileWarning } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/services/api';
import type { SyncEvent } from '@/types';
import type { SyncStatusKind } from '@/hooks/useSyncStatus';
import { useSyncConflicts } from '@/hooks/useSyncConflicts';
import { SyncEventList, shortPath } from './SyncEventList';

interface Props {
  status: SyncStatusKind;
  lastSyncedAt: string | null;
  events: SyncEvent[];
  connected: boolean;
  onClose: () => void;
}

type Tab = 'activity' | 'conflicts';

export function SyncDetailsPanel({ status, lastSyncedAt, events, connected, onClose }: Props) {
  const [scanning, setScanning] = useState(false);
  const [resolvingId, setResolvingId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>('activity');

  // Always poll conflicts while the panel is open — it's lightweight and the
  // user explicitly clicked through to look at sync state.
  const { conflicts, refresh: refreshConflicts, resolve } = useSyncConflicts(true);

  const handleScan = async () => {
    setScanning(true);
    try {
      const result = await api.scanAndSync();
      toast.success(result.message ?? 'Sync complete');
      void refreshConflicts();
    } catch (err) {
      toast.error('Sync failed — see details');
      // eslint-disable-next-line no-console
      console.error('scanAndSync failed', err);
    } finally {
      setScanning(false);
    }
  };

  const handleResolve = async (syncId: number, useFile: boolean) => {
    setResolvingId(syncId);
    try {
      const result = await resolve(syncId, useFile);
      toast.success(result.message ?? 'Conflict resolved');
    } catch (err) {
      toast.error('Failed to resolve conflict');
      // eslint-disable-next-line no-console
      console.error('resolveSyncConflict failed', err);
    } finally {
      setResolvingId(null);
    }
  };

  const headerLabel = (() => {
    if (!connected) return 'Disconnected from backend';
    if (status === 'syncing' || scanning) return 'Sync in progress…';
    if (status === 'error') return 'Sync errors detected';
    if (status === 'conflict' || conflicts.length > 0) return 'Conflicts need resolution';
    if (lastSyncedAt) return `Last synced at ${new Date(lastSyncedAt).toLocaleString()}`;
    return 'No sync activity yet';
  })();

  const showConflictsTab = conflicts.length > 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg bg-gray-900 rounded-xl shadow-2xl border border-gray-800 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <RefreshCw
              className={`w-4 h-4 ${(status === 'syncing' || scanning) ? 'animate-spin text-primary-400' : 'text-gray-500'}`}
            />
            <h2 className="text-sm font-semibold text-white">File sync</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/10"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-5 py-3 border-b border-gray-800 flex items-center justify-between gap-3">
          <p className="text-xs text-gray-400">{headerLabel}</p>
          <button
            type="button"
            onClick={handleScan}
            disabled={scanning || status === 'syncing'}
            className="text-xs font-medium px-3 py-1.5 rounded-md bg-primary-500/15 text-primary-400 hover:bg-primary-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {scanning ? 'Syncing…' : 'Sync now'}
          </button>
        </div>

        {showConflictsTab && (
          <div className="px-5 pt-2 border-b border-gray-800 flex items-center gap-1 text-xs">
            <button
              type="button"
              onClick={() => setTab('activity')}
              className={`px-3 py-1.5 rounded-t-md transition-colors ${tab === 'activity' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
              Activity
            </button>
            <button
              type="button"
              onClick={() => setTab('conflicts')}
              className={`px-3 py-1.5 rounded-t-md transition-colors flex items-center gap-1.5 ${tab === 'conflicts' ? 'bg-gray-800 text-white' : 'text-gray-400 hover:text-gray-200'}`}
            >
              <AlertTriangle className="w-3 h-3 text-amber-400" />
              Conflicts ({conflicts.length})
            </button>
          </div>
        )}

        <div className="max-h-80 overflow-y-auto">
          {tab === 'conflicts' && showConflictsTab ? (
            <ul className="divide-y divide-gray-800/60">
              {conflicts.map((c) => {
                const path = shortPath(c.file_path) ?? c.file_path;
                const lastSynced = c.last_synced
                  ? new Date(c.last_synced).toLocaleString()
                  : 'never';
                const busy = resolvingId === c.id;
                return (
                  <li key={c.id} className="px-5 py-3">
                    <div className="flex items-start gap-2">
                      <FileWarning className="w-3.5 h-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs text-gray-200 truncate font-mono" title={c.file_path}>
                          {path}
                        </p>
                        <p className="text-[10px] text-gray-500 mt-0.5">
                          Last synced: {lastSynced}
                        </p>
                        {c.error_message && (
                          <p className="text-[10px] text-red-400 mt-0.5 truncate" title={c.error_message}>
                            {c.error_message}
                          </p>
                        )}
                        <div className="flex items-center gap-2 mt-2">
                          <button
                            type="button"
                            onClick={() => handleResolve(c.id, true)}
                            disabled={busy}
                            className="text-[11px] px-2.5 py-1 rounded-md bg-emerald-500/15 text-emerald-400 hover:bg-emerald-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {busy ? 'Resolving…' : 'Use file version'}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleResolve(c.id, false)}
                            disabled={busy}
                            className="text-[11px] px-2.5 py-1 rounded-md bg-primary-500/15 text-primary-400 hover:bg-primary-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            Use database version
                          </button>
                        </div>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <SyncEventList
              events={events}
              emptyMessage='No recent sync events. Click "Sync now" to scan your synced notes folder.'
            />
          )}
        </div>
      </div>
    </div>
  );
}
