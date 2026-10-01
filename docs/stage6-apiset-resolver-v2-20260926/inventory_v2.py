"""Read-only input inventory only. No compiler/linker/observer is executed."""
import datetime, json, os, stat, sys, time, traceback
from pathlib import Path
from resolver_v2 import *

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'stage6-prospective-pair-20260926'
VS=Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools')
E=json.loads((OLD/'initialized-environment.json').read_text())
BIN=Path(E['VCToolsInstallDir'])/'bin/Hostx64/x64'
SYSTEM=Path(E['SystemRoot'])/'System32'
SCHEMA_PATH=Path(json.loads((HERE/'host-before.json').read_text())['schema_path'])
RUNTIME='BUILD_TOOL_RUNTIME_DEPENDENCY'

def save(name,data):
 with (HERE/name).open('x',encoding='utf-8',newline='\n') as f:
  json.dump(data,f,indent=2,sort_keys=True);f.write('\n')

def stable_record(p):
 p=Path(p);before=p.stat();r=identity(p);after=p.stat()
 if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
  raise ProvenanceError('Input changed while hashing: '+str(p))
 return {**r,'mtime_ns':after.st_mtime_ns}

def environment():
 if json.loads((HERE/'focused-result.json').read_text())['exit_code']!=0:
  raise ProvenanceError('Focused tests have not passed')
 if any(E.get(k) for k in ['CL','_CL_','LINK']):raise ProvenanceError('Injected build flags')
 check_binding(host_binding(SCHEMA_PATH),json.loads((HERE/'host-before.json').read_text()))
 for r in json.loads((OLD/'tool-versions.json').read_text()):
  if sha(BIN/r['Name'])!=r['SHA256'].lower():raise ProvenanceError('Toolchain drift: '+r['Name'])
 return SchemaV6.from_file(SCHEMA_PATH)

def edge(schema,p,row):
 r=import_evidence(p,row,RUNTIME)
 if r['kind']=='API_SET_CONTRACT':
  mapping=resolve_contract(schema,row['exact_name'],p)
  target=resolve_physical(mapping['host'],p,BIN,SYSTEM)
  r['mapping']=mapping
 else:target=resolve_physical(row['exact_name'],p,BIN,SYSTEM)
 r['selected_host']={'classification':RUNTIME,**target}
 return r

def regression():
 schema=environment();edges=[]
 for name,nextname in [('mspdbcore.dll','msobj140.dll'),('msobj140.dll','tbbmalloc.dll')]:
  p=BIN/name;rows=[r for r in PE(p).imports() if r['exact_name'].lower()==nextname]
  if len(rows)!=1:raise ProvenanceError('Regression chain not unique: '+name)
  edges.append(edge(schema,p,rows[0]))
 # Retain the actual CRT contract names instead of inventing a direct physical import.
 crt=[]
 for row in PE(BIN/'tbbmalloc.dll').imports():
  if row['exact_name'].lower().startswith(('api-ms-win-crt-', 'ucrtbase.')):
   r=edge(schema,BIN/'tbbmalloc.dll',row)
   if Path(r['selected_host']['path']).name.lower()=='ucrtbase.dll':crt.append(r)
 if not crt:raise ProvenanceError('No evidenced tbbmalloc -> ucrtbase mapping')
 edges.extend(crt)
 p=Path(crt[0]['selected_host']['path']);contract='api-ms-win-core-errorhandling-l1-1-0.dll'
 rows=[r for r in PE(p).imports() if r['exact_name']==contract and r['import_kind']=='NORMAL']
 if len(rows)!=1:raise ProvenanceError('Exact UCRT regression import not found')
 result=edge(schema,p,rows[0]);edges.append(result)
 save('blocker-regression.json',{'status':'PASS','edges':edges,'current_case':result,
  'schema':{'classification':'CURRENT_HOST_MAPPING','version':schema.version,
    'identity':schema.source,'host_binding':host_binding(SCHEMA_PATH)},
  'function_destinations':{'classification':'CORROBORATIVE_ONLY','used_as_mapping_proof':False,
    'new_function_observation_performed':False},
  'same_name_physical_api_set_required':False,'builds_performed':False})
 print('BLOCKER_REGRESSION_PASS',result['mapping']['method'],result['selected_host']['path'],flush=True)

