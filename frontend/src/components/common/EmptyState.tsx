import { ReactNode } from 'react';

type IllustrationVariant = 'projects' | 'tasks' | 'areas' | 'search' | 'generic';

interface EmptyStateProps {
  variant?: IllustrationVariant;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

/**
 * Reusable empty state with inline SVG illustration and encouraging copy.
 * BACKLOG-135: Empty State Illustrations.
 */
export function EmptyState({
  variant = 'generic',
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  return (
    <div className={`card text-center py-12 px-6 ${className}`}>
      <div className="flex justify-center mb-6">
        <Illustration variant={variant} />
      </div>
      <p className="text-gray-600 dark:text-gray-300 text-lg font-medium mb-1">{title}</p>
      {description && (
        <p className="text-gray-400 dark:text-gray-500 text-sm mb-4 max-w-md mx-auto">
          {description}
        </p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

function Illustration({ variant }: { variant: IllustrationVariant }) {
  const size = 96;
  const shared = 'text-gray-300 dark:text-gray-600';

  switch (variant) {
    case 'projects':
      return (
        <svg width={size} height={size} viewBox="0 0 96 96" fill="none" className={shared} aria-hidden="true">
          {/* Folder shape */}
          <rect x="12" y="30" width="72" height="48" rx="6" stroke="currentColor" strokeWidth="2.5" />
          <path d="M12 36h28l6-6h26a6 6 0 0 1 6 6" stroke="currentColor" strokeWidth="2.5" fill="none" />
          {/* Sparkle */}
          <circle cx="48" cy="54" r="3" fill="currentColor" opacity="0.5" />
          <path d="M48 46v-4M48 62v4M40 54h-4M56 54h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" opacity="0.4" />
        </svg>
      );
    case 'tasks':
      return (
        <svg width={size} height={size} viewBox="0 0 96 96" fill="none" className={shared} aria-hidden="true">
          {/* Clipboard */}
          <rect x="22" y="16" width="52" height="68" rx="6" stroke="currentColor" strokeWidth="2.5" />
          <rect x="34" y="12" width="28" height="10" rx="4" stroke="currentColor" strokeWidth="2" />
          {/* Check lines */}
          <path d="M34 42h28M34 54h20M34 66h24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
          {/* Check mark */}
          <circle cx="34" cy="42" r="0" />
        </svg>
      );
    case 'areas':
      return (
        <svg width={size} height={size} viewBox="0 0 96 96" fill="none" className={shared} aria-hidden="true">
          {/* Grid of cards */}
          <rect x="12" y="18" width="32" height="26" rx="4" stroke="currentColor" strokeWidth="2.5" />
          <rect x="52" y="18" width="32" height="26" rx="4" stroke="currentColor" strokeWidth="2.5" />
          <rect x="12" y="52" width="32" height="26" rx="4" stroke="currentColor" strokeWidth="2.5" />
          <rect x="52" y="52" width="32" height="26" rx="4" stroke="currentColor" strokeWidth="2.5" opacity="0.4" strokeDasharray="4 3" />
        </svg>
      );
    case 'search':
      return (
        <svg width={size} height={size} viewBox="0 0 96 96" fill="none" className={shared} aria-hidden="true">
          {/* Magnifying glass */}
          <circle cx="42" cy="42" r="22" stroke="currentColor" strokeWidth="2.5" />
          <path d="M58 58l18 18" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
          {/* Question mark */}
          <path d="M38 36a6 6 0 0 1 8-4.5 6 6 0 0 1 0 10.5H42v3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" opacity="0.5" />
          <circle cx="42" cy="50" r="1.5" fill="currentColor" opacity="0.5" />
        </svg>
      );
    default:
      return (
        <svg width={size} height={size} viewBox="0 0 96 96" fill="none" className={shared} aria-hidden="true">
          {/* Empty box */}
          <rect x="18" y="24" width="60" height="52" rx="6" stroke="currentColor" strokeWidth="2.5" />
          <path d="M18 40h60" stroke="currentColor" strokeWidth="2" opacity="0.4" />
          {/* Dots */}
          <circle cx="48" cy="58" r="2" fill="currentColor" opacity="0.3" />
          <circle cx="38" cy="58" r="2" fill="currentColor" opacity="0.3" />
          <circle cx="58" cy="58" r="2" fill="currentColor" opacity="0.3" />
        </svg>
      );
  }
}
