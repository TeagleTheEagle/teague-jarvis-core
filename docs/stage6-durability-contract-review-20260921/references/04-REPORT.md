# Stage 6 — cleanup integration preflight

**Final status: BLOCKED.** The immutable 97-identity stress evidence cannot satisfy C5's independent application-level START/STOP requirement. C8 requires stopping if a replay case cannot be justified. This was established during preflight, so no checker implementation, focused test campaign, fresh stress or regressions were started.

The previous **97 = 94 retained + 3 qualified kernel identities** result remains valid for its explicitly limited kernel-identity purpose. It was not proof of the additional independent event requirement. No old result or evidence file has been rewritten.

## Evidence establishing the blocker

The preserved run is:

`D:\JARVIS-STAGE6-LIVE\991e246fb08b45a3904e4cadfa8f4e99\code\etw-stress-0ecaea118aec42c9b0afcaf56c8686d5`

Its archived `stress.ps1` launches only the ETW consumer and Python stress fixture. `stress.py` uses retained handles/Toolhelp and synthetic internal markers. Neither starts the independent WMI/application event monitor.

The complete run-file inventory has no `events.jsonl`, `tap.json`, `queue-state.json` or `queue-entries.json`. Synthetic internal entry/work/return markers are not the required independent process START/STOP stream, and do not cover console helpers. `etw-result.json` contains kernel start/exit events; C5 explicitly prohibits substituting those for the independent stream.

All **1,436 members** of the previous archive were re-read and hash-verified, including the exact stress source and evidence. The archived source matches the current source. This is a missing capture, not a missing file recovered elsewhere within that archive. See `97-run-file-inventory.json`, `prior-archive-verification.json`, and the per-identity assessment `97-identity-preflight.json`.

## 1–3. Files, hashes and old cleanup logic

**Cleanup/monitor/runtime files changed: none.** Only this new review directory contains new audit, snapshot, report and packaging artifacts. All **61 existing diagnostic source/executable hashes** match the prior final-source manifest; exact paths and hashes are in `source-prechange-hashes.json`.

Audited functions, under the D: code directory above:

- `evidence_support.py`, `TreeTracker.scan()` and `finish()`: kernel creation-time identity, signaled handle, exit data and closure. Lines 120–147 determine retained-tree exit/closure.
- `tree_reconcile.py`, `match_child()`: requires exactly one retained identity, matching parent/image name, no recorded PID reuse, and a matching WMI STOP.
- `collect_hardened.py:100`: `if result['retainedMatches']!=1 or result['stopMatches']!=1:missing.append(result)` — the exact condition rejecting a child solely for lacking a retained match, even if separate kernel evidence exists.
- `collect_hardened.py:102`: `good=paired and not missing and q['remaining']==0 and not q['failed'] and q['enqueued']==q['persisted']==q['removed']`.
- `collect_hardened.py:104`: fails when that proof is incomplete. Lines 87 and 107 also report retained-tree cleanup and final disposition.
- `reconcile.py:31`: the separate diagnostic kernel reconciler accepts a recorded error 87 after kernel exit; it is not integrated into the collector. Its optional `tap.json` check at line 52 does not require an independent START/STOP stream. Its PASS is explicitly kernel-identity-only.

## 4–8. Proposed evidence classes and strict conditions

These are reviewed requirements only; they have **not** been implemented in this pass.

| Class | Required proof |
|---|---|
| HANDLE_CONFIRMED_EXIT | Unambiguous retained kernel identity; signaled handle; recorded exit time/code; successful reconciliation/handle closure; independently persisted START and STOP |
| KERNEL_CONFIRMED_PREACQUISITION_EXIT | Complete matching kernel creation/exit pair; exact identity and parent/image consistency; positively recorded failed acquisition after exit; no contradictory handle evidence; independently persisted START and STOP |
| INSUFFICIENT_EVIDENCE | Any missing identity, missing independent event, unknown acquisition error/order, ambiguity, conflict, duplicate exit or unexplained disappearance |

