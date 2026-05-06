# Museum Gallery AI Blueprint

Status: active product blueprint.

This supersedes the earlier generic Room AI direction. The product is now a
museum/gallery CCTV analytics and camera-only interaction system.

## Product Direction

The system uses existing or dedicated gallery cameras to understand visitor
behavior in museum spaces.

Phase 1 focuses on analytics:

- entry/exit counts
- live occupancy by gallery
- dwell time by exhibit zone
- queue/crowding detection
- heatmaps
- visitor paths
- exhibit engagement score
- ignored exhibits
- congested zones
- time-of-day patterns
- gallery layout recommendations

Phase 2 adds camera-only interaction:

- no microphone
- no visitor app required
- no visitor phone required
- speaker output only
- interaction triggered by observed behavior and museum policy
- content grounded in curator-approved material

## Selected Technical Direction

We will start with Option 2 from the open-source framework research:

> Build a modern custom museum analytics pipeline using open-source computer
> vision components instead of building detection/tracking from scratch.

Core building blocks:

- OpenCV for video capture, frame handling, and lower-level CV utilities.
- A pluggable detector/tracker adapter.
- Roboflow Supervision or equivalent utilities for zones, tracking helpers,
  annotations, and line/polygon events.
- A custom museum analytics domain layer.
- A custom dashboard and debugging surface.

Detector choice remains open until license, accuracy, and deployment constraints
are reviewed. Ultralytics YOLO is a strong prototype candidate, but its AGPL /
commercial licensing must be reviewed before production commitment.

## Why Not Build From Scratch

Detection, tracking, line counting, zone counting, and heatmaps are solved
computer-vision building blocks. Rebuilding them first would waste effort and
make the system harder to debug.

The product value is in museum intelligence:

- turning tracks into exhibit engagement
- detecting ignored exhibits
- understanding congestion and visitor flow
- producing curator/operator recommendations
- making the system explainable and privacy-aware

## MVP Scope

The first MVP should use recorded video or webcam input before integrating
production CCTV.

MVP capabilities:

- load a video source
- detect people
- track people across frames
- define gallery zones
- define exhibit zones
- count entry/exit crossings
- calculate occupancy by zone
- calculate dwell time by exhibit zone
- flag crowded/congested zones
- generate simple heatmap data
- show visitor path traces
- produce a basic dashboard
- show a developer debug panel

MVP non-goals:

- production CCTV/VMS integration
- face recognition
- identity recognition
- demographic guessing
- emotion detection
- long-term individual visitor profiles
- speaker interaction
- AI-generated recommendations without explainable rules

## Domain Model

Core entities:

- Museum
- Gallery
- Camera
- VideoSource
- CameraView
- FloorPlan
- Zone
- Exhibit
- VisitorTrack
- CameraTrack
- TrackEvent
- ZoneVisit
- MetricSnapshot
- Recommendation

Zone types:

- entrance
- exit
- gallery
- exhibit
- queue
- restricted
- pathway

Event types:

- track_started
- track_updated
- track_lost
- zone_entered
- zone_exited
- line_crossed
- dwell_updated
- crowding_detected
- congestion_detected

## Multi-Camera Architecture

Museums will normally need multiple cameras. A single camera can prove the
analytics loop, but the architecture must treat cameras as separate viewpoints
inside one larger gallery system.

### Camera Roles

Different cameras may have different jobs:

- entrance cameras for entry/exit counting
- gallery overview cameras for occupancy and flow
- exhibit-facing cameras for dwell and engagement
- corridor cameras for path transitions between galleries
- queue-area cameras for congestion and waiting patterns
- restricted-zone cameras for safety alerts

### Camera Independence First

Each camera should process its own stream independently at first:

```text
Camera Stream
  -> Frame Reader
  -> Detector
  -> Tracker
  -> Camera-Local Events
```

Camera-local events are then normalized into museum-level analytics:

```text
Camera-Local Events
  -> Spatial Mapping
  -> Gallery/Event Fusion
  -> Museum Metrics
```

This keeps the system easier to debug. If one camera fails, the rest of the
system can still work.

### Camera Calibration

Each camera needs configuration:

- camera ID
- physical location
- gallery or room assignment
- stream URL or file source
- frame size and orientation
- zone polygons
- entrance/exit lines
- optional mapping from image coordinates to floor-plan coordinates

For early prototypes, zones can be drawn directly on camera frames. For better
multi-camera analytics, camera views should later be mapped to a shared
floor-plan coordinate system.

See [Spatial Camera Mapping](architecture/spatial-camera-mapping.md) for the
systems-thinking model of how camera views become gallery/path understanding.

