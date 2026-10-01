# WSL installation — 11 September 2026

User explicitly approved WSL2 and required Windows components. Firmware virtualization was previously verified enabled.

First non-UAC installation attempt returned the WSL-not-installed message. Then launched the Microsoft system wsl.exe with administrator elevation, arguments `--install --no-distribution`. Installer exited 0. `wsl --version` now reports WSL 2.7.13.0 and kernel 6.18.33.2-2. Default WSL version is 2. No Linux distribution was installed.

Windows Component Based Servicing reports RebootPending. HypervisorPresent remains false; `wsl --status` says WSL2 cannot start and refers to Virtual Machine Platform/firmware virtualization. Consequently installation of the WSL package is verified, but functional WSL2 operation and feature activation are NOT yet verified. Next: user saves work and restarts voluntarily, then recheck firmware virtualization, hypervisor, optional-feature state and WSL status. Do not treat successful installer exit as proof of an operational sandbox.

No automatic restart, Docker install, firewall changes, production JARVIS code change, second Core or general generated-code execution. WSL is infrastructure for a future restricted test environment, not itself the completed repair sandbox.

## Post-restart verification — PASSED

After the user's restart, virtualization and the Windows hypervisor were verified active and no CBS restart was pending. `wsl --install -d Ubuntu-24.04 --no-launch` completed successfully. A subsequent verification was blocked by Codex automatic approval review reporting a usage limit; that blocked check provided no boot evidence.

After usage access was restored, the following commands completed successfully (combined process exit 0):

```powershell
wsl --list --verbose
wsl -d Ubuntu-24.04 --exec /usr/bin/uname -r
```

The listing showed `Ubuntu-24.04`, initially `Stopped`, with VERSION `2`. The kernel query then booted the distribution and returned `6.18.33.2-microsoft-standard-WSL2`. This verifies an operational WSL2 Linux environment. The initial Stopped state is normal before the boot query.

No production JARVIS source, memory, provider, voice or Core services were modified by this verification. No second JARVIS was launched. Only this installation record was updated. Regression tests were not run because no application code changed.

The restricted repair runner is still pending: WSL boot success does not establish network isolation, host-file isolation, resource limits or safe execution of generated code. No autonomous repair or deployment has been enabled.
