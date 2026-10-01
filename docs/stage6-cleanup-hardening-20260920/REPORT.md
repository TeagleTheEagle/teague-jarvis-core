# Stage 6 cleanup hardening and startup/exit tracing

**INCONCLUSIVE — STOP FOR REVIEW.** The hard-deadline symptom reproduced in the unchanged whoami probe, PID13340. Its kernel lifetime was **14.0241948 seconds**. This establishes a new real failure, not its internal cause. The trace campaign stopped immediately after bounded evidence cleanup; no further test or acceptance campaign was run after that reproduction. Neither acceptance Dry Run nor protected hashing ran.

The evidence corrections preserve substantially more of this failure, but the complete child/helper proof requirement is not satisfied. Do not classify this infrastructure as validated. Stage6 remains incomplete.

## 1–4. Changed files, hashes, defects and corrections

New candidate: `D:\JARVIS-STAGE6-LIVE\0ee67d2f7dd041c2a2c83bc27f6b86c6\code`. Previous candidate and failed/diagnostic archives remain immutable. All 50 previous candidate files were hashed before editing and rechecked unchanged; all223 tracked non-document application files remained unchanged. Source/Git state was captured; HEAD remains9460dbc44f63c95d1128c1a27f124f87d99b530b, branch main. Existing unrelated changes were not incorporated. No commit was made.

`source-before.json`, `final-source.json`, `files-changed.json`, `final-diff.patch`, per-run source-hashes.json, and candidate-revision1/2 preserve source boundaries. Report preparation scripts are additional evidence tooling under this report directory; they do not execute JARVIS. Before-hashes below refer to the previous diagnostic candidate, not an assertion that all previous instrumentation was already acceptance-approved.

| File | Before SHA-256 | After SHA-256 |
|---|---|---|
| `collect.py` | `992622fc2f92d249a12169f2186b11b32e9709c6ec9dfd1299f42d06d772ca42` | `0c618b0c37a1fca3de14f8ea6b857a92dfa117a370759c0421a5952c36226cf4` |
| `collect_hardened.py` | `NEW` | `75de037ef5284d75f8c2020aef55a701ddb40ac45914eea7d6d18f7caf39187d` |
| `diagnostic_launch.ps1` | `4008b2417907cd2317dbfcc1e08b03728e67b915de5ec19b2e2cf7fe7e333525` | `3b0fd5c0c8cb043ad8df3526e2bb5a7de1f60c5f1ff44a46b33e5bd89c91c18c` |
| `evidence_support.py` | `NEW` | `c0db37a1b28054f405ce6f462bea409fce57a89fbf303ef9660e09528cd6eb19` |
| `finalize.py` | `db61f691e6b856999081d7b29001c5bd9fc8b98bedf62b1974cb76648057776a` | `0bd47900e8926f4fb7bd444f38cb0071cd8a855bfb9cf8dabde00ac622e28bcc` |
| `monitor.ps1` | `9b08b08db9cc6aef6d3ce3a3ad346282b89fb3f90efc795f775aa7fe7929bea7` | `8f85de1875a6f588e5755d209ff85b3e6bceafe671e4e795506af718887afc44` |
| `test_hardening.py` | `NEW` | `fa31af61f0cccaab5de65835ca302566ea841f3f50d07bec4c2fe9803ec3de66` |
| `test_tree_reconcile.py` | `NEW` | `03f82531471234762ea109abf0c867bf8cefb4a8d41547bd977b614a28aeb49a` |
| `trace_fixture.py` | `NEW` | `c13fbcb426101e3030af72f440348417808e92646d1b0036676aa8b4ec3c68d5` |
| `tree_reconcile.py` | `NEW` | `b1b0e82d7a8f37f1cd76278c5272ccbfb1e3c319b6cdfe305c8b8bbdd146c025` |

Confirmed defects and corrections:

