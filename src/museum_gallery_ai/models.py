from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Point = tuple[float, float]
BBox = tuple[float, float, float, float]

ZoneType = Literal["entrance", "exit", "gallery", "exhibit", "queue", "restricted", "pathway"]
LineType = Literal["entry", "exit", "transition"]
LineDirection = Literal["any", "positive", "negative"]


@dataclass(frozen=True)
class CameraConfig:
    camera_id: str
    gallery_id: str
    name: str = ""


@dataclass(frozen=True)
class ZoneConfig:
    zone_id: str
    zone_type: ZoneType
    camera_id: str
    gallery_id: str
    points: tuple[Point, ...]
    name: str = ""
    exhibit_id: str | None = None


@dataclass(frozen=True)
class LineConfig:
    line_id: str
    line_type: LineType
    camera_id: str
    gallery_id: str
    start: Point
    end: Point
    direction: LineDirection = "any"
    name: str = ""


@dataclass(frozen=True)
class DetectorConfig:
    provider: str = "ultralytics"
    model_name: str = "yolo11n.pt"
    confidence_threshold: float = 0.18
    image_size: int = 1280
    tracker: str = "bytetrack.yaml"
    device: str = "cpu"


@dataclass(frozen=True)
class ProcessingConfig:
    max_frames: int | None = None
    frame_stride: int = 1
    dwell_confirm_seconds: float = 3.0
    lost_track_grace_seconds: float = 5.0
    congestion_threshold: int = 5
    congestion_min_seconds: float = 10.0
    short_lived_track_seconds: float = 1.0
    id_switch_window_seconds: float = 2.0
    id_switch_distance_pixels: float = 80.0
    line_fragmentation_buffer_pixels: float = 30.0


@dataclass(frozen=True)
class PipelineConfig:
    camera: CameraConfig
    detector: DetectorConfig
    processing: ProcessingConfig
    zones: tuple[ZoneConfig, ...] = ()
    lines: tuple[LineConfig, ...] = ()


@dataclass(frozen=True)
class TrackObservation:
    track_id: str
    bbox: BBox
    confidence: float
    class_name: str = "person"

    @property
    def center(self) -> Point:
        x, y, width, height = self.bbox
        return (x + width / 2.0, y + height / 2.0)

    @property
    def foot_point(self) -> Point:
        x, y, width, height = self.bbox
        return (x + width / 2.0, y + height)


@dataclass(frozen=True)
class TrackEvent:
    timestamp_seconds: float
    camera_id: str
    gallery_id: str
    event_type: str
    track_id: str | None = None
    zone_id: str | None = None
    line_id: str | None = None
    confidence: float = 1.0
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp_seconds"] = round(float(self.timestamp_seconds), 3)
        data["confidence"] = round(float(self.confidence), 4)
        return data


@dataclass
class ZoneMetrics:
    zone_id: str
    zone_type: str
    total_visitors: int = 0
    active_visitors: int = 0
    max_concurrent: int = 0
    total_dwell_seconds: float = 0.0
    congestion_events: int = 0
    pass_by_count: int = 0

    @property
    def average_dwell_seconds(self) -> float:
        if self.total_visitors == 0:
            return 0.0
        return self.total_dwell_seconds / self.total_visitors

    def to_dict(self) -> dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "zone_type": self.zone_type,
            "total_visitors": self.total_visitors,
            "active_visitors": self.active_visitors,
            "max_concurrent": self.max_concurrent,
            "total_dwell_seconds": round(self.total_dwell_seconds, 3),
            "average_dwell_seconds": round(self.average_dwell_seconds, 3),
            "congestion_events": self.congestion_events,
            "pass_by_count": self.pass_by_count,
        }


@dataclass
class LineMetrics:
    line_id: str
    line_type: str
    crossings: int = 0
    positive_crossings: int = 0
    negative_crossings: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
