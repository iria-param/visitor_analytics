# Room AI Blueprint

Status: superseded by [Museum Gallery AI Blueprint](MUSEUM_GALLERY_AI_BLUEPRINT.md).

Room AI is a room-aware voice assistant. It listens, speaks, and uses a camera
to understand the visible room context when the user gives permission.

The goal is not to build a movie-style fantasy first. The goal is to build a
small, reliable system that can:

- hear a person clearly
- respond naturally with voice
- look at the room when needed
- explain what it sees
- answer questions about the room
- run simple approved actions
- make its behavior understandable and debuggable

## Product Principle

Room AI should behave like a helpful assistant in a physical space, not like a
chatbot with a camera attached.

It must understand:

- the person speaking
- the current conversation
- the visible room state
- available tools/actions
- privacy and safety boundaries
- uncertainty in what it sees or hears

## MVP Scope

The first version should run as a browser-based app on a laptop or desktop with
camera, microphone, and speaker access.

MVP capabilities:

- start/stop a voice session
- microphone input
- spoken assistant response
- camera snapshot on user request
- "What do you see?" room description
- question answering about visible objects
- simple conversation memory inside one session
- visible debug panel showing audio, vision, and tool events

MVP non-goals:

- always-on surveillance
- face recognition
- identifying private personal information
- controlling real home devices
- long-term memory
- autonomous actions without confirmation
- production smart-home hardware integration

## Recommended First Technical Direction

Start with a web app because it gives the fastest path to camera, microphone,
speaker, and WebRTC testing.

Suggested stack:

- TypeScript
- browser client
- OpenAI Realtime API or Realtime Agents SDK for speech-to-speech interaction
- camera snapshot capture through browser media APIs
- backend token/session endpoint so API secrets stay off the client
- structured event log for debugging

Why this first:

- voice latency matters, and Realtime/WebRTC is designed for low-latency voice
- browser APIs make camera/microphone access easier to prototype
- the user can test quickly without custom hardware
- debugging is easier when events are visible in the UI

## Core User Flows

### 1. Start A Session

1. User opens the app.
2. App asks for microphone permission.
3. App asks for camera permission only when needed or when the user enables it.
4. Backend creates a realtime session.
5. Client connects through WebRTC.
6. Assistant greets the user.

### 2. Voice Conversation

1. User speaks.
2. Voice activity detection detects the turn.
3. Audio is sent to the realtime model.
4. Model responds with audio.
5. UI records the transcript and session events for debugging.

### 3. Room Vision

1. User asks a visual question, such as "What do you see on my desk?"
2. App captures a current camera frame.
3. Frame is sent as image input with the user's question.
4. Model answers with uncertainty when the image is unclear.
5. Debug panel records that an image was captured and why.

### 4. Approved Actions

1. User asks for an action.
2. Assistant decides whether a tool is needed.
3. System checks whether the tool is allowed.
4. User confirms sensitive actions.
5. Tool runs.
6. Result is spoken back and logged.

## Systems-Thinking Architecture

### System Boundary

Inside the MVP boundary:

- browser app
- microphone input
- camera snapshot input
- speaker output
- backend session service
- realtime model connection
- debug/event log

Outside the MVP boundary:

- smart-home devices
- user account system
- long-term memory
- autonomous background monitoring
- multi-room hardware
- production deployment

### Important Flows

- audio from user to model
- audio from model to user
- camera frame from browser to model
- session credentials from backend to browser
- debug events from client/backend to UI
- future tool calls from model to backend

### Feedback Loops

- User trust increases when the assistant explains what it is doing.
- User trust decreases if the camera is used unexpectedly.
- Debugging quality increases when every audio, vision, and tool event is logged.
- Latency worsens when too many images or tools are sent during conversation.
- Product quality improves when failed interactions are reviewed and converted
  into tests or better prompts.

### Delays

- microphone capture and voice activity detection
- network round trip to the model
- model response generation
- audio playback
- camera frame capture and upload
- tool execution

