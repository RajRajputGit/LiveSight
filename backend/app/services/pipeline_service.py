"""Background Pipeline Service managing video capture, inference, and status telemetry.

Conforms to Phase 4 specifications in 02_SYSTEM_ARCHITECTURE.md and 05_API_SPECIFICATION.md:
- Keeps heavy computer vision processing in a dedicated background worker
- Decouples YOLO inference from HTTP/WebSocket request lifecycles
- Exposes thread-safe runtime status for GET /api/status
- Emits detected domain events to EventService for persistence and live streaming
"""

from __future__ import annotations
from datetime import datetime, timezone
import logging
from pathlib import Path
import threading
import time
from typing import Any, Dict, Optional, Union

from backend.app.schemas.status import PipelineStatusEnum, RuntimeStatusResponse
from backend.app.services.event_service import EventService
from rules.engine import RuleEngine
from vision.detector import YOLODetector
from vision.pipeline import DetectionPipeline
from vision.source import VideoSource

logger = logging.getLogger("livesight.pipeline_service")


class PipelineService:
    """Manages the background vision pipeline lifecycle and telemetry status."""

    def __init__(self, event_service: EventService) -> None:
        self.event_service = event_service
        self._lock = threading.Lock()

        # Telemetry state
        self._pipeline_status: str = PipelineStatusEnum.IDLE.value
        self._source_id: Optional[str] = None
        self._source_type: Optional[str] = None
        self._model_loaded: bool = False
        self._tracking_enabled: bool = False
        self._last_frame_at: Optional[str] = None
        self._last_error: Optional[str] = None

        # Threading state
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def get_status(self) -> RuntimeStatusResponse:
        """Get snapshot of current runtime pipeline status."""
        with self._lock:
            return RuntimeStatusResponse(
                pipeline_status=self._pipeline_status,
                source_id=self._source_id,
                source_type=self._source_type,
                model_loaded=self._model_loaded,
                tracking_enabled=self._tracking_enabled,
                last_frame_at=self._last_frame_at,
                last_error=self._last_error,
            )

    def set_status(
        self,
        pipeline_status: Optional[str] = None,
        source_id: Optional[str] = None,
        source_type: Optional[str] = None,
        model_loaded: Optional[bool] = None,
        tracking_enabled: Optional[bool] = None,
        last_frame_at: Optional[str] = None,
        last_error: Optional[str] = None,
    ) -> None:
        """Update telemetry status fields (thread-safe)."""
        with self._lock:
            if pipeline_status is not None:
                self._pipeline_status = pipeline_status
            if source_id is not None:
                self._source_id = source_id
            if source_type is not None:
                self._source_type = source_type
            if model_loaded is not None:
                self._model_loaded = model_loaded
            if tracking_enabled is not None:
                self._tracking_enabled = tracking_enabled
            if last_frame_at is not None:
                self._last_frame_at = last_frame_at
            if last_error is not None:
                self._last_error = last_error

    def start(
        self,
        source_target: Union[int, str] = 0,
        model_name: str = "yolo11n.pt",
        confidence: float = 0.35,
        enable_tracking: bool = True,
        tracker_config: str = "bytetrack.yaml",
        rules_config: Optional[str] = "configs/rules.json",
        max_frames: Optional[int] = None,
    ) -> None:
        """Start vision pipeline processing in a background daemon thread."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                logger.warning("Pipeline background worker is already running.")
                return

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_worker,
                kwargs={
                    "source_target": source_target,
                    "model_name": model_name,
                    "confidence": confidence,
                    "enable_tracking": enable_tracking,
                    "tracker_config": tracker_config,
                    "rules_config": rules_config,
                    "max_frames": max_frames,
                },
                daemon=True,
                name="livesight-vision-worker",
            )
            self._thread.start()
            logger.info("Started background vision pipeline thread.")

    def stop(self, timeout: float = 5.0) -> None:
        """Signal background worker to stop and wait for termination."""
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            logger.info("Background vision pipeline thread stopped.")
        with self._lock:
            if self._pipeline_status == PipelineStatusEnum.RUNNING.value:
                self._pipeline_status = PipelineStatusEnum.STOPPED.value

    def _run_worker(
        self,
        source_target: Union[int, str],
        model_name: str,
        confidence: float,
        enable_tracking: bool,
        tracker_config: str,
        rules_config: Optional[str],
        max_frames: Optional[int] = None,
    ) -> None:
        """Background worker loop executing capture, inference, tracking, and rules."""
        source = None
        pipeline = None

        try:
            # 1. Open Video Source
            source = VideoSource(source_target)
            source_id = (
                f"webcam_{source.device_index}"
                if source.is_webcam
                else (source.source_path.name if source.source_path else "unknown_source")
            )
            source_type = "webcam" if source.is_webcam else "file"

            with self._lock:
                self._source_id = source_id
                self._source_type = source_type
                self._pipeline_status = PipelineStatusEnum.RUNNING.value
                self._tracking_enabled = enable_tracking
                self._last_error = None

            # 2. Load Detector
            detector = YOLODetector(
                model_name_or_path=model_name,
                confidence_threshold=confidence,
            )
            with self._lock:
                self._model_loaded = True

            # 3. Load Rule Engine if configured
            rule_engine = None
            if rules_config:
                p = Path(rules_config).expanduser()
                if p.exists():
                    rule_engine = RuleEngine.from_config_file(p)

            # 4. Initialize Pipeline
            pipeline = DetectionPipeline(
                detector=detector,
                enable_tracking=enable_tracking,
                tracker_config=tracker_config,
                rule_engine=rule_engine,
            )

            # 5. Process Frames
            for frame_idx, frame in source:
                if self._stop_event.is_set():
                    break
                if max_frames is not None and frame_idx >= max_frames:
                    break

                # Inference, tracking, rule evaluation
                _, _, _, new_events = pipeline.process_frame(
                    frame=frame,
                    source_label=source_id,
                    draw_annotations=False,
                    return_events=True,
                )

                now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                with self._lock:
                    self._last_frame_at = now_utc

                # Persist and stream any triggered domain events
                for event in new_events:
                    try:
                        self.event_service.record_event(event)
                    except Exception as exc:
                        logger.error("Failed to record event in background pipeline: %s", exc)

            with self._lock:
                self._pipeline_status = PipelineStatusEnum.STOPPED.value

        except Exception as exc:
            logger.error("Vision worker encountered failure: %s", exc, exc_info=True)
            with self._lock:
                self._pipeline_status = PipelineStatusEnum.FAILED.value
                self._last_error = str(exc)
        finally:
            if source is not None:
                source.release()
            if pipeline is not None:
                pipeline.reset_tracker()
            with self._lock:
                self._model_loaded = False
