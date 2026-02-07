/**
 * Protected Route Component
 *
 * Wraps routes that require authentication.
 * - If auth is disabled, renders children directly
 * - If auth is enabled and user is authenticated, renders children
 * - If auth is enabled and user is not authenticated, redirects to login
 */

import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, authEnabled } = useAuth();
  const location = useLocation();

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // If auth is disabled, allow access
  if (!authEnabled) {
    return <>{children}</>;
  }

  // If authenticated, allow access
  if (isAuthenticated) {
    return <>{children}</>;
  }

  // Not authenticated, redirect to login with return URL
  return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />;
}

export default ProtectedRoute;
