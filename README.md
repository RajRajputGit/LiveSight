# LiveSight: Real-Time AI Object Detection, Tracking & Event Engine

**LiveSight** is a modular, local-first computer vision and monitoring application built with OpenCV, Ultralytics YOLO, ByteTrack, and FastAPI.

- **Phase 1**: Standalone Real-Time YOLO Object Detection.
- **Phase 2**: Multi-Object Tracking with **ByteTrack** (`bytetrack.yaml`).
- **Phase 3**: Rule-Based **Event Engine** for spatial zone monitoring (`rules.json`).
- **Phase 4**: **Persistence & Backend API** with SQLite, FastAPI, and WebSockets.

---

## 📌 Features Overview

- **Object Detection & Tracking**: Runs pretrained YOLO models (e.g. `yolo11n.pt`) with ByteTrack for persistent multi-object tracking.
- **Rule-Based Event Engine**: Deterministic spatial reasoning using ray-casting point-in-polygon algorithms to detect restricted zone entries.
- **Intelligent Alert Deduplication**: Evaluates `outside -> inside` state transitions; suppresses redundant alerts while an object stays inside a zone.
- **Cooldowns & Track Expiry**: Configurable re-entry cooldowns (e.g. 5s) and track expiry handling (e.g. 2s) for occluded or re-acquired tracks.
- **SQLite Persistence**: Stores structured domain events with indexes on timestamp, camera, and event type. Events survive service restarts.
- **FastAPI REST & WebSocket Backend**:
  - `GET /api/health`: Health status endpoint.
  - `GET /api/status`: Real-time pipeline, model, and source telemetry.
  - `GET /api/events`: Paginated event history with filtering by camera and event type.
  - `WS /api/events/stream`: Live event stream broadcast to connected subscribers.
- **Decoupled Architecture**: Inference executes in a managed background worker thread, completely independent of HTTP request handling.
- **Visual Overlays & Zone Rendering**: Displays semi-transparent polygon zones (highlighting red upon intrusion), bounding boxes, class labels, unique track IDs (e.g. `#3 person 0.88`), and a telemetry HUD (FPS, detections, active tracks, total alerts).
- **Track Consistency**: Uses deterministic colors per track ID so objects retain consistent colors across frames.
- **Safe Tracker Lifecycle**: Safely handles unassigned / missing track IDs and resets tracker state on stream restarts or loops.
- **Flexible Video Sources**: Supports webcam devices (by index: `0`, `1`), local video files (`.mp4`, `.avi`, `.mov`), or generated test clips.
- **Backward-Compatible & Configurable**: Toggle tracking on or off (`--track` vs `--no-track`), configure rules (`--rules configs/rules.json`), specify SQLite persistence (`--db data/events.db`), or run headless (`--headless`).
- **CPU & GPU Ready**: Runs locally on CPU/Metal without GPU dependencies, with a dedicated **Google Colab Notebook** provided for cloud GPU experiments.

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- **Python**: Python 3.10 or higher.
- **OS**: macOS, Linux, or Windows.
- **Hardware**: Standard CPU, Apple Silicon Metal (`mps`), or NVIDIA CUDA GPU.

### 2. Environment Setup

From the repository root:

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🎬 Running Detection, Tracking, and Rules

### A. Run with Webcam and Default Zone Rules
```bash
python main.py --source 0 --rules configs/rules.json
```
> **macOS Note**: When running for the first time, grant camera permission in *System Settings -> Privacy & Security -> Camera*.

### B. Run with a Local Video File and Event Engine
```bash
python main.py --source video/gettyimages-1206324549-640_adpp.mp4 --rules configs/rules.json
```

### C. Run Pure Detection Mode (Phase 1 Compatibility)
To disable tracking and rules:
```bash
python main.py --source data/sample_demo.mp4 --no-track --rules ""
```

### D. Run with Custom ByteTrack Configuration
```bash
python main.py --source data/sample_demo.mp4 --tracker configs/bytetrack.yaml
```

