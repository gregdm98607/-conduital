/**
 * TrialBanner — Day 7 / 11 / 13 trial expiry prompts.
 *
 * Decision matrix (days remaining, inclusive of today):
 *   8+   → nothing
 *   4-7  → Day-7 sticky top banner (amber, dismissible per session)
 *   2-3  → Day-11 sticky top banner (red, dismissible per session)
 *   0-1  → Day-13 blocking modal (cannot dismiss, only Upgrade or Request Extension)
 *   <0   → trial expired, /license/status will report is_trial_active=false → nothing
 *
 * Telemetry: emits *_shown once per session per tier, *_dismissed on user dismiss.
 * Paid users and free-tier-after-expiry users see nothing.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, X, Clock } from 'lucide-react';
import { useTrialStatus } from '@/hooks/useTrialStatus';
import { telemetry } from '@/services/telemetry';

const SESSION_DISMISS_DAY7 = 'trial_banner_day7_dismissed';
const SESSION_DISMISS_DAY11 = 'trial_banner_day11_dismissed';
const SESSION_SHOWN_DAY7 = 'trial_banner_day7_shown';
const SESSION_SHOWN_DAY11 = 'trial_banner_day11_shown';
const SESSION_SHOWN_DAY13 = 'trial_banner_day13_shown';

type BannerTier = 'day7' | 'day11' | 'day13' | null;

function pickTier(daysRemaining: number | null): BannerTier {
  if (daysRemaining === null) return null;
  if (daysRemaining <= 1) return 'day13';
  if (daysRemaining <= 3) return 'day11';
  if (daysRemaining <= 7) return 'day7';
  return null;
}

export function TrialBanner() {
  const { loaded, isTrialActive, isPaid, daysRemaining } = useTrialStatus();
  const [day7Dismissed, setDay7Dismissed] = useState(
    () => sessionStorage.getItem(SESSION_DISMISS_DAY7) === 'true'
  );
  const [day11Dismissed, setDay11Dismissed] = useState(
    () => sessionStorage.getItem(SESSION_DISMISS_DAY11) === 'true'
  );
  const [extensionRequested, setExtensionRequested] = useState(false);

  const tier = !loaded || !isTrialActive || isPaid ? null : pickTier(daysRemaining);

  // Fire *_shown once per session per tier
  useEffect(() => {
    if (tier === 'day7' && !sessionStorage.getItem(SESSION_SHOWN_DAY7) && !day7Dismissed) {
      telemetry.track('trial_day_7_banner_shown', { days_remaining: daysRemaining });
      sessionStorage.setItem(SESSION_SHOWN_DAY7, 'true');
    } else if (tier === 'day11' && !sessionStorage.getItem(SESSION_SHOWN_DAY11) && !day11Dismissed) {
      telemetry.track('trial_day_11_banner_shown', { days_remaining: daysRemaining });
      sessionStorage.setItem(SESSION_SHOWN_DAY11, 'true');
    } else if (tier === 'day13' && !sessionStorage.getItem(SESSION_SHOWN_DAY13)) {
      telemetry.track('trial_day_13_modal_shown', { days_remaining: daysRemaining });
      sessionStorage.setItem(SESSION_SHOWN_DAY13, 'true');
    }
  }, [tier, daysRemaining, day7Dismissed, day11Dismissed]);

  const dismissDay7 = () => {
    sessionStorage.setItem(SESSION_DISMISS_DAY7, 'true');
    setDay7Dismissed(true);
    telemetry.track('trial_day_7_banner_dismissed', { days_remaining: daysRemaining });
  };

  const dismissDay11 = () => {
    sessionStorage.setItem(SESSION_DISMISS_DAY11, 'true');
    setDay11Dismissed(true);
    telemetry.track('trial_day_11_banner_dismissed', { days_remaining: daysRemaining });
  };

  const requestExtension = () => {
    setExtensionRequested(true);
    telemetry.track('trial_extension_requested', { days_remaining: daysRemaining });
  };

  if (tier === 'day13') {
    return (
      <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-md w-full p-6 space-y-5">
          <div className="flex items-start gap-3">
            <div className="shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center">
              <Clock className="w-5 h-5 text-red-600 dark:text-red-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                Trial ends tomorrow
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Your free trial of Conduital expires in less than 24 hours. Upgrade now to
                keep full access to projects, the inbox, AI features, and weekly review.
              </p>
            </div>
          </div>

          {extensionRequested ? (
            <div className="rounded-lg bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 px-3 py-2 text-sm">
              Extension request received — we&apos;ll review it shortly.
            </div>
          ) : null}

          <div className="flex flex-col gap-2">
            <Link
              to="/settings"
              className="btn btn-primary w-full justify-center"
            >
              Upgrade now
            </Link>
            <button
              type="button"
              onClick={requestExtension}
              disabled={extensionRequested}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 underline-offset-2 hover:underline disabled:opacity-50 disabled:no-underline"
            >
              {extensionRequested ? 'Extension requested' : 'Request a 7-day extension'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (tier === 'day11' && !day11Dismissed) {
    return (
      <div className="bg-red-600 text-white px-4 py-2.5 flex items-center gap-3 shadow-md">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        <span className="text-sm flex-1">
          <strong>Only {daysRemaining} day{daysRemaining === 1 ? '' : 's'} left</strong> in
          your trial. Upgrade to keep full access after it expires.
        </span>
        <Link
          to="/settings"
          className="text-sm font-medium bg-white/15 hover:bg-white/25 px-3 py-1 rounded-md transition-colors"
        >
          See plans
        </Link>
        <button
          type="button"
          onClick={dismissDay11}
          aria-label="Dismiss"
          className="text-white/80 hover:text-white p-1 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  if (tier === 'day7' && !day7Dismissed) {
    return (
      <div className="bg-amber-500 text-amber-950 px-4 py-2.5 flex items-center gap-3 shadow-sm">
        <Clock className="w-4 h-4 shrink-0" />
        <span className="text-sm flex-1">
          <strong>{daysRemaining} days left</strong> in your trial. Choose a plan to keep
          full access when it ends.
        </span>
        <Link
          to="/settings"
          className="text-sm font-medium bg-amber-900/15 hover:bg-amber-900/25 px-3 py-1 rounded-md transition-colors"
        >
          See plans
        </Link>
        <button
          type="button"
          onClick={dismissDay7}
          aria-label="Dismiss"
          className="text-amber-950/70 hover:text-amber-950 p-1 rounded"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return null;
}
