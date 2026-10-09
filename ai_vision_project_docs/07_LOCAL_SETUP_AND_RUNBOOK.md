# Local Setup and Runbook

## 1. Prerequisites
- Python version supported by the selected computer-vision packages.
- Git.
- Node.js LTS and npm for the frontend phase.
- Webcam or sample video.
- Internet access for initial package/model downloads.
- Enough disk space for model weights and test clips.

Hardware acceleration is optional. Start with a small pretrained model and benchmark the machine.

## 2. Initial Python environment
From the repository root:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install ultralytics opencv-python fastapi "uvicorn[standard]" pydantic
```
Pin tested versions in a dependency file after the first successful setup. The exact package versions may need adjustment for the machine and Python version.

Windows activation:
```powershell
.venv\\Scripts\\Activate.ps1
```

## 3. First computer-vision smoke test
Create a minimal detection script using OpenCV and the selected Ultralytics YOLO model. Begin with a local video file if webcam permissions or camera availability are uncertain.

Basic checks:
- Can OpenCV open the source?
- Can the model load?
- Does inference return detections?
- Can an annotated frame be displayed?
- Does pressing the quit key release resources?

## 4. Configuration
Use environment variables or a validated settings file. Suggested `.env.example`:
```dotenv
APP_ENV=development
API_HOST=127.0.0.1
API_PORT=8000
VIDEO_SOURCE=0
MODEL_NAME=yolo11n.pt
CONFIDENCE_THRESHOLD=0.35
TRACKING_ENABLED=true
DATABASE_URL=sqlite:///./data/events.db
LOG_LEVEL=INFO
```
This is an illustrative starting configuration. Confirm model names and supported settings in the installed library. Never commit secrets or production credentials.

## 5. Running services (target state)
Backend:
```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
The import path must match the final repository layout.

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Vision pipeline:
- During the earliest phase, run the detection script directly.
- Later, start it as a managed background service through the application lifecycle.
- Avoid running two processes against the same camera unless the device supports it.

## 6. Common issues
### Webcam cannot open
- Check OS camera permission for the terminal/IDE.
- Close other applications using the webcam.
- Try another camera index.
- Test a local video file to isolate camera issues.

### Model download/load fails
- Check network access and disk space.
- Verify the model identifier and package compatibility.
- Download weights only from trusted sources and review the model license.

### Slow inference
- Record a baseline before optimizing.
- Try a smaller model or smaller inference image size.
- Reduce unnecessary display/render work.
- Do not assume GPU acceleration is active; inspect actual device behavior.

### No track IDs
- Confirm tracking rather than detection-only inference is enabled.
- Check tracker configuration and installed package version.
- Track IDs may be absent for some detections or change after tracker reset.

### CORS errors
- Configure the backend to allow the exact local frontend origin during development.
- Do not use permissive wildcard CORS with credentials in production.

### WebSocket repeatedly disconnects
- Inspect backend logs and browser network tools.
- Verify URL scheme/port and proxy settings.
- Implement client reconnect with bounded backoff.
- Fetch event history after reconnect if missed events matter.

### Database path fails
- Ensure the parent directory exists and the process has write permission.
- Use a stable path outside temporary directories.
- Back up the database before schema migrations.

## 7. Shutdown and cleanup
- Stop pipeline workers before closing the database.
- Release camera/video resources.
- Close WebSocket connections.
- Ensure background tasks are cancelled or joined cleanly.
- Avoid deleting test data until needed logs/results have been saved.
