# CLAUDE.md

Instructions for Claude Opus 4.7 when working as a coworker on this repository.

The shared repository rules live in `AGENTS.md`. Follow that file first. This
file adds Claude-specific responsibilities so Claude and Codex can collaborate
without stepping on each other.

## Standing Rule: Dual-Role Fallback

When Codex is unavailable (rate-limited, offline, or otherwise blocked) and the
user confirms the situation, Claude takes on BOTH roles until Codex is back:

- Claude continues to research, plan, review, and write handoffs.
- Claude additionally inspects files, edits code, runs tests, and proposes
  exact commits the user can execute.
- Git operations still go through the user's PowerShell terminal (the sandbox
  cannot write to `.git/` on a Windows mount). Claude hands exact commands.
- Branch in flight is honoured. No branch switches, no destructive git
  commands, no merges to `main` without explicit user approval.
- Privacy boundary unchanged: no ReID, no face/demographic/emotion inference,
  no raw video storage, no person crops.
- Every Codex-side action Claude takes during this period is logged in
  `docs/AGENT_COMMUNICATION.md` so Codex can see it on return.
- Claude reverts to review-only mode the moment Codex is back online.

This rule applies automatically whenever the user signals Codex is out.

## Role

Claude Opus 4.7 is the project's deep-thinking coworker. Use Claude for tasks
where careful reasoning is more valuable than direct local execution:

- research synthesis from official or authentic sources;
- architecture and systems-thinking proposals;
- privacy, safety, and product-risk review;
- code-review style critique;
- test strategy and acceptance criteria;
- comparison of implementation options;
- handoff notes for Codex before implementation.

Codex remains the primary local repository operator unless the user explicitly
asks otherwise. Codex should usually perform file edits, run tests, manage git,
and verify outputs in this workspace.

## What Claude Should Produce

When asked to help, Claude should return one of these concrete artifacts:

- a short research brief with citations;
- an implementation proposal with risks and acceptance criteria;
- a code review with prioritized findings;
- a focused test plan;
- a handoff note that Codex can execute locally.

Avoid vague advice. Make the next action obvious.

## Handoff Format

Use this structure when handing work to Codex:

```text
Goal:
Files likely involved:
Proposed change:
Verification commands:
Risks or open questions:
What not to change:
```

If the task touches identity tracking, privacy, or CCTV analytics, also include:

```text
Privacy boundary:
Metrics needed:
Failure modes:
```

## Communication Rule

Important Claude conclusions must be copied or summarized into
`docs/AGENT_COMMUNICATION.md` so the user can see what was decided. Do not treat
private chat between agents as a source of truth.

## Project Map And Routing

The user does not want to point at specific files for every task. Use this map
to find the right place automatically. The tiers below are deliberately
ordered: non-negotiable beats active beats reference beats superseded.

### Importance tiers

Non-negotiable (privacy policy, agent rules, production code, active product
direction). Never silently rewrite, never reorder without an ADR or explicit
user approval:

- [AGENTS.md](AGENTS.md) — shared rules for Codex and Claude.
- [CLAUDE.md](CLAUDE.md) — this file.
- [CODING_STANDARDS.md](CODING_STANDARDS.md) — engineering and AI-assisted
  coding rules.
- [docs/PROJECT_START_WORKFLOW.md](docs/PROJECT_START_WORKFLOW.md) — research
  first, plan, discuss, build.
- [docs/MUSEUM_GALLERY_AI_BLUEPRINT.md](docs/MUSEUM_GALLERY_AI_BLUEPRINT.md) —
  active product blueprint and privacy boundary.
- [docs/AGENT_COMMUNICATION.md](docs/AGENT_COMMUNICATION.md) — visible
  decisions and handoff log. Source of truth for cross-agent state.
- [src/museum_gallery_ai/](src/museum_gallery_ai/) — production package.
- [configs/trackers/](configs/trackers/), [configs/calibrated.json](configs/calibrated.json),
  [configs/eval/tracker_only.json](configs/eval/tracker_only.json) — committed
  configs must reflect policy (e.g. `with_reid: False`).
