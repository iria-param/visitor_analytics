import json
import tempfile
import unittest
from pathlib import Path

from scripts.compare_runs import collect_rows, row_from_metrics, split_run_name


class CompareRunsTests(unittest.TestCase):
    def test_split_run_name_recognizes_tracker_suffixes(self):
        self.assertEqual(split_run_name("day1_baseline"), ("day1", "baseline"))
        self.assertEqual(split_run_name("day1_bytetrack_museum"), ("day1", "bytetrack_museum"))
        self.assertEqual(split_run_name("day1_botsort_museum"), ("day1", "botsort_museum"))

    def test_row_from_metrics_flattens_track_diagnostics(self):
        metrics = {
            "track_diagnostics": {
                "unique_track_count": 10,
                "real_track_count": 9,
                "fallback_track_count": 1,
                "duration_seconds": {"median": 2.0, "p25": 1.0, "p75": 3.0, "max": 5.0},
                "short_lived_track_count": 2,
                "likely_id_switch_count": 4,
                "gap_stats": {"total_gaps": 6, "max_gap_processed_frames": 8},
                "tracks_per_minute": 12.5,
            },
            "run_seconds": 30.25,
            "tracker": {"track_buffer": 90},
        }

        row = row_from_metrics("gallery_day1_botsort_museum", metrics)

        self.assertEqual(row["clip_id"], "gallery_day1")
        self.assertEqual(row["tracker"], "botsort_museum")
        self.assertEqual(row["duration_median"], 2.0)
        self.assertEqual(row["likely_switch_count"], 4)
        self.assertEqual(row["track_buffer"], 90)

    def test_collect_rows_reads_metrics_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            runs = Path(temp_dir)
            run_dir = runs / "day1_baseline"
            run_dir.mkdir()
            (run_dir / "metrics_summary.json").write_text(
                json.dumps({"track_diagnostics": {"unique_track_count": 1}}),
                encoding="utf-8",
            )

            rows = collect_rows(runs)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["clip_id"], "day1")
        self.assertEqual(rows[0]["unique_track_count"], 1)


if __name__ == "__main__":
    unittest.main()
