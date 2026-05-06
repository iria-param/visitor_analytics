from __future__ import annotations

import argparse
from pathlib import Path

from .calibration_app import CalibrationServer
from .config import load_config
from .processor import OfflineProcessor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="museum_gallery_ai", description="Museum Gallery AI analytics pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", help="Process one recorded video source")
    process.add_argument("--config", required=True, help="Path to YAML config")
    process.add_argument("--source", required=True, help="Path to recorded video file")
    process.add_argument("--output", required=True, help="Output directory for events, metrics, and overlay")

    calibrate = subparsers.add_parser("calibrate", help="Open a browser UI to click zones and lines")
    calibrate.add_argument("--source", required=True, help="Path to recorded video file")
    calibrate.add_argument("--output-config", default="configs/calibrated.json", help="Where to save the clicked config")
    calibrate.add_argument("--host", default="127.0.0.1", help="Calibration server host")
    calibrate.add_argument("--port", type=int, default=8765, help="Calibration server port")
    calibrate.add_argument("--no-browser", action="store_true", help="Do not automatically open the browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "process":
        config = load_config(args.config, source_override=args.source)
        summary = OfflineProcessor(config, args.source, Path(args.output)).run()
        print(f"Processed {summary['processed_frames']} frames")
        print(f"Events: {Path(args.output) / 'events.jsonl'}")
        print(f"Metrics: {Path(args.output) / 'metrics_summary.json'}")
        print(f"Overlay: {Path(args.output) / 'overlay.mp4'}")
        return 0
    if args.command == "calibrate":
        CalibrationServer(args.source, args.output_config, args.host, args.port).serve(open_browser=not args.no_browser)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2
