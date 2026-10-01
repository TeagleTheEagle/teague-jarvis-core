# Proposed boundary — design and focused sacrificial validation only

The 116-file collector candidate and all historical evidence remain immutable. New prototypes run only under a fresh D:\JARVIS-STAGE6-LIVE directory. No large dataset, protected files, VirtualBox, production operation, security policy, threshold or deadline change is permitted.

## Identity

Retain the composite `(run/boot scope, PID, kernel CreateTime, kernel ProcessSequenceNumber)` and exact parent sequence. Corroborate CreateTime and exit with a retained Windows process handle and native owned-child PE evidence. A handle anchors the process object after exit; its numeric value is not a global identifier. A late OpenProcess lookup must match creation time before being used. It must never be used to assign a delayed notification merely because its PID matches.

Supported ETW extended process-start keys are a candidate supplemental field, not a replacement for subject identity. A kernel event's header can refer to the emitting thread/process, while its payload describes a different subject process. No assumption that the extended key equals payload ProcessSequenceNumber or names the subject is allowed without a controlled measurement. The existing schema already supplies subject CreateTime and sequence on start/exit. SystemBasicProcessInformation is documented only on sufficiently recent Windows and does not reconstruct already-exited processes; do not introduce private NT API information classes or assume sequence fields share namespaces.

CIM Win32_ProcessStartTrace/StopTrace lacks CreateTime/process sequence. Joining to a kernel stream cannot create that missing discriminator when multiple incarnations satisfy constraints. Preserve AMBIGUOUS/UNMATCHED. Historical classification remains 0/21/1. Future mandatory independent CIM-to-instance proof therefore remains an integration blocker unless a supported discriminator is actually captured. A second ETW subscription is independent transport, not independent underlying event generation; it must not silently replace independent CIM evidence.

## Streaming design

Every acceptance-critical record must enter an authoritative sequenced stream **before** any optional bounded view. Preserve all existing channels: kernel lifecycle, native entry/exit, retained handles, CIM source callbacks, exact queue enqueue/persist/remove receipts, heartbeat, health, required sampler closure, hash/metadata/finalization outcomes, and currently required startup forensics. No provider/category is removed.

For each stream: bounded ingestion queue; dedicated D: writer; 8 MiB CREATE_NEW segments; SHA-256; first/last sequence and count per segment; finite record/byte/segment budgets; final manifest; source/ETW loss counters checked separately. Sequence is assigned under the same ingestion lock as admission. Record an attempted admission count and a sticky fault when a producer cannot be accepted. Equal accepted/persisted counts alone cannot excuse lost admissions. No destructive rotation. Preserve incomplete segments and failure manifests; never seal an incomplete run as successful.

A 20,000-row query view is permitted only downstream of authoritative admission, with explicit truncation count. The current EventTap is **not** such a view: it supplies required callback/enqueue evidence, discards new rows after 20,000 and causes a fatal overflow. The frozen checker still depends on it. A prototype demonstration does not migrate that checker or satisfy actual decoupling acceptance.

All source categories retain their current acceptance/forensic role. Detailed file/registry/scheduler evidence remains required for the current startup diagnosis. Resource summaries can be labelled secondary only where their absence is already explicitly permitted; observer/sampler termination evidence remains mandatory. No filtering is proposed.

Backpressure: writer drains asynchronously; producers never block on disk under the queue lock. Finite queue exhaustion, oversized record, quota exhaustion, writer/hash/flush/create failure, sequence gap/duplicate, missing segment or nonzero upstream loss sets sticky failure. Do not silently sample required records. A slow I/O cannot be made bounded merely by increasing queue memory; existing observer shutdown bounds remain required, and stuck cleanup blocks acceptance.

## Focused prototype boundary

1. Copy only the reviewed TraceSink source into a fresh disposable D: prototype. Add authoritative sequence, attempted-admission count, segment first/last sequence, explicit totals, byte/record queue metrics and controlled test-only fault injection. Do not edit the frozen sink.
2. Test generated metadata payloads at >=97,212 records/sec through multiple segments. These are **capacity records, not process evidence**. Demonstrate >20,000 authoritative records while a separate view remains bounded/truncated. Test disk/write/hash/create errors, backpressure and tampering; no full-disk allocation.
3. Validate retained handles with harmless fixed native probes, concurrent identical images and after-exit queries. Use actual creation/exit times; do not claim PID reuse occurred if Windows did not reuse a PID. Synthetic event reorder/reuse tests remain distinctly labelled.
4. Reinspect existing kernel/native/handle evidence using exact keys and original notification ambiguity. A fresh elevated integrated run is not equivalent to source-independent identity proof and is gated on a justified integration rather than changing the evidence rule to obtain a pass.

The complete future reserve must include all channels plus archive and finalization. New quotas may be proposed and validated as a finite contract, but are not considered enforced by this standalone sink. Historical medium rates and observed burst envelopes inform sizing; peak sustained over the entire run is not claimed as measured behavior. Record actual record sizes, sustained/burst models, storage/queue performance and remaining uncertainty.
