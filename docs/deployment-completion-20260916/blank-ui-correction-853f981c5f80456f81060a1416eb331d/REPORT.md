# JARVIS blank UI — controlled TEST correction

Date: 2026-09-16. Disposition: **PASS for the bounded relocated TEST bootstrap correction; STOP FOR REVIEW.**

Both actual Electron interfaces visibly render after moving the existing TEST initialization before Electron readiness. The previous blank captures, unsuccessful attempts, packages and diagnostic findings remain preserved. No production activation or acceptance commit was performed.

## Correction and scope

Runtime source changed: `deployment_test/package.py`, only its `ELECTRON_ENTRY` and `NODE_LAUNCHER` templates.

Before: Node started Electron immediately; the packaged Electron entry waited for asynchronous private configuration before calling the existing `launchTestClient`. Electron could initialize GPU/profile state before the existing TEST profile/rendering policy was applied.

After: Node waits for configuration, passes only bounded nonsecret TEST client/path metadata to the fixed Electron entry, and sends full configuration through the existing private IPC channel. The entry calls the unchanged `launchTestClient` synchronously during initial module loading. Its existing validation and pre-readiness profile/rendering policy run before asynchronous authentication and BrowserWindow creation.

No new GPU switches, rendering policies or dependency versions were introduced. No renderer, preload, Core protocol, authentication, lifecycle, Store or production behavior was changed. Authentication and executable verification remain required before attachment/window creation.

Additional TEST files:
- `tests/deployment_contract/test_electron_startup.cjs`: eight focused bootstrap and credential-boundary tests.
- `tests/deployment_contract/blank_ui_validation.py`: uses the existing packaged TEST and actual-client fixtures; pauses for actual pixel inspection, captures both clients, then runs existing client lifecycle checks. It verifies and imports the candidate's matching frozen deployment policy.
- This evidence directory contains report, source snapshots, collection helper, logs, screenshots and hashes.

Exact working-source patch: [source-changes.diff](source-changes.diff). Before/after source hashes: [final-validation.json](final-validation.json). The pre-build review was recorded in [PREBUILD-REVIEW.md](PREBUILD-REVIEW.md).

## Root-cause validation

**Initialization-order hypothesis: CONFIRMED for this controlled packaged-bootstrap reproduction.**

The preserved baseline authenticated and loaded both pages but produced white pixels; its GPU child processes used the generic Electron profile. With the initialization-order correction and otherwise identical packaged runtime/dependency/client payloads:
- Both interfaces rendered actual visible pixels in Windows screenshots and existing Electron capturePage captures.
- Both authenticated to the same TEST Core and read the same canonical TEST records.
- All eight sampled main/renderer/GPU/utility processes used the correct per-client TEST profile.
- Actual close/reopen, renderer-crash survival, restart, cancellation and cleanup regressions passed.

The candidate has exactly three changed payloads: generated `app/client-launcher.cjs`, generated `app/deployment-entry.cjs`, and their source template `app/deployment_test/package.py`. No UI redesign or dependency substitution explains the result. This supports the startup-order defect at the bootstrap level; it does not identify a specific Chromium compositor/driver/DLL failure internally. The old restricted-context GPU/DLL finding and historical Stage 1 PermissionErrors retain their separate classifications.

## Actual client results

| Requirement | Teague Industries / JARVIS | JARVIS Intelligence |
|---|---|---|
| BrowserWindow/page/preload/TEST renderer | PASS — actual attached renderer | PASS — actual attached renderer |
| Authenticated Core access | PASS | PASS |
| Visible pixels | PASS | PASS |
| Accessibility tree | Present; saved separately | Present; saved separately |
| Renderer remained operational | PASS — actual client interactions and captures | PASS — actual client interactions and captures |
| Profile isolation in sampled child processes | PASS | PASS |
| Meaningful renderer exception | None observed in available logs; console coverage limitation below | None observed in available logs; console coverage limitation below |

Actual Electron capture evidence:
- [Teague Industries / JARVIS](teague-08739ff7-a8c1-4b56-9667-88af06643803.png)
- [JARVIS Intelligence](intelligence-002bc7bf-7cd6-48ee-9488-8f9f013e29c3.png)

