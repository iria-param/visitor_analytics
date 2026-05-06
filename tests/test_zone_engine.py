import unittest

from museum_gallery_ai.metrics import MetricsEngine
from museum_gallery_ai.models import LineConfig, ProcessingConfig, TrackObservation, ZoneConfig
from museum_gallery_ai.zone_engine import ZoneEventEngine


def _track(track_id: str, foot_x: float, foot_y: float) -> TrackObservation:
    return TrackObservation(track_id=track_id, bbox=(foot_x - 1, foot_y - 2, 2, 2), confidence=0.9)


class ZoneEngineTests(unittest.TestCase):
    def test_dwell_confirmation_and_occupancy_flow(self):
        zone = ZoneConfig(
            zone_id="exhibit_a",
            zone_type="exhibit",
            camera_id="camera_1",
            gallery_id="gallery_1",
            points=((0, 0), (10, 0), (10, 10), (0, 10)),
        )
        processing = ProcessingConfig(dwell_confirm_seconds=3.0, lost_track_grace_seconds=1.0)
        engine = ZoneEventEngine((zone,), (), processing)
        metrics = MetricsEngine((zone,), (), congestion_threshold=5)

        events = engine.process(0.0, [_track("1", 5, 5)])
        for event in events:
            metrics.apply(event)
        self.assertEqual([event.event_type for event in events], ["zone_entered"])
        self.assertEqual(metrics.summary()["zones"]["exhibit_a"]["active_visitors"], 0)

        events = engine.process(3.1, [_track("1", 5, 5)])
        for event in events:
            metrics.apply(event)
        self.assertIn("dwell_confirmed", [event.event_type for event in events])
        self.assertEqual(metrics.summary()["zones"]["exhibit_a"]["total_visitors"], 1)
        self.assertEqual(metrics.summary()["zones"]["exhibit_a"]["active_visitors"], 1)

        events = engine.process(5.0, [_track("1", 20, 20)])
        for event in events:
            metrics.apply(event)
        self.assertIn("zone_exited", [event.event_type for event in events])
        zone_summary = metrics.summary()["zones"]["exhibit_a"]
        self.assertEqual(zone_summary["active_visitors"], 0)
        self.assertGreaterEqual(zone_summary["total_dwell_seconds"], 3.0)

    def test_line_crossing_increments_entry_count(self):
        line = LineConfig(
            line_id="entry_line",
            line_type="entry",
            camera_id="camera_1",
            gallery_id="gallery_1",
            start=(0, 0),
            end=(10, 0),
            direction="any",
        )
        engine = ZoneEventEngine((), (line,), ProcessingConfig())
        metrics = MetricsEngine((), (line,))

        self.assertEqual(engine.process(0.0, [_track("1", 5, -1)]), [])
        events = engine.process(1.0, [_track("1", 5, 1)])
        for event in events:
            metrics.apply(event)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "line_crossed")
        self.assertEqual(events[0].camera_id, "camera_1")
        self.assertEqual(events[0].gallery_id, "gallery_1")
        self.assertEqual(events[0].evidence["direction"], "positive")
        self.assertEqual(metrics.summary()["entry_count"], 1)

    def test_ignored_exhibit_recommendation_from_pass_by_events(self):
        zone = ZoneConfig(
            zone_id="exhibit_a",
            zone_type="exhibit",
            camera_id="camera_1",
            gallery_id="gallery_1",
            points=((0, 0), (10, 0), (10, 10), (0, 10)),
        )
        engine = ZoneEventEngine((zone,), (), ProcessingConfig(dwell_confirm_seconds=10.0, lost_track_grace_seconds=0.5))
        metrics = MetricsEngine((zone,), ())

        for index in range(3):
            track_id = str(index)
            for event in engine.process(float(index * 2), [_track(track_id, 5, 5)]):
                metrics.apply(event)
            for event in engine.process(float(index * 2) + 1.0, [_track(track_id, 20, 20)]):
                metrics.apply(event)

        recommendations = metrics.summary()["recommendations"]
        self.assertTrue(recommendations)
        self.assertEqual(recommendations[0]["type"], "ignored_exhibit")


if __name__ == "__main__":
    unittest.main()
