/**
 * useTrialStatus — derives daysRemaining and banner state from /license/status.
 *
 * The 14-day reverse trial gives every install full-tier access for two weeks.
 * We surface a Day-7 banner, a stronger Day-11 banner, and a blocking Day-13
 * modal (per CPO Trial Conversion Plan). All dismissals are per-launch
 * (sessionStorage) so the user sees the prompt again next time the app opens.
 */

import { useEffect, useState } from 'react';
import { api } from '@/services/api';

export interface TrialStatus {
  loaded: boolean;
  isTrialActive: boolean;
  isPaid: boolean;
  daysRemaining: number | null;
  trialExpiresAt: Date | null;
}

const REFRESH_INTERVAL_MS = 1000 * 60 * 30; // 30 min — trial is day-granular

export function useTrialStatus(): TrialStatus {
  const [status, setStatus] = useState<TrialStatus>({
    loaded: false,
    isTrialActive: false,
    isPaid: false,
    daysRemaining: null,
    trialExpiresAt: null,
  });

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await api.getLicenseStatus();
        if (cancelled) return;
        const expiresAt = data.trial_expires_at ? new Date(data.trial_expires_at) : null;
        const daysRemaining = expiresAt
          ? Math.ceil((expiresAt.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
          : null;
        setStatus({
          loaded: true,
          isTrialActive: data.is_trial_active,
          isPaid: data.is_paid,
          daysRemaining,
          trialExpiresAt: expiresAt,
        });
      } catch {
        if (!cancelled) {
          setStatus(prev => ({ ...prev, loaded: true }));
        }
      }
    };

    load();
    const id = setInterval(load, REFRESH_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return status;
}
