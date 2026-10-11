# Canonical Core — Stage 5 isolated reliability completion

16 September 2026 (Sydney). **Stage 4 is CLOSED in its approved TEST scope. Stage 5's approved isolated reliability matrix is complete and PASS, with inherited exclusions and environment limitations retained.** Production cutover/release remains blocked. No acceptance commit, production activation, migration, installation or paid provider call occurred.

## Stage 4 acceptance handoff

The [Stage 4 closure](../lifecycle-stage4-evidence/stage4-acceptance-20260916/REVIEW.md) binds the fresh 34-check human sequence to the corrected authenticated Electron denial path and existing automated evidence. Four human-run process identities were verified exited. Its final matrix has 48 PASS, three DEFERRED and three LIMITATION cells, with no open in-scope requirement. The selected human/acceptance evidence was archived and hash-verified before Stage 5 began.

## Stage 5 implementation and results

The only new executable test logic is `tests/lifecycle_stage5/campaign.py`, which composes the unchanged Stage 4 coordinator/Core fixtures. It adds no runtime route, Store change, identity policy, provider or production behavior. Existing client, worker and security suites run against the same frozen source. The remaining new scripts perform regression orchestration, read-only reconciliation and evidence preparation.

| Validation | Actual result |
|---|---|
| [Integrated actual-process campaign](integrated-f22acb95e72142b6bae0404e5c0df31f.json) | **1,152 recorded checks passed**, including the existing startup smoke and the additional combinations below |
| Real authenticated input/authority + resource pressure | Invalid input, oversized input, extra authority fields, token-owner mismatch, ordinary shutdown and scope escalation denied; valid request still worked. Actual Core reached its 128-session limit, rejected excess admission, retained preexisting controller authority, freed capacity on detach and rejected stale request authority after reattachment |
| Provider failure + duplicate/reconnect/restart | Five actual-Core scenarios: simulated OpenAI success, temporary 429, quota exhaustion, local unavailable, generation failure. Correct successful/failed persisted state, no duplicate generation on repeated operation, content-conflict denial, owner-isolated provenance, historical response preserved after cancellation, exact last-provider record preserved across authorized restart. No live provider used |
| Concurrent reconnect/shutdown | Four actual races: all four reconnect attempts were DENIED while shutdown returned DRAINING. Fresh epoch/session checks followed. This is the observed ordering, not a claim that randomized scheduling exercised both outcomes. Controlled attachment-before-shutdown is also exercised throughout the campaign |
| Startup contention / interrupted restart / recovery | Four rounds of eight actual competing coordinators; exactly one winner each, losing coordinators adopted the same Core. Three Core crash/recovery rounds and three post-spawn coordinator-loss/adoption rounds; additional before-intent, intent and claimed-boundary crashes. Persistent records and conservative budget uncertainty survived; old sessions/grants did not. UNKNOWN journal work blocked new start authorization |
| [Actual Electron client/media campaign](../lifecycle-stage4-evidence/client-state-media-07ed541b098c4ae198b618f4813f23de.json) | **74 checks, zero failures**, approved host context. Actual Teague/Intelligence executable authentication, shared state, modeled lease partition/expiry, stale callbacks, client detach/renderer crash, reopen, explicit Core restart, emergency and clean shutdown. Both saved screenshots were inspected: authenticated STAGE4_TEST; physical media clearly unavailable |
| Stage 1 / 2 / 3 regressions | **23 PASS + one existing skip / 35 PASS + one existing skip / 43 PASS** |
| Ownership / controller recovery / inspection / repair / repair-loop | **27 / 52 / 13 / 22 / 16 PASS** |
| Shared response boundary | **306 trials, 4,748 assertions**, no failures or live workers. Earlier acceptance evidence remains preserved; counts are not added together |
| Python / offline provider / desktop+Intelligence regressions | **212 / 62 / 35 PASS** |
| Native identity / bootstrap | **15 / 6 PASS** |
| Actual Core normal / emergency / deadline / expiry | **29 / 32 / 36 / 45 PASS** |
| Actual inspection cancel / detach / emergency | **43 / 43 / 44 PASS** |
| Actual synthetic repair cancel / detach / emergency / drain | **44 / 45 / 45 / 46 PASS**; no real repair execution or guessed refund |
| Actual authenticated event polling | **43 PASS** |
| Offline fallback / Deep Review integration / authenticated Deep Review pipe | **12 / 14 / 8 PASS**. The final helper's legacy console says “Electron checks”; that helper is a pipe test, not an additional Electron launch |
| Standalone syntax | Three new Python test/evidence scripts compiled successfully. Frozen JavaScript was unchanged; actual desktop execution and existing prior syntax evidence remain valid |

[regressions-081519.json](regressions-081519.json) records all **29 regression commands**, actual PIDs, times, logs and exit codes (all zero). Counts above overlap prior acceptance suites and include assertions within scenarios; they are not an aggregate count of independent test cases. [requirement-to-evidence.json](requirement-to-evidence.json) maps the approved Stage 5 requirements and retained limits.

## Independent persistence, identity and source verification