- [tests/](tests/) — must keep passing.

Active project context (current open work — read when the prompt is about
trackers, IDs, NMS, ReID, or Approach 2 steps):

- [docs/approaches/approach_2_identity_stability_and_journey_tracking.md](docs/approaches/approach_2_identity_stability_and_journey_tracking.md)
- [docs/research/0005-tracker-flicker-and-nms-merging.md](docs/research/0005-tracker-flicker-and-nms-merging.md)
  — most recent research; defines F1-F9, A1-A4, Q1-Q4, R1-R5, options A-D,
  milestones M1-M7.
- [notebooks/colab_tracker_comparison.ipynb](notebooks/colab_tracker_comparison.ipynb)
  — Colab batch-comparison notebook. Cell outputs are committed so agents
  read run summaries directly. Two-way sync: VS Code edits → `git push` →
  Colab `!git pull`; Colab "File → Save a copy in GitHub" → VS Code
  `git pull`.

Reference (older but still cited; load only when a topic above points here):

- [docs/research/0002-museum-cctv-visitor-analytics-existing-systems.md](docs/research/0002-museum-cctv-visitor-analytics-existing-systems.md)
- [docs/research/0003-open-source-video-analytics-frameworks.md](docs/research/0003-open-source-video-analytics-frameworks.md)
- [docs/research/0004-approach-2-tracking-reid-frameworks.md](docs/research/0004-approach-2-tracking-reid-frameworks.md)
- [docs/planning/0001-option-2-modern-cv-pipeline-plan.md](docs/planning/0001-option-2-modern-cv-pipeline-plan.md)
- [docs/architecture/spatial-camera-mapping.md](docs/architecture/spatial-camera-mapping.md)
- [docs/adr/0002-select-modern-cv-pipeline.md](docs/adr/0002-select-modern-cv-pipeline.md) (Accepted)
- [docs/approaches/approach_1_current_baseline.md](docs/approaches/approach_1_current_baseline.md)

Superseded (do not treat as current direction):

- [docs/ROOM_AI_BLUEPRINT.md](docs/ROOM_AI_BLUEPRINT.md) — replaced by Museum
  Gallery AI Blueprint.
- [docs/adr/0001-room-ai-mvp-architecture.md](docs/adr/0001-room-ai-mvp-architecture.md) — superseded by 0002.
- [docs/research/0001-room-ai-foundation-research.md](docs/research/0001-room-ai-foundation-research.md) — Room AI era.

Generated, never committed:

- `runs/` — overlay/events/metrics outputs. Read for evidence, never stage.

### Routing table

When the prompt matches a topic, open the "Read first" file(s) before
answering, then dive into the code/configs in "Then likely touch".

