"""Explicitly authorized retained TEST cleanup; verify pinned handle before termination."""
from pathlib import Path
import ctypes as c,json,sys,hashlib
D=Path(__file__).resolve().parent;R=D.parents[1]
old=R/'docs/stage5-accepted-baseline-20260917';app=Path(json.loads((old/'baseline.json').read_text())['app'])
root=Path(json.loads((D/'actual-client-1903d5b3d8814cb29fdc417646558add.json').read_text())['roots'][0])
sys.path.insert(0,str(app/'tests/lifecycle_stage2'));import pipe_transport as t
assert (root/'TEST_ONLY').read_text()=='NO PRODUCTION SERVICES'
event={'identity':json.loads((root/'stage4-ready.json').read_text())['identity'],'coordinator':json.loads(next(root.glob('coordinator-*.json')).read_text())['peer']}
assert event['identity']['namespace']==root.name
t.api(t.k,'TerminateProcess',[t.H,t.D])
records=[]
for pin in (event['identity'],event['coordinator']):
    pin={k:pin[k] for k in ('pid','created','exe_digest')}
    try:live=t.identity(pin['pid'])
    except Exception as e:
        if getattr(e,'errno',None)!=87 and str(e)!='PROCESS_DEAD':raise
        records.append({'identity':pin,'result':'ALREADY_EXITED'});continue
    if live!=pin:
        records.append({'identity':pin,'result':'PID_REUSED_NOT_TERMINATED','current':live});continue
    h=t.check(t.k.OpenProcess(0x100001|0x1000,False,pin['pid']))
    try:
        times=[t.w.FILETIME() for _ in range(4)];t.check(t.k.GetProcessTimes(h,*map(c.byref,times)))
        assert (times[0].dwHighDateTime<<32)|times[0].dwLowDateTime==pin['created']
        path=c.create_unicode_buffer(32768);size=t.D(len(path));t.check(t.k.QueryFullProcessImageNameW(h,0,path,c.byref(size)))
        assert hashlib.sha256(Path(path.value).read_bytes()).hexdigest()==pin['exe_digest']
        t.check(t.k.TerminateProcess(h,94));assert t.k.WaitForSingleObject(h,5000)==0
        records.append({'identity':pin,'result':'IDENTITY_VERIFIED_TEST_TERMINATION','reason':'Original controller exited; private in-memory authentication credentials unavailable; previous authenticated cleanup failed.'})
    finally:t.k.CloseHandle(h)
(D/'packaged-failure-cleanup.json').write_text(json.dumps(records,indent=2))
# Retire only this exited coordinator's readiness metadata, preserving its bytes.
for p in root.glob('coordinator-*.json'):
    data=json.loads(p.read_text());assert data['peer']['pid']==15220
    try:assert t.identity(15220)!=data['peer']
    except Exception as e:
        if getattr(e,'errno',None)!=87 and str(e)!='PROCESS_DEAD':raise
    target=D/('retired-'+p.name);target.write_bytes(p.read_bytes());assert target.read_bytes()==p.read_bytes();p.unlink()
print(json.dumps(records))
