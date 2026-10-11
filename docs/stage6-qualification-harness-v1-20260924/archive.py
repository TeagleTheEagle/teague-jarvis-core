from prepare import *
from analyze import verify_binding
import ast,zipfile
A=pathlib.Path(r'C:\Users\jonny\OneDrive\Desktop\TEAGUE INDUSTRIES DATABASE\06 SOURCE RECORDS\STAGE6 QUALIFICATION HARNESS V1 20260924')
assert not A.exists()
verify_binding(load(R/'qualification-binding-final.json'))
for x in load(R/'before.json')['inputs']:assert rec(x['path'])==x
assert not (C/'ONE-FINAL-ATTEMPT').exists()
census=load(R/'final-census.json');assert census['processCount']==census['traceCount']==0
syntax=[]
for p in R.glob('*.py'):ast.parse(p.read_text());syntax.append(rec(p))
write(R/'final-syntax-2.json',dict(status='PASS',files=syntax))
toolroot=pathlib.Path(r'C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x64')
compiler=dict(version='19.44.35228.0',source='generated assembly banner',files=[rec(toolroot/n) for n in ['cl.exe','link.exe']])
assert load(R/'compiler-identity.json')==compiler
exit_evidence=load(R/'selftest-3-exit.json')
assert exit_evidence['code']==0 and exit_evidence['exited'] and not exit_evidence['benchmarkExecuted']
write(R/'elevation-check.json',dict(status='PASS',basis='Successful ordinary subprocess.Popen/CreateProcess selftest launch; no ShellExecute runas or UAC used. No embedded-manifest claim.',evidence=rec(R/'selftest-3-exit.json'),launcher=rec(R/'test_harness.py'),UACRequested=False,liveETWStarted=False))
write(R/'final-status.json',dict(status='FINAL_OVERHEAD_HARNESS_READY',qualificationExecuted=False,nativeChecks=254,pythonChecks=27,sourceCodePreservationChecks=1268,preservedInputs=1219,processes=0,traces=0,productionChanged=False,protectedAccess=False,performanceQualified=False))
members=[]
for label,root in [('report',R),('harness',C)]:
 for p in sorted(root.rglob('*')):
  if p.is_file() and 'temp' not in p.relative_to(root).parts:members.append(dict(member=label+'/'+p.relative_to(root).as_posix(),**rec(p)))
write(R/'archive-manifest.json',members)
A.mkdir(parents=True);zpath=A/'evidence.zip'
with zipfile.ZipFile(zpath,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for x in members:z.write(x['path'],x['member'])
 z.write(R/'archive-manifest.json','archive-manifest.json')
with zipfile.ZipFile(zpath) as z:
 assert len(z.namelist())==len(members)+1 and z.testzip() is None
 for x in members:
  with z.open(x['member']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
  assert z.getinfo(x['member']).file_size==x['bytes']
 assert z.read('archive-manifest.json')==(R/'archive-manifest.json').read_bytes()
receipt=dict(status='PASS',archive=str(zpath),sha256=sha(zpath),verifiedMembers=len(members)+1,manifestSHA256=sha(R/'archive-manifest.json'))
write(R/'archive-receipt.json',receipt);write(A/'archive-receipt.json',receipt)
shutil.copy2(R/'archive-manifest.json',A/'archive-manifest.json');assert sha(A/'archive-manifest.json')==receipt['manifestSHA256']
print(json.dumps(receipt))
