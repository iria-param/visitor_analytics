# CLAUDE.md

Guidance for Codex and other coding agents working in this repository.

## Project Status

This repository is currently a new project workspace. Before making assumptions,
inspect the files that exist at the time of the task and adapt to the project's
actual structure, frameworks, and conventions.

## Collaboration Style

- Start by understanding the user's goal, the current repository state, and any
  constraints before editing files.
- Prefer making the requested change end to end: inspect, implement, verify, and
  summarize.
- Ask concise clarifying questions only when a safe assumption is not possible.
- Keep changes focused on the user's request. Do not refactor unrelated code.
- Never overwrite or revert user changes unless the user explicitly asks.

## How To Approach Tasks

1. Inspect the repository layout and relevant files.
2. Identify the smallest safe implementation path.
3. Make scoped edits that match existing patterns.
4. Run the most relevant checks available.
5. Report what changed, what was verified, and any remaining risk.

## New Project Workflow

For any new project, major feature, or architecture direction, follow
`docs/PROJECT_START_WORKFLOW.md`.

Do not jump directly into implementation. Research from authentic sources first,
cite those sources, create a plan, discuss the plan with the user, and only then
start building after the direction is mutually agreed.

## Commands And Verification

No project-specific commands are defined yet. Once the project has a stack, add
the exact commands here.

Common examples to replace with real commands:

```powershell
# Install dependencies
npm install

# Run tests
npm test

# Run linting
npm run lint

# Start local development server
npm run dev
```

If commands are unknown, inspect package files or project docs first, such as
`package.json`, `pyproject.toml`, `requirements.txt`, `Cargo.toml`, `README.md`,
or framework-specific configuration files.

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

## Frontend Guidelines

If this becomes a frontend project:

- Build the actual usable experience as the first screen, not a marketing page,
  unless a landing page is explicitly requested.
- Match the existing design system and component patterns.
- Make layouts responsive and verify that text does not overflow or overlap.
- Use real assets or appropriate generated bitmap assets when visual quality
  matters.
- Run the app locally and inspect it in a browser after significant UI changes.

## Git Guidelines

- Check `git status --short` before editing and before finishing.
- Treat uncommitted changes as user work unless clearly created by the current
  task.
- Do not run destructive git commands such as `git reset --hard` or
  `git checkout --` without explicit user approval.
- Use branch names prefixed with `codex/` unless the user asks otherwise.

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
