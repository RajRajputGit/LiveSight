"""YOLO Object Detector wrapper for LiveSight.

Uses Ultralytics YOLO models (e.g. YOLO11, YOLOv8) to perform object detection
and normalizes outputs into LiveSight detection contracts.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Union

import numpy as np

from vision.exceptions import InferenceError, ModelLoadError
from vision.schemas import BoundingBox, Detection


class YOLODetector:
    """YOLO-based object detector producing normalized LiveSight detections."""

    def __init__(
        self,
        model_name_or_path: str = "yolo11n.pt",
        confidence_threshold: float = 0.35,
        classes: Optional[List[int]] = None,
        device: Optional[Union[str, int]] = None,
    ) -> None:
        """Initialize the YOLO detector.

        Args:
            model_name_or_path: Model name (e.g. 'yolo11n.pt') or path to local .pt weights.
            confidence_threshold: Minimum confidence score [0.0 - 1.0] to keep a detection.
            classes: Optional list of class IDs to filter (e.g., [0] for person only).
            device: Computation device (e.g., 'cpu', 'mps', 0). None lets PyTorch auto-select.
        """
        self.model_name_or_path = model_name_or_path
        self.confidence_threshold = float(confidence_threshold)
        self.classes = classes
        self.device = device
        self.model = self._load_model()

    def _load_model(self):
        """Safely load Ultralytics YOLO model with actionable error reporting."""
        try:
            from ultralytics import YOLO

            model = YOLO(self.model_name_or_path)
            return model
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to load YOLO model from '{self.model_name_or_path}'.\n"
                f"Underlying error: {type(exc).__name__}: {exc}\n"
                "Actionable steps:\n"
                "  1. Verify the model name is valid (e.g., 'yolo11n.pt', 'yolov8n.pt').\n"
                "  2. If using a custom model file, verify the path exists and is not corrupted.\n"
                "  3. If downloading for the first time, check internet connectivity and disk space.\n"
                "  4. Verify that PyTorch and Ultralytics are properly installed in the active environment."
            ) from exc

    @property
    def class_names(self) -> Dict[int, str]:
        """Dictionary mapping class ID to class name."""
        if hasattr(self.model, "names") and isinstance(self.model.names, dict):
            return self.model.names
        return {}

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Run object detection inference on a frame.

        Args:
            frame: Input image/frame in BGR format (numpy array).

        Returns:
            List of normalized Detection objects.
        """
        if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
            return []

        try:
            results = self.model.predict(
                frame,
                conf=self.confidence_threshold,
                classes=self.classes,
                device=self.device,
                verbose=False,
            )
        except Exception as exc:
            raise InferenceError(
                f"Inference failed on frame of shape {frame.shape}: {exc}"
            ) from exc

        detections: List[Detection] = []
        if not results:
            return detections

        first_res = results[0]
        boxes = getattr(first_res, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return detections

        names = self.class_names

        for box in boxes:
            coords = box.xyxy[0].tolist()
            x1, y1, x2, y2 = float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3])

            # Ensure coordinate bounds are sane
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = names.get(cls_id, f"class_{cls_id}")

            detections.append(
                Detection(
                    class_id=cls_id,
                    class_name=cls_name,
                    confidence=conf,
                    bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                )
            )

        return detections
