# Deployment and Operations

## 1. Deployment stages
### Stage A: Local development
All services run on one developer machine. Use test videos, local SQLite, and development-only settings.

### Stage B: Reproducible local deployment
Containerize backend and frontend where useful. Persist database data in a volume. Keep model weights and large videos outside the image where practical.

### Stage C: Single edge device
Run inference near the camera. Test device compatibility, thermal behavior, sustained performance, camera connectivity, and recovery after restart.

### Stage D: Edge plus cloud
Edge devices process video and send event metadata or selected media to a central service. Add authentication, encrypted transport, device identity, monitoring, and controlled software updates.

## 2. Docker principles
- Use a pinned base image and pinned dependencies.
- Run as a non-root user where practical.
- Use health checks.
- Keep secrets out of image layers.
- Persist database data.
- Avoid mounting the host camera into containers until permissions and device paths are understood.
- Hardware acceleration requires platform-specific configuration; a generic Dockerfile does not guarantee GPU access.

## 3. Configuration by environment
Keep development, test, and production settings separate:
- `development`: reload and verbose logs allowed.
- `test`: temporary database and deterministic fixtures.
- `production`: no debug mode, restricted CORS, authentication, durable storage, managed secrets, and appropriate logging.

## 4. Observability
Track:
- Pipeline state and last successful frame time.
- Source reconnects and errors.
- Frame processing latency and FPS.
- Detection count and event count.
- Database write failures.
- WebSocket client count and disconnects.
- Memory/CPU/GPU use where available.
- Model/version/configuration used by each benchmark or deployment.

Do not log raw video, credentials, or unnecessary personal data.

## 5. Security checklist
- [ ] Bind development services to localhost by default.
- [ ] Add authentication before exposing the service to a network.
- [ ] Authorize event history and camera controls.
- [ ] Validate source paths and configuration.
- [ ] Restrict file upload types and size if uploads are added.
- [ ] Use HTTPS/WSS outside local development.
- [ ] Protect snapshots and video with access controls.
- [ ] Set retention/deletion policy.
- [ ] Keep dependencies updated.
- [ ] Review model and dataset licenses.
- [ ] Avoid exposing remote device-control endpoints without authentication and audit logging.

## 6. Edge optimization path
1. Benchmark baseline inference.
2. Choose model size and image resolution based on required accuracy and latency.
3. Profile the full pipeline, not just model inference.
4. Evaluate ONNX or other supported export paths.
5. On compatible NVIDIA hardware, evaluate TensorRT and validate output parity.
6. Test multiple streams and resource contention.
7. Measure sustained operation, not only a short demo.
8. Document rollback to a known-good model/runtime.

## 7. Operations and recovery
- Restart policy should distinguish recoverable source failures from fatal model/configuration failures.
- Avoid endless tight retry loops; use backoff.
- Make readiness distinct from process liveness.
- Keep a known-good release/model configuration.
- Back up event metadata if it matters.
- Record deployment version and configuration so failures can be reproduced.

## 8. Release checklist
- [ ] Automated tests pass.
- [ ] Benchmark is recorded for the target hardware.
- [ ] Configuration and migrations are reviewed.
- [ ] Logs are actionable and contain no secrets.
- [ ] Authentication and network exposure are reviewed.
- [ ] Data retention and privacy are documented.
- [ ] Startup, shutdown, and restart have been tested.
- [ ] Rollback plan exists.
