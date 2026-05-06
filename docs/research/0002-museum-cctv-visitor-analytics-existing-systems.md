# Museum CCTV Visitor Analytics: Existing Systems Research

Date: 2026-05-05

Status: research brief, not an implementation plan.

## Updated Product Understanding

The project is no longer a general room voice assistant.

Updated direction:

- Phase 1: use existing CCTV/camera feeds to understand visitor analytics in a
  museum or gallery.
- Phase 2: add AI interaction based only on what the system sees in the gallery.
- No microphone.
- Output can use speakers.
- The system should infer visitor/gallery interaction from camera behavior, not
  spoken input.

## Main Answer

Yes, similar systems already exist.

The market already has products for:

- people counting
- occupancy
- visitor flow
- dwell time
- queue detection
- heatmaps
- CCTV-based movement analytics
- museum/gallery visitor analytics dashboards

There is also academic research on:

- museum visitor tracking with cameras
- visitor-artwork relationship analysis
- behavior clustering
- ambient intelligence in museum spaces
- automatic audio guides triggered by visual recognition

The more differentiated idea is:

> A fixed-gallery, no-microphone AI system that watches visitor interaction with
> exhibits through CCTV/cameras and uses speakers to respond contextually.

That exact combination appears less common than either visitor analytics alone
or phone/headset-based AI museum guides.

## Existing Commercial / Product Categories

### 1. CCTV Video Analytics For Museums

Source: https://www.isarsoft.com/solutions/video-analytics-for-museums

Used for: evidence that CCTV/video analytics for museums already exists.

Findings:

- Isarsoft markets video analytics specifically for museums.
- Claimed use cases include planning, operations, security, visitor counting,
  flow analysis, layout optimization, queue management, and real-time KPIs.
- It describes integration with existing camera systems and BI/VMS systems.
- It emphasizes anonymization, GDPR compliance, and live processing.

Implication:

- Phase 1 is not a new invention by itself. We need differentiation through
  experience design, privacy posture, museum-specific insights, cost, or Phase 2
  interaction.

### 2. Real Museum Deployment: Wien Museum

Source: https://www.isarsoft.com/article/wien-museum-case-study

Used for: evidence of real museum deployment.

Findings:

- Isarsoft and PKE announced an AI-powered video-based visitor counting system
  at Wien Museum.
- The system integrates into existing camera infrastructure.
- It tracks visitor movement patterns, especially at entrances and exits.
- The stated goals include replacing manual counts, improving operations, and
  supporting data-driven museum management.

Implication:

- Museums are already buying this category.
- A new product must either compete with or build on this kind of capability.

### 3. Edge Camera Analytics

Source: https://help.axis.com/en-us/axis-people-counter

Used for: understanding camera-vendor people counting capabilities.

Findings:

- AXIS People Counter runs as an analytic application on compatible network
  cameras.
- It counts people passing through entrances, directions of movement, occupancy,
  and average visiting time.
- Axis documentation includes mounting guidance, multi-camera occupancy setup,
  validation, and API examples.

Source: https://developer.axis.com/vapix/applications/people-counter-api/

Used for: understanding integration/API possibilities.

Findings:

- Axis exposes people-counter data through APIs.
- The API can return real-time in/out counts and available historical data.

Implication:

- If a museum already uses Axis cameras, the MVP might integrate with camera
  analytics instead of building all detection from scratch.
- Camera placement and calibration are part of the product, not an afterthought.

### 4. General Video Intelligence / Business Intelligence

Source: https://www.briefcam.com/solutions/planning-research/

Used for: evidence that video can be aggregated into operational analytics.

Findings:

- BriefCam offers quantitative analysis of video data.
- Claimed features include object movement, demographic segmentation, behavior
  trends, hotspots, object interactions, dashboards, and correlation with third
  party data.

Implication:

- Enterprise video-intelligence platforms already cover analytics dashboards.
- We should be careful with demographic analysis because it increases privacy,
  fairness, and legal risk.

### 5. CCTV Heatmap / Dwell Analytics

Source: https://facit.ai/heatmap-people-tracking-visualisation-software/

Used for: evidence of CCTV-compatible heatmap and dwell-time analytics.

Findings:

- Facit describes heatmap people tracking software compatible with existing CCTV.
- It focuses on dwell time, traffic flow, and visitor/customer spread.

Implication:

- Heatmaps and dwell time are commodity analytics.
- Our product should treat them as baseline features, not the unique value.

### 6. Sensor-Based Museum Analytics

Source: https://intelligentcounting.com/

Used for: evidence that culture/heritage visitor analytics is a mature market.

