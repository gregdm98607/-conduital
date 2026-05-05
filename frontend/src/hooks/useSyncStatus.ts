/**
 * Live file-sync status (BACKLOG-153, S33).
 *
 * Subscribes to /ws/sync-status, falls back to a one-shot HTTP fetch of
 * /sync/events when the socket is unavailable. Exposes:
 *
 *   - status:        'idle' | 'syncing' | 'error' | 'conflict'
 *   - lastSyncedAt:  ISO timestamp of the most recent successful completion
 *   - events:        recent sync events (newest first, capped)
 *   - errorCount:    count of unresolved error events in the buffer
 *   - conflictCount: count of unresolved conflict events in the buffer
 *
 * Polling on /sync/events is the safety net — if the WS reconnect loop is in
 * a backoff window, the indicator still updates within ~30s.
 */

import { useEffect, useRef, useState } from 'react';
import { api } from '@/services/api';
import type { SyncEvent } from '@/types';

const MAX_EVENTS = 20;
const HTTP_FALLBACK_INTERVAL_MS = 30_000;

export type SyncStatusKind = 'idle' | 'syncing' | 'error' | 'conflict';

export interface SyncStatusValue {
  status: SyncStatusKind;
  lastSyncedAt: string | null;
  events: SyncEvent[];
  errorCount: number;
  conflictCount: number;
  connected: boolean;
}

type WSMessage =
  | { type: 'snapshot'; events: SyncEvent[]; last_synced_at: string | null }
  | { type: 'event'; event: SyncEvent };

function deriveStatus(events: SyncEvent[]): SyncStatusKind {
  // Walk newest → oldest: the first terminal event wins.
  for (const e of events) {
    if (e.action === 'scan_completed') return 'idle';
    if (e.action === 'scan_started') return 'syncing';
    if (e.action === 'conflict_detected') return 'conflict';
    if (e.action === 'sync_error') return 'error';
    if (e.action === 'file_synced' || e.action === 'project_synced') return 'idle';
  }
  return 'idle';
}

function countUnresolved(events: SyncEvent[], action: SyncEvent['action']): number {
  return events.filter((e) => e.action === action && !e.success).length;
}

function resolveWsUrl(): string {
  const apiBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (apiBase) {
    try {
      const url = new URL(apiBase);
      const proto = url.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${proto}//${url.host}/ws/sync-status`;
    } catch {
      // fall through
    }
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws/sync-status`;
}

export function useSyncStatus(enabled: boolean = true): SyncStatusValue {
  const [events, setEvents] = useState<SyncEvent[]>([]);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [connected, setConnected] = useState<boolean>(false);

  // Keep a ref for the polling fallback so it doesn't stomp WS state.
  const wsConnectedRef = useRef<boolean>(false);

  useEffect(() => {
    if (!enabled) return;

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let reconnectDelay = 1_000;
    let cancelled = false;

    const connect = () => {
      if (cancelled) return;
      try {
        socket = new WebSocket(resolveWsUrl());
      } catch {
        scheduleReconnect();
        return;
      }

      socket.onopen = () => {
        reconnectDelay = 1_000;
        wsConnectedRef.current = true;
        setConnected(true);
      };

      socket.onmessage = (evt) => {
        let msg: WSMessage;
        try {
          msg = JSON.parse(evt.data);
        } catch {
          return;
        }
        if (msg.type === 'snapshot') {
          setEvents(msg.events.slice(0, MAX_EVENTS));
          setLastSyncedAt(msg.last_synced_at);
        } else if (msg.type === 'event') {
          setEvents((prev) => [msg.event, ...prev].slice(0, MAX_EVENTS));
          if (msg.event.success && (msg.event.action === 'file_synced'
              || msg.event.action === 'project_synced'
              || msg.event.action === 'scan_completed')) {
            setLastSyncedAt(msg.event.timestamp);
          }
        }
      };

      socket.onclose = () => {
        wsConnectedRef.current = false;
        setConnected(false);
        if (!cancelled) scheduleReconnect();
      };

      socket.onerror = () => {
        try {
          socket?.close();
        } catch {
          // ignore
        }
      };
    };

    const scheduleReconnect = () => {
      if (cancelled || reconnectTimer) return;
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null;
        reconnectDelay = Math.min(reconnectDelay * 2, 30_000);
        connect();
      }, reconnectDelay);
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      try {
        socket?.close();
      } catch {
        // ignore
      }
    };
  }, [enabled]);

  // HTTP fallback: keep state warm if the WS is disconnected.
  useEffect(() => {
    if (!enabled) return;

    let cancelled = false;
    const tick = async () => {
      if (cancelled || wsConnectedRef.current) return;
      try {
        const data = await api.getSyncEvents(MAX_EVENTS);
        if (cancelled) return;
        setEvents(data.events);
        setLastSyncedAt(data.last_synced_at);
      } catch {
        // ignore — WS will recover or next tick will retry
      }
    };

    // Initial fetch so first paint isn't empty even if WS is racing startup.
    tick();
    const interval = setInterval(tick, HTTP_FALLBACK_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [enabled]);

  return {
    status: deriveStatus(events),
    lastSyncedAt,
    events,
    errorCount: countUnresolved(events, 'sync_error'),
    conflictCount: countUnresolved(events, 'conflict_detected'),
    connected,
  };
}
