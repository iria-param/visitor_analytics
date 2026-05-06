# Open Source Video Analytics Frameworks Research

Date: 2026-05-05

Status: research brief, not an implementation plan.

## Question

Is there an open-source framework we can directly implement and modify instead
of building the museum visitor analytics system from scratch?

Desired capabilities:

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

## Short Answer

No single mature open-source framework was found that does the full museum
analytics product end to end.

The closest options are:

1. Use OpenDataCam as an old but relevant full-app reference/fork candidate.
2. Build a modern custom system using Ultralytics YOLO + Supervision + OpenCV.
3. Use Frigate as a camera/NVR ingestion and object-event layer, then build
   museum analytics separately.

Best current recommendation:

> Do not build detection/tracking from scratch. Build the product around proven
> open-source computer-vision components, but create our own museum analytics
> domain layer, dashboard, and recommendation logic.

## Candidate 1: OpenDataCam

Source: https://github.com/opendatacam/opendatacam

Source: https://opendata.cam/

License: MIT, according to the GitHub repository.

What it is:

- An open-source tool to quantify moving objects in videos and camera feeds.
- It detects objects, tracks them, lets users define counters, and records
  counts when objects cross those counters.
- It supports real-time and pre-recorded video sources.
- It includes trajectory analysis and an API.
- It emphasizes local processing and not saving photo/video data.

Strengths:

- Closest "full application" match.
- Has UI, API, counting, tracking, and trajectory concepts.
- Good privacy posture for derived metadata over raw video.
- Useful for learning how an end-to-end open video analytics product is shaped.

Weaknesses:

- Latest GitHub release shown in repository metadata is v3.0.2 from 2021.
- Built around older YOLO/Darknet ecosystem.
- Not museum-specific.
- Does not appear to directly provide exhibit engagement scores, ignored
  exhibit detection, gallery layout recommendations, or modern AI interaction.

Fit:

- Good reference or fork candidate if we want a fast proof of concept.
- Risky as the main long-term production foundation without modernization.

## Candidate 2: Ultralytics YOLO Solutions

Source: https://docs.ultralytics.com/

Source: https://docs.ultralytics.com/guides/object-counting/

Source: https://docs.ultralytics.com/guides/region-counting/

Source: https://docs.ultralytics.com/guides/heatmaps/

Source: https://docs.ultralytics.com/guides/queue-management/

Source: https://docs.ultralytics.com/guides/trackzone/

Source: https://docs.ultralytics.com/modes/track/

Source: https://github.com/ultralytics/ultralytics

License note:

- Ultralytics states that YOLO is available under AGPL-3.0 and an Enterprise
  License.
- For commercial deployment, licensing must be reviewed before committing to
  this stack.

What it is:

- A modern computer-vision framework for detection, segmentation, pose,
  classification, and tracking.
- Official docs include object counting, region counting, heatmaps, queue
  management, and track-zone examples.
- Tracking supports live streams and video sources.

Strengths:

- Strong modern detection/tracking base.
- Good official examples for several requested metrics.
- Suitable for prototypes and production if license is acceptable.
- Actively maintained.

Weaknesses:

- It is not a complete museum analytics product.
- It does not provide a museum dashboard, exhibit model, recommendation engine,
  retention/privacy layer, or business workflow out of the box.
- AGPL/commercial licensing needs serious review.

Fit:

- Strongest technical building block for detection/tracking/zone analytics.
- Best combined with our own analytics service and dashboard.

## Candidate 3: Roboflow Supervision

Source: https://github.com/roboflow/supervision

Source: https://supervision.roboflow.com/latest/detection/tools/line_zone/

Source: https://supervision.roboflow.com/latest/detection/tools/polygon_zone/

Source: https://supervision.roboflow.com/latest/trackers/

License: MIT, according to the GitHub repository.

What it is:

- A Python computer-vision utility library.
- It is model-agnostic and provides reusable tools for detections, annotations,
  tracking, line zones, polygon zones, and dataset utilities.
- Documentation includes `LineZone` for in/out crossing counts and `PolygonZone`
  for zone-based detection/counting.

Strengths:

- MIT license is easier for commercial products than AGPL.
- Good for building our own analytics pipeline.
- Model-agnostic: can work with multiple detectors.
- Useful abstractions for zones and tracking.

Weaknesses:

- Not a complete application.
- No museum dashboard or analytics product out of the box.
- We still need video ingestion, persistence, APIs, dashboard, calibration,
  privacy controls, and recommendations.

Fit:

- Excellent library layer for custom implementation.
- Strong pairing with YOLO, RT-DETR, RF-DETR, or another detector.

## Candidate 4: Frigate

Source: https://docs.frigate.video/

Source: https://docs.frigate.video/configuration/zones/

Source: https://github.com/blakeblackshear/frigate

License: MIT, according to the GitHub repository.

What it is:

- A local NVR for IP cameras with realtime AI object detection.
- Uses OpenCV and TensorFlow for local object detection.
- Has RTSP restreaming, WebRTC/MSE live view, MQTT integration, zones, masks,
  object events, and a UI.

Strengths:

- Strong IP camera/NVR foundation.
- Good for camera integration, zones, live view, events, and local processing.
- MIT license.
- Active project with recent releases.

Weaknesses:

- Designed mainly for home/security NVR use, not museum analytics.
- It has zones and loitering, but not a full visitor analytics or exhibit
  engagement dashboard.
- Adapting the UI/product model may be more work than using it as an event
  source.

Fit:

- Good if our first problem is reliable camera ingestion and object events from
  existing IP cameras.
- Less ideal if we need a custom museum analytics product quickly.

