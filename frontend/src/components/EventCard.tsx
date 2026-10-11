import React from 'react';
import { SecurityEvent } from '../types/events';

interface EventCardProps {
  event: SecurityEvent;
  isNew?: boolean;
}

export const EventCard: React.FC<EventCardProps> = ({ event, isNew = false }) => {
  const formattedDate = new Date(event.occurred_at).toLocaleString();
  const confidencePercent = (event.confidence * 100).toFixed(1);

  return (
    <div
      className={`relative bg-zinc-900/90 border rounded-xl p-4 transition-all duration-300 hover:border-zinc-700 shadow-md ${
        isNew
          ? 'border-rose-500/70 shadow-rose-950/40 bg-zinc-900/95 ring-1 ring-rose-500/30'
          : 'border-zinc-800'
      }`}
    >
      {/* Top row: event alert type, timestamp, isNew badge */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-rose-500 shrink-0" />
          <h4 className="text-sm font-semibold text-zinc-100 flex items-center gap-1.5">
            <span>🚨</span>
            <span className="capitalize">{event.event_type.replace(/_/g, ' ')}</span>
          </h4>
          {isNew && (
            <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-rose-600/30 text-rose-300 border border-rose-500/50">
              LIVE
            </span>
          )}
        </div>

        <span className="text-xs text-zinc-400 font-mono shrink-0" title={event.occurred_at}>
          {formattedDate}
        </span>
      </div>

      {/* Badges row: Zone, Object Class, Track ID, Camera ID */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="text-xs px-2 py-0.5 rounded-md bg-rose-950/60 border border-rose-800/60 text-rose-300 font-medium">
          Zone: <span className="font-semibold text-rose-200">{event.zone_id}</span>
        </span>

        <span className="text-xs px-2 py-0.5 rounded-md bg-sky-950/60 border border-sky-800/60 text-sky-300 font-medium">
          Class: <span className="font-semibold text-sky-200 capitalize">{event.object_class}</span>
        </span>

        <span
          className={`text-xs px-2 py-0.5 rounded-md border font-medium ${
            event.track_id
              ? 'bg-indigo-950/60 border-indigo-800/60 text-indigo-300'
              : 'bg-zinc-800/60 border-zinc-700/60 text-zinc-400'
          }`}
        >
          {event.track_id ? `Track #${event.track_id}` : 'Untracked'}
        </span>

        <span className="text-xs px-2 py-0.5 rounded-md bg-zinc-800/60 border border-zinc-700/60 text-zinc-400 font-mono">
          Camera: {event.camera_id}
        </span>

        <span className="text-xs px-2 py-0.5 rounded-md bg-emerald-950/60 border border-emerald-800/60 text-emerald-300 font-mono ml-auto">
          {confidencePercent}% conf
        </span>
      </div>

      {/* Bounding box and Event ID footer */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-zinc-800/70 text-[11px] text-zinc-500">
        <div className="font-mono">
          {event.bbox ? (
            <span>
              BBox: [{Math.round(event.bbox.x1)}, {Math.round(event.bbox.y1)},{' '}
              {Math.round(event.bbox.x2)}, {Math.round(event.bbox.y2)}]
            </span>
          ) : (
            <span>No bounding box</span>
          )}
        </div>

        <div className="font-mono text-zinc-500 truncate max-w-[200px]" title={event.event_id}>
          ID: {event.event_id}
        </div>
      </div>
    </div>
  );
};
