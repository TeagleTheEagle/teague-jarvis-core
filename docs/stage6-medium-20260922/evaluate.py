import hashlib,json,os,sys
from pathlib import Path
R=Path(__file__).parent
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
pre=load(R/'preflight.json');C=Path(pre['code']);root=Path(pre['root']);K=Path(pre['checker'])
sys.path[:0]=[str(K),str(C)];import fresh_binding as fb;import checker_medium as checker
assert fb.sha(C/'medium-source-freeze.json')==load(R/'ready.json')['freezeSHA256']
host=R/'final'/(R/'post-host-run.txt').read_text(encoding='utf8').strip()/'final-host-state.json';assert load(host)['status']=='PASS'
with (root/'final-host-state.json').open('xb') as f:f.write(host.read_bytes());f.flush();os.fsync(f.fileno())
intake=fb.seal_intake(C)
try:
 result=checker.evaluate()
except Exception as e:
 with (R/'checker-failure.json').open('x',encoding='utf8') as f:json.dump(dict(status='REJECT',reason=str(e),error=type(e).__name__),f,indent=2)
 raise
with (R/'checker-result.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2);f.flush();os.fsync(f.fileno())
print(json.dumps(dict(status=result['status'],identities=len(result['rules']['identities']),classes=result['rules']['counts'],intakeFiles=len(intake['files']),archivePending=True)))
