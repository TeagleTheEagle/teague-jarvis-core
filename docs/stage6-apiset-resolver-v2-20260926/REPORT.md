# ANOTHER_PROVENANCE_BLOCKER_FOUND

## Result

The narrowly scoped API-set correction passed 40/40 focused offline tests and the exact original failed-chain regression. Input inventory stopped at its first different unresolved dependency. Neither prospective observer was built. No live ETW, UAC, VM access, or production change occurred.

## Correction and evidence

New files only: resolver_v2.py, test_resolver_v2.py, run_focused.py, inventory_v2.py, final_census.ps1 and preserve_result.py, plus generated evidence. No predecessor file was edited. resolver-parser.diff and inventory-successor.diff show the versioned replacement comparison, not an in-place modification.

The v6 parser retains schema bounds, HashFactor, sorted hash index, exact hashed-name/length, namespace fields, all values, and importer aliases. Resolution uses indexed-hash plus full hashed-name equality, then the exact importer override or unambiguous default. No version substitution, nearest match, hardcoded host, or all-values expansion occurs. Unsupported layouts, malformed bounds, ambiguous or empty applicable mappings fail closed.

Focused tests: 40 passed / 0 failed. See focused-tests.log. Python syntax checks passed. Missing ordinary physical DLLs still fail; ordered physical search is unchanged (importer directory, VC bin, System32). This is not a complete Windows SxS/loader emulator.

Exact import: `api-ms-win-core-errorhandling-l1-1-0.dll`, NORMAL import of ucrtbase.dll, classified BUILD_TOOL_RUNTIME_DEPENDENCY. The documented query returned E_NOTIMPL (0x80004001). Mapping method: `OFFLINE_SCHEMA_V6_HASH_INDEX`.

Selected schema entry: `api-ms-win-core-errorhandling-l1-1-3`; hashed name `api-ms-win-core-errorhandling-l1-1`, length 68 bytes. Selected default has an empty importer alias and host kernelbase.dll. Host: `C:\Windows\System32\KernelBase.dll`. SHA-256: `bffbb14b005b7b2764dbde1a95512aeb95662215fc33c780618435cde6661d6a`.

Host: Windows 26200.9550, AMD64, schema version 6. Schema: `C:\Windows\System32\apisetschema.dll`. SHA-256: `568c72f6216d83a716d6fa9bec59ae8d93e6728062d969ac362013f3910c0007`. Host/schema unchanged from the reviewed preparation. Function-forward destinations were not used as mapping proof or newly probed.

## First unrelated blocker — no scope expansion

Importer: `C:\Windows\System32\sechost.dll`. Exact DELAY import: `ext-ms-win-security-chambers-l1-1-0.dll`. Symbol: GetCapabilitySidsEx. Failure: `No nonempty applicable host`. Raw indexed schema selection is preserved in first-blocker-evidence.json. No same-name DLL was invented and no delay import was ignored.

This is a provenance-closure blocker, not evidence that JARVIS, Windows, or the SDK is broken. Whether this declared delayed runtime dependency is required on the prospective build execution path is UNESTABLISHED. Changing that classification requires a separate review. No such change occurred.

Inventory: 5877 files / 1000155407 bytes hashed; 170 resolved import edges across 6 visited images. Encountered unresolved dependencies: 1. Encountered ambiguous mappings: 0. Resolved targets outside inventory: 0. Remaining traversal was stopped and is UNASSESSED (170 pending stack entries, not unique modules). These zeros are partial observations, not complete-closure claims.

The six provenance classes remain distinct. File rows: BUILD_INPUT_REQUIRED permitted root superset = 5,730; BUILD_TOOL_RUNTIME_DEPENDENCY = 146; CURRENT_HOST_MAPPING schema file = 1. OS identity is separately CURRENT_HOST_MAPPING. OUTPUT_RUNTIME_DEPENDENCY, CORROBORATIVE_ONLY and NOT_REQUIRED_FOR_BUILD_COMPARABILITY have no newly observed file rows. No observer output exists to inspect. Runtime-only edges do not enlarge BUILD_INPUT_REQUIRED.

## Preservation and cleanup

All 1008 preserved files retain identical inventory, SHA-256, size and modification time. Scope is exactly preservation-before.json: current authority-independent candidate and six prior evidence/preparation trees. This is not a claim that every historical repository archive was rehashed. All 5877 captured inventory inputs were reverified unchanged. Frozen checker/finalizer, detailed observer, authority, witness and handoff are unchanged.

Final host census: 0 matching diagnostic processes, 0 trace sessions, 0 VirtualBox processes. The initial sandbox census was denied and preserved as final-census.json; the same read-only census succeeded in host command context, without Windows UAC or process/trace changes. A broad read-only AGENTS.md search encountered access-denied historical fixture directories; direct project instruction read succeeded. No protected VM/configuration was read.

Production touched: NO. Protected VM touched: NO. CONTROL built: NO. TREATMENT built: NO. ETW/live run: NO. No cleanup termination or security change occurred.

## Owner review next

Read-only review of the exact sechost delayed contract: establish its current schema disposition and whether prospective build comparability requires it. Propose any narrowly bounded provenance classification amendment separately; preserve missing/ambiguous required-dependency failure. Do not omit it automatically, rebuild, launch observers, or change acceptance. Paired-build procedure remains withheld because inventory is incomplete.

Historical ETW-loss causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.

## Method references and limits

Microsoft API-set loader model: https://learn.microsoft.com/en-us/windows/win32/apiindex/api-set-loader-operation

Microsoft documented query: https://learn.microsoft.com/en-us/windows/win32/api/apiquery2/nf-apiquery2-getapisetmodulebasename

Implementation cross-check (not a Microsoft specification): Wine ntdll loader get_apiset_entry/get_apiset_target, https://github.com/wine-mirror/wine/blob/master/dlls/ntdll/loader.c. Independently implemented hash-index/hashed-length matching and importer selection, bounded to tested namespace v6. No external code was executed. Current-host regression and adversarial fixtures validate this successor within its stated scope.

Archive status is in archive-verification.json. Every archive member is checked against its pre-archive digest. This archive preserves a stopped offline attempt; it is not Stage 6 acceptance.
