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

## Current Project Direction

Approach 1 is complete as a working offline visitor analytics baseline.

Approach 2 is active:

- improve single-camera track ID stability;
- add diagnostics for track duration, short-lived tracks, gaps, and likely ID
  switches;
- compare ByteTrack and BoT-SORT with numbers before introducing ReID;
- defer multi-camera visitor journeys until single-camera identity stability is
  measurable.

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
