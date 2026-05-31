/**
 * LicenseBadge — always-visible tier pill in the sidebar footer (BACKLOG-160).
 *
 * License tier is otherwise only surfaced on the Settings page. The Welcome
 * modal covers the activation moment and the TrialBanner covers expiry; this
 * pill covers every other moment. Clicking it navigates to Settings → License.
 *
 * Three states (label logic mirrors Settings.tsx):
 *   - Paid  → 'GTD+' (effective_tier 'full') or 'GTD'
 *   - Trial → 'Free Trial · Nd'
 *   - Free  → 'Free' (trial expired, not purchased)
 */

import { Link } from 'react-router-dom';
import { Sparkles, Clock, Lock, type LucideIcon } from 'lucide-react';
import { useTrialStatus } from '@/hooks/useTrialStatus';
import { telemetry } from '@/services/telemetry';

export function LicenseBadge() {
  const { loaded, isPaid, isTrialActive, daysRemaining, tier, effectiveTier } =
    useTrialStatus();

  // Avoid a flash of the wrong tier before /license/status resolves.
  if (!loaded) return null;

  let label: string;
  let Icon: LucideIcon;
  let pillClass: string;
  let title: string;

  if (isPaid) {
    label = effectiveTier === 'full' ? 'GTD+' : 'GTD';
    Icon = Sparkles;
    pillClass =
      'bg-primary-500/10 text-primary-400 border-primary-500/20 hover:bg-primary-500/20';
    title = `Licensed — ${label}. Manage your license in Settings.`;
  } else if (isTrialActive) {
    const hasDays = daysRemaining != null && daysRemaining > 0;
    label = hasDays ? `Free Trial · ${daysRemaining}d` : 'Free Trial';
    Icon = Clock;
    pillClass =
      'bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20';
    title = hasDays
      ? `Free trial — ${daysRemaining} day${daysRemaining === 1 ? '' : 's'} left. See plans in Settings.`
      : 'Free trial active. See plans in Settings.';
  } else {
    label = 'Free';
    Icon = Lock;
    pillClass =
      'bg-gray-700/40 text-gray-400 border-gray-700 hover:bg-gray-700/60';
    title = 'Free tier. See plans in Settings.';
  }

  const handleClick = () => {
    telemetry.track('license_badge_clicked', {
      tier,
      effective_tier: effectiveTier,
      is_paid: isPaid,
      is_trial_active: isTrialActive,
      days_remaining: daysRemaining,
    });
  };

  return (
    <Link
      to="/settings"
      onClick={handleClick}
      title={title}
      aria-label={title}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg border text-xs font-medium transition-colors ${pillClass}`}
    >
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span className="truncate">{label}</span>
    </Link>
  );
}
