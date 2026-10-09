# Implementation Plan and Milestones

## Working agreement
Build in small vertical slices. Every phase should finish with a runnable demonstration, tests, and an update to the relevant docs. Do not start the next phase while the current phase has unresolved critical failures.

## Phase 0 — Repository and environment
Tasks:
- Create repository and `docs/` folder.
- Create Python virtual environment.
- Add dependency file and `.gitignore`.
- Record OS, CPU, RAM, and optional GPU details.
- Confirm Python and package versions.

Exit criteria:
- Fresh environment can install dependencies.
- No secrets or private footage are committed.
- README setup steps work from a clean checkout.

## Phase 1 — Standalone object detection
Tasks:
- Select a supported pretrained model.
- Load a webcam or sample video with OpenCV.
- Run inference and draw detections.
- Add graceful shutdown and source error handling.
- Print elapsed time/FPS as a diagnostic, not as a benchmark claim.

Exit criteria:
- Sample video processes end-to-end.
- Bounding boxes and labels are visible.
- Source errors are actionable.
- A documented command launches the demo.

## Phase 2 — Object tracking
Tasks:
- Add tracker integration.
- Display track IDs.
- Test crossing paths, short occlusions, missed detections and source restart.
- Document track-ID limitations.

Exit criteria:
- Track IDs appear when the tracker provides them.
- Tracker state resets correctly on source restart.
- Known failure cases are documented.

## Phase 3 — Rule engine
Tasks:
- Implement polygon geometry.
- Add point-in-polygon function.
- Select the reference point for each object.
- Add outside/inside state transitions.
- Add track expiry and duplicate suppression.
- Unit-test rule logic with synthetic tracks.

Exit criteria:
- Tests prove entry triggers once.
- Staying inside does not create duplicate events every frame.
- Exit and re-entry follows the documented policy.
- Geometry handles points on polygon boundaries according to a defined rule.

## Phase 4 — Persistence and backend
Tasks:
- Define Pydantic event schemas.
- Implement SQLite repository.
- Add health/status endpoint.
- Add event history endpoint with pagination.
- Add WebSocket event publisher.
- Keep inference in a background service, not inside API request handlers.

Exit criteria:
- Events survive backend restart.
- API responses match documented schemas.
- WebSocket clients receive new events.
- Database failures are visible in logs.

## Phase 5 — Dashboard
Tasks:
- Initialize React application.
- Add backend API client.
- Build system status and event list.
- Subscribe to WebSocket updates.
- Add reconnect state and historical fetch.
- Add video display/annotated-frame strategy.

Exit criteria:
- Dashboard displays historical and live events.
- Disconnected backend is clearly represented.
- Reconnection does not create duplicate visible events.
- Empty and error states are implemented.

## Phase 6 — Quality and performance
Tasks:
- Add unit, integration and smoke tests.
- Benchmark a fixed video clip and configuration.
- Record model, resolution, hardware, duration, FPS, and latency.
- Profile before changing model size or concurrency.
- Test long-running stability.

Exit criteria:
- Critical rule and API tests pass.
- Benchmark is reproducible.
- No unbounded memory growth is observed in the chosen test duration.
- Performance claims are backed by saved measurements.

## Phase 7 — Optional features
Choose only when justified:
- Multiple simultaneous sources.
- RTSP input.
- Snapshot capture.
- Authentication and authorization.
- Push notifications.
- Docker Compose.
- Cloud event/media storage.
- ONNX or hardware-specific acceleration.
- Edge device management.
- ReID or custom model training.

## Suggested weekly rhythm
1. Select one small task.
2. Define expected behavior and acceptance tests.
3. Implement the smallest solution.
4. Run formatting, linting, and tests.
5. Manually verify the behavior.
6. Update documentation and changelog.
7. Commit a small, meaningful change.

## Task template
```markdown
### Task: [short name]
- Why:
- Scope:
- Out of scope:
- Files/modules:
- Acceptance criteria:
  - [ ] ...
- Tests:
- Risks:
- Documentation to update:
- Status: Planned / In Progress / Blocked / Done
```
