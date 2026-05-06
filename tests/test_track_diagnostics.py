import unittest

from museum_gallery_ai.models import LineConfig, ProcessingConfig, TrackObservation, ZoneConfig
from museum_gallery_ai.track_diagnostics import TrackDiagnostics


def _track(track_id: str, foot_x: float, foot_y: float) -> TrackObservation:
    return TrackObservation(track_id=track_id, bbox=(foot_x - 1, foot_y - 2, 2, 2), confidence=0.9)


class TrackDiagnosticsTests(unittest.TestCase):
    def test_empty_run_summary_is_safe(self):
        diagnostics = TrackDiagnostics(ProcessingConfig())

        summary = diagnostics.summary((), ())

        self.assertEqual(summary["unique_track_count"], 0)
        self.assertEqual(summary["real_track_count"], 0)
        self.assertEqual(summary["duration_seconds"]["mean"], None)
        self.assertEqual(summary["tracks_per_minute"], 0.0)
        self.assertEqual(summary["likely_id_switch_count"], 0)

    def test_real_and_fallback_tracks_are_reported_separately(self):
        diagnostics = TrackDiagnostics(ProcessingConfig(short_lived_track_seconds=1.0))
        diagnostics.observe(0.0, 0, [_track("1", 10, 10), _track("tmp_1_1", 30, 30)])
        diagnostics.observe(2.0, 1, [_track("1", 12, 12), _track("tmp_1_1", 31, 31)])

        summary = diagnostics.summary((), ())

        self.assertEqual(summary["unique_track_count"], 2)
        self.assertEqual(summary["real_track_count"], 1)
        self.assertEqual(summary["fallback_track_count"], 1)
        self.assertEqual(summary["duration_seconds"]["mean"], 2.0)
        self.assertEqual(summary["short_lived_track_count"], 0)

    def test_short_lived_tracks_are_counted_by_threshold(self):
        diagnostics = TrackDiagnostics(ProcessingConfig(short_lived_track_seconds=1.0))
        diagnostics.observe(0.0, 0, [_track("1", 10, 10), _track("2", 20, 20)])
        diagnostics.observe(0.5, 1, [_track("1", 11, 11)])
        diagnostics.observe(2.0, 2, [_track("1", 12, 12)])

        summary = diagnostics.summary((), ())

        self.assertEqual(summary["real_track_count"], 2)
        self.assertEqual(summary["short_lived_track_count"], 1)
        self.assertEqual(summary["duration_seconds"]["max"], 2.0)

    def test_gap_detection_uses_processed_frame_indices(self):
        diagnostics = TrackDiagnostics(ProcessingConfig())
        diagnostics.observe(0.0, 0, [_track("1", 10, 10)])
        diagnostics.observe(1.0, 1, [_track("1", 11, 10)])
        diagnostics.observe(4.0, 4, [_track("1", 12, 10)])
        diagnostics.observe(7.0, 7, [_track("1", 13, 10)])

        summary = diagnostics.summary((), ())

        self.assertEqual(summary["gap_stats"]["tracks_with_gaps"], 1)
        self.assertEqual(summary["gap_stats"]["total_gaps"], 2)
        self.assertEqual(summary["gap_stats"]["mean_gap_processed_frames"], 2.0)
        self.assertEqual(summary["gap_stats"]["max_gap_processed_frames"], 2)

    def test_likely_id_switch_heuristic_excludes_fallback_ids(self):
        processing = ProcessingConfig(id_switch_window_seconds=2.0, id_switch_distance_pixels=20.0)
        diagnostics = TrackDiagnostics(processing)
        diagnostics.observe(0.0, 0, [_track("1", 100, 100), _track("tmp_5_5", 200, 200)])
        diagnostics.observe(1.0, 1, [_track("1", 110, 100)])
        diagnostics.observe(2.0, 2, [_track("2", 115, 105), _track("tmp_6_6", 205, 205)])

        summary = diagnostics.summary((), ())

        self.assertEqual(summary["likely_id_switch_count"], 1)
        self.assertEqual(summary["fallback_track_count"], 2)

    def test_fragmentation_hotspots_count_zone_line_and_outside(self):
        zone = ZoneConfig(
            zone_id="exhibit_a",
            zone_type="exhibit",
            camera_id="camera_1",
            gallery_id="gallery_1",
            points=((0, 0), (40, 0), (40, 40), (0, 40)),
        )
        line = LineConfig(
            line_id="entry_line",
            line_type="entry",
            camera_id="camera_1",
            gallery_id="gallery_1",
            start=(50, 0),
            end=(50, 100),
        )
        diagnostics = TrackDiagnostics(ProcessingConfig(line_fragmentation_buffer_pixels=10.0))
        diagnostics.observe(0.0, 0, [_track("1", 20, 20), _track("2", 55, 30)])
        diagnostics.observe(1.0, 1, [_track("1", 55, 20), _track("2", 90, 30)])

        hotspots = diagnostics.summary((zone,), (line,))["fragmentation_hotspots"]

        self.assertEqual(hotspots["by_zone"]["exhibit_a"]["track_starts"], 1)
        self.assertEqual(hotspots["by_zone"]["exhibit_a"]["track_ends"], 0)
        self.assertEqual(hotspots["by_line"]["entry_line"]["track_starts_within_buffer"], 1)
        self.assertEqual(hotspots["by_line"]["entry_line"]["track_ends_within_buffer"], 1)
        self.assertEqual(hotspots["outside_any_zone"]["track_starts"], 1)
        self.assertEqual(hotspots["outside_any_zone"]["track_ends"], 2)


if __name__ == "__main__":
    unittest.main()
