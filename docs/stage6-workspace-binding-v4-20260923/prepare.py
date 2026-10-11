import pathlib,json,hashlib,uuid,shutil,zipfile
R=pathlib.Path(__file__).parent;D=R.parent;S=D/'stage6-loss-telemetry-v2-20260923';N=S/'candidate'
T=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\cab9745de28a4cae8aa6f6f7a516bf54\code-r2')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def record(p):
 s=p.stat();return dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=sha(p))
assert not (R/'before.json').exists()
# Execute only the already-reviewed read/hash checks, not its output writer.
code=(S/'verify_preservation.py').read_text();code=code.split('result=')[0]
exec(compile(code,str(S/'verify_preservation.py'),'exec'),{'__file__':str(S/'verify_preservation.py')})
archives=[]
for receipt in (S/'archive-receipt.json',D/'stage6-trace-diagnostic-preflight-20260923/archive-receipt.json'):
 v=read(receipt);a=pathlib.Path(v['archive']);m=a.parent/'manifest.json';assert sha(a)==v['archiveSHA256'] and sha(m)==v['manifestSHA256'];rows=read(m);rows=rows['files'] if isinstance(rows,dict) else rows
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==len(rows)==len(set(z.namelist()))
  for x in rows:
   with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
 archives.append(dict(path=str(a),members=len(rows),sha256=sha(a)))
rows=read(N/'small-source-v3.json');assert len(rows)==217
inputs=[record(N/x['name']) for x in rows]+[record(N/'small-source-v3.json')]
inputs += [record(T/x['name']) for x in read(T/'source-manifest.json')]+[record(T/'source-manifest.json')]
C=pathlib.Path('D:/JARVIS-STAGE6-LIVE')/uuid.uuid4().hex/'code'
C.mkdir(parents=True,exist_ok=False)
for x in rows:
 p=C/x['name'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(N/x['name'],p);assert sha(p)==x['sha256']
shutil.copy2(N/'small-source-v3.json',C/'predecessor-source-v3.json')
for name in ('failure_preserve_v1.py','one_run_v1.py','policy.json','test_failure_preserve_v1.py'):
 shutil.copy2(T/name,R/name)
with (R/'before.json').open('x') as f:json.dump(dict(candidate=str(C),predecessor=str(N),inputs=inputs,archives=archives,liveRun=False),f,indent=2)
print(json.dumps(dict(candidate=str(C),files=217,priorInputsVerified=482,failedRunFilesVerified=83,archives=archives)))
