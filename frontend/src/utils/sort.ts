import type { SortDirection } from '../components/common/SortableHeader';

/** Parse a sort option string like "priority_desc" into key + direction */
export function parseSortOption(opt: string): { key: string; direction: SortDirection } {
  if (!opt || !opt.includes('_')) {
    return { key: opt || '', direction: 'desc' };
  }
  const parts = opt.split('_');
  const direction = parts.pop() as SortDirection;
  const key = parts.join('_');
  return { key: key || '', direction: direction === 'asc' ? 'asc' : 'desc' };
}
