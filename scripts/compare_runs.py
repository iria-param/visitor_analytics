from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


FIELDNAMES = [
    "clip_id",
    "tracker",
    "unique_track_count",
    "real_track_count",
    "fallback_track_count",
    "duration_median",
    "duration_p25",
    "duration_p75",
    "duration_max",
    "short_lived_count",
    "likely_switch_count",
    "total_gaps",
    "max_gap_processed_frames",
    "tracks_per_minute",
    "run_seconds",
    "track_buffer",
]

TRACKER_SUFFIXES = {
    "bytetrack_museum": "bytetrack_museum",
    "botsort_museum": "botsort_museum",
    "baseline": "baseline",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare Museum Gallery AI run diagnostics.")
    parser.add_argument("--runs", required=True, help="Directory containing run subdirectories.")
    parser.add_argument("--out", required=True, help="CSV output path.")
    parser.add_argument("--expected-runs", type=int, help="Fail if this many metrics files are not found.")
    args = parser.parse_args(argv)

    rows = collect_rows(Path(args.runs))
    if args.expected_runs is not None and len(rows) != args.expected_runs:
        raise SystemExit(f"Expected {args.expected_runs} runs, found {len(rows)}.")

    out_csv = Path(args.out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    write_csv(out_csv, rows)
    out_json = out_csv.with_suffix(".json")
    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} rows to {out_csv}")
    print(f"Wrote {len(rows)} rows to {out_json}")
    return 0


def collect_rows(runs_dir: Path) -> list[dict[str, Any]]:
    metrics_paths = sorted(runs_dir.glob("*/metrics_summary.json"))
    rows = []
    for metrics_path in metrics_paths:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        rows.append(row_from_metrics(metrics_path.parent.name, metrics))
    return rows


def row_from_metrics(run_name: str, metrics: dict[str, Any]) -> dict[str, Any]:
    diagnostics = metrics.get("track_diagnostics") or {}
    durations = diagnostics.get("duration_seconds") or {}
    gaps = diagnostics.get("gap_stats") or {}
    clip_id, tracker = split_run_name(run_name)
    return {
        "clip_id": clip_id,
        "tracker": tracker,
        "unique_track_count": diagnostics.get("unique_track_count", 0),
        "real_track_count": diagnostics.get("real_track_count", 0),
        "fallback_track_count": diagnostics.get("fallback_track_count", 0),
        "duration_median": durations.get("median"),
        "duration_p25": durations.get("p25"),
        "duration_p75": durations.get("p75"),
        "duration_max": durations.get("max"),
        "short_lived_count": diagnostics.get("short_lived_track_count", 0),
        "likely_switch_count": diagnostics.get("likely_id_switch_count", 0),
        "total_gaps": gaps.get("total_gaps", 0),
        "max_gap_processed_frames": gaps.get("max_gap_processed_frames", 0),
        "tracks_per_minute": diagnostics.get("tracks_per_minute", 0.0),
        "run_seconds": metrics.get("run_seconds"),
        "track_buffer": metrics.get("tracker", {}).get("track_buffer"),
    }


def split_run_name(run_name: str) -> tuple[str, str]:
    for suffix, tracker in TRACKER_SUFFIXES.items():
        marker = f"_{suffix}"
        if run_name.endswith(marker):
            return run_name[: -len(marker)], tracker
    return run_name, "unknown"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    raise SystemExit(main())
