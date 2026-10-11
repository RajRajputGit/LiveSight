import React from 'react';
import { RuntimeStatusResponse, PipelineStatusType } from '../types/status';
import { ApiError } from '../api/client';

interface SystemStatusCardProps {
  status: RuntimeStatusResponse | null;
  loading: boolean;
  error: ApiError | Error | null;
  lastUpdated: Date | null;
  onRefresh: () => void;
}

export const SystemStatusCard: React.FC<SystemStatusCardProps> = ({
  status,
  loading,
  error,
  lastUpdated,
  onRefresh,
}) => {
  const getStatusBadge = (pipelineStatus: PipelineStatusType = 'idle') => {
    switch (pipelineStatus) {
      case 'running':
        return {
          bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400',
          dot: 'bg-emerald-400 animate-pulse',
          label: 'RUNNING',
        };
      case 'idle':
        return {
          bg: 'bg-sky-500/15 border-sky-500/30 text-sky-400',
          dot: 'bg-sky-400',
          label: 'IDLE',
        };
      case 'stopped':
        return {
          bg: 'bg-amber-500/15 border-amber-500/30 text-amber-400',
          dot: 'bg-amber-400',
          label: 'STOPPED',
        };
      case 'failed':
      case 'error':
      default:
        return {
          bg: 'bg-rose-500/15 border-rose-500/30 text-rose-400',
          dot: 'bg-rose-400',
          label: 'FAILED',
        };
    }
  };

  const badge = getStatusBadge(status?.pipeline_status);

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-zinc-800/80">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-sky-900/20">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-zinc-100">
              Pipeline Runtime Telemetry
            </h3>
            <p className="text-xs text-zinc-400">
              {lastUpdated
                ? `Polled at ${lastUpdated.toLocaleTimeString()}`
                : 'Waiting for heartbeat...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wider border ${badge.bg}`}
          >
            <span className={`w-2 h-2 rounded-full ${badge.dot}`} />
            {badge.label}
          </span>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 hover:border-zinc-500 transition-colors disabled:opacity-50"
            title="Refresh status"
          >
            <svg
              className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`}
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

      {/* Grid of properties */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4">
        {/* Active Source */}
        <div className="bg-zinc-950/60 rounded-xl p-3 border border-zinc-800/60">
          <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
            Video Source
          </span>
          <span className="text-sm font-semibold text-zinc-100 truncate block mt-1" title={status?.source_id || 'None'}>
            {status?.source_id ? status.source_id : 'No active source'}
          </span>
          <span className="text-[11px] text-zinc-500 capitalize block mt-0.5">
            Type: {status?.source_type || 'unassigned'}
          </span>
        </div>

        {/* Detector Status */}
        <div className="bg-zinc-950/60 rounded-xl p-3 border border-zinc-800/60">
          <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
            YOLO Detector
          </span>
          <div className="flex items-center gap-1.5 mt-1">
            <span
              className={`w-2 h-2 rounded-full ${
                status?.model_loaded ? 'bg-emerald-400' : 'bg-zinc-600'
              }`}
            />
            <span className="text-sm font-semibold text-zinc-100">
              {status?.model_loaded ? 'Model Ready' : 'Not Loaded'}
            </span>
          </div>
          <span className="text-[11px] text-zinc-500 block mt-0.5">
            Inference engine active
          </span>
        </div>

        {/* ByteTrack Mode */}
        <div className="bg-zinc-950/60 rounded-xl p-3 border border-zinc-800/60">
          <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
            Multi-Object Tracker
          </span>
          <div className="flex items-center gap-1.5 mt-1">
            <span
              className={`w-2 h-2 rounded-full ${
                status?.tracking_enabled ? 'bg-indigo-400' : 'bg-amber-400'
              }`}
            />
            <span className="text-sm font-semibold text-zinc-100">
              {status?.tracking_enabled ? 'ByteTrack' : 'Disabled'}
            </span>
          </div>
          <span className="text-[11px] text-zinc-500 block mt-0.5">
            {status?.tracking_enabled ? 'Track IDs active' : 'Raw detections'}
          </span>
        </div>

        {/* Last Frame Processed */}
        <div className="bg-zinc-950/60 rounded-xl p-3 border border-zinc-800/60">
          <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
            Latest Heartbeat
          </span>
          <span className="text-sm font-semibold text-zinc-100 block mt-1">
            {status?.last_frame_at
              ? new Date(status.last_frame_at).toLocaleTimeString()
              : 'None'}
          </span>
          <span className="text-[11px] text-zinc-500 block mt-0.5">
            {status?.last_frame_at
              ? new Date(status.last_frame_at).toLocaleDateString()
              : 'Awaiting feed'}
          </span>
        </div>
      </div>

      {/* Error callout if last_error is present */}
      {status?.last_error && (
        <div className="mt-4 p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 flex items-start gap-2">
          <span className="text-rose-400 font-bold">⚠️</span>
          <div>
            <strong className="font-semibold">Pipeline Alert: </strong>
            <span>{status.last_error}</span>
          </div>
        </div>
      )}

      {error && !status && (
        <div className="mt-4 p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-xs text-amber-300 flex items-center justify-between">
          <span>Backend status unreachable: {error.message}</span>
          <button
            onClick={onRefresh}
            className="text-xs underline hover:text-amber-100"
          >
            Retry
          </button>
        </div>
      )}
    </div>
  );
};
