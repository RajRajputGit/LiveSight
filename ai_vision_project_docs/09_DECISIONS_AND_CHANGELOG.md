# Architecture Decisions and Changelog

## How to record decisions
For every decision that changes architecture, dependencies, data contracts, or deployment assumptions, add a short Architecture Decision Record (ADR). Keep accepted decisions even if they are later superseded.

## ADR template
```markdown
## ADR-NNN: [Decision title]
- Status: Proposed / Accepted / Superseded
- Date:
- Context:
- Decision:
- Alternatives considered:
- Consequences:
- Follow-up tasks:
```

## Initial decisions

### ADR-001: Local-first modular monolith
- Status: Accepted
- Context: The project is for hands-on learning and must run on a developer machine before scaling.
- Decision: Start with a modular Python application, one video source, FastAPI, SQLite, and a separate React frontend.
- Alternatives: Start with microservices, cloud-managed services, or a multi-device cluster.
- Consequences: Easier debugging and lower setup cost. Interfaces should remain modular so components can be separated later.

### ADR-002: Pretrained detector before custom training
- Status: Accepted
- Context: The immediate goal is to learn system integration, not dataset collection.
- Decision: Start with a pretrained YOLO model and evaluate whether it meets the target use case.
- Alternatives: Train a custom model immediately.
- Consequences: Faster initial progress; model accuracy is limited by its training data and supported classes. Review licensing before redistribution/commercial use.

### ADR-003: Deterministic rules separate from inference
- Status: Accepted
- Context: Event rules should be testable without running a neural network.
- Decision: Implement zone geometry and state transitions in a separate rule module.
- Consequences: Easier testing and predictable alert behavior.

### ADR-004: SQLite for initial persistence
- Status: Accepted
- Context: The first deployment is single-machine and local.
- Decision: Store event metadata in SQLite initially.
- Alternatives: PostgreSQL or a cloud database.
- Consequences: Minimal setup; migration may be needed for multi-user or concurrent deployment.

### ADR-005: Event metadata over frame streaming for backend MVP
- Status: Accepted
- Context: Live events are required, but relaying every video frame through FastAPI adds complexity and bandwidth.
- Decision: Send event metadata through WebSockets first; display video through a separate local preview or a later explicit streaming design.
- Consequences: Clear separation of events and media; video streaming needs its own design.

### ADR-006: Standalone YOLO Vision Adapter and Schema Contracts
- Status: Accepted
- Date: 2026-10-10
- Context: Phase 1 requires running object detection on local video and webcam with clean error handling, FPS diagnostics, and modular design.
- Decision: Use Python 3.10 with Ultralytics YOLO (`yolo11n.pt`) and OpenCV; structure the vision pipeline into modular components (`source`, `detector`, `annotator`, `pipeline`, and `schemas`) emitting normalized `Detection` and `BoundingBox` data contracts.
- Alternatives: Tightly couple OpenCV window drawing inside the detector loop.
- Consequences: Vision pipeline components are testable, reusable in background tasks, and ready for Tracker integration in Phase 2.

### ADR-007: ByteTrack Multi-Object Tracking Integration
- Status: Accepted
- Date: 2026-10-10
- Context: Phase 2 requires tracking objects across consecutive frames with track IDs, handling occlusions, missing IDs, and tracker resets cleanly.
- Decision: Integrate ByteTrack via Ultralytics with `bytetrack.yaml` and `lapx`; encapsulate tracking in `ByteTrackerAdapter` and `DetectionPipeline`; extend `Detection` schema with optional `track_id`; display `#<id>` in `FrameAnnotator`; provide Google Colab notebook for GPU benchmarking.
- Alternatives: Implement custom SORT tracker or deep appearance ReID model.
- Consequences: Lightweight CPU-compatible multi-object tracking; track IDs are scoped to the continuous video stream session and reset on stream restart.

