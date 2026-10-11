/**
 * Centralized HTTP API client with standardized error parsing.
 * Preserves 05_API_SPECIFICATION.md error contract.
 */

import { ApiErrorResponse } from '../types/api';

export class ApiError extends Error {
  public code: string;
  public details?: unknown;
  public status: number;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, { ...options, headers });

    if (!response.ok) {
      let errorBody: ApiErrorResponse | null = null;
      try {
        errorBody = await response.json();
      } catch {
        // Response was not JSON
      }

      if (errorBody && errorBody.error) {
        throw new ApiError(
          response.status,
          errorBody.error.code || 'API_ERROR',
          errorBody.error.message || `Request failed with status ${response.status}`,
          errorBody.error.details
        );
      }

      throw new ApiError(
        response.status,
        'HTTP_ERROR',
        `Request to ${endpoint} failed with HTTP status ${response.status}`
      );
    }

    return (await response.json()) as T;
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    const message = err instanceof Error ? err.message : 'Network error or backend unreachable';
    throw new ApiError(0, 'NETWORK_ERROR', message);
  }
}