## Candidate 5: OpenCV

Source: https://opencv.org/

Source: https://docs.opencv.org/

What it is:

- A major open-source computer-vision library.
- Useful for video capture, image processing, calibration, geometric transforms,
  drawing overlays, and lower-level CV operations.

Strengths:

- Stable foundation.
- Useful for RTSP/video handling and frame processing.
- Works with most Python CV stacks.

Weaknesses:

- Too low-level to be the product framework by itself.
- Does not directly provide museum analytics.

Fit:

- Supporting library, not the main product framework.

## Feature Coverage Matrix

| Capability | OpenDataCam | Ultralytics | Supervision | Frigate | Custom Domain Layer Needed |
| --- | --- | --- | --- | --- | --- |
| Entry/exit counts | Yes | Yes | Yes | Partial | Calibration/rules |
| Live occupancy by gallery | Partial | Buildable | Buildable | Partial | Yes |
| Dwell time by exhibit zone | Partial/buildable | Buildable | Buildable | Loitering-like partial | Yes |
| Queue/crowding detection | Partial | Yes/examples | Buildable | Partial | Yes |
| Heatmaps | Partial/paths | Yes/examples | Buildable | No/limited | Yes |
| Visitor paths | Yes trajectories | Tracking buildable | Tracking buildable | Events/tracks partial | Yes |
| Exhibit engagement score | No | No | No | No | Yes |
| Ignored exhibits | No | No | No | No | Yes |
| Congested zones | Buildable | Buildable | Buildable | Buildable | Yes |
| Time-of-day patterns | Export/buildable | No | No | Events/buildable | Yes |
| Layout recommendations | No | No | No | No | Yes |
| Museum-specific dashboard | No | No | No | No | Yes |
| Existing CCTV/IP camera support | Yes | Via OpenCV/stream source | Via pipeline | Strong | Depends |

## Main Finding

The generic computer-vision parts are available:

- detection
- tracking
- line crossing
- zone counting
- heatmaps
- queue/crowd zones
- trajectories

The museum product intelligence is not available as a ready open-source system:

- exhibit model
- gallery map model
- engagement scoring
- ignored exhibit detection
- layout recommendation logic
- curator/operator dashboard
- privacy-preserving reporting policy

This means the product value is not in "can we detect people?" The product value
is in turning detection events into museum decisions.

## Recommended Technical Direction

### Option A: Fastest Prototype

Use OpenDataCam as a reference/fork candidate.

Pros:

- UI and API already exist.
- Counting/tracking concepts are built.
- Good for quick demonstration.

Cons:

- Older stack.
- More modernization risk.
- Museum-specific analytics still need custom work.

Best if:

- We need to show a quick proof of concept with minimal original code.

### Option B: Best Long-Term Open Foundation

Build our own pipeline using:

- OpenCV for video input and frame handling
- a detector/tracker stack such as Ultralytics YOLO or another model
- Supervision for line zones, polygon zones, tracking utilities, and annotation
- our own analytics service
- our own dashboard

Pros:

- Modern, modular, easier to understand.
- We own the domain model and debugging story.
- Easier to build museum-specific logic cleanly.

Cons:

- More initial engineering than forking OpenDataCam.
- Need license review if using Ultralytics commercially.

Best if:

- We want production-quality architecture and developer understanding.

### Option C: Camera/NVR-First

Use Frigate for IP camera ingestion/object events and build museum analytics
beside it.

Pros:

- Strong camera/NVR foundation.
- MIT license.
- RTSP, zones, live view, and MQTT integration already exist.

Cons:

- Security/home-automation product model may not match museums.
- Museum dashboard and analytics still need custom work.

Best if:

- The hardest first problem is connecting to existing CCTV reliably.

## Recommendation

For this project, use Option B as the primary direction:

> Build a custom museum analytics product on top of open-source CV libraries,
> instead of forking an old full app or building CV primitives from scratch.

Suggested first architecture:

- Video source adapter: file, webcam, RTSP later
- Detector/tracker adapter: start with a pluggable interface
- Zone model: gallery, entrance, exit, exhibit zone, queue zone, restricted zone
- Event model: track seen, zone entered, zone exited, dwell updated, crossing
- Metrics engine: occupancy, dwell, queue, heatmap, paths
- Museum analytics engine: engagement, ignored exhibits, congestion,
  time-of-day patterns
- Recommendation engine: simple rule-based layout suggestions first
- Dashboard: live view, analytics, debug evidence

## License Warning

Before production/commercial use, review licenses carefully.

- OpenDataCam: MIT in GitHub metadata.
- Supervision: MIT in GitHub metadata.
- Frigate: MIT in GitHub metadata.
- Ultralytics: AGPL-3.0 or Enterprise License according to official docs/GitHub.

AGPL may be incompatible with a closed-source commercial deployment unless the
project accepts AGPL obligations or uses an enterprise license.

## Research Gaps

Need further research before implementation:

- Which detector/tracker gives acceptable accuracy on museum CCTV angles?
- How well do trackers maintain IDs in crowds and occlusions?
- What camera protocols will the target museum provide?
- Do we need homography/floor-plan calibration for accurate heatmaps?
- What privacy/legal jurisdiction applies to the deployment?
- Do we need to avoid storing raw video entirely?

## Planning Implication

The next planning document should not say "build from scratch."

It should say:

> Build the museum-specific product layer ourselves, while reusing open-source
> detection, tracking, zone, and camera-processing components.

No implementation should start until the user chooses between:

1. OpenDataCam fork/reference path.
2. Modern custom pipeline path.
3. Frigate camera/NVR-first path.
