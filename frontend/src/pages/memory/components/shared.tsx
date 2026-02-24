/**
 * Shared helper components and utilities for the Memory page tabs.
 */

/** Energy level scale used by session capture (1 = low, 5 = high) */
export const ENERGY_LEVELS = [1, 2, 3, 4, 5] as const;

export function getPriorityColor(priority: number): string {
  if (priority >= 80) return 'text-red-600 dark:text-red-400';
  if (priority >= 60) return 'text-orange-600 dark:text-orange-400';
  if (priority >= 40) return 'text-blue-600 dark:text-blue-400';
  return 'text-gray-500 dark:text-gray-400';
}

export function getPriorityBg(priority: number): string {
  if (priority >= 80) return 'bg-red-100 dark:bg-red-900/30';
  if (priority >= 60) return 'bg-orange-100 dark:bg-orange-900/30';
  if (priority >= 40) return 'bg-blue-100 dark:bg-blue-900/30';
  return 'bg-gray-100 dark:bg-gray-800';
}

export function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: number | string;
  sub?: string;
}) {
  return (
    <div className="card text-center py-4">
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{value}</p>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{label}</p>
      {sub && <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

export function MiniBar({
  label,
  count,
  total,
  colorClass,
}: {
  label: string;
  count: number;
  total: number;
  colorClass: string;
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-32 text-gray-600 dark:text-gray-400 truncate flex-shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${colorClass} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-gray-900 dark:text-gray-100 font-medium tabular-nums flex-shrink-0">
        {count}
      </span>
      <span className="w-8 text-right text-gray-400 dark:text-gray-500 text-xs tabular-nums flex-shrink-0">
        {pct}%
      </span>
    </div>
  );
}

export function EnergyDots({ level }: { level: number }) {
  return (
    <span className="flex items-center gap-0.5" title={`Energy: ${level}/5`}>
      {ENERGY_LEVELS.map((n) => (
        <span
          key={n}
          className={`w-2 h-2 rounded-full ${
            n <= level
              ? level >= 4
                ? 'bg-green-500'
                : level >= 2
                ? 'bg-yellow-500'
                : 'bg-red-400'
              : 'bg-gray-200 dark:bg-gray-600'
          }`}
        />
      ))}
    </span>
  );
}
