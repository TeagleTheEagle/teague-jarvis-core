"""Execute the one owner-authorized attempt; no retry or implementation changes."""
import pathlib,os,sys,json,hashlib,datetime
R=pathlib.Path(__file__).parent
v=json.loads((R/'preflight-result.json').read_text());assert v['status']=='PASS'
C=pathlib.Path(v['candidate']);root=pathlib.Path(v['runRoot'])
with (R/'launch-once.json').open('x') as f:json.dump(dict(run=v['run'],utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),ownerApproved=True,attempt=1),f)
os.chdir(C);sys.path[0]=str(C)
import workspace_binding_v4 as b
p=b.runtime_policy()
for key in ('PYTHONHOME','PYTHONPATH','PYTHONSTARTUP'):assert not os.environ.get(key)
os.environ['PATH']=os.pathsep.join(dict.fromkeys(str(pathlib.Path(x['path']).parent) for x in p['executables'].values()))
os.environ['PSModulePath']=os.pathsep.join(p['moduleRoots']);os.environ['PYTHONNOUSERSITE']='1'
os.environ['TEMP']=os.environ['TMP']=str(root/'temp')
assert b.sha(root/b.NAME)==v['workspaceBindingSHA256'];b.verify(root)
import one_run_v4 as w, failure_preserve_v4 as f
result=w.execute(v['run'],f.cli_policy(v['run']),approved=True)
with (R/'run-result.json').open('x') as out:json.dump(result,out,indent=2)
print(json.dumps(result,sort_keys=True),flush=True)
sys.exit(0 if result.get('route')=='SUCCESS_FINALIZER_COMPLETED' else 1)
