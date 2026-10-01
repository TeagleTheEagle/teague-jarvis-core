# Final overhead qualification harness preparation

FINAL_OVERHEAD_HARNESS_READY, contingent on passing final census and archive receipt. No qualification benchmark executed. No final overhead measurement or performance qualification exists.

## Bound artifact

Workspace: `D:\JARVIS-STAGE6-LIVE\qualification-harness-v1-20260924`.
Binary: `J6FinalQualification.exe`.
Final SHA-256: `d68159ce5c85a2cf71fbbe297a09e16cb214bce0d862024e6367535315d3ccfb`.
Protocol SHA-256: `46e30ed33fba977e430b7d290d042a245160156bb67f9788d91e11b92abf1ab1`.
Authoritative binding: qualification-binding-final.json. The unsuffixed binding/review are retained intermediate evidence, not the launch binding.

One executable contains three separately compiled, namespace-isolated paths. Original headers are copied byte-identically. Namespace aliases prevent cross-arm timer/recorder state sharing. There is no common successor timer accidentally used by A. MSVC 19.44, C++17, /EHsc /O2 /GL-; linker /OPT:NOICF. The map records distinct linked addresses. All commands, build logs, assembly and objects are preserved.

The prior approved 60-block three-arm schedule is preserved. Protocol labels remain A=baseline, B=separate-clock reference, C=optimized. The owner's requested optimized comparison B corresponds to protocol C; this naming is explicitly bound. Primary qualification remains optimized C versus unchanged A, never reference B versus C alone. No extra reference campaign is proposed or run.

## Feature/state table

| Feature | A unchanged baseline | B reference | C optimized |
|---|---|---|---|
| Timer header | Frozen predecessor | Frozen separate-clock reference | Frozen successor |
| Selector body | Predecessor | Successor | Successor |
| New scope handoff | Absent | 96 bytes | 96 bytes |
| Scope total size | 88 bytes | 184 bytes | 184 bytes |
| Lifecycle append | Absent | Enabled | Enabled |
| Arrival/existing completion reads | 1 + 1 | 1 + 1 | 1 + 1 |
| Extra diagnostic completion read | Absent | One when eligible/enabled | Absent |
| Existing v2 sidecar | Disabled | Disabled | Disabled |
| Original timer/lock metrics | Present | Present | Present |
| State/reset | Arm-local | Arm-local | Arm-local |

Source binding proves A has the actual predecessor CallbackScope definition, not a successor with output disabled. A generated assembly contains no Handoff/lifecycleTap path. B/C use unchanged accepted record/handshake semantics and the versioned completion endpoint; profiling variant D is absent. The baseline and optimized timer constructors each have one QPC call; destructors have one each, versus two in reference B. Non-QPC timer-destructor call targets match after namespace normalization. Existing histogram locks are not new locks. Source and assembly show the additional optimized stores/stack footprint rather than hiding them in A. Instruction-line counts and linked symbols are recorded in generated-code-review-final.json; no performance conclusion follows from them.

## Workload and limitations

The harness uses exact source-derived authority callback and detailed LifecycleEvent bodies. The detailed outer prefix is retained through lifecycle provider/id filtering; unrelated detailed events are out of scope. All three arms use identical controlled adapters and preallocated selector state. No live TDH, OpenProcess, output filesystem, ETW session, provider or protected data is used. The adapters supply fixed synthetic decoded fields; direct original selected-output QPC calls remain real. Existing metadata, acquisition and accepted-output timing sites are represented equally. Detailed schema lookup is a declared cache hit; acquisition represents the existing failed-open timing branch, without an OS process query.

This is the intended controlled offline callback workload, not the complete native ETW decoder/map/I/O path. Preallocated selector storage and scalar decode adapters replace expensive native dependencies identically in every arm. A future result cannot establish live ETW overhead, provider behavior, or JARVIS total CPU cost. Compiler/layout/register effects remain part of the compiled comparison.

Cases: admitted START/STOP, unknown parent/instance, duplicate START/STOP, invalid identity, decode failure, capacity rejection, handled exception and out-of-scope event; both authority/detail channels. Inputs use version 4 and fixed scalar fields, with deterministic per-callback identities. Duplicate cases repeat one identity so capacity rejection cannot mask them. Each chunk's case is ordinal modulo 11, channel is floor(ordinal/11) modulo 2. Warm-up and measurement independently restart this input order. A/B/C receive identical counts and input generation. State/query/output digests must match. No sleeps, artificial one-arm work or adaptive calibration.

