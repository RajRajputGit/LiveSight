/**
 * React hook for live WebSocket event stream subscription.
 * Implements bounded exponential backoff reconnection and event deduplication hooks.
 * Matches WS /api/events/stream contract in 05_API_SPECIFICATION.md Section 5.
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { ConnectionStatus } from '../types/api';
import { EventStreamMessage, SecurityEvent } from '../types/events';

export interface UseEventStreamOptions {
  onEvent?: (event: SecurityEvent) => void;
  onReconnect?: () => void;
  enabled?: boolean;
}

export interface UseEventStreamResult {
  connectionStatus: ConnectionStatus;
  lastMessageAt: Date | null;
  reconnectCount: number;
  connect: () => void;
  disconnect: () => void;
}

const INITIAL_BACKOFF_MS = 1000;
const MAX_BACKOFF_MS = 10000;
const BACKOFF_MULTIPLIER = 1.5;

export function useEventStream(options: UseEventStreamOptions = {}): UseEventStreamResult {
  const { onEvent, onReconnect, enabled = true } = options;

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessageAt, setLastMessageAt] = useState<Date | null>(null);
  const [reconnectCount, setReconnectCount] = useState<number>(0);

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const backoffMsRef = useRef<number>(INITIAL_BACKOFF_MS);
  const isMountedRef = useRef<boolean>(true);
  const hadConnectedRef = useRef<boolean>(false);

  // Keep callback refs fresh
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;
  const onReconnectRef = useRef(onReconnect);
  onReconnectRef.current = onReconnect;

  const getWebSocketUrl = (): string => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/api/events/stream`;
  };

  const cleanupSocket = () => {
    if (socketRef.current) {
      socketRef.current.onopen = null;
      socketRef.current.onmessage = null;
      socketRef.current.onerror = null;
      socketRef.current.onclose = null;
      if (
        socketRef.current.readyState === WebSocket.OPEN ||
        socketRef.current.readyState === WebSocket.CONNECTING
      ) {
        socketRef.current.close();
      }
      socketRef.current = null;
    }
  };

  const scheduleReconnect = useCallback(() => {
    if (!isMountedRef.current || !enabled) return;

    if (reconnectTimeoutRef.current !== null) {
      window.clearTimeout(reconnectTimeoutRef.current);
    }

    setConnectionStatus('reconnecting');
    const delay = backoffMsRef.current;
    backoffMsRef.current = Math.min(backoffMsRef.current * BACKOFF_MULTIPLIER, MAX_BACKOFF_MS);

    reconnectTimeoutRef.current = window.setTimeout(() => {
      if (isMountedRef.current && enabled) {
        setReconnectCount((prev) => prev + 1);
        establishConnection();
      }
    }, delay);
  }, [enabled]);

  const establishConnection = useCallback(() => {
    if (!enabled || !isMountedRef.current) return;

    cleanupSocket();
    setConnectionStatus((prev) => (prev === 'connected' ? 'connected' : 'connecting'));

    const wsUrl = getWebSocketUrl();
    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setConnectionStatus('connected');
        backoffMsRef.current = INITIAL_BACKOFF_MS;

        // Trigger onReconnect callback if we were previously connected and reconnected
        if (hadConnectedRef.current && onReconnectRef.current) {
          onReconnectRef.current();
        }
        hadConnectedRef.current = true;
      };

      ws.onmessage = (event: MessageEvent) => {
        if (!isMountedRef.current) return;
        try {
          const payload = JSON.parse(event.data) as EventStreamMessage;
          if (payload && payload.type === 'event.created' && payload.data) {
            setLastMessageAt(new Date());
            if (onEventRef.current) {
              onEventRef.current(payload.data);
            }
          }
        } catch {
          // Non-JSON message received, ignore
        }
      };

      ws.onerror = () => {
        if (!isMountedRef.current) return;
        // On error, let ws.onclose trigger reconnection
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        setConnectionStatus('disconnected');
        scheduleReconnect();
      };
    } catch {
      scheduleReconnect();
    }
  }, [enabled, scheduleReconnect]);

  useEffect(() => {
    isMountedRef.current = true;

    if (enabled) {
      establishConnection();
    } else {
      cleanupSocket();
      setConnectionStatus('disconnected');
    }

    return () => {
      isMountedRef.current = false;
      if (reconnectTimeoutRef.current !== null) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      cleanupSocket();
    };
  }, [enabled, establishConnection]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current !== null) {
      window.clearTimeout(reconnectTimeoutRef.current);
    }
    cleanupSocket();
    setConnectionStatus('disconnected');
  }, []);

  const connect = useCallback(() => {
    backoffMsRef.current = INITIAL_BACKOFF_MS;
    establishConnection();
  }, [establishConnection]);

  return {
    connectionStatus,
    lastMessageAt,
    reconnectCount,
    connect,
    disconnect,
  };
}