Only the first two classes may pass. A still-running retained handle cannot be bypassed by choosing the kernel alternative.

Identity must include PID plus kernel creation/sequence identity, parent identity, and consistent image identity. PID-only application notifications require an unambiguous association; multiple recorded lifetimes for that PID must fail unless the independent event itself can be bound safely. Do not interpret WMI `TIME_CREATED` as kernel creation time. Do not silently equate unrelated image paths by basename alone.

For the no-handle class require **kernel exit QPC < acquisition-attempt QPC**, with a common documented monotonic clock. Equality or unknown ordering is insufficient. The existing auxiliary reconciler's `>=` is not the requested strict rule and would need tightening. Generic access denial must not qualify as a post-exit acquisition failure. Duplicate or conflicting kernel exits must fail closed.

**START and STOP must both have been independently captured and persisted.** Kernel events or current PID absence cannot supply missing application events. The primary run failure must remain separate from cleanup evidence; successful cleanup never retroactively passes the run.

## 9–17. Validation and cleanup disposition

| Item | Result |
|---|---|
| Focused checker tests | NOT RUN — preflight stop before implementation |
| 97-identity kernel-only replay facts | 94 retained + 3 qualified post-exit kernel records, 0 unexplained kernel identity gaps; preserved |
| Full C5/C8 cleanup replay | BLOCKED — required independent START/STOP proof unavailable for all 97; 0 eligible for a new full-cleanup PASS |
| Fresh stress | NOT RUN — C8 stop condition |
| New handle-confirmed cleanup count | NOT ESTABLISHED; prior 94 is kernel/handle evidence, not new C5 acceptance |
| New kernel-confirmed cleanup count | NOT ESTABLISHED; prior 3 lacks C5 evidence |
| Unresolved count | 97 missing required independent lifecycle proof; not 97 unexplained kernel identities |
| Orphan/process result | No sacrificial processes launched this pass; final read-only snapshot found 0 matching diagnostic/VirtualBox processes |
| ETW cleanup | No ETW session launched this pass; read-only session query found 0 J6Kernel sessions |
| Regressions | NOT RUN — no checker/source changes, and the explicit preflight stop applies |

The initial command-text snapshot returned one PowerShell match and is preserved in `current-host-state.json`. It could match its own inline filter text. A separate script then recorded its observer identity explicitly and excluded it; `final-host-snapshot.json` records zero matching processes. Current absence is only a current snapshot, never substituted for historical exit proof.

## 18–22. Historical accuracy and preservation

- Historical **87 helper gaps remain UNKNOWN**. No acquisition reason has been invented or assigned retrospectively.
- PID **13340** remains a preserved hard-deadline failure; cause UNCONFIRMED.
- PID **9240** remains a preserved hard-deadline/observer failure; cause UNCONFIRMED.
- Protected VM/configuration: **NOT ACCESSED**. No VirtualBox launch, protected hashing or dry run.
- Production JARVIS: **NOT MODIFIED**. No runtime, security, deadline, provider or production configuration change.
- **HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.**

## 23–25. Archive, eligibility and next decision

This review and its evidence are archived separately to TEAGUE INDUSTRIES DATABASE. `archive-verification.json` records actual member verification and hashes. The prior 1,436-member archive remains unchanged.

**Protected-baseline eligibility: NOT ELIGIBLE / NOT AUTHORIZED.**

**Final status: BLOCKED.** This is an acceptance-evidence conflict, not evidence of a production/runtime defect.

The smallest owner decision needed is to preserve the old 97-identity run as **kernel-only evidence**, accept its new full-cleanup replay as an expected missing-evidence failure, and permit a fresh stress run capturing **both** independent START/STOP events and kernel evidence. The checker integration and focused tests can then precede that fresh run. This changes the impossible C8 expectation, not C5's security/cleanup requirement. Do not fabricate old events or weaken C5 to obtain 94+3 full-cleanup passes.