### E. Run Built-in Sample Video Demo
```bash
# 1. Generate test video
python scripts/create_sample_video.py

# 2. Run tracking and zone monitoring on sample video
python main.py --source data/sample_demo.mp4 --rules configs/rules.json
```

### F. Save Annotated Output Video
```bash
python main.py --source video/gettyimages-1206324549-640_adpp.mp4 --rules configs/rules.json --output data/annotated_output.mp4
```

### G. Run Headless (No GUI Window)
```bash
python main.py --source video/gettyimages-1206324549-640_adpp.mp4 --rules configs/rules.json --headless --max-frames 60
```

---

## ⚙️ Command-Line Arguments Reference

| Flag | Short | Default | Description |
|---|---|---|---|
| `--source` | `-s` | `0` | Camera device index (`0`, `1`) or path to local video file. |
| `--model` | `-m` | `yolo11n.pt` | Model name or path (`yolo11n.pt`, `yolov8n.pt`, etc.). |
| `--conf` | `-c` | `0.35` | Confidence score threshold (0.0 to 1.0). |
| `--track` / `--no-track` | | `True` | Enable or disable ByteTrack multi-object tracking. |
| `--tracker` | | `bytetrack.yaml` | Tracker config identifier or YAML file path (`configs/bytetrack.yaml`). |
| `--rules` | `-r` | `configs/rules.json` | Path to JSON zone rules configuration file. Set to `""` to disable rules. |
| `--db` | | `data/events.db` | Path to SQLite database to persist detected domain events. Set to `""` to disable. |
| `--device` | | `None` | Compute device (`cpu`, `mps`, `cuda:0`). PyTorch auto-selects if omitted. |
| `--headless` | | `False` | Run without opening an OpenCV GUI preview window. |
| `--output` | `-o` | `None` | Path to save annotated output video (`.mp4`). |
| `--max-frames` | | `None` | Maximum number of frames to process before exiting cleanly. |

---

## 🌐 Phase 4 Backend API & SQLite Persistence

LiveSight Phase 4 introduces a local FastAPI backend, SQLite event repository, and WebSocket event publisher.

### 1. Launching the Backend Server

Start the API with Uvicorn:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive Swagger API documentation is available at: **`http://127.0.0.1:8000/docs`**.

### 2. Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Process health check (`{"status": "ok", "service": "ai-vision-backend"}`). |
| `GET` | `/api/status` | Runtime status of video source, pipeline, model, tracking, and last frame timestamp. |
| `GET` | `/api/events` | Paginated domain event history (`limit`, `before`, `event_type`, `camera_id`). |
| `WS` | `/api/events/stream` | Real-time WebSocket event stream (`{"type": "event.created", "data": {...}}`). |

### 3. Example API Queries

```bash
# Health check
curl http://127.0.0.1:8000/api/health

# Runtime pipeline telemetry
curl http://127.0.0.1:8000/api/status

# Retrieve recent events (default limit: 50, max: 100)
curl "http://127.0.0.1:8000/api/events?limit=10"

# Filter by camera and event type with pagination cursor
curl "http://127.0.0.1:8000/api/events?camera_id=cam_01&event_type=restricted_zone_intrusion&before=2026-10-10T12:00:00.000Z"
```

### 4. Background Vision Inference

In accordance with Phase 4 architecture, computer vision inference executes in a managed background worker thread, completely isolated from HTTP request lifecycle handlers. Set `START_PIPELINE_ON_STARTUP=true` in environment or launch via `PipelineService`.

---

## 🛡️ Phase 3 Event Engine & Spatial Rule Evaluation

LiveSight Phase 3 evaluates object positions against configurable spatial polygons in real time using a deterministic ray-casting algorithm.

### Zone State Machine & Duplicate Prevention
- **State Transition Rule**: An alert (`restricted_zone_intrusion`) is triggered **only** when an object's spatial state transitions from `OUTSIDE` to `INSIDE`.
- **Duplicate Suppression**: While an object remains `INSIDE` across consecutive frames, no repeat alerts are fired.
- **Cooldown on Re-entry**: After an object exits (`INSIDE -> OUTSIDE`), a cooldown timer (`cooldown_seconds`, default 5.0s) prevents jitter or momentary border-crossing from flooding alerts.
- **Track Expiry & Occlusion Recovery**: Lost tracks are held for `track_expiry_seconds` (default 2.0s). If reacquired, state continuity is preserved.
- **Untracked Fallback**: If an object detection lacks a track ID or tracking is disabled, a spatial debouncer prevents frame-by-frame spam.

