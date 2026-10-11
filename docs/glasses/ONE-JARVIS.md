# One JARVIS, many devices

9 September 2026. Binding architecture, recorded in root AGENTS.md.

Production: device -> capabilities -> running JARVIS App -> shared Store/personality/providers/VoiceEngine. Native clients never load provider credentials, reproduce personality, or create an App. `wearables/real_core.py` is a loopback HTTP adapter to that running instance. `wearables/service.py` invokes its existing methods. `MockCore` and temporary probe App instances are explicit testing substitutes, not device-specific deployments.

`device_registry.py` is owned by App. It tracks declared/ready capabilities, presence expiry, simulated status and the device for each active request. `device_registry` is a read-only Core tool. Unknown or expired capabilities are not selected. The PC adapter's presence is refreshed on Core activity; peripheral readiness is not invented. This prototype registers the local wearable client; it does not claim any phone or glasses is physically connected.

The registry can plan one request using several devices: camera from glasses, display from PC, speaker from the initiating device where available. `plan` ranks an available explicit preference first, then the interaction device, then a deterministic available candidate. This is a basic capability policy, not a claim of context-aware acoustic/device quality optimization. Plans are explicitly non-executable and still need action authorization. Future device adapters will publish supported readiness and permission changes; registration itself never grants control.

Mock capability descriptors remain simulated. Cross-device planning excludes them unless a test explicitly opts in. Device disconnect clears its active request associations. Tests cover mixed-device planning, expiry, unavailable permissions, mock isolation and disconnect.

Preserved: existing PC tool set and desktop behavior. Wearable requests have a narrower read-only tool allowlist; vision has no executable tools. There is one shared conversation store, using wearable-prefixed conversation IDs in the same database. Conversation IDs distinguish sessions, not identities. Memory lookup uses the existing Core context. Memory writes through this adapter remain deferred; no parallel wearable memory database exists.

Remaining work: physical presence adapters; multi-client authentication and sessions; permission-aware executable cross-device orchestration; native phone client. No physical integration has begun.
