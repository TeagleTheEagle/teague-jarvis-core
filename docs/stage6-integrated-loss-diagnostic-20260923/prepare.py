import pathlib,json,hashlib,shutil,uuid,difflib
R=pathlib.Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((R.parent/'stage6-large-small-integration-20260922/candidate.json').read_text());O=pathlib.Path(old['code'])
t=json.loads((R.parent/'stage6-loss-telemetry-20260922/integrity.json').read_text());T=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\f40cb16a8a384236b05179bc8f2aea6b\code')
for x in old['files']:assert sha(O/x['name'])==x['sha256'],x['name']
for x in t['candidate']:assert sha(T/x['name'])==x['sha256'],x['name']
assert shutil.disk_usage(O).free>300*2**30,'Existing two-channel storage reserve unavailable'
C=O.parent.parent/uuid.uuid4().hex/'code';C.mkdir(parents=True)
for x in old['files']:
 p=C/x['name'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(O/x['name'],p)
overlays=['authority_trace.cpp','startup_trace.cpp','durable_sink.hpp','trace_sink.hpp','trace_telemetry.hpp','J6AuthorityTrace.exe','J6StartupTrace.exe']
for n in overlays:shutil.copy2(T/n,C/n)
p=C/'small_launch.ps1';s=p.read_text();needle=str(O).replace('\\','\\\\');assert s.count(needle)==1;s=s.replace(needle,str(C).replace('\\','\\\\'));p.write_text(s)
allow=json.loads((C/'baseline-allowlist.json').read_text());allow['syntheticRoots']=[str(C/'small-synthetic')];assert allow['approvedProtectedRoots']==[] and allow['realProtectedAccess'] is False
(C/'baseline-allowlist.json').write_text(json.dumps(allow,indent=2))
files=[dict(name=str(p.relative_to(C)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(C.rglob('*')) if p.is_file() and p.name!='small-source.json']
(C/'small-source.json').write_text(json.dumps(files,indent=2))
changes=[]
for x in files:
 before=sha(O/x['name']) if (O/x['name']).is_file() else None
 if before!=x['sha256']:changes.append(dict(name=x['name'],before=before,after=x['sha256'],telemetryOverlay=x['name'] in overlays))
for n in ('small_launch.ps1','baseline-allowlist.json'):
 (R/(n+'.diff')).write_text(''.join(difflib.unified_diff((O/n).read_text().splitlines(True),(C/n).read_text().splitlines(True))))
with (R/'candidate.json').open('x') as f:json.dump(dict(code=str(C),source=str(C/'small-synthetic'),files=files,changes=changes,oldVerified=len(old['files']),telemetryVerified=len(t['candidate']),diagnosticOnly=True,attemptLimit=1),f,indent=2)
for name in ('run.ps1','gate.ps1','host_preflight.ps1'):shutil.copy2(R.parent/'stage6-large-small-integration-20260922'/name,R/name)
print(C)
