import React, { useState, useCallback } from 'react';
import { Header } from './components/Header';
import { SystemStatusCard } from './components/SystemStatusCard';
import { CameraPreviewPlaceholder } from './components/CameraPreviewPlaceholder';
import { EventFilters } from './components/EventFilters';
import { EventList } from './components/EventList';
import { useSystemStatus } from './hooks/useSystemStatus';
import { useEventHistory } from './hooks/useEventHistory';
import { useEventStream } from './hooks/useEventStream';
import { EventFilterParams, SecurityEvent } from './types/events';

export const App: React.FC = () => {
  const [filters, setFilters] = useState<EventFilterParams>({ limit: 50 });
  const [newestEventId, setNewestEventId] = useState<string | null>(null);

  // 1. System status polling
  const {
    status,
    loading: statusLoading,
    error: statusError,
    lastUpdated,
    refresh: refreshStatus,
  } = useSystemStatus(3000);

  // 2. Historical & live events management
  const {
    events,
    loading: eventsLoading,
    loadingMore,
    error: eventsError,
    hasMore,
    addLiveEvent,
    loadMore,
    refresh: refreshEvents,
    reconcileAfterReconnect,
  } = useEventHistory(filters);

  // 3. Live WebSocket stream
  const handleLiveEvent = useCallback(
    (event: SecurityEvent) => {
      addLiveEvent(event);
      setNewestEventId(event.event_id);

      // Reset live highlight after 4 seconds
      setTimeout(() => {
        setNewestEventId((current) => (current === event.event_id ? null : current));
      }, 4000);
    },
    [addLiveEvent]
  );

  const handleReconnect = useCallback(() => {
    // Reconcile events missed while WebSocket was disconnected
    reconcileAfterReconnect();
    refreshStatus();
  }, [reconcileAfterReconnect, refreshStatus]);

  const { connectionStatus, reconnectCount, connect } = useEventStream({
    onEvent: handleLiveEvent,
    onReconnect: handleReconnect,
    enabled: true,
  });

  const handleRefreshAll = async () => {
    await Promise.all([refreshStatus(), refreshEvents()]);
  };

  const latestEvent = events.length > 0 ? events[0] : null;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans selection:bg-sky-500/30 selection:text-sky-200">
      <Header
        connectionStatus={connectionStatus}
        reconnectCount={reconnectCount}
        onReconnectClick={connect}
        onRefreshAll={handleRefreshAll}
        isRefreshing={statusLoading || eventsLoading}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: System Telemetry & Viewport (5 cols on lg) */}
          <div className="lg:col-span-5 space-y-6">
            <SystemStatusCard
              status={status}
              loading={statusLoading}
              error={statusError}
              lastUpdated={lastUpdated}
              onRefresh={refreshStatus}
            />

            <CameraPreviewPlaceholder
              status={status}
              latestEvent={latestEvent}
            />
          </div>

          {/* Right Column: Live & Historical Events Feed (7 cols on lg) */}
          <div className="lg:col-span-7 space-y-4">
            <div className="flex items-center justify-between pb-1">
              <div>
                <h2 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
                  <span>Security & Intrusion Events</span>
                  {events.length > 0 && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 font-mono font-medium border border-rose-500/30">
                      {events.length}
                    </span>
                  )}
                </h2>
                <p className="text-xs text-zinc-400">
                  Real-time event stream from YOLO detector, ByteTrack, and Rule Engine.
                </p>
              </div>

              <button
                onClick={refreshEvents}
                disabled={eventsLoading}
                className="text-xs text-sky-400 hover:text-sky-300 underline font-medium"
              >
                Refresh List
              </button>
            </div>

            <EventFilters
              filters={filters}
              onFilterChange={setFilters}
              totalEventsCount={events.length}
            />

            <EventList
              events={events}
              loading={eventsLoading}
              loadingMore={loadingMore}
              error={eventsError}
              hasMore={hasMore}
              onLoadMore={loadMore}
              onRetry={refreshEvents}
              newestEventId={newestEventId}
            />
          </div>
        </div>
      </main>

      <footer className="border-t border-zinc-900 bg-zinc-950/90 py-4 text-center text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-wrap items-center justify-between gap-2">
          <span>LiveSight AI Vision System — Phase 5 Dashboard</span>
          <span className="font-mono text-[11px]">
            API: http://127.0.0.1:8000 | WebSocket: /api/events/stream
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
