import React from 'react';
import { SecurityEvent } from '../types/events';
import { EventCard } from './EventCard';
import { ApiError } from '../api/client';
import { ErrorBanner } from './ErrorBanner';

interface EventListProps {
  events: SecurityEvent[];
  loading: boolean;
  loadingMore: boolean;
  error: ApiError | Error | null;
  hasMore: boolean;
  onLoadMore: () => void;
  onRetry: () => void;
  newestEventId?: string | null;
}

export const EventList: React.FC<EventListProps> = ({
  events,
  loading,
  loadingMore,
  error,
  hasMore,
  onLoadMore,
  onRetry,
  newestEventId,
}) => {
  return (
    <div className="space-y-4">
      {/* Error state */}
      {error && <ErrorBanner error={error} onRetry={onRetry} />}

      {/* Loading Skeleton */}
      {loading && events.length === 0 && (
        <div className="space-y-3">
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-4 animate-pulse"
            >
              <div className="flex justify-between items-center mb-3">
                <div className="h-4 bg-zinc-800 rounded w-1/3" />
                <div className="h-3 bg-zinc-800 rounded w-1/4" />
              </div>
              <div className="flex gap-2 mb-3">
                <div className="h-5 bg-zinc-800 rounded w-20" />
                <div className="h-5 bg-zinc-800 rounded w-24" />
                <div className="h-5 bg-zinc-800 rounded w-16" />
              </div>
              <div className="h-3 bg-zinc-800/60 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && events.length === 0 && !error && (
        <div className="bg-zinc-900/40 border border-zinc-800/60 rounded-2xl p-10 text-center flex flex-col items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-zinc-800/60 border border-zinc-700/60 flex items-center justify-center text-zinc-400 mb-3">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h4 className="text-sm font-semibold text-zinc-200">
            No Security Events Recorded
          </h4>
          <p className="text-xs text-zinc-500 mt-1 max-w-sm">
            No restricted-zone intrusions or perimeter events match your current filter settings.
          </p>
        </div>
      )}

      {/* Event Cards List */}
      {events.length > 0 && (
        <div className="space-y-3">
          {events.map((event) => (
            <EventCard
              key={event.event_id}
              event={event}
              isNew={event.event_id === newestEventId}
            />
          ))}
        </div>
      )}

      {/* Load More Pagination */}
      {hasMore && (
        <div className="pt-2 text-center">
          <button
            onClick={onLoadMore}
            disabled={loadingMore}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 hover:border-zinc-500 transition-colors disabled:opacity-50 inline-flex items-center gap-2"
          >
            {loadingMore ? (
              <>
                <svg
                  className="w-3.5 h-3.5 animate-spin"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span>Loading Previous Events...</span>
              </>
            ) : (
              <span>Load More Historical Events</span>
            )}
          </button>
        </div>
      )}
    </div>
  );
};
