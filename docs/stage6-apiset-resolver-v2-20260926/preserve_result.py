"""Preserve this stopped offline attempt; never resumes dependency traversal."""
import ast, datetime, difflib, hashlib, json, os, stat, zipfile
from pathlib import Path
from resolver_v2 import sha, identity, SchemaV6, normalize_contract, hash_name, host_binding, check_binding
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'stage6-prospective-pair-20260926'

def read(name):return json.loads((HERE/name).read_text(encoding='utf-8-sig'))
def save(name,data):
 with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:
  json.dump(data,f,indent=2,sort_keys=True);f.write('\n')
def record(p):
 p=Path(p);s=p.stat();return {'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)}

before=read('preservation-before.json');preserved=before['files']
bad=[r['path'] for r in preserved if not Path(r['path']).is_file() or record(r['path'])!=r]
if bad:
 save('preservation-failure.json',{'status':'PRESERVATION_FAILURE','paths':bad});raise SystemExit('PRESERVATION_FAILURE')
paths=set()
for root in before['historicalRoots']:
 for base,dirs,files in os.walk(root,followlinks=False):
  for n in dirs+files:
   p=Path(base)/n
   if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise RuntimeError('Reparse in preserved scope')
  paths.update(str(Path(base)/n).casefold() for n in files)
if paths!={r['path'].casefold() for r in preserved}:raise RuntimeError('Preserved inventory changed')
host=read('host-before.json');check_binding(host_binding(host['schema_path']),host)
inv=read('inventory-result.json');reg=read('blocker-regression.json')
for r in inv['files']:
 if record(r['path'])!={k:r[k] for k in ['path','bytes','mtime_ns','sha256']}:raise RuntimeError('Inventory drift: '+r['path'])
schema=SchemaV6.from_file(host['schema_path']);failure=inv['first_failure'];row=failure['current']
name=normalize_contract(row['exact_name']);prefix=name[:name.rfind('-')];hv=hash_name(prefix,schema.factor)
matches=[schema.entries[x['index']] for x in schema.hash_entries if x['hash']==hv
 and schema.entries[x['index']]['hashed_length']==len(prefix)*2
 and schema.entries[x['index']]['hashed_name'].lower()==prefix]
save('first-blocker-evidence.json',{'failure':failure,'importer_identity':identity(row['importer']),
 'indexed_schema_matches':matches,'schema_identity':schema.source,'classification':'BUILD_TOOL_RUNTIME_DEPENDENCY',
 'disposition':'UNRESOLVED; stopped without replacement, omission, or further dependency traversal',
 'build_time_necessity':'UNESTABLISHED; this is a transitive declared DELAY import, not an observed linker input',
 'scope':'Recording the failed lookup only; no optional-dependency rule introduced'})
syntax=[]
for p in sorted(HERE.glob('*.py')):
 ast.parse(p.read_text(encoding='utf-8'),filename=str(p));syntax.append(identity(p))
save('syntax-verification.json',{'status':'PASS','method':'ast.parse; no pycache or imported execution','files':syntax})
save('source-hashes.json',{'files':[identity(p) for p in sorted(HERE.iterdir()) if p.suffix in {'.py','.ps1'}]})
save('preservation-after.json',{'status':'PASS','files':len(preserved),'inventory_identical':True,
 'contents_sizes_mtimes_identical':True,'inventory_inputs_reverified':len(inv['files']),
 'host_binding':host_binding(host['schema_path']),'before_manifest_sha256':sha(HERE/'preservation-before.json'),
 'failed_predecessor_unchanged':True,'historical_scope_unchanged':True,'frozen_checker_finalizer_unchanged':True,
 'authority_unchanged':True,'protected_vm_accessed':False,'production_modified':False,
 'control_builds':0,'treatment_builds':0,'etw_runs':0,'uac_requests':0})
for predecessor,successor,target in [('pe_review.py','resolver_v2.py','resolver-parser.diff'),('freeze_inputs.py','inventory_v2.py','inventory-successor.diff')]:
 diff=''.join(difflib.unified_diff((OLD/predecessor).read_text().splitlines(True),
   (HERE/successor).read_text().splitlines(True),fromfile='preserved-predecessor/'+predecessor,tofile='versioned-successor/'+successor))
 (HERE/target).write_text(diff,encoding='utf-8')
census=read('final-census-host.json')
if census['status']!='PASS':raise RuntimeError('Final census incomplete')
case=reg['current_case'];counts=inv['counts']
report=f'''# ANOTHER_PROVENANCE_BLOCKER_FOUND

## Result

The narrowly scoped API-set correction passed 40/40 focused offline tests and the exact original failed-chain regression. Input inventory stopped at its first different unresolved dependency. Neither prospective observer was built. No live ETW, UAC, VM access, or production change occurred.

## Correction and evidence

New files only: resolver_v2.py, test_resolver_v2.py, run_focused.py, inventory_v2.py, final_census.ps1 and preserve_result.py, plus generated evidence. No predecessor file was edited. resolver-parser.diff and inventory-successor.diff show the versioned replacement comparison, not an in-place modification.

The v6 parser retains schema bounds, HashFactor, sorted hash index, exact hashed-name/length, namespace fields, all values, and importer aliases. Resolution uses indexed-hash plus full hashed-name equality, then the exact importer override or unambiguous default. No version substitution, nearest match, hardcoded host, or all-values expansion occurs. Unsupported layouts, malformed bounds, ambiguous or empty applicable mappings fail closed.

Focused tests: 40 passed / 0 failed. See focused-tests.log. Python syntax checks passed. Missing ordinary physical DLLs still fail; ordered physical search is unchanged (importer directory, VC bin, System32). This is not a complete Windows SxS/loader emulator.

Exact import: `{case['exact_name']}`, NORMAL import of ucrtbase.dll, classified BUILD_TOOL_RUNTIME_DEPENDENCY. The documented query returned E_NOTIMPL (0x80004001). Mapping method: `{case['mapping']['method']}`.

Selected schema entry: `{case['mapping']['selection']['selected_entry']['name']}`; hashed name `{case['mapping']['selection']['selected_entry']['hashed_name']}`, length 68 bytes. Selected default has an empty importer alias and host kernelbase.dll. Host: `{case['selected_host']['path']}`. SHA-256: `{case['selected_host']['sha256']}`.

Host: Windows {host['os']['CurrentBuildNumber']}.{host['os']['UBR']}, {host['architecture']}, schema version 6. Schema: `{host['schema_path']}`. SHA-256: `{host['schema_sha256']}`. Host/schema unchanged from the reviewed preparation. Function-forward destinations were not used as mapping proof or newly probed.

## First unrelated blocker — no scope expansion

Importer: `{row['importer']}`. Exact DELAY import: `{row['exact_name']}`. Symbol: GetCapabilitySidsEx. Failure: `{failure['message']}`. Raw indexed schema selection is preserved in first-blocker-evidence.json. No same-name DLL was invented and no delay import was ignored.

This is a provenance-closure blocker, not evidence that JARVIS, Windows, or the SDK is broken. Whether this declared delayed runtime dependency is required on the prospective build execution path is UNESTABLISHED. Changing that classification requires a separate review. No such change occurred.

Inventory: {counts['files_hashed']} files / {counts['bytes_hashed']} bytes hashed; {counts['resolved_import_edges']} resolved import edges across {counts['runtime_images_visited']} visited images. Encountered unresolved dependencies: 1. Encountered ambiguous mappings: 0. Resolved targets outside inventory: 0. Remaining traversal was stopped and is UNASSESSED ({counts['pending_paths_not_visited']} pending stack entries, not unique modules). These zeros are partial observations, not complete-closure claims.

The six provenance classes remain distinct. File rows: BUILD_INPUT_REQUIRED permitted root superset = 5,730; BUILD_TOOL_RUNTIME_DEPENDENCY = 146; CURRENT_HOST_MAPPING schema file = 1. OS identity is separately CURRENT_HOST_MAPPING. OUTPUT_RUNTIME_DEPENDENCY, CORROBORATIVE_ONLY and NOT_REQUIRED_FOR_BUILD_COMPARABILITY have no newly observed file rows. No observer output exists to inspect. Runtime-only edges do not enlarge BUILD_INPUT_REQUIRED.

## Preservation and cleanup

All {len(preserved)} preserved files retain identical inventory, SHA-256, size and modification time. Scope is exactly preservation-before.json: current authority-independent candidate and six prior evidence/preparation trees. This is not a claim that every historical repository archive was rehashed. All {len(inv['files'])} captured inventory inputs were reverified unchanged. Frozen checker/finalizer, detailed observer, authority, witness and handoff are unchanged.

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
'''
with (HERE/'REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
files=sorted(p for p in HERE.rglob('*') if p.is_file())
members=[{'name':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
save('archive-manifest.json',{'status':'NON-ACCEPTANCE; ANOTHER_PROVENANCE_BLOCKER_FOUND','members':members})
files.append(HERE/'archive-manifest.json')
with zipfile.ZipFile(HERE/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(HERE).as_posix())
with zipfile.ZipFile(HERE/'evidence.zip') as z:
 if z.testzip() is not None:raise RuntimeError('Archive CRC failure')
 for p in files:
  if hashlib.sha256(z.read(p.relative_to(HERE).as_posix())).hexdigest()!=sha(p):raise RuntimeError('Archive hash mismatch')
save('archive-verification.json',{'status':'PASS','verified_members':len(files),
 'archive_sha256':sha(HERE/'evidence.zip'),'manifest_sha256':sha(HERE/'archive-manifest.json')})
print(json.dumps({'status':'ANOTHER_PROVENANCE_BLOCKER_FOUND','preserved_files':len(preserved),
 'archive_members':len(files),'archive_sha256':sha(HERE/'evidence.zip')}))
