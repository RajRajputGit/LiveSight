# API Specification

This is the initial contract for the local MVP. Keep implementation aligned with this document. If a contract changes, update this file and add/adjust tests in the same change.

## 1. Conventions
- Base URL during local development: `http://localhost:8000`
- JSON request/response bodies.
- Timestamps: ISO 8601 with timezone; prefer UTC in API responses.
- API versioning can be introduced when external clients depend on the API.
- Error responses should have a consistent shape.
- Do not expose filesystem paths or secrets unnecessarily.

## 2. Health endpoint
### `GET /api/health`
Purpose: report whether the backend process is responding.

Example response:
```json
{
  "status": "ok",
  "service": "ai-vision-backend"
}
```

## 3. Runtime status endpoint
### `GET /api/status`
Purpose: report the state of the video source and processing pipeline.

Example response:
```json
{
  "pipeline_status": "running",
  "source_id": "local_camera_01",
  "source_type": "webcam",
  "model_loaded": true,
  "tracking_enabled": true,
  "last_frame_at": "2026-10-09T17:12:15.120Z",
  "last_error": null
}
```
Use enumerated states and validate fields in the implementation.

## 4. Event history
### `GET /api/events`
Query parameters:
- `limit`: optional integer with a documented maximum.
- `before`: optional cursor or timestamp for pagination.
- `event_type`: optional event type filter.
- `camera_id`: optional source filter.

Example response:
```json
{
  "items": [
    {
      "event_id": "evt_01JEXAMPLE",
      "camera_id": "local_camera_01",
      "event_type": "restricted_zone_intrusion",
      "occurred_at": "2026-10-09T17:12:15.120Z",
      "object_class": "person",
      "track_id": "7",
      "confidence": 0.94,
      "zone_id": "restricted_zone_A",
      "bbox": {"x1": 120, "y1": 80, "x2": 260, "y2": 430},
      "snapshot_path": null
    }
  ],
  "next_cursor": null
}
```

## 5. Live event stream
### `WS /api/events/stream`
Server sends one JSON message per event:
```json
{
  "type": "event.created",
  "data": {
    "event_id": "evt_01JEXAMPLE",
    "camera_id": "local_camera_01",
    "event_type": "restricted_zone_intrusion",
    "occurred_at": "2026-10-09T17:12:15.120Z",
    "object_class": "person",
    "track_id": "7",
    "confidence": 0.94,
    "zone_id": "restricted_zone_A",
    "bbox": {"x1": 120, "y1": 80, "x2": 260, "y2": 430},
    "snapshot_path": null
  }
}
```
Client requirements:
- Handle disconnects.
- Reconnect with bounded backoff.
- Deduplicate events by `event_id`.
- Fetch history after reconnect if missed events matter.

## 6. Error response
Recommended shape:
```json
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "The limit parameter must be within the allowed range."
  }
}
```

## 7. Future endpoints (not in initial scope)
- `GET /api/sources`
- `POST /api/sources`
- `GET /api/zones`
- `POST /api/zones`
- `PATCH /api/zones/{zone_id}`
- `POST /api/pipeline/start`
- `POST /api/pipeline/stop`
- `GET /api/metrics`

Do not expose remote start/stop controls until authorization and safe lifecycle management are designed.

## 8. API acceptance tests
- Health returns successful response when backend is ready.
- Status fields match the actual pipeline state.
- Event history supports limits and returns stable ordering.
- Invalid query values return a validation error.
- WebSocket emits valid schema messages.
- WebSocket disconnect does not crash the publisher.
- Persisted events remain available after backend restart.
