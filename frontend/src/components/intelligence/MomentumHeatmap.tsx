import { useState, useMemo, useCallback, useRef, useEffect } from 'react';
import { Activity } from 'lucide-react';
import { useMomentumHeatmap } from '../../hooks/useIntelligence';
import { MOMENTUM_THRESHOLDS } from '../../utils/momentum';

const WEEKS = 13; // 13 weeks = ~91 days
const DAYS_PER_WEEK = 7;
const DAY_LABELS = ['Mon', '', 'Wed', '', 'Fri', '', ''];

type DayCell = { date: string; avg_momentum: number; completions: number; hasData: boolean };

function getHeatmapColor(value: number, hasData: boolean): string {
  if (!hasData) return 'bg-gray-100 dark:bg-gray-800';
  if (value <= 0) return 'bg-gray-200 dark:bg-gray-700';
  if (value < MOMENTUM_THRESHOLDS.LOW) return 'bg-emerald-100 dark:bg-emerald-900/40';
  if (value < MOMENTUM_THRESHOLDS.MODERATE) return 'bg-emerald-300 dark:bg-emerald-700/60';
  if (value < MOMENTUM_THRESHOLDS.STRONG) return 'bg-emerald-500 dark:bg-emerald-600';
  return 'bg-emerald-700 dark:bg-emerald-500';
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function buildTooltipContent(day: DayCell): string {
  const datePart = formatDate(day.date);
  const momentumPart = day.hasData ? `${(day.avg_momentum * 100).toFixed(0)}% momentum` : 'No data';
  const taskPart = day.completions > 0
    ? `, ${day.completions} task${day.completions !== 1 ? 's' : ''} completed`
    : '';
  return `${datePart}: ${momentumPart}${taskPart}`;
}

export function MomentumHeatmap() {
  const { data, isLoading } = useMomentumHeatmap(91);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; content: string } | null>(null);
  const [focusedCell, setFocusedCell] = useState<{ col: number; row: number } | null>(null);
  const gridRef = useRef<HTMLDivElement>(null);
  const cellRefs = useRef<Map<string, HTMLDivElement>>(new Map());

  // Build the grid: 13 columns (weeks) × 7 rows (days)
  const grid = useMemo(() => {
    if (!data?.data) return [];

    const lookup = new Map(data.data.map(d => [d.date, d]));
    const today = new Date();
    const totalDays = WEEKS * DAYS_PER_WEEK;

    const days: DayCell[] = [];
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

    // Arrange into columns (weeks), Mon-Sun
    const firstDate = new Date(days[0].date + 'T00:00:00');
    const firstDayOfWeek = (firstDate.getDay() + 6) % 7; // Mon=0

    const padded: (DayCell | null)[] = [];
    for (let i = 0; i < firstDayOfWeek; i++) {
      padded.push(null);
    }
    padded.push(...days);

    const weeks: (DayCell | null)[][] = [];
    for (let i = 0; i < padded.length; i += 7) {
      weeks.push(padded.slice(i, i + 7));
    }

    return weeks;
  }, [data]);

  // Month labels: one label per first-appearance of a month, positioned by grid column
  const monthLabels = useMemo(() => {
    if (grid.length === 0) return [];
    const labels: { label: string; colStart: number; colSpan: number }[] = [];
    let lastMonth = '';
    let currentLabel: { label: string; colStart: number; colSpan: number } | null = null;

    grid.forEach((week, colIdx) => {
      const firstDay = week.find(d => d && d.date);
      if (firstDay && firstDay.date) {
        const d = new Date(firstDay.date + 'T00:00:00');
        const month = d.toLocaleDateString('en-US', { month: 'short' });
        if (month !== lastMonth) {
          if (currentLabel) labels.push(currentLabel);
          // +1 to account for the day-label column in the grid
          currentLabel = { label: month, colStart: colIdx + 2, colSpan: 1 };
          lastMonth = month;
        } else if (currentLabel) {
          currentLabel.colSpan++;
        }
      }
    });
    if (currentLabel) labels.push(currentLabel);
    return labels;
  }, [grid]);

  const showTooltipForCell = useCallback((el: HTMLElement, day: DayCell) => {
    const rect = el.getBoundingClientRect();
    setTooltip({
      x: rect.left + rect.width / 2,
      y: rect.top - 4,
      content: buildTooltipContent(day),
    });
  }, []);

  const hideTooltip = useCallback(() => setTooltip(null), []);

  // Keyboard navigation for the grid
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!focusedCell || grid.length === 0) return;
    let { col, row } = focusedCell;
    let handled = true;

    switch (e.key) {
      case 'ArrowRight': col = Math.min(col + 1, grid.length - 1); break;
      case 'ArrowLeft': col = Math.max(col - 1, 0); break;
      case 'ArrowDown': row = Math.min(row + 1, DAYS_PER_WEEK - 1); break;
      case 'ArrowUp': row = Math.max(row - 1, 0); break;
      case 'Home': col = 0; row = 0; break;
      case 'End': col = grid.length - 1; row = DAYS_PER_WEEK - 1; break;
      default: handled = false;
    }

    if (handled) {
      e.preventDefault();
      setFocusedCell({ col, row });
      const cellKey = `${col}-${row}`;
      const cellEl = cellRefs.current.get(cellKey);
      if (cellEl) {
        cellEl.focus();
        const day = grid[col]?.[row];
        if (day && day.date) {
          showTooltipForCell(cellEl, day);
        } else {
          hideTooltip();
        }
      }
    }
  }, [focusedCell, grid, showTooltipForCell, hideTooltip]);

  // Dismiss tooltip on outside touch
  useEffect(() => {
    if (!tooltip) return;
    const handler = () => setTooltip(null);
    document.addEventListener('touchstart', handler, { passive: true });
    return () => document.removeEventListener('touchstart', handler);
  }, [tooltip]);

  if (isLoading) {
    return (
      <div className="mb-8">
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-emerald-600" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Momentum Activity</h3>
          </div>
          <div className="h-28 bg-gray-100 dark:bg-gray-800 rounded animate-pulse" role="status" aria-label="Loading momentum heatmap" />
        </div>
      </div>
    );
  }

  const totalCols = grid.length + 1; // +1 for day-label column

  return (
    <div className="mb-8">
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-emerald-600" />
          <h3 id="heatmap-title" className="font-semibold text-gray-900 dark:text-gray-100">Momentum Activity</h3>
          <span className="text-xs text-gray-400 dark:text-gray-500">90 days</span>
        </div>

        <div className="overflow-x-auto">
          {/* CSS Grid layout: 1 day-label col + N week columns */}
          <div
            ref={gridRef}
            role="grid"
            aria-labelledby="heatmap-title"
            aria-rowcount={DAYS_PER_WEEK + 1}
            aria-colcount={totalCols}
            onKeyDown={handleKeyDown}
            className="inline-grid gap-0.5"
            style={{
              gridTemplateColumns: `24px repeat(${grid.length}, 12px)`,
              gridTemplateRows: `16px repeat(${DAYS_PER_WEEK}, 12px)`,
            }}
          >
            {/* Row 0: month labels */}
            <div /> {/* Empty top-left corner */}
            {grid.map((_, colIdx) => {
              const label = monthLabels.find(m => m.colStart === colIdx + 2);
              return (
                <div key={`month-${colIdx}`} className="flex items-end" role="columnheader">
                  {label && (
                    <span className="text-[10px] text-gray-400 dark:text-gray-500 leading-none whitespace-nowrap">
                      {label.label}
                    </span>
                  )}
                </div>
              );
            })}

            {/* Rows 1-7: day label + cells */}
            {Array.from({ length: DAYS_PER_WEEK }, (_, rowIdx) => (
              <>
                {/* Day label */}
                <div key={`label-${rowIdx}`} className="flex items-center justify-end pr-1" role="rowheader">
                  <span className="text-[10px] text-gray-400 dark:text-gray-500">{DAY_LABELS[rowIdx]}</span>
                </div>

                {/* Cells for this row across all weeks */}
                {grid.map((week, colIdx) => {
                  const day = week[rowIdx];
                  const cellKey = `${colIdx}-${rowIdx}`;

                  if (!day || !day.date) {
                    return <div key={cellKey} className="w-3 h-3" role="gridcell" />;
                  }

                  const ariaLabel = buildTooltipContent(day);

                  return (
                    <div
                      key={cellKey}
                      ref={(el) => {
                        if (el) cellRefs.current.set(cellKey, el);
                        else cellRefs.current.delete(cellKey);
                      }}
                      role="gridcell"
                      tabIndex={focusedCell?.col === colIdx && focusedCell?.row === rowIdx ? 0 : -1}
                      aria-label={ariaLabel}
                      className={`w-3 h-3 rounded-sm ${getHeatmapColor(day.avg_momentum, day.hasData)} cursor-pointer transition-colors hover:ring-1 hover:ring-gray-400 dark:hover:ring-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-500`}
                      onMouseEnter={(e) => showTooltipForCell(e.currentTarget, day)}
                      onMouseLeave={hideTooltip}
                      onTouchStart={(e) => {
                        e.stopPropagation();
                        showTooltipForCell(e.currentTarget, day);
                      }}
                      onFocus={(e) => {
                        setFocusedCell({ col: colIdx, row: rowIdx });
                        showTooltipForCell(e.currentTarget, day);
                      }}
                      onBlur={hideTooltip}
                    />
                  );
                })}
              </>
            ))}
          </div>

          {/* Tooltip */}
          {tooltip && (
            <div
              className="fixed z-50 px-2 py-1 text-xs bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded shadow-lg pointer-events-none whitespace-nowrap"
              role="tooltip"
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
        <div className="flex items-center gap-2 mt-3 justify-end" aria-label="Legend: momentum activity levels">
          <span className="text-[10px] text-gray-400 dark:text-gray-500">Less</span>
          <div className="w-3 h-3 rounded-sm bg-gray-200 dark:bg-gray-700" aria-hidden="true" />
          <div className="w-3 h-3 rounded-sm bg-emerald-100 dark:bg-emerald-900/40" aria-hidden="true" />
          <div className="w-3 h-3 rounded-sm bg-emerald-300 dark:bg-emerald-700/60" aria-hidden="true" />
          <div className="w-3 h-3 rounded-sm bg-emerald-500 dark:bg-emerald-600" aria-hidden="true" />
          <div className="w-3 h-3 rounded-sm bg-emerald-700 dark:bg-emerald-500" aria-hidden="true" />
          <span className="text-[10px] text-gray-400 dark:text-gray-500">More</span>
        </div>
      </div>
    </div>
  );
}
