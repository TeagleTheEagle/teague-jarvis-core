# Rootless repair runtime — 11 September 2026

Status: installation and trusted smoke probes PASSED. General repair-runner acceptance is NOT complete.

User explicitly approved installing Podman and required dependencies inside Ubuntu WSL2 and creating non-administrator Linux account `jarvis-repair`.

Installed from existing signed Ubuntu repositories after apt-get update: podman, uidmap, fuse-overlayfs, dbus-user-session and package-manager dependencies. Podman reports 4.9.3. No repository changes. Created Linux-only jarvis-repair UID/GID 1000 with a home directory, locked password and only its own group; no sudo membership. Standard subordinate UID/GID mappings: 100000:65536. No existing account permissions changed.

Ubuntu package installation enabled Podman service/socket/maintenance units. Disabled and stopped these new units for on-demand testing. Final checks: podman.socket, podman.service and podman-auto-update.timer inactive and disabled. No Windows firewall/security changes or JARVIS service modifications.

## Verified evidence

- `podman info` executed as jarvis-repair: rootless=true, cgroups v2 with cpu/memory/pids controllers, seccomp enabled. API socket absent. AppArmor and SELinux reported unavailable; neither was disabled by this task.
- Downloaded official docker.io/library/alpine:3.22 for trusted probes only. Runs used immutable local image ID `b66e0ce64844f5c6435b0c4bfd965558199ab0f53270846861c979cb1ac29365` and --pull=never.
- Container flags: --network=none --read-only --read-only-tmpfs=false --cap-drop=ALL --security-opt=no-new-privileges --user=65534:65534 --pids-limit=32 --memory=128m --memory-swap=128m --cpus=0.5 --log-driver=none --timeout=15 --rm. No volumes, host directories or credentials supplied.
- Trusted shell probe exit 0: UID/GID 65534; memory.max=134217728, memory.swap.max=0, pids.max=32, cpu.max=50000 100000. CapEff=0, NoNewPrivs=1, Seccomp=2. No network routes. /mnt/c and root/user Podman sockets absent. Attempt to touch /tmp/write-probe denied.
- Separate sleep-30 probe with --timeout=2 terminated in approximately 3.94 seconds including command overhead, exit 1. Final podman ps -a empty: no leftover containers. This proves timeout cleanup for that probe, not all cancellation/race cases.
- Existing targeted experiment tests passed immediately before installation: 9 tests in 0.166 seconds. No application code changed. Full Python/desktop regressions and live voice were not rerun for this infrastructure-only installation.

## Scope and remaining gates

ONE JARVIS unchanged. No App/Core, provider, canonical memory or voice service installed in Linux. Podman's own SQLite metadata is container bookkeeping, not JARVIS memory. Package/image caches remain inside Ubuntu; this report contains no secrets.

WSL itself still has Windows drive access. Container restrictions must be mandatory on every future run. The account alone is not the isolation boundary. Rootless containers share the WSL kernel and do not constitute perfect hostile-code isolation.

Before executing general generated patches: implement a fail-closed controller, bounded manifest/input/output handling, explicit environment filtering, protected independent test evaluation, owned-container cancellation, failure cleanup and negative security tests. Verify actual network-connect denial, memory/process exhaustion behavior, stop controls and restart behavior. Preserve mandatory review before any production deployment. No autonomous self-repair or automatic promotion has been enabled. Linux probes cannot establish Windows/Electron repair correctness.

References consulted for selection: https://podman.io/docs/installation and https://docs.podman.io/en/stable/markdown/podman.1.html . Installed-version behavior was checked locally; smoke-probe results above are measured evidence.
