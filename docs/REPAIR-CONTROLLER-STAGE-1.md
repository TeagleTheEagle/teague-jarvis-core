# Restricted repair controller — 11 September 2026

Stage result: PASS for numeric fixture execution and reviewed isolation probes. General autonomous diagnosis/deployment is NOT implemented.

## Built

repair_sandbox.py provides a standalone test-only controller using existing rootless Podman in Ubuntu under jarvis-repair. It creates one uniquely named disposable container per invocation, supplies bounded source via stdin, and deletes only that owned container. It neither imports server.App nor instantiates a Core, provider, store, device registry or voice owner. No production files, memory or credentials are mounted. No provider calls were made.

The public check_candidate entry point reuses repair_trial.validate_candidate: only the single numeric delay function is accepted. Arbitrary imports, loops, filesystem operations and model-supplied commands are rejected before runtime. A separate host AST interpreter computes values independently; raw container output alone cannot certify success. No model-supplied test scripts, arbitrary file manifests or artifact export. The private execution primitive runs explicitly reviewed probes only; it is not registered as a JARVIS tool or network endpoint.

Official Python image downloaded as docker.io/library/python:3.12-alpine; runs pin local content ID 28eb0cb65acb65b970e85c0dc57d10067868fae8dd00d072413df273132123ac and never pull automatically. Container: UID/GID 65534, no network, read-only root, no writable temp mounts, zero capabilities, no-new-privileges, seccomp, 128 MiB memory, zero swap, 32 PIDs, half CPU, 1–15 seconds, 8 KiB input, 16 KiB captured output. Host environment excludes WSLENV and provider/proxy configuration. Podman preflight requires rootless/seccomp/cgroup v2 controllers.

Cancellation kills/removes the owned container with zero grace, then closes client pipes and verifies absence. Cleanup failures raise and prevent a successful result. Runtime commands have separate bounded control timeouts; a frozen WSL service can still delay cleanup and must be treated as a failure, not assumed stopped.

## Actual evidence

verify_repair_sandbox.py produced docs/repair-sandbox-results.json:

- Faulty baseline rejected: 4/6 correct.
- Previously real-Core-generated candidate executed in real Python: 6/6, READY_FOR_REVIEW, 1.110 seconds including controller overhead after preflight. This was the saved candidate, not a fresh AI generation.
- Non-root, no Windows mount, no Podman socket, no forwarded credentials, read-only filesystem, actual failed connection to TEST-NET 192.0.2.1, expected memory/PID cgroup values: all passed.
- Output flood stopped, retained at most 16 KiB: 0.843 seconds.
- Two-second container timeout: process ended nonzero, total 2.718 seconds.
- Memory allocation probe stopped with exit 137: 0.907 seconds.
- Process creation denied after 31 children (32 total including parent); children reaped: 1.219 seconds.
- Cancellation scheduled after three seconds: CANCELLED, 3.172 seconds from controller start. All eight runs verified cleanup.

Initial tests exposed a roughly 11-second cancellation/output-stop delay. First corrected ordering so container removal precedes pipe closure; then identified Podman's default ten-second stop grace and set --time=0. Final live probe suite passed after both fixes. These earlier attempts are not counted as successful cancellation evidence.

Unit checks: 14 targeted tests passed. Full Python discovery: 182/182 passed in 31.941 seconds (before final zero-grace flag adjustment; live probes retested that adjustment). Desktop: 13/13 passed in 26.647 seconds using bundled Node because npm was absent from PATH. No live voice or UI manual verification performed. Production source remained unchanged; existing unrelated UI edits were preserved.

## Reproduce and next gate

From the authoritative project directory run `.venv\Scripts\python.exe -m unittest test_repair_sandbox` for deterministic unit checks, or `.venv\Scripts\python.exe verify_repair_sandbox.py` for explicit live WSL/container tests. The latter needs access to the installed WSL distribution and image and replaces only its test-result JSON. It does not call AI or deploy anything.

Remaining: automated bounded fault selection/diagnosis through existing Core; broader patch contracts and independent tests; external stop-control integration; restart/controller-crash/race testing; approved staging/promotion and verified rollback. No automatic retries, daemon, scheduler, new assistant goals, purchases or live self-modification. Linux containers share a WSL kernel and cannot prove Windows/Electron correctness. Restricted fixture success is not acceptance of arbitrary generated-code execution.

Files created: repair_sandbox.py, test_repair_sandbox.py, verify_repair_sandbox.py, docs/repair-sandbox-results.json, this report. Source snapshots and evidence copied to Teague Industries records.
