import { getMomentumColor, getMomentumLabel, formatMomentumScore } from '../../utils/momentum';

interface MomentumPulseRingProps {
  score: number;
  size?: 'sm' | 'md' | 'lg';
}

const sizeConfig = {
  sm: { ring: 'w-16 h-16', text: 'text-sm', label: 'text-[10px]' },
  md: { ring: 'w-24 h-24', text: 'text-xl', label: 'text-xs' },
  lg: { ring: 'w-32 h-32', text: 'text-2xl', label: 'text-sm' },
};

export function MomentumPulseRing({ score, size = 'md' }: MomentumPulseRingProps) {
  const color = getMomentumColor(score);
  const label = getMomentumLabel(score);
  const percentage = formatMomentumScore(score);
  const config = sizeConfig[size];

  // Animation speed scales with momentum (stronger = faster pulse)
  const animationDuration = score >= 0.7 ? '2s' : score >= 0.4 ? '3s' : '4s';

  return (
    <div className="flex flex-col items-center gap-1">
      <div className={`relative ${config.ring} flex items-center justify-center`}>
        {/* Outer pulse ring */}
        <div
          className="absolute inset-0 rounded-full opacity-30"
          style={{
            border: `2px solid ${color}`,
            animation: `momentum-pulse ${animationDuration} ease-in-out infinite`,
          }}
        />
        {/* Inner solid ring */}
        <div
          className="absolute inset-1 rounded-full"
          style={{
            border: `3px solid ${color}`,
            boxShadow: `0 0 12px ${color}33`,
          }}
        />
        {/* Score text */}
        <div className="relative text-center">
          <span className={`font-bold ${config.text}`} style={{ color }}>
            {percentage}
          </span>
        </div>
      </div>
      <span className={`font-medium ${config.label}`} style={{ color }}>
        {label}
      </span>
    </div>
  );
}
