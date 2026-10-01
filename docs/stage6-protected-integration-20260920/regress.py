import pathlib,json,subprocess,os,sys,uuid,shutil,hashlib
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code']);old=pathlib.Path(json.loads((R/'candidate.json').read_text())['old'])
fixture='dual-9aa6b84f76074c83956a1cb4fad811bc'
if not (C/fixture).exists():shutil.copytree(old/fixture,C/fixture)
for p in (old/fixture).rglob('*'):
 if p.is_file():assert hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256((C/fixture/p.relative_to(old/fixture)).read_bytes()).hexdigest()
out=C/('baseline-regress-'+uuid.uuid4().hex);out.mkdir();(out/'temp').mkdir()
env=dict(os.environ,TEMP=str(out/'temp'),TMP=str(out/'temp'),PYTHONDONTWRITEBYTECODE='1');py=sys.executable;ps=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
commands=[('baseline',[py,'-B','-m','unittest','-v','test_baseline']),('integration',[py,'-B','-m','unittest','-v','test_dry_integration']),('dual',[py,'-B','-m','unittest','-v','test_dual_cleanup']),('kernel',[py,'-B','test_reconcile.py']),('hardening',[py,'-B','-m','unittest','-v','test_hardening','test_tree_reconcile']),('probe',[py,'-B','run_probe_policy.py']),('monitor',[py,'-B','run_focused.py']),('queue',[ps,'-NoProfile','-File','test_queue.ps1']),('finalization',[ps,'-NoProfile','-File','test_finalization_gate.ps1'])]
results=[]
for name,args in commands:
 with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:q=subprocess.run(args,cwd=C,env=env,stdout=stdout,stderr=stderr)
 result=dict(name=name,command=args,exit=q.returncode);results.append(result);print(json.dumps(result),flush=True)
 if q.returncode:break
with (out/'results.json').open('x') as f:json.dump(results,f,indent=2)
with (R/('regress-'+out.name+'.json')).open('x') as f:json.dump(dict(directory=str(out),results=results),f,indent=2)
raise SystemExit(any(x['exit'] for x in results))
