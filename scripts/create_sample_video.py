"""Helper script to create a sample test video for LiveSight object detection."""

from pathlib import Path
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vision.utils import create_synthetic_test_video


def main():
    target = Path("data/sample_demo.mp4")
    print(f"[*] Generating sample test video at: {target}...")
    create_synthetic_test_video(target, num_frames=120, width=640, height=480, fps=30)
    print(f"[+] Done! You can now run:\n    python main.py --source {target}")


if __name__ == "__main__":
    main()
