from pathlib import Path
import json,hashlib,ctypes
D=Path(__file__).resolve().parent;R=D.parents[1];old=D.parent/'stage6-separated-io-20260917';S=Path(json.loads((old/'source.json').read_text())['source']);digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
preserved=json.loads((D.parent/'stage6-timeout-diagnosis-20260917/preserved-input-hashes.json').read_text())
assert all(digest(Path(p))==h for p,h in preserved.items())
source=json.loads((old/'final-reconciliation.json').read_text());assert all(digest(S/x['path'])==x['after'] for x in source['files'])
accepted=R/'docs/deployment-completion-20260917/final-blockers/accepted-app';entries=json.loads((R/'docs/stage6-20260917/source.json').read_text())['accepted_files'];assert all(digest(accepted/x['path'])==x['sha256'] for x in entries)
prior=json.loads((old/'deployment-1c0ad3bad7964153a7cdf2ceee603ae2.json').read_text());packages=[prior['package'],next(x['build_b'] for x in prior['records'] if 'build_b' in x)];verified=[]
for item in packages:
    root=Path(item['package']);assert digest(root/'manifest.json')==item['sha256'];manifest=json.loads((root/'manifest.json').read_text());assert all(digest(root/x['path'])==x['sha256'] and (root/x['path']).stat().st_size==x['bytes'] for x in manifest['files']);verified.append({'package':str(root),'manifest_sha256':item['sha256'],'verified_files':len(manifest['files'])})
identities={};roots=set();runs=[]
def visit(value):
    if isinstance(value,dict):
        if all(k in value for k in ('pid','created','exe_digest')):identities[(int(value['pid']),int(value['created']))]={k:value[k] for k in ('pid','created','exe_digest')}
        for v in value.values():visit(v)
    elif isinstance(value,list):
        for v in value:visit(v)
for p in list(D.glob('reproduction-*.json'))+list(D.glob('full-profile-*.json'))+list(D.glob('negative-profile-*.json'))+list(D.glob('full-normal-*.json')):
    data=json.loads(p.read_text());visit(data);roots.update(data['roots']);runs.append({'file':p.name,'checks':len(data['records']),'passed':sum(x['passed'] for x in data['records']),'failed':sum(not x['passed'] for x in data['records'])})
k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.OpenProcess.restype=ctypes.c_void_p;k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_ulonglong)]*4;k.CloseHandle.argtypes=[ctypes.c_void_p];live=[];errors=[]
for (pid,created),identity in identities.items():
    h=k.OpenProcess(0x1000,False,pid)
    if not h:
        error=ctypes.get_last_error()
        if error!=87:errors.append({'pid':pid,'winerror':error})
        continue
    try:
        times=[ctypes.c_ulonglong() for _ in range(4)]
        if not k.GetProcessTimes(h,*[ctypes.byref(x) for x in times]):errors.append({'pid':pid,'winerror':ctypes.get_last_error()})
        elif times[0].value==created:live.append(identity)
    finally:k.CloseHandle(h)
result={'accepted_files_verified':len(entries),'candidate_files_verified':len(source['files']),'packages':verified,'historical_failure_hashes_unchanged':True,'runtime_files_changed':False,'runs':runs,'recorded_identities_checked':len(identities),'live_recorded_identities':live,'identity_check_errors':errors,'test_roots':sorted(roots),'production_changed':False}
(D/'final-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('test_roots','packages')}))
assert not live and not errors
