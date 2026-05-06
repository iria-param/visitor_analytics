# Project Start Workflow

Every new project, major feature, or architecture direction must begin with
research before implementation.

The purpose is to avoid shallow building, trend-chasing, and "zombie coding."
We first understand the domain, the authentic technical sources, the risks, and
the system behavior. Then we plan. Then we discuss. Only after mutual agreement
do we build.

## Required Workflow

### 1. Research First

Before planning or coding, collect information from authentic sources.

Preferred source types:

- official product/API documentation
- standards bodies
- academic papers or books from recognized experts
- vendor architecture guides
- security guidance from trusted organizations
- framework/runtime documentation
- source repositories from the maintainers
- production postmortems or engineering blogs from credible teams

Avoid using weak sources as primary evidence:

- random blog posts with no sources
- SEO articles
- copied tutorials
- outdated examples
- social media opinions
- AI-generated summaries without citations

Research output must include:

- key findings
- direct links to sources
- what each source is being used for
- assumptions
- open questions
- risks and unknowns
- outdated or conflicting guidance, if found

### 2. Understand The System

Use systems thinking before proposing architecture.

Answer:

- What problem are we solving?
- Who are the users?
- What is inside and outside the system boundary?
- What data, trust, money, time, and control flows through the system?
- What feedback loops will the product create?
- What delays or bottlenecks matter?
- What failure modes could cascade?
- What incentives does the design create?
- What small leverage points could improve the whole system?

### 3. Plan Next

After research, create a plan.

The plan should include:

- product goal
- MVP scope
- non-goals
- architecture options
- recommended approach
- tradeoffs
- risks
- privacy/security implications
- debugging strategy
- testing strategy
- milestone sequence
- definition of done

The plan must distinguish:

- what we know
- what we assume
- what needs validation
- what we are deliberately postponing

### 4. Discuss Before Building

Do not start implementation immediately after planning.

First discuss with the user:

- Is this actually the product they want?
- Is the MVP scope correct?
- Are the tradeoffs acceptable?
- Are privacy and safety boundaries acceptable?
- Are there missing constraints?
- Should the architecture be simpler or more ambitious?
- What should be built first?

Implementation starts only after the user confirms the direction or asks to
proceed.

### 5. Build In Small Verified Steps

Once aligned:

- build the smallest useful slice first
- keep the system debuggable
- add tests or checks as soon as behavior becomes important
- document decisions as they are made
- keep architecture decision records for major decisions
- review each milestone against the original research and plan

## Project Start Checklist

Before coding, confirm:

- Research sources are cited.
- The problem is clearly stated.
- MVP and non-goals are written.
- System boundaries are clear.
- Architecture tradeoffs are visible.
- Debugging and observability are planned.
- Security and privacy risks are considered.
- The user has reviewed the plan.
- The user has approved the first build step.

## Standard Prompt For Future Projects

```text
Before building, research authentic sources first. Cite them.
Then create a plan with systems thinking, architecture options, risks,
debugging strategy, and MVP scope.
Do not implement until we discuss and agree on the direction.
```
