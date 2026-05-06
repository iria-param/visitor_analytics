# Agent Communication Log

This file keeps Codex, Claude, and the user aligned. It is not a private agent
scratchpad. Anything written here should be useful to the user.

## Protocol

- Record decisions that affect architecture, privacy, testing, or project
  direction.
- Record cross-agent handoffs before implementation when possible.
- Keep entries short and factual.
- Include verification commands and results when a change is tested.
- If Codex and Claude disagree, write both positions and the user's final
  decision.
- Do not store secrets, API keys, CCTV credentials, or private video details.

## Handoff Template

```text
Date:
From:
To:
Topic:
Context:
Recommendation:
Files affected:
Verification:
User decision needed:
Status:
```

## Current Division Of Work

Codex:

- local repository inspection and edits;
- tests, smoke tests, and generated output verification;
- git branch and commit work when requested;
- implementation after research and plan agreement.

Claude Opus 4.7:

- research and architecture review;
- systems-thinking critique;
- privacy and risk review;
- test-plan design;
- focused code-review style feedback;
- implementation handoffs for Codex.

## Log

### 2026-05-06 - Approach 2 Step 1 Smoke Test

From: Claude/Codex collaboration

Topic: Museum-tuned tracker config smoke test

Context: Claude proposed testing ByteTrack and BoT-SORT tracker YAML files at
runtime because schema tests alone do not prove Ultralytics accepts the files.

Recommendation: Keep the tracker configs and tests as Step 1. Do not judge ID
stability by overlay viewing alone; Step 2 should add numerical diagnostics.

Files affected:

- `configs/trackers/bytetrack_museum.yaml`
- `configs/trackers/botsort_museum.yaml`
- `tests/test_tracker_configs.py`

Verification:

- ByteTrack museum run processed 614 frames and produced events, metrics, and
  overlay outputs.
- BoT-SORT museum run processed 614 frames and produced events, metrics, and
  overlay outputs.
- `.\.venv\Scripts\python -m pytest` passed with 10 tests.

User observation: Visual overlay comparison did not show a significant
difference.

Decision: Move to Approach 2 Step 2 before changing tracker strategy. Add track
diagnostics so tracker quality can be compared with numbers.

Status: Step 1 committed as `f5f80cd`.

### 2026-05-06 - Approach 2 Step 2 Handoff (Track Diagnostics)

Date: 2026-05-06

From: Claude Opus 4.7

To: Codex

Topic: Add numerical track diagnostics to `metrics_summary.json` so the
Approach 1 baseline, ByteTrack-museum, and BoT-SORT-museum runs can be
compared with numbers rather than by watching the overlay.

Context: Step 1 (`f5f80cd`) shipped museum-tuned ByteTrack and BoT-SORT
configs. Both ran successfully on `Recording 2026-05-05 193149.mp4`, but
visual overlay comparison did not show a clear ID-stability improvement.
Before changing tracker strategy or considering ReID, we need numbers.
Branch in flight: `codex/approach-2-id-stability`.

Recommendation: Add an in-pipeline `TrackDiagnostics` collector. It observes
the existing `TrackObservation` stream (no new sensors, no images, no
appearance features) and emits an additive `track_diagnostics` block in
`metrics_summary.json`. Existing summary fields stay untouched.

Files affected:

- New: `src/museum_gallery_ai/track_diagnostics.py` - `TrackDiagnostics`
  collector with `observe(timestamp_seconds, processed_frame_index,
  observations)` and `summary(zones, lines)`.
- New: `tests/test_track_diagnostics.py` - happy path, short-lived
  threshold, gap detection (uses processed indices, not raw video
  indices), ID-switch heuristic, fragmentation hotspot, fallback-id
  exclusion, empty-run safety.
- Edit: `src/museum_gallery_ai/processor.py` - instantiate the collector
  alongside `MetricsEngine`, call `observe(...)` once per processed frame
  right after `detector.track_people(frame.image)`, and merge
  `summary["track_diagnostics"] = diagnostics.summary(...)` before
  `write_json(...)`.
- Edit: `src/museum_gallery_ai/models.py` - extend `ProcessingConfig` with
  `short_lived_track_seconds: float = 1.0`,
  `id_switch_window_seconds: float = 2.0`,
  `id_switch_distance_pixels: float = 80.0`, and (Codex chooses one)
  either reuse a line buffer already implied by `ZoneEventEngine` or add
  `line_fragmentation_buffer_pixels: float = 30.0`. Document the choice.