def inventory():
 schema=environment()
 if json.loads((HERE/'blocker-regression.json').read_text())['status']!='PASS':raise ProvenanceError('Regression prerequisite')
 incs=[Path(p) for p in E['INCLUDE'].split(';') if p]
 libs=[Path(p) for p in E['LIB'].split(';') if p]
 roots=[(BIN,RUNTIME),*[(p,'BUILD_INPUT_REQUIRED') for p in incs+libs],
        (VS/'Common7/Tools/vsdevcmd',RUNTIME),(VS/'VC/Auxiliary/Build',RUNTIME)]
 rows={};resolution=[];seen=set();pending=[];failure=None;phase='ROOT_INVENTORY';current=None
 started=time.monotonic()
 def add(p,classification):
  key=str(Path(p).resolve()).casefold()
  if key not in rows:
   r=stable_record(p);rows[key]={**r,'classification':classification}
   journal.write(json.dumps(rows[key],sort_keys=True)+'\n');journal.flush()
  elif rows[key]['classification']!=classification:
   raise ProvenanceError('Conflicting provenance class: '+key)
 with (HERE/'input-records.jsonl').open('x',encoding='utf-8') as journal:
  try:
   for root,classification in roots:
    current=str(root)
    if not root.is_dir():raise Unresolved('Required root absent: '+str(root))
    print('INVENTORY_ROOT',str(root),flush=True)
    for base,dirs,files in os.walk(root,followlinks=False):
     dirs.sort();files.sort()
     for name in dirs+files:
      p=Path(base)/name
      if p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:raise ProvenanceError('Reparse input: '+str(p))
     for name in files:add(Path(base)/name,classification)
   for p in [VS/'Common7/Tools/VsDevCmd.bat',OLD/'capture-env.cmd',Path(sys.executable),SYSTEM/'cmd.exe']:
    add(p,RUNTIME)
   add(SCHEMA_PATH,'CURRENT_HOST_MAPPING')
   phase='TRANSITIVE_BUILD_TOOL_RUNTIME_CLOSURE'
   pending=[BIN/n for n in ['cl.exe','link.exe','c1xx.dll','c2.dll','mspdb140.dll','mspdbcore.dll'] if (BIN/n).is_file()]
   while pending:
    p=pending.pop();key=str(p.resolve()).casefold()
    if key in seen:continue
    seen.add(key);add(p,RUNTIME);current={'importer':str(p)}
    for row in PE(p).imports():
     current={'importer':str(p),**row};r=edge(schema,p,row)
     target=Path(r['selected_host']['path']);add(target,RUNTIME)
     resolution.append(r);pending.append(target)
    if len(seen)%20==0:print('RUNTIME_CLOSURE',len(seen),len(resolution),flush=True)
   check_binding(host_binding(SCHEMA_PATH),json.loads((HERE/'host-before.json').read_text()))
  except Exception as exc:
   failure={'type':type(exc).__name__,'message':str(exc),'phase':phase,'current':current,'traceback':traceback.format_exc()}
  finally:
   result={'status':'ANOTHER_PROVENANCE_BLOCKER_FOUND' if failure else 'PROVENANCE_INVENTORY_NOW_COMPLETE',
    'first_failure':failure,'elapsed_seconds':time.monotonic()-started,
    'roots':[{'path':str(p),'classification':c} for p,c in roots],
    'files':sorted(rows.values(),key=lambda x:x['path'].casefold()),'loader_resolution':resolution,
    'counts':{'files_hashed':len(rows),'bytes_hashed':sum(r['bytes'] for r in rows.values()),
      'runtime_images_visited':len(seen),'resolved_import_edges':len(resolution),
      'unresolved_required_dependencies_encountered':int(failure is not None),
      'ambiguous_mappings_encountered':int(bool(failure and failure['type']=='Ambiguous')),
      'resolved_edges_outside_inventory':sum(str(Path(r['selected_host']['path']).resolve()).casefold() not in rows for r in resolution),
      'pending_paths_not_visited':len(pending)},
    'classification_counts':{c:sum(r['classification']==c for r in rows.values()) for c in sorted(CLASSES)},
    'host_mapping':{'classification':'CURRENT_HOST_MAPPING','schema_version':schema.version,'schema':schema.source,
       'os':host_binding(SCHEMA_PATH)},
    'limits':['Inventory roots are a permitted superset; actual compiler/header/link use has not been measured.',
     'Static normal and delay import traversal; no claim every runtime dependency is executed.',
     'No observer output exists for this pair; OUTPUT_RUNTIME_DEPENDENCY closure is deferred until separately approved builds.',
     'Ordinary DLL ordered search preserved: importer directory, VC bin, System32; not a full SxS/Windows loader model.',
     'If first failure exists, remaining closure is unassessed; reported unresolved count is encountered count only.'],
    'control_built':False,'treatment_built':False,'etw_started':False}
   save('inventory-result.json',result)
   print(result['status'],json.dumps(result['counts']),flush=True)
   if failure:print('FIRST_FAILURE',failure['message'],flush=True)
 if failure:return 2
 return 0

if __name__=='__main__':
 if sys.argv[1]=='regression':regression()
 elif sys.argv[1]=='inventory':sys.exit(inventory())
 else:raise SystemExit('Only regression or inventory is supported')