### ADR-008: Deterministic Rule Engine and Domain Event Model
- Status: Accepted
- Date: 2026-10-10
- Context: Phase 3 requires evaluating tracked/detected objects against spatial rules (e.g. restricted zones), preventing duplicate event floods while an object remains inside, handling tracking dropouts, track expiry, and untracked detections gracefully, and producing structured domain event payloads adhering to the project event contract.
- Decision: Implement a modular `rules` package (`geometry`, `schemas`, `restricted_zone`, `engine`). Use ray-casting point-in-polygon with deterministic boundary inclusion; track object spatial states (`ZoneState`: OUTSIDE, INSIDE, UNKNOWN); trigger `restricted_zone_intrusion` events exclusively on OUTSIDE -> INSIDE state transitions; implement re-entry cooldowns (default 5.0s), track expiry (default 2.0s), and untracked fallback spatial debouncing; encapsulate rules in `RuleEngine` loadable from JSON config (`configs/rules.json`); integrate seamlessly with `DetectionPipeline` and `FrameAnnotator` without breaking Phase 1 or Phase 2 APIs.
- Alternatives Considered: Hardcode zone coordinates in the pipeline loop; re-evaluate events on every frame without state tracking; use external GIS dependencies (e.g. Shapely).
- Consequences: Lightweight zero-extra-dependency implementation; 100% deterministic, testable in isolation from neural networks or video inputs; contracts match downstream Phase 4 FastAPI/SQLite schemas.

### ADR-009: SQLite Event Persistence and Decoupled FastAPI Backend
- Status: Accepted
- Date: 2026-10-10
- Context: Phase 4 requires persisting detected domain events so they survive restarts, providing HTTP endpoints for service health, pipeline runtime status, and paginated event history, streaming live events over WebSockets, and keeping heavy computer vision inference decoupled from API request handlers.
- Decision: Implement the `backend/app` package using FastAPI, Pydantic, and SQLite. Store event metadata in SQLite with `EventRepository` supporting cursor-based pagination, event type / camera filters, and WAL mode; manage live WebSocket clients with `EventPublisher` guaranteeing that subscriber disconnects do not crash publishing; orchestrate event recording through `EventService`; manage video inference in a dedicated background daemon thread via `PipelineService`; add `--db` persistence flag to `main.py` CLI; standardize error responses to `{"error": {"code": "...", "message": "..."}}` adhering to `05_API_SPECIFICATION.md`.
- Alternatives Considered: Run inference synchronously inside FastAPI route handlers (rejected: blocks event loop and introduces high request latency); use heavyweight ORMs like SQLAlchemy (rejected: adds unnecessary dependencies; standard library `sqlite3` provides fast, clean, zero-dependency storage).
- Consequences: Clear separation of computer vision processing and HTTP services; events survive application restarts; fully compatible with downstream Phase 5 React dashboard.

### ADR-010: React Dashboard Architecture and Event Stream Reconciliation
- Status: Accepted
- Date: 2026-10-10
- Context: Phase 5 requires a responsive monitoring interface that connects to the Phase 4 FastAPI REST endpoints and WebSocket stream, visualizes pipeline runtime status, presents live and historical security events, handles disconnections and re-connections gracefully without duplicating events, and honors ADR-005 (event metadata and spatial bounding boxes rather than raw frame streaming).
- Decision: Implement the frontend using React 18, TypeScript, Vite, and Tailwind CSS.
  - Implement structured API clients (`apiClient`, `statusApi`, `eventsApi`) with custom `ApiError` mapping to backend standardized error envelopes (`05_API_SPECIFICATION.md`).
  - Implement `useEventStream` with bounded exponential backoff (`1s -> 2s -> 4s -> 10s max`) and reconnection reconciliation hook.
  - Implement `useEventHistory` with $O(1)$ `event_id` deduplication across historical fetches and live WebSocket streams; upon socket reconnection, trigger reconciliation queries to recover missed events without duplicating visible cards.
  - Implement `CameraPreviewPlaceholder` rendering spatial HUD telemetry, active target restricted zone boundaries, and real-time bounding box overlays `[x1, y1, x2, y2]`, with clear architecture notes explaining ADR-005.
  - Build UI with robust loading skeletons, empty state placeholders, error alert banners with retry actions, and filter controls.
