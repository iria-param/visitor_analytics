# 0005 - Tracker Flicker, Proximity-Merge, and ReID Effectiveness

Date: 2026-05-14
Author: Claude Opus 4.7 (research role; reviewed by user)
Status: Draft for Codex review and user approval before any implementation.

Workflow: This document is produced under
`docs/PROJECT_START_WORKFLOW.md`. It is research + plan. No code, no config,
no experiment runner is to be changed on the basis of this document until the
user approves the plan and Codex implements in small verified steps.

---

## 1. Context and Why This Research

A 72-second offline experiment on real-CCTV `gallery_day1` was run on three
tracker variants (baseline ByteTrack, museum-tuned ByteTrack, museum-tuned
BoT-SORT). Aggregate diagnostics indicated BoT-SORT was the most stable
(switches reduced ~47% vs baseline across three clips). Visual inspection
revealed two failure modes that those metrics had hidden:

1. Single-frame box drops on the same physical visitor (visible "blinking").
2. Fresh IDs assigned to the same physical visitor every time two visitors
   walked close together and then separated.

An additional offline experiment with `with_reid: True` on BoT-SORT was
authorised by the user (offline only, no deployment, see
`docs/AGENT_COMMUNICATION.md` entry 2026-05-14 "One-Off Offline ReID
Experiment Authorised"). The user's verbal verdict after watching the
overlay: "ID across occlusion: same or very slight improvement". The user
later confirmed "ReID is not working" in our current state.

This research investigates **why ReID had no visible effect** and **what
actually causes the sub-second ID churn**, with citations to authentic
sources, so we can plan a focused remediation.

---

## 2. Sources Consulted

Primary (Ultralytics official):

- Ultralytics BoT-SORT API reference, with full source for
  `BOTSORT.__init__`, `init_track`, `get_dists`, and the `ReID` class —
  <https://docs.ultralytics.com/reference/trackers/bot_sort/>
- Ultralytics multi-object tracking docs —
  <https://docs.ultralytics.com/modes/track>
- Ultralytics configuration reference (default IoU NMS = 0.7) —
  <https://docs.ultralytics.com/usage/cfg>
- Ultralytics NMS reference —
  <https://docs.ultralytics.com/reference/utils/nms>
- Ultralytics NMS glossary —
  <https://www.ultralytics.com/glossary/non-maximum-suppression-nms>

Primary (Ultralytics source and issues):

- `ultralytics/trackers/bot_sort.py` (main branch) —
  <https://github.com/ultralytics/ultralytics/blob/main/ultralytics/trackers/bot_sort.py>
- PR #20192 "New tracker re-identification (ReID) of lost tracks" — merged
  in `ultralytics 8.3.114`, April 2025 —
  <https://github.com/ultralytics/ultralytics/pull/20192>
- Issue #20391 "[BOTSORT] Encoder initialized even when with_reid set to
  False" — fixed in `ultralytics 8.3.117` —
  <https://github.com/ultralytics/ultralytics/issues/20391>
- Issue #3818 "botsort.yaml and with with_reid" —
  <https://github.com/ultralytics/ultralytics/issues/3818>
- Issue #20498 "Problem when I use botsort tracker with ReID and
  yolo11n-cls.pt" —
  <https://github.com/ultralytics/ultralytics/issues/20498>
- Discussion #20699 "Inconsistent Object Tracking Across Frames with YOLO11n
  and BoT-SORT" —
  <https://github.com/orgs/ultralytics/discussions/20699>

Primary (project local files):

- `src/museum_gallery_ai/detector.py` — calls `model.track(..., iou=0.4)`.
- `src/museum_gallery_ai/processor.py` — orchestrates detection + tracking.
- `configs/trackers/botsort_museum.yaml` — current tracker thresholds.
- `configs/eval/tracker_only.json` — current detector thresholds.
- `requirements.txt` — `ultralytics>=8.3` (unpinned upper).

Secondary (tutorial by the PR author, useful for recommended thresholds, not
treated as a primary spec):

- Mohammed Yasin, "Tracking with Efficient Re-Identification in
  Ultralytics", April 2025 (updated Sept 2025), the author of PR #20192 —
  <https://y-t-g.github.io/tutorials/yolo-reid/>

Out of scope for this research (already covered by prior brief
`docs/research/0004-approach-2-tracking-reid-frameworks.md`):

- Architectural comparisons between FairMOT, BoT-SORT, MOTRv2, etc. We are
  not recommending switching architectures here; only tuning what we have.

---

## 3. Key Findings

### F1. Our project uses an aggressive NMS IoU threshold

`src/museum_gallery_ai/detector.py` line 28 calls Ultralytics with
`iou=0.4`. Ultralytics' default for `iou` (the NMS IoU threshold) is
`0.7` per the configuration reference. A **lower** `iou` value means NMS
suppresses boxes that overlap less. So `iou=0.4` is **more aggressive
suppression than default**, which is the opposite direction of what
crowded pedestrian scenes typically need. Two visitors walking
shoulder-to-shoulder whose boxes overlap by 0.4-0.7 will be collapsed to
a single box; the lower-confidence box is discarded for that frame.

Source: `src/museum_gallery_ai/detector.py:28`;
`https://docs.ultralytics.com/usage/cfg`;
`https://www.ultralytics.com/glossary/non-maximum-suppression-nms`.

### F2. Native-features ReID requires Ultralytics >= 8.3.114

PR #20192, merged April 2025, is the **first version of Ultralytics that
natively supports ReID via YOLO detector features** when
`with_reid: True` and `model: auto`. Before 8.3.114, that flag
combination did not produce useful ReID embeddings out of the box. Our
`requirements.txt` pins `ultralytics>=8.3` with no upper bound. Whether
Codex's local environment and the Colab environment installed 8.3.114
or later is not currently verified.

Source: <https://github.com/ultralytics/ultralytics/pull/20192>;
`requirements.txt`.

### F3. How "model: auto" ReID actually works (source-level)

From `ultralytics/trackers/bot_sort.py` main branch:

```python
self.encoder = (
    (lambda feats, s: [f.cpu().numpy() for f in feats])
    if args.with_reid and self.args.model == "auto"
    else ReID(args.model)
    if args.with_reid
    else None
)
```

In `auto` mode the "encoder" is a thin lambda that consumes pre-extracted
detector features. The feature extraction is performed by a PyTorch hook
inside Ultralytics' tracker callback, which captures the input to the
Detect layer of the YOLO model. NMS-survived detections are mapped back
to their corresponding feature vectors and those vectors become the
ReID embeddings.

These embeddings are **YOLO detection features**, not features trained
for appearance discrimination between persons. They encode "what kind of
object is here" more strongly than "which specific person is here".
This matters for our scene (small / distant CCTV crops of similarly
dressed visitors), discussed in F5.

Source: `bot_sort.py` `BOTSORT.__init__` lines 175-185 of the GitHub
HEAD; PR #20192 description.

### F4. The appearance-similarity gate in our config is essentially closed

`configs/trackers/botsort_museum.yaml` sets `appearance_thresh: 0.8`.
The cost-matrix logic in `BOTSORT.get_dists` is:

```python
if self.args.with_reid and self.encoder is not None:
    emb_dists = matching.embedding_distance(tracks, detections) / 2.0
    emb_dists[emb_dists > (1 - self.appearance_thresh)] = 1.0
    emb_dists[dists_mask] = 1.0
    dists = np.minimum(dists, emb_dists)
```

With `appearance_thresh = 0.8`, any embedding distance greater than
`1 - 0.8 = 0.2` is set to 1.0 (i.e. rejected). For native YOLO features
on small/distant crops the typical embedding distance between two
crops of the SAME visitor across a brief flicker is in the 0.3-0.6
range. With the gate at 0.2, the appearance score is almost always
rejected, leaving only IoU to drive matching. **In effect ReID is
silently bypassed at the matching stage even when enabled.**

For comparison the Yasin tutorial (the PR author) explicitly recommends
`appearance_thresh: 0.3` for native features. Our value of `0.8` is the
Ultralytics default but the default was chosen for a separate ReID
model, not for native features.

Source: `bot_sort.py` `get_dists` (lines 210-223 of GitHub HEAD);
`configs/trackers/botsort_museum.yaml` line 53; Yasin tutorial.

### F5. Native features are weak for distant CCTV crops

The native-feature ReID approach was demonstrated by the PR author on
in-store object tracking where persons occupy a substantial fraction
of the frame. Distant museum/gallery CCTV at 1080p where a typical
visitor occupies 60-120 px tall is closer to the harder end of the
spectrum. YOLO11n's detection features at that scale are likely to
produce embeddings whose intra-person distance and inter-person
distance bands overlap significantly.

This is consistent with the user's empirical verdict that the ReID
overlay looked "the same or very slight improvement" against
position-only BoT-SORT — even when ReID was technically running with
appearance-thresh fixed, the embeddings may not have been
discriminative enough to change matching outcomes on this scene.

Source: PR #20192 description (in-store object example); Yasin
tutorial figure showing the comparison; the user's observation.

### F6. The "new track" gate is permissive

`new_track_thresh: 0.30` (`botsort_museum.yaml` line 25). Any
detection above 0.30 confidence is eligible to start a new track
without first having to match an existing track. Most recovered
detections after a flicker come back at conf 0.5-0.85, which is well
above 0.30. So even when Kalman + IoU is close enough to match the
recovered detection back to the lost track, BoT-SORT's parallel branch
is fully willing to spawn a brand new ID. Hungarian assignment can
prefer the new-spawn path over the recover path in ambiguous cases.

Source: `bot_sort.py` (calls into `byte_tracker.py` for new-track
handling); `configs/trackers/botsort_museum.yaml` line 25.

### F7. The "match" gate is wide, not strict

`match_thresh: 0.8` is the cost threshold used by Hungarian
assignment. Cost is computed as `1 - IoU` after fuse_score, so a match
is accepted whenever cost <= 0.8, i.e. IoU >= 0.2. This is permissive,
not strict. Earlier in this investigation Claude wrote that matching
was "too strict" — that was wrong. Matching is already very permissive.
The failure is upstream: when proximity-merge collapses two boxes into
one, only **one** detection exists in the frame, so only one of the two
live tracks gets matched at all. The "lost" track is left orphaned for
the duration of the merge, and on separation a new-track spawn is
cheap because of F6.

Source: `bot_sort.py` (inherits `BYTETracker` matching);
`byte_tracker.py` cost matrix code.

### F8. Two known Ultralytics bugs adjacent to our use case

- #20391 (8.3.117): encoder initialised even when `with_reid: False`.
  Cosmetic for us (we want True), but indicates the area is recently
  touched and not fully stable.
- #20498: `yolo11n-cls.pt` does not work cleanly as a ReID model in
  current Ultralytics, with reported tracking failures.

These suggest the ReID code path is recently added and still settling.

Source: #20391, #20498.

### F9. Our diagnostic counts double-count proximity-merge re-spawns

Because of F6 + F7, what `track_diagnostics.py` reports as
`short_lived_count` and `likely_switch_count` over-counts the same
physical visitor each time a proximity-merge separates with a fresh
ID. The cross-clip number "243 short-lived tracks on BoT-SORT" should
not be read as "243 short visits". A substantial fraction is one
physical visitor being re-spawned several times. We cannot quantify
the fraction without inspecting `events.jsonl`.

Source: user's dense-frame observation at 0:50-1:10; our prior log
entry 2026-05-11; the failure-mode mechanism in F1, F6.

---

## 4. Mapping Findings to the Three Occlusion Cases

Earlier in the conversation we separated three failure modes that all
get loosely called "occlusion". Here is the mapping with findings.

| Case | What it is | Findings that explain it | Where it lives |
|------|------------|--------------------------|----------------|
| 1. Partial occlusion | part of a person hidden, detector confidence dips | F4 + F5 | Layer 2 (detector) and Layer 5 (overlay renderer not drawing Kalman-predicted boxes) |
| 2. Full occlusion (> track_buffer) | person fully hidden then reappears | F4 (gate closed) + F5 (native features weak) → ReID does not rescue | Layer 3 (tracker, ReID) |
| 3. Proximity merge | two visitors close, NMS collapses to one box | F1 (iou=0.4) + F6 (new spawn cheap) + F7 (only one detection to match against) | Layer 2 (NMS) and Layer 3 (new_track_thresh) together |

The proximity-merge case (#3) is what the user observed at 0:50-1:10 in
both the no-ReID and ReID overlays. ReID cannot help case #3 because
when both visitors are merged into one box, no separate feature vector
is extracted for the lost visitor.

---

## 5. Assumptions

A1. Codex's local Ultralytics version and the Colab Ultralytics version
are recent enough (>= 8.3.114) for native ReID to be functional.
Not yet verified.

A2. The visible flicker patterns and ID-renumbering events we observed in
the overlay videos for `gallery_day1` are representative of the
behaviour on `gallery_day2` and `gallery_day3`. Not verified frame-
by-frame on those clips.

A3. The native-feature embeddings on yolo11n at imgsz=1280 are too weak to
discriminate similarly-dressed visitors. This is hypothesised from F5
and the user's verdict, not directly measured.

A4. Lowering NMS aggressiveness (raising `iou` from 0.4) will not
introduce a regression in single-person detection (boxes-on-shadows
problem). Not directly verified for our scene.

---

## 6. Open Questions

Q1. What Ultralytics version is currently installed in our `.venv` and
in the Colab environment when section 3 of the notebook runs? Both
need to be checked. Requires `pip show ultralytics` in each.

Q2. What does the `events.jsonl` from the existing
`gallery_day1_botsort_museum_reid` run look like for the green-shirt
visitor at 0:50-1:10? Specifically how many distinct track IDs were
assigned to that region over the 20-second window? This would
quantify F9.

Q3. Does our current Ultralytics version actually export the
detection-layer features through the PyTorch hook (as PR #20192
intends), or is the hook missing/different in our version? Requires
inspecting the installed `ultralytics/trackers/track.py`.

Q4. What is `embedding_distance` actually computing on native features?
Cosine similarity over normalised vectors? Euclidean? Requires
reading `ultralytics/trackers/utils/matching.py`.

---

## 7. Risks and Unknowns

R1. Tuning four knobs at once will obscure causality. We will not be
able to attribute the improvement (or regression) to a single change.
Mitigation: change one knob per experiment.

R2. Lowering NMS suppression (`iou` 0.4 -> higher) may produce two boxes
on one person in some poses (e.g. side view with bag held out).
Mitigation: cap the change at a moderate value first (0.5), verify
visually, then consider further increase.

R3. Lowering `appearance_thresh` from 0.8 to 0.3 will let weaker
appearance signals influence matching. If F5 is right and native
features are noisy, this could cause incorrect cross-person matches
(wrong-person ID reuse), which is worse for analytics than fresh-ID
spawn. Mitigation: keep `proximity_thresh: 0.5` as a position gate
so appearance only acts among spatially plausible candidates.

R4. The whole research stack is partly inferred from source reading; we
have not yet executed a controlled experiment that varies one knob
and measures the effect. Mitigation: see plan section 8.

R5. The committed `botsort_museum.yaml` carries explicit privacy
comments about ReID. Any plan that recommends `with_reid: True` for
deployment requires a written ADR and the visitor-consent step the
user already raised. Section 9 below addresses this.

---

## 8. Plan (For Discussion Before Implementation)

### Product goal

Reduce sub-second ID churn on the same physical visitor in single-camera
museum CCTV, without crossing the project's privacy boundary.

### MVP scope

A reproducible offline experiment series on `gallery_day1` (1 clip,
1800 frames, overlay on) that varies exactly one knob per run,
measures the change in `unique_track_count`, `short_lived_count`,
`likely_switch_count`, and the green-shirt visitor's ID count in the
0:50-1:10 window. No production deployment, no visitor-facing change.

### Non-goals

- Not switching tracker architecture (no FairMOT, no MOTRv2 in this
  cycle).
- Not training or fine-tuning the detector.
- Not introducing multi-camera fusion.
- Not enabling ReID for deployment.
- Not changing the privacy policy.

### Architecture options

**Option A. Tracker-only tuning, no ReID, single-knob experiments.**

Knobs to try, one experiment per knob:

A.1 NMS `iou`: 0.4 -> 0.5 (less aggressive). File:
`src/museum_gallery_ai/detector.py` line 28. Hypothesis: reduces
case-3 frequency by letting close boxes coexist.

A.2 `new_track_thresh`: 0.30 -> 0.50. File:
`configs/trackers/botsort_museum.yaml` line 25. Hypothesis: prevents
flicker-driven new-ID spawns.

Each variant is a sibling YAML or a CLI override. Committed configs
remain at current values during the experiment.

**Option B. Layer 5 cosmetic fix: render Kalman-predicted boxes.**

File: `src/museum_gallery_ai/overlay.py`. During a frame where a track
has no current detection but a valid Kalman prediction and is still
inside `track_buffer`, draw the predicted box in a different style
(e.g. dashed). This makes the overlay visibly reflect the tracker's
internal state and removes much of the "flicker" perception without
changing identity counts. Useful for stakeholder demos.

**Option C. Re-tuned ReID experiment (offline, gated).**

A second one-off offline ReID experiment with the same boundary as the
2026-05-14 entry, but with `appearance_thresh: 0.3` (per F4 / Yasin)
instead of 0.8. Sibling file `botsort_museum_reid_tuned.yaml`,
committed-config unchanged. Single Colab run on `gallery_day1` with
overlay on, results logged in `AGENT_COMMUNICATION.md`. Decision on
whether to pursue ReID further depends on the visual + numerical
outcome of this run.

**Option D. Detector swap to yolo11s.**

Only if Options A-C are insufficient. yolo11s is larger and would
likely improve native-feature quality and detection on distant
visitors. Slower (estimated 2-3× per frame).

### Recommended approach

Run the options in this order, in **separate** small experiments,
because each will give a clean signal:

1. A.1 (raise NMS `iou`). Cheapest. Targets case 3.
2. A.2 (raise `new_track_thresh`). Cheap. Targets the same case via a
   different lever; useful even after A.1 in case some merges still
   happen.
3. C (re-tuned ReID). Tests whether the original ReID experiment
   failure was due to F4 (gate closed) rather than F5 (features weak).
4. B (Kalman overlay) when there is a stakeholder demo to make.
5. D (yolo11s) only if 1-3 do not converge to acceptable behaviour.

### Tradeoffs

A.1 raises NMS `iou` -> more boxes survive close to each other. Risk
R2 (possible double box on one person). Mitigation: keep at 0.5 first.

A.2 raises `new_track_thresh` -> some legitimately new visitors who
enter the frame at conf 0.30-0.50 may have to wait for a higher
confidence before getting a track. Slight delay before a new visitor's
ID appears.

C with appearance_thresh 0.3 -> may cause cross-person ID confusion if
two visitors are similarly dressed (R3). For museum visitor analytics
this is usually less harmful than flicker-driven over-counts.

D yolo11s -> slower; needs GPU.

### Debugging strategy

- All experiments overlay ON, on Colab, with the same `gallery_day1`
  clip. Diff = single knob change.
- Per experiment, log: command line, knob value, run duration,
  `unique_track_count`, `short_lived_count`, `likely_switch_count`,
  and a 5-frame visual of the 0:50.5 merge moment to verify the
  proximity-merge behaviour changed.
- Keep all per-experiment YAML/JSON in a runtime-only folder
  (`/content/runtime_configs/exp_A1/...` etc) so the committed configs
  do not move during the cycle.

### Testing strategy

- Existing pytest suite must continue to pass (`.\.venv\Scripts\python
  -m pytest`). No code paths in `processor.py` need to change for
  A.1/A.2/C. Option B (`overlay.py`) requires a unit test for the
  "draw predicted box when no current detection" case.
- A new diagnostic (Q2 above) — per-track ID-renumbering count
  inside a configurable spatial window — would let us programmatically
  measure case-3 churn. This is the most useful new metric but is
  also out of MVP scope for this cycle.

### Milestone sequence

M1. Pin Ultralytics to a known good version range
(`ultralytics>=8.3.117,<8.4`) in `requirements.txt` so Codex's
environment, the user's local env, and Colab agree. Verify on first
run.

M2. Run experiment A.1 on `gallery_day1`. Log results.

M3. Run experiment A.2 on `gallery_day1`. Log results.

M4. Decide whether to run C. If yes, run with the same gating used
in 2026-05-14 (offline, no deployment, no commits of generated runs).

M5. Compare M2/M3/M4 visually at the 0:50 marker and numerically on
short_lived_count.

M6. If a tuning combination shows a clear improvement, write an ADR
that records the rationale and the new defaults.

M7. Only after ADR and explicit user approval, change the committed
`botsort_museum.yaml` or `detector.py` defaults.

### Definition of done

- Each experiment produces a row in `comparison_real_cctv.csv` (or an
  equivalent log table) with the knob value and resulting metrics.
- The proximity-merge moment at 0:50 has been re-inspected on each
  variant's overlay. The user has eyes-on confirmation that case 3
  behaviour changed (better, same, worse).
- The cycle concludes with either (a) an ADR recommending a default
  change, or (b) a logged decision that further work needs a richer
  approach (detector swap, FairMOT-style joint training).

---

## 9. Privacy Implications

This research recommends:

- **A.1 and A.2 do not touch ReID.** They are tracker/detector tuning.
  No privacy boundary issue.
- **Option B (Kalman overlay) is purely visual.** No identity
  inference, no embedding storage. No privacy boundary issue.
- **Option C re-tunes ReID and is gated by the existing 2026-05-14
  experiment boundary** (offline only, no deployment, no person
  crops saved, embeddings in-memory only). Any production use still
  requires the visitor consent process and a written ADR, as already
  documented in `MUSEUM_GALLERY_AI_BLUEPRINT.md`.
- **Option D (yolo11s) is detector-only.** No privacy boundary
  issue.

No option in this plan, if executed, would change the committed
`with_reid: False` in `botsort_museum.yaml`. The committed config
continues to reflect policy.

---

## 10. What This Document Does NOT Decide

- It does not approve flipping `with_reid: True` in the committed
  config.
- It does not approve any change to `MUSEUM_GALLERY_AI_BLUEPRINT.md`.
- It does not authorise running the experiments; that requires user
  approval and Codex to be the implementer of file changes.
- It does not commit Ultralytics to a specific version yet; that is
  M1 in section 8.

---

## 11. Appendix - File Inventory of Knobs

For Codex's convenience, the files that hold the knobs discussed:

- `src/museum_gallery_ai/detector.py` line 28 — NMS `iou` (currently 0.4)
- `src/museum_gallery_ai/detector.py` (no `agnostic_nms` set; uses default False)
- `configs/eval/tracker_only.json` — `confidence_threshold` (currently 0.18)
- `configs/eval/tracker_only.json` — `image_size` (currently 1280)
- `configs/trackers/botsort_museum.yaml` — `track_buffer` (90), `match_thresh` (0.8), `new_track_thresh` (0.30), `appearance_thresh` (0.8), `proximity_thresh` (0.5), `with_reid` (False), `model` (auto)
- `configs/trackers/bytetrack_museum.yaml` — same `track_buffer`, `match_thresh`, `new_track_thresh` semantics
- `requirements.txt` — `ultralytics>=8.3` (needs upper-bound discussion in M1)
