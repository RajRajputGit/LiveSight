/**
 * React hook for managing event history, pagination, filtering, and live deduplication.
 * Guarantees duplicate prevention by event_id across REST and WebSocket streams.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getEvents } from '../api/eventsApi';
import { SecurityEvent, EventFilterParams } from '../types/events';
import { ApiError } from '../api/client';

export interface UseEventHistoryResult {
  events: SecurityEvent[];
  loading: boolean;
  loadingMore: boolean;
  error: ApiError | Error | null;
  hasMore: boolean;
  nextCursor: string | null;
  addLiveEvent: (event: SecurityEvent) => void;
  loadMore: () => Promise<void>;
  refresh: () => Promise<void>;
  reconcileAfterReconnect: () => Promise<void>;
  clearEvents: () => void;
}

export function useEventHistory(
  filters: EventFilterParams = { limit: 50 }
): UseEventHistoryResult {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);

  // Set of known event IDs for O(1) deduplication
  const seenEventIdsRef = useRef<Set<string>>(new Set());
  const filtersRef = useRef<EventFilterParams>(filters);
  filtersRef.current = filters;

  const fetchInitial = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getEvents(filtersRef.current);
      const newSeen = new Set<string>();
      const dedupedItems: SecurityEvent[] = [];

      for (const item of response.items) {
        if (!newSeen.has(item.event_id)) {
          newSeen.add(item.event_id);
          dedupedItems.push(item);
        }
      }

      seenEventIdsRef.current = newSeen;
      setEvents(dedupedItems);
      setNextCursor(response.next_cursor);
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (!nextCursor || loadingMore) return;

    setLoadingMore(true);
    try {
      const response = await getEvents({
        ...filtersRef.current,
        before: nextCursor,
      });

      const itemsToAdd: SecurityEvent[] = [];
      for (const item of response.items) {
        if (!seenEventIdsRef.current.has(item.event_id)) {
          seenEventIdsRef.current.add(item.event_id);
          itemsToAdd.push(item);
        }
      }

      setEvents((prev) => [...prev, ...itemsToAdd]);
      setNextCursor(response.next_cursor);
    } catch (err: unknown) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoadingMore(false);
    }
  }, [nextCursor, loadingMore]);

  const addLiveEvent = useCallback((event: SecurityEvent) => {
    // 1. Strict deduplication by event_id
    if (seenEventIdsRef.current.has(event.event_id)) {
      return;
    }

    // 2. Filter matching check
    const currentFilters = filtersRef.current;
    if (currentFilters.event_type && event.event_type !== currentFilters.event_type) {
      return;
    }
    if (currentFilters.camera_id && event.camera_id !== currentFilters.camera_id) {
      return;
    }

    // 3. Register and prepend to events
    seenEventIdsRef.current.add(event.event_id);
    setEvents((prev) => [event, ...prev]);
  }, []);

  const reconcileAfterReconnect = useCallback(async () => {
    try {
      // Fetch latest 30 events to reconcile any gap while disconnected
      const response = await getEvents({
        ...filtersRef.current,
        limit: 30,
      });

      const missedEvents: SecurityEvent[] = [];
      for (const item of response.items) {
        if (!seenEventIdsRef.current.has(item.event_id)) {
          seenEventIdsRef.current.add(item.event_id);
          missedEvents.push(item);
        }
      }

      if (missedEvents.length > 0) {
        // Merge missed events and sort descending by occurred_at
        setEvents((prev) => {
          const combined = [...missedEvents, ...prev];
          return combined.sort(
            (a, b) => new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime()
          );
        });
      }
    } catch {
      // Reconcile error handled gracefully without crashing UI
    }
  }, []);

  const clearEvents = useCallback(() => {
    seenEventIdsRef.current.clear();
    setEvents([]);
    setNextCursor(null);
  }, []);

  // Re-fetch when filter criteria changes
  useEffect(() => {
    fetchInitial();
  }, [
    fetchInitial,
    filters.event_type,
    filters.camera_id,
    filters.limit,
  ]);

  return {
    events,
    loading,
    loadingMore,
    error,
    hasMore: Boolean(nextCursor),
    nextCursor,
    addLiveEvent,
    loadMore,
    refresh: fetchInitial,
    reconcileAfterReconnect,
    clearEvents,
  };
}
