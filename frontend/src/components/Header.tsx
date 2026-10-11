import React, { useState, useEffect } from 'react';
import { ConnectionStatus } from '../types/api';
import { ConnectionBadge } from './ConnectionBadge';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  reconnectCount: number;
  onReconnectClick: () => void;
  onRefreshAll: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  connectionStatus,
  reconnectCount,
  onReconnectClick,
  onRefreshAll,
  isRefreshing = false,
}) => {
  const [currentTime, setCurrentTime] = useState<string>(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-500 to-rose-500 p-0.5 shadow-lg shadow-sky-500/20">
            <div className="w-full h-full bg-zinc-950 rounded-[10px] flex items-center justify-center">
              <svg
                className="w-5 h-5 text-sky-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-zinc-100">
                LiveSight
              </h1>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.2 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30 font-semibold">
                Phase 5
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Real-Time AI Vision & Event Engine
            </p>
          </div>
        </div>

        {/* Right side controls: Clock, WS status badge, Refresh button */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-zinc-400 font-mono bg-zinc-900/80 px-2.5 py-1 rounded-lg border border-zinc-800">
            <span className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
            <span>{currentTime}</span>
          </div>

          <ConnectionBadge
            status={connectionStatus}
            reconnectCount={reconnectCount}
            onReconnectClick={onReconnectClick}
          />

          <button
            onClick={onRefreshAll}
            disabled={isRefreshing}
            className="p-2 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 hover:border-zinc-700 transition-colors disabled:opacity-50"
            title="Refresh dashboard data"
          >
            <svg
              className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};
