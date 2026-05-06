# Approach 1: Current Baseline

Status: accomplished baseline.

This approach records what has been built so far. It is the working foundation
before we start the next iteration on identity stability and journey analytics.

## What We Built

Approach 1 created a modular offline computer-vision pipeline for museum/gallery
visitor analytics.

Current capabilities:

- process a recorded video file
- detect people using YOLO11n
- track people using Ultralytics tracking with ByteTrack
- draw tracking overlays on an output video
- click zones and entry lines using a calibration web UI
- calculate exhibit dwell time
- calculate pass-by count
- calculate max concurrent visitors in a zone
- count entry-line crossings
- write structured `events.jsonl`
- write `metrics_summary.json`
- run unit tests for core geometry, config, zone events, dwell, occupancy, and
  line crossing behavior

## Current Pipeline

```text
Recorded Video
  -> OpenCV Frame Reader
  -> YOLO11n Person Detector
  -> ByteTrack Tracker
  -> Zone / Line Event Engine
  -> Metrics Engine
  -> Overlay Video + JSON Events + Metrics Summary
```

## Current Code Entry Points

- Package: `src/museum_gallery_ai`
- CLI: `python -m museum_gallery_ai`
- Demo config: `configs/demo.yaml`
- Clicked calibration config: `configs/calibrated.json`
- Tests: `tests`
- VS Code launch/tasks: `.vscode`

Useful commands:

```powershell
.\.venv\Scripts\python -m pytest
```

```powershell
.\.venv\Scripts\python -m museum_gallery_ai calibrate --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output-config configs/calibrated.json
```

```powershell
.\.venv\Scripts\python -m museum_gallery_ai process --config configs/calibrated.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs/calibrated_sample
```

## Validation Completed

The sample recording was processed successfully.

Observed outputs:

- `runs/calibrated_sample/overlay.mp4`
- `runs/calibrated_sample/events.jsonl`
- `runs/calibrated_sample/metrics_summary.json`

Example calibrated metrics from the sample:

```text
processed_frames: 614
entry_count: 1
exhibit_1 total_visitors: 8
exhibit_1 pass_by_count: 22
exhibit_2 total_visitors: 5
exhibit_2 pass_by_count: 7
```

## What Approach 1 Proves

Approach 1 proves that we can:

- run the local development environment
- detect and track people in recorded CCTV-style footage
- create user-defined zones and lines
- calculate first-pass visitor analytics
- produce visible debug evidence through overlay video
- inspect raw tracking events through JSONL

## Known Limitations

Approach 1 is intentionally not final.

Known limitations:

- tracking IDs can change when a detection disappears and comes back
- ByteTrack default settings are not tuned for museum occlusions
- no BoT-SORT / appearance ReID baseline yet
- no ID-switch report yet
- zones are still camera-frame polygons, not a full spatial/floor-plan model
- no floor-plan homography or camera-to-space mapping yet
- no cross-camera journey reconstruction
- no dashboard
- no live CCTV / RTSP integration
- no heatmap output yet
- no optimized zone strategy beyond manual clicking

## Privacy Boundary

Approach 1 does not use:

- face recognition
- demographic guessing
- emotion detection
- microphone input
- cross-camera re-identification
- persistent visitor identity

It uses temporary camera-local track IDs only.

## Related Documentation

- `README.md`
- `docs/MUSEUM_GALLERY_AI_BLUEPRINT.md`
- `docs/architecture/spatial-camera-mapping.md`
- `docs/planning/0001-option-2-modern-cv-pipeline-plan.md`
- `docs/research/0003-open-source-video-analytics-frameworks.md`
