import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Keyboard } from 'lucide-react';

const SHORTCUTS: { key: string; description: string; section: string }[] = [
  // Navigation
  { key: '?', description: 'Show this help', section: 'General' },
  { key: 'g h', description: 'Go to Dashboard', section: 'Navigation' },
  { key: 'g d', description: 'Go to Today\'s Focus', section: 'Navigation' },
  { key: 'g p', description: 'Go to Projects', section: 'Navigation' },
  { key: 'g a', description: 'Go to Areas', section: 'Navigation' },
  { key: 'g t', description: 'Go to All Tasks', section: 'Navigation' },
  { key: 'g n', description: 'Go to Next Actions', section: 'Navigation' },
  { key: 'g i', description: 'Go to Inbox', section: 'Navigation' },
  { key: 'g w', description: 'Go to Weekly Review', section: 'Navigation' },
  { key: 'g s', description: 'Go to Settings', section: 'Navigation' },
];

const NAVIGATION_MAP: Record<string, string> = {
  h: '/',
  d: '/daily',
  p: '/projects',
  a: '/areas',
  t: '/tasks',
  n: '/next-actions',
  i: '/inbox',
  w: '/weekly-review',
  s: '/settings',
};

export function KeyboardShortcutOverlay() {
  const [isOpen, setIsOpen] = useState(false);
  const [pendingG, setPendingG] = useState(false);
  const navigate = useNavigate();

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Don't trigger when typing in inputs/textareas
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable
      ) {
        return;
      }

      // Close overlay on Escape
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
        return;
      }

      // Toggle overlay on ?
      if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        setIsOpen((prev) => !prev);
        setPendingG(false);
        return;
      }

      // "g" prefix for navigation
      if (e.key === 'g' && !e.ctrlKey && !e.metaKey && !isOpen) {
        setPendingG(true);
        // Auto-clear after 1.5s
        setTimeout(() => setPendingG(false), 1500);
        return;
      }

      // Second key of "g + X" chord
      if (pendingG && !isOpen) {
        const route = NAVIGATION_MAP[e.key];
        if (route) {
          e.preventDefault();
          navigate(route);
        }
        setPendingG(false);
        return;
      }
    },
    [isOpen, pendingG, navigate]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // Lock body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const sections = [...new Set(SHORTCUTS.map((s) => s.section))];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="presentation">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      />

      {/* Overlay */}
      <div
        className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl m-4 w-full max-w-lg"
        role="dialog"
        aria-modal="true"
        aria-labelledby="shortcuts-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Keyboard className="w-5 h-5 text-primary-500" />
            <h2 id="shortcuts-title" className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Keyboard Shortcuts
            </h2>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Close shortcuts"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 max-h-[60vh] overflow-y-auto">
          {sections.map((section) => (
            <div key={section} className="mb-5 last:mb-0">
              <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                {section}
              </h3>
              <div className="space-y-1.5">
                {SHORTCUTS.filter((s) => s.section === section).map((shortcut) => (
                  <div
                    key={shortcut.key}
                    className="flex items-center justify-between py-1"
                  >
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {shortcut.description}
                    </span>
                    <div className="flex items-center gap-1">
                      {shortcut.key.split(' ').map((k, i) => (
                        <span key={i}>
                          {i > 0 && (
                            <span className="text-gray-400 dark:text-gray-500 text-xs mx-0.5">then</span>
                          )}
                          <kbd className="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 text-xs font-mono font-semibold text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded shadow-sm">
                            {k}
                          </kbd>
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-700 text-center">
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Press <kbd className="px-1.5 py-0.5 text-xs font-mono bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">Esc</kbd> or <kbd className="px-1.5 py-0.5 text-xs font-mono bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded">?</kbd> to close
          </span>
        </div>
      </div>
    </div>
  );
}
