import React from 'react';
import { ApiError } from '../api/client';

interface ErrorBannerProps {
  error: ApiError | Error | null;
  onRetry?: () => void;
  title?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  error,
  onRetry,
  title = 'API Communication Error',
}) => {
  if (!error) return null;

  const isApiError = error instanceof ApiError;
  const errorCode = isApiError ? (error as ApiError).code : 'ERROR';
  const errorMessage = error.message || 'An unexpected error occurred';

  return (
    <div className="bg-rose-950/40 border border-rose-500/50 rounded-xl p-4 text-rose-200 mb-4 shadow-lg backdrop-blur-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-rose-900/60 flex items-center justify-center text-rose-400 font-bold shrink-0 mt-0.5">
            !
          </div>
          <div>
            <h4 className="text-sm font-semibold text-rose-100 flex items-center gap-2">
              {title}
              <span className="text-xs px-2 py-0.5 rounded bg-rose-900/80 text-rose-300 font-mono">
                {errorCode}
              </span>
            </h4>
            <p className="text-xs text-rose-300/90 mt-1">{errorMessage}</p>
          </div>
        </div>

        {onRetry && (
          <button
            onClick={onRetry}
            className="shrink-0 px-3 py-1.5 text-xs font-medium rounded-lg bg-rose-600/30 hover:bg-rose-600/50 text-rose-100 border border-rose-500/40 hover:border-rose-400 transition-colors"
          >
            Retry Request
          </button>
        )}
      </div>
    </div>
  );
};
