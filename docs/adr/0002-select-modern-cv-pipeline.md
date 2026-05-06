# ADR 0002: Select Modern CV Pipeline For Museum Analytics

## Status

Accepted

## Context

The product direction has changed from a general room-aware assistant to a
museum/gallery CCTV analytics system.

We researched whether an open-source framework already provides the full desired
feature set:

- entry/exit counts
- live occupancy
- dwell time
- queue/crowding detection
- heatmaps
- visitor paths
- exhibit engagement score
- ignored exhibits
- congested zones
- time-of-day patterns
- gallery layout recommendations

No single mature open-source framework was found that provides all of this as a
ready museum analytics product.

## Decision

Use Option 2:

> Build a custom museum analytics product using modern open-source
> computer-vision components.

We will not build detection/tracking primitives from scratch. We will use
libraries for video processing, detection, tracking, zones, and annotations, and
build the museum-specific analytics layer ourselves.

## Expected Architecture

- Video source adapter
- Detector adapter
- Tracker adapter
- Zone/event engine
- Metrics engine
- Museum analytics engine
- Dashboard/API

## Alternatives Considered

### OpenDataCam Fork

Pros:

- closest full-app open-source reference
- includes counting and tracking concepts
- MIT license

Cons:

- older stack
- not museum-specific
- modernization risk

### Frigate Camera/NVR Layer

Pros:

- strong IP camera/NVR support
- MIT license
- zones and object events

Cons:

- focused on security/home automation
- not museum analytics
- dashboard/product model mismatch

### Build Everything From Scratch

Pros:

- maximum control

Cons:

- slow
- risky
- unnecessary
- harder to debug

## Benefits

- reuses proven CV building blocks
- keeps our product domain clean
- supports replacing detector/tracker later
- avoids being locked into old full-app architecture
- lets us focus on museum-specific intelligence

## Tradeoffs

- more initial architecture work than forking OpenDataCam
- detector licensing must be reviewed
- we must build dashboard, persistence, calibration, and reporting ourselves
- accuracy must be validated on museum-like footage

## Feedback Loops

- Better debug overlays improve developer understanding.
- Better event evidence improves trust in analytics.
- Poor tracking accuracy creates poor recommendations.
- Clear privacy defaults increase deployability in museums.
- Museum-specific insights increase product differentiation.

## Signals This Decision Is Wrong

- We cannot achieve acceptable tracking accuracy with available open-source
  models.
- Existing CCTV integration becomes the main blocker before analytics.
- A full open-source project appears that already solves the museum analytics
  layer well.
- Licensing blocks the chosen detector/tracker path.

## References

- Open-source framework research: ../research/0003-open-source-video-analytics-frameworks.md
- Museum existing systems research: ../research/0002-museum-cctv-visitor-analytics-existing-systems.md
- Active product blueprint: ../MUSEUM_GALLERY_AI_BLUEPRINT.md
