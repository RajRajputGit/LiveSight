import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useEventHistory } from '../hooks/useEventHistory';
import * as eventsApi from '../api/eventsApi';
import { SecurityEvent } from '../types/events';

const mockEvent1: SecurityEvent = {
  event_id: 'evt_01',
  camera_id: 'cam_1',
  event_type: 'restricted_zone_intrusion',
  occurred_at: '2026-10-10T12:00:00.000Z',
  object_class: 'person',
  track_id: '1',
  confidence: 0.95,
  zone_id: 'restricted_zone_A',
  bbox: { x1: 10, y1: 20, x2: 30, y2: 40 },
  snapshot_path: null,
};

const mockEvent2: SecurityEvent = {
  event_id: 'evt_02',
  camera_id: 'cam_1',
  event_type: 'restricted_zone_intrusion',
  occurred_at: '2026-10-10T12:01:00.000Z',
  object_class: 'person',
  track_id: '2',
  confidence: 0.88,
  zone_id: 'restricted_zone_A',
  bbox: { x1: 50, y1: 60, x2: 70, y2: 80 },
  snapshot_path: null,
};

describe('useEventHistory hook', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('fetches initial events and avoids duplicates', async () => {
    vi.spyOn(eventsApi, 'getEvents').mockResolvedValue({
      items: [mockEvent2, mockEvent1, mockEvent1], // duplicate in response
      next_cursor: 'cursor_123',
    });

    const { result } = renderHook(() => useEventHistory({ limit: 50 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Should have deduplicated mockEvent1
    expect(result.current.events).toHaveLength(2);
    expect(result.current.events[0].event_id).toBe('evt_02');
    expect(result.current.events[1].event_id).toBe('evt_01');
    expect(result.current.hasMore).toBe(true);
  });

  it('addLiveEvent prepends new event and strictly deduplicates existing ID', async () => {
    vi.spyOn(eventsApi, 'getEvents').mockResolvedValue({
      items: [mockEvent1],
      next_cursor: null,
    });

    const { result } = renderHook(() => useEventHistory({ limit: 50 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Add unique live event
    act(() => {
      result.current.addLiveEvent(mockEvent2);
    });
    expect(result.current.events).toHaveLength(2);
    expect(result.current.events[0].event_id).toBe('evt_02');

    // Try to add duplicate of mockEvent1
    act(() => {
      result.current.addLiveEvent(mockEvent1);
    });
    expect(result.current.events).toHaveLength(2); // Still 2!
  });

  it('reconcileAfterReconnect merges missed events without duplicating', async () => {
    vi.spyOn(eventsApi, 'getEvents').mockResolvedValueOnce({
      items: [mockEvent1],
      next_cursor: null,
    });

    const { result } = renderHook(() => useEventHistory({ limit: 50 }));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.events).toHaveLength(1);

    // Mock reconnect response that includes both old event and a new missed event
    vi.spyOn(eventsApi, 'getEvents').mockResolvedValueOnce({
      items: [mockEvent2, mockEvent1],
      next_cursor: null,
    });

    await act(async () => {
      await result.current.reconcileAfterReconnect();
    });

    expect(result.current.events).toHaveLength(2);
    expect(result.current.events.map((e) => e.event_id)).toEqual(['evt_02', 'evt_01']);
  });
});
