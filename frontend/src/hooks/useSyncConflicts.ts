/**
 * useSyncConflicts — fetches unresolved file-sync conflicts (BACKLOG-153, S34).
 *
 * Polls /api/v1/sync/conflicts whenever the parent surface reports a conflict
 * status (or when a `conflict_detected` event arrives). Refetches lazily —
 * the conflict list rarely grows, so we don't need a tight polling loop.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '@/services/api';
import type { SyncConflict } from '@/types';

export interface SyncConflictsValue {
  conflicts: SyncConflict[];
  loading: boolean;
  refresh: () => Promise<void>;
  resolve: (syncId: number, useFile: boolean) => Promise<{ success: boolean; message: string }>;
}

const POLL_INTERVAL_MS = 30_000;

export function useSyncConflicts(active: boolean): SyncConflictsValue {
  const [conflicts, setConflicts] = useState<SyncConflict[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const cancelledRef = useRef<boolean>(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getSyncConflicts();
      if (!cancelledRef.current) setConflicts(data);
    } catch {
      // ignore — leave previous value visible
    } finally {
      if (!cancelledRef.current) setLoading(false);
    }
  }, []);

  const resolve = useCallback(
    async (syncId: number, useFile: boolean) => {
      const result = await api.resolveSyncConflict(syncId, useFile);
      // Optimistically drop the resolved row, then re-fetch authoritative state.
      setConflicts((prev) => prev.filter((c) => c.id !== syncId));
      void refresh();
      return result;
    },
    [refresh],
  );

  useEffect(() => {
    cancelledRef.current = false;
    if (!active) return;

    void refresh();
    const interval = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => {
      cancelledRef.current = true;
      clearInterval(interval);
    };
  }, [active, refresh]);

  return { conflicts, loading, refresh, resolve };
}
