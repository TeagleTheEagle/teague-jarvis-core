import pathlib,subprocess,json,sys,os,uuid,time
code=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\991e246fb08b45a3904e4cadfa8f4e99\code');r=code/('kernel-regress-'+uuid.uuid4().hex);r.mkdir();(r/'temp').mkdir();env=dict(os.environ,TEMP=str(r/'temp'),TMP=str(r/'temp'),PYTHONDONTWRITEBYTECODE='1')
py=sys.executable;ps=r'C:\Users\jonny\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
commands=[('reconcile',[py,'-B','test_reconcile.py']),('hardening',[py,'-B','-m','unittest','-v','test_hardening','test_tree_reconcile']),('probe',[py,'-B','run_probe_policy.py']),('monitor',[py,'-B','run_focused.py']),('queue',[ps,'-NoProfile','-File','test_queue.ps1']),('finalization',[ps,'-NoProfile','-File','test_finalization_gate.ps1'])]
results=[]
for name,args in commands:
 start=time.monotonic()
 with (r/(name+'.stdout')).open('xb') as out,(r/(name+'.stderr')).open('xb') as err:
  p=subprocess.run(args,cwd=code,env=env,stdout=out,stderr=err)
 x=dict(name=name,command=args,cwd=str(code),exit=p.returncode,seconds=time.monotonic()-start);results.append(x)
 with (r/(name+'.json')).open('x') as f:json.dump(x,f,indent=2)
 print(json.dumps(x),flush=True)
 if p.returncode:break
with (r/'results.json').open('x') as f:json.dump(results,f,indent=2)
print(r)
