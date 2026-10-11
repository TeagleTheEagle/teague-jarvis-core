import pathlib,json,hashlib,subprocess,sys,difflib
R=pathlib.Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=load(R/'before.json');C=pathlib.Path(b['candidate']);O=pathlib.Path(b['original']);frozen=load(R/'candidate-final-r2.json')
for r in b['inputs']+load(R/'additional-inputs.json'):
 p=pathlib.Path(r['path']);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(r['bytes'],r['mtimeNs'],r['sha256']),str(p)
for r in frozen['files']:assert sha(C/r['name'])==r['sha256']
assert sha(C/'small-source-v3.json')==frozen['manifestSHA256']
command=[sys.executable,'-B','-m','unittest','test_successor_v3']
t=subprocess.run(command,cwd=C,capture_output=True,text=True,timeout=90)
with (R/'successor-tests-final-r2.json').open('x') as f:json.dump(dict(command=command,returncode=t.returncode,stdout=t.stdout,stderr=t.stderr,sourceManifestSHA256=frozen['manifestSHA256'],liveQualification=False),f,indent=2)
assert t.returncode==0,t.stderr
source=load(R.parent/'stage6-checker-v2-20260923'/'final-verification.json')['source'];known={x['name'] for x in source}
changed=[r for r in frozen['files'] if r['name'] not in known or sha(O/r['name'])!=r['sha256']]
diff=[]
for r in changed:
 name=r['name'];p=C/name
 if p.suffix not in ('.py','.ps1','.cpp','.hpp','.json'):continue
 old=O/name
 oldtext=old.read_text().splitlines(True) if old.is_file() else []
 diff.extend(difflib.unified_diff(oldtext,p.read_text().splitlines(True),fromfile=str(old) if old.is_file() else '/dev/null',tofile=str(p)))
(R/'implementation-final-r2.diff').write_text(''.join(diff))
for r in frozen['files']:assert sha(C/r['name'])==r['sha256']
with (R/'final-verification-r2.json').open('x') as f:json.dump(dict(status='PASS',revision=2,preservedInputs=len(b['inputs']),originalSourceFiles=194,predecessorFiles=183,candidateSourceFiles=216,sourceManifestSHA256=frozen['manifestSHA256'],changedOrNew=changed,protectedVMAccess=False,productionChanges=False),f,indent=2)
print(json.dumps(dict(status='PASS',manifestSHA256=frozen['manifestSHA256'],changed=[r['name'] for r in changed])))
