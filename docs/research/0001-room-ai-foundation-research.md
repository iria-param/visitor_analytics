# Room AI Foundation Research

Date: 2026-05-05

Status: research brief, not an implementation plan.

## Research Rule

This document uses authentic sources only:

- official product/API documentation
- standards/reference documentation
- recognized security and privacy organizations
- recognized systems-thinking source material

No coding should start from this document alone. The next step is to turn these
findings into a plan, discuss that plan, and build only after agreement.

## Product Being Researched

Room AI is a room-aware voice assistant. It should hear the user, speak back,
and use camera input to understand the visible room when the user explicitly
allows it.

The product is closer to an ambient assistant than a normal chatbot, so the
research must cover:

- realtime voice interaction
- browser microphone and camera access
- vision input
- privacy and consent
- AI/LLM security
- observability and debugging
- systems-thinking architecture

## Source Summary

### OpenAI Realtime API

Source: https://developers.openai.com/api/docs/guides/realtime

Used for: understanding the official OpenAI path for low-latency multimodal
interactions.

Key findings:

- The Realtime API is designed for low-latency multimodal applications.
- It supports speech-to-speech interaction and multimodal inputs such as audio,
  image, and text.
- OpenAI describes three main connection styles: WebRTC, WebSocket, and SIP.
- For browser voice agents, OpenAI points developers toward Realtime voice
  agents and WebRTC-style connections.

Implication for Room AI:

- The MVP should use realtime voice rather than a slow chain of speech-to-text,
  text response, and text-to-speech unless we deliberately choose more control
  over latency.

### OpenAI Voice Agents

Source: https://developers.openai.com/api/docs/guides/voice-agents

Used for: choosing the voice-agent architecture and early interaction design.

Key findings:

- OpenAI distinguishes speech-to-speech realtime architecture from chained
  speech-to-text -> text model -> text-to-speech architecture.
- Realtime speech-to-speech is best for low-latency, fluid conversation.
- Chained architecture gives more control and transparency because transcripts
  and intermediate text are easier to inspect.
- OpenAI recommends starting small, keeping the agent focused, limiting tools,
  and using clear prompts.

Implication for Room AI:

- The first MVP should probably use realtime voice for the core interaction,
  but the debug panel should expose transcripts/events so developers can still
  understand what happened.
- Tool access should be small and explicit in early versions.

### OpenAI Realtime WebRTC

Source: https://developers.openai.com/api/docs/guides/realtime-webrtc

Used for: browser transport choice.

Key findings:

- OpenAI recommends WebRTC for client-side/browser realtime applications.
- WebRTC is presented as more suitable for browser/mobile low-latency voice
  interactions.
- Browser connections should not expose long-lived API keys; a backend should
  create sessions or issue ephemeral credentials.

Implication for Room AI:

- The system should have a backend session service even for the MVP.
- The frontend should never contain a long-lived OpenAI API key.

### OpenAI Images And Vision

Source: https://developers.openai.com/api/docs/guides/images-vision

Used for: understanding image input and room understanding.

Key findings:

- OpenAI vision-capable models can analyze image inputs.
- Images can be used as input to models for understanding visual content.
- Image understanding is not the same as continuous video understanding.

Implication for Room AI:

- The first version should use camera snapshots instead of continuous video.
- Room vision should be framed as "current camera frame analysis," not magical
  persistent awareness.

### MDN: getUserMedia

Source: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia

Used for: browser camera/microphone behavior.

Key findings:

- `getUserMedia()` prompts the user for permission before providing microphone
  or camera streams.
- It requires a secure context in supporting browsers.
- It can fail when permission is denied, devices are missing, or constraints
  cannot be satisfied.
- The user may ignore the permission prompt, so the promise may not resolve or
  reject immediately.

Implication for Room AI:

- Permission states and errors must be first-class UI/debug states.
- The app must handle "permission prompt ignored" without hanging silently.
- Local development and deployment must account for secure-context behavior.

### W3C Media Capture And Streams

Source: https://w3c.github.io/mediacapture-main/

Used for: standards-level understanding of browser media capture.

Key findings:

- The standard defines APIs for requesting access to local multimedia devices
  such as microphones and cameras.
- Media streams have tracks, sources, constraints, capabilities, and settings.
- Constraints affect device selection and media behavior.

Implication for Room AI:

- Camera and microphone settings should be explicit, inspectable, and logged.
- Device constraints should be kept simple in the first version.

### OWASP Top 10 Web Application Security

Source: https://owasp.org/Top10/2021/

Used for: baseline web application security risks.

Key findings:

- OWASP lists broken access control, cryptographic failures, injection,
  insecure design, misconfiguration, vulnerable components, authentication
  failures, data integrity failures, logging/monitoring failures, and SSRF as
  major web application risks.

Implication for Room AI:

- Even the MVP needs secure-by-default design for auth, secrets, API endpoints,
  logging, dependency management, and deployment configuration.

### OWASP API Security Top 10

Source: https://owasp.org/API-Security/editions/2023/en/0x11-t10/

Used for: backend/session-service and future tool API risks.

Key findings:

- API risks include broken object/function authorization, broken authentication,
  unrestricted resource consumption, security misconfiguration, improper
  inventory management, and unsafe consumption of third-party APIs.

Implication for Room AI:

- The backend should protect session creation, rate limits, model usage, tool
  calls, and object access.
- Cost control is a security and reliability requirement, not just a billing
  concern.

### OWASP Top 10 For LLM Applications / GenAI Security

Source: https://owasp.org/www-project-top-10-for-large-language-model-applications

Used for: LLM-specific security risks.

Key findings:

- Important LLM risks include prompt injection, insecure output handling,
  sensitive information disclosure, excessive agency, overreliance, and model
  denial of service.

Implication for Room AI:

