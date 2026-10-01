# Stage 4 challenge publication diagnosis — review gate

Diagnosis only. No Core was launched. Disposable file reader processes used the
unchanged Stage 1 write/read functions. No credentials, App, Store, providers,
lifecycle/authentication modifications, forced termination or production access.

## Cause / evidence

120 disposable trials across three preserved runs. Each attempted replacement used
a NEW unique challenge; failure ends the trial without retry. Loop timing (1ms
between writes, up to 200 writes) deliberately amplifies overlap and is not an
estimate of production failure frequency. Normal readers poll every 15ms; faster
readers yield with sleep(0); held readers retain an open handle for 40ms. No files
are removed. Reader stop is signalled only AFTER the publication attempt. All
reader children exited normally with code 0. The writer is the diagnostic process;
its PID/creation time and each reader PID/creation time are in writer-events.json.
Final repeated run additionally records executable identity and a source snapshot.
The two exploratory runs predate that snapshot and retain their own full events.

| Reader condition | Failed trials / trials | Successful publications |
|---|---:|---:|
| No reader | 0/20 | 4000 |
| 15ms polling | 12/20 | 2243 |
| Fast polling | 20/20 | 18 |
| Open Python reader held 40ms | 20/20 | 0 |
| Native reader, share read/write/delete, held 40ms | 20/20 | 0 |
| Reader closed and exited before fresh attempt | 0/20 | 20 |

All 72 failures capture complete Python traceback, errno 13, WinError 5, unique
source temporary path, destination challenge.json and monotonic attempt times.
Every traceback locates the failure in tests/lifecycle_stage1/harness.py:83,
os.replace(temporary,path). Temporary write_text completed first. Existing source
bytes stayed SHA256 4bce741b09ff94edc11c57c65fcc9fa3cb85e6a623758a262797acf21ba59856.

## Exact experimental failure mechanism and limits

A reader holds the current destination open; writer finishes a unique temporary
JSON; os.replace attempts to replace the open destination and Windows returns
access denied in this environment. Held-reader readiness precedes the attempt;
reader events bracket its lifetime. Closing the reader before the attempt removes
the failure in the controlled comparison. Simply requesting FILE_SHARE_DELETE
was insufficient; no share-flag-only correction is justified by these results.

This establishes reader/replace overlap as a sufficient experimental condition.
It does not isolate the underlying filesystem/filter implementation, nor prove
antivirus caused (or did not contribute to) the Windows result. No security
exclusions, ACL changes, security-log inference or native handle tracing occurred.
Successful same-directory no-reader/closed-reader controls weigh against a blanket
permission denial. Cleanup cannot explain the held-reader failure because cleanup
starts after it. Duplicate publication is not required: challenges were distinct.

Keep three incidents separate:
1. Original historical Stage 1 error: ROOT CAUSE UNCONFIRMED / FAIL-SAFE / REVIEW
   REQUIRED. No newly recovered original traceback or handle record.
2. Previously reproduced response.json replacement conflict and approved
   once-per-successfully-answered-challenge correction: unchanged, not invalidated
   or reclassified by this diagnosis.
3. New Stage4 challenge.json failure: direct prior exception paths/WinError plus
   source analysis and this reproduction strongly support a reader/replace
   conflict. The specific handle/filter in the prior Stage4 run remains unproven;
   its missing traceback cannot be retroactively reconstructed as captured fact.

## Minimum proposed correction — NOT IMPLEMENTED

Serialize ONLY challenge.json read and replace critical sections using a separate
bounded Windows OS-held IPC guard shared by the coordinator and test Core.
Do not change supervisor.lock or core.lock or repurpose either lifetime lock.
Stage4 already uses the shared Stage1 helper. A named mutex with a reviewed TEST
namespace and bounded wait is a candidate guard; timeout/abandonment must fail
closed, never accept existing metadata or authorize a replacement Core. Guard
identity/security and abandonment handling require review before implementation.
Keep temporary-file publication, unique fresh challenge and all identity checks.
No retry of a failed publication, no ACL changes, no relaxed verification.

This is an additional IPC synchronization mechanism, not a claim that a one-line
share-mode change fixes it. Its design must establish a finite acquisition deadline
inside reconciliation's total deadline. Reader access ends before publication and
writer access ends before readers resume. Existing failed artifacts remain intact.

## Files to change if approved

- tests/lifecycle_stage1/harness.py: narrowly scoped challenge IPC guard and use
  around challenge reads/publication only. Existing duplicate-response suppression
  and both lifetime locks remain unchanged.
- tests/lifecycle_stage1/test_stage1.py: guard ownership/abandonment/deadline and
  freshness regressions, retaining all existing cases.
- tests/lifecycle_stage4/challenge_diagnostic.py: before/after comparison only.
- tests/lifecycle_stage4/test_stage4.py and fixtures.py: affected reattachment and
  shutdown validation/evidence only if needed; no production runtime correction.
- Stage4 report and nonsecret evidence.

If review selects a different primitive or needs a broader production module,
return for scope review. No correction was implemented during this diagnosis.

## Isolated test plan

Repeat all six reader conditions with the guard, multiple readers and coordinators,
new/unchanged challenges, held guard, crashed/abandoned guard owner, timeout,
publication failure, invalid/reparse/denied guard namespace and PID/creation-time
mismatch. Prove no stale response accepted; a publication error stays recorded;
no replacement starts while identity is uncertain. Test the total deadline, not
just individual waits. Retain before/after failures without retries.

## Regression plan

