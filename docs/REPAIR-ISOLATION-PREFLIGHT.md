# General repair isolation — preflight, 11 September 2026

Status: BLOCKED ON HOST PREREQUISITES. No general generated code executed.

Read-only checks: Windows 11 Home 64-bit build 26200; Ryzen 7 3700X; 32 GiB installed RAM; SLAT supported; VirtualizationFirmwareEnabled=false; HypervisorPresent=false. WSL reports not installed. Docker/Podman/VMware/VirtualBox CLIs not found in PATH; WindowsSandbox.exe absent. This is not an exhaustive inventory of all installed applications. Initial CIM query was denied in the execution sandbox; repeated read-only with escalation succeeded. No automatic approval rejection occurred.

## Proposed setup to review

1. User enables AMD SVM/CPU virtualization in firmware. Verify hardware status afterward. No BIOS setting changed by this task; motherboard-specific directions must be confirmed from the actual model/manual.
2. With explicit installation approval, install WSL2 and its required virtualization components through Microsoft's documented setup. This is a persistent Windows feature change and may need administrator access and a reboot. Never reboot without separate agreement.
3. Select and verify a Linux container runtime after checking current Home-edition compatibility and licensing. Docker's current page states Home supports Linux containers but lists Pro/Enterprise/Education in the requirements table; resolve that documentation discrepancy before promising installation compatibility. Windows Sandbox is not a supported Home-edition route. Do not attempt an edition bypass or upgrade purchase.
4. Build the project runner only after verifying the chosen runtime. Candidate processes run non-root with no network, no credentials, no Docker socket, no host PID namespace, no devices, no added capabilities, no privilege escalation, a read-only root filesystem, bounded temporary storage, CPU/memory/PID/time/output limits, and cancellation that kills the owned execution unit. Copy only an explicit scrubbed fixture/source manifest, never mount the production repository or memory database. No automatic source promotion.
5. Verify denied network, denied host writes, credential absence, process/time/output limits, cleanup, cancellation, container restart behavior, and independent checks protected from candidate edits. Host-side controller rechecks hashes and never treats arbitrary candidate output as proof. Containers share a guest kernel and are not perfect hostile-code isolation; consider a dedicated disposable VM for broader or higher-risk execution.

## Boundary

This environment supplies execution capacity only; it contains no deployed JARVIS Core, identity, canonical memory or credentials. The existing Core generates candidates and owns requests. Artifact export is bounded, treated as untrusted, and reviewed. Production Windows/Electron-specific repair tests still need a suitable isolated Windows environment; Linux tests alone cannot prove Windows behavior.

## Current deliverable

Preflight and reviewable setup plan only. No WSL, Docker, Windows features, registry policies, firewall changes or new services installed. Prior 177-test baseline unchanged; no production code changed and no test suite rerun for this document-only step.

References checked today:
- https://learn.microsoft.com/en-us/windows/wsl/install
- https://docs.docker.com/desktop/setup/install/windows-install/
- https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/

Next user actions: enable firmware virtualization, then explicitly authorize the agreed WSL2/runtime installation. General arbitrary patch execution remains blocked until isolation acceptance passes.
