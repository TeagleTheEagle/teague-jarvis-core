# Bounded TEST IPC guard — review package

Status: approved guard correction automated validation PASS. Overall Stage4
acceptance remains INCOMPLETE; production activation BLOCKED; no acceptance commit
and no Stage5. This report does not certify physical voice/media or remaining
broader Stage4 coverage.

## Cleanup

Approved Core26784 was reverified against creation134335979170821093, executable
SHA256 and exact TEST namespace/command line on a held process handle. Authenticated
shutdown remained unavailable in recovery. TerminateProcess was used only on that
verified Core. Launcher24164 exited naturally. No launcher or unrelated process
was force-terminated. Retained controller subsequently exited. Existing evidence
hashes were unchanged. Evidence: ipc-guard-approved-cleanup.json.

## Exact change

Source files changed in this continuation:
- tests/lifecycle_stage1/harness.py
- tests/lifecycle_stage1/test_stage1.py (four additional cases; existing cases retained)
- tests/lifecycle_stage4/challenge_diagnostic.py
- tests/lifecycle_stage4/electron_challenge_diagnostic.py
Plus this report, Stage4 report link, scoped source snapshots and nonsecret evidence.
No production runtime module, authentication, launchers, Store or data changed.

A Windows CreateMutexW/WaitForSingleObject/ReleaseMutex guard named
Global\TEAGUE-TEST-IPC-<SHA256 of case-folded absolute validated TEST directory>
coordinates BOTH challenge.json and response.json. The files share one short
critical-section mutex; other files retain their existing behavior. Stable naming
across processes/sessions does not rely on file existence. Default Windows DACL
and non-inheritable handle are used; no ACL/security changes. Same-user cooperative
TEST processes are the security assumption, not an independently authenticated
mutex. Wrong-object/access failures are denied, never treated as identity proof.

Target attribute validation, temporary JSON write and replacement happen inside
the guard. Readers hold it through file close and JSON decoding. Temp names remain
unique. No failed publication retry or opportunistic file deletion was added.
Lifetime locks, coordinator logic, PID/creation-time checks and the prior
once-per-successfully-answered response logic are AST-identical to the before copy.

## Deadlock, deadlines, cleanup and failure semantics

No helper nests another guard or waits for another process while holding it.
The guard is released before response polling or lifetime-lock probing. No inverse
lock dependency was introduced. WaitForSingleObject waits at most250ms, limited
further by the remaining reconciliation deadline. The 1-second reconciliation
clock now starts before challenge publication, so guard waiting consumes its budget.
Timeout, abandonment, failed wait/creation/release raises IPCGuardError and is not
swallowed as missing JSON; identity cannot be accepted on that failure. Acquired
abandoned ownership is released before reporting failure. No automatic recovery
clearance or replacement Core authorization is added. Normal exit closes handles;
Windows releases an owning thread's mutex on exit. The abandonment test uses actual
Windows thread termination semantics; other-session coverage remains unperformed.

A bounded mutex wait does NOT impose a hard deadline on a hung filesystem/kernel
call. Uncooperative external readers/filters do not participate in the mutex and
can still cause fail-closed errors. Named-object interference can deny availability,
not grant Core authority. Production use/security hardening remains separately gated.

## Retained failures and change made in response

Initial new negative-path test setup produced two unittest errors (missing marker
exception expectation and invalid directory inspected by teardown). The original
20 Stage1 cases passed. Failed run TEST-b85fa... retained; only the new test setup
was corrected. No Stage1 behavior was weakened for that test.

First guarded file run TEST-IPC-GUARD-a969... still had2/10 fast-reader failures.
Inspection found target GetFileAttributesW outside mutex coordination. That query
was moved inside the same guard. This is a coverage correction, not a retry. Its
causal role is supported by source inspection and the following comparison, not
by a captured kernel handle trace. Transitional regression outputs are retained
with ipc-guard-* names; only ipc-final-* and the final source hash count below.

## Final validation

Final harness SHA256:
b1b1d0054594ea0098158dd835ba62b587a486469e2c93bd5684f968c33b2203

File-only: 240 trials,24,120 successful publications,0 publication failures and
0 reader errors. Each of challenge/response received20 trials per condition:
no reader,15ms reader,fast reader,held Python reader,held delete-sharing reader,
and reader closed. Unique challenges; no retry after failed attempt. Original
unguarded challenge experiment was72 failed trials/120; first partial guard failed
2/60; all remain evidence. Different targets and amplified timing mean these are
controlled comparisons, not a production failure-rate estimate.

Actual Electron diagnostic:100 reconciliations each with no Electron, Teague only,
Intelligence only,both,reopened Teague,and crashed Intelligence renderer:600/600;
no background FAILED_CLOSED events. A background fault now stops the diagnostic
condition immediately rather than relying only on reconcile's return value.
Actual existing Electron probe:29 checks PASS including shared identity/state,
ownership denial,close/reopen/crash isolation and authorized shutdown.

Real synthetic App: normal29,emergency32,deadline36 checks PASS. Measured shutdown
recovery30.094seconds; ownership retained until supported owner re-evaluation and
exit. Expected injected failure cleanup PASS. All six resulting TEST Cores verified
exited and lifetime locks released. This uses deterministic silent TEST audio;
no microphone or browser-TTS fallback was enabled.

Regression totals:
- Stage1:23 PASS,1 existing cross-session SKIP (24 total).
- Stage2:35 PASS,1 existing other-user/cross-session SKIP (36 total).
- Stage3:43 PASS.
- Stage4 ownership/drain model:27 PASS.
- Prior response-correction comparison:50 trials,0 failures.
- Native peer bridge:15 PASS; authenticated bootstrap:6 PASS.
- Existing Python:212 PASS; desktop:19 PASS; Intelligence:3 PASS.
- Python compile validation:4 changed source/test files PASS; JS syntax:5 TEST
  client-related files PASS.

## Evidence distinctions

A: original historical Stage1 PermissionError root cause remains UNCONFIRMED.
B: previous repeated-response publication defect/correction remains separate and
unchanged; suppressing duplicates alone never guaranteed fresh replacements safe.
C: current challenge/response replace/read contention is experimentally reproduced;
final coordination eliminates it in the tested cooperative conditions.
The old Windows memory-read crash remains separate historical context; no evidence
establishes a common mechanism.

## Rollback

ipc-guard-before contains byte-for-byte snapshots and hashes taken before edits.
Restore only these four changed source files from that snapshot, or reverse only
this guard delta if later unrelated edits exist. Retain all evidence. Never reset
other dirty files, move data, remove ownership files, change ACLs or restart production.
A rollback reinstates the known file-contention risk and leaves activation blocked.

## Remaining review

This is evidence for the bounded IPC correction, not a production reliability
proof. Cross-session, adversarial named-object/ACL cases, filesystem-filter behavior
and physical media remain limitations. Broader Stage4 worker/inspection/repair
cleanup,approval/stream/upload coverage and human lifecycle controls remain as
listed in the master Stage4 report; they are not silently certified by these tests.
STOP FOR REVIEW. No production activation, installer, autonomy, repair deployment,
OllamaPhase2 or Stage5.
