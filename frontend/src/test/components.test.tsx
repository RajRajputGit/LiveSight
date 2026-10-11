import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ConnectionBadge } from '../components/ConnectionBadge';
import { SystemStatusCard } from '../components/SystemStatusCard';
import { EventCard } from '../components/EventCard';
import { EventFilters } from '../components/EventFilters';
import { EventList } from '../components/EventList';
import { SecurityEvent } from '../types/events';
import { RuntimeStatusResponse } from '../types/status';

const sampleEvent: SecurityEvent = {
  event_id: 'evt_01JEXAMPLE01',
  camera_id: 'local_camera_01',
  event_type: 'restricted_zone_intrusion',
  occurred_at: '2026-10-10T12:00:00.000Z',
  object_class: 'person',
  track_id: '12',
  confidence: 0.94,
  zone_id: 'restricted_zone_A',
  bbox: { x1: 100, y1: 150, x2: 250, y2: 400 },
  snapshot_path: null,
};

describe('Frontend Components', () => {
  describe('ConnectionBadge', () => {
    it('renders connected state correctly', () => {
      render(<ConnectionBadge status="connected" />);
      expect(screen.getByText('WS Live')).toBeInTheDocument();
    });

    it('renders disconnected state and allows reconnect click', () => {
      const handleReconnect = vi.fn();
      render(<ConnectionBadge status="disconnected" onReconnectClick={handleReconnect} />);
      expect(screen.getByText('WS Disconnected')).toBeInTheDocument();

      const btn = screen.getByText('Reconnect');
      fireEvent.click(btn);
      expect(handleReconnect).toHaveBeenCalledTimes(1);
    });

    it('renders reconnecting state with count', () => {
      render(<ConnectionBadge status="reconnecting" reconnectCount={3} />);
      expect(screen.getByText('Reconnecting (3)...')).toBeInTheDocument();
    });
  });

  describe('SystemStatusCard', () => {
    it('renders runtime telemetry and running status', () => {
      const mockStatus: RuntimeStatusResponse = {
        pipeline_status: 'running',
        source_id: 'sample_video.mp4',
        source_type: 'file',
        model_loaded: true,
        tracking_enabled: true,
        last_frame_at: '2026-10-10T12:00:00.000Z',
        last_error: null,
      };

      const handleRefresh = vi.fn();
      render(
        <SystemStatusCard
          status={mockStatus}
          loading={false}
          error={null}
          lastUpdated={new Date('2026-10-10T12:00:01.000Z')}
          onRefresh={handleRefresh}
        />
      );

      expect(screen.getByText('RUNNING')).toBeInTheDocument();
      expect(screen.getByText('sample_video.mp4')).toBeInTheDocument();
      expect(screen.getByText('Model Ready')).toBeInTheDocument();
      expect(screen.getByText('ByteTrack')).toBeInTheDocument();
    });

    it('renders idle status when pipeline is idle', () => {
      const mockStatus: RuntimeStatusResponse = {
        pipeline_status: 'idle',
        source_id: null,
        source_type: 'unknown',
        model_loaded: false,
        tracking_enabled: false,
        last_frame_at: null,
        last_error: null,
      };

      render(
        <SystemStatusCard
          status={mockStatus}
          loading={false}
          error={null}
          lastUpdated={null}
          onRefresh={vi.fn()}
        />
      );

      expect(screen.getByText('IDLE')).toBeInTheDocument();
      expect(screen.getByText('No active source')).toBeInTheDocument();
      expect(screen.getByText('Not Loaded')).toBeInTheDocument();
    });
  });

  describe('EventCard', () => {
    it('renders all event metadata and attributes accurately', () => {
      render(<EventCard event={sampleEvent} isNew={true} />);

      expect(screen.getByText(/restricted zone intrusion/i)).toBeInTheDocument();
      expect(screen.getByText('restricted_zone_A')).toBeInTheDocument();
      expect(screen.getByText('person')).toBeInTheDocument();
      expect(screen.getByText('Track #12')).toBeInTheDocument();
      expect(screen.getByText('94.0% conf')).toBeInTheDocument();
      expect(screen.getByText('LIVE')).toBeInTheDocument();
      expect(screen.getByText(/BBox: \[100, 150, 250, 400\]/i)).toBeInTheDocument();
    });

    it('handles untracked event without track id', () => {
      const untrackedEvent: SecurityEvent = {
        ...sampleEvent,
        event_id: 'evt_untracked_99',
        track_id: null,
      };

      render(<EventCard event={untrackedEvent} isNew={false} />);
      expect(screen.getByText('Untracked')).toBeInTheDocument();
    });
  });

  describe('EventFilters', () => {
    it('triggers filter change on event type select', () => {
      const handleFilterChange = vi.fn();
      render(
        <EventFilters
          filters={{ limit: 50 }}
          onFilterChange={handleFilterChange}
          totalEventsCount={5}
        />
      );

      const select = screen.getByLabelText(/event type/i);
      fireEvent.change(select, { target: { value: 'restricted_zone_intrusion' } });

      expect(handleFilterChange).toHaveBeenCalledWith({
        limit: 50,
        event_type: 'restricted_zone_intrusion',
      });
    });

    it('allows clearing filters', () => {
      const handleFilterChange = vi.fn();
      render(
        <EventFilters
          filters={{ limit: 50, event_type: 'restricted_zone_intrusion' }}
          onFilterChange={handleFilterChange}
          totalEventsCount={1}
        />
      );

      const resetBtn = screen.getByText('Reset Filters');
      fireEvent.click(resetBtn);

      expect(handleFilterChange).toHaveBeenCalledWith({ limit: 50 });
    });
  });

  describe('EventList', () => {
    it('renders empty state when there are no events', () => {
      render(
        <EventList
          events={[]}
          loading={false}
          loadingMore={false}
          error={null}
          hasMore={false}
          onLoadMore={vi.fn()}
          onRetry={vi.fn()}
        />
      );

      expect(screen.getByText('No Security Events Recorded')).toBeInTheDocument();
    });

    it('renders list of events and pagination button when hasMore is true', () => {
      const handleLoadMore = vi.fn();
      render(
        <EventList
          events={[sampleEvent]}
          loading={false}
          loadingMore={false}
          error={null}
          hasMore={true}
          onLoadMore={handleLoadMore}
          onRetry={vi.fn()}
        />
      );

      expect(screen.getByText(/restricted zone intrusion/i)).toBeInTheDocument();
      const loadMoreBtn = screen.getByText('Load More Historical Events');
      fireEvent.click(loadMoreBtn);
      expect(handleLoadMore).toHaveBeenCalledTimes(1);
    });
  });
});
