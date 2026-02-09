import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { api } from '../../services/api';

interface Props {
  children: React.ReactNode;
}

/**
 * Guards protected routes by checking if first-run setup is complete.
 *
 * In packaged mode: redirects to /setup if setup hasn't been completed.
 * In development mode: always passes through (no redirect).
 */
export function SetupGuard({ children }: Props) {
  const navigate = useNavigate();
  const location = useLocation();
  const [checking, setChecking] = useState(true);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function checkSetup() {
      try {
        const status = await api.getSetupStatus();

        if (cancelled) return;

        // In dev mode, always allow through
        if (!status.is_packaged) {
          setAllowed(true);
          setChecking(false);
          return;
        }

        // In packaged mode, redirect to setup if not complete
        if (!status.setup_complete) {
          navigate('/setup', { replace: true });
          return;
        }

        setAllowed(true);
      } catch {
        // If we can't check status, allow through (fail open)
        setAllowed(true);
      } finally {
        if (!cancelled) {
          setChecking(false);
        }
      }
    }

    checkSetup();

    return () => {
      cancelled = true;
    };
  }, [navigate, location.pathname]);

  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!allowed) {
    return null;
  }

  return <>{children}</>;
}
