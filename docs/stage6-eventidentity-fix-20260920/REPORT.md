# EventIdentifier correction — final report



MONITOR_STILL_DEFECTIVE



Blocking failure: C: sustained hashing produced a 14.5649514-second interval between heartbeats 153 and 154. The threshold remains 10 seconds. Maximum sampled reader age was 8.3645728 seconds. Failure was first detected by offline reconciliation after all five workloads finished; no further campaign was run. workload-failure-analysis.json preserves the exact interval and surrounding trace. Adjacent traces localize 7.6266274 seconds between serialization end and append begin, followed by 6.1961153 seconds spanning append/persistence/removal. Those measurements do not establish whether underlying I/O, scheduling or another mechanism caused the delay.

Five-workload disposition: idle PASS; C: reads PASS; C: hashing FAIL (heartbeat); CPU-only PASS; D: hashing PASS. Per-phase reconciliation fields in raw evidence refer to event-pipeline completeness only, not full workload acceptance. Full five-workload gate FAIL.

## 1–6. Source, defect and mechanism

All changes are new files under C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\stage6-eventidentity-fix-20260920. One preparation script also exists at C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis\docs\prepare_eventidentity_fix.py. No original source was edited. Exact source paths and before/after SHA-256 values: source-before.json, source-final.json; source.diff records candidate changes. New files have no pre-change hash.

Old Drain used Remove-Event -EventIdentifier, deleting all queued siblings with a collided external number. Teardown had the same destructive risk. New event_queue.cs assigns monotonic bounded QueueSequence at enqueue under the concrete collection SyncRoot, keys by reference identity, and removes exactly one reference-matched index only after AppendAllText succeeds. External numbers and PIDs are never destructive keys. Single outstanding selection and atomic publishing guard reject competing consumers; unexpected disappearance fails closed. No queue lock spans disk I/O. See DESIGN.md for complete lock/write/failure/rollback semantics.

Sequence uniqueness is protected by the same lock for every producer; the 20,000-entry collector bound fails before integer overflow. Actual PSEventArgsCollection and live-session reference behavior were tested.



## 7–8. Collision tests and stress

queue-tests result: {"sessionReferenceProof": true, "status": "PASS", "concreteType": "System.Management.Automation.PSEventArgsCollection", "results": {"status": "PASS", "checks": 222, "groups": [{"name": "two_START", "status": "PASS", "events": 2}, {"name": "two_STOP", "status": "PASS", "events": 2}, {"name": "START_STOP", "status": "PASS", "events": 2}, {"name": "three", "status": "PASS", "events": 3}, {"name": "ten", "status": "PASS", "events": 10}, {"name": "head", "status": "PASS", "events": 4}, {"name": "middle", "status": "PASS", "events": 4}, {"name": "tail", "status": "PASS", "events": 4}, {"name": "consecutive", "status": "PASS", "events": 6}, {"name": "distinct_processes", "status": "PASS", "events": 3}, {"name": "failed_write_zero_removed_and_retry_refusal", "status": "PASS"}, {"name": "successful_retry_no_duplicate", "status": "PASS"}, {"name": "residue_and_foreign_consumer", "status": "PASS"}, {"name": "concurrent_high_volume", "status": "PASS", "generated": 10000, "enqueued": 10000, "selected": 10000, "persisted": 10000, "removed": 10000, "remaining": 0, "externalCollisions": 9993, "internalCollisions": 0, "duplicates": 0, "losses": 0, "siblingDeletions": 0, "concurrentEnqueues": 10000, "seconds": 2.8161255}]}}

The required collision cases are covered by the named C# groups and their FIFO/sibling/retry assertions; duplicate-PID rejection is additionally covered by focused test_event_rejection. The stress uses four concurrent producers, 10,000 events, seven repeating external IDs and one active consumer.



## 9–15. Real probes, regressions, workload/heartbeat/pipeline totals

