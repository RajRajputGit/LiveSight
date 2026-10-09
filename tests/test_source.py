"""Unit tests for VideoSource adapter."""

from pathlib import Path
import pytest

from vision.exceptions import VideoSourceError
from vision.source import VideoSource
from vision.utils import create_synthetic_test_video


def test_video_source_file_not_found(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.mp4"
    with pytest.raises(VideoSourceError) as exc_info:
        VideoSource(source=str(non_existent))

    err_msg = str(exc_info.value)
    assert "Video file not found" in err_msg
    assert "Actionable steps" in err_msg


def test_video_source_directory_path(tmp_path: Path):
    with pytest.raises(VideoSourceError) as exc_info:
        VideoSource(source=str(tmp_path))

    err_msg = str(exc_info.value)
    assert "is a directory" in err_msg


def test_video_source_invalid_webcam_index():
    # Attempting to open an invalid high camera index (e.g. 9999) should fail with VideoSourceError
    with pytest.raises(VideoSourceError) as exc_info:
        VideoSource(source=9999)

    err_msg = str(exc_info.value)
    assert "Failed to open webcam at device index 9999" in err_msg
    assert "Actionable steps" in err_msg


def test_video_source_synthetic_video(tmp_path: Path):
    test_video_path = tmp_path / "test_clip.mp4"
    create_synthetic_test_video(test_video_path, num_frames=15, width=320, height=240, fps=25)

    with VideoSource(source=str(test_video_path)) as source:
        assert not source.is_webcam
        assert source.width == 320
        assert source.height == 240
        assert source.fps > 0

        frames = list(source)
        assert len(frames) == 15
        idx, first_frame = frames[0]
        assert idx == 0
        assert first_frame.shape == (240, 320, 3)

    # After exit, cap should be released
    assert source._cap is None