### Zone Configuration (`configs/rules.json`)
Coordinates can be specified in normalized values (`0.0` to `1.0`) so zones scale automatically to any camera resolution:
```json
{
  "zones": [
    {
      "zone_id": "restricted_zone_A",
      "name": "Restricted Area A",
      "target_classes": ["person"],
      "reference_point": "bottom_center",
      "cooldown_seconds": 5.0,
      "track_expiry_seconds": 2.0,
      "reacquire_generates_alert": false,
      "allow_untracked_events": true,
      "untracked_cooldown_seconds": 5.0,
      "min_confidence": 0.35,
      "polygon": [
        [0.20, 0.20],
        [0.80, 0.20],
        [0.80, 0.80],
        [0.20, 0.80]
      ]
    }
  ]
}
```

---

## ☁️ Google Colab GPU Experiments

Since local development may lack a dedicated GPU, a standalone Google Colab notebook is included:

📓 **[`notebooks/LiveSight_Phase2_GPU_Tracking.ipynb`](notebooks/LiveSight_Phase2_GPU_Tracking.ipynb)**

### Features of the Colab Notebook:
- Enables NVIDIA GPU acceleration (`T4` / `V100` / `A100`).
- Demonstrates ByteTrack tracking with `device="cuda:0"`.
- Measures GPU inference latency and throughput (FPS).
- Displays animated HTML5 video playback inline inside Colab.

---

## 🧠 Track ID Behavior & Known Limitations

Following [`ai_vision_project_docs/02_SYSTEM_ARCHITECTURE.md`](ai_vision_project_docs/02_SYSTEM_ARCHITECTURE.md):

1. **Scoped to Stream Session**: A track ID is ephemeral and valid only within the current stream session. It is not a permanent identity.
2. **Stream Restarts & Resets**: When a video source restarts or loops, `pipeline.reset_tracker()` clears existing tracks and resets the ID counter to avoid stale associations.
3. **Occlusions & Dropouts**: ByteTrack maintains lost tracks for `track_buffer` frames (default: `30` in `configs/bytetrack.yaml`). If an object remains occluded longer than this threshold, it is dropped and assigned a new ID upon reappearance.
4. **Crossing Paths & ID Switches**: Rapid movements or occlusions in dense scenes can occasionally result in ID switches. Tuning `match_thresh` and `track_high_thresh` helps mitigate drift.

---

## 📂 Project Architecture

