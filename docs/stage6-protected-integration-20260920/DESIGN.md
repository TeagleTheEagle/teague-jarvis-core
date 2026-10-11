# Protected-baseline collector integration — synthetic validation only

The 73 frozen source files are preserved in the original D: workspace and both historical archives. The new candidate is an independent file copy; old sacrificial behavior and its entry points remain byte-identical.

## Audit

- `dry_contract.source_for/prepare`: miniature/dry1 fixed synthetic roots; fixture-specific restriction.
- `dry_contract.inventory`: exactly 12 regular `.bin` files; fixture-specific restriction. Reparse rejection and source metadata checks remain safety invariants.
- `dry_contract.validate`: fixed warning5/probe13.6/observer15/heartbeat10/campaign90. Probe, heartbeat and identity semantics remain unchanged; 90 seconds is the existing fixture campaign bound, not measured suitability for a protected-size dataset.
- `dry_collect.main`: actual 90-second admission deadline; worker plus independent process probes and retained tree cleanup.
- `app_monitor.ps1` and `kernel_trace.cpp`: separate fixed 180-second observer bounds. Both must be accounted for in duration derivation.
- `dry_hash_worker.snapshot/main`: complete two-pass SHA-256 reads, pre/during/post metadata checks. `dry_finalize` creates the manifest/archive only after dual-evidence closure.

## Separate mode

New `baseline_*` entry points use explicit `protected_baseline` mode, caller-supplied root matched to a campaign allowlist, recursive deterministic inventory and arbitrary file extensions. For this pass only D: synthetic roots are admitted; real VM/config paths are rejected lexically before any filesystem operation. Real protected-root enrollment remains a separate owner-reviewed activation of the collector, not implicit authorization from its name.

Read source files using binary read-only handles; verify the opened handle's final path, volume/file identity and metadata before reading. Reject reparse paths, traversal, duplicate case-folded paths, hard links and output/source overlap. Inventory is repeated; hash passes must match. A worker audit hook additionally rejects accidental Python mutations outside its D: output directory and process launching. This is defense against accidental collector operations, not an OS security sandbox against malicious native code. No ACL, VirtualBox API or protected-file operation is introduced.

All evidence stays on D: until live collection closes. Existing queue, probe, retained-handle, qualified-post-exit and finalization rules are reused. New mode adapters are separate files; existing modules are not silently broadened.

## Duration evidence

Create 59,665,402,098 bytes of fresh synthetic data, including 32GiB/16GiB/7GiB files and mixed nested metadata-sized files; no VM data is copied. Initial calibration separately measures two full logical read/hash passes. Expected two-pass time = twice the slower observed full pass; campaign = rounded-up 30-second units of twice that estimate plus 30 seconds; monitor = campaign plus 120 seconds. Proposed limits are synthetic-only, finite and capped; if cap is insufficient, stop for review. Long-run target is at least 1.5 times the estimated capture duration, with any extra observation time explicitly excluded from throughput. This is an initial derivation that must then survive monitored large-data runs; it is not a guarantee of C: throughput or uncached disk performance.

## One-UAC feasibility review

The current architecture does not support gate-wide reuse without changing run semantics. Native tracing authenticates one root PID/creation tuple and writes one run directory; retained observer checks bind both observers to that run; finalization requires both to exit. Two independent protected-mode dry runs also require fresh state. A persistent elevated service or command broker would introduce a new boundary. Per the owner's explicit fallback instruction, retain existing per-run UAC prompts. No privilege/policy changes, persistent helper, arbitrary-command interface or elevated Codex session will be introduced.

## Failure policy

Expected focused failure injections must reject acceptance. Preserve unexpected failures, source before/after hashes and process evidence. A failed full protected-mode Dry Run #1 stops the campaign and prevents #2. Never retry or raise a deadline to hide a failed acceptance run. Real protected hashing is prohibited throughout this integration pass.