### Leverage Points

- clear privacy controls
- visible session state
- structured logs
- small tool surface
- careful assistant instructions
- explicit confirmation for actions
- tests around session lifecycle and failure states

## Architecture Components

### Client App

Responsibilities:

- request microphone/camera permissions
- start and stop realtime sessions
- display transcript
- capture camera snapshots
- play assistant audio
- show debug events
- expose user controls for privacy

Must be easy to debug:

- show session state
- show whether mic/camera are active
- show last captured image timestamp
- show connection status
- show model/tool events

### Backend Session Service

Responsibilities:

- create realtime sessions or ephemeral client credentials
- keep API keys secret
- enforce allowed models and tools
- apply server-side safety rules
- log server events

The client must never contain long-lived API keys.

### Realtime Assistant

Responsibilities:

- conduct natural voice conversation
- ask for camera input only when useful
- explain uncertainty
- avoid pretending to see things it cannot see
- call approved tools only when needed

### Vision Input

Responsibilities:

- capture a frame only when requested or clearly needed
- avoid continuous video streaming in the MVP
- label image events in the debug log
- allow the user to disable camera use

### Tool Gateway

Responsibilities:

- expose safe actions to the assistant
- validate arguments
- require confirmation for sensitive actions
- record every tool call and result

Early tools can be fake/local before real integrations exist.

Examples:

- get current time
- create local note
- set local reminder
- summarize visible room state

### Memory

MVP memory should be session-only.

Long-term memory should wait until privacy, consent, deletion, and data
retention rules are designed.

## Privacy And Safety Rules

- Camera must have a visible on/off state.
- The assistant should not silently capture images.
- Do not identify people by face.
- Do not infer sensitive traits.
- Do not store images by default.
- Do not log secrets or private personal data.
- Ask confirmation before actions that affect files, accounts, payments,
  messages, devices, or external services.

## Debugging Strategy

Every session should help developers answer:

- Did the browser get microphone permission?
- Did the browser get camera permission?
- Is the realtime connection open?
- Did voice activity detection detect the user turn?
- Was an image captured?
- What did the assistant receive?
- Did the assistant call a tool?
- Did the tool succeed or fail?
- Was the response delayed by network, model, tool, or playback?

The debug panel should show:

- connection state
- mic state
- camera state
- current session ID
- latest transcript turns
- image capture events
- tool call events
- errors with useful context

## Milestones

### Milestone 1: Voice Prototype

- Web app shell
- Start/stop session
- Mic input
- Assistant voice output
- Transcript
- Debug panel

### Milestone 2: Vision Prototype

- Camera permission
- Manual snapshot capture
- "What do you see?" interaction
- Image event logging

### Milestone 3: Room-Aware Assistant

- Assistant asks for a snapshot when visual context is needed
- Room questions work reliably
- Clear uncertainty handling

### Milestone 4: Tool Prototype

- Add safe local tools
- Show tool calls in debug panel
- Require confirmation for sensitive actions

### Milestone 5: Production Hardening

- authentication
- rate limits
- cost controls
- monitoring
- tests
- privacy review
- deployment pipeline

## Key Open Questions

- Should the first prototype be browser-only or desktop app?
- Should the assistant be push-to-talk, wake-word, or manual start?
- Should camera snapshots be manual only, automatic on visual questions, or both?
- What actions should the assistant eventually perform?
- Should the system support one room, many rooms, or mobile movement?
- What level of memory is acceptable?
- What privacy promise do we want to make to users?

## References

- OpenAI Realtime API: https://platform.openai.com/docs/guides/realtime
- OpenAI Voice Agents: https://platform.openai.com/docs/guides/voice-agents
- OpenAI Realtime WebRTC: https://platform.openai.com/docs/guides/realtime-webrtc
- OpenAI Vision: https://platform.openai.com/docs/guides/vision
- Project coding standards: ../CODING_STANDARDS.md
