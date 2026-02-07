/**
 * Momentum scoring utilities
 */

export type MomentumLevel = 'weak' | 'low' | 'moderate' | 'strong';

export function getMomentumLevel(score: number): MomentumLevel {
  if (score >= 0.7) return 'strong';
  if (score >= 0.4) return 'moderate';
  if (score >= 0.2) return 'low';
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
