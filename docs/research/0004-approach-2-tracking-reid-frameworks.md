# Approach 2 Research: Tracking, ReID, And Journey Frameworks

Date: 2026-05-06

Status: research brief for Approach 2.

## Question

Does a framework already exist for improving person ID stability and tracking a
visitor journey across cameras, and can we build upon it?

## Short Answer

Yes, this already exists as a known computer-vision problem:

- single-camera multi-object tracking
- person re-identification
- multi-target multi-camera tracking

We should not build this from scratch.

Best immediate path:

> Start with Ultralytics BoT-SORT and tracker tuning because it fits our current
> YOLO pipeline with the least change.

Best later path:

> Evaluate OpenVINO Multi Camera Multi Target demo and/or BoxMOT when we move
> from same-camera ID stability to cross-camera anonymous journey tracking.

Training on museum recordings should come only after these baselines are
measured and found insufficient.

## Current Baseline

Approach 1 currently uses:

```text
YOLO11n person detection
Ultralytics track()
ByteTrack tracker
camera-local temporary track IDs
```

Known issue:

- If a person disappears due to occlusion, missed detection, distance, or low
  confidence, ByteTrack may create a new ID when they reappear.

## Candidate 1: Ultralytics Track Mode

Sources:

- https://docs.ultralytics.com/modes/track/
- https://github.com/ultralytics/ultralytics/blob/main/docs/en/modes/track.md
- https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/trackers/botsort.yaml

What it provides:

- YOLO tracking mode.
- Built-in ByteTrack and BoT-SORT support.
- Tracker config files.
- `track_buffer`, `match_thresh`, `new_track_thresh`, `track_high_thresh`,
  `track_low_thresh`, `with_reid`, `appearance_thresh`, and
  `proximity_thresh`.

Important finding:

- Ultralytics docs describe `track_buffer` as the number of frames a lost track
  is kept alive before removal. Increasing it helps short occlusions.
- Ultralytics docs describe BoT-SORT ReID as appearance-based matching that can
  improve tracking across occlusions, with extra compute cost.
- The official BoT-SORT default sets `with_reid: False`, so enabling ReID is a
  deliberate choice, not the default.

Fit for us:

- Best first step because our code already uses Ultralytics.
- Lowest integration cost.
- Useful for same-camera ID stability.

Recommended use:

- Add `configs/trackers/botsort_museum.yaml`.
- Compare:
  - current ByteTrack
  - tuned ByteTrack
  - BoT-SORT without ReID
  - BoT-SORT with ReID if acceptable

Risks:

- AGPL/commercial licensing already applies through Ultralytics.
- ReID may slow processing.
- ReID can still be wrong in crowds or similar clothing.

## Candidate 2: BoxMOT

Sources:

- https://mikel-brostrom.github.io/boxmot/
- https://github.com/zs001122/yolo_tracking
- https://zenodo.org/records/7629840/latest

What it provides:

- A pluggable tracker collection.
- Supports trackers such as:
  - ByteTrack
  - BoT-SORT
  - StrongSORT
  - DeepOCSORT
  - OCSORT
  - BoostTrack
- Supports motion-only and motion-plus-appearance trackers.
- Uses appearance/ReID models such as OSNet, LightMBN, and CLIPReID.

Important finding:

- BoxMOT explicitly separates lightweight motion-only trackers from
  motion-plus-appearance trackers.
- Motion-plus-appearance trackers are better for identity consistency but cost
  more compute.

Fit for us:

- Strong second step if Ultralytics BoT-SORT is not enough.
- Good for tracker benchmarking.
- Gives us more options without writing tracker algorithms ourselves.

Risks:

- Adds dependency complexity.
- More tracker options can create tuning confusion if we do not define a clear
  evaluation metric.

Recommended use:

- Do not integrate immediately.
- First create an ID-switch diagnostic report.
- Use BoxMOT if Ultralytics trackers cannot meet our target.

## Candidate 3: OpenVINO Multi Camera Multi Target Demo

Sources:

- https://docs.openvino.ai/2023.3/omz_demos_multi_camera_multi_target_tracking_demo_python.html
- https://docs.openvino.ai/2023.3/omz_models_model_person_reidentification_retail_0288.html
- https://www.intel.com/content/www/us/en/support/articles/000057233/software/development-software.html

What it provides:

- Multi-camera multi-target tracking demo.
- Input can be several video files or several webcams.
- Runs detector first, then person re-identification model for detected objects.
- Assigns IDs to objects.
- Can output visualization, history JSON, and detection JSON.
- Includes quality measurement tooling for multi-camera tracking.

Important finding:

- The demo expects an object detection model plus an object re-identification
  model.
- OpenVINO provides pre-trained person re-identification models such as
  `person-reidentification-retail-0288`.
- The `person-reidentification-retail-0288` model outputs a 256-float embedding
  for cosine-distance matching.
- Its documented Market-1501 rank-1 accuracy is 86.1%, but the documentation
  notes best pose coverage for standing upright, parallel to image plane, and
  occlusion below 50%.