- Edit: `docs/approaches/approach_2_identity_stability_and_journey_tracking.md`
  - mark Step 2 complete with a brief "what was measured" note ONLY after
  numerical results exist.

Output schema (additive, under new top-level `track_diagnostics` key):

- `unique_track_count`, `real_track_count`, `fallback_track_count` -
  fallback ids are those starting with `tmp_` from the
  `UltralyticsPersonTracker._track_id` fallback path.
- `duration_seconds: { mean, median, p25, p75, min, max }` - `null` when
  no real tracks.
- `short_lived_track_count` plus echoed `short_lived_threshold_seconds`.
- `tracks_per_minute` - `real_track_count * 60 /
  (last_observed_seconds - first_observed_seconds)`; `0.0` if duration
  is non-positive.
- `gap_stats: { tracks_with_gaps, total_gaps,
  mean_gap_processed_frames, max_gap_processed_frames }` - gaps measured
  in processed frame indices so `frame_stride > 1` does not look like
  gaps.
- `likely_id_switch_count` plus echoed `likely_id_switch_params: {
  window_seconds, distance_pixels }`. Heuristic: a real track ends at
  `t_end, p_end`; another real track starts within `window_seconds`
  after `t_end` and within `distance_pixels` of `p_end`. Each pair
  counted once. Fallback ids excluded.
- `fragmentation_hotspots: { by_zone: { zone_id: { track_starts,
  track_ends } }, by_line: { line_id: { track_starts_within_buffer,
  track_ends_within_buffer } }, outside_any_zone: { track_starts,
  track_ends } }`. Reuse `geometry.point_in_polygon`; do not
  re-implement.

Verification:

```powershell
.\.venv\Scripts\python -m pytest -v

.\.venv\Scripts\python -m museum_gallery_ai process `
  --config configs\calibrated.json `
  --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" `
  --output runs\step2_baseline

.\.venv\Scripts\python -m museum_gallery_ai process `
  --config configs\calibrated_bytetrack_museum.json `
  --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" `
  --output runs\step2_bytetrack_museum

.\.venv\Scripts\python -m museum_gallery_ai process `
  --config configs\calibrated_botsort_museum.json `
  --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" `
  --output runs\step2_botsort_museum
