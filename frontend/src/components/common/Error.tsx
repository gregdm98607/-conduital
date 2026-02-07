import { AlertCircle } from 'lucide-react';

interface ErrorProps {
  message?: string;
  fullPage?: boolean;
}

export function Error({ message = 'Something went wrong', fullPage = false }: ErrorProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <AlertCircle className="w-12 h-12 text-red-500" />
      <p className="text-gray-900 dark:text-gray-100 font-semibold">Error</p>
      <p className="text-gray-600 dark:text-gray-400 text-sm max-w-md text-center">{message}</p>
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