Findings:

- Intelligent Counting says it serves cultural and heritage sites.
- Claimed capabilities include live footfall tracking, space utilization, and
  individual visitor journeys.

Source: https://www.visitorcount.com/pages/people-counting-analytics-for-museums-galleries-wellpoint

Used for: evidence of non-camera visitor analytics alternatives.

Findings:

- Wellpoint targets museums and galleries with visitor counting and analytics.
- It emphasizes live occupancy, reporting dashboards, peak times, exhibition
  popularity, queue management, and dwell-time insights.
- It uses sensor-based detection rather than cameras.

Implication:

- Not all competitors use CCTV. Some compete by being more privacy-preserving.
- A camera-based product must justify why video is necessary.

## Research / Academic Evidence

### 1. Deep Learning For Museum Visitor Behavior

Source: https://www.mdpi.com/2076-3417/12/2/533

Used for: museum-specific computer vision research.

Findings:

- The paper proposes using deep learning and RGB cameras to collect museum
  visitor behavior data.
- It discusses visitor movement, time spent near artworks, distance from
  artworks, trajectories, and heatmaps.
- It frames the goal as helping museum staff understand visitor flow, artwork
  engagement, arrangement, and lighting issues.

Implication:

- Our Phase 1 metrics should include count, occupancy, trajectory, dwell time,
  exhibit engagement, and heatmaps.
- The research supports using off-the-shelf cameras, but privacy and calibration
  must be handled carefully.

### 2. Visitor Behavior Visualization And Prediction

Source: https://research.vu.nl/en/publications/visualizing-clustering-and-predicting-the-behavior-of-museum-visi

Used for: visitor analytics beyond simple counting.

Findings:

- The paper explores visualizing, clustering, and predicting museum visitor
  behavior using low-cost mobile and fixed proximity sensors.
- It notes that surveys and manual observation are limited by scale and bias.

Implication:

- A valuable product should move from raw counts to patterns: visitor paths,
  common route clusters, congestion, exhibit popularity, and possible layout
  improvements.

### 3. Visitor-Artwork Network Analysis

Source: https://www.sciencedirect.com/science/article/pii/S1474034621000616

Used for: evidence of artwork-level engagement analytics.

Findings:

- Cameras installed in a museum recorded visitors.
- Object detection and image retrieval were used to track visitors from video.
- Time spent with different artworks was measured.
- Data was converted into a visitor-artwork network.

Implication:

- Exhibit-level analytics are a strong direction for a museum-specific product.
- This is more valuable than only "how many people entered."

### 4. Ambient Intelligence For Museums

Source: https://www.sciencedirect.com/science/article/abs/pii/S0167865522002173

Used for: evidence of ambient intelligence and visitor behavior analysis in
museum environments.

Findings:

- SeSAME is described as an ambient intelligence system for museum environments.
- It collects and analyzes visitor behavior.
- It uses re-identification and multimodal deep learning for visual profiling of
  visitor interest.

Implication:

- Ambient AI museum systems are being researched.
- Re-identification and visual profiling create higher privacy and fairness
  risks. Our product should avoid identifying individuals unless there is a very
  strong reason and legal basis.

### 5. Computer Vision For Museum Exhibit Design

Source: https://www.rti.org/insights/computer-vision-for-museum-exhibit-design

Used for: practical museum/exhibit design use case.

Findings:

- RTI and the North Carolina Museum of Natural Sciences used computer vision to
  understand how visitors move through an exhibit.
- The article frames the problem as replacing manual observation and surveys
  with behavioral evidence.

Implication:

- Museum staff pain is real: they want to know how visitors actually move, not
  only what surveys say.

## Existing AI Museum Guide / Interaction Products

### 1. Camera-Based AI Museum Guide

Source: https://www.tell-me.ai/

Used for: evidence that camera-based AI museum guides already exist.

Findings:

- TellMe lets visitors point a device camera at exhibits and receive guide
  content.
- It emphasizes browser-based delivery, no app install, approved collection
  sources, institutional policy, and analytics.

Implication:

- AI museum guides exist, but this is visitor-device centric, not fixed CCTV +
  room speaker.

### 2. Mobile AI Museum Guide

Source: https://vibemuse.app/

Used for: evidence of multimodal AI museum-guide consumer apps.

Findings:

- VibeMuse lets visitors scan art, ask questions, and hear spoken explanations.
- It supports image/video/voice/text input and voice output.

Implication:

- Phone-based AI guides are not our exact target, but they compete for the
  visitor-experience layer.

### 3. Automatic Museum Audio Guide

