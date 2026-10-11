/**
 * Pipeline status and health response types.
 * Matches backend schemas in backend/app/schemas/status.py
 * and 05_API_SPECIFICATION.md Section 2 & 3.
 */

export type PipelineStatusType =
  | 'idle'
  | 'running'
  | 'error'
  | 'stopped'
  | 'failed';

export interface HealthResponse {
  status: string;
  service: string;
}

export interface RuntimeStatusResponse {
  pipeline_status: PipelineStatusType;
  source_id: string | null;
  source_type: string;
  model_loaded: boolean;
  tracking_enabled: boolean;
  last_frame_at: string | null;
  last_error: string | null;
}
