# Narrow tracker correction — implementation design review

STATUS: DESIGN READY FOR BOUNDED TEST IMPLEMENTATION. No implementation authorized by this review itself; no candidate/checker edits or live tests performed.

## Verified insertion points

Inspected candidate: `D:\JARVIS-STAGE6-LIVE\693f0cd17ff4419aaf404604a23edc5f\code`.

The actual path is `small_launch.ps1` -> native `RunCollector` -> `traced_collect.py` -> **`large_collect.main`**. `baseline_collect.py` is not the selected collector entry for this run.

- `large_collect.py:11` constructs `TreeTracker()` before the collection try/finally. Sampler and worker are launched at lines 21–22; probes subsequently register with the tracker.
- `evidence_support.py:80` starts the scan thread during construction.
- `evidence_support.py:82` (`add`) captures creation identity and calls the handle-image API, but lacks query begin/end and surrounding live-state records.
- `evidence_support.py:95` (`scan`) discovers only children of existing tracked rows. The collector is absent, so its own console helper is outside that discovery set.
- `evidence_support.py:139` (`finish`) waits for every tracked row to exit before closing handles. Adding the collector as an ordinary row would make it wait for its own exit. That is not an acceptable correction.

The exact inspected source hashes are recorded separately in this review package. The previous failed run remains failed.

## Proposed implementation: two TEST modules, supporting evidence only

### 1. Separate discovery anchor

Add an opt-in collector-root anchor to TreeTracker. Existing callers keep their existing behavior by default. `large_collect.main` opts in at construction, before launching the sampler, hash worker or probes.

Initialize the anchor before starting the scan thread. Duplicate the current-process handle with only query-limited-information/synchronize access, record handle-derived PID, creation FILETIME, full image and capture timings, and bind it to the collector's recorded/native identity during offline review. A numeric PID or process name alone must never establish the anchor.

Keep the anchor separate from descendant `rows` and their `allExited` calculations. It is a discovery scope, not an exited-process claim. Its evidence must explicitly state that the collector is still alive when it closes its self-held handle. Existing launcher-owned native/retained-handle evidence continues to prove the collector's later actual exit. Do not fabricate an anchor exit or mark it as successfully exited.

Use the anchor only as an additional exact parent-instance candidate when discovering descendants. Keep existing retained-parent lifetime checks and reject multiple matching parent instances. Discovery remains provisional; authoritative kernel sequence/parent-sequence reconciliation is still mandatory before any future qualification.

Construction failure must close the newly duplicated anchor handle and start no scan thread. Cleanup stops/joins the scan thread before closing its anchor handle. Descendants must still satisfy the original exit/handle-closure conditions and bounds. Failure to join or close fails the supporting-evidence test. Never introduce a wait for the collector's own exit inside that collector.

### 2. Complete live-image capture record

In `TreeTracker.add`, record monotonic acquisition/query timing, handle-derived PID and creation identity, query return/error and exact image, plus nonblocking retained-handle state before and after the image query. Preserve the existing handle even when metadata capture fails so exit/cleanup evidence is not discarded.

A supporting capture is valid only if the queried handle identifies the same process instance, the image succeeds, the query interval is valid, both surrounding observations establish a live process, and later authoritative evidence places the query strictly inside that instance's lifetime. Record failures explicitly. Do not convert unknown values or errors into success, and do not replace a missing image with Toolhelp/ETW names.

Record anchor evidence separately from descendants in a new versioned supporting artifact, leaving the existing `tree-handles.json` meaning intact. Use fresh run paths and exclusive durable finalization. Bound new storage with an explicit capacity; overflow fails closed. Do not change scan cadence, deadlines, heartbeat limits, capture providers, queues or privileges.

### 3. No checker admission yet

The current `small_check.py`/`small_coverage.py` remain frozen. This experiment does not admit tracker images as a replacement for their required tracer source. Even a successful supporting experiment cannot retroactively pass the failed run.

After this path is demonstrated, any versioned checker integration must explicitly review source provenance, exact creation/parent binding, contradiction handling and complete evidence predicates. It must not relabel an independent tracker record as an authority-tracer query. The existing error-87 post-exit exception is unchanged.

## Focused validation before any integrated rerun

1. Default TreeTracker behavior remains unchanged when no anchor is requested.
2. Opt-in anchor is valid before scanning/workload admission; construction failure closes handles and starts no thread.
3. A directly collector-owned sacrificial child/helper becomes discoverable; a worker-owned descendant remains discoverable.
4. The anchor remains alive during tracker shutdown without being counted as an exited descendant. External parent evidence independently verifies its eventual exit.
5. Successful image capture has complete identity, live-state and timing evidence.
6. Failed image query, post-exit query, mismatched PID/creation, reused parent, ambiguous parent, partial timing and contradictory kernel/native data remain rejected.
7. Missing short-lived helper stays missing; no retry or invented fallback.
8. Descendant cleanup, thread join, anchor handle close and output finalization failures all fail closed.
9. Storage overflow, duplicate records and stale-run reuse are rejected.
10. Run focused existing tracker/cleanup regressions and compare original source hashes. Tiny sacrificial data only, no large or protected data.

These are proposed tests, NOT executed results. An initial experiment should collect supporting evidence only and stop before a new integrated acceptance attempt.

## Limits and decision

This closes a demonstrated discovery-scope gap and makes independent capture timing auditable. It cannot guarantee catching every short-lived helper: the collector must reach tracker setup, and polling can miss processes that exit sooner. The 28 ms historical helper therefore remains a meaningful stress case, not something to remove or delay artificially.

No ETW setting adjustment, process suspension, helper lifetime extension, new elevated service/driver, authority broadening, production change or schema change is proposed. If satisfying the contract requires any of those, stop for separate review.

Implementation files: separate TEST copies of `evidence_support.py`, `large_collect.py`, and new focused tests/supporting-artifact verification. `traced_collect.py`, native launcher, authority tracer and frozen acceptance checker need no changes for this first experiment.

Rollback: discard selection of the new candidate, retain its evidence; existing frozen candidate remains unchanged. No production rollback required.

NEXT ACTION: Implement this two-module supporting-evidence experiment in a separate TEST candidate and run its focused sacrificial tests, once explicitly approved. No further design review is needed for that exact bounded scope unless implementation exposes a new boundary.

Historical tracing/delay causes remain UNCONFIRMED. Historical 21 AMBIGUOUS / 1 UNMATCHED unchanged. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