Separate Windows screenshots: [Teague](teague-visible.jpg), [Intelligence](intelligence-visible.jpg). Accessibility snapshots: [Teague](teague-accessibility.txt), [Intelligence](intelligence-accessibility.txt). These were inspected by Codex; this is not a claimed new human acceptance run.

Electron version: **44.2.0**.
Executable SHA-256: `07b043bf9b0a0ac14a82fac0b612b7b7ed13cde727d706d74e41a45278ab51f1`.

Initial visual run: Teague PID 468 and Intelligence PID 22824 authenticated to Core PID 14596, epoch `1f0d251977da4378a200e05c826e559b`, data identity `TEST-134c2060ce2d4e4f9cfcf697c5c46bc1`. Creation times and executable hashes are in [active-identities.json](active-identities.json) and the actual-client evidence.

## Exact profile and child-process observations

Teague profile:
`C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\deployment-test-releases\TEST-INSTALL-a4f91536cd1d4a30ab426480ffe3f1c7\client-state\teague-ab5e7abc-a8aa-495c-ba66-cd08828b2f06`

Intelligence profile:
`C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\deployment-test-releases\TEST-INSTALL-a4f91536cd1d4a30ab426480ffe3f1c7\client-state\intelligence-8b44eebe-fe05-4cff-a0cc-10aeead83c34`

| Role | Teague PID | Intelligence PID | Observed profile |
|---|---:|---:|---|
| Main | 468 | 22824 | Corresponding exact profile above, reported by the main process |
| Renderer | 2428 | 5852 | Same corresponding profile, process arguments |
| GPU | 20548 | 24384 | Same corresponding profile, process arguments |
| Utility | 17140 | 18148 | Same corresponding profile, process arguments |

**8/8 observations matched.** None of these sampled processes used `C:\Users\jonny\AppData\Roaming\Electron`. This is a sampled live process census, not a continuous filesystem trace. See [child-profile-observations.json](child-profile-observations.json) for exact paths, identities, timestamps and hashes.

## Validation and commands

Working directory: `C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\jarvis`.

| Validation | Result | Evidence |
|---|---|---|
| Actual candidate bootstrap + existing Electron client lifecycle regression | **101 checks passed, 0 failed** | [actual-client evidence](actual-client-bd29756dc43a41ef999e94198db672db.json) |
| Focused startup contract | **8 tests passed, 0 failed, 0 skipped** | [startup log](startup-contract-tests.log) |
| Existing desktop + Intelligence tests | **35 tests passed, 0 failed, 0 skipped** | [regression log](desktop-intelligence-regressions.log) |
| Syntax only | **2 Python files parsed; 4 JavaScript files checked, all passed** | [final validation](final-validation.json) |

Commands:
```powershell
.\.venv\Scripts\python.exe -B tests\deployment_contract\blank_ui_validation.py docs\deployment-completion-20260916\blank-ui-correction-853f981c5f80456f81060a1416eb331d

& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests\deployment_contract\test_electron_startup.cjs

& 'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test desktop/test/*.test.cjs intelligence/test/stage4-client.test.cjs

.\.venv\Scripts\python.exe -B docs\deployment-completion-20260916\blank-ui-correction-853f981c5f80456f81060a1416eb331d\collect_final_evidence.py
```

Actual desktop execution used the approved host context. The interactive visual driver received VISUAL_PASS only after real Windows screenshots were inspected, then REGRESS after both capturePage images were inspected. The collection helper records each exact node --check command and Python parse input; syntax checks do not count as runtime validation.

The unchanged existing actual-client checks cover authenticated executable identity, canonical TEST records, request cancellation, capture/playback ownership, stale callbacks, lease expiry, disconnect/reconnect, client closure without Core death, renderer-crash survival, explicit stop/restart with a new epoch, emergency suspension, persisted settings/budgets and authenticated cleanup. Media is modeled/silent, not physical capture/playback.

## Integrity and preservation

Candidate package:
`C:\Users\jonny\Documents\Codex\2026-09-07\cr\outputs\deployment-test-releases\TEST-PACKAGE-2966f064bb014c14a13e260937ea4074`

Build identity: `c7ecba53315d460a86e1e02a64d9cf70`.
Manifest SHA-256:
`fcbd0381f3b4d2b0acd89c15e373418dc27172a60456e3e1698a1963fec091e3`.

