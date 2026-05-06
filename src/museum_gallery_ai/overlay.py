from __future__ import annotations

from pathlib import Path

from .models import LineConfig, TrackObservation, ZoneConfig


class OverlayRenderer:
    def __init__(self, zones: tuple[ZoneConfig, ...], lines: tuple[LineConfig, ...]) -> None:
        import cv2
        import numpy as np

        self._cv2 = cv2
        self._np = np
        self.zones = zones
        self.lines = lines

    def render(self, frame, tracks: list[TrackObservation], metrics: dict) -> object:
        cv2 = self._cv2
        np = self._np
        annotated = frame.copy()
        for zone in self.zones:
            pts = np.array(zone.points, dtype=np.int32)
            color = self._zone_color(zone.zone_type)
            cv2.polylines(annotated, [pts], True, color, 2)
            x, y = [int(v) for v in zone.points[0]]
            label = zone.name or zone.zone_id
            cv2.putText(annotated, label, (x + 4, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        for line in self.lines:
            start = tuple(int(v) for v in line.start)
            end = tuple(int(v) for v in line.end)
            color = (255, 220, 0) if line.line_type == "entry" else (0, 180, 255)
            cv2.line(annotated, start, end, color, 2)
            cv2.putText(annotated, line.name or line.line_id, start, cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        for track in tracks:
            x, y, width, height = [int(v) for v in track.bbox]
            foot_x, foot_y = [int(v) for v in track.foot_point]
            cv2.rectangle(annotated, (x, y), (x + width, y + height), (0, 255, 0), 2)
            cv2.circle(annotated, (foot_x, foot_y), 4, (0, 255, 0), -1)
            cv2.putText(
                annotated,
                f"id={track.track_id} {track.confidence:.2f}",
                (x, max(0, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        entry_count = metrics.get("entry_count", 0)
        exit_count = metrics.get("exit_count", 0)
        cv2.putText(annotated, f"Entry: {entry_count} Exit: {exit_count}", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return annotated

    @staticmethod
    def _zone_color(zone_type: str) -> tuple[int, int, int]:
        if zone_type == "exhibit":
            return (0, 128, 255)
        if zone_type == "queue":
            return (255, 0, 255)
        if zone_type == "restricted":
            return (0, 0, 255)
        return (255, 128, 0)


class OverlayVideoWriter:
    def __init__(self, output_path: str | Path, fps: float, frame_size: tuple[int, int]) -> None:
        import cv2

        self._cv2 = cv2
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(str(output_path), fourcc, fps, frame_size)
        if not self._writer.isOpened():
            raise RuntimeError(f"Could not open overlay writer: {output_path}")

    def write(self, frame) -> None:
        self._writer.write(frame)

    def close(self) -> None:
        self._writer.release()
