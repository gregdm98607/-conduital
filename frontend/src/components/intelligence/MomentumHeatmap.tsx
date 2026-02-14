import { useState, useMemo } from 'react';
import { Activity } from 'lucide-react';
import { useMomentumHeatmap } from '../../hooks/useIntelligence';

const WEEKS = 13; // 13 weeks = ~91 days
const DAYS_PER_WEEK = 7;
const DAY_LABELS = ['Mon', '', 'Wed', '', 'Fri', '', ''];

function getMomentumColor(value: number, hasData: boolean): string {
  if (!hasData) return 'bg-gray-100 dark:bg-gray-800';
  if (value <= 0) return 'bg-gray-200 dark:bg-gray-700';
  if (value < 0.25) return 'bg-emerald-100 dark:bg-emerald-900/40';
  if (value < 0.5) return 'bg-emerald-300 dark:bg-emerald-700/60';
  if (value < 0.75) return 'bg-emerald-500 dark:bg-emerald-600';
  return 'bg-emerald-700 dark:bg-emerald-500';
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function MomentumHeatmap() {
  const { data, isLoading } = useMomentumHeatmap(91);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; content: string } | null>(null);

  // Build the grid: 13 columns (weeks) × 7 rows (days)
  const grid = useMemo(() => {
    if (!data?.data) return [];

    // Build a lookup by date string
    const lookup = new Map(data.data.map(d => [d.date, d]));

    // Fill all 91 days ending today, then arrange into weeks
    const today = new Date();
    const totalDays = WEEKS * DAYS_PER_WEEK;

    const days: Array<{ date: string; avg_momentum: number; completions: number; hasData: boolean }> = [];
    for (let i = totalDays - 1; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const dateStr = d.toISOString().split('T')[0];
      const entry = lookup.get(dateStr);
      days.push({
        date: dateStr,
        avg_momentum: entry?.avg_momentum ?? 0,
        completions: entry?.completions ?? 0,
        hasData: entry ? (entry.avg_momentum > 0 || entry.completions > 0) : false,
      });
    }

    // Arrange into columns (weeks). Each column is a week Mon-Sun.
    // First, find what day of the week the first date is
    const firstDate = new Date(days[0].date + 'T00:00:00');
    const firstDayOfWeek = (firstDate.getDay() + 6) % 7; // Mon=0

    // Pad start with nulls if first date doesn't start on Monday
    const padded: typeof days = [];
    for (let i = 0; i < firstDayOfWeek; i++) {
      padded.push({ date: '', avg_momentum: 0, completions: 0, hasData: false });
    }
    padded.push(...days);

    // Split into weeks of 7
    const weeks: (typeof padded)[] = [];
    for (let i = 0; i < padded.length; i += 7) {
      weeks.push(padded.slice(i, i + 7));
    }

    return weeks;
  }, [data]);

  // Get month labels for the top
  const monthLabels = useMemo(() => {
    if (grid.length === 0) return [];
    const labels: { label: string; col: number }[] = [];
    let lastMonth = '';
    grid.forEach((week, colIdx) => {
      const firstDay = week.find(d => d && d.date);
      if (firstDay && firstDay.date) {
        const d = new Date(firstDay.date + 'T00:00:00');
        const month = d.toLocaleDateString('en-US', { month: 'short' });
        if (month !== lastMonth) {
          labels.push({ label: month, col: colIdx });
          lastMonth = month;
        }
      }
    });
    return labels;
  }, [grid]);

  if (isLoading) {
    return (
      <div className="mb-8">
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-emerald-600" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Momentum Activity</h3>
          </div>
          <div className="h-28 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" />
        </div>
      </div>
    );
  }

  return (
    <div className="mb-8">
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Momentum Activity</h3>
          <span className="text-xs text-gray-400 dark:text-gray-500">90 days</span>
        </div>

        <div className="overflow-x-auto relative">
          {/* Month labels */}
          <div className="flex ml-8 mb-1">
            {monthLabels.map((m, i) => (
              <span
                key={i}
                className="text-xs text-gray-400 dark:text-gray-500"
                style={{ position: 'absolute', left: `${m.col * 16 + 32}px` }}
              >
                {m.label}
              </span>
            ))}
          </div>

          <div className="flex gap-0.5 mt-5">
            {/* Day labels */}
            <div className="flex flex-col gap-0.5 mr-1">
              {DAY_LABELS.map((label, i) => (
                <div key={i} className="w-6 h-3 flex items-center justify-end">
                  <span className="text-[10px] text-gray-400 dark:text-gray-500">{label}</span>
                </div>
              ))}
            </div>

            {/* Grid */}
            {grid.map((week, colIdx) => (
              <div key={colIdx} className="flex flex-col gap-0.5">
                {week.map((day, rowIdx) => {
                  if (!day || !day.date) {
                    return <div key={rowIdx} className="w-3 h-3" />;
                  }
                  return (
                    <div
                      key={rowIdx}
                      className={`w-3 h-3 rounded-sm ${getMomentumColor(day.avg_momentum, day.hasData)} cursor-pointer transition-colors hover:ring-1 hover:ring-gray-400 dark:hover:ring-gray-500`}
                      onMouseEnter={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        setTooltip({
                          x: rect.left + rect.width / 2,
                          y: rect.top - 4,
                          content: `${formatDate(day.date)}: ${day.hasData ? `${(day.avg_momentum * 100).toFixed(0)}% momentum` : 'No data'}${day.completions > 0 ? `, ${day.completions} task${day.completions !== 1 ? 's' : ''} completed` : ''}`,
                        });
                      }}
                      onMouseLeave={() => setTooltip(null)}
                    />
                  );
                })}
              </div>
            ))}
          </div>

          {/* Tooltip */}
          {tooltip && (
            <div
              className="fixed z-50 px-2 py-1 text-xs bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded shadow-lg pointer-events-none whitespace-nowrap"
              style={{
                left: `${tooltip.x}px`,
                top: `${tooltip.y}px`,
                transform: 'translate(-50%, -100%)',
              }}
            >
              {tooltip.content}
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-2 mt-3 justify-end">
          <span className="text-[10px] text-gray-400 dark:text-gray-500">Less</span>
          <div className="w-3 h-3 rounded-sm bg-gray-200 dark:bg-gray-700" />
          <div className="w-3 h-3 rounded-sm bg-emerald-100 dark:bg-emerald-900/40" />
          <div className="w-3 h-3 rounded-sm bg-emerald-300 dark:bg-emerald-700/60" />
          <div className="w-3 h-3 rounded-sm bg-emerald-500 dark:bg-emerald-600" />
          <div className="w-3 h-3 rounded-sm bg-emerald-700 dark:bg-emerald-500" />
          <span className="text-[10px] text-gray-400 dark:text-gray-500">More</span>
        </div>
      </div>
    </div>
  );
}
