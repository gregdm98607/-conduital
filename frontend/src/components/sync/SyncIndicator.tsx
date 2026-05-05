/**
 * SyncIndicator — sidebar footer indicator for live file-sync state
 * (BACKLOG-153, S33).
 *
 * Replaces the static "File Sync" placeholder in the Layout footer with a
 * live status: spinning icon while syncing, green/red/amber dot when idle,
 * relative timestamp ("Synced 2m ago"). Click opens SyncDetailsPanel.
 */

import { useState } from 'react';
import { CloudCog, CloudOff, AlertCircle, RefreshCw } from 'lucide-react';
import { useSyncStatus, relativeTime, type SyncStatusKind } from '@/hooks/useSyncStatus';
import { SyncDetailsPanel } from './SyncDetailsPanel';

function statusLabel(status: SyncStatusKind, lastSyncedAt: string | null): string {
  switch (status) {
    case 'syncing':
      return 'Syncing…';
    case 'error':
      return 'Sync error';
    case 'conflict':
      return 'Sync conflict';
    case 'idle':
    default:
      return lastSyncedAt ? `Synced ${relativeTime(lastSyncedAt)}` : 'Not yet synced';
  }
}

function StatusIcon({ status }: { status: SyncStatusKind }) {
  if (status === 'syncing') {
    return <RefreshCw className="w-3 h-3 animate-spin text-primary-400" />;
  }
  if (status === 'error') {
    return <AlertCircle className="w-3 h-3 text-red-400" />;
  }
  if (status === 'conflict') {
    return <AlertCircle className="w-3 h-3 text-amber-400" />;
  }
  return <CloudCog className="w-3 h-3 text-gray-500" />;
}

interface Props {
  appVersion?: string | null;
}

export function SyncIndicator({ appVersion }: Props) {
  const { status, lastSyncedAt, events, errorCount, conflictCount, connected } = useSyncStatus();
  const [open, setOpen] = useState(false);

  const label = statusLabel(status, lastSyncedAt);
  const offline = !connected && status === 'idle' && lastSyncedAt === null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="w-full flex items-center justify-center gap-1.5 text-[11px] text-gray-500 hover:text-gray-300 transition-colors py-0.5 rounded"
        title={offline ? 'Backend disconnected' : 'View sync activity'}
      >
        {offline ? (
          <CloudOff className="w-3 h-3 text-gray-600" />
        ) : (
          <StatusIcon status={status} />
        )}
        <span>{offline ? 'Offline' : label}</span>
        {(errorCount > 0 || conflictCount > 0) && (
          <span className="ml-1 text-[10px] px-1 rounded bg-red-500/20 text-red-300">
            {errorCount + conflictCount}
          </span>
        )}
        {appVersion && (
          <>
            <span className="text-gray-700">·</span>
            <span className="text-gray-700">v{appVersion}</span>
          </>
        )}
      </button>

      {open && (
        <SyncDetailsPanel
          onClose={() => setOpen(false)}
          status={status}
          lastSyncedAt={lastSyncedAt}
          events={events}
          connected={connected}
        />
      )}
    </>
  );
}
