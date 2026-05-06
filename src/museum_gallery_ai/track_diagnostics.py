from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from statistics import mean, median
from typing import Any

from .geometry import point_in_polygon
from .models import LineConfig, Point, ProcessingConfig, TrackObservation, ZoneConfig


@dataclass
class _TrackRecord:
    track_id: str
    first_timestamp: float
    last_timestamp: float
    first_processed_frame_index: int
    last_processed_frame_index: int
    first_point: Point
    last_point: Point
    observation_count: int = 1
    gap_count: int = 0
    gap_total_processed_frames: int = 0
    gap_max_processed_frames: int = 0

    def observe(self, timestamp_seconds: float, processed_frame_index: int, point: Point) -> None:
        gap = processed_frame_index - self.last_processed_frame_index - 1
        if gap > 0:
            self.gap_count += 1
            self.gap_total_processed_frames += gap
            self.gap_max_processed_frames = max(self.gap_max_processed_frames, gap)
        self.last_timestamp = timestamp_seconds
        self.last_processed_frame_index = processed_frame_index
        self.last_point = point
        self.observation_count += 1

    @property
    def duration_seconds(self) -> float:
        return max(0.0, self.last_timestamp - self.first_timestamp)

    @property
    def is_fallback(self) -> bool:
        return self.track_id.startswith("tmp_")


class TrackDiagnostics:
    def __init__(self, processing: ProcessingConfig) -> None:
        self.short_lived_track_seconds = processing.short_lived_track_seconds
        self.id_switch_window_seconds = processing.id_switch_window_seconds
        self.id_switch_distance_pixels = processing.id_switch_distance_pixels
        self.line_fragmentation_buffer_pixels = processing.line_fragmentation_buffer_pixels
        self._tracks: dict[str, _TrackRecord] = {}
        self._first_observed_seconds: float | None = None
        self._last_observed_seconds: float | None = None

    def observe(
        self,
        timestamp_seconds: float,
        processed_frame_index: int,
        observations: list[TrackObservation],
    ) -> None:
        if self._first_observed_seconds is None:
            self._first_observed_seconds = timestamp_seconds
        self._last_observed_seconds = timestamp_seconds

        for observation in observations:
            point = observation.foot_point
            record = self._tracks.get(observation.track_id)
            if record is None:
                self._tracks[observation.track_id] = _TrackRecord(
                    track_id=observation.track_id,
                    first_timestamp=timestamp_seconds,
                    last_timestamp=timestamp_seconds,
                    first_processed_frame_index=processed_frame_index,
                    last_processed_frame_index=processed_frame_index,
                    first_point=point,
                    last_point=point,
                )
            else:
                record.observe(timestamp_seconds, processed_frame_index, point)

    def summary(self, zones: tuple[ZoneConfig, ...], lines: tuple[LineConfig, ...]) -> dict[str, Any]:
        real_tracks = [track for track in self._tracks.values() if not track.is_fallback]
        fallback_tracks = [track for track in self._tracks.values() if track.is_fallback]
        durations = [track.duration_seconds for track in real_tracks]
        gaps = [track for track in real_tracks if track.gap_count > 0]
        total_gaps = sum(track.gap_count for track in real_tracks)
        total_gap_frames = sum(track.gap_total_processed_frames for track in real_tracks)
        max_gap_frames = max((track.gap_max_processed_frames for track in real_tracks), default=0)

        elapsed_seconds = 0.0
        if self._first_observed_seconds is not None and self._last_observed_seconds is not None:
            elapsed_seconds = self._last_observed_seconds - self._first_observed_seconds

        return {
            "unique_track_count": len(self._tracks),
            "real_track_count": len(real_tracks),
            "fallback_track_count": len(fallback_tracks),
            "duration_seconds": _duration_stats(durations),
            "short_lived_track_count": sum(
                1 for duration in durations if duration < self.short_lived_track_seconds
            ),
            "short_lived_threshold_seconds": round(self.short_lived_track_seconds, 3),
            "tracks_per_minute": round((len(real_tracks) * 60.0 / elapsed_seconds), 3)
            if elapsed_seconds > 0
            else 0.0,
            "gap_stats": {
                "tracks_with_gaps": len(gaps),
                "total_gaps": total_gaps,
                "mean_gap_processed_frames": round(total_gap_frames / total_gaps, 3) if total_gaps else 0.0,
                "max_gap_processed_frames": max_gap_frames,
            },
            "likely_id_switch_count": self._likely_id_switch_count(real_tracks),
            "likely_id_switch_params": {
                "window_seconds": round(self.id_switch_window_seconds, 3),
                "distance_pixels": round(self.id_switch_distance_pixels, 3),
            },
            "fragmentation_hotspots": self._fragmentation_hotspots(real_tracks, zones, lines),
        }

    def _likely_id_switch_count(self, tracks: list[_TrackRecord]) -> int:
        likely_switches = 0
        for ended in tracks:
            for started in tracks:
                if ended.track_id == started.track_id:
                    continue
                time_delta = started.first_timestamp - ended.last_timestamp
                if time_delta < 0 or time_delta > self.id_switch_window_seconds:
                    continue
                if _distance(ended.last_point, started.first_point) <= self.id_switch_distance_pixels:
                    likely_switches += 1
        return likely_switches

    def _fragmentation_hotspots(
        self,
        tracks: list[_TrackRecord],
        zones: tuple[ZoneConfig, ...],
        lines: tuple[LineConfig, ...],
    ) -> dict[str, Any]:
        by_zone = {
            zone.zone_id: {"track_starts": 0, "track_ends": 0}
            for zone in zones
        }
        by_line = {
            line.line_id: {"track_starts_within_buffer": 0, "track_ends_within_buffer": 0}
            for line in lines
        }
        outside_any_zone = {"track_starts": 0, "track_ends": 0}

        for track in tracks:
            if not _increment_zone_counts(track.first_point, zones, by_zone, "track_starts"):
                outside_any_zone["track_starts"] += 1
            if not _increment_zone_counts(track.last_point, zones, by_zone, "track_ends"):
                outside_any_zone["track_ends"] += 1

            for line in lines:
                if _point_to_segment_distance(track.first_point, line.start, line.end) <= self.line_fragmentation_buffer_pixels:
                    by_line[line.line_id]["track_starts_within_buffer"] += 1
                if _point_to_segment_distance(track.last_point, line.start, line.end) <= self.line_fragmentation_buffer_pixels:
                    by_line[line.line_id]["track_ends_within_buffer"] += 1

        return {
            "by_zone": by_zone,
            "by_line": by_line,
            "outside_any_zone": outside_any_zone,
        }


