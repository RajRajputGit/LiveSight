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

## Changelog
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

