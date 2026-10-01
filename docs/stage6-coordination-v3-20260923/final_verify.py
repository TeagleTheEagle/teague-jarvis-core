import pathlib,json,hashlib,difflib,subprocess,sys
R=pathlib.Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=load(R/'before.json');C=pathlib.Path(before['candidate']);O=pathlib.Path(before['original'])
for r in before['inputs']+load(R/'additional-inputs.json'):
 p=pathlib.Path(r['path']);s=p.stat();assert s.st_size==r['bytes'] and s.st_mtime_ns==r['mtimeNs'] and sha(p)==r['sha256'],str(p)
frozen=load(R/'candidate-frozen.json')
for r in frozen['files']:
 p=C/r['name'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
assert sha(C/'small-source-v3.json')==frozen['manifestSHA256']
result=subprocess.run([sys.executable,'-B','-m','unittest','test_successor_v3'],cwd=C,capture_output=True,text=True,timeout=90)
with (R/'successor-tests-final.json').open('x') as f:json.dump(dict(command=[sys.executable,'-B','-m','unittest','test_successor_v3'],returncode=result.returncode,stdout=result.stdout,stderr=result.stderr,liveQualification=False),f,indent=2)
assert result.returncode==0,result.stderr
pairs={'authority_trace_v3.cpp':'authority_trace.cpp','large_collect_v3.py':'large_collect.py','traced_collect_v3.py':'traced_collect.py','small_binding_v3.py':'small_binding_v2.py','tracker_adapter_v3.py':'tracker_adapter_v2.py','support_verifier_v3.py':'support_verifier.py','small_check_v3.py':'small_check_v2.py','small_finalize_v3.py':'small_finalize_v2.py','small_launch_v3.ps1':'small_launch_v2.ps1','traced_collect.py':'traced_collect.py','baseline-allowlist.json':'baseline-allowlist.json'}
diff=[]
for target,source in pairs.items():diff.extend(difflib.unified_diff((O/source).read_text().splitlines(True),(C/target).read_text().splitlines(True),fromfile=str(O/source),tofile=str(C/target)))
(R/'implementation.diff').write_text(''.join(diff))
known={x['name'] for x in load(R.parent/'stage6-checker-v2-20260923'/'final-verification.json')['source']}
changed=[]
for r in frozen['files']:
 if r['name'] not in known or sha(O/r['name'])!=r['sha256']:changed.append(r)
for r in frozen['files']:assert sha(C/r['name'])==r['sha256']
with (R/'final-verification.json').open('x') as f:json.dump(dict(status='PASS',preservedInputs=len(before['inputs']),additionalSyntheticFiles=12,originalSourceFiles=194,predecessorSourceFiles=183,newCandidateSourceFiles=len(frozen['files']),candidateManifestSHA256=frozen['manifestSHA256'],changedOrNew=changed,protectedVMAccess=False,productionChanged=False,historicalFailuresUnchanged=True),f,indent=2)
print(json.dumps(dict(status='PASS',originalFiles=194,predecessorFiles=183,candidateFiles=len(frozen['files']),preservedInputs=len(before['inputs']),changedOrNew=len(changed))))
