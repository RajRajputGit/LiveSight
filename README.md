# LiveSight: Real-Time AI Object Detection and Monitoring System

Phase 1 implementation: Standalone Real-Time YOLO Object Detection on local video streams and webcams.

---

## 📌 Phase 1 Overview

This phase implements a clean, modular, and beginner-friendly computer vision pipeline that runs pretrained YOLO object detection on video feeds:
- **Input Sources**: Live webcam (by device index, e.g. `0`, `1`) or local video files (`.mp4`, `.avi`, `.mov`).
- **AI Model**: Ultralytics YOLO (`yolo11n.pt` by default, or any supported YOLO model).
- **Visuals**: Draws bounding boxes, class labels, confidence scores, and a diagnostic FPS HUD badge.
- **Graceful Exit**: Press `q` in the video window or press `Ctrl+C` in the terminal to exit cleanly.
- **Actionable Diagnostics**: Friendly error handling for missing video files, blocked webcams, and model-loading failures.
- **Headless & Recording**: Run with `--headless` in automated environments and optionally save output with `--output`.

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- **Python**: Python 3.10 or higher.
- **OS**: macOS, Linux, or Windows.
- **Hardware**: Standard CPU or Apple Silicon / CUDA GPU (PyTorch auto-selects).

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

## 🎬 Running the Detection Pipeline

### A. Run with Webcam
To run on your default integrated webcam or external USB camera:
```bash
python main.py --source 0
```
> **macOS Note**: When running for the first time, macOS may ask for camera permission for your Terminal/IDE. Ensure permission is granted in *System Settings -> Privacy & Security -> Camera*.

### B. Run with a Local Video File
To run detection on any local video file:
```bash
python main.py --source path/to/your_video.mp4
```

### C. Run with the Built-in Sample Video
If you don't have a video clip or camera immediately handy, generate a sample synthetic clip:
```bash
# 1. Generate synthetic video
python scripts/create_sample_video.py

# 2. Run detection on the sample video
python main.py --source data/sample_demo.mp4
```

### D. Save Annotated Video Output
Save the detection video to disk:
```bash
python main.py --source data/sample_demo.mp4 --output data/annotated_output.mp4
```

### E. Run in Headless Mode (No GUI Window)
Ideal for servers, background scripts, or benchmarks:
```bash
python main.py --source data/sample_demo.mp4 --headless --max-frames 60
```

---

## ⚙️ Command-Line Arguments Reference

| Flag | Short | Default | Description |
|---|---|---|---|
| `--source` | `-s` | `0` | Camera device index (`0`, `1`) or path to a local video file. |
| `--model` | `-m` | `yolo11n.pt` | Model name or path (`yolo11n.pt`, `yolov8n.pt`, etc.). |
| `--conf` | `-c` | `0.35` | Confidence score threshold (0.0 to 1.0). |
| `--device` | | `None` | Compute device (`cpu`, `mps`, `cuda`). PyTorch auto-selects if omitted. |
| `--headless` | | `False` | Run without opening an OpenCV GUI window. |
| `--output` | `-o` | `None` | Path to save annotated video output (`.mp4`). |
| `--max-frames` | | `None` | Max frames to process before cleanly exiting. |

---

## 📂 Modular Architecture Layout

Following the architecture defined in [`ai_vision_project_docs/02_SYSTEM_ARCHITECTURE.md`](ai_vision_project_docs/02_SYSTEM_ARCHITECTURE.md):

```text
LiveSight/
├── vision/
│   ├── __init__.py         # Package exports
│   ├── schemas.py          # BoundingBox and Detection data structures
│   ├── exceptions.py       # Actionable VisionError, VideoSourceError, ModelLoadError
│   ├── source.py           # VideoSource adapter (webcam + file capture)
│   ├── detector.py         # YOLODetector (Ultralytics wrapper & normalization)
│   ├── annotator.py        # FrameAnnotator (bounding boxes, labels, FPS badge)
│   ├── pipeline.py         # DetectionPipeline (orchestration & metrics)
│   └── utils.py            # Utility helpers (synthetic video generation)
├── tests/
│   ├── test_schemas.py     # Schema and contract validation unit tests
│   ├── test_source.py      # Video source error and reading tests
│   ├── test_detector.py    # Detector loading and inference unit tests
│   ├── test_pipeline.py    # Pipeline and annotator unit tests
│   └── test_cli.py         # main.py CLI integration tests
├── scripts/
│   └── create_sample_video.py # Helper script to create test video
├── ai_vision_project_docs/ # Architecture and design documentation
├── main.py                 # CLI entry point
├── requirements.txt        # Project dependencies
├── .gitignore              # Git ignore rules
└── README.md               # Setup and usage guide
```

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:

```bash
pytest -v
```

All unit and integration tests run self-contained without needing an active webcam.

---

## 🔍 Troubleshooting

### Webcam fails to open (`VideoSourceError`)
1. **Camera permissions on macOS**: Open *System Settings -> Privacy & Security -> Camera* and ensure your Terminal, iTerm2, or VS Code/IDE is toggled ON.
2. **Device index**: If camera index `0` doesn't open, try `--source 1`.
3. **Hardware lock**: Ensure FaceTime, Zoom, Photo Booth, or browser tabs aren't currently using the camera.

### Model loading issues (`ModelLoadError`)
1. If weights are downloaded for the first time, ensure an internet connection is available.
2. The default model `yolo11n.pt` is lightweight (~5.6 MB) and downloads automatically to the working directory.
3. Check disk space and permissions in the project folder.

### Low FPS / Diagnostic Latency
1. LiveSight uses moving-average frame timing for diagnostic reporting.
2. For higher performance on Apple Silicon Macs, PyTorch automatically leverages Metal Performance Shaders (`mps`). On CPU, lightweight models like `yolo11n.pt` provide optimal real-time latency.
