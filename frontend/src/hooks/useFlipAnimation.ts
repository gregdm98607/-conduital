import { useRef, useLayoutEffect, useCallback } from 'react';

/**
 * FLIP animation hook for smooth reorder transitions.
 *
 * Usage:
 *   const { containerRef, capturePositions } = useFlipAnimation<HTMLDivElement>(deps);
 *
 * Call `capturePositions()` before changing sort order, or pass the sort
 * dependency as `deps` — positions are automatically captured before each
 * layout pass.
 *
 * Children of the container must have a `data-flip-id` attribute (typically
 * the item's unique id) so the hook can track elements across renders.
 */
export function useFlipAnimation<T extends HTMLElement>(
  deps: unknown[],
  { duration = 250, easing = 'ease-out' } = {},
) {
  const containerRef = useRef<T>(null);
  const positionsRef = useRef<Map<string, DOMRect>>(new Map());

  const capturePositions = useCallback(() => {
    const container = containerRef.current;
    if (!container) return;
    const map = new Map<string, DOMRect>();
    for (const child of container.children) {
      const id = (child as HTMLElement).dataset.flipId;
      if (id) map.set(id, child.getBoundingClientRect());
    }
    positionsRef.current = map;
  }, []);

  // Capture positions before every render triggered by deps
  // (useLayoutEffect fires synchronously after DOM mutation but before paint)
  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const prev = positionsRef.current;
    if (prev.size === 0) {
      // First render — just capture and bail
      capturePositions();
      return;
    }

    // Measure new positions
    const animations: Animation[] = [];
    for (const child of container.children) {
      const el = child as HTMLElement;
      const id = el.dataset.flipId;
      if (!id) continue;

      const oldRect = prev.get(id);
      const newRect = el.getBoundingClientRect();
      if (!oldRect) continue;

      const dx = oldRect.left - newRect.left;
      const dy = oldRect.top - newRect.top;

      if (Math.abs(dx) < 1 && Math.abs(dy) < 1) continue;

      const anim = el.animate(
        [
          { transform: `translate(${dx}px, ${dy}px)` },
          { transform: 'translate(0, 0)' },
        ],
        { duration, easing, fill: 'none' },
      );
      animations.push(anim);
    }

    // Capture positions for next change
    capturePositions();

    return () => {
      animations.forEach((a) => a.cancel());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { containerRef, capturePositions };
}
