import { useState, useCallback } from 'react';
import { CheckCircle } from 'lucide-react';

interface CompleteTaskButtonProps {
  taskId: number;
  onComplete: (taskId: number) => void;
  disabled?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

/**
 * Animated task completion button with green ripple celebration effect.
 * Shows a brief animation on click before triggering the mutation.
 */
export function CompleteTaskButton({
  taskId,
  onComplete,
  disabled = false,
  size = 'sm',
  className = '',
}: CompleteTaskButtonProps) {
  const [celebrating, setCelebrating] = useState(false);

  const iconSize = size === 'sm' ? 'w-4 h-4' : 'w-5 h-5';
  const buttonSize = size === 'sm' ? 'p-1' : 'p-1.5';

  const handleClick = useCallback(() => {
    if (disabled || celebrating) return;
    setCelebrating(true);

    // Fire mutation after brief animation delay
    setTimeout(() => {
      onComplete(taskId);
      // Reset after animation completes
      setTimeout(() => setCelebrating(false), 500);
    }, 150);
  }, [disabled, celebrating, onComplete, taskId]);

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      title="Complete task"
      className={`${buttonSize} rounded-full transition-all duration-200 ${
        celebrating
          ? 'text-green-500 bg-green-50 dark:bg-green-900/30 animate-celebrate-ripple'
          : 'text-gray-400 hover:text-green-500 hover:bg-green-50 dark:hover:bg-green-900/20'
      } disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
    >
      <CheckCircle className={`${iconSize} ${celebrating ? 'fill-green-500 text-white' : ''}`} />
    </button>
  );
}
