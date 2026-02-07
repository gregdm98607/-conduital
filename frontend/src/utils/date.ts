/**
 * Date formatting utilities
 */

import { formatDistanceToNow, format, parseISO, isValid, differenceInDays } from 'date-fns';

/**
 * Safely format a date string for API submission.
 * Returns the date in YYYY-MM-DD format, or undefined if empty/invalid.
 * This ensures consistent date format between create and edit operations.
 *
 * @param dateString - Date string from form input (usually YYYY-MM-DD from HTML date input)
 * @returns Date string in YYYY-MM-DD format, or undefined
 */
export function formatDateForApi(dateString: string | undefined | null): string | undefined {
  if (!dateString || dateString.trim() === '') {
    return undefined;
  }

  try {
    // HTML date inputs return YYYY-MM-DD format, but let's validate and normalize
    const parsed = parseISO(dateString);
    if (!isValid(parsed)) {
      return undefined;
    }
    // Return in YYYY-MM-DD format which Pydantic expects for date fields
    return format(parsed, 'yyyy-MM-dd');
  } catch {
    return undefined;
  }
}

export function formatRelativeTime(dateString?: string): string {
  if (!dateString) return 'Never';
  try {
    const date = parseISO(dateString);
    if (!isValid(date)) return 'Invalid date';

    const now = new Date();
    const diffDays = differenceInDays(now, date);

    // Clamp future dates — likely a timezone mismatch, not a real future event
    if (date > now) return 'Just now';

    // For old dates (30+ days), show absolute date for clarity
    if (diffDays >= 30) {
      return format(date, 'MMM d, yyyy');
    }

    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return 'Invalid date';
  }
}

export function formatDate(dateString?: string): string {
  if (!dateString) return '';
  try {
    const date = parseISO(dateString);
    return format(date, 'MMM d, yyyy');
  } catch {
    return 'Invalid date';
  }
}

export function formatDateTime(dateString?: string): string {
  if (!dateString) return '';
  try {
    const date = parseISO(dateString);
    return format(date, 'MMM d, yyyy h:mm a');
  } catch {
    return 'Invalid date';
  }
}

export function daysSince(dateString?: string): number | null {
  if (!dateString) return null;
  try {
    const date = parseISO(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  } catch {
    return null;
  }
}

export type DueDateStatus = 'overdue' | 'due-soon' | 'normal' | null;

export interface DueDateInfo {
  status: DueDateStatus;
  text: string;
  daysUntil: number | null;
}

/**
 * Get due date status and formatted display text
 * @param dueDateString - ISO date string for the due date
 * @param taskStatus - Task status (completed/cancelled tasks are not overdue)
 * @returns DueDateInfo with status, display text, and days until due
 */
export type ReviewStatus = 'overdue' | 'due-soon' | 'current' | 'never-reviewed';

export interface ReviewStatusInfo {
  status: ReviewStatus;
  text: string;
  daysSinceReview: number | null;
  isOverdue: boolean;
}

/**
 * Get review status based on last reviewed date and review frequency
 * @param lastReviewedAt - ISO date string of last review
 * @param reviewFrequency - 'daily', 'weekly', or 'monthly'
 * @returns ReviewStatusInfo with status, display text, and overdue flag
 */
export function getReviewStatus(
  lastReviewedAt?: string,
  reviewFrequency: 'daily' | 'weekly' | 'monthly' = 'weekly'
): ReviewStatusInfo {
  if (!lastReviewedAt) {
    return {
      status: 'never-reviewed',
      text: 'Never reviewed',
      daysSinceReview: null,
      isOverdue: true,
    };
  }

  const daysSinceReview = daysSince(lastReviewedAt);
  if (daysSinceReview === null) {
    return {
      status: 'never-reviewed',
      text: 'Never reviewed',
      daysSinceReview: null,
      isOverdue: true,
    };
  }

  // Define thresholds based on frequency
  const thresholds: Record<string, { overdue: number; warning: number }> = {
    daily: { overdue: 2, warning: 1 },
    weekly: { overdue: 10, warning: 7 },
    monthly: { overdue: 40, warning: 30 },
  };

  const threshold = thresholds[reviewFrequency] || thresholds.weekly;

  // Format the text
  let text: string;
  if (daysSinceReview === 0) {
    text = 'Reviewed today';
  } else if (daysSinceReview === 1) {
    text = 'Reviewed yesterday';
  } else {
    text = `Reviewed ${daysSinceReview} days ago`;
  }

  if (daysSinceReview >= threshold.overdue) {
    return {
      status: 'overdue',
      text,
      daysSinceReview,
      isOverdue: true,
    };
  } else if (daysSinceReview >= threshold.warning) {
    return {
      status: 'due-soon',
      text,
      daysSinceReview,
      isOverdue: false,
    };
  } else {
    return {
      status: 'current',
      text,
      daysSinceReview,
      isOverdue: false,
    };
  }
}

export function getDueDateInfo(
  dueDateString?: string,
  taskStatus?: string
): DueDateInfo {
  if (!dueDateString) {
    return { status: null, text: '', daysUntil: null };
  }

  try {
    const dueDate = parseISO(dueDateString);
    const today = new Date();
    // Reset time to compare dates only
    today.setHours(0, 0, 0, 0);
    const dueDateOnly = new Date(dueDate);
    dueDateOnly.setHours(0, 0, 0, 0);

    const diffTime = dueDateOnly.getTime() - today.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    const formattedDate = format(dueDate, 'MMM d');

    // Completed or cancelled tasks are never overdue
    const isCompletedOrCancelled = taskStatus === 'completed' || taskStatus === 'cancelled';

    if (diffDays < 0 && !isCompletedOrCancelled) {
      // Overdue
      const daysOverdue = Math.abs(diffDays);
      return {
        status: 'overdue',
        text: daysOverdue === 1 ? `${formattedDate} (1 day overdue)` : `${formattedDate} (${daysOverdue} days overdue)`,
        daysUntil: diffDays,
      };
    } else if (diffDays === 0) {
      // Due today
      return {
        status: 'due-soon',
        text: 'Due today',
        daysUntil: 0,
      };
    } else if (diffDays <= 3 && !isCompletedOrCancelled) {
      // Due soon (within 3 days)
      return {
        status: 'due-soon',
        text: diffDays === 1 ? `${formattedDate} (tomorrow)` : `${formattedDate} (in ${diffDays} days)`,
        daysUntil: diffDays,
      };
    } else {
      // Normal due date
      return {
        status: 'normal',
        text: formattedDate,
        daysUntil: diffDays,
      };
    }
  } catch {
    return { status: null, text: 'Invalid date', daysUntil: null };
  }
}