- Old collect.py replaced collector-failure.json during cleanup, stopped walking handles on an exception and discarded worker stderr. New collect.py delegates to collect_hardened.py, which keeps a first-failure ledger, appends secondary failures, walks every retained probe and separately reports cleanup. This new entry point is explicitly diagnostic-only and cannot seal acceptance.
- The previous diagnostic probe_timing.py already sampled final kernel details after an independent-observer timeout. That file was reused unchanged; the hardened collector now treats that observer failure as a separate latched failure even if later exit succeeds.
- evidence_support.py provides Ledger, bounded concurrent output draining, Managed helpers and a read-only process-tree observer. Retained process access is query-limited-information plus synchronize; it has no termination right. Main handles are duplicated, not reconstructed by PID.
- monitor.ps1 may drain and durably flush late events after a FAILED_CLOSED producer when all probe exits are independently confirmed. It then reports failure/exit1. This separates cleanup from successful acceptance; authentication/queue identity and original finalization barriers remain unchanged. No successful acceptance seal is emitted.
- finalize.py rejects primary-failure.json and appends finalization/archive errors through the ledger, preserving a prior primary failure.
- An initial live matcher incorrectly bounded WMI TIME_CREATED by kernel lifetime. Microsoft defines it as event-generation time, not kernel process creation time. Seven focused tests validate the correction; PID reuse, duplicate starts, wrong parent/image and missing STOP remain rejected. [Microsoft Win32_ProcessStartTrace documentation](https://learn.microsoft.com/en-us/previous-versions/windows/desktop/krnlprov/win32-processstarttrace).
- PhaseD exposed image-query WinError31 and WinError5 after acquiring child handles. A narrow fix retains the handle/creation identity even when image lookup fails, records image=UNKNOWN and the full error, and still fails closed. No permission change or retry was introduced. The original failures are preserved.

## 5. Primary-error preservation

PASS for tested paths. In phaseE the primary is the original HardDeadline traceback at collection. It remains unchanged while secondary_failures records worker cancellation/nonzero exit, failed monitor disposition and incomplete child proof. cleanup_results stores per-process exits and closes. A new Ledger instance used by an archive/finalizer loads the existing primary rather than replacing it. Later normal exit never changes failed status.

Limits: failure of the evidence filesystem itself can prevent further evidence writes and cannot be guaranteed recoverable. No claim of surviving arbitrary storage loss. Abrupt OS/collector death is not equivalent to the tested caught parent exception.

## 6. Stdout/stderr preservation

PASS for focused large-output, timeout, nonzero-exit and caught-parent-exception tests. Separate concurrent readers keep a64KiB prefix per stream, count/hash the full stream, mark truncation and drain/discard the tail; they do not wait for process completion before reading. Prefix bytes are written unbuffered as received to D:. EOF/reader error/thread state are explicit receipts; missing EOF cannot pass. A synthetic helper emitted2MiB on each stream without pipe deadlock. A deliberately delayed fixture still failed at13.6s and retained both streams when it later exited.

PhaseE workload stderr preserved774 bytes with the exact `Diagnostic workload cancelled` traceback, exit1. No provider calls, secrets, environment dumps or account identity output were collected. The unchanged whoami probe continues to use DEVNULL, preserving its existing workload/privacy behavior; diagnostic helper output alone is captured. Power failure durability is not claimed for live prefixes; final archival is separate. An abruptly killed collector can leave incomplete output metadata; that is failed/inconclusive, not complete capture.

## 7–8. Child handles and complete-tree design

Main probe, worker and resource-helper handles are retained directly; the tree observer duplicates them and samples Toolhelp process/parent relationships at a nominal10ms interval. Descendant handles are retained while available. Kernel creation times must fall inside the recorded parent's lifetime; image and parent links are recorded, and ambiguous PID reuse is rejected. Known launch arguments are fixed synthetic paths/integers only. Unknown child command lines stay UNKNOWN.

Each retained row contains PID, creation FILETIME, parentPID, role, image or metadata error, handle value/retention QPC, kernel exit FILETIME/code, signal-observed QPC and handle-close result. Handle signaling is never converted into a fabricated STOP event. WMI START/STOP reconciliation remains independent.

**The tree guarantee is incomplete.** Across five cases, 217 child/helper STARTs had corresponding STOP observations, but only 130 had matching retained identities; 87 lacked that stronger proof. Short-lived conhost processes can disappear between snapshots, and delayed WMI delivery cannot recover their already-closed kernel handles. ParentPID/name plus later absence is not treated as equivalent proof. PhaseE's conhost PID19276 belongs to that missing-handle set. No Job, suspended start, debugger attachment, console flag change or probe replacement was introduced to make capture pass. Arbitrary/deeper/unobserved descendants cannot be claimed comprehensively covered.

## 9–10. Focused tests and regressions

- Initial focused smoke suite:12/12 PASS (historical transitional run retained).
- Expanded hardening suite:16/16 PASS; actual output flood, fixed-deadline delayed fixture, retained child/console handles, both exit orderings, orphan observation, internal markers, hashes and first-error preservation.
- WMI association tests:7/7 PASS.
- Metadata-loss correction subset:10/10 PASS (new image-query fault test, two real parent/child lifecycle tests, the seven association tests). These counts overlap; they are not summed as unique requirements.
- Existing probe-policy tests:26/26 PASS.
- Existing monitor/D-workspace/heartbeat/process/failure-injection/finalization Python suite:69/69 PASS.
- Exact queue/EventIdentifier suite:222 assertions PASS;10,000-event collision stress:10,000 persisted/removed, zero residue/loss/duplicates/internal-ID collisions;9,993 deliberately induced external-ID collisions.
- Existing finalization-gate suite:196 assertions PASS, including late STOP, missing STOP, failed subscriber/heartbeat/consumer/write/flush, unknown/mismatched/duplicate identity, and1,000-process/2,000-event clustered simulation. This actual run count supersedes no historical result.
- Standalone Python syntax compilation passed for the final candidate files listed in syntax-python.json. Syntax is not runtime acceptance.

Exact commands/output: hardening-tests-1.txt, hardening-tests-2.txt, tree-reconcile-tests.txt, metadata-regression.txt, focused-result.json/txt, probe-policy-*/result.json, queue-regression.txt, finalization-regression.txt in the archived live candidate. All were run with Python -B / PowerShell -NoProfile; run paths and source hashes accompany each. Broad regressions preceded the final metadata-only correction; its directly affected subset passed afterward. The unexpected phaseE hard failure then triggered STOP, so no later full rerun was performed. Production runtime tests were not run because application hashes did not change.

## 11–12. Sacrificial trace campaign and reproduced failure

| Case | Probes / START / STOP | Max kernel lifetime s | Max heartbeat s | Retained child identities / observed children | Disposition |
|---|---:|---:|---:|---:|---|
| A | 37 / 37 / 37 | 0.0283603 | 1.0651070 | 24/38 | FAILED |
| B | 55 / 55 / 55 | 2.1729223 | 1.0659369 | 32/57 | FAILED |
| C | 31 / 31 / 31 | 6.1251877 | 1.0550308 | 19/33 | FAILED |
| D | 56 / 56 / 56 | 0.0273609 | 1.0661307 | 33/58 | FAILED |
| E | 24 / 24 / 24 | 14.0241948 | 6.3615859 | 22/31 | FAILED |

A=idle; B=C: sustained reads; C=C: hashing; D=D: hashing; E=two-pass sacrificial hash workload plus explicit diagnostic helper/console activity. E stopped during its first pass. No manifest/archive/acceptance dry run was performed by that worker. These are bounded diagnostic subsets, not the full five-workload acceptance campaign. None of the failed traces was retried for a pass. A's original false matching failure remains preserved; corrected offline analysis still finds14 genuinely unretained helpers.

Total main probe lifecycle: 203 STARTs and 203 STOPs. All main retained handles exited; no queue residue. All five cases remain failed because complete child proof was not achieved; D additionally preserves metadata-query errors, E additionally preserves the actual deadline failure. Main probe eligible-response counts exclude the failed probe even though its later lifecycle was captured.

## 13–14. Internal and external timings

New real failure identity: PID13340; creation FILETIME134343540714922892; parent collector18604; unchanged `D:\JARVIS-STAGE6-LIVE\0ee67d2f7dd041c2a2c83bc27f6b86c6\code/J6Probe.exe`, SHA25623240ef9f8b0a9a324110b1c2331de31dc1b0e08f5359cb707e51a939af56cd3, no arguments. This is the whoami image, not the deliberately delayed test fixture.

| Observable | Seconds after launch |
|---|---:|
| CreateProcess returned | 0.0024289 |
| Main identity captured | 0.0024764 |
| Independent tree handle retained | 0.0027122 |
| Internal entry / work / cleanup | UNKNOWN |
| Hard deadline failure; handle still nonsignaled | 13.6110283 |
| Independent observer saw signal | 14.0258927 |
| Tree observer saw signal | 14.0294543 |
| STOP callback | 15.0903775 |
| STOP enqueued | 15.0904278 |
| STOP persisted | 20.8244644 |

Kernel lifetime14.0241948s; exit code0; kernel exit FILETIME134343540855164840. Recorded kernel+user CPU time0.046875s. The independent15s wait returned0 **before its deadline**, unlike historical PID9240 which timed out at15s. Exact kernel signaling QPC is unknown; observer times are upper-bound observations, not the exact signal instant. Later normal exit does not invalidate the hard-deadline failure.

Native diagnostic controls retain anonymous mapping markers. Python sacrificial helpers additionally log entry/import-initialization, work, token query, filesystem operations, cleanup, stdout/stderr closes, child wait and return-main markers. These provide timings for those controls only. They do not instrument inside Microsoft's whoami or establish its internal delay. No file-filter, kernel stack or image-load ETW evidence was collected.

The failing lifetime overlapped four C:4MiB read/hash operations whose reads lasted3.7305792,3.2982786,3.4998397 and3.3147054s. Their hashing was about2ms each. This is measured storage overlap, **not proof that the reads caused the probe delay**. The console helper's START/STOP callbacks are delayed event observations, not its kernel creation/exit times. No causal claim about Defender, a driver, console initialization or teardown is supported.

## 15–17. Cleanup, residual uncertainty and historical status

All retained campaign processes exited and handles were closed. Final host reconciliation checked393 recorded identities across focused tests/campaigns with zero matching live identities; all217 event-child PIDs were absent in the later host snapshot. Zero matching J6Probe/candidate processes and zero VirtualBox processes. These are current-state findings; they do not upgrade missing historical child-handle proof.

PhaseE preserved original failure plus all three secondary failures. Its worker exited1 due to the explicit stop signal; monitor exited1 after late-event drain/durable flush to keep the producer failure fail closed. Queue48 enqueued/persisted/removed, zero residue. The failed state is retained despite clean main/worker shutdown. No unrelated process was killed. The already-authorized existing regression fixtures exercised their own directly retained disposable process termination, not production or unrelated processes.

Unresolved: exact whoami entry/work/teardown location of delay; exact missing child creation/exit timings; short-lived helper coverage; scheduler/storage/security causation; impact of diagnostic observer overhead; incomplete application-wide process-tree proof. No timeout increase, arbitrary retry, probe substitution or Windows security change was made.

PID9240 remains FAILED, internal cause UNCONFIRMED. This new PID13340 failure does not establish that both share a root cause. HISTORICAL STAGE1 CAUSE: UNCONFIRMED.

## 18–22. Protection, archive, eligibility and final status

Protected VM/configuration access: NONE. No VirtualBox launch, protected hashing, VM/snapshot/ACL changes. Production changes: NONE;223 tracked application hashes unchanged. Prior50-file candidate and both historical archive hashes unchanged. The initial elevated Git inventory hit Git's ownership guard; this preparation failure was preserved and read-only Git capture was performed under the normal repository owner. No safe.directory configuration or security setting was changed.

Archive destination: `C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 CLEANUP HARDENING 20260920`. archive-verification.json is the authoritative post-copy member/hash verification receipt; do not infer archival success until it exists. Raw old/new failed traces, source revisions, output captures, timing records, complete diff, before/after hashes and tests are included. No .env, keys, VM artifacts or production data are included.

Protected-baseline eligibility: **NOT ELIGIBLE / UNAUTHORIZED**. No Dry Run#1 rerun, no Dry Run#2, no protected hashing, no acceptance commit. No trace case ran after the hard failure.

**Final status: INCONCLUSIVE.** Evidence infrastructure is improved and successfully preserved the new failure, but its complete child-handle/lifecycle requirement is not satisfied. It must not be labelled EVIDENCE_INFRASTRUCTURE_VALIDATED.

Next review: approve/design an earlier, bounded kernel-level child creation/exit observation method that preserves unique identities without changing probe behavior. Polling/WMI cannot guarantee retaining these short-lived helpers. Separately determine what startup/loader or wait-state trace can locate whoami's internal delay; do not infer it from C: overlap. No further implementation or execution is performed here.

Rollback: use the unchanged previous candidate; leave the new diagnostic candidate inactive and retain all failed evidence. No production rollback, Git reset, security change or evidence deletion is required. The new diagnostic collector is not a replacement accepted baseline.