Full existing Stage1 suite plus new cases; unchanged Stage2 and Stage3 suites;
affected Stage4 real reattachment/emergency/30-second deadline tests and actual
Electron tests; full required Stage4 regression matrix before acceptance. No
regressions were rerun in this diagnosis-only turn; AST validation of the diagnostic
script passed. This is not Stage4 acceptance or physical voice/media verification.

## Rollback plan

Before any approved correction, snapshot/hash the exact existing Stage1 source
and approved Stage4 files (including uncommitted changes). Restore only that
correction delta if validation fails, retain all evidence and keep the activation
gate closed. No production data/configuration migration or rollback is involved.
Do not reset unrelated working-tree changes.

## Preservation and decision

New files this diagnosis: challenge_diagnostic.py, this report, diagnosis summary,
three disposable evidence directories and copy manifests. Previously preserved
failure files hash-checked. Production unchanged; no new Core; no acceptance
commit; Stage5 not started. Stage4 remains paused.

REQUEST: approve only the isolated challenge IPC guard design/implementation and
above tests, subject to fail-closed deadline/security review; retain separate
production activation and full Stage4 acceptance gates.


## Additional historical context and actual Electron matrix

User reports a preserved pre-Canonical-Core Windows memory-read application crash
while experimenting with Intelligence and the original application. The dialog
alone identifies neither the faulting executable nor a common mechanism with
Python file publication. Treat as historical context, not causation.
Read-only git revision f86b046 and current source comparison: Intelligence reads
desktop/.jarvis-session.json and opens the referenced origin; it does not spawn a
backend. Desktop backend.cjs spawns server.py on port 0; desktop main uses an
Electron single-instance lock. Shared session discovery exists in that design;
separate userData/checkout or startup paths could change singleton behavior, but
no archived process trace establishes that this happened. No evidence here proves
duplicate providers, voice owners, Core owners or a common memory-crash mechanism.
Current TEST clients use pinned authenticated pipe attachment and independent
TEST profiles; the diagnostic alone starts one synthetic TEST Core. Production
session descriptors and credentials were not read.

The actual-client diagnostic derived the existing authenticated Electron probe,
without changing its runtime, pin checks, lifecycle or production paths. A missing
subprocess import caused one setup failure before any Core started; its evidence
is retained (468a84...). After diagnostic-only import correction, run 839097...
reached these conditions:

| Condition | Challenge reconciliation returns | Recorded result |
|---|---:|---|
| No Electron, actual TEST Core | 100/100 valid | No publication error observed in this interval |
| Teague only | 100/100 valid | No publication error observed in this interval |
| Intelligence only | 100/100 valid | No publication error observed in this interval |
| Both clients | 100/100 valid | Core-side response.json publication FAILED CLOSED |
| Teague close/reopen with Intelligence present | NOT COMPLETED | Reattachment denied after Core recovery state |
| Renderer crash | NOT RUN | Stopped at reattachment/cleanup failure |

These valid reconcile returns are NOT lifecycle acceptance. The control-loop
failure timestamp falls inside the both-clients interval. It records full traceback
at stage4_runtime.py:353 -> harness.py:83 os.replace(response temporary,response.json),
errno 13, WinError 5. The existing once-per-successfully-answered logic was present;
fresh challenges still require replacements. Thus duplicate-response suppression
reduces the previously reproduced exposure but cannot guarantee all replacements
are safe. Do not change or relabel its earlier validated evidence.

The harness observed only reconcile returns during each interval and did not
immediately inspect background FAILED_CLOSED events; that limitation allowed the
interval to finish before the next attachment exposed the recovery state. The
underlying event, not the diagnostic 'passed' bookkeeping flag, governs this
classification. Existing control-loop recovery remains in force; valid file
identity reconciliation alone did not authorize the denied reattachment.

Correlation with both clients does NOT prove the clients caused the response
failure. File-only tests already establish challenge failures without Electron;
the actual matrix has only one run and sequential timing is a confounder. The
new Core-side response failure is a fresh recorded event, not new proof of the
original historical crash or original historical Stage1 incident.

### Retained TEST process — separate cleanup approval needed

All Electron clients exited. Authenticated shutdown was attempted but did not
establish Core exit; no forced termination. Core PID26784, creation
134335979170821093, TEST-STAGE4-664be26d9d7b4aaeb0eb80553005546c,
exe SHA256 372c2eae555b344520bf147be0096e009069aeca4e7f78d6aecea6d53158056a
matches preserved identity. Launcher24164 waits for it. Controller24976 retains
its credentials in memory and accepts fixed STATUS/SHUTDOWN actions; credentials
are not exported or written to evidence. STATUS returned through authentication.
Production untouched. Do not terminate using PID alone or assume old cleanup
approval for PIDs23524/28464 covers this new process.

### Updated proposed correction scope — supersedes challenge-only proposal above

Review a bounded TEST IPC guard for BOTH challenge and response JSON read/replace
critical sections, preserving the once-per-answered-challenge correction and all
identity/freshness/lifetime locks. Concurrent reader/replace coordination, rather
than a share-flag-only change, is indicated by controlled evidence. This adds an
IPC synchronization primitive and requires explicit scope/design review. No fix
is implemented. Same proposed source/test files and rollback apply; extend tests
to fresh response publication, background fault detection and full client matrix.
Acceptance and production activation remain blocked. No full regressions rerun.

REQUEST APPROVAL: (1) identity-bound cleanup of this retained TEST Core and only
its waiting launcher if necessary, preserving controller/evidence; (2) separately,
the bounded bidirectional TEST JSON IPC guard and isolated tests. Recheck all
identities immediately before any approved termination. STOP FOR REVIEW.