- The assistant must not be allowed to take broad actions directly.
- Tool calls need validation, authorization, confirmation, and logging.
- The user interface must communicate uncertainty instead of encouraging blind
  trust in the assistant.

### NIST AI Risk Management Framework

Source: https://www.nist.gov/itl/ai-risk-management-framework

Used for: trustworthy AI risk framing.

Key findings:

- NIST AI RMF is intended to help manage AI risks to individuals,
  organizations, and society.
- It uses functions such as govern, map, measure, and manage.
- Trustworthy AI characteristics include reliability, safety, security,
  resilience, accountability, transparency, explainability, privacy enhancement,
  and fairness.

Implication for Room AI:

- We should explicitly map, measure, and manage AI risks before production.
- For the MVP, we should start with transparency, privacy, controllability, and
  explainability through visible state and debug logs.

### NIST Privacy Framework

Source: https://www.nist.gov/privacy-framework

Used for: privacy risk framing.

Key findings:

- NIST frames privacy as enterprise risk management focused on improving
  individuals' privacy.

Implication for Room AI:

- Camera, microphone, room context, and conversation history are privacy-heavy.
- Data minimization, retention, deletion, and consent need to be designed early,
  not added later.

### FTC Voice Assistant Privacy Guidance

Source: https://consumer.ftc.gov/node/77539

Used for: consumer-facing voice assistant privacy expectations.

Key findings:

- Voice assistants can access sensitive information depending on permissions and
  connected accounts.
- Users should know how the assistant works, when it is listening, what accounts
  are connected, and how to delete old recordings.

Implication for Room AI:

- Room AI must visibly show listening/camera state.
- The MVP should avoid long-term recordings by default.
- Any future connected accounts or device integrations need clear user control.

### FTC IoT Security Guidance

Source: https://www.ftc.gov/business-guidance/resources/careful-connections-keeping-internet-things-secure

Used for: connected-device and smart-home security posture.

Key findings:

- Security should be designed from the beginning.
- Connected devices create risks because compromise can affect other connected
  systems.
- Reasonable security depends on device function, collected data, sharing, and
  likely risks.

Implication for Room AI:

- Do not start with real smart-home control.
- When device control is added, it should go through an explicit tool gateway
  with permissions, confirmation, logging, and least privilege.

### Donella Meadows Systems Thinking

Source: https://donellameadows.org/systems-thinking-resources/

Used for: architecture-thinking model.

Key findings:

- The iceberg model asks us to look below visible events into patterns,
  structures, and mental models.
- Stocks and flows help explain system behavior over time.

Implication for Room AI:

- The architecture should not be designed only as components.
- We need to track flows of audio, images, trust, user attention, permission,
  cost, data retention, and assistant agency.
- Trust can degrade quickly if camera/mic behavior is unclear.

## Early Conclusions

### 1. Browser-Based MVP Is Still The Best First Step

The browser gives us microphone, speaker, camera, and WebRTC access without
custom hardware. This matches OpenAI's guidance for browser voice agents and
lets us debug the interaction before building a device.

### 2. Realtime Voice Should Be The Main Interaction

For a room assistant, latency is part of the product experience. Realtime
speech-to-speech is the right default for the core interaction.

### 3. Snapshot-Based Vision Should Come Before Continuous Vision

Continuous room watching creates privacy, cost, and system complexity too early.
Camera snapshots are enough to validate "what do you see?" and room-aware Q&A.

### 4. Debuggability Must Be A Product Feature

This product combines browser permissions, audio capture, model behavior,
networking, image capture, and future tools. Without a debug panel, developers
will not understand failures.

### 5. Privacy Must Shape The Architecture

Mic/camera state, image capture, transcript retention, and future connected
accounts need explicit controls. Trust is not a UI polish item here; it is a
core system property.

### 6. Tool Use Must Be Delayed Or Narrow

LLM and API security sources both warn against excessive agency, weak access
control, and unsafe API consumption. The first assistant can observe and answer.
Actions should come later through a controlled tool gateway.

## Systems-Thinking Notes

### System Boundary For MVP

Inside:

- browser client
- microphone permission and audio stream
- speaker output
- camera permission and manual/requested snapshot
- backend session service
- OpenAI realtime model session
- local debug/event panel

Outside:

- smart-home device control
- long-term memory
- user accounts
- mobile apps
- custom hardware
- always-on monitoring

### Important Flows

- audio from user to model
- audio from model to user
- image snapshot from camera to model
- session credentials from backend to browser
- user trust from visible controls and predictable behavior
- cost from realtime audio/image usage
- debug evidence from events to developer

### Feedback Loops

- Clear state indicators increase trust.
- Hidden capture decreases trust.
- Better debug logs improve developer understanding and faster fixes.
- More tool permissions increase usefulness but also increase risk.
- More automation can reduce friction but also reduce user control.

### Delays

- permission prompt delay
- speech detection delay
- network/model response delay
- audio playback delay
- image capture and upload delay
- user trust recovery delay after unexpected behavior

## Open Questions Before Planning

1. Should the first prototype be push-to-talk or open mic after session start?
2. Should camera snapshots be manual only, or can the assistant request one when
   a visual question is asked?
3. Should the first version store any transcript locally, or only show it during
   the session?
4. Should the MVP require user login, or is local developer testing enough?
5. Should the first assistant be only conversational, or include one safe local
   tool such as "create a note"?
6. What environment are we targeting first: laptop browser, desktop browser,
   wall-mounted tablet, or future device?
7. What is the privacy promise for the MVP?

## Recommended Next Step

Create a planning document based on this research with:

- MVP scope
- non-goals
- architecture options
- recommended architecture
- risk table
- debug/observability design
- milestone plan
- questions for user decision

Do not implement until that plan is reviewed and approved.
