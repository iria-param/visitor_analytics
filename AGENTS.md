# AGENTS.md

Guidance for Codex, Claude, and other coding agents working in this repository.

## Project Status

This repository contains the Museum Gallery AI project. Approach 1 is a working
offline Python pipeline for recorded-video visitor analytics. Approach 2 is now
focused on improving track ID stability before anonymous visitor journey
analytics and multi-camera reasoning.

Before making assumptions, inspect the current files and adapt to the actual
structure, frameworks, and conventions.

## Collaboration Style

- Start by understanding the user's goal, the repository state, and any active
  constraints before editing files.
- Prefer making the requested change end to end: inspect, implement, verify,
  and summarize.
- Ask concise clarifying questions only when a safe assumption is not possible.
- Keep changes focused on the user's request. Do not refactor unrelated code.
- Never overwrite or revert user changes unless the user explicitly asks.
- Keep the user in the loop when coordinating between Codex and Claude.

## Agent Roles

Codex is the primary repository operator in this workspace:

- inspect the local codebase and git state;
- implement code and documentation changes;
- run local tests and smoke tests;
- manage branches and commits when requested;
- keep this file and the communication log current.

Claude Opus 4.7 is a coworker for focused thinking tasks:

- research synthesis from authentic sources;
- architecture proposal review;
- test-plan and risk review;
- alternate implementation suggestions;
- code-review style critique before larger changes.

Do not let either agent make hidden decisions. Important decisions, handoffs,
test results, and disagreements should be recorded in
`docs/AGENT_COMMUNICATION.md`.

## New Project And Major Feature Workflow

For any new project, major feature, or architecture direction, follow
`docs/PROJECT_START_WORKFLOW.md`.

Do not jump directly into implementation. Research from authentic sources first,
cite those sources, create a plan, discuss the plan with the user, and only then
start building after the direction is mutually agreed.

## How To Approach Tasks

1. Inspect the repository layout and relevant files.
2. Check `git status --short` before editing.
3. Identify the smallest safe implementation path.
4. Make scoped edits that match existing patterns.
5. Run the most relevant checks available.
6. Update documentation or the communication log when the task changes project
   direction.
7. Report what changed, what was verified, and any remaining risk.

## Commands And Verification

Install dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pip install -e .
```

Run tests:

```powershell
.\.venv\Scripts\python -m pytest
```

Run the offline processor:

```powershell
.\.venv\Scripts\python -m museum_gallery_ai process --config configs/demo.yaml --source path\to\video.mp4 --output runs/demo
```

Run the calibration UI:

```powershell
.\.venv\Scripts\python -m museum_gallery_ai calibrate --source path\to\video.mp4 --output-config configs/calibrated.json
```

## Coding Guidelines

- Follow `CODING_STANDARDS.md` for production-quality engineering expectations.
- Follow the style already present in the codebase.
- Prefer clear, direct code over new abstractions.
- Add abstractions only when they remove real duplication or match existing
  architecture.
- Add comments sparingly, only where they explain non-obvious decisions.
- Keep generated files, lockfiles, and formatting changes scoped to the task.
- Use ASCII by default unless the file already uses Unicode or the task requires
  it.

## Computer Vision Product Boundaries

- Avoid face recognition, demographic guessing, emotion detection, or microphone
  input unless the user explicitly reopens the ethics and privacy decision.
- Store derived events and metrics by default, not raw CCTV video.
- Treat persistent person identity as anonymous tracking only.
- Prefer measurable diagnostics over visual guessing when comparing trackers.

## Git Guidelines

- Check `git status --short` before editing and before finishing.
- Treat uncommitted changes as user work unless clearly created by the current
  task.
- Do not run destructive git commands such as `git reset --hard` or
  `git checkout --` without explicit user approval.
- Use branch names prefixed with `codex/` unless the user asks otherwise.
- Keep commits focused. Do not include temporary A/B configs or generated run
  outputs unless the user asks.

## Good User Prompt Format

Users can get the best results with:

```text
Goal: what should be built, fixed, or changed.
Context: relevant files, errors, screenshots, logs, examples, or links.
Constraints: what to avoid, style rules, architecture rules, or scope limits.
Done when: tests pass, a bug no longer reproduces, or the UI matches a target.
```

## Definition Of Done

A task is done when:

- The requested behavior is implemented.
- Relevant checks were run, or the reason they could not be run is documented.
- The final response names the changed files and verification performed.
- Any assumptions, limitations, or follow-up risks are clearly stated.