### Cross-Camera Visitor Tracking

Do not start with cross-camera identity tracking.

Cross-camera re-identification is hard and privacy-sensitive. It can create
legal, ethical, and trust problems because it tries to follow the same person
across multiple cameras.

Phase 1 should use anonymous camera-local track IDs and aggregate metrics.

Allowed early approach:

- Camera A says 10 people exited Gallery 1 toward Gallery 2.
- Camera B says 9 people entered Gallery 2 shortly after.
- The system estimates gallery flow statistically.

Avoid early:

- face recognition
- person re-identification
- persistent visitor identity
- demographic guessing
- tracking a named or identifiable person across cameras

### Event Fusion

Museum-level analytics should be built from events, not raw camera frames.

Examples:

- entrance camera emits `line_crossed`
- exhibit camera emits `zone_entered`, `dwell_updated`, `zone_exited`
- gallery camera emits `occupancy_snapshot`
- queue camera emits `crowding_detected`

The fusion layer combines these events by:

- camera ID
- gallery ID
- zone ID
- timestamp
- event type
- confidence

### Failure Handling

Multi-camera systems must tolerate partial failure.

If one camera goes offline:

- mark affected metrics as partial
- keep other cameras running
- show camera health in the dashboard
- avoid pretending gallery-wide analytics are complete

### Scaling Path

1. Single recorded video.
2. Multiple recorded videos processed independently.
3. Multiple live camera streams.
4. Gallery-level event fusion.
5. Floor-plan heatmaps.
6. Optional privacy-reviewed cross-camera flow estimation.
7. Only if truly necessary, evaluate re-identification under strict legal and
   ethical review.

## Metrics

### Entry/Exit Count

Count tracked people crossing configured entrance and exit lines.

### Live Occupancy

Calculate current active tracks inside each gallery or zone.

### Dwell Time

Measure how long a tracked person remains inside an exhibit zone.

### Queue/Crowding Detection

Detect when too many tracks remain in a queue/crowd zone for too long.

### Heatmaps

Aggregate track positions over time into a spatial density grid.

### Visitor Paths

Store simplified path points for each anonymous track during a session.

### Exhibit Engagement Score

Start with an explainable rule:

```text
engagement = weighted dwell time + repeat visits + group density near exhibit
```

Do not use facial analysis, emotion detection, or identity recognition.

### Ignored Exhibits

An exhibit may be flagged as ignored when traffic near the exhibit is high but
dwell time or engagement is low.

### Congested Zones

Flag zones with sustained occupancy above a configured threshold.

### Time-Of-Day Patterns

Aggregate metrics by time bucket, such as 15 minutes, 1 hour, day, and week.

### Gallery Layout Recommendations

Start rule-based, not generative:

- high congestion near narrow pathway -> review circulation
- high pass-by and low dwell near exhibit -> improve placement or signage
- high dwell and repeated crowding -> consider more space or duplicate context
- ignored exhibit near high-traffic route -> review label visibility or lighting

## Debugging Requirements

The system must expose what it thinks and why.

Developer debug views should include:

- current video source state
- detector/tracker status
- frame processing time
- detected person boxes
- track IDs
- zone boundaries
- line crossings
- zone enter/exit events
- dwell calculations
- occupancy calculations
- recommendation evidence
- dropped frames and errors

## Privacy Boundaries

Default design:

- process video for anonymous tracks and aggregate metrics
- do not identify faces
- do not infer demographics
- do not store raw video by default
- do not store individual visitor identity
- keep track IDs temporary and anonymous
- prefer derived metrics over images/video retention

## Phase Plan

### Phase 1A: Offline Video Analytics Prototype

- recorded video input
- people detection/tracking
- zone configuration by code or simple UI
- counts, occupancy, dwell, heatmap, paths
- debug overlay

### Phase 1B: Museum Dashboard

- gallery/exhibit model
- daily analytics
- engagement and ignored exhibit reports
- congestion report
- simple layout recommendations

### Phase 1C: CCTV Integration

- RTSP/camera adapter
- camera calibration
- multi-camera support
- deployment/runtime monitoring

### Phase 2: Camera-Only Speaker Interaction

- behavior trigger engine
- curator-approved content library
- speaker output
- no microphone
- opt-in/signage policy
- interaction audit logs

## Open Decisions

- Which detector/tracker should be used first?
- Should the prototype use recorded museum-like footage, webcam footage, or
  synthetic test footage?
- Should the dashboard be a local web app first?
- Should raw video ever be stored?
- Which jurisdiction/privacy standard applies to the first deployment?
- What camera feed protocol will the first museum provide?
