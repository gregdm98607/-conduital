/**
 * Authentication Service for Project Tracker
 *
 * Handles:
 * - Token storage and retrieval
 * - Auth status checks
 * - Token refresh
 * - Google OAuth flow initiation
 */

import axios from 'axios';
import type { AuthStatus, TokenResponse, User } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

// Storage keys
const ACCESS_TOKEN_KEY = 'pt_access_token';
const REFRESH_TOKEN_KEY = 'pt_refresh_token';

class AuthService {
  private refreshPromise: Promise<string | null> | null = null;

  /**
   * Get stored access token
   */
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  /**
   * Get stored refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  }

  /**
   * Store tokens in localStorage
   */
  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }

  /**
   * Clear stored tokens
   */
  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  /**
   * Check if user has tokens stored
   */
  hasTokens(): boolean {
    return !!this.getAccessToken();
  }

  /**
   * Parse tokens from URL hash after OAuth callback
   * URL format: /path#auth=access_token=xxx&refresh_token=yyy
   */
  parseTokensFromUrl(): { accessToken: string; refreshToken: string } | null {
    const hash = window.location.hash;
    if (!hash.startsWith('#auth=')) {
      return null;
    }

    const params = new URLSearchParams(hash.substring(6)); // Remove '#auth='
    const accessToken = params.get('access_token');
    const refreshToken = params.get('refresh_token');

    if (accessToken && refreshToken) {
      return { accessToken, refreshToken };
    }

    return null;
  }

  /**
   * Clear URL hash after extracting tokens
   */
  clearUrlHash(): void {
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
  }

  /**
   * Get authentication status from backend
   */
  async getAuthStatus(): Promise<AuthStatus> {
    const response = await axios.get<AuthStatus>(`${API_BASE_URL}/auth/status`, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<User> {
    const response = await axios.get<User>(`${API_BASE_URL}/auth/me`, {
      headers: this.getAuthHeaders(),
    });
    return response.data;
  }

  /**
   * Refresh access token using refresh token
   * Implements single-flight pattern to prevent multiple simultaneous refreshes
   */
  async refreshAccessToken(): Promise<string | null> {
    // If a refresh is already in progress, wait for it
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    this.refreshPromise = this.doRefresh(refreshToken);

    try {
      return await this.refreshPromise;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async doRefresh(refreshToken: string): Promise<string | null> {
    try {
      const response = await axios.post<TokenResponse>(`${API_BASE_URL}/auth/refresh`, {
        refresh_token: refreshToken,
      });

      const { access_token, refresh_token } = response.data;
      this.setTokens(access_token, refresh_token);
      return access_token;
    } catch (error) {
      // Refresh failed, clear tokens
      this.clearTokens();
      return null;
    }
  }

  /**
   * Logout - clear tokens and optionally notify backend
   */
  async logout(): Promise<void> {
    try {
      // Notify backend (optional, JWT is stateless)
      await axios.post(`${API_BASE_URL}/auth/logout`, null, {
        headers: this.getAuthHeaders(),
      });
    } catch {
      // Ignore errors, we're logging out anyway
    }

    this.clearTokens();
  }

  /**
   * Get Google OAuth login URL
   * This redirects the browser to Google's consent screen
   */
  getGoogleLoginUrl(redirectUrl?: string): string {
    const params = new URLSearchParams();
    if (redirectUrl) {
      params.set('redirect_url', redirectUrl);
    }
    const queryString = params.toString();
    return `${API_BASE_URL}/auth/google/login${queryString ? `?${queryString}` : ''}`;
  }

  /**
   * Initiate Google OAuth login by redirecting to backend
   */
  loginWithGoogle(redirectUrl?: string): void {
    window.location.href = this.getGoogleLoginUrl(redirectUrl);
  }

  /**
   * Get authorization headers for API requests
   */
  getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken();
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
    return {};
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
