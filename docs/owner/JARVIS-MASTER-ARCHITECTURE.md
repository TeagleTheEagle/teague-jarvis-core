# JARVIS Master System Architecture and Capabilities (owner document)

> Text extracted 2026-10-01 from the owner's Word document
> `OneDrive\Desktop\JARVIS_Master_System_Architecture_and_Capabilities.docx`.
> Kept here as product direction for future engineering sessions. It is a planning
> reference, not a status claim; see docs/owner/ARCHITECTURE-ALIGNMENT.md for how it
> compares with the code. Section 17 (Codex as engineering operator) predates the
> 2026-10-01 delegation of engineering to Claude Code.

TEAGUE INDUSTRIES
JARVIS
Master System Architecture
and Capability Document
A consolidated record of the JARVIS platform, integrations, safeguards, device architecture and development additions
## Executive Summary
JARVIS has evolved from a PC-based AI assistant concept into a multi-device personal AI platform. The central architecture is one persistent JARVIS Core with shared memory, permissions, tools, identity and device state. Phones, PCs, glasses, vehicles and hardware projects connect to that Core as authenticated endpoints rather than becoming separate assistants.
This document consolidates the major additions made to the project: Wi-Fi and device discovery, capability and permission controls, Qwen/OpenAI provider support, voice and speech systems, Halo glasses, iPhone client architecture, remote connectivity, backup/recovery, deployment hardening, Stage 6 validation infrastructure, Windows packaging direction, Tesla integration and Mark I hardware integration.
Status legend
## Contents
## 1. Foundational Architecture — One JARVIS, Many Devices
Architecture rule: One persistent JARVIS Core; many authenticated clients and endpoints.
The defining decision is that JARVIS is not recreated independently on every device. The Core remains the authoritative system for identity, memory, tool orchestration, permissions and state. Devices expose capabilities to the Core and receive outputs from it.
One JARVIS identity and conversational continuity across devices.
One memory/state system rather than separate phone, PC, glasses or vehicle memories.
One permission and approval engine controlling actions across every endpoint.
One device registry tracking presence, identity, capabilities and trust.
AI providers are interchangeable intelligence backends; they do not become separate JARVIS instances.
Endpoint devices may perform local low-latency work, but authoritative orchestration remains with the Core.
Devices / Sensors  →  JARVIS Core  →  Memory + Permissions + Tools  →  AI Providers  →  Actions / Voice / Displays
## 2. JARVIS Core
Status: Implemented and under Stage 6 deployment/recovery acceptance.
Central conversation/orchestration layer.
Long-term memory and context handling.
Tool and action execution.
Device registry and presence awareness.
Permissions, approvals, authentication and audit behavior.
Provider routing and model selection.
Response lifecycle protections including cancellation and late-write handling.
Backend service currently associated with the local JARVIS endpoint on the Windows system.
## 3. AI Provider Layer — OpenAI, Qwen and Fallbacks
Design: JARVIS owns the loop; providers supply intelligence.
## OpenAI
Existing OpenAI provider path remains part of JARVIS.
Provider configuration and model routing remain behind the Core rather than inside device-specific clients.
Live model response can be externally blocked by API balance/quota without invalidating the local deployment path.
## Alibaba Cloud / Qwen
External API status: Standalone Qwen connectivity and voice technologies have been demonstrated; full production-Core integration remains a separate controlled integration task.
qwen3.8-max — intended for more complex reasoning/planning.
qwen3.8-flash — intended for fast/routine requests once fully validated.
qwen3-asr-flash — speech-to-text path.
qwen3-tts-vc-2026-01-22 — cloned-voice synthesis path.
Custom cloned JARVIS voice created for the Qwen TTS stack.
DASHSCOPE_API_KEY is the credential variable; actual secrets must never be embedded in prompts, source, reports or screenshots.
Qwen should be integrated behind existing JARVIS provider abstractions, not bolted directly into UI or device code.
## Provider fallback philosophy
Multiple providers remain available until a replacement path is fully validated.
Provider outages should not duplicate or fragment Core logic.
Errors, retries, cancellation, streaming and tool-call compatibility are provider-boundary concerns.
Provider switching must preserve JARVIS memory, identity, permissions and tool state.
## 4. Voice, Speech Recognition and Speech Synthesis
Direction: Modular STT → Core → TTS pipeline with provider choice and local fallback.
## Speech-to-text (STT)
Local faster-whisper / CTranslate2 path validated on clean Windows.
Microsoft Visual C++ x64 runtime identified as required for native CTranslate2 loading.
Cold and warm local transcription paths have been exercised.
Qwen ASR is a future provider option behind the same STT boundary.
## Text-to-speech (TTS)
Fish/JARVIS voice path validated in the clean VM.
Qwen cloned JARVIS voice available as an additional future TTS provider.
Voice provider changes must remain behind the existing VoiceEngine/lifecycle logic.
Cancellation, interruption, duplicate playback, cleanup and fallback behavior remain acceptance-critical.
Target voice loop: Microphone → STT → JARVIS Core → reasoning/tools → TTS → speaker/output endpoint.
## 5. Wi-Fi / Network Device Discovery and Device Registry
Direction: Discover, identify and authenticate devices; never equate “found on Wi-Fi” with “authorized to control.”
Network observation/discovery using mechanisms such as mDNS, ARP, hostnames and basic diagnostics.
Multi-device registry with presence/online state.
Capability manifests describing what each device can do.
Authenticated device pairing before any control path is trusted.
Planned PC/Mac agents and hardware endpoints.
Potential Home Assistant / home integration path.
Power-outage and network diagnostic awareness.
Future local hardware nodes such as ESP32/Mark I devices.
Important boundary: Discovery is not permission. A device may be visible on the network and still have zero control permissions.
## 6. Permissions, Approvals and Operator Control
Design goal: Every action is capability-scoped, attributable, revocable and auditable.
Central permission enforcement in the Core.
Authenticated device pairing and owner checks.
Per-capability authorization rather than generic unrestricted access.
Read-only vs mutating action distinction.
Required mode/scope/permissions per capability.
Approval requirements for sensitive actions.
Side-effect and reversibility metadata.
Idempotency rules for repeated commands.
Cancellation support for long-running actions.
Expiry, availability and usage-limit controls.
Audit logging and evidence trails.
Revocation and kill-switch concepts.
Operator/diagnostic modes that retain authentication and logging.
## Example capability contract
## 7. Remote Connectivity and Presence
Goal: JARVIS remains reachable securely when the user is away from the main PC.
Local Wi-Fi path when devices are on the same trusted network.
iPhone/cellular bridge for out-of-home access.
Secure private networking is preferred over directly exposing the Core to the public internet.
Tailscale-style private networking has been discussed as a practical direction.
Remote device presence should still obey the same authentication, capability and approval rules as local devices.
## 8. iPhone / iOS Client
Status: Native SwiftUI client project started; intended as a client to the single Core.
Native JARVIS iOS application shell in Xcode.
App display name configured as JARVIS.
Bundle identifier configured for Teague Industries JARVIS.
iPhone simulator configured for development; real iPhone 15 deployment planned.
Client responsibilities: UI, microphone/audio, camera/photo access where permitted, notifications, authentication and Bluetooth device bridges.
The iPhone app should not contain a second independent memory/Core.
Production Core connection should occur only after the mobile-facing API/auth contract is stable.
## 9. Brilliant Labs Halo Smart Glasses
Integration direction: Halo becomes a JARVIS endpoint: eyes, ears, speaker, HUD and motion/tap input.
Public Brilliant SDK / Python SDK / Flutter SDK / Web Bluetooth / Lua API / BLE specifications provide a documented integration surface.
Display can be used for JARVIS HUD output.
Microphones provide hands-free voice input.
Bone-conduction/speaker output can deliver JARVIS voice.
Optical sensor/camera can provide visual context where permitted.
IMU, taps/buttons and motion can become interaction inputs.
Lua can support device-side low-latency behavior.
iPhone can act as the Bluetooth bridge between Halo and the central JARVIS Core.
Native SwiftUI + CoreBluetooth is a viable direction rather than rebuilding the iOS app solely in Flutter.
Target Halo flow: Halo sensors → Bluetooth → iPhone JARVIS client → JARVIS Core → tools/providers → iPhone → Halo HUD + audio.
## 10. Windows Desktop Application and Stage 7 Direction
Current state: Core/development environment first; proper packaged application follows Stage 6 acceptance.
Future normal desktop experience: JARVIS icon → Core starts automatically → desktop UI opens → voice/STT/TTS ready.
No routine PowerShell/python/server.py workflow for normal use once packaging is complete.
Stage 7 is intended to prove install, first launch, update A→B, interruption recovery, rollback, uninstall, reinstall and state preservation.
Release artifacts should be hash-verified and provenance/evidence retained.
## 11. Backup, Restore and Disaster Recovery
Goal: A JARVIS failure or lost computer should not mean loss of identity, state or recoverable project data.
Backup architecture covers JARVIS data, relevant source/state and recovery metadata.
Secrets should remain outside ordinary backup artifacts where designed.
Python/Node dependency folders and model caches can be reconstructed rather than blindly copied.
Restore must be proven on disposable targets, not assumed from a successful file copy.
Identity/state preservation after restore is a Stage 6 acceptance objective.
External Samsung backup storage has been used for large JARVIS backup/copy workflows.
## 12. Deployment Hardening
Status: Substantial clean-Windows hardening completed; Stage 6 continues formal acceptance.
Python 3.12 identified as the validated Windows runtime; Python 3.11 produced a reproducible wearable cancellation failure.
Node.js LTS identified as required for existing JS-backed tests.
Microsoft Visual C++ x64 Redistributable identified as required by local STT/native CTranslate2.
Local voice/STT requirements made explicit.
Test requirements separated from production runtime dependencies.
Windows prerequisite checker and setup script introduced.
.env/API credentials intentionally kept outside clean deployment packages.
Clean VM successfully ran JARVIS, local STT, voice and core UI/command paths.
## 13. Stage 6 Preservation and Validation Infrastructure
Purpose: Prove deployment/recovery without silently mutating protected evidence or accepting incomplete results.
D:-based live evidence workspace to avoid C:-volume stalls observed during monitoring.
Heartbeat health monitoring with fail-closed behavior.
Process START/STOP lifecycle tracing.
Native process/PE-entry tracing for early startup evidence.
EventIdentifier collision defect identified and corrected.
Internally unique queue identity / exact-entry removal semantics.
PID-reuse-safe correlation logic.
Bounded finalization/quiescence before sealing evidence.
Child/helper process accounting and retained-handle evidence.
Archive and SHA-256 verification of evidence.
Protected-source preservation rules and read-only baseline design.
Large synthetic datasets used to validate collector scale before touching protected VM artifacts.
## Stage 6 principle
Fail closed. If identity, lifecycle, trace completeness, hashes, containment or preservation cannot be proven, the run stops and remains failed/blocked rather than being “mostly passed.”
## 14. Tesla Integration
Status: Future authenticated endpoint/integration path.
Tesla should connect through supported vehicle/account APIs or phone-mediated capabilities rather than unsafe direct vehicle hacking.
JARVIS can conceptually expose vehicle status and approved commands as capability-scoped tools.
Vehicle operations should require especially strict authentication, permission scope, logging and approval.
## 15. Mark I / ESP32 / Physical Hardware
Status: Hardware project and future JARVIS device endpoint.
Mark I hand/forearm project can become an authenticated device in the registry.
ESP32-class electronics or other controllers can expose a narrow capability manifest to the Core.
Physical actions should remain permission-scoped and fail-safe.
CAD and fabrication work is separate from Core identity; the device joins JARVIS rather than becoming a separate assistant.
## 16. Local / Offline AI Direction
Status: Future expansion; some local speech functionality already validated.
Local STT is already part of the validated direction.
Local model runtimes such as Ollama/llama.cpp and local Qwen-class models have been considered.
Local wake-word and local TTS remain possible future paths.
Cloud providers can be used for high-capability tasks while local services preserve resilience and privacy.
Offline mode is a separate implementation objective; a cloud Qwen connection does not make JARVIS offline.
## 17. Codex as an Engineering Operator
Role: Engineering/development agent, separate from the JARVIS user-facing Core.
Codex is used to implement, test, audit and document JARVIS.
Long-running test campaigns and evidence archiving can be delegated to Codex.
Codex should not silently alter production behavior or cross protected validation gates.
Long-term, JARVIS may be able to delegate engineering tasks to Codex through controlled tools while preserving Core permissions and auditability.
## 18. Security Model
Secrets are never embedded in source, screenshots, reports or prompts.
API keys are external configuration; exposed keys should be rotated.
Authentication is required separately from network visibility.
Permissions are capability-scoped.
Approval is required for sensitive/irreversible operations.
Actions are auditable and ideally reversible where possible.
Protected VM/evidence workflows are isolated from ordinary experimentation.
Validation never weakens Windows security policy merely to force a pass.
Production changes and validation infrastructure changes are kept distinct.
## 19. Capability and Device Expansion Model
New devices should follow a consistent onboarding model rather than adding custom one-off logic to the Core.
Device is discovered or introduced.
Device identity is authenticated/paird.
Device registers its capabilities.
Capabilities declare required permissions, reversibility, limits and approval rules.
JARVIS Core decides whether/when an action may run.
Device adapter performs the operation.
Result and audit evidence return to the Core.
Capability can be revoked without rebuilding JARVIS.
## 20. Current System Picture and Remaining Work
Current conceptual system:
JARVIS Core — central identity, memory, tools, permissions and orchestration.
Provider layer — OpenAI today, Qwen integration path, future local providers.
Voice layer — local STT + cloud/local TTS options.
Device layer — Windows PC, iPhone, Halo, future hardware endpoints, Tesla and home systems.
Security layer — authentication, capability permissions, approvals and audit.
Recovery layer — backup, clean deployment, restore and preservation evidence.
Engineering layer — Codex, regression suites, staged acceptance and evidence archives.
## Major remaining work
Complete Stage 6 clean deployment, protected baseline, isolation, recovery and final preservation acceptance.
Proceed into Stage 7 Windows packaging/update/rollback/uninstall/reinstall acceptance.
Complete Qwen provider integration behind existing abstractions.
Complete native iOS client and secure Core connection.
Implement Halo BLE/CoreBluetooth bridge and HUD/voice workflows.
Expand authenticated device adapters for home, vehicle and physical hardware.
Continue local/offline model capability as a later resilience/privacy layer.
## 21. Teague Industries Engineering Principles
“Slow motion is better than no motion.”
— Mr. Teague & White Audi
“Trust the process > rush the process.”
— Mr. Teague
“Quantity and quality as one: use the greatest useful depth and coverage possible, but never increase scope past the point where clarity, precision or execution quality begins to drop.”
— Working standard
## Master Summary
JARVIS is now best understood as a private personal AI operating platform. The Core is the persistent brain and authority; models provide intelligence; devices provide sensors, outputs and actions; permissions govern what can happen; recovery and validation make the system trustworthy. The long-term objective is not to create many disconnected assistants, but to make one JARVIS present across the user’s computing, wearable, vehicle and physical-device environment.
Canonical architecture: ONE JARVIS CORE → shared memory + permissions + tools + device registry → multiple AI providers → multiple authenticated devices.
Document note: This is a consolidated project reference, not a claim that every planned capability is already production-complete. Items are explicitly separated into validated, implemented/active, planned/integration and deferred/external states where relevant.
[table 0]
Owner | Mr. Teague
System | JARVIS — One Core, Many Devices
Organisation | Teague Industries
Document purpose | Master reference for what JARVIS is, what has been added, what is validated, and what remains planned
[table 1]
VALIDATED | Demonstrated successfully in testing or in the current JARVIS environment.
IMPLEMENTED / ACTIVE | Exists in the project or workflow, but may still be undergoing broader acceptance.
PLANNED / INTEGRATION | Architecture or integration path has been defined but is not fully production-integrated.
DEFERRED / EXTERNAL | Blocked by external factors, future hardware, quota, or later-stage acceptance.
[table 2]
1. Foundational Architecture — One JARVIS, Many Devices | 12. Deployment Hardening
2. JARVIS Core | 13. Stage 6 Preservation and Validation Infrastructure
3. AI Provider Layer — OpenAI, Qwen and Fallbacks | 14. Tesla Integration
4. Voice, Speech Recognition and Speech Synthesis | 15. Mark I / ESP32 / Physical Hardware
5. Wi-Fi / Network Device Discovery and Device Registry | 16. Local / Offline AI Direction
6. Permissions, Approvals and Operator Control | 17. Codex as an Engineering Operator
7. Remote Connectivity and Presence | 18. Security Model
8. iPhone / iOS Client | 19. Capability and Device Expansion Model
9. Brilliant Labs Halo Smart Glasses | 20. Current System Picture and Remaining Work
10. Windows Desktop Application and Stage 7 Direction | 21. Teague Industries Engineering Principles
11. Backup, Restore and Disaster Recovery | 
[table 3]
Capability | Permission posture | Example
Read status | Low-risk / read-only | Battery, presence, device status
Control device | Authenticated + scoped | Turn on an approved endpoint
Sensitive action | Explicit approval | Account, system, irreversible or external side effect
Emergency stop | Owner-only / high priority | Revoke or halt device/action execution
