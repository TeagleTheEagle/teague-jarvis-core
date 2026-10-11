# JARVIS architectural invariant

ONE JARVIS. ONE IDENTITY. ONE MEMORY. ONE INTELLIGENCE. MANY DEVICES.

All production devices connect to the running central App/Core. Personality, provider configuration, context, preferences, voice configuration, memory and tool policy stay there. Never instantiate a second production App/Store/AI stack for phone, glasses, watch, car or home adapters. Temporary isolated App instances in tests/probes are test fixtures, not a deployment architecture.

Device adapters expose capabilities and media only. The Core-owned DeviceRegistry owns presence, request source and proposed cross-device routing. Registration never grants tool authority. Plans are not executed unless each action passes existing authorization. Preserve all existing PC capabilities.

MockCore is explicit development simulation, labelled as such, without production memory, credentials or copied personality. Never fall back silently from real services to mock answers.

No physical Meta integration is authorized yet. Finish/review the real Core adapter milestone before proceeding to physical hardware.

## Teague Industries project storage

The canonical project-record folder is `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE`.
Keep source snapshots, design documents, milestone evidence, experiment records and change-history exports there through `Sync-TeagueIndustries.ps1` when the folder is writable. Keep the heavy local runtime (`.venv`, dependency caches, model data and generated runtime state) in the local workspace so the application remains reliable. Never copy `.env`, API keys, tokens or other secrets into the Teague Industries record folder.
