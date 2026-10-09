"""Integration tests for main.py CLI."""

import subprocess
import sys
from pathlib import Path

from vision.utils import create_synthetic_test_video


def test_cli_invalid_video_path():
    result = subprocess.run(
        [sys.executable, "main.py", "--source", "non_existent_file.mp4"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "Video Source Failure" in result.stderr
    assert "Video file not found" in result.stderr


def test_cli_invalid_model():
    result = subprocess.run(
        [sys.executable, "main.py", "--source", "0", "--model", "non_existent_weights_xyz.pt"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    # Either video source failed (if no camera) or model loading failed, exiting cleanly with code 1
    combined_err = result.stderr + result.stdout
    assert "ERROR" in combined_err


def test_cli_headless_synthetic_video(tmp_path: Path):
    test_video = tmp_path / "cli_test.mp4"
    create_synthetic_test_video(test_video, num_frames=10, width=320, height=240, fps=25)

    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--source",
            str(test_video),
            "--model",
            "yolo11n.pt",
            "--headless",
            "--max-frames",
            "5",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Processing started" in result.stdout
    assert "Reached max frames limit (5)" in result.stdout
    assert "LiveSight Phase 1 Run Summary" in result.stdout
    assert "Total Frames:     5" in result.stdout
