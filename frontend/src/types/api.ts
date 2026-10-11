/**
 * Standard API error contract matching backend backend/app/schemas/error.py
 * and 05_API_SPECIFICATION.md Section 6.
 */

export interface ApiErrorDetail {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
  [key: string]: unknown;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: ApiErrorDetail[] | Record<string, unknown> | null;
  };
}

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected' | 'reconnecting';