```text
LiveSight/
├── backend/
│   └── app/
│       ├── __init__.py         # App package init
│       ├── main.py             # FastAPI entry point, lifespan, CORS, and error handlers
│       ├── config.py           # Application settings and environment configuration
│       ├── schemas/            # Pydantic data contract schemas
│       │   ├── event.py        # EventResponse, EventListResponse, EventStreamMessage
│       │   ├── status.py       # HealthResponse, RuntimeStatusResponse
│       │   └── error.py        # Standardized ErrorResponse envelope
│       ├── repositories/       # Persistence layer
│       │   └── event_repository.py # SQLite EventRepository with WAL mode & pagination
│       ├── services/           # Application service layer
│       │   ├── event_service.py    # Event coordination & persistence
│       │   ├── event_publisher.py  # WebSocket client manager & live broadcast
│       │   └── pipeline_service.py # Decoupled background vision runner & telemetry
│       └── api/                # FastAPI route modules
│           ├── routes_health.py    # GET /api/health
│           ├── routes_status.py    # GET /api/status
│           ├── routes_events.py    # GET /api/events (paginated history)
│           └── routes_stream.py    # WS /api/events/stream (live WebSocket)
├── vision/
│   ├── __init__.py         # Vision exports (Schemas, VideoSource, YOLODetector, Tracker, Pipeline)
│   ├── schemas.py          # BoundingBox, Detection (with track_id), Track contract
│   ├── exceptions.py       # VisionError, VideoSourceError, ModelLoadError, TrackerError
│   ├── source.py           # VideoSource adapter (webcam + file capture, safe resource release)
│   ├── detector.py         # YOLODetector (predict and track methods, tracker state reset)
│   ├── tracker.py          # ByteTrackerAdapter (configuration, validation, lifecycle reset)
│   ├── annotator.py        # FrameAnnotator (bounding boxes, track IDs, labels, zone overlays, HUD)
│   ├── pipeline.py         # DetectionPipeline (tracking toggle, rules engine, rolling FPS)
│   └── utils.py            # Utility helpers (synthetic video generator)
├── rules/
│   ├── __init__.py         # Rules package exports (Point, Polygon, DomainEvent, ZoneRule, RuleEngine)
│   ├── geometry.py         # Point, Polygon, ray-casting point-in-polygon, reference points
│   ├── schemas.py          # ZoneState enum and DomainEvent schema contract
│   ├── restricted_zone.py  # RestrictedZoneRule state machine, deduplication, cooldowns, expiry
│   └── engine.py           # RuleEngine orchestrator, event dispatch, config loading
├── configs/
│   ├── bytetrack.yaml      # ByteTrack tracker parameters
│   └── rules.json          # Restricted zone spatial definitions and thresholds
├── notebooks/
│   └── LiveSight_Phase2_GPU_Tracking.ipynb # Google Colab GPU tracking experiments
├── tests/
│   ├── test_schemas.py     # Schema, contract, and track_id validation unit tests
│   ├── test_source.py      # Video source error and reading tests
│   ├── test_detector.py    # Detector loading, inference, and tracking unit tests
│   ├── test_tracker.py     # ByteTrackerAdapter, missing IDs, and reset unit tests
│   ├── test_pipeline.py    # Pipeline and annotator unit tests
│   ├── test_geometry.py    # Point-in-polygon and geometric primitives tests
│   ├── test_rules_schemas.py # DomainEvent schema contract and validation tests
│   ├── test_restricted_zone.py # State machine, duplicate suppression, cooldown, expiry tests
│   ├── test_rule_engine.py # Multi-rule processing, listener dispatch, and config tests
│   ├── test_pipeline_rules_integration.py # Pipeline integration with RuleEngine tests
│   ├── test_backend_schemas.py  # Phase 4 Pydantic backend schemas tests
│   ├── test_event_repository.py # Phase 4 SQLite repository persistence & pagination tests
│   ├── test_backend_api.py      # Phase 4 FastAPI REST endpoints integration tests
│   ├── test_websocket_stream.py # Phase 4 live WebSocket stream broadcast tests
│   ├── test_pipeline_service.py # Phase 4 decoupled background worker tests
│   └── test_cli.py         # main.py CLI integration tests (--track, --tracker, --rules, --db)
├── scripts/
│   └── create_sample_video.py # Helper script to create test video
├── ai_vision_project_docs/ # Architecture and design documentation
├── main.py                 # CLI entry point
├── requirements.txt        # Project dependencies (CV, ByteTrack, FastAPI, Pydantic, Uvicorn)
├── .gitignore              # Git ignore rules
└── README.md               # Setup and usage guide
```

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

All 83 unit and integration tests run entirely locally on CPU without requiring an external camera or GPU.

---

## 🔍 Troubleshooting

### Missing module `lap` / `lapx`
- ByteTrack requires a linear assignment solver (`lapx`).
- Run `pip install lapx>=0.5.5` or `pip install -r requirements.txt`.

### Webcam fails to open (`VideoSourceError`)
1. On macOS, grant camera permission in *System Settings -> Privacy & Security -> Camera*.
2. If index `0` fails, try `--source 1`.
3. Check if other applications (FaceTime, Zoom, browser) are locking the webcam.

### Low FPS / Diagnostic Latency
1. Local execution uses rolling-average frame timing for diagnostic reporting.
2. For high throughput, use a lightweight model like `yolo11n.pt` or run GPU experiments via the included Colab notebook.