Fit for us:

- Strong reference for Approach 2 Phase B: multi-camera journey reconstruction.
- Gives us a real architecture for multiple videos/cameras and ReID embeddings.
- Better fit for cross-camera experimentation than building from scratch.

Risks:

- It is an OpenVINO stack, not our current YOLO/Ultralytics stack.
- It may require model conversion and a separate runtime path.
- Accuracy may be limited by camera angle, occlusion, clothing similarity, and
  museum lighting.

Recommended use:

- Use as research/reference for cross-camera journey design.
- Consider a separate spike later:

```text
OpenVINO demo on 2 recorded videos
  -> inspect generated history JSON
  -> compare with our planned journey model
```

## Candidate 4: NVIDIA Multi-Camera Tracking Workflow

Source:

- https://www.nvidia.com/en-us/ai-data-science/ai-workflows/multi-camera-tracking/

What it provides:

- Production-oriented multi-target multi-camera tracking workflow.
- Uses DeepStream SDK, pretrained models, embeddings, and microservices.
- Tracks and associates objects across cameras.
- Uses visual embeddings/appearance plus spatial-temporal information.

Important finding:

- NVIDIA describes a global ID across cameras based on embeddings/appearance,
  not personal biometric identity.

Fit for us:

- Useful production architecture reference.
- Potential future deployment path if target hardware includes NVIDIA GPUs or
  Jetson.

Risks:

- Heavier platform commitment.
- May require NVIDIA hardware, DeepStream, containers, and microservices.
- Not the fastest path for our current local Python prototype.

Recommended use:

- Use as production reference, not the next implementation step.

## Candidate 5: Torchreid / ReID Training Libraries

Sources:

- https://kaiyangzhou.github.io/deep-person-reid/
- https://huggingface.co/papers/1910.10093

What it provides:

- A PyTorch library for person re-identification.
- Supports image and video ReID.
- Supports multiple datasets.
- Includes training, evaluation, pretrained models, and extensibility.

Important finding:

- Torchreid is a research/development library for ReID models, not an
  end-to-end museum analytics product.

Fit for us:

- Useful only if off-the-shelf ReID is insufficient.
- Good for a future training phase using annotated museum recordings.

Risks:

- Requires labeled data.
- Requires privacy review.
- Adds ML training/evaluation complexity.

Recommended use:

- Do not use immediately.
- Revisit only after we have baseline metrics showing that off-the-shelf
  trackers fail.

## Comparison

| Option | Best For | Use Now? |
| --- | --- | --- |
| Ultralytics BoT-SORT | Same-camera ID stability | Yes |
| BoxMOT | Tracker benchmarking and stronger ReID trackers | Later if needed |
| OpenVINO MTMC demo | Cross-camera journey tracking reference | Later spike |
| NVIDIA MTMC workflow | Production-scale GPU/DeepStream architecture | Later reference |
| Torchreid | Custom ReID training | Only after evaluation |

## Recommended Approach 2 Sequence

### Phase 2A: Same-Camera ID Stability

Build on our current stack:

- Add museum-specific ByteTrack and BoT-SORT tracker configs.
- Run the same video with each tracker.
- Generate comparison outputs.
- Add an ID stability report:
  - total unique IDs
  - short-lived track count
  - average track duration
  - likely ID switches
  - tracks lost and recreated nearby

### Phase 2B: Tracklet Summaries

Create per-track summaries:

- first seen
- last seen
- duration
- sampled foot-points
- zones visited
- dwell by zone
- confidence statistics

These are still camera-local and anonymous.

### Phase 2C: Cross-Camera Journey Research Spike

Evaluate OpenVINO's Multi Camera Multi Target demo using recorded videos:

- run two or more videos
- inspect history JSON
- understand embedding-based matching
- compare to our data model

### Phase 2D: Anonymous Journey ID

Only after camera-local stability:

```text
camera-local tracklets
  -> transition-zone matching
  -> time-gap constraints
  -> appearance embedding similarity
  -> anonymous journey ID
```

## Training Decision

Do not train immediately.

Training previous museum recordings should happen only if:

- tuned ByteTrack is not stable enough
- BoT-SORT is not stable enough
- OpenVINO/BoxMOT baselines are not stable enough
- we have labeled same-person examples
- privacy and retention rules are approved

## Privacy Boundary

Approach 2 should still use:

```text
anonymous journey IDs
```

Not:

```text
real identity
```

Avoid:

- face recognition
- demographic guessing
- persistent identity across visits
- storing person crops by default
- cross-camera ReID without explicit privacy review

## Conclusion

We can build upon existing work.

Immediate implementation should not integrate a new large framework yet. The
lowest-risk next step is:

```text
Ultralytics BoT-SORT + tracker tuning + ID stability report
```

Then, if needed:

```text
BoxMOT tracker comparison
```

For true cross-camera journey tracking:

```text
OpenVINO MTMC demo spike
```
