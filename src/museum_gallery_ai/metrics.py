from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import LineConfig, LineMetrics, TrackEvent, ZoneConfig, ZoneMetrics


class MetricsEngine:
    def __init__(self, zones: tuple[ZoneConfig, ...], lines: tuple[LineConfig, ...], congestion_threshold: int = 5) -> None:
        self.zone_metrics = {zone.zone_id: ZoneMetrics(zone.zone_id, zone.zone_type) for zone in zones}
        self.line_metrics = {line.line_id: LineMetrics(line.line_id, line.line_type) for line in lines}
        self.congestion_threshold = congestion_threshold
        self._entry_counts = 0
        self._exit_counts = 0
        self._seen_tracks_by_zone: dict[str, set[str]] = defaultdict(set)

    def apply(self, event: TrackEvent) -> None:
        if event.event_type == "line_crossed" and event.line_id:
            self._apply_line_crossing(event)
        if not event.zone_id:
            return
        metric = self.zone_metrics.get(event.zone_id)
        if metric is None:
            return
        if event.event_type == "zone_entered" and event.track_id:
            self._seen_tracks_by_zone[event.zone_id].add(event.track_id)
        elif event.event_type == "dwell_confirmed":
            metric.total_visitors += 1
            metric.active_visitors += 1
            metric.max_concurrent = max(metric.max_concurrent, metric.active_visitors)
            if metric.active_visitors >= self.congestion_threshold:
                metric.congestion_events += 1
        elif event.event_type == "zone_exited":
            if event.evidence.get("confirmed"):
                metric.active_visitors = max(0, metric.active_visitors - 1)
                metric.total_dwell_seconds += float(event.evidence.get("duration_seconds", 0.0))
            else:
                metric.pass_by_count += 1

    def summary(self) -> dict[str, Any]:
        zones = {zone_id: metric.to_dict() for zone_id, metric in self.zone_metrics.items()}
        lines = {line_id: metric.to_dict() for line_id, metric in self.line_metrics.items()}
        recommendations = self._recommendations(zones)
        return {
            "entry_count": self._entry_counts,
            "exit_count": self._exit_counts,
            "zones": zones,
            "lines": lines,
            "recommendations": recommendations,
        }

    def _apply_line_crossing(self, event: TrackEvent) -> None:
        metric = self.line_metrics.get(event.line_id or "")
        if metric is None:
            return
        metric.crossings += 1
        direction = event.evidence.get("direction")
        if direction == "positive":
            metric.positive_crossings += 1
        elif direction == "negative":
            metric.negative_crossings += 1
        line_type = event.evidence.get("line_type")
        if line_type == "entry":
            self._entry_counts += 1
        elif line_type == "exit":
            self._exit_counts += 1

    @staticmethod
    def _recommendations(zones: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        for zone_id, metric in zones.items():
            if metric["zone_type"] != "exhibit":
                continue
            if metric["pass_by_count"] >= 3 and metric["total_visitors"] == 0:
                recommendations.append(
                    {
                        "type": "ignored_exhibit",
                        "zone_id": zone_id,
                        "message": "High pass-by activity with no confirmed dwell. Review label visibility, lighting, or placement.",
                        "evidence": {
                            "pass_by_count": metric["pass_by_count"],
                            "total_visitors": metric["total_visitors"],
                        },
                    }
                )
            if metric["congestion_events"] > 0:
                recommendations.append(
                    {
                        "type": "congested_exhibit",
                        "zone_id": zone_id,
                        "message": "Sustained occupancy reached the congestion threshold. Review circulation space around this exhibit.",
                        "evidence": {"congestion_events": metric["congestion_events"]},
                    }
                )
        return recommendations
