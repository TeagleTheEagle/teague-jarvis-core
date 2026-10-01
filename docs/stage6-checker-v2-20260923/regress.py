import pathlib,json,shutil,subprocess,sys,uuid,hashlib
R=pathlib.Path(__file__).resolve().parent;C=pathlib.Path(json.loads((R/'candidate.json').read_text())['code'])
shutil.copy2(R.parent/'stage6-tracker-experiment-20260923/test_tracker.py',C/'test_tracker.py');shutil.copy2(R/'tracker_regression.py',C/'tracker_regression.py')
p=subprocess.run([sys.executable,'-B',str(C/'tracker_regression.py')],cwd=C,capture_output=True,text=True,timeout=90)
with (R/('tracker-tests-'+uuid.uuid4().hex+'.json')).open('x') as f:json.dump(dict(command=[sys.executable,'-B',str(C/'tracker_regression.py')],returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),f,indent=2)
print(p.stdout,p.stderr);raise SystemExit(p.returncode)
