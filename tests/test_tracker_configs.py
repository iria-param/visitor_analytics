"""Schema checks for the museum-tuned tracker YAML files.

These tests do not run Ultralytics. They only verify that the YAML files
parse and contain the fields Ultralytics requires, so a typo or missing
field is caught before a long pipeline run uses them.

Schema reference (verified at write time):
  .venv/Lib/site-packages/ultralytics/cfg/trackers/bytetrack.yaml
  .venv/Lib/site-packages/ultralytics/cfg/trackers/botsort.yaml
"""
from __future__ import annotations

from pathlib import Path
import unittest

import yaml


CONFIG_DIR = Path("configs/trackers")

# Fields shared by both tracker types in the Ultralytics schema.
SHARED_REQUIRED_FIELDS = {
    "tracker_type": str,
    "track_high_thresh": (int, float),
    "track_low_thresh": (int, float),
    "new_track_thresh": (int, float),
    "track_buffer": int,
    "match_thresh": (int, float),
    "fuse_score": bool,
}

# BoT-SORT-only fields.
BOTSORT_EXTRA_REQUIRED_FIELDS = {
    "gmc_method": str,
    "proximity_thresh": (int, float),
    "appearance_thresh": (int, float),
    "with_reid": bool,
    "model": str,
}


def _load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise AssertionError(f"{path} did not parse to a mapping")
    return data


class TrackerConfigSchemaTests(unittest.TestCase):
    def _assert_required(self, data: dict, required: dict, path: Path) -> None:
        for field, expected_type in required.items():
            self.assertIn(field, data, f"{path}: missing required field '{field}'")
            self.assertIsInstance(
                data[field],
                expected_type,
                f"{path}: field '{field}' has wrong type ({type(data[field]).__name__})",
            )

    def test_bytetrack_museum_schema(self):
        path = CONFIG_DIR / "bytetrack_museum.yaml"
        data = _load(path)
        self.assertEqual(
            data.get("tracker_type"),
            "bytetrack",
            f"{path}: tracker_type must be 'bytetrack'",
        )
        self._assert_required(data, SHARED_REQUIRED_FIELDS, path)

    def test_botsort_museum_schema(self):
        path = CONFIG_DIR / "botsort_museum.yaml"
        data = _load(path)
        self.assertEqual(
            data.get("tracker_type"),
            "botsort",
            f"{path}: tracker_type must be 'botsort'",
        )
        self._assert_required(data, SHARED_REQUIRED_FIELDS, path)
        self._assert_required(data, BOTSORT_EXTRA_REQUIRED_FIELDS, path)

    def test_botsort_museum_reid_disabled_by_default(self):
        # Privacy guard. The project privacy policy requires explicit review
        # before ReID can be turned on. If someone flips this to True without
        # adding the corresponding ADR, this test is the trip-wire.
        path = CONFIG_DIR / "botsort_museum.yaml"
        data = _load(path)
        self.assertFalse(
            data.get("with_reid"),
            f"{path}: with_reid must remain False until privacy review is recorded",
        )

    def test_museum_track_buffer_is_extended(self):
        # The headline Approach 2 Step 1 delta. If someone reverts these to
        # the Ultralytics default of 30, the museum tuning is gone and we
        # should know.
        for name in ("bytetrack_museum.yaml", "botsort_museum.yaml"):
            path = CONFIG_DIR / name
            data = _load(path)
            self.assertGreaterEqual(
                data["track_buffer"],
                60,
                f"{path}: track_buffer should be >= 60 (museum tuning); got {data['track_buffer']}",
            )


if __name__ == "__main__":
    unittest.main()
