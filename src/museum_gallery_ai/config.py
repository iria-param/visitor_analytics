from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import CameraConfig, DetectorConfig, LineConfig, PipelineConfig, ProcessingConfig, ZoneConfig


def _point(value: list[int | float] | tuple[int | float, int | float]) -> tuple[float, float]:
    if len(value) != 2:
        raise ValueError(f"Expected point with 2 values, got {value!r}")
    return (float(value[0]), float(value[1]))


def load_config(path: str | Path, source_override: str | None = None) -> PipelineConfig:
    raw = _load_mapping(Path(path))
    camera_raw: dict[str, Any] = raw.get("camera") or {}
    camera = CameraConfig(
        camera_id=str(camera_raw.get("camera_id", "camera_1")),
        gallery_id=str(camera_raw.get("gallery_id", "gallery_1")),
        name=str(camera_raw.get("name", "")),
    )
    detector = DetectorConfig(**(raw.get("detector") or {}))
    processing = ProcessingConfig(**(raw.get("processing") or {}))

    zones = []
    for zone_raw in raw.get("zones") or []:
        zones.append(
            ZoneConfig(
                zone_id=str(zone_raw["zone_id"]),
                zone_type=zone_raw.get("zone_type", "exhibit"),
                camera_id=str(zone_raw.get("camera_id", camera.camera_id)),
                gallery_id=str(zone_raw.get("gallery_id", camera.gallery_id)),
                points=tuple(_point(p) for p in zone_raw["points"]),
                name=str(zone_raw.get("name", "")),
                exhibit_id=zone_raw.get("exhibit_id"),
            )
        )

    lines = []
    for line_raw in raw.get("lines") or []:
        lines.append(
            LineConfig(
                line_id=str(line_raw["line_id"]),
                line_type=line_raw.get("line_type", "transition"),
                camera_id=str(line_raw.get("camera_id", camera.camera_id)),
                gallery_id=str(line_raw.get("gallery_id", camera.gallery_id)),
                start=_point(line_raw["start"]),
                end=_point(line_raw["end"]),
                direction=line_raw.get("direction", "any"),
                name=str(line_raw.get("name", "")),
            )
        )

    if source_override:
        # Source path is passed at runtime, not stored in CameraConfig, so the same
        # camera identity can process files, webcams, and RTSP streams later.
        _ = str(source_override)

    return PipelineConfig(
        camera=camera,
        detector=detector,
        processing=processing,
        zones=tuple(zones),
        lines=tuple(lines),
    )


def _load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml
    except ImportError:
        return json.loads(text)
    loaded = yaml.safe_load(text)
    return loaded or {}
