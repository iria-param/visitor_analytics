# Museum Gallery AI

Museum Gallery AI is a planned CCTV/camera-based visitor analytics system for
museums and galleries. Phase 1 focuses on visitor analytics from camera feeds.
Phase 2 adds camera-only speaker interaction with no microphone.

The project is currently in the research and architecture stage. We are not
jumping directly into implementation. The working rule is:

```text
Research first. Plan next. Discuss together. Build after agreement.
```

## Start Here

- [Project Start Workflow](docs/PROJECT_START_WORKFLOW.md): mandatory workflow
  for research, planning, discussion, and implementation.
- [Foundation Research](docs/research/0001-room-ai-foundation-research.md):
  first authentic-source research brief for Room AI.
- [Museum CCTV Analytics Research](docs/research/0002-museum-cctv-visitor-analytics-existing-systems.md):
  research on existing museum CCTV analytics and camera-only interaction systems.
- [Open Source Video Analytics Frameworks](docs/research/0003-open-source-video-analytics-frameworks.md):
  research on reusable open-source foundations for visitor analytics.
- [Approach 2 Tracking/ReID Research](docs/research/0004-approach-2-tracking-reid-frameworks.md):
  research on existing ID-stability, ReID, and multi-camera tracking frameworks.
- [Coding Standards](CODING_STANDARDS.md): engineering standards for
  production-quality, understandable, debuggable code.
- [Museum Gallery AI Blueprint](docs/MUSEUM_GALLERY_AI_BLUEPRINT.md): active
  product and architecture direction.
- [Spatial Camera Mapping](docs/architecture/spatial-camera-mapping.md):
  systems-thinking design for mapping cameras to museum space and pathways.
- [Option 2 Modern CV Pipeline Plan](docs/planning/0001-option-2-modern-cv-pipeline-plan.md):
  proposed implementation plan for discussion.
- [Approach 1: Current Baseline](docs/approaches/approach_1_current_baseline.md):
  what has been accomplished in code and documentation so far.
- [Approach 2: Identity Stability And Journey Tracking](docs/approaches/approach_2_identity_stability_and_journey_tracking.md):
  next planned direction for better track IDs and anonymous visitor journeys.
- [Architecture Decision Records](docs/adr): decisions and tradeoffs.
- [Agent Instructions](CLAUDE.md): instructions for Codex and other coding
  agents working in this repository.

## Current Product Direction

The selected direction is Option 2:

```text
Build a custom museum analytics product using modern open-source computer-vision
components, while owning the museum-specific analytics layer.
```

The first MVP should process a recorded video or simple camera feed before
production CCTV integration.

Initial focus:

- people detection and tracking
- entry/exit counts
- occupancy by gallery/zone
- dwell time by exhibit zone
- heatmaps and visitor paths
- crowding/congestion signals
- basic exhibit engagement and ignored exhibit rules
- debug overlays and event logs

The MVP deliberately avoids face recognition, identity tracking, demographic
guessing, emotion detection, microphone input, and raw video storage by default.

## First Build

The first code slice is a modular offline Python pipeline.

Install dependencies in the project virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pip install -e .
```

Run the processor:

```powershell
.\.venv\Scripts\python -m museum_gallery_ai process --config configs/demo.yaml --source path\to\video.mp4 --output runs/demo
```

Expected outputs:

```text
runs/demo/events.jsonl
runs/demo/metrics_summary.json
runs/demo/overlay.mp4
```

Run unit tests:

```powershell
.\.venv\Scripts\python -m pytest
```

## VS Code Workflow

Open this folder in VS Code:

```powershell
code "C:\Users\Admin\Documents\New project"
```

VS Code is configured to use:

```text
.venv\Scripts\python.exe
```

To watch how the video is tracked:

1. Open the **Run and Debug** panel.
2. Choose **Process sample recording**.
3. Press **F5**.
4. Wait for processing to finish.
5. Open:

```text
runs/vscode_sample/overlay.mp4
```

That overlay video shows:

- detected person boxes
- track IDs
- confidence values
- exhibit zone polygon
- entry line
- current entry/exit counters

The raw event stream is here:

```text
runs/vscode_sample/events.jsonl
```

The metrics summary is here:

```text
runs/vscode_sample/metrics_summary.json
```

## Mark Zones By Clicking

Use the calibration UI to click zones and lines on a frame from the video:

```powershell
.\.venv\Scripts\python -m museum_gallery_ai calibrate --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output-config configs/calibrated.json
```

Open the shown local URL if the browser does not open automatically:

```text
http://127.0.0.1:8765
```

In the browser:

1. Choose **Draw Exhibit Zone**.
2. Click around the exhibit/gallery area.
3. Click **Finish Shape**.
4. Choose **Draw Entry Line**.
5. Click two points across the entrance/pathway.
6. Click **Save Config**.

Then process the video with your clicked config:

```powershell
.\.venv\Scripts\python -m museum_gallery_ai process --config configs/calibrated.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs/calibrated_sample
```

Open:

```text
runs/calibrated_sample/overlay.mp4
```

## Development Philosophy

This project should help developers understand what is happening behind the
scenes. Code should not merely work; it should be readable, observable,
testable, and debuggable.

Architecture decisions should use systems thinking: boundaries, flows, feedback
loops, delays, incentives, failure modes, and leverage points.

## Repository Status

Approach 1 has a working offline Python pipeline. The next coding iteration is
Approach 2: improving tracking ID stability before anonymous cross-camera
journey reconstruction.
