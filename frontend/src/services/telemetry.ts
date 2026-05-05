/**
 * Telemetry Client — PostHog event capture
 *
 * Singleton that batches analytics events and forwards them to the backend's
 * /api/v1/telemetry/events endpoint. Backend handles PostHog forwarding;
 * frontend never talks to PostHog directly.
 *
 * Lifecycle:
 *   1. init() runs once at App mount. Fetches distinct_id from backend
 *      (lazy — backend creates one on first call) and syncs opt-out flag.
 *   2. track(event, properties) appends to in-memory buffer.
 *   3. Buffer auto-flushes when it reaches MAX_BATCH events OR after
 *      FLUSH_INTERVAL_MS, whichever comes first.
 *   4. flush() runs on beforeunload (best-effort via sendBeacon).
 *
 * Opt-out:
 *   - Stored in localStorage AND backend (mirrored). localStorage is the
 *     fast path so we don't network-call before deciding to drop.
 *   - setOptOut(true) drains the buffer first, then stops capturing.
 *
 * Failure modes:
 *   - All errors swallowed. Telemetry must never disrupt UX.
 *   - If backend is down, events are dropped after one failed flush attempt.
 */

import axios, { AxiosError } from 'axios';

const TELEMETRY_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const LOCALSTORAGE_OPT_OUT = 'posthog_opt_out';
const LOCALSTORAGE_DISTINCT_ID = 'posthog_distinct_id';
const LOCALSTORAGE_FIRST_LAUNCH_SENT = 'posthog_first_launch_sent';

const MAX_BATCH = 10;
const FLUSH_INTERVAL_MS = 5000;

interface TelemetryEvent {
  event: string;
  properties: Record<string, string | number | boolean | null>;
}

class TelemetryClient {
  private distinctId: string | null = null;
  private optOut = false;
  private buffer: TelemetryEvent[] = [];
  private flushTimer: ReturnType<typeof setTimeout> | null = null;
  private initPromise: Promise<void> | null = null;

  /**
   * Initialise the client. Idempotent — safe to call multiple times.
   * Resolves once distinct_id is available (or init has failed silently).
   */
  init(): Promise<void> {
    if (this.initPromise) return this.initPromise;

    this.initPromise = (async () => {
      // Fast path: read opt-out from localStorage so capture() can short-circuit
      // before we even fetch distinct_id.
      this.optOut = localStorage.getItem(LOCALSTORAGE_OPT_OUT) === 'true';

      // Fast path: cached distinct_id from a prior session
      const cached = localStorage.getItem(LOCALSTORAGE_DISTINCT_ID);
      if (cached) {
        this.distinctId = cached;
      }

      // Always reconcile with backend (source of truth for distinct_id).
      try {
        const resp = await axios.get<{ distinct_id: string; is_new: boolean }>(
          `${TELEMETRY_BASE_URL}/telemetry/distinct-id`,
          { timeout: 5000 }
        );
        this.distinctId = resp.data.distinct_id;
        localStorage.setItem(LOCALSTORAGE_DISTINCT_ID, this.distinctId);

        // Fire app_first_launch exactly once per installation.
        // Use a localStorage flag rather than relying solely on backend's is_new
        // (which only flips on the very first /distinct-id call ever).
        if (resp.data.is_new && !localStorage.getItem(LOCALSTORAGE_FIRST_LAUNCH_SENT)) {
          this.track('app_first_launch', {});
          localStorage.setItem(LOCALSTORAGE_FIRST_LAUNCH_SENT, 'true');
        }
      } catch {
        // Backend unreachable — telemetry stays inactive for this session
      }

      // Drain any events queued before init() finished
      if (this.buffer.length > 0) this.scheduleFlush();

      // Best-effort flush on tab close
      window.addEventListener('beforeunload', () => this.flushSync());
    })();

    return this.initPromise;
  }

  /**
   * Capture an event. No-ops if opted out. Pre-init events are buffered
   * and drained once init() completes.
   */
  track(event: string, properties: Record<string, string | number | boolean | null> = {}): void {
    if (this.optOut) return;
    this.buffer.push({ event, properties });
    if (this.buffer.length >= MAX_BATCH) {
      this.flush();
    } else {
      this.scheduleFlush();
    }
  }

  /**
   * Update opt-out preference. Drains pending buffer first if turning OFF
   * tracking so we don't lose events that were captured while still opted in.
   */
  async setOptOut(value: boolean): Promise<void> {
    if (value && !this.optOut) {
      // Flush the buffer one last time before going dark
      await this.flush();
    }
    this.optOut = value;
    localStorage.setItem(LOCALSTORAGE_OPT_OUT, value ? 'true' : 'false');
    try {
      await axios.post(
        `${TELEMETRY_BASE_URL}/telemetry/opt-out`,
        { opt_out: value },
        { timeout: 5000 }
      );
    } catch {
      // Local state is authoritative for the UX; backend will reconcile
      // next time setOptOut() succeeds.
    }
  }

  isOptedOut(): boolean {
    return this.optOut;
  }

  /**
   * Flush the current buffer to the backend. Returns when the request
   * completes (success or failure). Safe to call concurrently.
   */
  async flush(): Promise<void> {
    if (this.flushTimer) {
      clearTimeout(this.flushTimer);
      this.flushTimer = null;
    }
    if (this.buffer.length === 0 || !this.distinctId || this.optOut) return;

    const events = this.buffer.splice(0, this.buffer.length);
    try {
      await axios.post(
        `${TELEMETRY_BASE_URL}/telemetry/events`,
        { distinct_id: this.distinctId, events, opt_out: false },
        { timeout: 5000 }
      );
    } catch (err) {
      // 422 means malformed event — drop them. Network errors also drop
      // (the backend is local; if it's down we have bigger problems).
      const status = (err as AxiosError)?.response?.status;
      if (status && status !== 422) {
        // Restore events for one retry on next flush cycle.
        // Cap to avoid unbounded growth if backend stays down.
        if (this.buffer.length < MAX_BATCH * 5) {
          this.buffer.unshift(...events);
        }
      }
    }
  }

  /**
   * Synchronous best-effort flush via navigator.sendBeacon (for beforeunload).
   * Skips if anything is missing — silent failure is acceptable.
   */
  private flushSync(): void {
    if (this.buffer.length === 0 || !this.distinctId || this.optOut) return;
    const payload = JSON.stringify({
      distinct_id: this.distinctId,
      events: this.buffer,
      opt_out: false,
    });
    try {
      const blob = new Blob([payload], { type: 'application/json' });
      navigator.sendBeacon(`${TELEMETRY_BASE_URL}/telemetry/events`, blob);
      this.buffer = [];
    } catch {
      // Browsers without sendBeacon — give up
    }
  }

  private scheduleFlush(): void {
    if (this.flushTimer) return;
    this.flushTimer = setTimeout(() => {
      this.flushTimer = null;
      this.flush();
    }, FLUSH_INTERVAL_MS);
  }
}

export const telemetry = new TelemetryClient();
export default telemetry;