- Alternatives Considered: Relay raw MJPEG or canvas video frames through WebSocket (rejected: violates ADR-005 and bloats backend event stream); use third-party heavyweight state managers like Redux (rejected: custom React hooks provide clean, zero-dependency, testable state management).
- Consequences: Lightweight, fast-loading, responsive dashboard; resilient to backend restarts and network dropouts; fully tested with Vitest and React Testing Library.

## Changelog
### Phase 5 — Dashboard (2026-10-10)
- Initialized React application with Vite, TypeScript, and Tailwind CSS in `frontend/`.
- Created standardized TypeScript types (`types/status.ts`, `types/events.ts`, `types/api.ts`) conforming to backend Pydantic schemas.
- Implemented HTTP API client (`api/client.ts`, `api/statusApi.ts`, `api/eventsApi.ts`) with robust error handling mapping to backend `ErrorResponse` contracts.
- Implemented `useSystemStatus` hook for periodic polling and telemetry updates from `GET /api/status`.
- Implemented `useEventStream` hook subscribing to `WS /api/events/stream` with bounded backoff reconnection and reconnect notification.
- Implemented `useEventHistory` hook with strict `event_id` deduplication, cursor-based pagination (`next_cursor`), filter support (`event_type`, `camera_id`), and historical reconciliation on reconnect.
- Built UI components:
  - `Header`: System branding, real-time clock, WebSocket connection status pill, manual refresh trigger.
  - `ConnectionBadge`: Visual indicators for `Connected`, `Connecting`, `Reconnecting`, and `Disconnected` states with manual reconnect button.
  - `SystemStatusCard`: Pipeline status badge (`RUNNING`, `IDLE`, `FAILED`), camera identifier, source type, YOLO model readiness, ByteTrack mode, and heartbeat timestamps.
  - `CameraPreviewPlaceholder`: Spatial surveillance HUD rendering zone boundaries, live event bounding box coordinates, and ADR-005 architectural notice.
  - `EventFilters`: Filter by event type and camera source, with active event counter and filter reset.
  - `EventCard`: Structured display of timestamp, zone ID, object class, track ID, confidence score, bounding box, and event ID with live highlight animation.
  - `EventList`: Skeletons for loading state, empty state placeholder, list of cards, and cursor pagination button.
  - `ErrorBanner`: Contextual API communication error banner with error code pill and retry trigger.
- Added comprehensive frontend test suite with Vitest and React Testing Library (18 tests passing across components, hooks, and API clients).
- Verified production build (`tsc && vite build`) and updated setup instructions in `README.md`.

### Phase 4 — Persistence and Backend (2026-10-10)
- Defined Pydantic schemas (`EventResponse`, `EventListResponse`, `EventStreamMessage`, `HealthResponse`, `RuntimeStatusResponse`, `ErrorResponse`) adhering to `03_WORKFLOW_AND_DATA_CONTRACTS.md` and `05_API_SPECIFICATION.md`.
- Implemented `EventRepository` using SQLite with WAL mode, parameterized queries, indexes on `occurred_at`, `camera_id`, and `event_type`, and cursor-based pagination (`limit`, `before`).
- Implemented `EventPublisher` with thread-safe WebSocket subscriber management and safe client disconnect handling.
- Implemented `EventService` coordinating persistence and WebSocket event dispatching.
- Implemented `PipelineService` decoupling heavy YOLO inference into a background worker thread and tracking runtime status telemetry.
- Implemented FastAPI REST and WebSocket routes:
  - `GET /api/health`: Health status.
  - `GET /api/status`: Runtime pipeline and video source telemetry.
  - `GET /api/events`: Paginated event history with filtering and validation error handling.
  - `WS /api/events/stream`: Live event stream broadcast.
