import React from 'react';
import { SecurityEvent } from '../types/events';
import { RuntimeStatusResponse } from '../types/status';

interface CameraPreviewPlaceholderProps {
  status: RuntimeStatusResponse | null;
  latestEvent: SecurityEvent | null;
}

export const CameraPreviewPlaceholder: React.FC<CameraPreviewPlaceholderProps> = ({
  status,
  latestEvent,
}) => {
  const isRunning = status?.pipeline_status === 'running';

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur-md flex flex-col">
      {/* Viewport Header */}
      <div className="p-4 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-950/40">
        <div className="flex items-center gap-2.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
          <h3 className="text-sm font-semibold text-zinc-100">
            Spatial Surveillance Viewport
          </h3>
          <span className="text-xs px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 font-mono">
            {status?.source_id || 'source_0'}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-zinc-800/80 border border-zinc-700/60 font-mono text-[11px]">
            {isRunning ? 'PIPELINE ACTIVE' : 'PIPELINE IDLE'}
          </span>
        </div>
      </div>

      {/* Visual Canvas Area */}
      <div className="relative aspect-video w-full bg-gradient-to-b from-zinc-950 via-zinc-900 to-zinc-950 flex flex-col items-center justify-center p-6 border-b border-zinc-800/50 overflow-hidden">
        {/* Subtle grid pattern background */}
        <div
          className="absolute inset-0 opacity-15 pointer-events-none"
          style={{
            backgroundImage:
              'linear-gradient(to right, #38bdf8 1px, transparent 1px), linear-gradient(to bottom, #38bdf8 1px, transparent 1px)',
            backgroundSize: '32px 32px',
          }}
        />

        {/* Spatial Zone Overlay Graphic */}
        <div className="absolute inset-6 border border-dashed border-rose-500/30 rounded-lg pointer-events-none flex items-start justify-end p-2">
          <span className="text-[10px] font-mono text-rose-400/70 bg-rose-950/60 px-1.5 py-0.5 rounded border border-rose-800/40">
            ZONE: restricted_zone_A
          </span>
        </div>

        {/* If we have a latest event with bounding box, visualize it */}
        {latestEvent ? (
          <div className="relative z-10 flex flex-col items-center text-center max-w-md p-4 rounded-xl bg-zinc-900/90 border border-rose-500/50 shadow-2xl backdrop-blur-md animate-fade-in">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-mono border border-rose-500/40 font-semibold uppercase">
                🚨 {latestEvent.event_type}
              </span>
              <span className="text-xs px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono border border-sky-500/40">
                {latestEvent.object_class} {latestEvent.track_id ? `#${latestEvent.track_id}` : ''}
              </span>
            </div>

            <div className="text-xs text-zinc-300 space-y-1">
              <div>
                <span className="text-zinc-500">Zone: </span>
                <span className="text-rose-300 font-semibold">{latestEvent.zone_id}</span>
                <span className="text-zinc-500 ml-3">Confidence: </span>
                <span className="text-emerald-400 font-semibold">
                  {(latestEvent.confidence * 100).toFixed(1)}%
                </span>
              </div>

              {latestEvent.bbox && (
                <div className="font-mono text-[11px] text-zinc-400 mt-2 bg-zinc-950/80 px-2 py-1 rounded border border-zinc-800">
                  Target BBox: [x1: {Math.round(latestEvent.bbox.x1)}, y1: {Math.round(latestEvent.bbox.y1)}, x2: {Math.round(latestEvent.bbox.x2)}, y2: {Math.round(latestEvent.bbox.y2)}]
                </div>
              )}
            </div>

            <div className="text-[11px] text-zinc-500 mt-2">
              Detected at: {new Date(latestEvent.occurred_at).toLocaleTimeString()}
            </div>
          </div>
        ) : (
          <div className="relative z-10 flex flex-col items-center text-center max-w-sm text-zinc-400">
            <div className="w-12 h-12 rounded-full bg-zinc-800/80 border border-zinc-700/80 flex items-center justify-center text-zinc-300 mb-3 shadow-inner">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h4 className="text-sm font-medium text-zinc-200">
              {isRunning ? 'Monitoring Stream...' : 'Pipeline Standing By'}
            </h4>
            <p className="text-xs text-zinc-500 mt-1">
              {isRunning
                ? 'Listening for restricted-zone intrusions and tracking trajectories.'
                : 'Start the vision pipeline to detect and stream events.'}
            </p>
          </div>
        )}
      </div>

      {/* Architecture Disclaimer / Policy Footer */}
      <div className="p-3 bg-zinc-950/70 border-t border-zinc-800/60 text-[11px] text-zinc-400 flex items-center gap-2">
        <span className="text-sky-400 text-xs shrink-0">ℹ️</span>
        <span>
          <strong>Architecture Note (ADR-005):</strong> Live spatial events and bounding boxes are streamed in real time via WebSockets. Raw video streaming (RTSP/WebRTC) is reserved for Phase 7.
        </span>
      </div>
    </div>
  );
};