| Topic in prompt | Read first | Then likely touch |
|-----------------|-----------|-------------------|
| Tracker tuning, ID flicker, sub-second churn, NMS, proximity merge, ReID, appearance_thresh | [docs/research/0005-tracker-flicker-and-nms-merging.md](docs/research/0005-tracker-flicker-and-nms-merging.md), latest entries in [docs/AGENT_COMMUNICATION.md](docs/AGENT_COMMUNICATION.md) | [src/museum_gallery_ai/detector.py](src/museum_gallery_ai/detector.py), [configs/trackers/botsort_museum.yaml](configs/trackers/botsort_museum.yaml), [configs/eval/tracker_only.json](configs/eval/tracker_only.json) |
| Track diagnostics, ID-switch count, short-lived tracks, gap stats | [docs/approaches/approach_2_identity_stability_and_journey_tracking.md](docs/approaches/approach_2_identity_stability_and_journey_tracking.md) (Step 2) | [src/museum_gallery_ai/track_diagnostics.py](src/museum_gallery_ai/track_diagnostics.py), [tests/test_track_diagnostics.py](tests/test_track_diagnostics.py), [scripts/compare_runs.py](scripts/compare_runs.py) |
| Add/compare tracker configs, museum-tuned YAMLs | [docs/research/0004-approach-2-tracking-reid-frameworks.md](docs/research/0004-approach-2-tracking-reid-frameworks.md) | [configs/trackers/](configs/trackers/), `configs/calibrated_*_museum*.json`, [tests/test_tracker_configs.py](tests/test_tracker_configs.py) |
| Zones, exhibit polygons, entry/exit lines, calibration UI | [docs/architecture/spatial-camera-mapping.md](docs/architecture/spatial-camera-mapping.md) | [src/museum_gallery_ai/zone_engine.py](src/museum_gallery_ai/zone_engine.py), [src/museum_gallery_ai/calibration_app.py](src/museum_gallery_ai/calibration_app.py), [src/museum_gallery_ai/geometry.py](src/museum_gallery_ai/geometry.py), [configs/calibrated.json](configs/calibrated.json) |
| Metrics (dwell, occupancy, pass-by, entry/exit, heatmaps) | [docs/MUSEUM_GALLERY_AI_BLUEPRINT.md](docs/MUSEUM_GALLERY_AI_BLUEPRINT.md) "Metrics" | [src/museum_gallery_ai/metrics.py](src/museum_gallery_ai/metrics.py), [tests/test_zone_engine.py](tests/test_zone_engine.py) |
| Detector / YOLO / NMS `iou=` / image size | [docs/research/0005-tracker-flicker-and-nms-merging.md](docs/research/0005-tracker-flicker-and-nms-merging.md) F1 | [src/museum_gallery_ai/detector.py](src/museum_gallery_ai/detector.py), [configs/eval/tracker_only.json](configs/eval/tracker_only.json) |
| Overlay video, debug drawing, Kalman preview | [docs/research/0005-tracker-flicker-and-nms-merging.md](docs/research/0005-tracker-flicker-and-nms-merging.md) Option B | [src/museum_gallery_ai/overlay.py](src/museum_gallery_ai/overlay.py) |
| CLI flags, fast-eval, `--max-frames`, `--frame-stride`, `--image-size`, `--no-overlay` | [README.md](README.md) "Fast-evaluation flags" | [src/museum_gallery_ai/cli.py](src/museum_gallery_ai/cli.py), [src/museum_gallery_ai/processor.py](src/museum_gallery_ai/processor.py), [tests/test_cli.py](tests/test_cli.py) |
| Run-to-run comparison, CSV summaries | [scripts/compare_runs.py](scripts/compare_runs.py) | [tests/test_compare_runs.py](tests/test_compare_runs.py) |
| Privacy, ReID gating, consent, retention | [docs/MUSEUM_GALLERY_AI_BLUEPRINT.md](docs/MUSEUM_GALLERY_AI_BLUEPRINT.md) "Privacy Boundaries"; [docs/AGENT_COMMUNICATION.md](docs/AGENT_COMMUNICATION.md) entry "2026-05-14 One-Off Offline ReID Experiment Authorised" | none without ADR |
| Multi-camera, cross-camera journey, transitions | [docs/architecture/spatial-camera-mapping.md](docs/architecture/spatial-camera-mapping.md); Approach 2 Steps 4-5 | architecture only; not implemented |
| Codex handoff, decision log entry | "Handoff Format" above | append to [docs/AGENT_COMMUNICATION.md](docs/AGENT_COMMUNICATION.md) |
| Tests fail / pytest behaviour | [tests/](tests/) directly | nearest `src/museum_gallery_ai/*.py` |
| Setup, venv, install, smoke-test commands | [README.md](README.md), [AGENTS.md](AGENTS.md) "Commands And Verification" | none |
| Smoke run across four trackers in one shot | [scripts/run_4tracker_smoke.ps1](scripts/run_4tracker_smoke.ps1) | none |
| Colab notebook, batch comparison, T4 GPU runs, `runtime_configs/`, `--expected-runs`, ReID experiment | [notebooks/colab_tracker_comparison.ipynb](notebooks/colab_tracker_comparison.ipynb) | [scripts/compare_runs.py](scripts/compare_runs.py), [configs/eval/tracker_only.json](configs/eval/tracker_only.json) (base config the notebook copies from) |