- Integrated SQLite persistence with root CLI (`main.py --db data/events.db`).
- Added 31 new automated unit and integration tests across schemas, repository, REST endpoints, WebSockets, background pipeline lifecycle, and CLI persistence (total test suite: 83 passing tests).

### Phase 3 — Event Engine (2026-10-10)
- Implemented `rules.geometry` module with `Point`, `Polygon` (supporting normalized and pixel coordinates), ray-casting point-in-polygon algorithm with boundary inclusive policy, and reference point extraction (`bottom_center`, `center`, `bottom_left`, `bottom_right`).
- Implemented `rules.schemas` with `ZoneState` enum and `DomainEvent` contract matching `03_WORKFLOW_AND_DATA_CONTRACTS.md` (UTC ISO-8601 timestamps, UUID identifiers, bounding box, confidence, camera ID, zone ID, and track ID).
- Implemented `RestrictedZoneRule` with per-track outside -> inside state machine, duplicate suppression, exit & re-entry cooldowns, track expiry handling for lost tracks, and untracked detection fallback.
- Implemented `RuleEngine` orchestrator supporting multiple rules, event listener dispatch, in-memory event history, and JSON configuration loader (`from_config_file`).
- Created default zone configuration in `configs/rules.json`.
- Integrated `RuleEngine` with `DetectionPipeline`, supporting backward-compatible 3-tuple return and optional 4-tuple with triggered events (`return_events=True`).
- Enhanced `FrameAnnotator` to render zone polygon overlays (semi-transparent fill with active intrusion highlights) and alert count badge in the telemetry HUD.
- Extended `main.py` CLI with `--rules` option, immediate console event alerts (`[EVENT] 🚨 ...`), and Phase 3 run summary metrics.
- Added comprehensive unit and integration tests (22 new tests across geometry, schemas, zone rules, rule engine, pipeline integration, and CLI; total test suite: 52 passing tests).

### Phase 2 — Multi-Object Tracking (2026-10-10)
- Integrated Ultralytics YOLO tracking with ByteTrack (`bytetrack.yaml`) using `lapx` solver.
- Extended `Detection` and `Track` schemas with optional `track_id` while maintaining 100% backward compatibility.
- Implemented `ByteTrackerAdapter` with tracker configuration validation and safe state resets.
- Added `track()` and `reset_tracker()` methods to `YOLODetector` with robust tensor and sequence parsing.
- Enhanced `FrameAnnotator` to display track IDs (`#<track_id>`), consistent track-based colors, and active track counts.
- Updated `DetectionPipeline` with `enable_tracking` toggle and `reset_tracker()` lifecycle handling.
- Updated `main.py` CLI with `--track / --no-track` and `--tracker` arguments.
- Added standalone Google Colab notebook `notebooks/LiveSight_Phase2_GPU_Tracking.ipynb` for cloud GPU experiments.
- Created `configs/bytetrack.yaml` for local tracker configuration.
- Added comprehensive unit and integration tests (30 passing tests).

### Phase 1 — Standalone Object Detection (2026-10-10)
- Configured clean Python 3.10 virtual environment with `requirements.txt` and `.gitignore`.
- Implemented `VideoSource` supporting webcams and local video files with actionable error reporting.
- Implemented `YOLODetector` using Ultralytics YOLO with detection normalization.
- Implemented `FrameAnnotator` with high-contrast bounding boxes, labels, confidence scores, and diagnostic HUD.
- Implemented `DetectionPipeline` with rolling FPS diagnostics.
- Implemented `main.py` CLI supporting webcam index, local video paths, `--headless` execution, and video recording.
- Created 17 unit and integration tests across schemas, video source, detector, pipeline, and CLI.
- Added comprehensive root `README.md` and sample video generation helper `scripts/create_sample_video.py`.

### Unreleased
- Initial documentation pack created.
- Initial scope defined as local-first object detection, tracking, restricted-zone event rules, API, persistence, and dashboard.
- Performance claims remain targets until benchmarked.


