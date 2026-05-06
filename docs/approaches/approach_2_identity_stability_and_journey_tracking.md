# Approach 2: Identity Stability And Anonymous Journey Tracking

Status: next planned approach.

Approach 2 starts after the current baseline. Its first priority is improving
tracking ID stability within one camera. Cross-camera journey analytics comes
after that foundation is measurable.

## Main Goal

Track visitors more consistently as anonymous camera-local IDs, then later
combine camera-local tracklets into anonymous full-journey IDs across the museum.

The target is:

```text
anonymous visitor journey
```

Not:

```text
real-world person identity
```

Example target output:

```text
Journey 42:
Entrance -> Main Hall -> Dinosaur Exhibit -> Exit
```

The system should not know the visitor's name, face identity, demographic group,
or whether they visited previously.

## Why This Is Needed

In Approach 1, a person can receive a new track ID when:

- the detector misses them for a few frames
- another person blocks them
- they pass behind an object
- they become too small or low-confidence
- they leave and re-enter the camera view

This causes fragmented analytics:

- one visitor may be counted as multiple visitors
- dwell time may split across multiple IDs
- journey paths become incomplete
- cross-camera matching becomes unreliable

## Research Direction

Approach 2 will evaluate stronger tracking before training any custom model.

Planned tracker baseline:

- current: ByteTrack
- next comparison: BoT-SORT
- optional: ReID / appearance matching where supported and acceptable

Relevant tracker ideas:

- ByteTrack uses high- and low-confidence detections to recover more tracks.
- BoT-SORT improves robustness using motion and appearance cues.
- ReID can help reconnect a person after occlusion, but increases complexity and
  privacy sensitivity.

Detailed framework research is recorded in:

- `docs/research/0004-approach-2-tracking-reid-frameworks.md`

Main finding:

```text
Build on existing tracking/ReID systems. Do not build ID stability or
multi-camera journey tracking from scratch.
```

## Implementation Sequence

### Step 1: Improve Same-Camera ID Stability

Add museum-specific tracker configs:

- `configs/trackers/bytetrack_museum.yaml`
- `configs/trackers/botsort_museum.yaml`

Tune:

- `track_buffer`
- matching thresholds
- new-track thresholds
- lost-track behavior
- optional ReID settings

Expected result:

- fewer ID changes when a person briefly disappears
- more stable dwell and occupancy numbers
- better track path continuity

### Step 2: Add Track Diagnostics

Add reports that explain tracking quality:

- number of unique track IDs
- average track duration
- short-lived tracks
- likely ID switches
- track disappearance/reappearance gaps
- path continuity evidence

This should be visible in metrics output, not hidden in video only.

### Step 3: Add Tracklet Summaries

For each anonymous camera-local track, store derived data:

- track ID
- camera ID
- first seen timestamp
- last seen timestamp
- sampled foot-points
- zones visited
- dwell by zone
- confidence summary

Do not store cropped person images by default.

### Step 4: Prepare For Cross-Camera Journey IDs

Before matching people across cameras, create:

- camera transition zones
- a museum space graph
- timestamp synchronization assumptions
- camera-to-gallery mapping
- entry/exit edges between galleries

Cross-camera journey matching should use:

- time gap
- possible path between cameras
- last/first known zone
- movement direction
- appearance similarity only if approved

### Step 5: Anonymous Journey Reconstruction

Only after same-camera tracking is stable:

```text
Camera-local tracklets
  -> candidate transition matches
  -> anonymous journey ID
  -> full visit path analytics
```

This should remain anonymous.

## Training Strategy

Do not train immediately.

Recommended sequence:

1. evaluate current ByteTrack baseline
2. evaluate tuned ByteTrack
3. evaluate BoT-SORT
4. measure ID switches and track fragmentation
5. use previous recordings for training only if off-the-shelf tracking is not
   accurate enough

Training with previous recordings requires:

- annotated same-person tracklets
- camera metadata
- privacy review
- data retention policy
- evaluation split
- clear acceptance metric

## Privacy Boundary

Allowed:

- anonymous camera-local track IDs
- anonymous journey IDs within a single visit/session
- aggregate route analytics
- derived tracklet metrics

Not allowed in this approach:

- face recognition
- named identity
- demographic guessing
- emotion detection
- persistent identity across multiple visits
- storing cropped person images by default
- cross-camera tracking without explicit privacy review

## Success Criteria

Approach 2 is successful when:

- same-camera ID flicker visibly decreases
- short occlusion cases keep the same ID more often
- metrics show fewer short-lived fragmented tracks
- dwell time becomes more stable
- ID-switch diagnostics are available
- the system is ready to design anonymous cross-camera journey matching

## Open Questions For The Coding Branch

When we start coding Approach 2, create a new branch first.

Recommended branch name:

```text
codex/approach-2-id-stability
```

Key decisions for that branch:

- exact tracker YAML defaults
- whether BoT-SORT ReID is enabled in prototype mode
- where track diagnostics are written
- what ID-switch heuristic is good enough for first evaluation
- how much track path data to store in JSON outputs

## Related Documentation

- `docs/approaches/approach_1_current_baseline.md`
- `docs/architecture/spatial-camera-mapping.md`
- `docs/research/0003-open-source-video-analytics-frameworks.md`
- `docs/planning/0001-option-2-modern-cv-pipeline-plan.md`
