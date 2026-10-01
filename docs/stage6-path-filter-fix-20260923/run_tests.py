import pathlib,subprocess,sys,json,ast,uuid
R=pathlib.Path(__file__).parent;out=R/('focused-'+uuid.uuid4().hex);out.mkdir()
files=list(R.glob('*.py'))
for p in files:ast.parse(p.read_bytes(),filename=str(p))
(out/'syntax.json').write_text(json.dumps(dict(status='PASS',files=[str(p) for p in files],method='ast.parse; no bytecode output'),indent=2))
args=[sys.executable,'-B',str(R/'test_dataset_filter.py')]
p=subprocess.run(args,cwd=R,capture_output=True,text=True,timeout=60)
(out/'tests.json').write_text(json.dumps(dict(args=args,cwd=str(R),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,liveRun=False),indent=2))
print(p.stdout,p.stderr,'EVIDENCE '+str(out));raise SystemExit(p.returncode)