Source: https://www.mdpi.com/1424-8220/20/3/779

Used for: evidence of camera-triggered audio guidance.

Findings:

- The paper presents an automatic museum audio guide with a camera-equipped
  headset.
- The system recognizes artworks and triggers audio guidance.
- It was tested in a real museum pilot.

Implication:

- Camera-triggered audio guidance exists, but it is device/headset-based.
- Our no-mic, fixed-camera, shared-speaker version is a different interaction
  model.

## Privacy / Governance Sources

### ICO CCTV And Video Surveillance Guidance

Source: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/cctv-and-video-surveillance/

Used for: privacy expectations around CCTV and video surveillance.

Findings:

- The ICO treats video surveillance systems as processing personal data when
  identifiable individuals are involved.
- It covers CCTV, AI-based surveillance, facial recognition, drones, dashcams,
  and similar systems.

Implication:

- Visitor analytics from CCTV is privacy-sensitive even if the product's goal is
  operational analytics.
- The system needs signage, purpose limitation, access control, retention rules,
  and privacy review.

### EDPB Video Devices Guidance

Source: https://www.edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-32019-processing-personal-data-through-video_pt

Used for: data protection principles around video devices.

Findings:

- EDPB guidance covers lawfulness, transparency, sensitive data, and video
  device processing.
- The summary warns against using surveillance for unexpected secondary
  purposes.

Implication:

- A museum cannot safely reuse CCTV for analytics or AI interaction without a
  clear lawful basis, transparency, and purpose definition.

### NIST AI Risk Management Framework

Source: https://www.nist.gov/itl/ai-risk-management-framework

Used for: AI risk management framing.

Findings:

- NIST AI RMF is designed to help manage risks from AI systems.
- It emphasizes trustworthy AI and the govern, map, measure, manage lifecycle.

Implication:

- Phase 2 should be treated as an AI risk-management problem, not only a feature
  problem.

## What Already Exists vs What May Be New

Already exists:

- CCTV/video-based people counting
- occupancy analytics
- dwell time analytics
- heatmaps
- visitor flow dashboards
- queue analytics
- museum visitor analytics
- camera-based museum audio guides
- phone-based AI museum guides
- research systems for visitor-artwork behavior

Possibly differentiated:

- fixed-gallery camera-only AI interaction
- no microphone
- no visitor phone/app
- speaker-based contextual response
- interaction triggered by observed behavior
- museum-approved content grounding
- privacy-preserving analytics first, interaction second
- developer/debugger-first architecture for museum operators

## Product Implications

Phase 1 should not try to beat mature vendors on generic people counting alone.
It should become museum-specific quickly.

Useful Phase 1 analytics:

- entry/exit counts
- live occupancy by gallery
- dwell time by exhibit zone
- queue/crowding detection
- heatmaps
- visitor paths
- exhibit engagement score
- ignored exhibits
- congested zones
- time-of-day patterns
- gallery layout recommendations

Phase 2 should not start with full "AI personality." It should start with
simple camera-triggered speaker behaviors:

- visitor stands near exhibit for long enough -> play short approved context
- visitor appears confused or repeatedly shifts between label and artwork ->
  offer brief help
- crowd forms -> switch to short group explanation
- visitor blocks pathway or enters restricted area -> safety message
- child-height visitor detected near interactive exhibit -> age-appropriate
  prompt, if allowed by policy

High-risk features to avoid early:

- face recognition
- identity tracking
- demographic guessing
- emotion detection
- individual re-identification
- persistent visitor profiles
- hidden recording
- open-ended AI speech without curator-approved grounding

## Open Questions For Planning

1. Are we building for an actual museum with existing CCTV, or a prototype using
   sample/recorded footage?
2. Do we know the CCTV vendor or camera protocol, such as RTSP, ONVIF, Axis, or
   a VMS platform?
3. Do we need real-time analytics first, or offline reports first?
4. Should Phase 1 store video, store only derived metrics, or support both?
5. What analytics matter most to museum staff: occupancy, exhibit engagement,
   crowding, security, or layout optimization?
6. For Phase 2, should speaker output be public-room audio or directional audio?
7. Should interaction be triggered automatically, or should a visible button/sign
   let visitors opt in?
8. What privacy/legal jurisdiction applies to the first deployment?

## Recommended Next Step

Update the product blueprint and architecture plan around the museum/gallery
use case:

- Phase 1: CCTV visitor analytics
- Phase 2: camera-only speaker interaction
- No microphone
- Privacy-preserving by default
- Museum-specific analytics, not generic retail analytics

No implementation should start until the user confirms this updated direction.
