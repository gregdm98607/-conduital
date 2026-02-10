import { useState, useRef, useEffect } from 'react';
import { Calendar, Clock } from 'lucide-react';

interface DeferPopoverProps {
  /** Called when user selects a defer date (ISO string, e.g. "2026-02-16") */
  onDefer: (deferUntil: string) => void;
  disabled?: boolean;
  /** Optional: compact size for inline use in cards */
  compact?: boolean;
}

function addDays(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

/**
 * A small popover with quick defer presets (1 Week, 1 Month) and a custom date picker.
 * BACKLOG-119: Task Push/Defer quick action.
 */
export function DeferPopover({ onDefer, disabled = false, compact = false }: DeferPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [customDate, setCustomDate] = useState('');
  const popoverRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    function handleClickOutside(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const handleDefer = (date: string) => {
    onDefer(date);
    setIsOpen(false);
    setCustomDate('');
  };

  const buttonClass = compact
    ? 'p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors'
    : 'btn btn-sm btn-secondary flex items-center gap-1';

  return (
    <div className="relative" ref={popoverRef}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        disabled={disabled}
        className={buttonClass}
        title="Defer task to a future date"
      >
        <Clock className={compact ? 'w-3.5 h-3.5' : 'w-4 h-4'} />
        {!compact && <span>Push</span>}
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3 w-56"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Defer until...</div>
          <div className="space-y-1 mb-3">
            <button
              onClick={() => handleDefer(addDays(7))}
              className="w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 flex items-center gap-2"
            >
              <Calendar className="w-3.5 h-3.5 text-gray-400" />
              1 Week
              <span className="text-xs text-gray-400 ml-auto">{addDays(7)}</span>
            </button>
            <button
              onClick={() => handleDefer(addDays(30))}
              className="w-full text-left px-3 py-2 text-sm rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 flex items-center gap-2"
            >
              <Calendar className="w-3.5 h-3.5 text-gray-400" />
              1 Month
              <span className="text-xs text-gray-400 ml-auto">{addDays(30)}</span>
            </button>
          </div>
          <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
            <label className="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-1">Custom date</label>
            <div className="flex gap-1">
              <input
                type="date"
                value={customDate}
                min={addDays(1)}
                onChange={(e) => setCustomDate(e.target.value)}
                className="flex-1 text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-1 focus:ring-primary-500"
              />
              <button
                onClick={() => customDate && handleDefer(customDate)}
                disabled={!customDate}
                className="btn btn-sm btn-primary px-2 py-1 text-xs"
              >
                Set
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
