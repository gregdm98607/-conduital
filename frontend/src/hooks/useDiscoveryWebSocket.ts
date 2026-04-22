/**
 * WebSocket subscription for real-time auto-discovery events (DEBT-016).
 *
 * Connects to /ws/discovery-status and pushes each event into the
 * ['discovery', 'status'] TanStack Query cache so Settings -> Discovery
 * Activity updates instantly instead of waiting for the 30s poll.
 *
 * Polling in `useDiscoveryStatus` remains as a fallback for when the
 * socket is disconnected (startup race, backend restart, network blip).
 */

import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

type DiscoveryEvent = {
  timestamp: string;
  action: string;
  folder: string;
  success: boolean;
  error?: string;
  detail?: string;
};

type DiscoveryStatus = {
  total_events: number;
  error_count: number;
  events: DiscoveryEvent[];
};

type WSMessage =
  | { type: 'snapshot'; events: DiscoveryEvent[] }
  | { type: 'event'; event: DiscoveryEvent };

const MAX_EVENTS = 20;

function buildStatus(events: DiscoveryEvent[]): DiscoveryStatus {
  return {
    total_events: events.length,
    error_count: events.filter((e) => !e.success).length,
    events,
  };
}

function resolveWsUrl(): string {
  // Frontend API base URL is an http(s) URL (e.g. http://localhost:8000/api/v1).
  // The WS endpoint lives at ws(s)://<host>/ws/discovery-status on the same origin.
  const apiBase = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (apiBase) {
    try {
      const url = new URL(apiBase);
      const proto = url.protocol === 'https:' ? 'wss:' : 'ws:';
      return `${proto}//${url.host}/ws/discovery-status`;
    } catch {
      // fall through to same-origin default
    }
  }
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/ws/discovery-status`;
}

export function useDiscoveryWebSocket(enabled: boolean = true): void {
  const queryClient = useQueryClient();

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
      };

      socket.onmessage = (evt) => {
        let msg: WSMessage;
        try {
          msg = JSON.parse(evt.data);
        } catch {
          return;
        }

        queryClient.setQueryData<DiscoveryStatus>(
          ['discovery', 'status'],
          (prev) => {
            if (msg.type === 'snapshot') {
              return buildStatus(msg.events.slice(0, MAX_EVENTS));
            }
            if (msg.type === 'event') {
              const existing = prev?.events ?? [];
              const next = [msg.event, ...existing].slice(0, MAX_EVENTS);
              return buildStatus(next);
            }
            return prev;
          },
        );
      };

      socket.onclose = () => {
        if (!cancelled) scheduleReconnect();
      };

      socket.onerror = () => {
        try {
          socket?.close();
        } catch {
          // ignore; onclose will handle reconnect
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
  }, [enabled, queryClient]);
}