Native tests count C++ operator-new activity and find none in these adapter callbacks. This is not a claim about allocations inside Windows/CRT exception machinery, or about native TDH/map allocation behavior, which is outside these controlled adapters. No new blocking lock is introduced; existing callback/event-map locks remain. No filesystem I/O occurs inside callback execution. Setup, digest/reset and output serialization occur outside measured chunks.

## Fixed future measurement

ABC, BCA, CAB, ACB, CBA, BAC repeated ten times: 60 blocks, 180 trials. Per arm/trial 20,000 excluded warm-up and 1,000,000 measured callbacks. Totals 3,600,000 warm-up / 180,000,000 measured. Chunks are 8,192 maximum; final measured chunk is 576. Original record capacity remains 16,384. Offline reset/digest occurs after callback return and outside CPU/wall intervals.

GetThreadTimes(GetCurrentThread()) kernel+user deltas remain the primary metric; raw counters, thread IDs, process identity, QPC wall intervals, frequency and counts are retained. These are 100ns units, not a guarantee of 100ns resolution. Short chunks may contain zero CPU increments; valid positive total trial CPU is mandatory. Quantization and scheduling uncertainty are not corrected with extra samples.

Within-block optimized percentages and deltas are grouped ten blocks into six means; Student-t 95% intervals use df=5. Numerical PASS requires upper bound <=1.0%; lower bound >1.0% is failure; otherwise not established. The analyzer never silently accepts unresolved drift: it emits descriptive position, temporal and grouped residual diagnostics and requires their review before a final disposition. No alternative estimator or new drift threshold was invented. Historical evidence is never pooled.

The launcher permits one fresh ONE-FINAL-ATTEMPT directory, checks bound hashes before/after, enforces 1,200 seconds, retains child handle/creation identity and rejects contradictions. Timeout terminates only its owned fixture process, preserves partial output and permits no retry. It does not archive or declare acceptance automatically; final census, drift review and archive verification remain explicit procedure steps.

## Executed preparation tests

- Final build: PASS; one same-build executable with three paths. No compiler warnings in final build log.
- Native short --selftest: 254 assertions PASS.
- Python result/protocol/binary validation: 27 checks PASS, using fabricated statistical input only.
- Generated-code/source/syntax/preservation review: 1,268 checks PASS, including 1,219 preserved-file comparisons. These are not additional runtime benchmark trials.
- Negative executable invocations: wrong protocol and wrong mode return 90 before benchmark entry.
- Correctly bound --qualify was NOT invoked. ONE-FINAL-ATTEMPT does not exist.

Tests cover branch outputs/identity state, decoded query counts, arm selection, state isolation, capacity, reset independence, warm-up exclusion, tiny measured callback counts, thread identity, valid CPU APIs, nonzero exits, malformed JSON, unsupported schema, wrong counts/order/thread/counter/protocol/binary, incomplete output, and no automatic acceptance of unresolved drift. Native measurement calls in selftest use only seven callbacks per arm and are correctness tests, not overhead estimates.

## Preserved failures and review corrections

The first selftest failed because the duplicate fixture prefilled 8,192 identities, triggering the existing earlier capacity rule. Exit 97, stderr and failed source/binary are preserved in failed-selftest-1. Corrected only fixture input preparation; frozen selector unchanged.

A subsequent fidelity review found that inherited semantic-test dependency doubles omitted original helper timing. The pre-review source/binary are retained in pre-timing-fidelity-review. All arms now retain the declared original timing sites equally. Intermediate 254/27 PASS results and their generated-code review remain preserved; final binding points to the final rebuild and final tests only.

No failed qualification attempt occurred. No benchmark retry, threshold change, recorder optimization or historical correction occurred.

## Preservation and next action

1,219 prior files match SHA-256, size and modification time, including timestamp successor/reference, attribution, prior benchmarks, frozen checker and historical ETW evidence. The 92-member implementation archive also verifies. Source snapshot and current artifact hashes are archived. No VM/configuration or production access was used to assert this; no operations targeted them.

Final read-only census and archive receipt are separate required evidence. Broad project sync is avoided because it would overwrite unrelated records; only this fresh bounded evidence archive is written. No secrets or environment files are included. No production change, live ETW, UAC, medium/59.7GB run or new optimization.

Historical ETW-loss cause remains UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED. No acceptance commit. Rollback is simply not using this offline fixture; all predecessors remain untouched.

STOP. OWNER-REVIEW-ONE-RUN.md contains the proposed single final execution procedure, not executed here.
