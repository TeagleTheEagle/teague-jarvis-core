from prepare_pair import *
import zipfile

before=read('preservation-before.json')
verify(before['files'])
current={}
for root in before['roots']:
 for row in tree(root):current[row['path']]=row
assert current=={r['path']:r for r in before['files']},'Preserved inventory changed'
save('preservation-after.json',{'status':'PASS','files':len(current),'beforeSHA256':digest(HERE/'preservation-before.json'),'identicalContentsSizesModificationTimes':True,'identicalInventory':True,'authoritySHA256':digest(CAND/'J6AuthorityTraceV3.exe'),'historicalDetailedSHA256':digest(CAND/'J6StartupTrace.exe'),'productionTouched':False,'protectedVMTouched':False,'ETWStarted':False,'UACRequested':False,'controlBuildAttempts':0,'treatmentBuildAttempts':0})
save('first-failure.json',{'status':'TOOLCHAIN_PROVENANCE_INCOMPLETE','phase':1,'script':'freeze_inputs.py','exception':'RuntimeError: Unbounded API-set input api-ms-win-core-errorhandling-l1-1-0.dll','exitCode':1,'classification':'Preparation-tool dependency-resolution coverage incomplete; not proof of a missing Windows component or JARVIS defect.','permittedInputManifestCompleted':False,'partialInputHashesPersisted':False,'controlBuildAttempts':0,'treatmentBuildAttempts':0,'noRetry':True,'noResolverCorrection':True})
report='''# TOOLCHAIN_PROVENANCE_INCOMPLETE

Offline preparation stopped in Phase 1 before either CONTROL or TREATMENT was built. No source delta or arm directories were created. No observer binary was executed; no ETW, UAC, tests, VM access, or production operation occurred.

## First failure

The preparation tool enumerated and hashed the requested MSVC/SDK roots in memory, then failed while resolving the transitive PE dependency closure:

`RuntimeError: Unbounded API-set input api-ms-win-core-errorhandling-l1-1-0.dll`

The resolver performed an exact API-set-name lookup in the parsed host schema and did not produce a target. This does not establish that the Windows loader would fail, that a physical DLL is missing, or that the SDK is defective. Version/alias semantics of the API-set resolution remain unreviewed. The missing permitted-input manifest is not treated as complete evidence. Intermediate input hashes existed only in the stopped process and were not persisted. No retry, resolver modification, or build followed.

## Recorded provenance

- MSVC toolset directory: 14.44.35207.
- Compiler file version: 19.44.35228.0.
- Compiler SHA-256: `88c8344236a27a6e727e0a8edc49aaa2690bdc7a9464b9d18cc7abe70a9f1c0d`.
- Linker file version: 14.44.35228.0.
- Linker SHA-256: `ca11e6c45debd34bf652dfe984c5360a531a005ed78bf72852330c9c2590cf0d`.
- Windows SDK selected by environment setup: 10.0.26100.0.
- SDK/input inventory identity: NOT PRODUCED; Phase 1 incomplete.
- Environment/setup command, setup script hash, compiler/backend versions/hashes recorded in the adjacent JSON files.
- `shared/evntrace.h` statically declares REAL_TIME=0x00000100, SYSTEM_LOGGER=0x02000000 and INDEPENDENT_SESSION=0x08000000. No code was changed.
- Intended requested modes remain CONTROL 0x02000100; TREATMENT 0x0A000100; authority 0x08000100. They are intended values, not new build outputs.

## Outputs and preservation

- CONTROL detailed binary/hash/manifest: NOT CREATED.
- TREATMENT detailed binary/hash/manifest: NOT CREATED.
- CONTROL build attempts: 0. TREATMENT build attempts: 0.
- Authority not rebuilt. SHA-256: `c405202381a2fed890512c553cc8b631cfc2f03e4d2ef955aa8f236d02949aef`.
- Historical detailed SHA-256: `5225e63c654a63fff05e4002475e8caae5910d4d11822a13119bf2791fc35634`.
- 992 preserved files verified with identical inventory, contents, sizes and modification timestamps. Scope: current candidate/live-run tree and the historical preparation, witness, authority-independent, live-result and result-review directories recorded in preservation-before.json. This is not a claim that every historical archive in the repository was rehashed.
- Frozen checker/finalizer and helper/witness material within the recorded candidate remain unchanged.
- Protected VM touched: NO. Production touched: NO. ETW/live run: NO.
- Two preliminary read-only searches used incorrect glob/header paths; corrected file-location queries succeeded. Neither launched a build or changed a source file.

## Next proposed action — owner review only

Review the preparation tool's API-set import-resolution method and the minimum supported evidence needed to bind compiler/linker OS dependencies. Determine whether the exact-name lookup incorrectly treats a resolvable API-set contract as an unbounded input. Do not modify the resolver, invent a mapping, run either observer, or rebuild during that review. A separately approved correction may later prepare a fresh inventory without changing JARVIS or ETW settings.

No executable two-run procedure is issued because no qualified prospective pair exists. The planned CONTROL then TREATMENT live comparison remains separately gated.

Historical failed runs remain FAILED. Historical ETW-loss causes remain UNCONFIRMED. HISTORICAL STAGE 1 CAUSE: UNCONFIRMED.
'''
with (HERE/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
files=sorted(p for p in HERE.iterdir() if p.is_file())
entries=[{'name':p.name,'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]
save('archive-manifest.json',{'status':'NON-ACCEPTANCE BLOCKED PREPARATION','members':entries})
files.append(HERE/'archive-manifest.json')
with zipfile.ZipFile(HERE/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.name)
with zipfile.ZipFile(HERE/'evidence.zip') as z:
 assert z.testzip() is None
 for p in files:assert hashlib.sha256(z.read(p.name)).hexdigest()==digest(p)
save('archive-verification.json',{'status':'PASS','verifiedMembers':len(files),'archiveSHA256':digest(HERE/'evidence.zip'),'manifestSHA256':digest(HERE/'archive-manifest.json')})
print(json.dumps({'status':'TOOLCHAIN_PROVENANCE_INCOMPLETE','preservationFiles':len(current),'archiveMembers':len(files),'archiveSHA256':digest(HERE/'evidence.zip'),'report':str(HERE/'REPORT.md')}))
