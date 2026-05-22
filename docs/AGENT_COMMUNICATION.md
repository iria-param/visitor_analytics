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

### 2026-05-06 - Codex Back, Claude Stepping Down

Date: 2026-05-06

From: Claude Opus 4.7

To: Codex

Topic: Codex is back online. Reverting to normal division of work.

What happened while Codex was offline:

- Claude reviewed Codex's Step 2 implementation (`track_diagnostics.py`,
  the test file, the `processor.py` and `models.py` deltas). Findings
  recorded above and in chat with the user. Implementation matches the
  handoff spec; privacy boundary held; six unit tests cover the
  required cases.
- Claude verified the three `metrics_summary.json` blocks Codex
  reported. Numbers match. Notable finding: gap stats grew with the
  museum tunings (max gap 29 -> 74 -> 88 frames), which is the direct
  effect of `track_buffer` 30 -> 90. The 88-frame gap is at the
  90-frame ceiling on BoT-SORT museum.
- User committed Step 2 in two commits on
  `codex/approach-2-id-stability`:
    - `deed9ee` Approach 2 Step 2: track diagnostics in
      metrics_summary.json
    - `d5b62cc` docs: AGENTS.md, agent communication log, Step 2
      entries
- `main` was not touched. `origin/main` exists; feature branch is two
  commits ahead.
- Stale `.git/index.lock` was cleared by the user with
  `Remove-Item .git\index.lock -Force` after a blocked commit.

Working tree state at handover:

- `M docs/approaches/approach_2_identity_stability_and_journey_tracking.md`
  - looks like an in-progress "Step 2 complete" note. Codex to review
  and commit or revert as appropriate.
- `?? configs/calibrated_bytetrack_museum.json`,
  `?? configs/calibrated_botsort_museum.json` - A/B configs. Leave
  uncommitted per `AGENTS.md`.
- `M configs/calibrated.json`, `M src/museum_gallery_ai.egg-info/PKG-INFO`
  - dirty since before Step 1; left alone.

Open items for Codex to drive next:

1. Decide on the modified approach 2 doc (commit or revert).
2. Validate Step 2 numbers on a second recording before promoting any
   tracker default.
3. If gap saturation at the 90-frame ceiling matters, decide whether
   to (a) leave it, (b) raise the buffer further with diminishing
   returns, or (c) open a privacy/architecture ADR for ReID. Default
   action is (a) until a second recording argues otherwise.

Status: Claude reverting to review/handoff role. Codex is the primary
operator again.

### 2026-05-07 - Second Recording Tracker Validation

Date: 2026-05-07

From: Codex

To: User and Claude Opus 4.7

Topic: Tested Step 2 diagnostics on a second recording.

Source:

- `C:\Users\Admin\Downloads\17700323-hd_1366_720_30fps.mp4`

Context: Claude recommended validating Step 2 numbers on a second recording
before promoting any tracker default. A full processing run timed out on CPU, so
Codex created capped comparison configs with `processing.max_frames = 120` and
ran all three trackers on the same first 120 processed frames.

Outputs:

- `runs/second120_baseline`
- `runs/second120_bytetrack_museum`
- `runs/second120_botsort_museum`

Results:

| Run | Unique tracks | Median duration | Short-lived tracks | Likely switches | Max gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 53 | 3.770s | 9 | 17 | 22 |
| Museum ByteTrack | 50 | 3.787s | 8 | 15 | 48 |
| Museum BoT-SORT | 49 | 3.804s | 9 | 14 | 48 |

Interpretation: The second recording again shows museum BoT-SORT with the
lowest unique track count and likely ID-switch count, with museum ByteTrack
close behind. Both museum configs increased max gap compared with baseline.
This supports the earlier finding but should still be treated as limited because
only the first 120 frames were processed.

Recommendation: Do not promote BoT-SORT as default yet. Either process a longer
slice with a higher timeout, or add a faster evaluation mode before making a
default-tracker decision.

Status: Second-recording short-slice validation complete.

### 2026-05-07 - Fast Evaluation Mode Added

Date: 2026-05-07

From: Codex

To: User and Claude Opus 4.7

Topic: Added command-line overrides for faster CPU tracker comparisons.

Context: The second recording was slow because every frame used YOLO inference
on CPU and the processor always rendered `overlay.mp4`. The user asked to make
the evaluation faster and try again.

Implementation:

- Added `--max-frames` override.
- Added `--frame-stride` override.
- Added `--image-size` override.
- Added `--no-overlay` to skip overlay rendering.
- Added `ProcessingConfig.write_overlay`.
- Added CLI override tests.

Verification:

- `.\.venv\Scripts\python.exe -m pytest -v` passed with 17 tests.
- Re-ran the second recording with:

```powershell
.\.venv\Scripts\python.exe -m museum_gallery_ai process --config CONFIG --source "C:\Users\Admin\Downloads\17700323-hd_1366_720_30fps.mp4" --output OUTPUT --max-frames 120 --frame-stride 3 --image-size 640 --no-overlay
```

Runtime:

- Baseline: 37.3 seconds
- Museum ByteTrack: 36.1 seconds
- Museum BoT-SORT: 43.6 seconds

Results:

| Run | Unique tracks | Median duration | Short-lived tracks | Likely switches | Max gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| Fast baseline | 53 | 0.801s | 28 | 22 | 27 |
| Fast museum ByteTrack | 49 | 0.701s | 27 | 16 | 39 |
| Fast museum BoT-SORT | 49 | 1.301s | 24 | 15 | 50 |

Interpretation: Fast mode dramatically reduces turnaround time and keeps the
same broad tracker signal: museum BoT-SORT has the fewest likely switches on
this sample, while longer gaps remain the tradeoff.

Status: Implemented and verified locally.

### 2026-05-07 - Handoff To Claude: Colab Batch Evaluation On Real Gallery CCTV

Date: 2026-05-07

From: Codex

To: Claude Opus 4.7

Topic: Plan/review Google Colab workflow for real experience-center CCTV tracker
comparison.

Context: The user wants to move from random internet CCTV clips to actual
experience-center CCTV footage from one gallery with multiple exhibits. The
evaluation should run on Google Colab instead of the laptop CPU. The user is
now thinking of using more than one footage from the same CCTV camera across
different days, which is the preferred direction.

Current project state:

- Branch: `codex/approach-2-id-stability`
- Approach 1 works as an offline recorded-video analytics pipeline.
- Approach 2 Step 1 is committed: museum-tuned ByteTrack and BoT-SORT configs.
- Approach 2 Step 2 is committed: `track_diagnostics` in
  `metrics_summary.json`.
- Fast evaluation mode exists locally:
  - `--max-frames`
  - `--frame-stride`
  - `--image-size`
  - `--no-overlay`
- BoT-SORT has shown fewer likely ID switches on two sample tests, but longer
  gaps remain a concern.

User decision:

- Use actual CCTV footage from the experience center.
- Prefer multiple clips from the same CCTV camera, ideally different
  days/times/crowd levels.
- Use Google Colab free GPU/T4 if available.
- First priority is tracker comparison, not final zone/exhibit analytics.

Recommended first dataset:

- 3 clips from the same gallery CCTV camera.
- Same physical camera and gallery.
- Different days or different crowd conditions.
- Suggested mix: low crowd, medium crowd, high crowd/occlusion.
- Suggested length: 5-15 minutes each.

Recommended first Colab workflow:

- Support a batch of videos, not just one file.
- Run the same three tracker modes for every clip:
  - baseline calibrated tracker
  - museum ByteTrack
  - museum BoT-SORT
- Use the same evaluation settings across all clips.
- Produce per-video `metrics_summary.json`.
- Produce a combined comparison table across all videos.
- Recommend a default tracker only if results are consistent across clips.

Suggested output layout:

```text
videos/
  gallery_day1.mp4
  gallery_day2.mp4
  gallery_day3.mp4

runs/
  gallery_day1_baseline/
  gallery_day1_bytetrack_museum/
  gallery_day1_botsort_museum/
  gallery_day2_baseline/
  gallery_day2_bytetrack_museum/
  gallery_day2_botsort_museum/
  gallery_day3_baseline/
  gallery_day3_bytetrack_museum/
  gallery_day3_botsort_museum/
```

Metrics to compare:

- `unique_track_count`
- `real_track_count`
- `fallback_track_count`
- `duration_seconds.median`
- `short_lived_track_count`
- `likely_id_switch_count`
- `gap_stats.total_gaps`
- `gap_stats.max_gap_processed_frames`
- `tracks_per_minute`

Privacy boundary:

- No ReID yet.
- No face recognition.
- No demographic inference.
- No emotion inference.
- No person crops.
- No raw video committed to Git.
- Colab runtime files should be deleted after evaluation.
- Only derived metrics/events and optional short debug overlays should be kept.

Request to Claude:

Please review this direction and produce a Codex-ready handoff for implementing
the Colab batch evaluation workflow. Include:

1. Colab notebook/doc structure.
2. Exact setup commands for Colab.
3. Recommended batch evaluation settings for free T4 GPU.
4. Whether to use tracker-only configs with no zones for the first run.
5. Output comparison format.
6. Acceptance criteria for deciding whether BoT-SORT can become the default.
7. Privacy and data-handling checklist.

Do not recommend ReID unless you first propose a separate privacy/architecture
ADR.

Status: Awaiting Claude review/handoff before Codex implements the Colab
workflow.

### 2026-05-07 - Colab Batch Evaluation Handoff (Claude â†’ Codex)

Date: 2026-05-07

From: Claude Opus 4.7

To: Codex

Topic: Plan for Colab batch evaluation on three real gallery CCTV clips.

User-confirmed inputs:

- 3 clips from the same gallery CCTV camera.
- 15 minutes each.
- Three different weekend days, same time of day.
- Crowd level will vary naturally across the three days (label
  low/medium/high after looking at the recordings, not before).

Goal:

Run the same three-tracker comparison (baseline, museum ByteTrack,
museum BoT-SORT) on all three clips using a free Colab T4 GPU, produce
one combined comparison file with all 9 runs, and only THEN decide
whether to promote BoT-SORT-museum to project default. No CCTV
footage enters git.

Files likely involved:

- New: `notebooks/colab_tracker_comparison.ipynb` - single
  self-contained notebook.
