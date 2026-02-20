/**
 * Shared AI error handling utilities.
 * All AI components should use getAIErrorMessage() for consistent error UX.
 */

/** Extract HTTP status from an Axios error */
export function getAIErrorStatus(err: unknown): number | undefined {
  return (err as { response?: { status?: number } })?.response?.status;
}

/** Get a user-friendly error message for AI failures */
export function getAIErrorMessage(err: unknown, fallback: string = 'AI service unavailable'): string {
  const status = getAIErrorStatus(err);
  if (status === 400 || status === 403) {
    return 'AI not configured — add your Anthropic API key in Settings.';
  }
  if (status === 429) {
    return 'AI service is busy — please try again shortly.';
  }
  if (status === 500) {
    return 'AI service encountered an error. Please try again.';
  }
  if (status === 502 || status === 503 || status === 504) {
    return 'AI service is temporarily unavailable. Please try again in a moment.';
  }
  return fallback;
}
