import { useState } from 'react';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { getMomentumColor } from '../../utils/momentum';
import type { MomentumFactor } from '../../types';

interface AreaHealthBreakdownProps {
  areaId: number;
}

function FactorBar({ factor }: { factor: MomentumFactor }) {
  const barPct = Math.round(factor.raw_score * 100);
  const weightPct = Math.round(factor.weight * 100);
  const color = getMomentumColor(factor.raw_score);

  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="w-36 shrink-0">
        <span className="font-medium text-gray-700 dark:text-gray-300">{factor.name}</span>
        <span className="text-gray-400 ml-1 text-xs">({weightPct}%)</span>
      </div>
      <div className="flex-1 flex items-center gap-2">
        <div className="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-300"
            style={{ width: `${barPct}%`, backgroundColor: color }}
          />
        </div>
        <span className="w-10 text-right text-xs font-semibold" style={{ color }}>
          {barPct}%
        </span>
      </div>
      <span className="w-36 text-right text-xs text-gray-500 dark:text-gray-400 shrink-0">{factor.detail}</span>
    </div>
  );
}

export function AreaHealthBreakdown({ areaId }: AreaHealthBreakdownProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const { data: breakdown, isLoading } = useQuery({
    queryKey: ['area-health-breakdown', areaId],
    queryFn: () => api.getAreaHealthBreakdown(areaId),
    enabled: isExpanded,
    staleTime: 60_000,
  });

  return (
    <div>
      {/* Clickable trigger row */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors mt-1"
        title="Show area health score breakdown"
      >
        <Info className="w-3 h-3" />
        <span>How is this calculated?</span>
        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {/* Expandable breakdown */}
      {isExpanded && (
        <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 space-y-2">
          {isLoading ? (
            <div className="text-sm text-gray-400 py-2 text-center">Loading breakdown...</div>
          ) : breakdown ? (
            <>
              {breakdown.factors.map((factor) => (
                <FactorBar key={factor.name} factor={factor} />
              ))}
              <div className="border-t border-gray-200 dark:border-gray-700 pt-2 mt-2 flex items-center justify-between text-sm">
                <span className="font-semibold text-gray-700 dark:text-gray-300">Total Score</span>
                <span
                  className="font-bold text-base"
                  style={{ color: getMomentumColor(breakdown.total_score) }}
                >
                  {Math.round(breakdown.total_score * 100)}%
                </span>
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
