import pathlib,json,subprocess,sys,uuid,os
R=pathlib.Path(__file__).parent;C=pathlib.Path(json.loads((R/'before.json').read_text())['candidate']);O=R/('tests-'+uuid.uuid4().hex);O.mkdir()
steps=sys.argv[1:] or ['test_handoff_v1.py']
env=os.environ.copy();temp=C/('offline-temp-'+uuid.uuid4().hex);temp.mkdir();env['TEMP']=env['TMP']=str(temp)
for name in steps:
 p=subprocess.run([sys.executable,'-B',str(C/name)],cwd=C,env=env,capture_output=True,text=True,timeout=240)
 with (O/(name+'.json')).open('x') as f:json.dump(dict(command=[sys.executable,'-B',str(C/name)],cwd=str(C),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,offline=True),f,indent=2)
 print(name,p.returncode,p.stdout,p.stderr,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
print('EVIDENCE',O)