**796/796 files match** in the candidate and each of its two TEST installations. The old package also remains **796/796 matched**, manifest `0a50be9481eb16cb88e59bc4b7492f33a46e42c74dd7ffc2c92a3ff749db9ceb`.

HEAD remains `8f0b9bce181800f9339249c4024e396246e94208`; no commit was created. All **297 recorded tracked-file hashes** match their pre-change values. The modified TEST packaging file and new test files were untracked before this task; their specific patch/hashes are separately preserved. All three recorded unchanged client/fixture sources match, and all **13 previously recorded diagnostic artifacts** remain hash-identical. Unrelated pre-existing working-tree changes were left intact.

## Failed and transitional evidence retained

1. Original blank windows, capture timeout and associated teardown errors remain in the preserved prior diagnostic. Later success does not erase them.
2. First candidate build failed with **REPARSE_DENIED**, because the invocation passed an unresolved Electron dependency symlink. The next invocation used the established fixture's resolved path, with no weakening of reparse checks and a new package identity. See [build-failure.json](build-failure.json) and both build-input records.
3. First candidate validation failed with **APP_LOCAL_CRT_REQUIRED** before Core launch: the runner imported unrelated pending working-tree native-package policy rather than the frozen candidate's matching policy. No DLL or runtime policy was changed. The corrected TEST driver verifies the complete candidate before importing its matching policy. The failed evidence remains [actual-client-validation.json](actual-client-validation.json); the successful run has a separate identity.
4. The sandboxed image-view tool could not directly read two owner-private TEST screenshots (access denied). Only the two existing image files were copied through approved host access, hash-verified, and then inspected. No ACLs were changed.

Final successful validation counts exclude these prior unsuccessful attempts; they remain disclosed failures.

## Shutdown and production boundary

Old Core PID 3864 was reverified against its preserved creation time, executable digest and TEST identity, then shut down through its retained authenticated controller. See [old-core-precleanup.json](old-core-precleanup.json) and [old-core-cleanup.json](old-core-cleanup.json).

All candidate clients and TEST Cores exited using existing lifecycle cleanup; coordinators exited normally. Explicit restart tests used sequential Core epochs. No blind kill or forced process termination was needed. The final [process census](final-process-census.json) reports **zero relevant processes** in the old and both candidate TEST installations, and PID 3864 is absent. TEST files remain preserved under existing policy.

- Production touched: **NO**.
- Production Core restarted: **NO**.
- Production data/configuration/enrollment used or changed: **NO**.
- Paid provider calls: **0**.
- Stage 4 lifecycle authority altered: **NO**.
- Acceptance commit created: **NO**.
- Production deployment/activation: **NO**.

Production preservation is supported by the scoped TEST paths/process identities, unchanged recorded production-source hashes and the absence of production operations in this campaign; it is not a disk-wide forensic claim about unrelated activity.

## Limitations and rollback

- No clean-machine, physical voice/media or paid-provider validation occurred.
- No permanent console instrumentation was added. Available Electron stderr shows configuration and close messages without meaningful renderer/GPU exceptions; the existing fixture does not forward the complete renderer console, so this is not an exhaustive no-console-error guarantee.
- Profile observations are exact sampled process evidence, not proof covering every future Windows host or transient process.
- Previously excluded/deferred product controls, approvals/uploads and other acceptance items retain their prior disposition. Rendering is not proof that all visible legacy controls are supported.
- The correction uses the frozen validated baseline's native/deployment policy; pending unrelated native packaging changes are not accepted by this result.
- Historical Stage 1 root cause and restricted-context missing/inaccessible DLL remain unconfirmed.

Rollback: keep the original immutable package and all evidence; do not overwrite an installed release. The TEST source correction can be reversed using only the saved template diff/before snapshot after checking for newer edits. Do not reset the entire dirty working tree. No production rollback or data migration is needed. Candidate credentials/state remain in their private local TEST locations; they are excluded from the archive.

Only nonsecret report/source/test evidence and images are archived to TEAGUE INDUSTRIES DATABASE with per-file SHA-256 verification. Heavy packages, TEST databases, bindings, keys and credentials are not copied. Stop here for review.

