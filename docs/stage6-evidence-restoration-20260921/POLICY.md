# Stage 6 evidence immutability policy

Use this directory's `host_preflight.ps1` for future host snapshots. Its mandatory run ID selects a fresh directory under this tool's `final` directory. It never accepts a historical output path. FileMode.CreateNew reserves the output before any query. An existing path fails explicitly without truncating or deleting anything.

Python final JSON, reports, incident copies and receipts use `evidence_io.create_bytes`, `create_json` or `create_report`, backed by atomic `open(..., 'xb')`. Create run directories with an explicit unique run ID and `exist_ok=False`. A collision is a failure, not a reason to delete or auto-renumber. Preserve failed/partial files; a later operation needs its own explicit run ID.

`runtime/` is the only location supported by this helper for intentional mutable state. Final evidence never uses that API. The existing monitor's health/control/state files are intentional runtime state; their acceptance snapshots are separate. No monitor directory restructuring or runtime behavior change was made here.

Historical scripts are immutable evidence, not approved reusable launchers. In particular, do not execute the prior `stage6-instance-stream-design-20260921/final_host.ps1`, report generator, measurement/reconciliation scripts or old capacity/probe drivers against their original directories. Their vulnerable operations are enumerated in output-audit.json. They remain unchanged to preserve source/evidence provenance. Port any future required operation into a fresh run and use the exclusive helper before reauthorization/execution; this pass does not authorize those workloads.

The restoration script has one documented exception: fixed-path restoration of the single authorized final-host-state.json. It requires the exact overwritten hash, independently verified archives, exclusive preservation copies and a recorded intent before opening that fixed target r+b. It refuses replay once the original hash is restored. It is not a general output function.

Guarantee is limited to the tested new preflight/report entry points. This does not change NTFS permissions or prevent an arbitrary program, owner edit, historical script invocation or malicious path-ancestor replacement from modifying files. ACL/security changes are outside scope. No global project-wide immutability claim is made.
