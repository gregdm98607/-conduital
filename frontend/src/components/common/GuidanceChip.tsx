import { ReactNode } from 'react';

interface GuidanceChipProps {
  isVisible: boolean;
  onDismiss: () => void;
  children: ReactNode;
}

export function GuidanceChip({ isVisible, onDismiss, children }: GuidanceChipProps) {
  if (!isVisible) return null;
  return (
    <div className="flex items-start gap-3 px-4 py-3 mb-4 bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg text-sm text-primary-800 dark:text-primary-300">
      <span className="flex-1">{children}</span>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss"
        className="shrink-0 text-primary-400 hover:text-primary-700 dark:hover:text-primary-200 mt-0.5"
      >
        ×
      </button>
    </div>
  );
}
