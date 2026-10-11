/**
 * API client methods for status and health.
 */

import { apiClient } from './client';
import { HealthResponse, RuntimeStatusResponse } from '../types/status';

export async function getHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>('/api/health');
}

export async function getStatus(): Promise<RuntimeStatusResponse> {
  return apiClient<RuntimeStatusResponse>('/api/status');
}
