import { Loader2 } from 'lucide-react';

interface LoadingProps {
  message?: string;
  fullPage?: boolean;
}

export function Loading({ message = 'Loading...', fullPage = false }: LoadingProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      <p className="text-gray-600 dark:text-gray-400">{message}</p>
    </div>
  );

  if (fullPage) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        {content}
      </div>
    );
  }

  return (
    <div className="p-8">
      {content}
    </div>
  );
}
