/**
 * Event data types matching backend schemas in backend/app/schemas/event.py
 * and 03_WORKFLOW_AND_DATA_CONTRACTS.md & 05_API_SPECIFICATION.md Section 4 & 5.
 */

export interface BoundingBoxDict {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface SecurityEvent {
  event_id: string;
  camera_id: string;
  event_type: string;
  occurred_at: string;
  object_class: string;
  track_id: string | null;
  confidence: number;
  zone_id: string;
  bbox: BoundingBoxDict | null;
  snapshot_path: string | null;
}

export interface EventListResponse {
  items: SecurityEvent[];
  next_cursor: string | null;
}

export interface EventStreamMessage {
  type: string;
  data: SecurityEvent;
}

export interface EventFilterParams {
  limit?: number;
  before?: string;
  event_type?: string;
  camera_id?: string;
}
