import pathlib,json,subprocess,sys,uuid
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate'])
attempt=R/('offline-'+uuid.uuid4().hex);attempt.mkdir()
steps=[([sys.executable,'-B',str(R/'freeze.py')],R),([sys.executable,'-B',str(C/'test_binding_v4.py')],C)]
for i,(args,cwd) in enumerate(steps):
 p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,timeout=240)
 with (attempt/(str(i)+'.json')).open('x') as f:json.dump(dict(args=args,cwd=str(cwd),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,liveRun=False),f,indent=2)
 print(p.stdout,p.stderr)
 if p.returncode:raise SystemExit(p.returncode)
print('OFFLINE_REPORT '+str(attempt))
