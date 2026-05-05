/**
 * SyncEventList — shared renderer for sync events.
 *
 * Used by SyncDetailsPanel (sidebar modal) and Settings → Recent Sync Activity
 * (BACKLOG-153, S34). Owns the icon + label mapping so both surfaces stay in
 * sync visually.
 */

import { AlertTriangle, CheckCircle2, FileCheck, FileWarning, Play, Square } from 'lucide-react';
import type { SyncEvent } from '@/types';

export function eventIcon(event: SyncEvent) {
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

export function actionLabel(event: SyncEvent): string {
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

export function shortPath(path?: string): string | null {
  if (!path) return null;
  const norm = path.replace(/\\/g, '/');
  const parts = norm.split('/');
  return parts.slice(-2).join('/');
}

interface Props {
  events: SyncEvent[];
  emptyMessage?: string;
  className?: string;
}

export function SyncEventList({ events, emptyMessage, className }: Props) {
  if (events.length === 0) {
    return (
      <p className={`px-5 py-6 text-xs text-gray-500 text-center ${className ?? ''}`}>
        {emptyMessage ?? 'No recent sync events.'}
      </p>
    );
  }
  return (
    <ul className={`divide-y divide-gray-800/60 dark:divide-gray-800/60 ${className ?? ''}`}>
      {events.map((event, idx) => (
        <li
          key={`${event.timestamp}-${idx}`}
          className="px-5 py-2.5 flex items-start gap-2.5 hover:bg-white/[0.02]"
        >
          <div className="mt-0.5 flex-shrink-0">{eventIcon(event)}</div>
          <div className="flex-1 min-w-0">
            <p className={`text-xs ${event.success ? 'text-gray-700 dark:text-gray-200' : 'text-red-600 dark:text-red-300'} truncate`}>
              {actionLabel(event)}
            </p>
            {shortPath(event.file_path) && (
              <p className="text-[10px] text-gray-500 dark:text-gray-500 truncate font-mono">
                {shortPath(event.file_path)}
              </p>
            )}
          </div>
          <span className="text-[10px] text-gray-500 dark:text-gray-600 flex-shrink-0">
            {new Date(event.timestamp).toLocaleTimeString()}
          </span>
        </li>
      ))}
    </ul>
  );
}
