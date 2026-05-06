# Coding Standards

This document defines how we write production-quality code in this repository.
The goal is not only to ship working software, but to make sure developers
understand how the system works, can debug it calmly, and can maintain it over
time.

## Core Principle

Code is not done when it runs once. Code is done when another developer can read
it, understand the flow, verify it, debug it, and safely change it later.

Every meaningful change should improve or preserve:

- correctness
- readability
- simplicity
- testability
- observability
- security
- maintainability

## Development Mindset

- Understand the problem before writing code.
- For new projects and major features, research authentic sources before
  planning or implementation.
- Read the surrounding code before changing it.
- Prefer the smallest complete solution that fits the existing design.
- Avoid "zombie coding": do not paste, generate, or accept code that you cannot
  explain.
- Make hidden behavior visible through names, structure, tests, logs, and docs.
- Treat debugging as a skill to practice, not as a last-minute panic activity.

## Code Organization

- Keep modules focused on one responsibility.
- Keep functions small enough to understand without scrolling through unrelated
  behavior.
- Separate business logic from framework glue, transport code, UI code, and
  persistence code where practical.
- Avoid circular dependencies.
- Prefer explicit data flow over global mutable state.
- Do not add abstractions for imagined future requirements. Add them when they
  remove real complexity or match an existing pattern.

## Architecture: Systems Thinking

Architecture decisions should use a systems-thinking approach inspired by
Donella Meadows. Do not design only the visible components. Understand the
system behavior created by relationships, feedback loops, incentives, delays,
constraints, and failure modes.

Before making a major architecture decision, answer:

- What is the system boundary?
- What users, services, teams, data stores, queues, jobs, and external providers
  are inside or outside that boundary?
- What are the important flows of data, control, money, time, trust, and user
  attention?
- What feedback loops exist?
- What delays exist between cause and effect?
- What incentives does this design create for users, developers, operators, and
  the business?
- What bottlenecks or constraints control the system's behavior?
- What happens when traffic, data volume, team size, or product complexity grows?
- What failure modes can cascade into other parts of the system?
- What small leverage point could improve the whole system?

Architecture standards:

- Prefer simple designs with clear data flow and clear ownership.
- Make system boundaries explicit.
- Design for debuggability before cleverness.
- Avoid hidden coupling between modules, services, teams, or deployment steps.
- Prefer observable workflows over invisible background behavior.
- Treat queues, caches, retries, cron jobs, and async workers as first-class
  architecture, not implementation details.
- Consider second-order effects before optimizing one part of the system.
- Avoid local optimizations that make the whole system harder to understand,
  operate, or change.
- Document important tradeoffs and the reason a design was chosen.

For significant architecture decisions, create a short Architecture Decision
Record with:

- context
- decision
- alternatives considered
- expected benefits
- tradeoffs and risks
- feedback loops affected
- operational/debugging impact
- signals that would tell us the decision is wrong

## Naming

- Use names that explain intent, not implementation trivia.
- Prefer `calculateInvoiceTotal` over `processData`.
- Prefer `isPaymentExpired` over `flag`.
- Avoid unclear abbreviations.
- A reader should usually know what a variable, function, or module is for
  without opening five other files.

## Comments And Documentation

- Code should explain what is happening.
- Comments should explain why something is happening.
- Add comments for unusual constraints, tradeoffs, algorithms, protocol details,
  performance assumptions, or business rules.
- Do not write comments that simply repeat the code.
- Update documentation when behavior, setup, commands, APIs, environment
  variables, or debugging steps change.

For non-trivial features, document:

- the main flow
- important files/modules
- external services involved
- known failure modes
- how to test it
- how to debug it

## Error Handling

- Handle expected failure paths deliberately.
- Do not swallow errors silently.
- Return or throw errors with enough context to diagnose the problem.
- Do not expose secrets, tokens, stack traces, or internal infrastructure details
  to end users.
- Fail securely when authorization, validation, configuration, or dependency
  checks cannot be completed.

## Logging And Observability

Production code should help us answer:

- What happened?
- Where did it happen?
- Who or what was affected?
- What request, job, user, tenant, or entity was involved?
- What changed recently?

Standards:

