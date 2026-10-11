"""Preserve originals; make a separate corrected preflight helper only."""
import pathlib,json,hashlib,zipfile,ast,difflib
R=pathlib.Path(__file__).parent;P=R.parent/'stage6-one-trace-diagnostic-v4-20260923';O=R.parent/'stage6-workspace-binding-v4-20260923'
C=pathlib.Path(r'D:\JARVIS-STAGE6-LIVE\fb0bf86657a64aff85a1799db37e94c7\code')
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def record(p):
 s=p.stat();return dict(path=str(p),bytes=s.st_size,mtimeNs=s.st_mtime_ns,sha256=sha(p))
assert not (R/'before.json').exists()
archives=[]
for root in (P,O):
 receipt=read(root/'archive-receipt.json');a=pathlib.Path(receipt['archive']);m=a.parent/'manifest.json'
 assert sha(a)==receipt['archiveSHA256'] and sha(m)==receipt['manifestSHA256']
 rows=read(m)['files']
 with zipfile.ZipFile(a) as z:
  assert len(z.namelist())==len(rows)==receipt['members']==len(set(z.namelist()))
  for x in rows:
   with z.open(x['path']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==x['sha256']
 archives.append(receipt)
rows=read(C/'small-source-v3.json');assert len(rows)==229 and sha(C/'small-source-v3.json')=='d2f6738f5d7c3f22fe361f6cb1da174f630d8e150574009b59825d88321ed4d7'
for x in rows:assert sha(C/x['name'])==x['sha256']
inputs=[record(C/x['name']) for x in rows]+[record(C/'small-source-v3.json')]+[record(p) for p in P.iterdir() if p.is_file()]
with (R/'before.json').open('x') as f:json.dump(dict(inputs=inputs,archives=archives,candidate=str(C),originalHelperSHA256=sha(P/'preflight.py')),f,indent=2)
original=(P/'preflight.py').read_text();snippet=(R/'dataset-filter-snippet.py').read_text()
needle=" dataset=[dict(name=x['name'],sha256=x['sha256'],bytes=x['bytes']) for x in rows if x['name'].startswith('small-synthetic/')]"
assert original.count(needle)==1
new=original.replace("assert pathlib.Path.cwd()==C",snippet+'\nassert pathlib.Path.cwd()==C',1).replace(needle,' dataset=dataset_records(rows,C)',1)
# New evidence destination prevents overwriting or reusing the failed preflight.
new=new.replace(str(P),str(R),1)
ast.parse(new)
with (R/'preflight.py').open('x') as f:f.write(new)
with (R/'implementation.diff').open('x') as f:f.write(''.join(difflib.unified_diff(original.splitlines(True),new.splitlines(True),fromfile=str(P/'preflight.py'),tofile=str(R/'preflight.py'))))
print(json.dumps(dict(originalSHA256=sha(P/'preflight.py'),correctedSHA256=sha(R/'preflight.py'),candidateFilesVerified=229,archivesVerified=[x['members'] for x in archives],liveRun=False)))
