/**
 * Momentum scoring utilities
 */

/** Shared thresholds for momentum level boundaries (used by heatmap, labels, colors) */
export const MOMENTUM_THRESHOLDS = {
  LOW: 0.2,
  MODERATE: 0.4,
  STRONG: 0.7,
} as const;

export type MomentumLevel = 'weak' | 'low' | 'moderate' | 'strong';

export function getMomentumLevel(score: number): MomentumLevel {
  if (score >= MOMENTUM_THRESHOLDS.STRONG) return 'strong';
  if (score >= MOMENTUM_THRESHOLDS.MODERATE) return 'moderate';
  if (score >= MOMENTUM_THRESHOLDS.LOW) return 'low';
  return 'weak';
}

export function getMomentumColor(score: number): string {
  const level = getMomentumLevel(score);
  const colors = {
    weak: '#ef4444', // red-500
    low: '#f97316', // orange-500
    moderate: '#eab308', // yellow-500
    strong: '#22c55e', // green-500
  };
  return colors[level];
}

export function getMomentumBgColor(score: number): string {
  const level = getMomentumLevel(score);
  const colors = {
    weak: 'bg-red-100',
    low: 'bg-orange-100',
    moderate: 'bg-yellow-100',
    strong: 'bg-green-100',
  };
  return colors[level];
}

export function getMomentumTextColor(score: number): string {
  const level = getMomentumLevel(score);
  const colors = {
    weak: 'text-red-700',
    low: 'text-orange-700',
    moderate: 'text-yellow-700',
    strong: 'text-green-700',
  };
  return colors[level];
}

export function getMomentumLabel(score: number): string {
  const level = getMomentumLevel(score);
  const labels = {
    weak: 'Weak',
    low: 'Low',
    moderate: 'Moderate',
    strong: 'Strong',
  };
  return labels[level];
}

export function formatMomentumScore(score: number): string {
  return (score * 100).toFixed(0) + '%';
}
