import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';

export type SortDirection = 'asc' | 'desc';

interface SortableHeaderProps {
  label: string;
  sortKey: string;
  currentSortKey: string;
  currentDirection: SortDirection;
  onSort: (key: string, direction: SortDirection) => void;
}

export function SortableHeader({ label, sortKey, currentSortKey, currentDirection, onSort }: SortableHeaderProps) {
  const isActive = currentSortKey === sortKey;

  const handleClick = () => {
    if (isActive) {
      // Toggle direction
      onSort(sortKey, currentDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Default to desc for numeric fields, asc for text
      onSort(sortKey, 'desc');
    }
  };

  return (
    <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider">
      <button
        type="button"
        onClick={handleClick}
        className={`inline-flex items-center gap-1 hover:text-gray-900 dark:hover:text-gray-200 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-1 rounded ${
          isActive ? 'text-gray-900 dark:text-gray-100' : 'text-gray-500 dark:text-gray-400'
        }`}
        aria-sort={isActive ? (currentDirection === 'asc' ? 'ascending' : 'descending') : 'none'}
      >
        {label}
        <span className="inline-flex flex-col" aria-hidden="true">
          {isActive ? (
            currentDirection === 'asc' ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )
          ) : (
            <ChevronsUpDown className="w-3.5 h-3.5 opacity-40" />
          )}
        </span>
      </button>
    </th>
  );
}

/** Non-sortable header for columns like "Actions" */
export function StaticHeader({ label }: { label: string }) {
  return (
    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
      {label}
    </th>
  );
}