```

Acceptance is met when: `pytest` is fully green; all three runs produce a
`track_diagnostics` block with the keys above; `unique_track_count` and
`likely_id_switch_count` are non-zero on at least one run on the sample
recording; `fallback_track_count` is reported separately; existing
`metrics_summary.json` fields (`processed_frames`, `source`, `camera`,
zone/line metrics) are unchanged in semantics.

Risks and open questions:

1. The `_track_id` fallback returns `tmp_<x>_<y>` ids that collapse all
   detections in the same coarse 20px grid into one "track". Without an
   explicit fallback filter, every diagnostic is destroyed. Filter with
   the `tmp_` prefix; report the count separately; do not refactor the
   fallback in this step.
2. The ID-switch heuristic is just a heuristic. False positives in dense
   scenes, false negatives across long occlusions. Output keeps the
   `likely_*` prefix and echoes the window/distance params.
3. Gaps must be measured against the processed frame index counter
   already incremented in `processor.py` (`processed_frames`), not
   `frame.frame_index`, otherwise `frame_stride > 1` looks gappy.
4. Empty-run safety: zero tracks means medians and tracks-per-minute
   must emit `null`/`0`, not raise.

What not to change:

- `detector.py`, including the `tmp_` fallback id behaviour. Flag it,
  do not refactor.
- The tracker YAMLs in `configs/trackers/`. Step 2 evaluates them, it
  does not retune.
- Existing keys in `metrics_summary.json`. Additive only.
- `ZoneEventEngine`, `MetricsEngine`. Collector observes the same
  stream; it does not depend on or alter their event flow.
- `events.jsonl` schema. Do not add per-frame raw observations to it -
  it would bloat dramatically and may already have downstream readers.
- `configs/calibrated.json` and `src/museum_gallery_ai.egg-info/PKG-INFO`
  - both dirty in the working tree since before Step 1; keep leaving
  them alone.

Privacy boundary:

- No new sensors, no microphone, no audio.
- No appearance features, embeddings, ReID, face detection, demographic
  inference, emotion inference. ID-switch heuristic uses pixel
  proximity only.
- No new persistent identifiers; track ids stay camera-local and
  per-run.
- No raw frames, no person crops, no clip writing.
- All output stays inside `metrics_summary.json` next to existing
  aggregates.
- BoT-SORT `with_reid: False` remains enforced by the existing
  `test_botsort_museum_reid_disabled_by_default` trip-wire. Do not
  relax it.

Metrics needed: see "Output schema" above.

Failure modes:

- Zero tracks: aggregates return `null`/`0`. Unit-tested.
- All-fallback ids: `real_track_count == 0`; duration stats `null`; the
  fallback dominance is visible in the JSON.
- Single-frame tracks: duration 0, counted short-lived, no gaps.
- `frame_stride > 1` mistake: mitigated by accepting the processed
  frame index as an explicit argument to `observe(...)`.
- Polygon edge cases: reuse `geometry.point_in_polygon` so behaviour
  matches existing zone events.
- Many tracks: per-track record stays small (no per-frame foot-points
  beyond first/last). Median/percentile is `O(n log n)` once at end of
  run.
- Heuristic noise: documented via the `likely_*` prefix and echoed
  parameters.
- Memory regression on long videos: if `processed_frame_indices` per
  track shows up in profiling, replace with a running gap accumulator
  (track only previous index + counters).

User decision needed: after Codex lands Step 2 and the three runs are
produced, the user reviews the three `track_diagnostics` blocks and
decides whether to (a) keep both ByteTrack-museum and BoT-SORT-museum,
(b) drop BoT-SORT, or (c) open a privacy/architecture ADR for ReID.
That ADR is its own deliberate decision, not a default next step.

Status: Drafted by Claude. Awaiting Codex implementation on
`codex/approach-2-id-stability`.

### 2026-05-06 - Approach 2 Step 2 Implemented (Track Diagnostics)

Date: 2026-05-06

From: Codex

To: User and Claude Opus 4.7

Topic: Track diagnostics added to `metrics_summary.json`.

Context: The user visually compared the Step 1 overlays and did not see a
significant improvement. Claude recommended numerical diagnostics before
retuning trackers or considering ReID.

Implementation:

- Added `src/museum_gallery_ai/track_diagnostics.py`.
- Added diagnostics config fields to `ProcessingConfig`.
- Wired diagnostics into `OfflineProcessor`.
- Added `tests/test_track_diagnostics.py`.
- Kept diagnostics additive. Existing events and metrics semantics were not
  changed.

Verification:

- `.\.venv\Scripts\python.exe -m pytest -v` passed with 16 tests.
- Baseline, museum ByteTrack, and museum BoT-SORT runs each processed 614
  frames and produced events, metrics, and overlay outputs.

Results:

| Run | Unique tracks | Median duration | Short-lived tracks | Likely switches |
| --- | ---: | ---: | ---: | ---: |
| `runs/step2_baseline` | 118 | 1.617s | 49 | 195 |
| `runs/step2_bytetrack_museum` | 108 | 2.000s | 44 | 169 |
| `runs/step2_botsort_museum` | 101 | 2.100s | 35 | 125 |

Recommendation: For this sample, BoT-SORT has the strongest fragmentation
signals. Do not make it the default yet. Validate on more recordings and inspect
the longer gap behavior before the default tracker is changed.

Privacy boundary: No ReID, face recognition, demographic inference, emotion
inference, crops, raw frames, or persistent identifiers were added.

Status: Implemented and verified. Awaiting user review and decision on whether
to test more recordings or promote a tracker default later.

### 2026-05-06 - Temporary Dual Role (Claude covering for Codex)

Date: 2026-05-06

From: Claude Opus 4.7

To: Codex (when you return) and the user

Topic: Codex hit its rate limit. The user asked Claude to cover both roles
until Codex is back (~22:33).

What this means while Codex is offline:

- Claude will follow `AGENTS.md` rules in addition to `CLAUDE.md`.
- Claude will inspect files, edit code, run tests, and propose commits -
  not only review and plan.
- Git operations still require the user to run PowerShell commands,
  because the Linux sandbox cannot write to `.git/` on the Windows
  mount. Claude will hand exact commands.
- Branch in flight remains `codex/approach-2-id-stability`. Claude will
  not switch branches or make destructive git changes without explicit
  user approval.
- Privacy boundary unchanged: no ReID, no face/demographic/emotion
  inference, no raw video storage, no person crops.
- Any code review findings, decisions, or handoffs Claude writes during
  this period will be appended to this log so Codex sees them on
  return.

Open items waiting for action when Codex returns or the user runs them:

- Commit Codex's Step 2 implementation (4 files) and the doc updates
  (commands already given to the user).
- Validate Step 2 numbers on a second recording before promoting a
  tracker default.

Status: Active dual-role mode. Will revert to Claude-only review once
Codex is online.

