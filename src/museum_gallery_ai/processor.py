from __future__ import annotations

from pathlib import Path
from typing import Any

from .detector import create_detector
from .metrics import MetricsEngine
from .models import PipelineConfig, TrackEvent
from .overlay import OverlayRenderer, OverlayVideoWriter
from .track_diagnostics import TrackDiagnostics
from .video import VideoSource
from .writers import JsonlEventWriter, write_json
from .zone_engine import ZoneEventEngine


class OfflineProcessor:
    def __init__(self, config: PipelineConfig, source: str | Path, output_dir: str | Path) -> None:
        self.config = config
        self.source = source
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> dict[str, Any]:
        video: VideoSource | None = None
        events_writer: JsonlEventWriter | None = None
        overlay_writer: OverlayVideoWriter | None = None
        processed_frames = 0
        last_timestamp = 0.0
        event_engine: ZoneEventEngine | None = None
        metrics: MetricsEngine | None = None
        diagnostics: TrackDiagnostics | None = None

        try:
            video = VideoSource(self.source)
            detector = create_detector(self.config.detector)
            event_engine = ZoneEventEngine(self.config.zones, self.config.lines, self.config.processing)
            metrics = MetricsEngine(self.config.zones, self.config.lines, self.config.processing.congestion_threshold)
            diagnostics = TrackDiagnostics(self.config.processing)
            renderer = OverlayRenderer(self.config.zones, self.config.lines)
            events_writer = JsonlEventWriter(self.output_dir / "events.jsonl")

            while True:
                frame = video.read()
                if frame is None:
                    break
                if frame.frame_index % self.config.processing.frame_stride != 0:
                    continue
                if self.config.processing.max_frames is not None and processed_frames >= self.config.processing.max_frames:
                    break

                tracks = detector.track_people(frame.image)
                diagnostics.observe(frame.timestamp_seconds, processed_frames, tracks)
                events = event_engine.process(frame.timestamp_seconds, tracks)
                self._record_events(events, metrics, events_writer)

                current_summary = metrics.summary()
                overlay = renderer.render(frame.image, tracks, current_summary)
                if overlay_writer is None:
                    height, width = overlay.shape[:2]
                    fps = max(1.0, video.fps / max(1, self.config.processing.frame_stride))
                    overlay_writer = OverlayVideoWriter(self.output_dir / "overlay.mp4", fps, (width, height))
                overlay_writer.write(overlay)

                processed_frames += 1
                last_timestamp = frame.timestamp_seconds
        finally:
            if event_engine is not None and metrics is not None and events_writer is not None:
                closing_events = event_engine.close(last_timestamp)
                self._record_events(closing_events, metrics, events_writer)
                events_writer.close()
            if overlay_writer is not None:
                overlay_writer.close()
            if video is not None:
                video.close()

        if metrics is None:
            raise RuntimeError("Processing did not start; metrics engine was not initialized.")
        summary = metrics.summary()
        summary["processed_frames"] = processed_frames
        summary["source"] = str(self.source)
        summary["camera"] = {
            "camera_id": self.config.camera.camera_id,
            "gallery_id": self.config.camera.gallery_id,
            "name": self.config.camera.name,
        }
        if diagnostics is not None:
            summary["track_diagnostics"] = diagnostics.summary(self.config.zones, self.config.lines)
        write_json(self.output_dir / "metrics_summary.json", summary)
        return summary

    @staticmethod
    def _record_events(events: list[TrackEvent], metrics: MetricsEngine, writer: JsonlEventWriter) -> None:
        for event in events:
            metrics.apply(event)
            writer.write(event)
