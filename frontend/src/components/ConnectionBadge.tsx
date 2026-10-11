import React from 'react';
import { ConnectionStatus } from '../types/api';

interface ConnectionBadgeProps {
  status: ConnectionStatus;
  reconnectCount?: number;
  onReconnectClick?: () => void;
}

export const ConnectionBadge: React.FC<ConnectionBadgeProps> = ({
  status,
  reconnectCount = 0,
  onReconnectClick,
}) => {
  const getBadgeConfig = () => {
    switch (status) {
      case 'connected':
        return {
          bg: 'bg-emerald-950/60 border-emerald-500/40 text-emerald-400',
          dot: 'bg-emerald-400 animate-pulse',
          label: 'WS Live',
        };
      case 'connecting':
        return {
          bg: 'bg-amber-950/60 border-amber-500/40 text-amber-400',
          dot: 'bg-amber-400 animate-ping',
          label: 'Connecting...',
        };
      case 'reconnecting':
        return {
          bg: 'bg-orange-950/60 border-orange-500/40 text-orange-400',
          dot: 'bg-orange-400 animate-pulse',
          label: `Reconnecting (${reconnectCount})...`,
        };
      case 'disconnected':
      default:
        return {
          bg: 'bg-rose-950/60 border-rose-500/40 text-rose-400',
          dot: 'bg-rose-400',
          label: 'WS Disconnected',
        };
    }
  };

  const config = getBadgeConfig();

  return (
    <div className="flex items-center gap-2">
      <div
        className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-medium border ${config.bg} transition-colors`}
        title={`WebSocket status: ${status}`}
      >
        <span className={`w-2 h-2 rounded-full ${config.dot}`} />
        <span>{config.label}</span>
      </div>

      {status === 'disconnected' && onReconnectClick && (
        <button
          onClick={onReconnectClick}
          className="text-xs px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 hover:border-zinc-500 transition-colors"
          title="Attempt WebSocket reconnect"
        >
          Reconnect
        </button>
      )}
    </div>
  );
};
