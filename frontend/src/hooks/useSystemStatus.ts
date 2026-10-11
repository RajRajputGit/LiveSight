/**
 * React hook for monitoring backend and pipeline runtime status.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { getStatus } from '../api/statusApi';
import { RuntimeStatusResponse } from '../types/status';
import { ApiError } from '../api/client';

export interface UseSystemStatusResult {
  status: RuntimeStatusResponse | null;
  loading: boolean;
  error: ApiError | Error | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
}

export function useSystemStatus(pollIntervalMs: number = 3000): UseSystemStatusResult {
  const [status, setStatus] = useState<RuntimeStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const isMountedRef = useRef<boolean>(true);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getStatus();
      if (isMountedRef.current) {
        setStatus(data);
        setError(null);
        setLastUpdated(new Date());
        setLoading(false);
      }
    } catch (err: unknown) {
      if (isMountedRef.current) {
        setError(err instanceof Error ? err : new Error(String(err)));
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    fetchStatus();

    if (pollIntervalMs > 0) {
      const intervalId = window.setInterval(fetchStatus, pollIntervalMs);
      return () => {
        isMountedRef.current = false;
        window.clearInterval(intervalId);
      };
    }

    return () => {
      isMountedRef.current = false;
    };
  }, [fetchStatus, pollIntervalMs]);

  return {
    status,
    loading,
    error,
    lastUpdated,
    refresh: fetchStatus,
  };
}
