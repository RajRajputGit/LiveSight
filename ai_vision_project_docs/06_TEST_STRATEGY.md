# Test Strategy

## 1. Testing goals
Verify correctness independently of model accuracy, then test the complete system using repeatable video fixtures. Separate functional correctness from performance measurement.

## 2. Test levels
### Unit tests
No webcam, network, or model download required.
- Point-in-polygon geometry.
- Bounding-box reference point calculation.
- Zone state transitions.
- Duplicate suppression and track expiry.
- Event schema validation.
- Event serialization and timestamp normalization.
- Repository mapping where practical.

### Integration tests
- API plus temporary SQLite database.
- Event creation persists expected fields.
- REST history returns saved events.
- WebSocket publisher delivers an event to a test client.
- Invalid settings fail clearly.

### End-to-end tests
- Process a short, authorized sample video.
- Verify the pipeline finishes without crashing.
- Verify detections are produced when expected.
- Use a deterministic test double for rule-event tests when model output would make tests flaky.
- Confirm the dashboard displays a seeded event and receives a live test event.

### Manual tests
- Webcam permission denied.
- Video file missing.
- End-of-file reached.
- Model weights unavailable.
- Backend restarted while dashboard is open.
- WebSocket disconnected and reconnected.
- Lighting, motion blur, occlusion, and crowded scenes.

## 3. Example test cases
| ID | Scenario | Expected result |
|---|---|---|
| T-01 | Valid frame with a visible person | Detector may return person detection above threshold |
| T-02 | Confidence below threshold | Detection is filtered according to configuration |
| T-03 | Track outside zone | No intrusion event |
| T-04 | Track enters zone | One intrusion event |
| T-05 | Track remains inside for many frames | No per-frame duplicate event |
| T-06 | Track exits then re-enters | Behavior follows documented re-entry policy |
| T-07 | Track ID is missing | Rule follows defined fallback; no crash |
| T-08 | Video source cannot open | Clear error/status; resources cleaned up |
| T-09 | Database write fails | Error is logged and surfaced |
| T-10 | WebSocket client disconnects | Publisher continues; client can reconnect |
| T-11 | Duplicate event arrives at frontend | UI deduplicates by event ID |
| T-12 | Empty event history | API/UI return a valid empty state |
| T-13 | Invalid zone polygon | Configuration validation rejects it |
| T-14 | Frame resolution changes | Zone coordinates remain correct or change is rejected explicitly |

## 4. Performance test protocol
Use the same clip and settings for comparisons:
1. Record machine model, OS, CPU, RAM, accelerator, and power mode if relevant.
2. Record model name/version, image size, confidence threshold, tracker, and video FPS/resolution.
3. Warm up the model before measurement.
4. Measure a fixed duration or full clip.
5. Report average FPS and processing latency; include p50/p95 latency if feasible.
6. Measure event latency separately from frame inference latency.
7. Repeat runs and record variation.
8. Save results to `docs/benchmark-results.md`.

Never compare FPS figures unless the model, resolution, hardware, and measurement procedure are sufficiently similar.

## 5. Quality gates
Before merging a change:
- [ ] Code imports and starts.
- [ ] Formatter/linter pass if configured.
- [ ] Relevant unit tests pass.
- [ ] Integration tests pass for API/repository changes.
- [ ] Manual smoke test completed for user-visible changes.
- [ ] Docs and examples match implementation.
- [ ] No secrets or private video files were committed.

## 6. Dataset and privacy
- Use public datasets only according to their licenses, or footage you are authorized to process.
- Avoid collecting unnecessary identifiable footage.
- Do not add face recognition to the MVP.
- Document retention and deletion behavior if storing snapshots or clips.
