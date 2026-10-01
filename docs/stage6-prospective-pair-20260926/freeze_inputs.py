from prepare_pair import *
from pe_review import inspect,apiset

e=read('initialized-environment.json')
assert not any(e.get(k) for k in ['CL','_CL_','LINK']), 'Unreviewed injected build flags'
vc=Path(e['VCToolsInstallDir']);binroot=vc/'bin/Hostx64/x64';sysroot=Path(e['SystemRoot'])/'System32'
assert (binroot/'cl.exe').is_file() and (binroot/'link.exe').is_file()
incs=[Path(p) for p in e['INCLUDE'].split(';') if p];libs=[Path(p) for p in e['LIB'].split(';') if p]
roots=[binroot,*incs,*libs,VS/'Common7/Tools/vsdevcmd',VS/'VC/Auxiliary/Build']
rows={}
for root in roots:
 print('INVENTORY',str(root),flush=True)
 for r in tree(root):rows[r['path'].casefold()]=r
for p in [VS/'Common7/Tools/VsDevCmd.bat',HERE/'capture-env.cmd',PYTHON,sysroot/'cmd.exe',sysroot/'apisetschema.dll']:
 rows[str(p).casefold()]=record(p)
api=apiset(sysroot/'apisetschema.dll');resolution=[];pending=[binroot/n for n in ['cl.exe','link.exe','c1xx.dll','c2.dll','mspdb140.dll','mspdbcore.dll'] if (binroot/n).is_file()];seen=set()
while pending:
 p=pending.pop();key=str(p).casefold()
 if key in seen:continue
 seen.add(key);rows[key]=record(p)
 for name in inspect(p)['imports']+inspect(p)['delayImports']:
  candidates=[name]
  if name.lower().startswith(('api-','ext-')):
   candidates=api.get(name.lower().removesuffix('.dll'),[])
   if not candidates:raise RuntimeError('Unbounded API-set input '+name)
  for resolved in candidates:
   if not resolved:continue
   options=[p.parent/resolved,binroot/resolved,sysroot/resolved]
   target=next((q for q in options if q.is_file()),None)
   if not target:raise RuntimeError('Unbounded PE dependency '+resolved)
   resolution.append({'importer':str(p),'requested':name,'resolved':str(target)})
   pending.append(target)
save('permitted-inputs.json',{'roots':list(map(str,roots)),'files':sorted(rows.values(),key=lambda r:r['path'].casefold()),'loaderResolution':resolution,'os':platform.platform(),'apiSetSchema':record(sysroot/'apisetschema.dll'),'notes':['SDK/MSVC input roots fully hashed before builds. Resolved build headers/libs must belong to this inventory.','Compiler/back-end/linker components and transitive PE imports are hashed. API-set resolution bound to recorded OS schema.','No CMake/MSBuild, compiler cache, PCH, supplied object, resource, response file or generated source is used.']})
effective={k:e[k] for k in ['INCLUDE','LIB','SystemRoot','SystemDrive','ComSpec']}
effective.update({'PATH':str(binroot)+';'+str(sysroot),'LIBPATH':'','CL':'','_CL_':'','LINK':'','VSLANG':'1033','TEMP':'<ARM>/temp','TMP':'<ARM>/temp'})
save('effective-environment-template.json',effective)
print('INPUTS_FROZEN',len(rows),sum(r['bytes'] for r in rows.values()),'bytes',flush=True)