Focused regression result: {"utc": "2026-09-20T00:16:33.114560+00:00", "command": ["outputs\\jarvis\\docs\\stage6-eventidentity-fix-20260920\\run_focused.py"], "python": "C:\\Users\\jonny\\Documents\\Codex\\2026-09-07\\cr\\outputs\\jarvis\\.venv\\Scripts\\python.exe", "modules": ["test_journal", "test_processes", "test_finalization", "test_extended_finalization", "test_probe_handles", "test_event_rejection"], "executed": 50, "failures": 0, "errors": 0, "skipped": 0, "seconds": 23.485000000015134, "passed": 50}

Real run results: {
  "smoke": {
    "run": "smoke",
    "status": "PASS",
    "errors": [],
    "probes": 4,
    "starts": 4,
    "stops": 4,
    "externalCollisions": 0,
    "internalCollisions": 0,
    "maxHeartbeatInterval": 1.0529352,
    "maxHeartbeatAge": 1.0066477,
    "queue": {
      "enqueued": 8,
      "selected": 8,
      "persisted": 8,
      "removed": 8,
      "remaining": 0,
      "maxDepth": 3,
      "failed": false,
      "failure": null,
      "identity": "reference + bounded monotonic enqueue sequence"
    },
    "phases": [
      {
        "phase": "idle",
        "expectedStarts": 4,
        "confirmedExits": 4,
        "startCallbacks": 4,
        "startEnqueued": 4,
        "startPersisted": 4,
        "stopCallbacks": 4,
        "stopEnqueued": 4,
        "stopPersisted": 4,
        "externalCollisions": 0,
        "internalCollisions": 0,
        "maxQueueDepth": 3,
        "maxHeartbeatAge": 1.0066477,
        "maxHeartbeatInterval": 1.0529352,
        "writeErrors": 0,
        "reconciliation": "PASS"
      }
    ],
    "independentObserver": "Separate WMI subscriber; same provider. Retained process handles independently establish exits."
  },
  "loads": {
    "run": "loads",
    "status": "FAIL",
    "errors": [
      "heartbeat interval"
    ],
    "probes": 279,
    "starts": 279,
    "stops": 279,
    "externalCollisions": 3,
    "internalCollisions": 0,
    "maxHeartbeatInterval": 14.5649514,
    "maxHeartbeatAge": 8.3645728,
    "queue": {
      "enqueued": 558,
      "selected": 558,
      "persisted": 558,
      "removed": 558,
      "remaining": 0,
      "maxDepth": 14,
      "failed": false,
      "failure": null,
      "identity": "reference + bounded monotonic enqueue sequence"
    },
    "phases": [
      {
        "phase": "idle",
        "expectedStarts": 29,
        "confirmedExits": 29,
        "startCallbacks": 29,
        "startEnqueued": 29,
        "startPersisted": 29,
        "stopCallbacks": 29,
        "stopEnqueued": 29,
        "stopPersisted": 29,
        "externalCollisions": 0,
        "internalCollisions": 0,
        "maxQueueDepth": 5,
        "maxHeartbeatAge": 1.0116731,
        "maxHeartbeatInterval": 1.024664,
        "writeErrors": 0,
        "reconciliation": "PASS"
      },
      {
        "phase": "disk",
        "expectedStarts": 53,
        "confirmedExits": 53,
        "startCallbacks": 53,
        "startEnqueued": 53,
        "startPersisted": 53,
        "stopCallbacks": 53,
        "stopEnqueued": 53,
        "stopPersisted": 53,
        "externalCollisions": 1,
        "internalCollisions": 0,
        "maxQueueDepth": 14,
        "maxHeartbeatAge": 7.6090698,
        "maxHeartbeatInterval": 8.4962453,
        "writeErrors": 0,
        "reconciliation": "PASS"
      },
      {
        "phase": "sustained",
        "expectedStarts": 71,
        "confirmedExits": 71,
        "startCallbacks": 71,
        "startEnqueued": 71,
        "startPersisted": 71,
        "stopCallbacks": 71,
        "stopEnqueued": 71,
        "stopPersisted": 71,
        "externalCollisions": 0,
        "internalCollisions": 0,
        "maxQueueDepth": 9,
        "maxHeartbeatAge": 8.3645728,
        "maxHeartbeatInterval": 14.5649514,
        "writeErrors": 0,
        "reconciliation": "PASS"
      },
      {
        "phase": "cpu",
        "expectedStarts": 39,
        "confirmedExits": 39,
        "startCallbacks": 39,
        "startEnqueued": 39,
        "startPersisted": 39,
        "stopCallbacks": 39,
        "stopEnqueued": 39,
        "stopPersisted": 39,
        "externalCollisions": 0,
        "internalCollisions": 0,
        "maxQueueDepth": 4,
        "maxHeartbeatAge": 1.0466454,
        "maxHeartbeatInterval": 1.0480613,
        "writeErrors": 0,
        "reconciliation": "PASS"
      },
      {
        "phase": "Dhash",
        "expectedStarts": 87,
        "confirmedExits": 87,
        "startCallbacks": 87,
        "startEnqueued": 87,
        "startPersisted": 87,
        "stopCallbacks": 87,
        "stopEnqueued": 87,
        "stopPersisted": 87,
        "externalCollisions": 2,
        "internalCollisions": 0,
        "maxQueueDepth": 5,
        "maxHeartbeatAge": 1.0314271,
        "maxHeartbeatInterval": 1.0493564,
        "writeErrors": 0,
        "reconciliation": "PASS"
      }
    ],
    "independentObserver": "Separate WMI subscriber; same provider. Retained process handles independently establish exits."
  },
  "dry1": {
    "status": "NOT RUN"
  },
  "dry2": {
    "status": "NOT RUN"
  }
}

