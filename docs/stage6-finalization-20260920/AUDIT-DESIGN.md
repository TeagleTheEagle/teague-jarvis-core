# F1 audit and F2/F3 design — before implementation

Audited source: `D:\JARVIS-STAGE6-LIVE\90e9469000dd4530a86b98fad67d7089\code`. Immutable hashes: audit-source-hashes.json.

Previous order: collect.py launches one probe at a time, waits five seconds with retained Popen handle, writes successful probe rows. In finally it stops the workload and writes collector-finished.json, then closes its heartbeat Reader. It waits for the monitor exit before finishing independent probe observations and writing retained-handle-verification.json. Thus the monitor completion marker precedes final retained-handle proof.

monitor.ps1 RUNNING loop drains ExactEventQueue, serializes each event, calls PersistAndRemove, publishes heartbeat and checks collector-finished. After that marker it sleeps two seconds, drains once, enumerates VirtualBox processes, calls Reconcile, durably flushes heartbeat, closes it and writes monitor-result. Subscriptions are removed only in finally, after these operations. EventTap remains attached until teardown. ExactEventQueue locks identity selection/persistence/removal correctly; it does not prohibit a new enqueue between the final drain and Reconcile. The recorded STOP arrived in that interval. This race is distinct from EventIdentifier collisions.

Manifests/archive are separate post-monitor tools. They must require successful exit/receipt, complete expected lifecycle counts, source preservation and durable verification. A failed monitor may be archived only as failed evidence, never accepted evidence.

F2 measured 854 preserved sacrificial probes across idle, C reads, C hash, CPU and D hash. Primary callback and enqueue maxima are approximately 3.007 s. Quiet bound = ceil_0.1(max + max(1 second, 0.5*max)) = 4.6 s. This is not a universal latency guarantee. Known identities and expected event counts—not quiet time alone—prevent acceptance with a missing notification.

New order:
1. Collector permanently exits its production loop: PRODUCERS_CLOSED.
2. WAITING_FOR_PROCESS_EXITS: stop workload; retain and verify every tracked probe handle, creation identity, signaled state and actual exit code. Publish expected identities/proof tied to this monitor nonce before collector-finished. No STOP records are synthesized.
3. Monitor continues real subscription, queue persistence and heartbeat publication. EVENT_QUIESCENCE starts only with producer proof, exited handles, empty queue and no active consumer. Any enqueue changes activity generation and resets quiet time. Missing or duplicate expected records prevent closure regardless of quiet time.
4. Within a 45-second closure budget (inside existing 60-second collector wait), require healthy subscriber/heartbeat, expected identity completeness, full quiet interval, empty queue and no active consumer. No deadline reset when events arrive.
5. FINAL_DRAIN / subscription close / post-close drain: keep exact queue handler attached; unregister real subscribers; drain residual entries. An event arriving at/after the closed boundary latches failure. All expected START/STOP pairs must already be complete before close; additional lifecycle events cannot be silently ignored.
6. Durable flush of heartbeat AND event file; reconciliation, receipt and SEALED state. Failure at any step invalidates acceptance. Keep failure/pending trace evidence. Final collector confirms monitor exit zero; archive checks source/receipt separately.

A finite quiet interval cannot guarantee no Windows callback ever arrives in the future. The complete expected-identity barrier is independently mandatory. Any post-boundary callback observed while teardown is finishing fails closed. No host-wide reliability or protection after monitoring ends is claimed.

Implementation scope: new diagnostic copy of monitor.ps1 and collect.py, a bounded finalization state-machine helper and focused tests, acceptance/evidence wiring. event_queue.cs, EventIdentifier semantics, journal stale limit, five-second probe wait and production sources remain unchanged. Native-control helpers are not promoted to replace the existing whoami acceptance probe.

Validation: deterministic virtual-clock injections exercise real state-machine methods with the unchanged ExactEventQueue for persistence; actual Windows probes still required for workloads, clustered exits and dry runs. Existing 69-test monitor suite and 222-check queue/10k stress rerun. Any probe timeout remains a failed workload and disqualifies dry runs/monitor acceptance; no timeout increase.
