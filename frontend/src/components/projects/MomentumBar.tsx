import { getMomentumColor, getMomentumLabel, formatMomentumScore } from '../../utils/momentum';

interface MomentumBarProps {
  score: number;
  showLabel?: boolean;
}

export function MomentumBar({ score, showLabel = true }: MomentumBarProps) {
  const color = getMomentumColor(score);
  const label = getMomentumLabel(score);
  const percentage = formatMomentumScore(score);

  return (
    <div>
      {showLabel && (
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Momentum</span>
          <span className="text-sm font-semibold" style={{ color }}>
            {label} ({percentage})
          </span>
        </div>
      )}
      <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-300"
          style={{
            width: `${score * 100}%`,
            backgroundColor: color,
          }}
        />
      </div>
    </div>
  );
}
