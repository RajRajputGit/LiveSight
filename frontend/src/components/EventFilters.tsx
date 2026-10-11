import React from 'react';
import { EventFilterParams } from '../types/events';

interface EventFiltersProps {
  filters: EventFilterParams;
  onFilterChange: (filters: EventFilterParams) => void;
  totalEventsCount: number;
}

export const EventFilters: React.FC<EventFiltersProps> = ({
  filters,
  onFilterChange,
  totalEventsCount,
}) => {
  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    onFilterChange({
      ...filters,
      event_type: val === 'all' ? undefined : val,
    });
  };

  const handleCameraChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.trim();
    onFilterChange({
      ...filters,
      camera_id: val === '' ? undefined : val,
    });
  };

  const handleReset = () => {
    onFilterChange({ limit: 50 });
  };

  const hasActiveFilters = Boolean(filters.event_type || filters.camera_id);

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-2xl p-4 shadow-md backdrop-blur-md flex flex-wrap items-center justify-between gap-4">
      <div className="flex flex-wrap items-center gap-3">
        {/* Event Type Filter */}
        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="event-type-select" className="text-zinc-400 font-medium">
            Event Type:
          </label>
          <select
            id="event-type-select"
            value={filters.event_type || 'all'}
            onChange={handleTypeChange}
            className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-sky-500 transition-colors"
          >
            <option value="all">All Events</option>
            <option value="restricted_zone_intrusion">Restricted Zone Intrusion</option>
          </select>
        </div>

        {/* Camera ID Filter */}
        <div className="flex items-center gap-2 text-xs">
          <label htmlFor="camera-id-input" className="text-zinc-400 font-medium">
            Source / Camera:
          </label>
          <input
            id="camera-id-input"
            type="text"
            placeholder="e.g. cam_01"
            value={filters.camera_id || ''}
            onChange={handleCameraChange}
            className="bg-zinc-950 border border-zinc-800 text-zinc-200 text-xs rounded-lg px-2.5 py-1.5 w-32 focus:outline-none focus:border-sky-500 transition-colors placeholder:text-zinc-600"
          >
          </input>
        </div>

        {hasActiveFilters && (
          <button
            onClick={handleReset}
            className="text-xs text-sky-400 hover:text-sky-300 underline font-medium"
          >
            Reset Filters
          </button>
        )}
      </div>

      <div className="text-xs text-zinc-400 flex items-center gap-2">
        <span>Recorded Events:</span>
        <span className="font-semibold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-200 font-mono">
          {totalEventsCount}
        </span>
      </div>
    </div>
  );
};
