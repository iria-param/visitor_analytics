from __future__ import annotations

from dataclasses import dataclass

from .geometry import crossing_direction, point_in_polygon
from .models import LineConfig, Point, ProcessingConfig, TrackEvent, TrackObservation, ZoneConfig


@dataclass
class ActiveZoneVisit:
    entry_timestamp: float
    last_seen_timestamp: float
    confidence: float
    confirmed: bool = False


class ZoneEventEngine:
    def __init__(
        self,
        zones: tuple[ZoneConfig, ...],
        lines: tuple[LineConfig, ...],
        processing: ProcessingConfig,
    ) -> None:
        self.zones = zones
        self.lines = lines
        self.processing = processing
        self._active_zone_visits: dict[tuple[str, str], ActiveZoneVisit] = {}
        self._previous_positions: dict[str, Point] = {}

    def process(self, timestamp_seconds: float, tracks: list[TrackObservation]) -> list[TrackEvent]:
        events: list[TrackEvent] = []
        current_zone_keys: set[tuple[str, str]] = set()

        for track in tracks:
            point = track.foot_point
            previous = self._previous_positions.get(track.track_id)
            if previous is not None:
                events.extend(self._line_events(timestamp_seconds, track, previous, point))

            for zone in self.zones:
                if point_in_polygon(point, zone.points):
                    key = (zone.zone_id, track.track_id)
                    current_zone_keys.add(key)
                    active = self._active_zone_visits.get(key)
                    if active is None:
                        self._active_zone_visits[key] = ActiveZoneVisit(
                            entry_timestamp=timestamp_seconds,
                            last_seen_timestamp=timestamp_seconds,
                            confidence=track.confidence,
                        )
                        events.append(self._event(timestamp_seconds, zone, "zone_entered", track, track.confidence))
                    else:
                        active.last_seen_timestamp = timestamp_seconds
                        active.confidence = max(active.confidence, track.confidence)
                        if not active.confirmed and timestamp_seconds - active.entry_timestamp >= self.processing.dwell_confirm_seconds:
                            active.confirmed = True
                            events.append(
                                self._event(
                                    timestamp_seconds,
                                    zone,
                                    "dwell_confirmed",
                                    track,
                                    active.confidence,
                                    {"dwell_seconds": timestamp_seconds - active.entry_timestamp},
                                )
                            )

            self._previous_positions[track.track_id] = point

        events.extend(self._expire_missing_tracks(timestamp_seconds, current_zone_keys))
        return events

    def close(self, timestamp_seconds: float) -> list[TrackEvent]:
        events: list[TrackEvent] = []
        for key, active in list(self._active_zone_visits.items()):
            zone_id, track_id = key
            zone = self._zone_by_id(zone_id)
            if zone is None:
                continue
            events.append(
                TrackEvent(
                    timestamp_seconds=timestamp_seconds,
                    camera_id=zone.camera_id,
                    gallery_id=zone.gallery_id,
                    event_type="zone_exited",
                    track_id=track_id,
                    zone_id=zone.zone_id,
                    confidence=active.confidence,
                    evidence={
                        "duration_seconds": max(0.0, active.last_seen_timestamp - active.entry_timestamp),
                        "confirmed": active.confirmed,
                        "reason": "stream_closed",
                    },
                )
            )
        self._active_zone_visits.clear()
        return events

    def _line_events(
        self,
        timestamp_seconds: float,
        track: TrackObservation,
        previous: Point,
        current: Point,
    ) -> list[TrackEvent]:
        events: list[TrackEvent] = []
        for line in self.lines:
            direction = crossing_direction(previous, current, line.start, line.end)
            if direction is None:
                continue
            if line.direction != "any" and line.direction != direction:
                continue
            events.append(
                TrackEvent(
                    timestamp_seconds=timestamp_seconds,
                    camera_id=line.camera_id,
                    gallery_id=line.gallery_id,
                    event_type="line_crossed",
                    track_id=track.track_id,
                    line_id=line.line_id,
                    confidence=track.confidence,
                    evidence={
                        "line_type": line.line_type,
                        "direction": direction,
                        "previous_point": list(previous),
                        "current_point": list(current),
                    },
                )
            )
        return events

    def _expire_missing_tracks(self, timestamp_seconds: float, current_zone_keys: set[tuple[str, str]]) -> list[TrackEvent]:
        events: list[TrackEvent] = []
        for key, active in list(self._active_zone_visits.items()):
            if key in current_zone_keys:
                continue
            if timestamp_seconds - active.last_seen_timestamp <= self.processing.lost_track_grace_seconds:
                continue
            zone_id, track_id = key
            zone = self._zone_by_id(zone_id)
            if zone is None:
                continue
            duration = max(0.0, active.last_seen_timestamp - active.entry_timestamp)
            events.append(
                TrackEvent(
                    timestamp_seconds=timestamp_seconds,
                    camera_id=zone.camera_id,
                    gallery_id=zone.gallery_id,
                    event_type="zone_exited",
                    track_id=track_id,
                    zone_id=zone.zone_id,
                    confidence=active.confidence,
                    evidence={"duration_seconds": duration, "confirmed": active.confirmed, "reason": "track_lost"},
                )
            )
            del self._active_zone_visits[key]
        return events

    def _zone_by_id(self, zone_id: str) -> ZoneConfig | None:
        for zone in self.zones:
            if zone.zone_id == zone_id:
                return zone
        return None

    @staticmethod
    def _event(
        timestamp_seconds: float,
        zone: ZoneConfig,
        event_type: str,
        track: TrackObservation,
        confidence: float,
        evidence: dict | None = None,
    ) -> TrackEvent:
        return TrackEvent(
            timestamp_seconds=timestamp_seconds,
            camera_id=zone.camera_id,
            gallery_id=zone.gallery_id,
            event_type=event_type,
            track_id=track.track_id,
            zone_id=zone.zone_id,
            confidence=confidence,
            evidence=evidence or {"zone_type": zone.zone_type},
        )
