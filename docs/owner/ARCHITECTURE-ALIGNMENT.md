# Owner architecture document vs. code — 2026-10-01

Compares docs/owner/JARVIS-MASTER-ARCHITECTURE.md with the claude/main code.

| Document says | Code today | Status |
|---|---|---|
| §1 One persistent Core; devices are authenticated clients | One Core per data folder enforced (core_lock.py); desktop and Intelligence join the shared background Core | Aligned (2026-10-01) |
| §10 "JARVIS icon → Core starts automatically → desktop UI opens" | Desktop app joins or starts the background Core; Startup shortcut (Install-JARVIS-Shortcuts.ps1) launches it at login | Aligned for development builds; packaged installer is Stage 7 |
| §3 OpenAI provider | providers.py (chat, vision, STT, TTS "cedar") | Implemented |
| §3 Qwen / DASHSCOPE_API_KEY | No production code reads DASHSCOPE_API_KEY; "qwen" appears only as local Ollama model names in Stage 4 evidence | Not started in code (document correctly says integration is separate) |
| §4 Local STT (faster-whisper), Fish TTS | local_stt.py, requirements-local-voice.txt; Fish in providers.py | Implemented; local-voice requirements not installed in this workspace yet |
| §5 Discovery is not permission; device registry | device_registry.py: registration grants no tool authority | Aligned; network discovery (mDNS/ARP) not implemented |
| §7 Remote access via private networking (Tailscale-style) | Core bound to 127.0.0.1 only | Deferred by owner decision (2026-10-01) |
| §8 Native SwiftUI iOS app in Xcode | Repository holds only ios/JARVIS/{Domain,SessionModel,MockCoreClient}.swift | The Xcode project is not in this workspace; supply it if iOS work starts |
| §9 Brilliant Labs Halo glasses | wearables/ code and AGENTS.md refer to Meta glasses ("No physical Meta integration is authorized yet"); no Halo/Brilliant references | **Owner decision 2026-10-01: the target glasses are Brilliant Labs (Halo).** Meta references are historical. Physical glasses integration is still not started and needs its own go-ahead; the AGENTS.md hardware caution applies to Halo too. |
| §14 Tesla, §15 Mark I / ESP32 | No code | Future, as the document states |
| §17 Codex as engineering operator | Superseded: Claude Code is sole writer, Codex reviewer-only (governance/OWNER-DELEGATION.md) | Document predates delegation |