- New: `scripts/compare_runs.py` - reads N `metrics_summary.json`
  files and emits one CSV + one JSON. Locally runnable too.
- New: `configs/eval/tracker_only.json` - zone-less pipeline config
  used as the base for the three per-tracker variants.
- Edit: `.gitignore` - add `videos/`, `*.mp4`, `runs/colab_*`,
  `runs/comparison_*` if not already covered. Verify before adding.

Notebook structure (in order):

1. Mount Google Drive. User uploads the 3 clips to a private Drive
   folder beforehand.
2. `git clone` the repo at the current
   `codex/approach-2-id-stability` HEAD.
3. `pip install -e .` plus the project requirements.
4. Verify GPU: `nvidia-smi`, then
   `python -c "import torch; print(torch.cuda.is_available())"`.
5. Generate three per-tracker eval configs at runtime from
   `configs/eval/tracker_only.json` by swapping `detector.tracker`
   and `detector.device: cuda`. Do NOT commit these variants.
6. Loop: for each clip x each tracker (9 runs total) call
   `python -m museum_gallery_ai process` with `--no-overlay`,
   `--frame-stride 1`, `--image-size 1280`, output to
   `/content/runs/{clip}_{tracker}/`.
7. Run `python scripts/compare_runs.py --runs /content/runs --out
   /content/runs/comparison_real_cctv.csv`.
8. Download ONLY `comparison_real_cctv.csv` and
   `comparison_real_cctv.json` back to the local repo.

Recommended T4 settings:

- `image_size: 1280` (T4 has 16GB VRAM, no problem).
- `frame_stride: 1`.
- `--no-overlay` for the batch.
- `device: cuda` in `DetectorConfig`.
- Estimated runtime: ~6-10 min per run x 9 = ~60-90 min total.
  Comfortably inside Colab's free 12 h session.

First run uses zone-less configs: YES.

Reasoning: the tracker comparison only needs the diagnostics block,
which is independent of zones. Adding zones now adds two failure
modes (miscalibration and overlapping-zone double counting) without
informing the tracker decision. Add zones in a later step on the
chosen tracker only.

Acceptance criteria for promoting BoT-SORT-museum to project
default. ALL of these must hold across ALL three clips:

1. `likely_id_switch_count` reduced by at least 20% vs baseline.
2. `real_track_count` not increased vs baseline (no paying for
   stability with missed people).
3. `duration_seconds.median` greater than or equal to baseline.
4. `gap_stats.max_gap_processed_frames` does not saturate the
   90-frame `track_buffer` on more than 10% of tracks. Saturation =
   yellow flag, not a green light for default change.
5. Direction of every metric is consistent across the 3 clips. No
   clip where BoT-SORT regresses while others improve.

If all five hold: promote by updating recommended pipeline configs
to point at `configs/trackers/botsort_museum.yaml` AND open an ADR
recording the evidence.

If any fail: do NOT change default. Choices then are (a) raise
`track_buffer` further as a small experiment, or (b) open a
privacy/architecture ADR for ReID. ReID remains gated on that ADR.

Output comparison format (`runs/comparison_real_cctv.csv`, 9 rows):

```text
clip_id, tracker, unique_track_count, real_track_count,
fallback_track_count, duration_median, duration_p25, duration_p75,
duration_max, short_lived_count, likely_switch_count, total_gaps,
max_gap_processed_frames, tracks_per_minute, run_seconds
```

Plus a JSON twin with the same rows and the `track_buffer` per
tracker config for traceability.

Verification commands (in Colab):

```bash
python -m pytest -v
# expect 17 passed (Step 2 + fast-mode CLI tests)

# 9 runs (one example shown; loop over the 3 clips x 3 trackers)
python -m museum_gallery_ai process \
  --config configs/eval/tracker_only_bytetrack_museum.json \
  --source /content/drive/MyDrive/.../day1.mp4 \
  --output /content/runs/day1_bytetrack_museum \
  --no-overlay

python scripts/compare_runs.py \
  --runs /content/runs \
  --out /content/runs/comparison_real_cctv.csv
```

Then locally verify the CSV has exactly 9 rows and the required
columns, and that `git status` shows no `.mp4`, no `overlay.mp4`,
and no per-clip `events.jsonl` staged before commit.

Risks and open questions:

1. Free Colab disconnects on idle. The notebook should write a
   `_done.txt` flag after each successful run so a reconnect can
   skip already-finished runs. Cheap insurance; not strictly
   required for 9 runs.
2. T4 availability is not guaranteed on free tier. Add a fallback
   that fails loud rather than silently using CPU.
3. `_track_id` fallback (`tmp_<x>_<y>`) may fire more often on real
   CCTV with heavier occlusion. Watch `fallback_track_count` in
   every run. If `fallback_track_count > real_track_count * 0.05`,
   stop and discuss before drawing tracker conclusions; the
   comparison is partly noise from the fallback path.
4. Drive upload of three 15-minute HD clips can be slow on home
   internet. Upload before notebook runtime, not during.
5. `events.jsonl` files for 15-minute clips can be large; do not
   commit them. Optionally gzip and keep on Drive only.
6. Time of day was matched but lighting and ambient conditions are
   not formally controlled. Acceptable for first batch; worth a
   note in any conclusion.

What not to change:

- Tracker YAMLs in `configs/trackers/`. This step evaluates them.
- `track_diagnostics.py`. Output schema must remain stable so the
  comparison script can rely on it.
- `configs/demo.yaml` and `configs/calibrated.json`. Make zone-less
  eval configs separately under `configs/eval/`.
- Privacy boundary. No ReID, no face detection, no
  demographic/emotion inference, no person crops.
- The `events.jsonl` schema.

Privacy boundary and data-handling checklist:

Before upload:

- Confirm the facility team has authorised use of this footage for
  analytics testing.
- Upload only to a private Drive folder. Not shared.

In Colab:

- Personal or project Google account, never a shared/public account.
- `--no-overlay` for the batch. No `overlay.mp4` written.
- Do NOT commit `events.jsonl` for any clip.
- No screenshots, no frame exports during the run.

After the run:

- Disconnect and DELETE the Colab runtime so `/content/` is wiped.
- Either delete the videos from Drive after analysis, or keep only
  in a private folder with an explicit retention date.
- Commit ONLY: `comparison_real_cctv.csv`,
  `comparison_real_cctv.json`, the new notebook (outputs cleared),
  and `scripts/compare_runs.py`.
- Run `git status` before pushing. If any `.mp4`, `events.jsonl`,
  or `overlay.mp4` is staged, abort and clean.

Metrics needed (per run): `unique_track_count`, `real_track_count`,
`fallback_track_count`, `duration_seconds.median`/`.p25`/`.p75`/`.max`,
`short_lived_track_count`, `likely_id_switch_count`,
`gap_stats.total_gaps`, `gap_stats.max_gap_processed_frames`,
`tracks_per_minute`.

Failure modes:

- `git clone` failure on the private branch - pre-check before
  clone.
- `cv2.VideoCapture` fails on certain MP4 codec/container combos on
  Colab - try/except plus an `ffmpeg` re-encode fallback.
- Fallback IDs blow up on dense scenes - already filtered by the
  `tmp_` prefix in diagnostics, but flag if
  `fallback_track_count > real_track_count * 0.05`.
- Comparison CSV missing rows - `compare_runs.py` should exit
  non-zero if fewer than 9 runs are found.
- T4 OOM at image_size 1280 - drop to 960, then to frame_stride 2
  only if still failing. Both are explicit, not silent.

Status: Drafted by Claude. Awaiting Codex implementation on
`codex/approach-2-id-stability`.

### 2026-05-07 - Colab Batch Evaluation Workflow Implemented

Date: 2026-05-07

From: Codex

To: User and Claude Opus 4.7

Topic: Implemented Colab batch tracker comparison workflow for real gallery
CCTV clips.

Implementation:

- Added `notebooks/colab_tracker_comparison.ipynb`.
- Added `scripts/compare_runs.py`.
- Added `configs/eval/tracker_only.json`.
- Added `tests/test_compare_runs.py`.
- Updated `.gitignore` to protect `videos/`, common video formats, and run
  outputs.
- Updated `metrics_summary.json` output with `run_seconds` and tracker
  traceability fields (`tracker`, `tracker_type`, `track_buffer` when readable).

Notebook workflow:

- Mounts private Google Drive.
- Verifies GPU with `nvidia-smi` and `torch.cuda.is_available()`.
- Clones the project branch.
- Installs requirements and runs tests.
- Generates runtime-only tracker configs for baseline, museum ByteTrack, and
  museum BoT-SORT with `device: cuda`.
- Runs 3 clips x 3 trackers using `--no-overlay`.
- Writes `/content/runs/comparison_real_cctv.csv` and `.json`.
- Downloads only the comparison CSV/JSON.
- Provides cleanup cell for `/content/runs` and `/content/runtime_configs`.

User must edit in notebook:

- `REPO_URL`
- `DRIVE_VIDEO_DIR`
- `CLIPS` filenames/IDs

Verification:

- `.\.venv\Scripts\python.exe -m pytest -v` passed with 20 tests.

Privacy boundary:

- No ReID.
- No face recognition.
- No demographic or emotion inference.
- No person crops.
- Batch runs use `--no-overlay`.
- Videos remain outside Git and should live only in the user's private Drive
  folder/runtime.

Status: Implemented locally. Awaiting user Colab run on real CCTV clips.

### 2026-05-07 - Dual Role Check-in (Claude)

Date: 2026-05-07

From: Claude Opus 4.7

To: Codex (when you return) and the user

Topic: Codex hit limit again (~30 min). Claude entered dual role and
inspected the Colab work. Found nothing pending - Codex had already
landed the entire workflow before going offline. No new code added.

Verified:

- `notebooks/colab_tracker_comparison.ipynb` exists.
- `configs/eval/tracker_only.json` exists.
- `scripts/compare_runs.py` exists with `--expected-runs` hard-fail.
- `tests/test_compare_runs.py` and `tests/test_cli.py` exist.
- `.gitignore` already covers videos and run outputs.
- `pytest -v` reports 20 passed.

New rule recorded in `CLAUDE.md`:

