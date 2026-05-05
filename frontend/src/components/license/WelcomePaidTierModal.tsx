/**
 * WelcomePaidTierModal — celebratory state shown once per activation.
 *
 * Trigger flow:
 *   1. Settings.handleActivateLicense detects free → paid transition,
 *      writes the new tier to sessionStorage and dispatches
 *      `conduital:license-activated` with `{ tier, effective_tier }`.
 *   2. This component (mounted in Layout) listens for the event,
 *      reads sessionStorage on mount in case it was set just before nav,
 *      renders the modal, fires `welcome_paid_tier` telemetry once,
 *      and clears the flag on dismissal.
 *
 * Per-session: the flag clears on dismiss; if the user reloads before
 * dismissing, the modal re-shows (sessionStorage survives reload).
 */

import { useEffect, useState } from 'react';
import { Sparkles, X, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { telemetry } from '@/services/telemetry';

const SESSION_KEY = 'welcome_paid_tier_pending';

type Tier = 'gtd' | 'full' | string;

interface UnlockedFeature {
  title: string;
  description: string;
}

const FEATURES_BY_TIER: Record<string, UnlockedFeature[]> = {
  gtd: [
    {
      title: 'GTD Inbox',
      description: 'Capture anything in seconds, process on your own schedule.',
    },
    {
      title: 'Weekly Review',
      description: 'A guided pass to keep every project current and trustworthy.',
    },
    {
      title: 'Someday / Maybe',
      description: 'Park ideas without losing them — surface only when ready.',
    },
    {
      title: 'Waiting For',
      description: 'Track delegations and external dependencies in one place.',
    },
  ],
  full: [
    {
      title: 'GTD Inbox + Weekly Review',
      description: 'The full GTD workflow — capture, process, review.',
    },
    {
      title: 'Memory Layer',
      description: 'AI remembers your sessions, decisions, and context across days.',
    },
    {
      title: 'AI Context & Suggestions',
      description: 'Proactive nudges, decompose tasks, energy/context filters.',
    },
    {
      title: 'Goals, Visions & Horizons',
      description: 'Connect today’s work to the long-term picture.',
    },
  ],
};

function featuresForTier(tier: Tier): UnlockedFeature[] {
  return FEATURES_BY_TIER[tier] ?? FEATURES_BY_TIER.gtd;
}

function tierLabel(tier: Tier): string {
  if (tier === 'full') return 'GTD+';
  if (tier === 'gtd') return 'GTD';
  return tier.toUpperCase();
}

interface ActivationDetail {
  tier: Tier;
  effective_tier: Tier;
}

export function WelcomePaidTierModal() {
  const [activeTier, setActiveTier] = useState<Tier | null>(null);

  useEffect(() => {
    const pending = sessionStorage.getItem(SESSION_KEY);
    if (pending) {
      setActiveTier(pending);
    }

    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail as ActivationDetail | undefined;
      if (!detail) return;
      const tier = detail.effective_tier || detail.tier;
      sessionStorage.setItem(SESSION_KEY, tier);
      setActiveTier(tier);
    };

    window.addEventListener('conduital:license-activated', handler);
    return () => window.removeEventListener('conduital:license-activated', handler);
  }, []);

  useEffect(() => {
    if (activeTier) {
      telemetry.track('welcome_paid_tier', {
        tier: activeTier,
      });
    }
  }, [activeTier]);

  const dismiss = () => {
    sessionStorage.removeItem(SESSION_KEY);
    setActiveTier(null);
    telemetry.track('welcome_paid_tier_dismissed', {
      tier: activeTier ?? '',
    });
  };

  if (!activeTier) return null;

  const features = featuresForTier(activeTier);

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full overflow-hidden">
        <div className="bg-gradient-to-br from-primary-500 to-primary-700 px-6 py-5 text-white relative">
          <button
            type="button"
            onClick={dismiss}
            aria-label="Close"
            className="absolute top-3 right-3 p-1.5 rounded-md text-white/80 hover:text-white hover:bg-white/10"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-white/15 flex items-center justify-center">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-white/80">
                {tierLabel(activeTier)} unlocked
              </p>
              <h2 className="text-xl font-bold">Welcome to Conduital {tierLabel(activeTier)}</h2>
            </div>
          </div>
          <p className="text-sm text-white/85 mt-3">
            Your license is active. Here&apos;s what just opened up for you.
          </p>
        </div>

        <div className="px-6 py-5 space-y-3">
          {features.map((feature) => (
            <div key={feature.title} className="flex items-start gap-3">
              <CheckCircle2 className="w-5 h-5 text-primary-500 dark:text-primary-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {feature.title}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        <div className="px-6 py-4 bg-gray-50 dark:bg-gray-900/40 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={dismiss}
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
          >
            Maybe later
          </button>
          <Link
            to="/inbox"
            onClick={dismiss}
            className="btn btn-primary inline-flex items-center gap-1.5"
          >
            Start exploring
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
