from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from .calibration_app import CalibrationServer
from .config import load_config
from .models import PipelineConfig
from .processor import OfflineProcessor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="museum_gallery_ai", description="Museum Gallery AI analytics pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    process = subparsers.add_parser("process", help="Process one recorded video source")
    process.add_argument("--config", required=True, help="Path to YAML config")
    process.add_argument("--source", required=True, help="Path to recorded video file")
    process.add_argument("--output", required=True, help="Output directory for events, metrics, and overlay")
    process.add_argument("--max-frames", type=int, help="Override processing.max_frames for quick evaluations")
    process.add_argument("--frame-stride", type=int, help="Override processing.frame_stride")
    process.add_argument("--image-size", type=int, help="Override detector.image_size")
    process.add_argument("--no-overlay", action="store_true", help="Skip overlay.mp4 rendering for faster metric runs")
    process.add_argument("--overlay", action="store_true", help="Force overlay.mp4 rendering even if config disables it")

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
        config = _apply_process_overrides(config, args)
        summary = OfflineProcessor(config, args.source, Path(args.output)).run()
        print(f"Processed {summary['processed_frames']} frames")
        print(f"Events: {Path(args.output) / 'events.jsonl'}")
        print(f"Metrics: {Path(args.output) / 'metrics_summary.json'}")
        if config.processing.write_overlay:
            print(f"Overlay: {Path(args.output) / 'overlay.mp4'}")
        else:
            print("Overlay: disabled")
        return 0
    if args.command == "calibrate":
        CalibrationServer(args.source, args.output_config, args.host, args.port).serve(open_browser=not args.no_browser)
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


def _apply_process_overrides(config: PipelineConfig, args: argparse.Namespace) -> PipelineConfig:
    processing = config.processing
    detector = config.detector

    if args.no_overlay and args.overlay:
        raise ValueError("Use either --overlay or --no-overlay, not both")
    if args.max_frames is not None:
        processing = replace(processing, max_frames=args.max_frames)
    if args.frame_stride is not None:
        if args.frame_stride < 1:
            raise ValueError("--frame-stride must be 1 or greater")
        processing = replace(processing, frame_stride=args.frame_stride)
    if args.no_overlay:
        processing = replace(processing, write_overlay=False)
    if args.overlay:
        processing = replace(processing, write_overlay=True)
    if args.image_size is not None:
        if args.image_size < 1:
            raise ValueError("--image-size must be 1 or greater")
        detector = replace(detector, image_size=args.image_size)

    return replace(config, processing=processing, detector=detector)
