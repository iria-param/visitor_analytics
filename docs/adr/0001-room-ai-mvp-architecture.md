# ADR 0001: Room AI MVP Architecture

## Status

Superseded by [ADR 0002](0002-select-modern-cv-pipeline.md).

## Context

We want to build Room AI: a room-aware voice assistant that can listen, speak,
and use camera input to understand the visible room when the user allows it.

This type of product has several hard constraints:

- voice latency must be low
- camera use must be explicit and trustworthy
- API keys must not be exposed in the browser
- behavior must be debuggable by developers
- the first version should teach us quickly without requiring custom hardware

## Decision

The MVP will be a browser-based application with a small backend session
service.

The browser client will handle:

- microphone access
- speaker playback
- camera permission and snapshot capture
- realtime connection
- transcript display
- debug panel

The backend will handle:

- realtime session creation
- API key protection
- allowed model/tool configuration
- future tool execution
- server-side logging and guardrails

The MVP will use manual or request-based camera snapshots, not continuous
background video analysis.

## Alternatives Considered

### Desktop App First

Could provide deeper OS integration, but slows early learning and adds packaging
complexity.

### Hardware Device First

Matches the final room-assistant vision, but creates hardware, audio, camera,
network, update, and deployment problems before the core interaction is proven.

### Text Chat First

Simpler, but it avoids the main product risk: natural room-based voice
interaction.

### Continuous Video First

More powerful, but privacy, cost, latency, and trust risks are too high for the
MVP.

## Expected Benefits

- fast prototype loop
- easy access to microphone and camera APIs
- direct testing by the user
- lower voice latency through realtime transport
- safer privacy posture through snapshot-based vision
- easier debugging through visible session events

## Tradeoffs And Risks

- browser permissions can be confusing for users
- WebRTC debugging can be difficult
- browser app cannot fully control the room or operating system
- snapshot-based vision may miss changes between frames
- model/API cost needs monitoring

## Feedback Loops Affected

- Clear camera controls increase user trust.
- Debug visibility increases developer learning speed.
- Low latency increases natural conversation quality.
- Excessive hidden automation decreases trust.
- Good logs convert confusing failures into future tests.

## Operational And Debugging Impact

The MVP must expose connection, audio, vision, and tool events in a debug panel.
This is not optional because the product combines several failure-prone systems:
browser permissions, audio capture, realtime networking, model behavior, image
input, and future tools.

## Signals This Decision Is Wrong

- Browser audio/camera reliability blocks normal testing.
- Latency is unacceptable even with realtime transport.
- Users need OS-level or device-level integrations immediately.
- The debug panel cannot explain common failures.
- Snapshot-based vision is too limited for the core use case.

## References

- Room AI blueprint: ../ROOM_AI_BLUEPRINT.md
- Coding standards: ../../CODING_STANDARDS.md