- Log important state transitions and failures.
- Include correlation/request IDs where available.
- Use structured logs when the stack supports them.
- Do not log secrets or sensitive personal data.
- Make logs useful for debugging, not noisy.
- Add metrics/traces for important production paths when applicable.

## Debugging Standard

When debugging, follow a methodical loop:

1. State the expected behavior.
2. State the actual behavior.
3. Reproduce the issue if possible.
4. Identify the smallest failing path.
5. Form one hypothesis at a time.
6. Test the hypothesis with evidence.
7. Record what was tried and what was learned.
8. Fix the root cause, not only the symptom.
9. Add a regression test or monitoring when possible.

Useful debugging questions:

- What changed most recently?
- Does the failure happen for all users or only some?
- Is the problem in input, processing, storage, output, or integration?
- Can I reduce this to a smaller case?
- What evidence would prove this theory wrong?

## Testing

- New behavior should usually include tests.
- Bug fixes should include a regression test when practical.
- Tests should be simple, meaningful, and maintainable.
- A test should fail for the right reason when the behavior is broken.
- Avoid tests that only assert implementation details.
- Prefer fast tests near the logic, and add integration/end-to-end tests for
  important cross-system behavior.

Minimum expectations:

- happy path
- important edge cases
- failure paths
- authorization/validation behavior where relevant

## Security

- Validate untrusted input on the trusted side of the system.
- Prefer allow-lists over deny-lists for validation.
- Use parameterized queries or safe ORM APIs for database access.
- Keep secrets out of code, logs, commits, client bundles, and screenshots.
- Store deploy-specific configuration in environment/config systems, not hard
  coded constants.
- Use least privilege for users, services, database credentials, and tokens.
- Do not invent cryptography. Use well-tested libraries and platform services.

## Configuration

- Separate code from environment-specific configuration.
- Local, staging, and production should differ by configuration, not by code
  edits.
- Document required environment variables and safe example values.
- Never commit real credentials.

## Code Review Standard

Reviews should protect long-term code health while keeping work moving.

Review for:

- design fit
- correctness
- simplicity
- readability
- tests
- naming
- useful comments
- security
- observability
- documentation

Authors should make changes small enough to review properly. Reviewers should
explain the reason behind important comments so the author learns the principle,
not just the requested edit.

## Pull Request / Change Checklist

Before considering a change complete, answer:

- Can I explain the code path in plain language?
- Did I remove unnecessary complexity?
- Did I test the behavior that matters?
- Did I consider failure paths?
- Did I avoid leaking sensitive data?
- Did I add or preserve useful logs/errors?
- Did I update docs or setup notes if behavior changed?
- Would another developer be able to debug this without guessing?

## AI-Assisted Coding Rules

AI can help write, explain, review, and debug code, but the developer remains
responsible for understanding and validating the result.

- Do not accept AI-generated code that you cannot explain.
- Ask AI to explain the flow, edge cases, and failure modes.
- Ask AI to identify simpler alternatives before adding abstractions.
- Ask AI to write or improve tests, not only implementation code.
- Verify generated code with tests, type checks, linting, or manual inspection.
- If AI changes code, review the diff like any other human-written change.

Useful prompts:

```text
Explain this module as if I need to debug it tomorrow.
```

```text
Before editing, trace the current code path and identify the failure points.
```

```text
Review this change for correctness, simplicity, tests, security, and debugging clarity.
```

```text
Add tests that would fail if this bug comes back.
```

## Definition Of Done

A task is done when:

- the requested behavior works
- the implementation is understandable
- relevant tests/checks pass, or skipped checks are explained
- failure paths are handled
- logs/errors help future debugging
- security-sensitive paths were considered
- documentation is updated when needed

## References

This standard is inspired by:

- Google Engineering Practices: https://google.github.io/eng-practices/
- Google Code Review Guide: https://google.github.io/eng-practices/review/
- Google SRE Effective Troubleshooting: https://sre.google/sre-book/effective-troubleshooting/
- Google SRE Monitoring Distributed Systems: https://sre.google/sre-book/monitoring-distributed-systems/
- OWASP Secure Coding Practices: https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/
- The Twelve-Factor App, Config: https://12factor.net/config
- Martin Fowler, Refactoring: https://martinfowler.com/books/refactoring.html
- Donella Meadows, Thinking in Systems: https://donellameadows.org/systems-thinking-resources/
