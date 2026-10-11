# Current setup and verification

Latest Milestone 4: [real Core demo, verification and limitations](MILESTONE-4-REVIEW.md). Real vision acceptance is blocked by HTTP 429; mock modes remain runnable. [One-Core invariant](ONE-JARVIS.md) applies to all future devices.

## Latest: mock glasses now runnable

Milestones 2–3 are implemented. Double-click `Start Mock Glasses.cmd` in the JARVIS folder or run `.\.venv\Scripts\python.exe -m wearables.demo --interactive` there. Read [the current run guide and verification report](MILESTONE-3-REVIEW.md). No API credits or glasses needed. The audit-only notes below describe the earlier Milestone 1 snapshot.

This is an audit/documentation deliverable, not an installed glasses application. No new runtime dependencies, services, credentials, database migrations or SDK installation were performed.

Existing workspace: `outputs/jarvis`. Windows PC supports the planned independent mock work. No Mac is available; native iOS/Meta SDK compilation and signing require a compatible Mac/Xcode environment later. Apple membership does not supply a compiler. Physical glasses are unnecessary for the Windows mock, but required for real audio route, heat, battery, locked-phone and latency validation.

Focused offline regression executed 9 September 2026 from JARVIS root:

```powershell
.\.venv\Scripts\python.exe -m unittest test_phone_bridge test_conversation_context test_memory_voice test_screen_observation test_voice_engine -q
```

Result: 20 tests passed in 1.792 seconds. Coverage is existing phone authentication/task retry behavior, selected context/memory/observation/voice logic. Not the full regression suite. No real API, microphone, glasses, TLS certificate path, phone deployment or native build tested.

For Milestone 2 onward, use temporary data directories and synthetic fixtures. Do not point development mocks at live personal storage. Before source refactor, create/rehearse a backup and add safe coverage of new source folders to recovery inventory.

No hardware purchase or Tailscale setup required to approve/start Milestones 2–3.
