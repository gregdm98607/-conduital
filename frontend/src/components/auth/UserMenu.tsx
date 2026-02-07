/**
 * User Menu Component
 *
 * Displays current user info and logout button in the header.
 * Only shown when auth is enabled.
 */

import { useState, useRef, useEffect } from 'react';
import { User, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export function UserMenu() {
  const { user, isAuthenticated, authEnabled, logout, loginWithGoogle } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Don't show anything if auth is disabled
  if (!authEnabled) {
    return null;
  }

  // Show login button if not authenticated
  if (!isAuthenticated || !user) {
    return (
      <button
        onClick={() => loginWithGoogle()}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors w-full"
      >
        <User className="w-4 h-4" />
        Sign In
      </button>
    );
  }

  // Show user menu if authenticated
  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-400 hover:bg-white/5 hover:text-gray-200 rounded-lg transition-colors w-full"
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.display_name || user.email}
            className="w-6 h-6 rounded-full ring-2 ring-gray-700"
          />
        ) : (
          <div className="w-6 h-6 rounded-full bg-primary-500/20 flex items-center justify-center">
            <span className="text-xs font-medium text-primary-400">
              {(user.display_name || user.email).charAt(0).toUpperCase()}
            </span>
          </div>
        )}
        <span className="hidden sm:inline max-w-[120px] truncate">
          {user.display_name || user.email}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50">
          {/* User Info */}
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
              {user.display_name || 'User'}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user.email}</p>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            <button
              onClick={async () => {
                setIsOpen(false);
                await logout();
                window.location.href = '/login';
              }}
              className="w-full flex items-center gap-3 px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserMenu;