[Reconciliation](reconciliation.json) examined 45 selected isolated TEST databases after fixture exit: all passed SQLite integrity and TEST identity checks, with no orphan assistant messages, orphan successful provenance, false-success or duplicate linked messages. Normal chat links its assistant row and provenance; text-only/Deep Review persist answer and provenance together in their existing row. No production database was opened.

[Cleanup](cleanup-final.json) rechecked **194 recorded PID/creation/executable identities** across successful and failed runs; none remained the same live process. Native checks distinguished PID reuse from ownership. No forced cleanup, broad process termination or evidence deletion occurred. Injected crashes used the existing identity-bound TEST self-exit fixture; cleanup otherwise used authenticated lifecycle operations.

[Final source hashes](source-final.json) match all **31 checked Stage 4 acceptance paths**, including the accepted IPC/native source and Electron executable. Native Python identity remains in every relevant process record. HEAD is `8f0b9bce181800f9339249c4024e396246e94208`, but the preexisting reviewed working tree has uncommitted changes: these hashes, not HEAD alone, identify the validated source. No closed runtime gate was modified.

## Preserved failures

The first integrated Stage 5 run, [integrated-1ac9ef43a83d48eaa858e09a70aab920.json](integrated-1ac9ef43a83d48eaa858e09a70aab920.json), has 220 passing records plus one failed verifier assertion and its exception summary. It expected a normal-chat `messages` link for a text-only response. The [approved response design](../lifecycle-stage4-evidence/response-commit-design-20260915/REVIEW.md) and [accepted fresh-process validation](../lifecycle-stage4-evidence/response-commit-final-validation-20260915/REVIEW.md) explicitly establish that text-only answer/provenance occupy one existing provenance row. The original verifier is preserved as `campaign-initial-verifier.py`. Only that mode-specific verifier assertion was corrected; runtime, authority and acceptance criteria were not altered. Its TEST processes exited normally. The successful 1,152-check run is separate evidence and does not erase that failed run.

All original Stage 4 failures remain preserved. The historical Stage 1 PermissionError still has unconfirmed cause; separately reproduced/corrected IPC mechanisms do not establish its historical cause. The historical Windows memory-read crash also remains separate. The human-driver failure and the closure-verifier matrix-label error remain in their original evidence packages.

## Residual limits and next review boundary

- Finite TEST contention/fault coverage is not an exhaustive proof under every Windows schedule or machine condition. Production shortcuts were not executed; actual simultaneous TEST coordinator launches exercise the startup boundary without touching production launchers.
- Existing other-user/cross-session/actual-remote-host skips remain limitations. PID/creation-time mismatch and fake-peer rejection are tested; arbitrary OS PID reuse or every enterprise security configuration is not claimed.
- Actual Electron lifecycle is validated in the approved host context. Restricted-context Electron 44.2.0 GPU failure remains disclosed: exit consistent with STATUS_DLL_NOT_FOUND, exact DLL/root cause unconfirmed. No GPU, DLL, Windows-security or production UI correction was introduced.
- Hardware voice/media and live-provider parity remain deferred. Modeled media and offline providers are labeled accurately. Client queue limits/deadlines use the real queue class in focused tests; Core session exhaustion and lifecycle failures use actual processes. No universal request throughput or resource-metering claim is made.
- Authenticated approval and upload features remain excluded under the owner's explicit decisions, not counted as passed. Cancellation/timeout does not establish zero resource consumption.

The next dependency remains the already identified **relocatable release/bootstrap and enrollment/protocol contract**. Stage 6's synthetic 19-table backup/restore/rollback rehearsal remains valid (13 checks), but live destination switching, clean-machine enrollment/recovery and installation have not been demonstrated. Stage 7 installation/update/uninstall needs that reviewed deployment contract and selected installer mechanism. Implementing it would expand the deployment trust/configuration boundary; it was not attempted under this validation campaign. No additional Stage 4 blocker was invented from that later-stage dependency.

## Files, rollback and disposition

Changed authored paths: the new Stage 5 test driver/evidence directory, the new Stage 4 acceptance-evidence directory, `docs/CORE-COMPLETION-CHECKLIST.md`, and the latest `docs/STAGE4-REMAINING-REQUIREMENTS-20260915.md` status entry. Existing fixtures generated their normal isolated reports/logs. The selected archive manifest provides exact copied paths and hashes; runtime databases, private enrollment material, secrets, profiles and dependencies are excluded.

Rollback requires no runtime or production change: retain this evidence, withdraw only the new documentation disposition if review rejects it, and disable the new standalone Stage 5 campaign entry point. Do not reset the dirty tree, clear stop latches, discard failed intents or restore old data over newer state. Earlier runtime corrections keep their reviewed rollback procedures.

**STAGE 4 — CLOSED (approved TEST acceptance).**  
**STAGE 5 — ISOLATED VALIDATION COMPLETE / PASS with stated limits.**  
**PRODUCTION CUTOVER / RELEASE — BLOCKED pending deployment/enrollment review.**

PRODUCTION SOURCE / DATA / CONFIGURATION CHANGED: NO  
PRODUCTION CORE RESTARTED: NO  
PRODUCTION SOFTWARE INSTALLED: NO  
PAID PROVIDER CALLS: NO  
ACCEPTANCE COMMIT / PRODUCTION ACTIVATION: NO
