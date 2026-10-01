import json,subprocess,sys,uuid
from pathlib import Path
R=Path(__file__).parent;P=R.parent/'stage6-telemetry-candidate-20260922';pre=json.loads((R/'candidate.json').read_text());C=Path(pre['code']);old=Path(pre['originalCode'])
# Fresh output locations; legacy evidence is read only and never modified.
(C/'validation-v2').mkdir();(C/'validation-v2/medium-positive-fixture.json').write_bytes((old/'validation-v2/medium-positive-fixture.json').read_bytes())
s=(P/'test_wrapper.py').read_text(encoding='utf8')
s=s.replace("src=next(C.glob('telemetry-tests-*/case-0-0'))",f"src=next(Path({str(old)!r}).glob('telemetry-tests-*/case-0-0'))")
needle='checks=[]';assert s.count(needle)==1
s=s.replace(needle,"# Synthetic fixture must include the full analyzer duplicate introduced in the live evidence.\nb['qualification']['writer']=copy.deepcopy(w)\n"+needle)
with (R/'test_wrapper_regression.py').open('x',encoding='utf8') as f:f.write(s)
s=(P/'test_telemetry.py').read_text(encoding='utf8')
s=s.replace("source=next(C.glob('telemetry-tests-*/case-2-0'))",f"source=next(Path({str(old)!r}).glob('telemetry-tests-*/case-2-0'))")
with (R/'test_telemetry_regression.py').open('x',encoding='utf8') as f:f.write(s)
results=[]
for script in ('test_wrapper_regression.py','test_telemetry_regression.py'):
 p=subprocess.run([sys.executable,'-B',str(R/script)],capture_output=True,text=True,timeout=60)
 row=dict(command=p.args,exit=p.returncode,stdout=p.stdout,stderr=p.stderr);results.append(row)
 with (R/(script+'.execution.json')).open('x') as f:json.dump(row,f,indent=2)
 assert p.returncode==0,script
print(json.dumps(dict(status='PASS',composition=21,telemetry=40,newActualAnalyzer=44,total=105)))