def _duration_stats(durations: list[float]) -> dict[str, float | None]:
    if not durations:
        return {
            "mean": None,
            "median": None,
            "p25": None,
            "p75": None,
            "min": None,
            "max": None,
        }
    return {
        "mean": round(mean(durations), 3),
        "median": round(median(durations), 3),
        "p25": round(_percentile(durations, 0.25), 3),
        "p75": round(_percentile(durations, 0.75), 3),
        "min": round(min(durations), 3),
        "max": round(max(durations), 3),
    }


def _percentile(values: list[float], percentile: float) -> float:
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * percentile
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - lower_index
    return sorted_values[lower_index] * (1.0 - weight) + sorted_values[upper_index] * weight


def _increment_zone_counts(
    point: Point,
    zones: tuple[ZoneConfig, ...],
    by_zone: dict[str, dict[str, int]],
    field: str,
) -> bool:
    matched = False
    for zone in zones:
        if point_in_polygon(point, zone.points):
            by_zone[zone.zone_id][field] += 1
            matched = True
    return matched


def _distance(a: Point, b: Point) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def _point_to_segment_distance(point: Point, start: Point, end: Point) -> float:
    segment_x = end[0] - start[0]
    segment_y = end[1] - start[1]
    length_squared = segment_x * segment_x + segment_y * segment_y
    if length_squared == 0:
        return _distance(point, start)
    projection = ((point[0] - start[0]) * segment_x + (point[1] - start[1]) * segment_y) / length_squared
    projection = max(0.0, min(1.0, projection))
    closest = (start[0] + projection * segment_x, start[1] + projection * segment_y)
    return _distance(point, closest)
