# Plan 0001: Option 2 Modern CV Pipeline

Status: proposed plan for discussion.

## Decision Already Chosen

The selected direction is Option 2:

> Build a custom museum analytics product using modern open-source
> computer-vision components, while owning the museum-specific analytics layer.

This avoids building detection/tracking from scratch while still giving us a
clean architecture for museum-specific behavior.

## Product Goal

Build a museum/gallery analytics system that transforms camera footage into
understandable visitor insights:

- how many visitors entered/exited
- where visitors spend time
- which exhibits attract attention
- which exhibits are ignored
- where crowding happens
- how visitor flow changes by time
- what layout changes may improve experience

## MVP Goal

Create an offline video analytics prototype that can process one video source
and produce explainable metrics.

MVP output should include:

- processed video overlay
- event log
- basic metrics summary
- zone-level analytics
- developer debug information

## Architecture

```text
Camera / Video Source
  -> Frame Reader
  -> Detector Adapter
  -> Tracker Adapter
  -> Camera-Local Zone/Event Engine
  -> Event Fusion Layer
  -> Metrics Engine
  -> Museum Analytics Engine
  -> Dashboard/API
```

The first implementation slice can use one recorded video, but the architecture
must be camera-aware from the start. A single camera is a special case of the
multi-camera system, not a separate design.

## Component Responsibilities

### Video Source Adapter

Inputs:

- recorded video file first
- webcam second
- RTSP/CCTV later

Responsibilities:

- open source
- read frames
- timestamp frames
- handle end-of-stream and errors
- report FPS and dropped frames
- identify which camera/source produced each frame

### Detector Adapter

Responsibilities:

- detect people in frames
- hide model-specific details behind an interface
- return bounding boxes, confidence, and class labels

Initial detector:

- To be decided after license review.
- Ultralytics YOLO is a likely prototype candidate.
- A non-AGPL detector should be considered for commercial flexibility.

### Tracker Adapter

Responsibilities:

- associate detections across frames
- produce temporary anonymous track IDs
- handle lost/reappearing tracks
- expose confidence and track state

### Zone/Event Engine

Responsibilities:

- represent entrance/exit lines
- represent gallery/exhibit/queue polygons
- detect line crossings
- detect zone enter/exit
- update dwell timers
- emit structured events
- attach camera ID, gallery ID, zone ID, timestamp, and confidence to events

### Event Fusion Layer

Responsibilities:

- combine camera-local events into museum-level metrics
- keep camera streams independent for debugging and fault isolation
- aggregate by camera, gallery, zone, and time bucket
- mark metrics as partial when a camera is offline or unreliable
- later support floor-plan coordinate mapping

Do not start with cross-camera person identity tracking. Use anonymous
camera-local track IDs first and derive aggregate flow patterns from time and
zone events.

### Metrics Engine

Responsibilities:

- entry/exit counts
- live occupancy
- dwell time
- heatmap grids
- visitor path summaries
- congestion thresholds
- time bucket aggregation

### Museum Analytics Engine

Responsibilities:

- exhibit engagement score
- ignored exhibit detection
- congested zone reporting
- time-of-day insights
- rule-based gallery layout recommendations

### Dashboard/API

Responsibilities:

- show video overlay
- show zone map
- show metrics
- show event log
- show debug details
- export reports later

## Data We Should Store First

Store derived data, not raw video:

- frame timestamp
- anonymous track ID
- bounding box center point
- zone enter/exit events
- line crossing events
- dwell durations
- aggregate metrics
- recommendation evidence

Avoid storing:

- faces
- identity
- demographic labels
- raw video by default
- cropped person images

## First Implementation Slice

Build the smallest slice that proves the core loop:

1. Load a local recorded video.
2. Detect people.
3. Track people.
4. Draw track boxes/IDs.
5. Define one entrance line and one exhibit zone in config.
6. Count line crossings.
7. Calculate dwell time inside the exhibit zone.
8. Print/export structured events.
9. Show a simple overlay/debug output.

The code should still model the source as a `Camera` or `VideoSource` with an
ID, so the second slice can add another camera/video without redesigning the
event model.

This validates:

- video ingestion
- detector integration
- tracking
- line/zone math
- event model
- debug visibility

## Proposed Tech Stack For First Slice

Backend / analytics:

- Python
- OpenCV
- Supervision
- detector/tracker adapter interface

Dashboard:

- start simple
- either a Python-generated debug video/report or a lightweight local web UI
- full web dashboard after the pipeline is proven

Data:

- JSONL event log first
- SQLite later for local analytics
- Postgres only when multi-user/server deployment is needed

## Risks

### License Risk

Ultralytics is powerful but has AGPL/commercial licensing implications.

Mitigation:

- keep detector behind an adapter
- document license decision before production
- consider MIT/Apache-compatible alternatives

### Accuracy Risk

Museum camera angles, occlusion, lighting, reflections, and crowds may reduce
tracking accuracy.

Mitigation:

- start with recorded footage
- keep debug overlays
- measure false counts
- design calibration tools

### Privacy Risk

CCTV footage can contain identifiable people.

Mitigation:

- derived metrics first
- no face recognition
- no raw video storage by default
- anonymous temporary tracks
- privacy review before real deployment

### Product Risk

Generic people counting is already commoditized.

Mitigation:

- focus on exhibit-level engagement and museum decisions
- build recommendation evidence, not only dashboards

## Testing Strategy

Early tests:

- geometry tests for line crossing
- polygon zone enter/exit tests
- dwell-time calculation tests
- occupancy aggregation tests
- engagement score rule tests
- ignored exhibit rule tests

Manual validation:

- run on sample video
- inspect overlay
- compare counted events with human observation

## Discussion Questions

Before implementation, confirm:

1. Should first input be a recorded video file?
2. Should we start with Python-only pipeline before any web dashboard?
3. Are we allowed to use Ultralytics for prototype while keeping detector
   replaceable?
4. Should raw video storage be disabled by default?
5. Is the first useful demo a processed video overlay plus JSON metrics, or a
   web dashboard?
6. For multi-camera planning, should the first museum model assume one camera
   per gallery, or multiple cameras per gallery?
7. Should cross-camera tracking be explicitly out of scope for Phase 1 and
   replaced with aggregate flow estimation?

## Recommendation

Start with the offline video analytics slice.

Do not build the full dashboard first. The core risk is whether we can reliably
turn camera footage into explainable events and metrics. Once that loop works,
the dashboard becomes much easier and more honest.
