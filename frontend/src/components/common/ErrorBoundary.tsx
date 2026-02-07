import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  resetCount: number;
}

const MAX_RESETS = 2;

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, resetCount: 0 };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReset = () => {
    this.setState(prev => ({
      hasError: false,
      error: null,
      resetCount: prev.resetCount + 1,
    }));
  };

  render() {
    if (this.state.hasError) {
      const canRetry = this.state.resetCount < MAX_RESETS;

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="flex flex-col items-center justify-center gap-4 max-w-md text-center px-6">
            <AlertCircle className="w-14 h-14 text-red-500" />
            <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Something went wrong
            </h1>
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              {canRetry
                ? 'An unexpected error occurred. You can try again or reload the page.'
                : 'This error keeps occurring. Please reload the page or go back to the dashboard.'}
            </p>
            {this.state.error && (
              <pre className="mt-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-300 max-w-full overflow-auto whitespace-pre-wrap">
                {this.state.error.message}
              </pre>
            )}
            <div className="flex gap-3 mt-2">
              {canRetry && (
                <button
                  onClick={this.handleReset}
                  className="btn btn-secondary btn-sm"
                >
                  Try Again
                </button>
              )}
              <button
                onClick={this.handleGoHome}
                className="btn btn-secondary btn-sm inline-flex items-center gap-2"
              >
                <Home className="w-4 h-4" />
                Go Home
              </button>
              <button
                onClick={this.handleReload}
                className="btn btn-primary btn-sm inline-flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Reload Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
