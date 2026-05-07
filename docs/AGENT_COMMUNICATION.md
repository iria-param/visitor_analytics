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

### 2026-05-07 - Colab Batch Evaluation Handoff (Claude → Codex)

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

