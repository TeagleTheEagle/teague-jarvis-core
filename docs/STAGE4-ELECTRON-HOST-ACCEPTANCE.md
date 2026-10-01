# Approved host-context procedure for actual Stage 4 Electron acceptance

Approved by the user on 2026-09-15. This is an acceptance execution procedure, not an Electron runtime correction or a general exception to TEST isolation.

## Scope and invocation

Use this context only when the approved acceptance step genuinely needs the actual Electron desktop. Keep non-desktop tests in their existing appropriate context. Do not run a production shortcut or launcher.

Working directory:

```text
C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis
```

Run the existing unchanged probe:

```powershell
.venv\Scripts\python.exe -B tests/lifecycle_stage4/fixtures.py --electron-app-probe
```

When invoked through Codex's command tool, select the reviewed host context (`sandbox_permissions: require_escalated`) for this exact isolated desktop probe. This setting selects the command execution context; it does not authorize changing Windows settings, elevating Electron's privileges, or disabling Chromium's renderer sandbox. The recorded successful host token was Medium integrity, with Administrators membership deny-only.

Before launch, compare the frozen response-commit and client/executable hashes with their reviewed manifests. Record the invocation, working directory, context, selected nonsecret environment, start/end time and exit result. Stop on a hash mismatch or an unexpected failure. Do not retry automatically or introduce flags.

The existing probe provisions a fresh `TEST-STAGE4-*` namespace with synthetic TEST state, starts one disposable isolated TEST Core, and attaches both real Electron TEST clients to it. Its TEST credentials remain in the existing private process boundary. Do not collect or archive credentials, private bootstrap configuration, production data, or Electron profiles.

## Required retained checks

- Authenticated peer/Core identity and independent TEST client profiles.
- Both actual renderers attached to the same TEST Core and shared TEST conversation state.
- Renderer privilege/network/legacy bridge denials and foreign request-control denial.
- Actual request completion; close/reopen and renderer-crash isolation; no old request replay.
- Both screenshot/visibility results, followed by visual inspection of the captured files. Do not replace this with Node-only or browser-only evidence.
- Separately authorized TEST shutdown, normal client/Core exits, and lifetime-lock release after Core exit.
- Existing cooperative cleanup only. A retained or uncertain TEST process requires the applicable reviewed cleanup procedure; never terminate by PID alone or kill unrelated processes.

Physical voice/capture remains unavailable in this fixture. The two standard screenshots show authenticated interfaces before the request is submitted; request completion is a separate actual-form check. This probe alone does not establish all response-commit persistence/race/restart requirements.

## Disclosed execution-environment limitation

Electron **44.2.0** repeatedly failed in the restricted Codex command context. Six GPU subprocess exits with code **-1073741515 / 0xC0000135** preceded `GPU process isn't usable`. The installed Windows SDK identifies that status as **STATUS_DLL_NOT_FOUND**. The exact missing or inaccessible DLL and its underlying cause remain **unconfirmed**.

The same frozen source, executable, launch construction, working directory and selected environment passed 29 actual Electron checks in the reviewed host context. Preserve the restricted failures as execution-environment findings; do not erase them or relabel them as JARVIS response-commit runtime failures.

No new `--disable-gpu` or other Chromium switches are authorized by this procedure. The client's pre-existing acceleration settings, renderer sandbox, authentication, ownership, lifecycle and TEST isolation stay unchanged. No DLL replacement, driver installation, cache deletion, ACL change or Windows security change is authorized.

Evidence: [diagnosis report](lifecycle-stage4-evidence/electron-gpu-diagnosis-20260915/REVIEW.md), [context comparison](lifecycle-stage4-evidence/electron-gpu-diagnosis-20260915/context-comparison.json), and [preserved run comparison](lifecycle-stage4-evidence/electron-gpu-diagnosis-20260915/result-comparison.json).

## Rollback and review boundary

There is no runtime patch or data migration to roll back. The procedure can be withdrawn through review by reverting this document and its acceptance references. Preserve all evidence and profiles; do not roll back databases or modify source to conceal a failing context.

Production remains unchanged and blocked. This procedure does not declare Stage 4 complete, create its acceptance commit, or authorize Stage 5.
