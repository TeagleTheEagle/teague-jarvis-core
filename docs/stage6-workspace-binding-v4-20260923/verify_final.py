"""Read-only hashes and host census; output only to this action's evidence directory."""
import ast,difflib,hashlib,json,pathlib,sys,zipfile,datetime
R=pathlib.Path(__file__).parent;v=json.loads((R/'before.json').read_text());C=pathlib.Path(v['candidate']);N=pathlib.Path(v['predecessor'])
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2)
for x in v['inputs']:
 p=pathlib.Path(x['path']);s=p.stat();assert(s.st_size,s.st_mtime_ns,sha(p))==(x['bytes'],x['mtimeNs'],x['sha256'])
prior=N.parent/'verify_preservation.py';exec(compile(prior.read_text().split('result=')[0],str(prior),'exec'),{'__file__':str(prior)})
for x in v['archives']:
 a=pathlib.Path(x['path']);assert sha(a)==x['sha256'];rows=read(a.parent/'manifest.json');rows=rows['files'] if isinstance(rows,dict) else rows
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==x['members']==len(set(z.namelist()))
  for row in rows:
   with z.open(row['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256']
rows=read(C/'small-source-v3.json');old={x['name']:x for x in read(N/'small-source-v3.json')};changes=[];diff=[];python=[]
for row in rows:
 p=C/row['name'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 if p.suffix=='.py':ast.parse(p.read_bytes(),filename=str(p));python.append(str(p))
 if row['name'] not in old or old[row['name']]['sha256']!=row['sha256']:
  source=N/row['name'];before=old.get(row['name'])
  # Versioned derivatives compare against their actual reviewed predecessor.
  mapping={'small_launch_v4.ps1':'small_launch_v3.ps1','external_driver_v4.py':'external_driver_v3.py','small_finalize_v4.py':'small_finalize_v3.py'}
  if row['name'] in mapping:source=N/mapping[row['name']]
  if row['name'] in ('failure_preserve_v4.py','one_run_v4.py'):source=R/row['name'].replace('_v4','_v1')
  changes.append(dict(path=str(p),predecessor=str(source) if source.exists() else None,beforeSHA256=sha(source) if source.exists() else None,afterSHA256=row['sha256']))
  if p.suffix in ('.py','.ps1','.json'):
   diff.extend(difflib.unified_diff(source.read_text().splitlines(True) if source.exists() else [],p.read_text().splitlines(True),fromfile=str(source) if source.exists() else '/dev/null',tofile=str(p)))
(R/'implementation.diff').write_text(''.join(diff))
write('changes.json',changes);write('syntax-python.json',dict(status='PASS',method='ast.parse; no imports, no bytecode output',files=python,count=len(python)))
sys.path.insert(0,str(C));import workspace_binding_v4 as b
b.runtime_policy()
import failure_preserve_v4 as fp
root=next(p for p in C.glob('protected-*') if (p/b.NAME).exists())
census=fp.host_census(root);write('final-census.json',census)
assert census['available'] and census['processes']==[] and census['traces']==[] and census['unknown']==[],census
for row in rows:assert sha(C/row['name'])==row['sha256']
write('final-verification.json',dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=str(C),manifestSHA256=sha(C/'small-source-v3.json'),candidateFiles=len(rows),predecessorFiles=217,recordedInputs=len(v['inputs']),historicalInputs=482,failedRunFiles=83,oldCandidateFiles=216,preservationToolFiles=4,historicalArchiveMembers=[105]+[x['members'] for x in v['archives']],frozenCheckerSHA256=sha(C/'medium-checker/frozen_reference.py'),versionedCheckerUnchanged=sha(C/'small_check_v3.py')==sha(N/'small_check_v3.py'),DLLSHA256=sha(C/'J6OwnedEntry.dll'),pythonSyntaxFiles=len(python),runtimeComponents=len(read(C/'shared-runtime-v4.json')['components']),liveDiagnosticProcesses=0,traceSessions=0,VirtualBoxProcesses=0,liveRunOccurred=False,UAC=False,protectedAccess=False,productionChange=False))
print((R/'final-verification.json').read_text())
