/**
 * SyncDetailsPanel — modal showing recent sync events + manual "Sync now" button.
 * (BACKLOG-153, S33).
 */

import { useState } from 'react';
import { X, RefreshCw, AlertTriangle, CheckCircle2, FileCheck, FileWarning, Play, Square } from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/services/api';
import type { SyncEvent } from '@/types';
import type { SyncStatusKind } from '@/hooks/useSyncStatus';

interface Props {
  status: SyncStatusKind;
  lastSyncedAt: string | null;
  events: SyncEvent[];
  connected: boolean;
  onClose: () => void;
}

function eventIcon(event: SyncEvent) {
  if (!event.success) {
    if (event.action === 'conflict_detected') return <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />;
    return <FileWarning className="w-3.5 h-3.5 text-red-400" />;
  }
  switch (event.action) {
    case 'scan_started':
      return <Play className="w-3.5 h-3.5 text-primary-400" />;
    case 'scan_completed':
      return <Square className="w-3.5 h-3.5 text-primary-400" />;
    case 'file_synced':
      return <FileCheck className="w-3.5 h-3.5 text-emerald-400" />;
    case 'project_synced':
      return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
    default:
      return <FileCheck className="w-3.5 h-3.5 text-gray-400" />;
  }
}

function actionLabel(event: SyncEvent): string {
  switch (event.action) {
    case 'scan_started':
      return 'Scan started';
    case 'scan_completed':
      if (event.stats) {
        const { synced = 0, errors = 0 } = event.stats;
        return `Scan completed — ${synced} synced${errors ? `, ${errors} errors` : ''}`;
      }
      return 'Scan completed';
    case 'file_synced':
      return event.detail ? `Synced: ${event.detail}` : 'File synced';
    case 'project_synced':
      return event.detail ? `Project written: ${event.detail}` : 'Project synced to file';
    case 'conflict_detected':
      return event.error ? `Conflict: ${event.error}` : 'Conflict detected';
    case 'sync_error':
      return event.error ? `Error: ${event.error}` : 'Sync error';
    default:
      return event.action;
  }
}

function shortPath(path?: string): string | null {
  if (!path) return null;
  const norm = path.replace(/\\/g, '/');
  const parts = norm.split('/');
  return parts.slice(-2).join('/');
}

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleTimeString();
}

export function SyncDetailsPanel({ status, lastSyncedAt, events, connected, onClose }: Props) {
  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    setScanning(true);
    try {
      const result = await api.scanAndSync();
      toast.success(result.message ?? 'Sync complete');
    } catch (err) {
      toast.error('Sync failed — see details');
      // eslint-disable-next-line no-console
      console.error('scanAndSync failed', err);
    } finally {
      setScanning(false);
    }
  };

  const headerLabel = (() => {
    if (!connected) return 'Disconnected from backend';
    if (status === 'syncing' || scanning) return 'Sync in progress…';
    if (status === 'error') return 'Sync errors detected';
    if (status === 'conflict') return 'Conflicts need resolution';
    if (lastSyncedAt) return `Last synced at ${new Date(lastSyncedAt).toLocaleString()}`;
    return 'No sync activity yet';
  })();

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

        <div className="max-h-80 overflow-y-auto">
          {events.length === 0 ? (
            <p className="px-5 py-6 text-xs text-gray-500 text-center">
              No recent sync events. Click "Sync now" to scan your synced notes folder.
            </p>
          ) : (
            <ul className="divide-y divide-gray-800/60">
              {events.map((event, idx) => (
                <li
                  key={`${event.timestamp}-${idx}`}
                  className="px-5 py-2.5 flex items-start gap-2.5 hover:bg-white/[0.02]"
                >
                  <div className="mt-0.5 flex-shrink-0">{eventIcon(event)}</div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs ${event.success ? 'text-gray-200' : 'text-red-300'} truncate`}>
                      {actionLabel(event)}
                    </p>
                    {shortPath(event.file_path) && (
                      <p className="text-[10px] text-gray-500 truncate font-mono">
                        {shortPath(event.file_path)}
                      </p>
                    )}
                  </div>
                  <span className="text-[10px] text-gray-600 flex-shrink-0">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