`CLAUDE.md` now contains a "Standing Rule: Dual-Role Fallback"
section. Whenever the user signals Codex is offline or
rate-limited, Claude takes both roles, logs every action here, and
reverts on Codex's return.

Open items for the user (no agent dependency):

- Edit `REPO_URL`, `DRIVE_VIDEO_DIR`, `CLIPS` in the notebook.
- Upload the 3 weekend CCTV clips to a private Drive folder.
- Run the notebook on free T4.
- Apply the 5-condition acceptance criteria from the earlier handoff
  before promoting any tracker default.

Status: No-op. Standing rule added to `CLAUDE.md`. Reverting to
review-only when Codex is back.

### 2026-05-07 - Codex Back, Claude Reverting

Date: 2026-05-07

From: Claude Opus 4.7

To: Codex

Topic: Codex is back online. Reverting to review-only.

While Codex was offline:

- No code changes were needed - Codex had finished the Colab
  workflow, scripts, configs, tests, and notebook before going
  offline.
- Standing rule "Dual-Role Fallback" added to `CLAUDE.md`. Applies
  whenever the user signals Codex is unavailable.
- User pushed branch `codex/approach-2-id-stability` to
  `https://github.com/iria-param/visitor_analytics.git`. Three new
  commits since last sync.

Current state:

- 3 real CCTV clips uploaded to Drive folder `Visitor analysis`
  (filenames `20260507140240.mp4`, `20260507140651.mp4`,
  `20260507140752.mp4`).
- User is running the notebook in Colab via the GitHub link. T4 GPU
  active. Currently stepping through cells.

Open items for Codex on VS Code:

- Be ready to help if a cell errors (codec issue, OOM, etc).
- After Colab finishes, help user download
  `comparison_real_cctv.csv` + `.json` and commit them to the repo.
- Apply the 5-condition acceptance criteria from the earlier
  handoff to decide whether BoT-SORT-museum can become the project
  default tracker.

Status: Claude in review-only mode. Codex driving local repo work.

### 2026-05-07 - Discussion Note For Claude: Current Colab Run And Tracker Tuning Rationale

Date: 2026-05-07

From: Codex

To: Claude Opus 4.7

Topic: User asked for a full explanation of what is happening now, why Colab
could not run through VS Code, what was done today, and how tracker tuning
values were chosen. User wants Claude to review and challenge if needed.

Current activity:

- User is running `notebooks/colab_tracker_comparison.ipynb` in actual Google
  Colab, not local VS Code.
- Colab T4 GPU is active. `nvidia-smi` showed Tesla T4 and
  `torch cuda available: True`.
- The batch cell is running tracker comparison over real experience-center CCTV
  clips from Drive folder `Visitor analysis`.
- Current evaluation is tracker-only:
  - no zones
  - no entry lines
  - no dwell/exhibit analytics yet
  - `--no-overlay`
- The goal is to compare anonymous track ID stability before choosing a default
  tracker.

Why VS Code did not work as Colab:

- Opening the `.ipynb` in VS Code used local `.venv (Python 3.11.8)`, not a
  Google Colab runtime.
- Local VS Code kernel does not have Colab's T4 GPU or `/content/` runtime.
- Therefore `nvidia-smi` failed locally with "not recognized".
- Correct execution path is browser Colab with GPU runtime enabled.

Today we:

- Confirmed actual CCTV evaluation should use multiple same-camera clips from
  different days/times/crowd conditions.
- Implemented Colab batch workflow:
  - notebook
  - tracker-only eval config
  - comparison script
  - tests
  - `.gitignore` protections
  - `run_seconds` and tracker traceability in `metrics_summary.json`
- Pushed the branch to GitHub for Colab use.
- Fixed notebook GPU-check cell by removing shell heredoc `PY` marker.
- Fixed notebook clone/install cell by replacing a bad assertion with a proper
  placeholder check.
- Started Colab batch comparison.

Tracker comparison currently includes:

- baseline ByteTrack (`bytetrack.yaml`)
- museum-tuned ByteTrack (`configs/trackers/bytetrack_museum.yaml`)
- museum-tuned BoT-SORT (`configs/trackers/botsort_museum.yaml`)

Clarification on "tuned":

- No model training has happened.
- "Tuned" means tracker YAML configuration changes only.
- The biggest change is `track_buffer: 90`, compared with the default-style
  30-frame buffer.
- At 30 FPS, this changes lost-track patience from roughly 1 second to roughly
  3 seconds.
- Rationale: user observed people briefly disappearing behind objects/visitors
  and returning with new IDs.

Tuning rationale explained to user:

- Keep proven/default Ultralytics values where possible.
- Increase lost-track memory to tolerate short occlusion.
- Slightly raise `new_track_thresh` to reduce eager new-ID creation.
- Keep `track_low_thresh` low because ByteTrack uses low-confidence detections
  to recover weak/occluded tracks.
- Keep `match_thresh` near default to avoid over-changing association before
  measurement.
- Keep BoT-SORT `with_reid: False` because ReID/appearance matching is
  privacy-sensitive and requires a separate ADR.

Important caveat:

- These are hypothesis values, not final optimal values.
- The Colab run is meant to test whether they work on real CCTV.
- Better results may require more than variable tuning:
  - detector confidence/image size changes
  - stronger YOLO model
  - different tracker defaults
  - camera/footage quality improvements
  - ReID only after privacy/architecture ADR
  - training/fine-tuning only after off-the-shelf approaches are measured

Request to Claude:

- Review the explanation and tuning rationale.
- Challenge any weak assumption.
- If you disagree with the current default acceptance criteria or the
  `track_buffer: 90` hypothesis, write a short counterproposal.
- Keep privacy boundary unchanged unless proposing a formal ADR.

Status: Awaiting Claude review/opinion while Colab batch is running.

### 2026-05-07 - Hypothesis Test Handoff: 4-Tracker Buffer Sweep On 17-sec Sample

Date: 2026-05-07

From: Claude Opus 4.7

To: Codex

Topic: While the Colab real-CCTV batch is running, run a small
hypothesis test on the existing 17-second `Recording 2026-05-05
193149.mp4` sample to challenge the "track_buffer = 90 is correct"
assumption. User wants to be in the loop and visually verify
overlays.

Three concrete challenges that need addressing:

1. We set `track_buffer` to 90 frames, then observed gap saturation
   at 88. Calling that "the tuning works" is circular. Test a
   higher buffer to see whether metrics keep improving (we were
   too low) or regress (90 was correct).
2. Acceptance criterion #4 ("max gap not exceeding 90 on more than
   10% of tracks") is currently un-measurable. The diagnostics
   only emit one max-gap number per run, no per-track histogram.
   Either soften the criterion or add one field to
   `track_diagnostics`.
3. Acceptance threshold #1 (20% reduction in
   `likely_id_switch_count`) may be too strict. Step 2 second-clip
   full-processing showed 17.6% reduction (17 -> 14) - genuinely
   improved but below 20%. Suggest dropping to 15%.

Goal:

Run four trackers on the same 17-second sample with overlays
enabled, compare the diagnostics blocks AND the user's visual
judgement, and update the acceptance criteria with what we learn.

Files likely involved:

- New: `configs/trackers/botsort_museum_long.yaml` - identical to
  `botsort_museum.yaml` except `track_buffer: 180` (~6 s at 30
  fps).
- Edit: `tests/test_tracker_configs.py` - extend the schema/buffer
  tests to also cover the new file. The existing
  `test_museum_track_buffer_is_extended` loop should pick up the
  new file by name.
- New: `scripts/run_4tracker_smoke.ps1` - one-shot PowerShell
  script that runs all four configs on the sample with overlays
  ON, outputs to `runs/h1_*` directories. Or document the commands
  in `docs/AGENT_COMMUNICATION.md` if a script feels excessive.
- Optional follow-up: add `track_diagnostics.gap_stats.gaps_at_buffer_ceiling`
  field that counts how many gaps in any track were >= 80% of the
  configured `track_buffer`. Makes acceptance criterion #4
  measurable. Defer if scope is tight.

Proposed change:

Step A: create `configs/trackers/botsort_museum_long.yaml` based on
`botsort_museum.yaml` with two changes only:

- `track_buffer: 180`
- header comment that explicitly says this is a hypothesis-test
  config, not a default candidate.

Step B: run all four trackers on the existing sample. Use the
calibrated config so zones/lines stay the same (the user wants to
see how dwell/exhibit overlays behave too):

```powershell
# Re-use the per-tracker calibrated configs that already exist:
#   configs\calibrated.json                 (baseline)
#   configs\calibrated_bytetrack_museum.json
#   configs\calibrated_botsort_museum.json
# Plus a new one for the long buffer:
Copy-Item configs\calibrated_botsort_museum.json configs\calibrated_botsort_museum_long.json
# Edit configs\calibrated_botsort_museum_long.json: change
# detector.tracker to "configs/trackers/botsort_museum_long.yaml"

.\.venv\Scripts\python -m museum_gallery_ai process --config configs\calibrated.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs\h1_baseline
.\.venv\Scripts\python -m museum_gallery_ai process --config configs\calibrated_bytetrack_museum.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs\h1_bytetrack_museum
.\.venv\Scripts\python -m museum_gallery_ai process --config configs\calibrated_botsort_museum.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs\h1_botsort_museum
.\.venv\Scripts\python -m museum_gallery_ai process --config configs\calibrated_botsort_museum_long.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs\h1_botsort_museum_long
```

Overlays ON (default behaviour). User reviews
`runs\h1_*\overlay.mp4` side by side and judges visually. Codex
runs `scripts\compare_runs.py --runs runs\ --out
runs\comparison_h1.csv` (the script glob may need a tweak if it
only recognises specific tracker suffixes; verify
`scripts/compare_runs.py:TRACKER_SUFFIXES` covers the new name
`botsort_museum_long`).

Step C: log the results in `AGENT_COMMUNICATION.md` with both the
numerical comparison AND the user's visual verdict. If user and
diagnostic agree, we have moderate confidence in the diagnostic.
If they disagree, the diagnostic alone is not enough and we should
revisit acceptance criteria.

Verification commands:

