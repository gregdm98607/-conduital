/**
 * Login Page
 *
 * Displays Google OAuth login button when auth is enabled.
 * Redirects to dashboard if auth is disabled or user is already authenticated.
 */

import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isAuthenticated, isLoading, authEnabled, googleConfigured, loginWithGoogle } = useAuth();

  const error = searchParams.get('error');
  const redirectTo = searchParams.get('redirect') || '/';

  // Redirect if already authenticated or auth is disabled
  useEffect(() => {
    if (!isLoading) {
      if (!authEnabled) {
        // Auth disabled, go straight to app
        navigate('/', { replace: true });
      } else if (isAuthenticated) {
        // Already logged in, go to redirect target
        navigate(redirectTo, { replace: true });
      }
    }
  }, [isLoading, authEnabled, isAuthenticated, navigate, redirectTo]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Auth is disabled or user is authenticated - will redirect in useEffect
  if (!authEnabled || isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          {/* Logo/Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
              <CheckCircle2 className="w-8 h-8 text-primary-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Conduital</h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">Sign in to manage your projects</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-800 dark:text-red-300">Authentication failed</p>
                <p className="text-sm text-red-700 dark:text-red-400 mt-1">
                  {error === 'google_auth_failed'
                    ? 'Unable to sign in with Google. Please try again.'
                    : 'An error occurred. Please try again.'}
                </p>
              </div>
            </div>
          )}

          {/* Google OAuth Status */}
          {!googleConfigured ? (
            <div className="p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg mb-6">
              <p className="text-sm text-amber-800 dark:text-amber-300">
                <strong>Configuration Required:</strong> Google OAuth is not configured. Please set{' '}
                <code className="bg-amber-100 dark:bg-amber-900/30 px-1 rounded">GOOGLE_CLIENT_ID</code> and{' '}
                <code className="bg-amber-100 dark:bg-amber-900/30 px-1 rounded">GOOGLE_CLIENT_SECRET</code> in the backend
                environment.
              </p>
            </div>
          ) : null}

          {/* Login Button */}
          <button
            onClick={() => loginWithGoogle(redirectTo)}
            disabled={!googleConfigured}
            className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-lg font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {/* Google Logo SVG */}
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Continue with Google
          </button>

          {/* Footer */}
          <p className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
            By signing in, you agree to our terms of service and privacy policy.
          </p>
        </div>

        {/* Additional Info */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Intelligent momentum for independent operators
          </p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
