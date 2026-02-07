/**
 * Authentication Context for Project Tracker
 *
 * Provides:
 * - Current user state
 * - Auth status (enabled/configured)
 * - Login/logout functions
 * - Loading states
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { authService } from '@/services/authService';
import type { User, AuthStatus } from '@/types';

interface AuthContextType {
  // User state
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Auth system state
  authEnabled: boolean;
  googleConfigured: boolean;

  // Actions
  loginWithGoogle: (redirectUrl?: string) => void;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authEnabled, setAuthEnabled] = useState(false);
  const [googleConfigured, setGoogleConfigured] = useState(false);

  /**
   * Check for tokens in URL (OAuth callback) and store them
   */
  const handleOAuthCallback = useCallback(() => {
    const tokens = authService.parseTokensFromUrl();
    if (tokens) {
      authService.setTokens(tokens.accessToken, tokens.refreshToken);
      authService.clearUrlHash();
      return true;
    }
    return false;
  }, []);

  /**
   * Fetch auth status and current user
   */
  const initializeAuth = useCallback(async () => {
    setIsLoading(true);

    try {
      // First, check for OAuth callback tokens in URL
      handleOAuthCallback();

      // Get auth status from backend
      const status: AuthStatus = await authService.getAuthStatus();
      setAuthEnabled(status.enabled);
      setGoogleConfigured(status.google_configured);

      // If auth is disabled, skip user fetch
      if (!status.enabled) {
        setUser(null);
        setIsLoading(false);
        return;
      }

      // If we have tokens, try to get user info
      if (authService.hasTokens()) {
        try {
          const userData = await authService.getCurrentUser();
          setUser(userData);
        } catch (error) {
          // Token might be invalid, try refresh
          const newToken = await authService.refreshAccessToken();
          if (newToken) {
            try {
              const userData = await authService.getCurrentUser();
              setUser(userData);
            } catch {
              // Still failed, clear tokens
              authService.clearTokens();
              setUser(null);
            }
          } else {
            setUser(null);
          }
        }
      } else if (status.user) {
        // Backend returned user in status (already authenticated via cookie or session)
        setUser(status.user);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, [handleOAuthCallback]);

  /**
   * Initialize on mount
   */
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  /**
   * Login with Google OAuth
   */
  const loginWithGoogle = useCallback((redirectUrl?: string) => {
    authService.loginWithGoogle(redirectUrl || window.location.pathname);
  }, []);

  /**
   * Logout
   */
  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  /**
   * Refresh user data
   */
  const refreshUser = useCallback(async () => {
    if (!authEnabled || !authService.hasTokens()) {
      return;
    }

    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  }, [authEnabled]);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    authEnabled,
    googleConfigured,
    loginWithGoogle,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