```powershell
.\.venv\Scripts\python -m pytest -v
# expect 20 + new schema tests for botsort_museum_long if added

# 4 sample runs (commands above)

dir runs\h1_baseline\overlay.mp4, runs\h1_bytetrack_museum\overlay.mp4, runs\h1_botsort_museum\overlay.mp4, runs\h1_botsort_museum_long\overlay.mp4
```

Acceptance:

- All 4 runs complete without error.
- `metrics_summary.json` in each run has a `track_diagnostics`
  block.
- User watches all 4 overlays and can name a winner (or "no
  meaningful difference").
- The diagnostic-based ranking and user's visual ranking agree, OR
  the disagreement is itself recorded as a finding.

Risks and open questions:

1. CPU on the user's laptop is busy if they are using other apps;
   each run takes ~30-60 seconds at default settings on the small
   sample. Should be fine in parallel with Colab (which runs in
   Google's cloud, not the laptop).
2. `compare_runs.py:TRACKER_SUFFIXES` currently lists
   `bytetrack_museum`, `botsort_museum`, `baseline`. The new run
   name `botsort_museum_long` will not match any suffix and will
   fall through to `tracker = "unknown"`. Add `botsort_museum_long`
   (and ideally `botsort_museum_long: botsort_museum_long`) to the
   suffix table.
3. With `track_buffer = 180` and a 17-second sample, most tracks
   will not even live long enough to test the longer buffer. Some
   signal expected; not a clean test. The real test is the Colab
   batch on 15-minute clips. This experiment is a sanity check
   before refining acceptance criteria.

What not to change:

- Existing tracker YAMLs (`bytetrack_museum.yaml`,
  `botsort_museum.yaml`).
- The privacy boundary. ReID still off; no faces; no demographic
  inference; no person crops.
- The `events.jsonl` schema.
- The Colab batch run that is still in progress. This experiment
  is on local CPU only.

Privacy boundary:

- Sample video already used in Step 1 and Step 2.
- All output is camera-local anonymous track ids.
- Overlays in `runs/h1_*` may show visitors; do not commit
  overlays. They are already covered by `.gitignore` (`runs/`).
- No new identifiers introduced.

Metrics needed:

Same as Step 2: `unique_track_count`, `real_track_count`,
`fallback_track_count`, `duration_seconds.median`, `short_lived_track_count`,
`likely_id_switch_count`, `gap_stats.total_gaps`,
`gap_stats.max_gap_processed_frames`, `tracks_per_minute`,
`run_seconds`. Plus the user's visual verdict in the log.

Failure modes:

- `compare_runs.py` writes "unknown" for tracker on the new run.
  Mitigate by adding the suffix.
- New YAML rejected by Ultralytics due to typo. Mitigate by
  copy-edit from existing `botsort_museum.yaml`, change only
  `track_buffer`.
- User cannot see a clear winner on a 17-second clip. Acceptable
  outcome - tells us the visual signal is weak at this scale and
  the Colab full-length run is the real test.

Status: Drafted by Claude. Awaiting Codex implementation. Run in
parallel with the Colab batch; do not block on Colab finishing.

### 2026-05-07 - Partial Local 4-Tracker Smoke Attempt

Date: 2026-05-07

From: Codex

To: User and Claude Opus 4.7

Topic: Started Claude's 4-tracker buffer hypothesis smoke test locally, but the
full overlay run timed out.

Implemented before running:

- Added `configs/trackers/botsort_museum_long.yaml` with `track_buffer: 180`.
- Updated tracker config schema/privacy tests to cover the long-buffer config.
- Updated `scripts/compare_runs.py` to recognize `botsort_museum_long`.
- Added `scripts/run_4tracker_smoke.ps1`.
- Ran tests: `.\.venv\Scripts\python.exe -m pytest -v` passed with 20 tests.

Run attempt:

- Started `scripts/run_4tracker_smoke.ps1`.
- The command timed out after the long local overlay workload.
- `runs/h1_baseline` completed with `metrics_summary.json` and `overlay.mp4`.
- `runs/h1_bytetrack_museum` produced a partial `overlay.mp4` but no
  `metrics_summary.json`, so it is not a valid comparison run.
- Two leftover ByteTrack processing Python processes were found and stopped.

Interpretation:

- The local full-overlay 4-tracker smoke test is too slow/risky to run as one
  blocking script on the laptop while Colab is also in use.
- Do not use the partial `h1_bytetrack_museum` output for decisions.
- The long-buffer config and comparison-script support are ready, but the smoke
  test should be rerun later either:
  - one tracker at a time;
  - with `--max-frames` / lower `--image-size`;
  - or on Colab after the current CCTV batch finishes.

Status: Partial attempt recorded. No tracker decision from this run.

### 2026-05-11 - Colab Real-CCTV Batch Results (3 clips x 3 trackers)

Date: 2026-05-11

From: Claude Opus 4.7 (dual-role mode; Codex out until 2026-05-12)

To: Codex and the user

Topic: Results of the Colab batch comparison on the three real
experience-center CCTV clips. Numbers logged; acceptance criteria applied;
no tracker default changed.

Run conditions:

- Colab Pro/free T4 GPU, `cuda` device.
- Zone-less `configs/eval/tracker_only.json` base, three runtime tracker
  variants (baseline, museum ByteTrack, museum BoT-SORT).
- `--no-overlay`, `frame_stride=1`, `image_size=1280`, `conf=0.18`.
- One-clip-at-a-time strategy (3 runs per Colab session) after earlier
  runtime resets wiped a prior multi-clip batch.

Clips (all from Drive `Visitor analysis/`):

- `gallery_clip1` = `20260507140240.mp4`
- `gallery_clip2` = `20260507140651.mp4`
- `gallery_clip3` = `20260507140752.mp4`

Note: filenames decode (YYYYMMDDHHMMSS) as all three from 2026-05-07 within
~7 minutes, not three weekend days as originally planned. User to confirm
whether to treat these as the canonical comparison or re-source clips
spread across days. Recording them here as `gallery_day1/2/3` in the
output for traceability of what was actually evaluated.

Per-clip results (rounded to two decimals where applicable):

Clip 1 (`gallery_day1`):

| metric | baseline | bytetrack_museum | botsort_museum |
| --- | ---: | ---: | ---: |
| unique tracks | 958 | 769 | 708 |
| real tracks | 943 | 755 | 695 |
| fallback tracks | 15 | 14 | 13 |
| duration median (s) | 1.48 | 2.28 | 2.56 |
| short-lived tracks | 407 | 283 | 243 |
| likely ID switches | 438 | 310 | 250 |
| total gaps | 3,216 | 3,413 | 3,268 |
| max gap (frames) | 31 | 90 | 90 |
| tracks per minute | 54.79 | 43.87 | 40.38 |
| run seconds | 836.72 | 823.45 | 1,584.29 |
| track_buffer | null | 90 | 90 |

Clip 2 (`gallery_day2`):

| metric | baseline | bytetrack_museum | botsort_museum |
| --- | ---: | ---: | ---: |
| unique tracks | 1,470 | 1,149 | 1,026 |
| real tracks | 1,468 | 1,147 | 1,024 |
| fallback tracks | 2 | 2 | 2 |
| duration median (s) | 1.28 | 2.16 | 2.32 |
| short-lived tracks | 658 | 430 | 368 |
| likely ID switches | 1,025 | 589 | 479 |
| total gaps | 5,421 | 5,851 | 5,605 |
| max gap (frames) | 31 | 91 | 90 |
| tracks per minute | 89.10 | 69.61 | 62.15 |
| run seconds | 820.71 | 822.00 | 1,514.97 |
| track_buffer | null | 90 | 90 |

Clip 3 (`gallery_day3`):

| metric | baseline | bytetrack_museum | botsort_museum |
| --- | ---: | ---: | ---: |
| unique tracks | 829 | 718 | 687 |
| real tracks | 751 | 640 | 611 |
| fallback tracks | 78 | 78 | 76 |
| duration median (s) | 1.28 | 1.64 | 1.72 |
| short-lived tracks | 343 | 265 | 246 |
| likely ID switches | 398 | 285 | 259 |
| total gaps | 1,952 | 2,024 | 1,960 |
| max gap (frames) | 31 | 87 | 87 |
| tracks per minute | 47.01 | 40.06 | 38.25 |
| run seconds | 682.97 | 757.23 | 1,452.00 |
| track_buffer | null | 90 | 90 |

Cross-clip totals (3 clips combined):

| metric | baseline | bytetrack_museum | botsort_museum |
| --- | ---: | ---: | ---: |
| total unique tracks | 3,257 | 2,636 | 2,421 |
| total real tracks | 3,162 | 2,542 | 2,330 |
| total likely ID switches | 1,861 | 1,184 | 988 |
| total short-lived | 1,408 | 978 | 857 |
| total run seconds | 2,340.40 | 2,402.68 | 4,551.26 |

Reductions vs baseline (computed from the totals above):

- bytetrack_museum: -19.1% unique tracks, -36.4% likely switches,
  -30.5% short-lived, +2.7% runtime.
- botsort_museum: -25.7% unique tracks, -46.9% likely switches,
  -39.1% short-lived, +94.5% runtime (~1.95x).

Observations:

- Stability ranking is identical on all three clips: botsort_museum best,
  bytetrack_museum middle, baseline worst on every stability metric.
- `botsort_museum` is consistently ~1.9x the wall-clock time of the other
  two trackers across all three clips.
- Clip 3 shows a notable jump in `fallback_track_count` (~77 vs 13-15 on
  clips 1/2), suggesting heavier occlusion or harder detector conditions.
  Worth flagging if Codex sees a recurring pattern in future clips.
- Clip 2 `bytetrack_museum` shows `max_gap_processed_frames = 91`, one
  frame over the configured `track_buffer = 90`. Edge case; recording it
  as a note for `track_diagnostics` review (could be a measurement off-by-one
  vs Ultralytics' internal counter). Not a blocker.
- `real_track_count` DECREASED for both tuned trackers vs baseline on all
  three clips. The handoff criterion #2 said "not increased" - decreasing
  passes the literal text. Interpretation: tuned trackers appear to be
  consolidating fragmented baseline tracks rather than missing detections
  (consistent with longer median duration and fewer likely switches).
  Cannot be proven from these aggregates alone; would need per-frame
  detection count comparison or visual spot-check.

Applying the 5-condition acceptance criteria for promoting
botsort_museum to project default (from the 2026-05-07 handoff):

1. `likely_id_switch_count` reduced >=20% vs baseline:
   - Clip 1: 42.9% reduction. PASS.
   - Clip 2: 53.3% reduction. PASS.
   - Clip 3: 34.9% reduction. PASS.
2. `real_track_count` not increased vs baseline:
   - All three clips show decreases. PASS.
3. `duration_median` >= baseline:
   - All three clips show increases. PASS.
4. `max_gap_processed_frames` does not saturate the 90-frame buffer on
   more than 10% of tracks:
   - UN-MEASURABLE with current diagnostics (only one max-gap aggregate
     per run, no per-track gap histogram). This was flagged in the
     2026-05-07 4-tracker hypothesis handoff.
   - Point estimate: clip 1 botsort hits exactly 90, clip 2 botsort hits
     90 (and bytetrack 91), clip 3 both at 87. At minimum the buffer is
     being touched on the largest gap of multiple runs.
5. Direction consistent across all clips: PASS for criteria 1-3.

Verdict per the original rules: 4 of 5 criteria pass; criterion 4 is
un-measurable with current diagnostics. Default tracker is NOT promoted.
This matches the original handoff: "If any fail: do NOT change default."

Recommended next steps (no implementation yet; awaiting user direction):

1. Resolve the same-day vs different-day question on the clips. If user
   wants three different days, re-record/re-evaluate. If same-day is
   acceptable for this round, mark these results as the canonical first
   batch with the caveat noted above.
2. Make criterion 4 measurable. Two options for Codex when back:
   a. Add `gap_stats.gaps_at_buffer_ceiling` (count of gaps >= 80% of
      configured `track_buffer`) and `gap_stats.tracks_at_buffer_ceiling`
      (count of tracks whose max gap saturated) to `track_diagnostics`.
      Already proposed in the 4-tracker handoff as optional follow-up.
   b. Soften criterion 4 to "max gap aggregate <= configured buffer" and
      note it in the ADR.
3. Save the 9 per-run `metrics_summary.json` files from Colab into the
   repo under `runs/colab_2026_05_07/{clip}_{tracker}/` (JSON only, no
   video, no overlays) so the raw evidence is in version control.
   STATUS 2026-05-11: not possible. The Colab runtime reset between
   batches. `/content/` was empty (only `sample_data`) when checked
   after the clip 3 download. Only the three comparison CSV/JSON
   summary files are preserved (the ones the user emailed/uploaded).
   For future batches, add a "copy `metrics_summary.json` files to
   Drive after each clip" cell to the notebook so the raw evidence
   survives a runtime reset.
4. Do NOT open the ReID ADR yet. The tuned trackers got us a 36-47%
   reduction in likely switches with no privacy expansion. ReID remains
   gated on whether a future delta justifies the privacy cost.

Files affected by this entry:

- This log only. No code changes. No git operations.

Verification:

- Numbers above are transcribed from
  `uploads/comparison_real_cctv.csv`, `uploads/comparison_real_cctv (1).csv`,
  and `uploads/comparison_real_cctv (2)-711f2fef.csv` provided by the user
  on 2026-05-11. CSVs read in place; no re-computation performed beyond
  totals and percentages shown.
- Reductions recomputed: e.g. botsort vs baseline likely switches =
  (1861 - 988) / 1861 = 0.4691 -> 46.91% -> rounded to 46.9%.

Privacy boundary: unchanged. No ReID, no faces, no demographic/emotion
inference, no person crops, no raw video committed. All metrics are
aggregate counts.

Status: Logged. Awaiting user decision on same-day clip question and
Codex return for any code changes (criterion 4 measurability,
metrics_summary persistence).

### 2026-05-12 - Correction: Real CCTV Clips Are Different Days

Date: 2026-05-12

From: User via Codex

To: Claude Opus 4.7 and Codex

Topic: Correcting the interpretation of the real-CCTV Colab batch clips.

Correction:

- The three clips used in the Colab real-CCTV batch are from different days.
- They are from the same location, same time window, and same camera.
- The earlier caveat that filenames appeared to be from the same day should not
  be treated as a project conclusion.

Updated interpretation:

- The Colab batch should be treated as a valid first multi-day, same-camera
  validation set.
- The BoT-SORT stability improvements are stronger evidence than previously
  stated, because they held across different days, not merely adjacent clips.
- The remaining blocker is not clip diversity; it is the unmeasurable buffer
  saturation criterion and the missing persisted per-run `metrics_summary.json`
  files after Colab runtime reset.

Status: Correction recorded. Future analysis should treat the batch as
different-day validation unless the user provides new contradictory evidence.

### 2026-05-13 - Visual Verification Attempt 1 Produced No Overlays (Config Slip)

Date: 2026-05-13

From: Claude Opus 4.7 (dual-role while Codex offline)

To: Codex on return, and user record

Topic: First overlay-ON visual verification run on clip 1 produced no
`overlay.mp4` files. Root cause identified. Re-run plan below.

What happened:

- User reopened `notebooks/colab_tracker_comparison.ipynb` on Colab T4 and ran
  the visual verification on clip 1 (`gallery_clip1_visual`) across all three
  trackers with `--max-frames 1800` and no `--no-overlay` flag.
- Three runs completed cleanly:
  - `gallery_clip1_visual_baseline` in 68.5 s
  - `gallery_clip1_visual_bytetrack_museum` in 56.6 s
  - `gallery_clip1_visual_botsort_museum` in 111.3 s
- The copy-to-Drive cell ran and printed `Done`.
- Drive folder `MyDrive/Visitor analysis/overlays_visual_check/` was empty.

Root cause:

- `configs/eval/tracker_only.json` has `"write_overlay": false` on line 18.
- `notebooks/colab_tracker_comparison.ipynb` cell that builds the runtime
  configs hardcodes `config['processing']['write_overlay'] = False` (line 171
  of the .ipynb source) before saving each per-tracker config to
  `/content/runtime_configs/`.
- The CLI has `--no-overlay` to force overlay off, but no flag to force it on.
  So removing `--no-overlay` from the batch loop did nothing: the per-tracker
  configs already had `write_overlay: false` baked in by the notebook.
- All three runs executed without an overlay writer, so no `overlay.mp4` was
  ever created. The copy cell iterated `runs_dir` and found nothing to copy,
  which is why it printed `Done` with no error.

My responsibility:

- I drafted the visual verification plan and instructed the user to drop
  `--no-overlay` without checking the notebook's config-generation cell. That
  was the gap. Logging it here so Codex sees the failure mode on return.

Re-run plan (in progress, owner: user, walked through by Claude):

1. Clean prior runs: `!rm -rf /content/runs /content/runtime_configs`
2. Edit the notebook cell that contains
   `base_config = json.loads(Path('configs/eval/tracker_only.json').read_text())`
   and change
   `config['processing']['write_overlay'] = False`
   to
   `config['processing']['write_overlay'] = True`.
3. Re-run that cell (regenerates runtime configs with overlay enabled).
4. Re-run the batch comparison cell (3 trackers x 1 clip, ~5-10 min total).
5. Re-run the copy-to-Drive cell. Overlays should now appear in
   `MyDrive/Visitor analysis/overlays_visual_check/`.

Followup for Codex when back:

- Consider adding a `--overlay` CLI flag in `cli.py` to mirror `--no-overlay`,
  so future eval runs can flip overlay on without editing the base config or
  the notebook. Trivial change, prevents a class of slip-ups.
- Optionally: refactor the notebook so the `write_overlay` value in the
  config-generation cell is a top-level variable the user can flip from the
  outside, instead of being buried inside the cell body.

Privacy boundary: unchanged. Overlays show only bounding boxes and track IDs.
No raw video committed. No ReID, no faces, no demographics.

Status: User executing re-run now. Will append the visual verdict to this log
once user has watched the overlays.

### 2026-05-14 - Overlay Visual Check Controls Added

Date: 2026-05-14

From: Codex

To: User and Claude Opus 4.7

Topic: Fixed the workflow so the user can generate `overlay.mp4` files to see
how boxes and track IDs follow people.

Implementation:

- Added `--overlay` CLI flag to force overlay generation even when the config
  has `write_overlay: false`.
- Kept `--no-overlay` for fast metric-only runs.
- Added a guard so `--overlay` and `--no-overlay` cannot be used together.
- Updated `notebooks/colab_tracker_comparison.ipynb` with explicit top-level
  controls:
  - `WRITE_OVERLAY`
  - `MAX_FRAMES`
  - `FRAME_STRIDE`
  - `IMAGE_SIZE`
- Updated the notebook batch command to use `--overlay` when
  `WRITE_OVERLAY = True`.
- Added a notebook cell to copy generated overlays to:
  `MyDrive/Visitor analysis/overlays_visual_check/`.

Recommended visual-check setting:

```python
WRITE_OVERLAY = True
MAX_FRAMES = 1800
FRAME_STRIDE = 1
IMAGE_SIZE = 1280
```

Expected output:

- `gallery_day1_baseline_overlay.mp4`
- `gallery_day1_bytetrack_museum_overlay.mp4`
- `gallery_day1_botsort_museum_overlay.mp4`

Verification:

- Notebook JSON validated locally.
- `.\.venv\Scripts\python.exe -m pytest -v` passed with 22 tests.

Status: Ready for user to re-run the Colab visual check and watch the overlay
videos.

### 2026-05-14 - Codex Back, Claude Reverting To Review-Only

Date: 2026-05-14

From: Claude Opus 4.7

To: Codex and user

Topic: Acknowledging Codex back online. Reverting to review-only per the
standing dual-role rule in `CLAUDE.md`.

What Claude did during the gap:

- Reviewed user uploads of `comparison_real_cctv.csv/.json` for clips 1-3,
  computed cross-clip totals and percentage reductions, and scored against the
  5-criterion acceptance test (4 pass, 1 un-measurable). Logged on
  2026-05-11.
- Acknowledged user's correction that clips are different-day, not same-day,
  and recorded the updated interpretation. Logged on 2026-05-12.
- Drafted a visual-verification plan instructing the user to drop
  `--no-overlay`. That plan was incomplete: the notebook's runtime-config cell
  hardcoded `write_overlay = False`, so the first re-run on 2026-05-13
  produced no overlay videos. Slip-up logged on 2026-05-13.

Verification of Codex's 2026-05-14 fix:

- `src/museum_gallery_ai/cli.py` line 25: `--overlay` flag added.
- `src/museum_gallery_ai/cli.py` line 62: mutual-exclusion guard against
  passing both `--overlay` and `--no-overlay`.
- `notebooks/colab_tracker_comparison.ipynb` lines 157-160: top-level
  `WRITE_OVERLAY`, `MAX_FRAMES`, `FRAME_STRIDE`, `IMAGE_SIZE` controls.
- Notebook batch cell branches on `WRITE_OVERLAY` to add `--overlay` to the
  CLI command.
- Codex reports 22 pytest cases pass.

Outstanding items Claude flagged that Codex may still want to pick up:

- Criterion 4 (per-track buffer saturation) is still un-measurable because
  `track_diagnostics.py` does not emit a per-track gap distribution. Optional
  improvement after the visual verdict, not a blocker for the visual check
  itself.
- bytetrack_museum gave `max_gap_processed_frames = 91` on clip 2 with
  configured buffer 90. Possibly an off-by-one in how diagnostics counts
  gaps. Not affecting the visual check; flag for later.

Claude returning to:

- research and architecture review;
- privacy and risk review;
- code-review style critique;
- test-plan design.

Codex resumes primary local repository operator role.

Status: Claude in review-only mode from 2026-05-14 onward unless user signals
otherwise.

### 2026-05-14 - Codex Handoff: Tracker Flicker, Proximity-Merge, and ReID Investigation

Date: 2026-05-14 (evening; supersedes the day's earlier ReID-experiment
entry below)

Reading order note: This entry is the final state of 2026-05-14. The
"One-Off Offline ReID Experiment Authorised" entry that appears below in
the file chronologically came earlier in the day. Read this entry as the
current state; the ReID-experiment entry as the authorisation that
preceded it.

From: Claude Opus 4.7 (research role)

To: Codex (primary repository operator)

User authorisation: explicit ("hand the entire case to codex from where we
last stopped on the communication log, be precise do not miss anything").

Topic: Hand the full case to Codex for implementation under
`docs/PROJECT_START_WORKFLOW.md`. The investigation behind this handoff is
in `docs/research/0005-tracker-flicker-and-nms-merging.md`. Codex must
review that document before touching any file.

#### Where we last stopped (timeline since the 2026-05-12 entry)

1. 2026-05-13 - Visual verification attempt 1 produced no overlays due to
   `write_overlay=False` hardcoded in the notebook. Logged that day.
2. 2026-05-14 (Codex) - Added `--overlay` CLI flag and notebook top-level
   `WRITE_OVERLAY` / `MAX_FRAMES` / `FRAME_STRIDE` / `IMAGE_SIZE` controls.
   Tests pass.
3. 2026-05-14 (user + Claude) - User ran the overlay verification on
   `gallery_day1` for all 3 trackers (baseline, bytetrack_museum,
   botsort_museum) and watched the videos. User verdict: detector boxes
   are on real people (good); but **same-person ID changes within
   sub-second windows** when boxes flicker; same-person ID changes after
   proximity-merge with another visitor (case 3); same-person new ID after
   full occlusion of >3.6 s (case 2).
4. 2026-05-14 (user) - Authorised a one-off offline ReID experiment for
   `gallery_day1` only. Boundary documented in the
   "2026-05-14 - One-Off Offline ReID Experiment Authorised" entry below.
5. 2026-05-14 (user + Claude) - User ran BoT-SORT with `with_reid: True` +
   `model: auto` on `gallery_day1`. Watched the new overlay. Verdict:
   "ID across occlusion: same or very slight improvement." Then confirmed
   in a follow-up: "i confirm that re-id is not working. in our current
   status."
6. 2026-05-14 (Claude) - Dense-frame inspection at 0:50-1:10 of the
   non-ReID and ReID overlays confirmed visually that proximity-merge
   collapses two boxes into one, and that the recovered detections after
   separation receive fresh IDs in **both** the no-ReID and the ReID
   runs.
7. 2026-05-14 (Claude) - Drafted hypotheses (NMS over-aggressive, ReID
   appearance gate too strict, new-track-spawn too cheap). User
   reminded Claude of `AGENTS.md` lines 53-55 and
   `docs/PROJECT_START_WORKFLOW.md` requirement: research first, cite
   authentic sources, plan, discuss, approve, then implement.
8. 2026-05-14 (Claude) - Did the research with primary sources
   (Ultralytics official docs, `ultralytics/trackers/bot_sort.py` source
   on GitHub HEAD, PR #20192 release notes for v8.3.114, issue #20391,
   issue #20498, the PR author's tutorial, our own
   `src/museum_gallery_ai/detector.py` and tracker YAMLs). Output is
   `docs/research/0005-tracker-flicker-and-nms-merging.md`.

#### Key facts Codex needs to know

KF1. Our NMS IoU threshold is `iou=0.4` in `src/museum_gallery_ai/detector.py`
line 28. Ultralytics default is 0.7. A lower value = more aggressive
suppression. For pedestrian-close scenes this is the wrong direction.

KF2. `with_reid: True` + `model: auto` in BoT-SORT only works for ReID
when Ultralytics version is **>= 8.3.114** (PR #20192, April 2025).
Our `requirements.txt` pins `ultralytics>=8.3` with no upper bound.
The installed version in `.venv` and in Colab needs to be verified.

KF3. With `appearance_thresh: 0.8` (our config) the appearance branch of
the cost matrix is effectively closed. Native YOLO detection features
are not appearance-discriminative enough to clear a 0.2 distance gate
on distant CCTV crops. The PR author's reference tutorial recommends
`0.3` for native features. This is the most likely reason the ReID
experiment looked indistinguishable from no-ReID.

KF4. `new_track_thresh: 0.30` is permissive. Any detection above 0.30
confidence can spawn a brand-new ID without first trying to match an
existing track. Recovered post-merge detections come back at conf
0.5-0.85, well above this threshold.

KF5. `match_thresh: 0.8` corresponds to "match accepted whenever
`1 - IoU` <= 0.8", i.e. IoU >= 0.2. That is **permissive**, not strict.
Claude initially mis-stated this; the matching gate is not the
problem.

KF6. The 243 "short-lived tracks" headline on `gallery_day1`
botsort_museum is over-counted by the same physical visitors being
re-spawned multiple times. The metric is real, the interpretation we
were attaching to it ("243 distinct short visits") was wrong.

KF7. Three different things have been called "occlusion" in our
discussion. They are distinct:
- Case 1: partial occlusion (lower body behind a cone) -> Layer 2
  flicker.
- Case 2: full occlusion >3.6 s -> Layer 3 ReID (would solve, but
  our ReID gate is closed; see KF3).
- Case 3: proximity-merge of two boxes -> Layer 2 NMS + Layer 3
  new-track-spawn. ReID cannot help case 3 because no separate
  embedding is extracted for the visitor whose box was suppressed.

#### Goal

Reduce same-visitor ID churn on single-camera museum CCTV without
crossing the project's privacy boundary, by tuning Layer 2 (detector
NMS) and Layer 3 (tracker spawn / appearance thresholds) one knob at a
time on the recorded `gallery_day1` clip.

#### Files likely involved

- `src/museum_gallery_ai/detector.py` line 28 — `iou=0.4` (NMS IoU
  threshold). May need to be exposed via config or overridden in an
  experiment YAML.
- `configs/trackers/botsort_museum.yaml` — `new_track_thresh`,
  `appearance_thresh`, `match_thresh`, `with_reid`, `model`,
  `proximity_thresh`. **Do not modify the committed file as part of an
  experiment.** Create sibling experimental YAMLs.
- `configs/trackers/bytetrack_museum.yaml` — same knobs that exist
  there. Keep consistent for fair comparison if Codex runs ByteTrack
  too.
- `notebooks/colab_tracker_comparison.ipynb` — section 4 already has
  the top-level controls. The TRACKERS dict will need an experimental
  variant entry per run.
- `requirements.txt` — `ultralytics>=8.3` may need to be tightened
  to `>=8.3.117,<8.4` so all environments agree on ReID-capable
  versions.
- `src/museum_gallery_ai/overlay.py` — only relevant if Codex pursues
  Option B (draw Kalman-predicted boxes). Out of MVP scope unless the
  user prioritises a stakeholder-demo cosmetic fix.

#### Proposed change (sequence, one at a time)

The full plan is section 8 of
`docs/research/0005-tracker-flicker-and-nms-merging.md`. Summarised:

M1. Pin Ultralytics version in `requirements.txt` to a known-good range
that includes native ReID + the encoder-init bug fix:
`ultralytics>=8.3.117,<8.4`. Update `.venv` and Colab to match.

M2. Experiment A.1 — raise NMS `iou` from 0.4 to 0.5. Done by either
adding an `iou` override field to the eval config or via a small
detector-level CLI flag. Run on `gallery_day1` with overlay ON,
compare numerically and visually at 0:50 vs the existing
`gallery_day1_botsort_museum_overlay.mp4`.

M3. Experiment A.2 — raise `new_track_thresh` from 0.30 to 0.50 in a
sibling file `configs/trackers/botsort_museum_a2.yaml`. Run as above.

M4. Optional Experiment C — re-run ReID with `appearance_thresh: 0.3`
in a sibling file `configs/trackers/botsort_museum_reid_tuned.yaml`.
Same offline boundary as the 2026-05-14 ReID experiment authorisation
(no deployment, no person crops, no commits of generated runs).

M5. Compare results. If a knob combination shows a clear improvement,
write a new ADR proposing the default change.

M6. Only after the ADR and user's explicit approval, change the
committed `botsort_museum.yaml` or `detector.py` defaults.

#### Verification commands

```powershell
# Verify the installed Ultralytics version
.\.venv\Scripts\python -c "import ultralytics; print(ultralytics.__version__)"

# Smoke test the current pipeline (should still pass)
.\.venv\Scripts\python -m pytest

# Per-experiment run (example for A.1, parameters illustrative)
.\.venv\Scripts\python -m museum_gallery_ai process `
    --config configs/eval/tracker_only.json `
    --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" `
    --output runs/exp_a1_iou_0_5 `
    --overlay --max-frames 1800
```

(Colab runs use the existing `colab_tracker_comparison.ipynb`. The
TRACKERS dict and runtime config JSON would need to point at the
experiment YAML.)

#### Risks or open questions

- R1. Tuning multiple knobs at once will obscure causality. Codex
  should run one knob change per experiment.
- R2. Raising NMS `iou` may produce double boxes on a single person in
  some poses. First step is `iou=0.5`, not larger; verify visually.
- R3. Lowering `appearance_thresh` to 0.3 may produce cross-person ID
  reuse (worse than fresh-ID spawn for analytics). Keep
  `proximity_thresh: 0.5` as a position gate.
- R4. Ultralytics installed version is currently unverified. M1
  resolves this. Without M1, A.1 and A.2 should still be safe because
  they touch knobs that existed long before PR #20192.
- Q1. Ultralytics version in `.venv` and Colab — needs `pip show
  ultralytics` in both.
- Q2. Quantify the proximity-merge re-spawn rate from
  `events.jsonl` of one of the existing BoT-SORT runs. Optional
  before M2, mandatory before writing the ADR in M5.

#### What NOT to change

- Do **not** flip `with_reid: True` in the committed
  `configs/trackers/botsort_museum.yaml`. Committed config continues
  to reflect privacy policy.
- Do **not** edit `MUSEUM_GALLERY_AI_BLUEPRINT.md` or any approach
  document on the basis of this brief alone. Any such edit goes
  through an ADR.
- Do **not** commit generated run outputs (`runs/exp_*` directories,
  overlay mp4s, events.jsonl, metrics_summary.json) — per
  `AGENTS.md` Git Guidelines.
- Do **not** introduce face recognition, person crops, demographic or
  emotion inference. Privacy boundary unchanged.
- Do **not** start multi-camera fusion work; that is still
  deliberately deferred per `CLAUDE.md`.

#### Privacy boundary

Unchanged. The full plan in
`docs/research/0005-tracker-flicker-and-nms-merging.md` section 9
states: A.1, A.2, and Option B do not touch ReID; Option C reuses the
boundary already authorised for the 2026-05-14 offline ReID experiment;
Option D is detector-only. The committed `with_reid: False` continues
to reflect policy. Visitor consent is a separate workstream the user
has indicated will be handled by the legal team.

#### Metrics needed (per experiment)

- `unique_track_count`
- `real_track_count`
- `short_lived_count`
- `likely_switch_count`
- `total_gaps`
- `max_gap_processed_frames`
- `run_seconds`
- A 5-frame visual snapshot at video time 0:50.5 to inspect the
  proximity-merge moment

These already exist in `metrics_summary.json` from
`scripts/compare_runs.py`. The visual snapshot is new and can be a
manual step (Codex extracts the 5 frames after the run completes).

#### Failure modes to watch for

- F1. Run completes but `metrics_summary.json` is missing or
  truncated — likely a runtime reset (see 2026-05-11 lesson). Copy
  metrics to Drive immediately after each run, not at the end of the
  batch.
- F2. Box-on-shadow false positives appear after lowering NMS or
  confidence — visible in overlay as boxes on the floor.
- F3. Two boxes on the same person after raising NMS `iou` —
  cap the value and inspect.
- F4. Tracks live longer but identity is wrong (Track 20 now contains
  two different people) — visible by watching the overlay; numerical
  signal is `unique_track_count` dropping below the visitor head-count
  estimate.

#### Codex's role from here

Codex reviews this entry and
`docs/research/0005-tracker-flicker-and-nms-merging.md`. Codex then
proposes either (a) "start with M1+M2, here are the exact file edits
and the run command", or (b) "I disagree with X in the plan, here is
my counter-proposal", and waits for user approval before changing
files.

Claude stays in review-only mode and is available for clarification,
test-plan review, and architecture critique on Codex's proposal.

Status: Handoff complete. Awaiting Codex review and user approval.

### 2026-05-14 - One-Off Offline ReID Experiment Authorised

Date: 2026-05-14

From: User (iria@paraminnovation.org) via Claude

To: Codex and project record

Topic: User has authorised a one-off offline experiment that flips
`with_reid: True` on BoT-SORT for the recorded `gallery_day1` clip, in order
to see whether appearance-based ReID visibly resolves the
ID-after-occlusion failure the user observed in the overlay videos.

Scope and boundary:

- Offline only. Recorded video file. No live camera, no live deployment.
- One clip (`gallery_day1`, 1800 frames, ~72 s).
- Output: `overlay.mp4`, `events.jsonl`, `metrics_summary.json`. No person
  crops saved. No embeddings persisted to disk. Embeddings exist only in
  memory during the run.
- The experiment is run in Colab on user-owned recordings stored in user's
  private Drive folder.
- Legal/visitor consent track is separate. User stated: "we will let the
  legal team take consultation from the visitors, for now from the recorded
  videos we shall do this experiment".

What this experiment is NOT:

- It is NOT a deployment decision.
- It does NOT change the `MUSEUM_GALLERY_AI_BLUEPRINT.md` privacy policy.
- It does NOT flip the committed `configs/trackers/botsort_museum.yaml` —
  that file stays `with_reid: False`. The experiment uses a separate
  experimental config (`botsort_museum_reid.yaml`) or an inline override on
  the Colab VM, so the repo state continues to reflect the policy.
- The result of this experiment is descriptive (does ReID work for this
  scene?), not normative (should we deploy ReID?).

Followup gate (still applies for any future deployment):

- A written ADR documenting the privacy review.
- Visitor-facing signage and consent process.
- A retention policy for ReID embeddings (currently: none — embeddings are
  in-memory only).
- A blueprint amendment if the policy direction changes.

Status: Walking user through the Colab procedure now. Findings will be
appended to this entry.

### 2026-05-18 - Correction: Overlay Generation Already Works; Commit ebdb142 Is Cleanup, Not Unblock

Date: 2026-05-18

From: Claude (Opus 4.7) — review-only mode

To: Codex and project record

Topic: Correct a wrong inference Claude made while walking the user
through the Colab git-sync flow today. Also record two verified facts
from the Colab run.

#### What Claude got wrong

While inspecting the user's notebook cell that builds the per-tracker
JSON configs, Claude saw it already wrote `write_overlay: True` and
then incorrectly concluded that overlay video generation must still be
blocked elsewhere (Claude speculated about a `--no-overlay` CLI flag
overriding the config). Claude did not verify this claim against the
overlay videos the user had already uploaded in earlier sessions.

The user pushed back. The user is correct.

#### What is actually true

Overlay generation has been working in Colab since the user applied
the manual section-5 workaround in the prior session. Evidence:

- The user uploaded `gallery_day1_baseline_overlay.mp4`,
  `gallery_day1_bytetrack_museum_overlay.mp4`,
  `gallery_day1_botsort_museum_overlay.mp4`, and
  `gallery_day1_botsort_museum_reid_overlay.mp4` in earlier turns. All
  four files exist and were analysed via ffmpeg (1920x1080, 25 fps,
  1800 frames, ~99 MB each).
- The frame extracted at 0:50 was from one of those overlay outputs.
- The proximity-merge / flicker observation in
  `docs/research/0005-tracker-flicker-and-nms-merging.md` is based on
  those existing overlay videos, not on hypothetical output.

Effect of commit `ebdb142` (today's push,
"Approach 2: add Colab overlay control for visual tracker checks") is
therefore a **cleanup, not a blocker fix**:

- Before: overlay produced only after a manual delete of the
  `--no-overlay` line in section 5.
- After: overlay produced out of the box when `WRITE_OVERLAY = True`
  in the top-level notebook control.

Net effect on findings, plan, and research conclusions: none. The
research document and Codex handoff remain valid as written.

#### Two verified facts from the Colab run today

V1. Ultralytics version on Colab is `8.4.51` (confirmed in pip
install output). This is well above the `8.3.114` minimum required
for native-features ReID (PR #20192). This resolves Q1 from
`docs/research/0005-tracker-flicker-and-nms-merging.md` for the Colab
environment. Local `.venv` version is still unverified.

V2. All 22 tests pass on the fresh Colab clone of
`codex/approach-2-id-stability` at commit `ebdb142`. No regressions
from today's commit. Test names captured in the user's terminal
output if needed for the record.

#### One housekeeping note

The pushed commit hash differs from what Claude expected. Claude
predicted `9130157`, the actual commit on `origin` is `ebdb142`. The
commit **message** is identical
("Approach 2: add Colab overlay control for visual tracker checks").
The hash changed because the user ran `git stash` +
`git pull --rebase` + `git push` after the initial commit was
rejected for being non-fast-forward; rebase rewrites the commit and
gives it a new SHA. Same content, new hash. No action needed.

#### What Codex should NOT change because of this entry

- Do not modify `docs/research/0005-tracker-flicker-and-nms-merging.md`.
  The findings (F1-F9), assumptions (A1-A4), open questions (Q1-Q4,
  with Q1 now answered for Colab), risks (R1-R5), options (A.1, A.2,
  B, C, D), and milestone sequence (M1-M7) are unchanged.
- Do not modify the prior handoff entry
  "2026-05-14 - Codex Handoff: Tracker Flicker, Proximity-Merge, and
  ReID Investigation". The handoff stands as written.

#### Standing posture

Claude remains in review-only mode. Awaiting Codex's proposal on
whether to start with M1+M2 (detector NMS iou 0.4 → 0.5, then
new_track_thresh 0.30 → 0.50) or a counter-proposal, with exact file
edits and run commands, for user approval.

Status: Correction logged. No code or config changes. Plan unchanged.

### 2026-05-22 - CLAUDE.md Project Map And Routing Added

Date: 2026-05-22

From: Claude (Opus 4.7) — review-only mode

To: Codex and project record

Topic: User asked Claude to add a project routing table to `CLAUDE.md` so
the user no longer has to point Claude at specific files for every task,
and so the importance tiers of folders are explicit.

What changed:

- Replaced the short "Current Project Direction" section in `CLAUDE.md`
  with three sections: "Project Map And Routing" (importance tiers,
  topic-to-file routing table, conventions for where new files go) and
  "Active State" (latest commit posture and pending Codex proposal on
  M1+M2).
- No source code, config, tests, or research documents were edited. The
  privacy boundary and existing handoffs are unchanged.

Files affected:

- `CLAUDE.md` (single edit, replaces the "Current Project Direction"
  block; everything else in the file is preserved).

Verification:

- Visual diff only. No tests run (no code changed).
- Pre-existing instruction in `AGENTS.md` ("Update documentation or the
  communication log when the task changes project direction") is the
  reason this entry exists despite not changing project direction.

User decision needed: None. Codex should be aware that future routing
decisions made by Claude will follow the table in `CLAUDE.md`. If Codex
disagrees with any tier label or routing entry, please add a counter-note
here.

Status: CLAUDE.md updated. Project direction unchanged. Awaiting Codex's
M1+M2 proposal as before.

### 2026-05-22 - Colab Notebook Consolidated To notebooks/

Date: 2026-05-22

From: Claude (Opus 4.7) — assisting user with workflow change

To: Codex and project record

Topic: The Colab notebook now lives in the repo at
`notebooks/colab_tracker_comparison.ipynb` with cell outputs committed, so
both Claude and Codex can read run summaries directly without relying on
the user to paste console output.

What changed:

- Commit `eb3e052` "Consolidate Colab notebook to notebooks/; remove stray
  approach-2-id-stability/ duplicate" — pushed to
  `origin/codex/approach-2-id-stability`.
  - Restored `notebooks/colab_tracker_comparison.ipynb` with the latest
    Colab-run cell outputs (55 KB; previously this canonical path was
    showing as `D` in the working tree).
  - Removed the duplicate at `approach-2-id-stability/notebooks/` that had
    been committed earlier. The folder name matched the branch name
    suffix — almost certainly a clone-into-wrong-folder accident from a
    previous session.
- `CLAUDE.md` routing table updated to point notebook-related prompts at
  `notebooks/colab_tracker_comparison.ipynb`, and the file is listed under
  the "Active project context" tier.

New two-way sync convention:

- VS Code edits the `.ipynb` directly via the Jupyter extension; commit
  and push as normal.
- Colab pulls via the `!git pull` cell in section 3.
- After running cells in Colab, save back via "File → Save a copy in
  GitHub" (cleanest), or a `!git add / !git commit / !git push` cell.

Codex implications:

- Treat `notebooks/colab_tracker_comparison.ipynb` as a read/write asset
  of the same status as `src/`: never delete, never silently rewrite
  without a clear reason logged here.
- Cell outputs committed = noisier diffs. Acceptable trade-off for now;
  revisit `nbstripout` if it becomes a problem.

Notebook current state (NOT a bug — deliberate user scope reduction):

- The `TRACKERS` dict in section 4 currently contains ONE entry
  (`botsort_museum_reid`) and the `CLIPS` list has only `gallery_day1`
  active. This is deliberate: the user reduced scope to one tracker × one
  clip because the full 3×3 batch was taking too long on the Colab T4.
  Treat this configuration as the working default for ad-hoc runs, not as
  a configuration drift to fix.
- One follow-up worth flagging: the `compare_runs.py` invocation in
  section 6 still passes `--expected-runs 9`, which no longer matches the
  reduced scope. Either drop the literal to match the current scope, or
  parameterise it (`len(CLIPS) * len(TRACKERS)`). Non-urgent; only
  matters when the comparison cell is actually re-run.
- Scaling back up to the full 3-clip × 3-tracker matrix is a one-line
  edit each in `CLIPS` and `TRACKERS` (the entries for the earlier
  baseline / bytetrack_museum / botsort_museum runs are commented out in
  the notebook history). No structural changes needed.
- The privacy boundary in the top-level markdown remains intact (no
  committed videos / overlays / events, no person crops, no
  ReID-as-default).
- Section 3 writes `botsort_museum_reid.yaml` into the cloned repo's
  `configs/trackers/` on Colab. This is a runtime file in `/content`, not
  committed back; the committed repo continues to enforce
  `with_reid: False` per the privacy boundary.

Files affected:

- `notebooks/colab_tracker_comparison.ipynb` (modified; +863, −718).
- `approach-2-id-stability/notebooks/colab_tracker_comparison.ipynb`
  (deleted; tracked content removed).
- `CLAUDE.md` (routing additions, uncommitted in working tree).
- This file (uncommitted in working tree).

Verification:

- `git push` to `origin/codex/approach-2-id-stability` succeeded
  (`ebdb142..eb3e052`).
- No tests run because no production code changed.

User decision needed: None for the consolidation itself. Two open items:
(1) the `TRACKERS`-vs-`--expected-runs 9` mismatch should be resolved
before the next batch comparison; deferring to user / Codex. (2) The
M1+M2 proposal from research 0005 is still pending Codex review — no
change in posture from the 2026-05-18 entry.

Status: Notebook consolidated and pushed. Standing posture unchanged.

### 2026-05-22 - Approach 2 M1 + M2-prep Implemented (Dual-Role)

Date: 2026-05-22

From: Claude (Opus 4.7) — acting under the dual-role fallback rule
because Codex has not appeared in the log since 2026-05-18 and the user
chose to proceed with M1+M2 from research 0005.

To: Codex and project record.

Topic: First two milestones from
`docs/research/0005-tracker-flicker-and-nms-merging.md` section 8 are
implemented. M1 pins Ultralytics; M2-prep exposes the NMS `iou` knob as
a config field and CLI override so the experiment in M2 can be a runtime
config change rather than a committed-default change. **The committed
default behaviour is unchanged** (iou still 0.4 for every existing
config).

Files changed (uncommitted in working tree):

- `requirements.txt` — `ultralytics>=8.3` → `ultralytics>=8.3.117,<8.4`
  per research 0005 F2 / F8. Note: per the 2026-05-18 V1 entry, Colab
  was running 8.4.51 which violates this upper bound — Colab will
  downgrade on next `pip install -r requirements-dev.txt`. If a
  regression appears, that is the first thing to check.
- `src/museum_gallery_ai/models.py` — added `iou: float = 0.4` field to
  `DetectorConfig` (appended after `device` to keep positional
  construction safe).
- `src/museum_gallery_ai/detector.py:28` — `iou=0.4` →
  `iou=self.config.iou`.
- `src/museum_gallery_ai/cli.py` — added `--detector-iou` flag mirroring
  the `--image-size` override pattern, with range validation
  (`0.0 < x < 1.0`).
- `tests/test_config.py` — new `test_detector_iou_defaults_to_0_4` that
  loads `configs/demo.yaml` and asserts the default value.
- `tests/test_cli.py` — extended three existing `argparse.Namespace`
  fixtures to include `detector_iou=None`; added two new tests:
  `test_detector_iou_override_applies_to_detector_config` (happy path)
  and `test_detector_iou_override_rejects_out_of_range` (failure path).

Verification:

- `.\.venv\Scripts\python -m pytest -v` — 25 passed, 0 failed (up from
  22). The three new tests cover the M2-prep contract.
- No production runs executed yet — M2 is the experiment run itself,
  scheduled for Colab next.

Privacy boundary:

- No ReID code path enabled or changed.
- No commit of person crops, raw video, or run outputs.
- Committed `with_reid: False` in `configs/trackers/botsort_museum.yaml`
  unchanged.

What M2 itself looks like (Colab experiment, NOT a committed change):

Paste this as a NEW cell in `notebooks/colab_tracker_comparison.ipynb`
after section 4. It runs the same clip × same tracker config twice,
differing only in `iou`, and produces a 2-row comparison CSV:

```python
# M2 experiment: NMS iou 0.4 (current default) vs 0.5 on gallery_day1.
# Same clip, same tracker config, only the iou knob differs.
import subprocess
import time
from pathlib import Path

clip = CLIPS[0]  # gallery_day1
runs_dir = Path('/content/runs')
runs_dir.mkdir(parents=True, exist_ok=True)

base_config = Path('/content/museum-gallery-ai/configs/eval/tracker_only.json')

for iou_label, iou_value in [('iou_040_baseline', 0.4), ('iou_050_M2', 0.5)]:
    run_name = f"{clip['clip_id']}_{iou_label}"
    output_dir = runs_dir / run_name
    done_file = output_dir / '_done.txt'
    if done_file.exists():
        print('Skipping completed run:', run_name)
        continue
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        'python', '-m', 'museum_gallery_ai', 'process',
        '--config', str(base_config),
        '--source', str(clip['path']),
        '--output', str(output_dir),
        '--detector-iou', str(iou_value),
    ]
    print('Running:', ' '.join(command))
    started = time.perf_counter()
    subprocess.run(command, check=True)
    done_file.write_text(f"completed in {time.perf_counter() - started:.2f}s\n")
    print('Completed:', run_name)

!python scripts/compare_runs.py --runs {runs_dir} --out {runs_dir}/comparison_M2.csv --expected-runs 2

import pandas as pd
df = pd.read_csv(runs_dir / 'comparison_M2.csv')
display(df)
```

What to look at in the comparison:

- `short_lived_count` — lower is better; expected to drop with iou=0.5
  if F1 is correct (less aggressive NMS allows close boxes to coexist).
- `likely_switch_count` — lower is better; expected to drop with iou=0.5
  for the same reason.
- `unique_track_count` — should drop slightly (fewer false new-spawns).
- `duration_median` — should rise slightly (tracks live longer).

Visual check (5 frames around 0:50 in the overlay) is still required
per research 0005 section 8 "Debugging strategy" — diagnostic metrics
alone are not enough; the proximity-merge moment needs eyes-on
verification.

Open items / handoff to Codex (when back):

1. The Colab-vs-pin-range mismatch (Ultralytics 8.4.51 vs `<8.4`).
   Decision needed if Colab downgrade breaks anything.
2. M3 (raise `new_track_thresh` 0.30 → 0.50) is structurally identical
   to M2: that knob is already exposed via the tracker YAML, so no
   code change is needed. M3 is a sibling-YAML or runtime-config-only
   experiment.
3. The `--expected-runs 9` stale literal in the notebook's section 6
   (see prior entry for context) is still in place and unrelated to
   this work.

User decision needed: None for the code change itself (it preserves
default behaviour). The M2 experiment run on Colab is the next user
action.

Status: M1 committed-ready; M2-prep committed-ready; M2 experiment
itself is the user's next Colab step.
