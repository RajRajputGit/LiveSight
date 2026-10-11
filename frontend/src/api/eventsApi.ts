/**
 * API client methods for historical events with pagination and filtering.
 */

import { apiClient } from './client';
import { EventFilterParams, EventListResponse } from '../types/events';

export async function getEvents(params: EventFilterParams = {}): Promise<EventListResponse> {
  const query = new URLSearchParams();

  if (params.limit !== undefined) {
    query.append('limit', params.limit.toString());
  }
  if (params.before) {
    query.append('before', params.before);
  }
  if (params.event_type) {
    query.append('event_type', params.event_type);
  }
  if (params.camera_id) {
    query.append('camera_id', params.camera_id);
  }

  const queryString = query.toString();
  const endpoint = `/api/events${queryString ? `?${queryString}` : ''}`;

  return apiClient<EventListResponse>(endpoint);
}
