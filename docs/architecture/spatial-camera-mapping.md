# Spatial Camera Mapping

Status: proposed architecture design.

Spatial camera mapping is how the system understands a museum as a connected
space instead of a set of unrelated camera feeds.

Without mapping, each camera only knows:

```text
person at pixel x,y in camera frame
```

With mapping, the system can understand:

```text
anonymous visitor activity near Exhibit A
movement from Gallery 1 toward Gallery 2
congestion near the north corridor
high pass-by but low dwell near Sculpture 4
```

## Systems-Thinking Frame

The museum is a system, not a collection of isolated cameras.

### System Boundary

Inside the analytics boundary:

- galleries
- exhibits
- entrances and exits
- corridors and pathways
- camera viewpoints
- zones and lines
- anonymous visitor tracks
- events and metrics
- dashboard and recommendations

Outside the initial boundary:

- identifying individual people
- face recognition
- demographic profiling
- visitor phones
- microphones
- ticketing/payment systems
- long-term visitor identity

### Stocks

Stocks are things that accumulate or persist over time:

- visitors currently inside a gallery
- visitors currently near an exhibit
- queue length
- accumulated dwell time
- heatmap density
- congestion duration
- engagement score
- ignored-exhibit evidence

### Flows

Flows are movements or changes between stocks:

- visitors entering the museum
- visitors leaving the museum
- visitors moving from Gallery A to Gallery B
- visitors entering or leaving exhibit zones
- crowd buildup near a bottleneck
- visitors passing by an exhibit without stopping

### Feedback Loops

Useful feedback loops:

- Better layout reduces congestion.
- Better signage increases dwell at ignored exhibits.
- Better exhibit placement improves visitor flow.
- Better analytics improves curator decisions.

Dangerous feedback loops:

- Poor camera placement creates misleading analytics.
- Misleading analytics causes bad layout decisions.
- Bad layout decisions worsen visitor flow.
- Hidden or unclear camera use reduces visitor trust.

### Delays

Important delays:

- camera event detection delay
- visitor movement from one camera zone to another
- reporting delay from raw events to dashboard metrics
- operational delay from insight to layout change
- trust recovery delay after unclear surveillance behavior

### Leverage Points

High-leverage design points:

- accurate camera-to-floor mapping
- clear zone definitions
- explainable event evidence
- privacy-preserving aggregation
- camera health monitoring
- calibration review workflow
- simple rule-based recommendations with visible evidence

## Spatial Model

The system needs a shared spatial model.

Core concepts:

- `FloorPlan`: the museum/gallery map.
- `Gallery`: a named room or gallery area.
- `Pathway`: a walkable connection between areas.
- `Exhibit`: a physical object or installation.
- `Zone`: a polygon or line used for analytics.
- `Camera`: a physical camera.
- `CameraView`: a camera's field of view over part of the floor plan.

## Coordinate Systems

The system has at least two coordinate systems:

### 1. Camera Frame Coordinates

Pixel coordinates inside one camera view:

```text
x = horizontal pixel
y = vertical pixel
```

Good for:

- drawing overlays
- detector bounding boxes
- camera-local zones
- camera-local line crossings

Bad for:

- comparing two cameras
- understanding museum layout
- producing floor-plan heatmaps

### 2. Floor-Plan Coordinates

Shared map coordinates for the physical gallery:

```text
x = floor-plan horizontal position
y = floor-plan vertical position
```

Good for:

- multi-camera heatmaps
- gallery flow
- pathway analysis
- congestion on a shared map
- layout recommendations

## Mapping Approach

### Phase 1: Camera-Local Zones

Start simple:

- draw zones directly on each camera frame
- assign each zone to a gallery, exhibit, or pathway
- emit camera-local events

Example:

```text
camera_id: gallery_1_overview
zone_id: exhibit_a_zone
event: zone_entered
track_id: camera-local anonymous ID
```

This is enough for:

- dwell time by exhibit
- camera-local occupancy
- entry/exit counting
- queue/crowd detection

### Phase 2: Logical Space Graph

Create a graph of connected spaces:

```text
Entrance -> Lobby -> Gallery 1 -> Corridor A -> Gallery 2 -> Exit
```

Each zone maps to a graph node or edge:

- exhibit zone -> gallery node
- doorway line -> transition edge
- corridor zone -> pathway node
- exit line -> outside edge

This enables:

- path understanding
- gallery-to-gallery flow
- bottleneck detection
- journey patterns without person re-identification

### Phase 3: Floor-Plan Calibration

Map camera image coordinates to floor-plan coordinates.

Typical approach:

- choose known points visible in the camera image
- match them to points on the floor plan
- compute a perspective transform / homography
- convert track foot-points from image coordinates to floor-plan coordinates

This enables:

- shared heatmaps across cameras
- more accurate path traces
- better congestion localization
- layout recommendations on the actual gallery map

## Track Position Rule

For people detections, use the bottom-center point of the bounding box as an
approximate floor contact point:

```text
track_position = (box_center_x, box_bottom_y)
```

This is more useful for floor mapping than the center of the full bounding box.

## Space Graph

The museum should be represented as a graph:

```text
Node: Entrance
Node: Lobby
Node: Gallery 1
Node: Gallery 2
Node: Exit

Edge: Entrance -> Lobby
Edge: Lobby -> Gallery 1
Edge: Gallery 1 -> Gallery 2
Edge: Gallery 2 -> Exit
```

Events update the graph:

- line crossing at doorway increments flow on an edge
- zone occupancy updates node stock
- dwell time updates exhibit stock
- congestion updates pathway/node risk

## Path Understanding Without Identity Tracking

Phase 1 should avoid following the same person across cameras.

Instead, use aggregate flow:

```text
Gallery 1 exit line crossings toward Corridor A
  compared with
Corridor A entry events shortly after
```

This estimates movement between spaces without identifying individuals.

## Data Model Sketch

```text
Camera
  id
  name
  gallery_id
  stream_uri
  status

CameraView
  camera_id
  floor_plan_id
  calibration_points
  homography_matrix

Zone
  id
  camera_id
  gallery_id
  exhibit_id optional
  type
  polygon_points
  floor_polygon optional

SpaceNode
  id
  type
  name

SpaceEdge
  id
  from_node_id
  to_node_id
  transition_zone_or_line_id

TrackEvent
  camera_id
  track_id
  event_type
  zone_id
  timestamp
  confidence
```

## Recommendation Logic From Spatial Mapping

Layout recommendations should be based on visible evidence:

- If many visitors pass near an exhibit but dwell is low, review label,
  placement, lighting, or line of sight.
- If dwell is high and congestion is high, increase space, adjust routing, or
  add repeated context elsewhere.
- If a pathway has sustained congestion, review circulation and doorway width.
- If visitors frequently backtrack, signage or route clarity may be weak.
- If one gallery is skipped after a transition point, review wayfinding.

## Debugging Requirements

The dashboard should let a developer/operator inspect:

- camera frame with zones
- floor plan with mapped zones
- space graph
- event stream
- camera health
- calibration status
- mapping confidence
- why a recommendation was produced

## Phase 1 Design Rule

Even if the first implementation uses one video, every event should include:

- `camera_id`
- `gallery_id`
- `zone_id` when applicable
- `timestamp`
- `track_id` scoped to the camera
- `event_type`
- `confidence`

This keeps the architecture ready for multiple cameras without redesigning the
analytics model later.
