from __future__ import annotations

from typing import Protocol

from .models import DetectorConfig, TrackObservation


class Detector(Protocol):
    def track_people(self, frame) -> list[TrackObservation]:
        ...


class UltralyticsPersonTracker:
    def __init__(self, config: DetectorConfig) -> None:
        self.config = config
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("ultralytics is required for the YOLO detector. Install requirements.txt.") from exc
        self._model = YOLO(config.model_name)
        if config.device:
            self._model.to(config.device)

    def track_people(self, frame) -> list[TrackObservation]:
        results = self._model.track(
            frame,
            conf=self.config.confidence_threshold,
            iou=0.4,
            imgsz=self.config.image_size,
            tracker=self.config.tracker,
            persist=True,
            verbose=False,
            classes=[0],
        )
        observations: list[TrackObservation] = []
        if not results or not getattr(results[0], "boxes", None):
            return observations

        boxes = results[0].boxes
        for index in range(len(boxes)):
            class_id = int(boxes.cls[index].item())
            if class_id != 0:
                continue
            confidence = float(boxes.conf[index].item())
            if confidence < self.config.confidence_threshold:
                continue
            x1, y1, x2, y2 = [float(v) for v in boxes.xyxy[index].tolist()]
            track_id = self._track_id(boxes, index, x1, y1)
            observations.append(
                TrackObservation(
                    track_id=track_id,
                    bbox=(x1, y1, x2 - x1, y2 - y1),
                    confidence=confidence,
                    class_name="person",
                )
            )
        return observations

    @staticmethod
    def _track_id(boxes, index: int, x: float, y: float) -> str:
        if boxes.id is not None and boxes.id[index] is not None:
            try:
                return str(int(boxes.id[index].item()))
            except Exception:
                return str(boxes.id[index])
        return f"tmp_{int(x // 20)}_{int(y // 20)}"


def create_detector(config: DetectorConfig) -> Detector:
    if config.provider != "ultralytics":
        raise ValueError(f"Unsupported detector provider: {config.provider}")
    return UltralyticsPersonTracker(config)