START/STOP callback evidence comes from the instrumented subscriber; enqueue evidence is separately recorded. Parallel WMI observation shares the native provider and is not an independent kernel source. Retained handles/GetProcessTimes independently prove process exits; those exits are never synthesized into STOP records.



## 16–21. Failure injection, dry runs and durability

Additional failure checks: {"status": "NOT RUN"}. New test_queue_finalization.py and test_failure_campaigns.py were prepared but NOT RUN because phase 8 failed. They are not accepted validation evidence.

Earlier focused tests cover publisher/producer death, reader death/restart, malformed/partial heartbeat, ten-second stale rejection, identity changes, hashing-child death, finalizer death, final flush failure and archive corruption. Collision tests cover event-write denial, zero removals and retry refusal. Additional checks cover actual selected-queue consumer termination, residue, late queue failure, malformed events and ambiguous identity.

Dry1: NOT RUN; Dry2: NOT RUN. Full failure-injection phase NOT RUN. Monitor heartbeat final flush completed, but workload evidence acceptance/finalization was not attempted after reconciliation failed. Passing focused fsync tests do not make this failed workload accepted. Top-level preservation archive verification is recorded separately in archive-verification.json; it archives failure, not a successful dry run.



## 22–27. Limits, preservation and disposition

Historical PID 13248 / 22544 / 21896 individual causes remain UNPROVEN. Historical timing delays remain unexplained. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

EventIdentifier collisions were subsequently proven to cause deterministic queue-event loss and the defect was corrected. This does not attribute the original three losses or prove all timing mechanisms reliable.

Prior validation evidence preservation: 1185 files checked; 0 changed. No protected VM/configuration paths were opened. No VirtualBox launch, production change, credential access or protected hashing was performed.

Protected-baseline eligibility: NOT ELIGIBLE

Rollback: stop using this new validation candidate. Preserve all candidate/old evidence. Do not restore any VM or production file. The original monitor remains known-defective.

Final status: MONITOR_STILL_DEFECTIVE

## Cleanup and next action
cleanup.json verifies zero matching live recorded identities, zero access-denied identity checks, and confirmed exits for the recorded probes, monitor and workload processes. host-state-final.json records zero VBox/VirtualBox/J6Probe processes and VBoxSDS stopped. No process termination was needed for campaign cleanup.

Next proposed action is a separately reviewed diagnosis of the 14.5649514-second heartbeat interval and the collector polling gaps. Do not raise the threshold, retry away this failure, execute either dry run, or hash protected files. Prepared phase-9 tests remain NOT RUN.

