import pathlib,json,hashlib,difflib,ast
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);before=json.loads((R/'frozen-before.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for x in before['candidateHashes']:
 assert sha(pathlib.Path(x['path']))==x['expected'];assert sha(C/x['name'])==x['expected']
names={x['name'] for x in before['candidateHashes']}|{p.name for p in C.glob('baseline*') if p.is_file() and p.suffix in ('.py','.ps1','.cpp','.json')}|{'test_baseline.py','J6BaselineTrace.exe'}
names.discard('baseline-source.json')
for n in names:
 if n.endswith('.py'):ast.parse((C/n).read_text())
manifest=[dict(name=n,sha256=sha(C/n)) for n in sorted(names)]
for path in (C/'baseline-source.json',R/'candidate-source.json'):
 with path.open('x') as f:json.dump(manifest,f,indent=2)
pairs=[('dry_collect.py','baseline_collect.py'),('dry_finalize.py','baseline_finalize.py'),('dry_launch.ps1','baseline_launch.ps1'),('app_monitor.ps1','baseline_monitor.ps1'),('kernel_trace.cpp','baseline_kernel_trace.cpp')]
diff=''.join(''.join(difflib.unified_diff((C/a).read_text().splitlines(True),(C/b).read_text().splitlines(True),fromfile=a,tofile=b)) for a,b in pairs)
with (R/'adapter-diff.patch').open('x') as f:f.write(diff)
with (R/'preservation.json').open('x') as f:json.dump(dict(original73Unchanged=True,sacrificial73Unchanged=True,candidateFiles=len(manifest),protectedAccess=False),f,indent=2)
print(json.dumps(dict(candidateFiles=len(manifest),original73Unchanged=True,syntax='PASS')))
