# Product Requirements Document (PRD)

## 1. Summary
Build a local-first application that analyzes live or recorded video, detects objects, tracks them across frames, applies configurable rules, and presents meaningful events to an operator.

## 2. Problem
Manual video monitoring is labor-intensive. A detection-only demo can identify objects in individual frames but does not provide an integrated workflow for tracking, event generation, history, and operator notification. The application aims to turn raw video into structured, reviewable events.

## 3. Goals
- Run a working end-to-end prototype on a developer laptop.
- Detect supported object classes using a pretrained model.
- Track objects across frames using a supported tracking algorithm.
- Generate deterministic events from detections and tracks.
- Provide a backend API and persistent event history.
- Display live status and events in a web dashboard.
- Make performance measurable rather than relying on unverified claims.
- Keep modules replaceable so hardware-specific optimization can be added later.

## 4. Non-goals for the initial MVP
- Guaranteed identification of a real-world person.
- Face recognition or biometric identification.
- Guaranteed sub-second push notifications.
- Production-grade multi-tenant security.
- Automatic bypassing of website, device, or network restrictions.
- Jetson/TensorRT deployment before the local pipeline is validated.
- Training a custom detector before pretrained inference is working.
- Full mobile application in the first milestone.

## 5. Primary users
### Operator
Wants to see the current video, tracked objects, and actionable events.

### Developer / maintainer
Wants reproducible setup, logs, tests, and clear module boundaries.

## 6. MVP user stories
- As a developer, I can choose a webcam or video file as the input.
- As an operator, I can see detected objects and their confidence scores.
- As an operator, I can see track IDs when tracking is enabled.
- As an operator, I can configure a restricted polygon zone.
- As an operator, I receive one event when the rule's trigger conditions are met.
- As an operator, I can view recent events and their timestamps.
- As a developer, I can run tests without requiring a physical camera.
- As a maintainer, I can inspect logs when a camera or model fails.

## 7. Functional requirements
### FR-01 Video input
Support one video source at a time in the first milestone: webcam index or local video file. Handle source-open failure and end-of-file cleanly.

### FR-02 Detection
Run a pretrained detector and produce class, confidence, and bounding-box coordinates for each accepted detection. Model and confidence threshold must be configurable.

### FR-03 Tracking
Allow tracking to be enabled and produce a track identifier where the tracker provides one. Track IDs are temporary tracker identities, not proof of a person's real-world identity.

### FR-04 Event rules
Support a deterministic restricted-zone rule. Define the reference point used for zone membership, such as the bottom-center of the bounding box. Make this explicit and configurable if needed.

### FR-05 Alert deduplication
Avoid producing a new alert for every frame while the same tracked object remains in the zone. Use a documented state transition or cooldown policy.

### FR-06 Persistence
Store event ID, camera/source ID, event type, object class, track ID when available, event timestamp, confidence, zone ID, and optional snapshot path.

### FR-07 Backend
Expose health, event history, and live event updates. Validate request and response schemas.

### FR-08 Dashboard
Show service status, video/detection view where applicable, latest events, and event history. Display connection errors and reconnection state.

### FR-09 Configuration
Keep runtime settings outside source code where practical. Provide `.env.example`; never commit secrets.

### FR-10 Observability
Log startup, source failures, model load failures, event creation, persistence failures, and client connection lifecycle.

## 8. Non-functional requirements
- **Reliability:** failures should be visible and should not silently terminate the application.
- **Maintainability:** detection, tracking, rules, persistence, API, and UI should have clear responsibilities.
- **Portability:** local CPU execution should be the baseline; accelerator use is optional.
- **Performance:** record FPS, processing latency, and event latency on the target machine.
- **Privacy:** use test videos or authorized camera feeds; minimize stored video and protect event access.
- **Testability:** core rule logic must be testable without webcam hardware or model downloads.

## 9. Success criteria for the local MVP
- A sample video can be processed from beginning to end.
- Detection overlays are visible.
- Track IDs are shown when tracking is enabled.
- A synthetic or real test track entering a configured zone produces the expected event.
- The same track does not generate one event per frame.
- Events are persisted and returned by the API.
- A connected dashboard receives live event updates.
- Automated tests cover zone geometry, rule transitions, schemas, and API behavior.
- A benchmark report records hardware, model, input resolution, average FPS, and latency.

## 10. Metrics to measure
- Detection precision/recall on a labeled evaluation set, if available.
- Tracking identity switches or a suitable tracking metric, if a labeled dataset is available.
- Average and percentile frame processing latency.
- Average FPS over a defined clip.
- Event-generation latency from rule trigger to backend event.
- WebSocket delivery latency on the local network.
- CPU, memory, and accelerator utilization where available.

Do not state a percentage or FPS result in a résumé or report unless it was measured using a documented test setup.

## 11. Assumptions and risks
- A pretrained model can be downloaded and run on the target machine.
- Available video quality and lighting affect detection quality.
- Occlusion and similar-looking objects can cause tracking ID switches.
- Camera and network streams may fail or have variable latency.
- The chosen model and its license must be reviewed before redistribution or commercial use.
- Privacy, consent, and local law must be considered before using real surveillance footage.

## 12. Open questions
- Which OS and hardware will be the baseline?
- Is the first input a webcam or prerecorded video?
- Which classes matter for the first demo?
- Should zone membership use box center, bottom-center, or segmentation mask?
- What is the alert re-trigger policy after an object exits and re-enters?
