"""Read-only preservation/census preflight; records only this new action's report."""
import hashlib,json,sys,zipfile
from pathlib import Path
R=Path(__file__).parent
P=R.parent/'stage6-failure-preservation-v1-20260923'
O=R.parent/'stage6-coordination-v3-20260923'
T=Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2')
sys.path.insert(0,str(T))
import failure_preserve_v1 as f
f.verify_candidate(f.cli_policy())
expected='e781ed6389dd809805fb89c27b6f838623d4f2da707fcd7a160d22c25249ea28'
if f.sha(T/'source-manifest.json')!=expected:raise ValueError('TOOL_MANIFEST_DRIFT')
rows=json.loads((T/'source-manifest.json').read_text())
for x in rows:
 if f.sha(T/x['name'])!=x['sha256']:raise ValueError('TOOL_DRIFT')
inputs=json.loads((O/'before.json').read_text())['inputs']
for x in inputs:
 p=Path(x['path'])
 if 'VirtualBox' in str(p):raise ValueError('UNEXPECTED_PROTECTED_PATH')
 s=p.stat()
 if (s.st_size,s.st_mtime_ns,f.sha(p))!=(x['bytes'],x['mtimeNs'],x['sha256']):raise ValueError('PRESERVED_INPUT_DRIFT:'+str(p))
archives=[]
for report in (O/'archive-receipt.json',P/'final-receipt.json'):
 v=json.loads(report.read_text());a=Path(v['archive']);m=a.parent/'manifest.json'
 if f.sha(a)!=v['archiveSHA256'] or f.sha(m)!=v['manifestSHA256']:raise ValueError('ARCHIVE_DRIFT')
 rows=json.loads(m.read_text());rows=rows['files'] if isinstance(rows,dict) else rows
 with zipfile.ZipFile(a) as z:
  if len(z.namelist())!=len(rows):raise ValueError('ARCHIVE_COUNT')
  for x in rows:
   with z.open(x['path']) as stream:d=hashlib.file_digest(stream,'sha256').hexdigest()
   if d!=x['sha256'] or z.getinfo(x['path']).file_size!=x['bytes']:raise ValueError('ARCHIVE_MEMBER')
 archives.append(dict(path=str(a),members=len(rows),sha256=v['archiveSHA256']))
census=f.host_census(R)
v=dict(status='PASS' if f.census_clean(census,R) else 'BLOCKED',utc=f.utc(),candidateFiles=216,
       toolFiles=4,preservedInputs=len(inputs),archives=archives,census=census,
       protectedAccess=False,productionChange=False,liveStarted=False)
f.write_new(R/'preflight.json',v)
print(json.dumps(v))
if v['status']!='PASS':raise SystemExit(1)
