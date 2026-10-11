import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiClient, ApiError } from '../api/client';
import { getStatus } from '../api/statusApi';
import { getEvents } from '../api/eventsApi';

describe('Frontend API Clients', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('apiClient parses successful JSON response', async () => {
    const mockData = { status: 'ok', service: 'ai-vision-backend' };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockData,
    });

    const res = await apiClient<{ status: string }>('/api/health');
    expect(res).toEqual(mockData);
  });

  it('apiClient parses backend standardized error format into ApiError', async () => {
    const errorBody = {
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid limit value',
        details: [{ loc: ['query', 'limit'], msg: 'must be <= 100' }],
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => errorBody,
    });

    try {
      await apiClient('/api/events?limit=999');
      expect.fail('Should have thrown ApiError');
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.code).toBe('VALIDATION_ERROR');
      expect(apiErr.message).toBe('Invalid limit value');
    }
  });

  it('getStatus calls /api/status', async () => {
    const mockStatus = {
      pipeline_status: 'running',
      source_id: '0',
      source_type: 'webcam',
      model_loaded: true,
      tracking_enabled: true,
      last_frame_at: '2026-10-10T12:00:00.000Z',
      last_error: null,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockStatus,
    });

    const res = await getStatus();
    expect(res).toEqual(mockStatus);
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/status', expect.anything());
  });

  it('getEvents builds query parameters properly', async () => {
    const mockEvents = { items: [], next_cursor: null };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockEvents,
    });

    await getEvents({
      limit: 25,
      event_type: 'restricted_zone_intrusion',
      camera_id: 'cam_front',
      before: 'cursor_abc',
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      '/api/events?limit=25&before=cursor_abc&event_type=restricted_zone_intrusion&camera_id=cam_front',
      expect.anything()
    );
  });
});
