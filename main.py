"""LiveSight - Real-Time AI Object Detection and Monitoring System (Phase 1).

Main entry point for running YOLO object detection on a webcam or local video file.

Usage:
  # Webcam (default index 0)
  python main.py

  # Specific webcam index
  python main.py --source 1

  # Local video file
  python main.py --source sample.mp4

  # Custom model and confidence threshold
  python main.py --source sample.mp4 --model yolo11n.pt --conf 0.40

  # Headless mode (no OpenCV GUI window, useful for scripts/servers)
  python main.py --source sample.mp4 --headless --max-frames 100
"""

from __future__ import annotations
import argparse
import sys
import time
from pathlib import Path
from typing import Optional

import cv2

from vision.annotator import FrameAnnotator
from vision.detector import YOLODetector
from vision.exceptions import ModelLoadError, VideoSourceError, VisionError
from vision.pipeline import DetectionPipeline
from vision.source import VideoSource


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="LiveSight Phase 1 - Real-Time YOLO Object Detection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default="0",
        help="Webcam device index (e.g. '0', '1') or path to a local video file.",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="yolo11n.pt",
        help="YOLO model weights name or path (e.g. 'yolo11n.pt', 'yolov8n.pt').",
    )
    parser.add_argument(
        "--conf",
        "-c",
        type=float,
        default=0.35,
        help="Confidence threshold between 0.0 and 1.0.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Inference device: 'cpu', 'mps', 'cuda', etc. Default: PyTorch auto-select.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without displaying an OpenCV GUI window.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Optional path to save annotated output video (.mp4).",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum number of frames to process before exiting (useful for testing).",
    )
    return parser.parse_args()


def run_detection(
    source_arg: str,
    model_arg: str = "yolo11n.pt",
    conf_arg: float = 0.35,
    device_arg: Optional[str] = None,
    headless: bool = False,
    output_path: Optional[str] = None,
    max_frames: Optional[int] = None,
) -> int:
    """Execute the detection loop on the chosen source."""
    print("=" * 65)
    print(" LiveSight: Real-Time AI Object Detection (Phase 1)")
    print("=" * 65)

    # 1. Initialize Video Source
    print(f"[*] Initializing video source: '{source_arg}'...")
    try:
        source = VideoSource(source=source_arg)
    except VideoSourceError as err:
        print(f"\n[ERROR] Video Source Failure:\n{err}", file=sys.stderr)
        return 1

    source_label = (
        f"Webcam [{source.device_index}]"
        if source.is_webcam
        else Path(str(source.source_path)).name
    )
    print(
        f"[+] Source opened: {source_label} | "
        f"Resolution: {source.width}x{source.height} | "
        f"FPS: {source.fps:.1f}"
    )

    # 2. Initialize YOLO Detector
    print(f"[*] Loading YOLO model '{model_arg}' (conf >= {conf_arg})...")
    try:
        detector = YOLODetector(
            model_name_or_path=model_arg,
            confidence_threshold=conf_arg,
            device=device_arg,
        )
    except ModelLoadError as err:
        source.release()
        print(f"\n[ERROR] Model Loading Failure:\n{err}", file=sys.stderr)
        return 1

    print(
        f"[+] Model ready: {len(detector.class_names)} classes supported "
        f"({detector.model_name_or_path})"
    )

    # 3. Setup Pipeline & Optional Video Writer
    annotator = FrameAnnotator()
    pipeline = DetectionPipeline(detector=detector, annotator=annotator)

    writer: Optional[cv2.VideoWriter] = None
    if output_path:
        out_p = Path(output_path).expanduser().resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            str(out_p),
            fourcc,
            source.fps if source.fps > 0 else 30.0,
            (source.width, source.height),
        )
        print(f"[+] Output will be saved to: {out_p}")

    window_name = "LiveSight - Phase 1 Object Detection (Press 'q' to quit)"
    if not headless:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, min(source.width, 1280), min(source.height, 720))
        print("[+] GUI window initialized. Press 'q' on the window to quit.")
    else:
        print("[+] Running in headless mode (no GUI window).")

    print("-" * 65)
    print("[*] Processing started...")

    start_wall_time = time.time()
    exit_reason = "Completed (End of stream)"

    try:
        for frame_idx, frame in source:
            if max_frames is not None and frame_idx >= max_frames:
                exit_reason = f"Reached max frames limit ({max_frames})"
                break

            # Run detection & annotate
            annotated_frame, detections, fps = pipeline.process_frame(
                frame=frame,
                source_label=source_label,
                draw_annotations=True,
            )

            # Write to output file if requested
            if writer is not None:
                writer.write(annotated_frame)

            # Display GUI window
            if not headless:
                cv2.imshow(window_name, annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    exit_reason = "User pressed 'q'"
                    print("\n[!] User requested quit ('q' key pressed).")
                    break

            # Diagnostic log every 30 frames
            if (frame_idx + 1) % 30 == 0:
                print(
                    f"    Frame {frame_idx + 1:>5} | "
                    f"FPS: {fps:5.1f} | "
                    f"Objects in frame: {len(detections)}"
                )

    except KeyboardInterrupt:
        exit_reason = "Interrupted by user (Ctrl+C)"
        print("\n[!] Interrupted by user (Ctrl+C).")
    except VisionError as err:
        exit_reason = f"Vision error: {err}"
        print(f"\n[ERROR] Pipeline error: {err}", file=sys.stderr)
        return 1
    finally:
        # Resource cleanup
        source.release()
        if writer is not None:
            writer.release()
        if not headless:
            cv2.destroyAllWindows()

    # 4. Print Run Summary
    elapsed_time = time.time() - start_wall_time
    total_frames = pipeline.total_frames
    avg_fps = (total_frames / elapsed_time) if elapsed_time > 0 else 0.0

    print("-" * 65)
    print(" LiveSight Phase 1 Run Summary")
    print("-" * 65)
    print(f"  Reason:           {exit_reason}")
    print(f"  Total Frames:     {total_frames}")
    print(f"  Elapsed Time:     {elapsed_time:.2f} seconds")
    print(f"  Average FPS:      {avg_fps:.1f}")
    if output_path:
        print(f"  Saved Video:      {output_path}")
    print("=" * 65)

    return 0


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    code = run_detection(
        source_arg=args.source,
        model_arg=args.model,
        conf_arg=args.conf,
        device_arg=args.device,
        headless=args.headless,
        output_path=args.output,
        max_frames=args.max_frames,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