### Where new files go

- New research → `docs/research/000N-kebab-case-title.md`. Increment N. Cite
  authentic sources per [docs/PROJECT_START_WORKFLOW.md](docs/PROJECT_START_WORKFLOW.md).
- New ADR → `docs/adr/000N-kebab-case-title.md`. Status starts as Proposed.
- New plan → `docs/planning/000N-kebab-case-title.md`.
- New approach milestone → update the matching
  `docs/approaches/approach_N_*.md`; do not create a new file unless the
  user opens a new approach.
- New tracker variant → sibling YAML in `configs/trackers/`; matching
  `configs/calibrated_*_<variant>.json`; add a row in
  [tests/test_tracker_configs.py](tests/test_tracker_configs.py) if the
  schema changes.
- Experiment-only A/B configs → committed only if the user asks; otherwise
  treat as runtime files. `runs/` outputs are never committed.
- Cross-agent decisions → append to [docs/AGENT_COMMUNICATION.md](docs/AGENT_COMMUNICATION.md)
  using the handoff template; never store in memory only.

## Active State

Approach 1 (offline baseline) is complete.

Approach 2 (single-camera ID stability) is active on branch
`codex/approach-2-id-stability`. Step 1 (museum-tuned tracker YAMLs) and
Step 2 (track diagnostics in `metrics_summary.json`) are implemented.

Latest research: [docs/research/0005-tracker-flicker-and-nms-merging.md](docs/research/0005-tracker-flicker-and-nms-merging.md)
identifies F1 (NMS `iou=0.4` too aggressive), F4 (`appearance_thresh: 0.8`
silently rejects ReID), F6 (`new_track_thresh: 0.30` too permissive), and
F7 (matching is permissive, not strict). Recommended next experiments are
M1 (pin Ultralytics), M2 (raise NMS `iou` 0.4 → 0.5), M3 (raise
`new_track_thresh` 0.30 → 0.50), each as a one-knob change with overlay-on
runs on `gallery_day1`.

Per [docs/AGENT_COMMUNICATION.md](docs/AGENT_COMMUNICATION.md) entry
"2026-05-18 Correction: Overlay Generation Already Works", the project is
awaiting Codex's proposal on whether to start with M1+M2 or a
counter-proposal. Claude stays in review-only mode unless the Standing Rule
dual-role fallback is activated.

Defer until single-camera identity is measurably stable:

- multi-camera journey reconstruction;
- floor-plan homography / shared coordinate system;
- dashboard work;
- any flip of `with_reid: True` in committed configs (gated by ADR).

## Constraints

- Do not introduce face recognition.
- Do not introduce demographic, emotion, or biometric classification.
- Do not store raw video by default.
- Do not enable ReID without an explicit privacy/architecture decision.
- Do not recommend large rewrites while a focused measurable step is available.
- Do not ask Codex to commit generated run outputs or temporary A/B configs.

## Useful Commands

Run tests:

```powershell
.\.venv\Scripts\python -m pytest
```

Run the current calibrated video processor:

```powershell
.\.venv\Scripts\python -m museum_gallery_ai process --config configs/calibrated.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs/calibrated_sample
```

Run tracker comparison configs:

```powershell
.\.venv\Scripts\python -m museum_gallery_ai process --config configs/calibrated_bytetrack_museum.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs/step1_bytetrack_museum
.\.venv\Scripts\python -m museum_gallery_ai process --config configs/calibrated_botsort_museum.json --source "C:\Users\Admin\Downloads\Recording 2026-05-05 193149.mp4" --output runs/step1_botsort_museum
```
