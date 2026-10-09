"""Utility helpers for LiveSight vision pipeline."""

from __future__ import annotations
from pathlib import Path
from typing import Union

import cv2
import numpy as np


def create_synthetic_test_video(
    output_path: Union[str, Path],
    num_frames: int = 60,
    width: int = 640,
    height: int = 480,
    fps: int = 30,
) -> Path:
    """Generate a lightweight synthetic MP4 video for local testing and verification.

    Draws moving shapes and test patterns so the detector and pipeline can run
    end-to-end without requiring a physical camera or external video download.

    Args:
        output_path: Destination path for the generated video file.
        num_frames: Number of frames to synthesize.
        width: Frame width in pixels.
        height: Frame height in pixels.
        fps: Target frame rate.

    Returns:
        Path to the generated video.
    """
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(path), fourcc, float(fps), (width, height))

    if not out.isOpened():
        raise RuntimeError(f"Could not initialize cv2.VideoWriter for '{path}'")

    for i in range(num_frames):
        # Create gradient background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :, 0] = int(30 + (i * 2) % 100)  # Blue
        frame[:, :, 1] = int(40 + (i * 1.5) % 80) # Green
        frame[:, :, 2] = 50                      # Red

        # Draw a moving rectangle
        rect_x = int(50 + (i * 7) % (width - 150))
        rect_y = int(80 + (i * 4) % (height - 150))
        cv2.rectangle(
            frame,
            (rect_x, rect_y),
            (rect_x + 90, rect_y + 110),
            (0, 220, 255),
            -1,
        )

        # Draw a moving circle
        circle_x = int(width - 80 - (i * 5) % (width - 160))
        circle_y = int(height - 100 - (i * 3) % (height - 180))
        cv2.circle(frame, (circle_x, circle_y), 45, (255, 120, 0), -1)

        # Frame counter label
        cv2.putText(
            frame,
            f"Test Frame {i + 1}/{num_frames}",
            (30, height - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        out.write(frame)

    out.release()
    return path
