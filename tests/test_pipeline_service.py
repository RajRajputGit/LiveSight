"""Unit and integration tests for PipelineService and background worker lifecycle."""

from pathlib import Path
import time
import pytest

from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.status import PipelineStatusEnum
from backend.app.services.event_publisher import EventPublisher
from backend.app.services.event_service import EventService
from backend.app.services.pipeline_service import PipelineService
from vision.utils import create_synthetic_test_video


@pytest.fixture
def services(tmp_path: Path):
    db_file = tmp_path / "pipeline_test.db"
    repo = EventRepository(db_file)
    publisher = EventPublisher()
    event_service = EventService(repo, publisher)
    pipeline_service = PipelineService(event_service)
    return repo, publisher, event_service, pipeline_service


def test_pipeline_service_initial_status(services):
    _, _, _, pipeline_service = services
    status = pipeline_service.get_status()
    assert status.pipeline_status == PipelineStatusEnum.IDLE.value
    assert status.model_loaded is False
    assert status.source_id is None


def test_pipeline_service_manual_status_update(services):
    _, _, _, pipeline_service = services
    pipeline_service.set_status(
        pipeline_status=PipelineStatusEnum.RUNNING.value,
        source_id="webcam_0",
        source_type="webcam",
        model_loaded=True,
        tracking_enabled=True,
        last_frame_at="2026-10-10T12:00:00.000Z",
    )

    status = pipeline_service.get_status()
    assert status.pipeline_status == "running"
    assert status.source_id == "webcam_0"
    assert status.source_type == "webcam"
    assert status.model_loaded is True
    assert status.tracking_enabled is True
    assert status.last_frame_at == "2026-10-10T12:00:00.000Z"


def test_pipeline_service_invalid_source_sets_failed_status(services):
    _, _, _, pipeline_service = services

    # Launch background worker pointing to a non-existent file
    pipeline_service.start(
        source_target="/nonexistent/path/to/video.mp4",
        max_frames=1,
    )

    # Wait for worker thread to fail and complete
    if pipeline_service._thread is not None:
        pipeline_service._thread.join(timeout=5.0)

    status = pipeline_service.get_status()
    assert status.pipeline_status == PipelineStatusEnum.FAILED.value
    assert status.last_error is not None
    assert "Video file not found" in status.last_error


def test_pipeline_service_synthetic_video_lifecycle(services, tmp_path: Path):
    _, _, _, pipeline_service = services

    # Create a small 5-frame synthetic video
    video_path = tmp_path / "pipeline_sample.mp4"
    create_synthetic_test_video(video_path, num_frames=5, width=320, height=240, fps=15)

    pipeline_service.start(
        source_target=str(video_path),
        model_name="yolo11n.pt",
        confidence=0.5,
        enable_tracking=True,
        rules_config="configs/rules.json",
        max_frames=5,
    )

    # Allow worker thread to process the 5 frames
    if pipeline_service._thread is not None:
        pipeline_service._thread.join(timeout=15.0)

    status = pipeline_service.get_status()
    assert status.pipeline_status in (PipelineStatusEnum.STOPPED.value, PipelineStatusEnum.IDLE.value)
    assert status.last_frame_at is not None
    assert status.last_error is None
