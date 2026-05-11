import { useState, useEffect } from 'react';
import { telemetry } from '@/services/telemetry';

/**
 * Returns [isVisible, dismiss].
 * The chip is visible once per install (keyed by chipId in localStorage).
 * Calling dismiss() hides the chip permanently and fires telemetry.
 */
export function useGuidanceChip(chipId: string): [boolean, () => void] {
  const storageKey = `guidance_chip_${chipId}_dismissed`;
  const [isVisible, setIsVisible] = useState(
    () => localStorage.getItem(storageKey) !== 'true'
  );

  useEffect(() => {
    if (isVisible) {
      telemetry.track('guidance_chip_shown', { chip_id: chipId });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const dismiss = () => {
    localStorage.setItem(storageKey, 'true');
    setIsVisible(false);
    telemetry.track('guidance_chip_dismissed', { chip_id: chipId });
  };

  return [isVisible, dismiss];
}
