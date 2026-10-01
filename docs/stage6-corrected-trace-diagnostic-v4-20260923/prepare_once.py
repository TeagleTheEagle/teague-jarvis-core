"""Verify approved correction evidence, then invoke the documented preflight once."""
import pathlib,json,hashlib,zipfile,subprocess,sys,datetime,os
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-path-filter-fix-20260923'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code')
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(n,v):
 with (R/n).open('x') as f:json.dump(v,f,indent=2);f.flush();os.fsync(f.fileno())
assert not (R/'preflight-attempt.json').exists()
v=read(P/'archive-receipt.json');a=pathlib.Path(v['archive']);m=a.parent/'manifest.json'
assert sha(a)==v['archiveSHA256'] and sha(m)==v['manifestSHA256']
rows=read(m)['files']
with zipfile.ZipFile(a) as z:
 assert len(z.namelist())==len(rows)==v['members']==278==len(set(z.namelist()))
 for x in rows:
  with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
assert sha(P/'preflight.py')=='485b0f0e172dce2765214caf96663e26d0afc44a41c6459c709ad7446f1d28ef'
write('correction-archive-check.json',dict(status='PASS',members=278,archiveSHA256=sha(a),helperSHA256=sha(P/'preflight.py')))
args=[sys.executable,'-B','-c',"exec(compile(open("+repr(str(P/'preflight.py'))+").read(), 'preflight.py', 'exec'))"]
write('preflight-attempt.json',dict(args=args,cwd=str(C),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempt=1,liveLaunches=0))
p=subprocess.run(args,cwd=C,capture_output=True,text=True,timeout=60)
write('preflight-command-result.json',dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
print(p.stdout,p.stderr);raise SystemExit(p.returncode)
